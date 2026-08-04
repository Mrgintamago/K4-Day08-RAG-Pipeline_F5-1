"""Đánh giá RAG bằng RAGAS và so sánh A/B hai cấu hình retrieval.

Quy trình F5-13:
    1. Đọc và kiểm tra ``golden_dataset.json``.
    2. Chạy ``generate_with_citation()`` cho từng câu hỏi.
    3. Đo faithfulness, answer relevancy, context recall và context precision.
    4. So sánh hybrid + rerank với dense-only.
    5. Xuất bảng điểm và ba câu tệ nhất ra ``results.md``.

RAGAS gọi LLM nhiều lần cho mỗi câu hỏi. Lệnh mặc định chỉ chạy 5 câu để kiểm tra
quota trước; chỉ dùng ``--full`` sau khi lượt 5 câu đã thành công. ``RunConfig`` được
đặt ``max_workers=1`` và runner có khoảng nghỉ giữa các câu để giảm nguy cơ HTTP 429.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Callable, Iterator

from dotenv import load_dotenv

load_dotenv()

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"

REQUIRED_GOLDEN_FIELDS = {"question", "expected_answer", "expected_context"}
METRIC_KEYS = (
    "faithfulness",
    "answer_relevance",
    "context_recall",
    "context_precision",
)
METRIC_LABELS = {
    "faithfulness": "Faithfulness",
    "answer_relevance": "Answer Relevance",
    "context_recall": "Context Recall",
    "context_precision": "Context Precision",
}
RAGAS_COLUMN_MAP = {
    "faithfulness": "faithfulness",
    # RAGAS 0.1.21 dùng hậu tố ``relevancy``; báo cáo của nhóm dùng ``relevance``.
    "answer_relevance": "answer_relevancy",
    "context_recall": "context_recall",
    "context_precision": "context_precision",
}

# Model judge tách khỏi model mặc định của Task 10 vì model generation có thể bị gỡ
# khỏi OpenRouter độc lập. ID này được kiểm tra qua endpoint /api/v1/models ngày chạy
# F5-13; vẫn có thể ghi đè bằng RAGAS_JUDGE_MODEL trong .env khi nhà cung cấp đổi model.
DEFAULT_OPENROUTER_JUDGE_MODEL = "google/gemma-4-31b-it:free"
CACHE_VERSION = "f5-13-v2"

# Config B phải thật sự chỉ dùng dense search. Trong Task 9, ``use_reranking=False``
# vẫn gộp dense và BM25 bằng RRF, nên runner bên dưới gọi semantic_search trực tiếp.
# Cách làm này không đổi bất kỳ chữ ký public nào đã chốt trong PLAN.md.
EVAL_CONFIGS = {
    "hybrid_rerank": {
        "label": "Config A (hybrid + rerank)",
        "retrieval_mode": "hybrid",
        "use_reranking": True,
    },
    "dense_only": {
        "label": "Config B (dense-only)",
        "retrieval_mode": "dense",
        "use_reranking": False,
    },
}


def load_golden_dataset() -> list[dict]:
    """Đọc và kiểm tra cấu trúc tối thiểu của Golden dataset."""
    with GOLDEN_DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError("golden_dataset.json phải chứa một JSON array")
    if len(dataset) < 15:
        raise ValueError("Golden dataset phải có ít nhất 15 cặp Q&A")

    for index, item in enumerate(dataset, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Mẫu số {index} phải là một JSON object")
        missing = REQUIRED_GOLDEN_FIELDS - set(item)
        if missing:
            raise ValueError(
                f"Mẫu số {index} thiếu trường: {', '.join(sorted(missing))}"
            )
        for field in REQUIRED_GOLDEN_FIELDS:
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(
                    f"Mẫu số {index}, trường {field} phải là chuỗi có nội dung"
                )

    return dataset


def prepare_ragas_records(
    golden_dataset: list[dict], pipeline_outputs: list[dict]
) -> list[dict]:
    """Chuẩn hóa output Task 10 thành record đầu vào của RAGAS."""
    if len(golden_dataset) != len(pipeline_outputs):
        raise ValueError("Số output pipeline phải bằng số mẫu trong Golden dataset")

    records = []
    for index, (golden, output) in enumerate(
        zip(golden_dataset, pipeline_outputs), start=1
    ):
        if not isinstance(output, dict) or "answer" not in output:
            raise ValueError(f"Output số {index} thiếu trường answer")

        sources = output.get("sources", [])
        if not isinstance(sources, list):
            raise ValueError(f"Output số {index}, sources phải là list")

        contexts = []
        for source in sources:
            content = source.get("content", "") if isinstance(source, dict) else str(source)
            if content and content.strip():
                contexts.append(content.strip())

        answer = str(output["answer"]).strip()
        # Faithfulness của RAGAS 0.1.x bỏ qua đoạn không kết thúc bằng dấu câu và trả
        # NaN với cảnh báo "No statements were generated". Thêm dấu chấm chỉ chuẩn hóa
        # cú pháp cho sentence splitter, không thay đổi nội dung câu trả lời được chấm.
        if answer and answer[-1] not in ".!?":
            answer += "."

        records.append(
            {
                "question": golden["question"],
                "answer": answer,
                "contexts": contexts,
                "ground_truth": golden["expected_answer"],
                "retrieval_source": output.get("retrieval_source", "unknown"),
            }
        )

    return records


def summarize_metrics(per_question: list[dict]) -> dict[str, float]:
    """Tính trung bình bốn metric trên các câu đã đánh giá."""
    if not per_question:
        return {metric: 0.0 for metric in METRIC_KEYS}

    summary = {}
    for metric in METRIC_KEYS:
        values = [float(row[metric]) for row in per_question if metric in row]
        if not values:
            raise ValueError(f"Không có dữ liệu cho metric {metric}")
        summary[metric] = mean(values)
    return summary


def find_worst_performers(per_question: list[dict], top_n: int = 3) -> list[dict]:
    """Lấy các câu có trung bình bốn metric thấp nhất."""
    if top_n <= 0:
        return []

    ranked = []
    for index, row in enumerate(per_question, start=1):
        missing = set(METRIC_KEYS) - set(row)
        if missing:
            raise ValueError(
                f"Kết quả câu {index} thiếu metric: {', '.join(sorted(missing))}"
            )
        item = dict(row)
        item["average"] = mean(float(row[metric]) for metric in METRIC_KEYS)
        stage, cause = _diagnose_failure(item)
        item.setdefault("failure_stage", stage)
        item.setdefault("root_cause", cause)
        ranked.append(item)

    return sorted(ranked, key=lambda item: item["average"])[:top_n]


def _diagnose_failure(row: dict) -> tuple[str, str]:
    """Suy luận tầng lỗi từ metric thấp nhất để hỗ trợ phân tích worst performer."""
    lowest = min(METRIC_KEYS, key=lambda metric: float(row[metric]))
    diagnostics = {
        "faithfulness": (
            "Generation",
            "Câu trả lời chưa bám chặt các context đã truy xuất.",
        ),
        "answer_relevance": (
            "Generation",
            "Câu trả lời chưa tập trung trực tiếp vào ý hỏi.",
        ),
        "context_recall": (
            "Retrieval",
            "Retriever bỏ sót evidence cần thiết so với đáp án chuẩn.",
        ),
        "context_precision": (
            "Ranking",
            "Top-k chứa nhiều chunk nhiễu hoặc chunk liên quan đứng chưa đủ cao.",
        ),
    }
    return diagnostics[lowest]


def _call_pipeline(rag_pipeline, question: str, top_k: int) -> dict:
    """Gọi callable hoặc object có ``generate_with_citation`` theo cùng hợp đồng."""
    if callable(rag_pipeline):
        output = rag_pipeline(question, top_k=top_k)
    elif hasattr(rag_pipeline, "generate_with_citation"):
        output = rag_pipeline.generate_with_citation(question, top_k=top_k)
    else:
        raise TypeError(
            "rag_pipeline phải callable hoặc có phương thức generate_with_citation"
        )
    if not isinstance(output, dict):
        raise ValueError("generate_with_citation phải trả về dict")
    return output


def run_pipeline_outputs(
    rag_pipeline,
    golden_dataset: list[dict],
    *,
    top_k: int = 5,
    delay_seconds: float = 1.0,
) -> list[dict]:
    """Sinh câu trả lời tuần tự và nghỉ giữa các câu để hạn chế rate limit."""
    if top_k <= 0:
        raise ValueError("top_k phải lớn hơn 0")
    if delay_seconds < 0:
        raise ValueError("delay_seconds không được âm")

    outputs = []
    total = len(golden_dataset)
    for index, item in enumerate(golden_dataset, start=1):
        print(f"  [{index}/{total}] {item['question']}")
        outputs.append(_call_pipeline(rag_pipeline, item["question"], top_k))
        if delay_seconds and index < total:
            time.sleep(delay_seconds)
    return outputs


def _dense_only_search(query: str, top_k: int = 5) -> list[dict]:
    """Retriever của Config B: semantic search thuần, không BM25 và không RRF."""
    from src.task5_semantic_search import semantic_search

    results = semantic_search(query, top_k=top_k)
    normalized = []
    for item in results[:top_k]:
        result = dict(item)
        result["source"] = "dense"
        normalized.append(result)
    return normalized


def _hybrid_rerank_search(query: str, top_k: int = 5) -> list[dict]:
    """Retriever của Config A: pipeline Task 9 với reranking bật."""
    from src.task9_retrieval_pipeline import retrieve

    return retrieve(query, top_k=top_k, use_reranking=True)


def _retriever_for_config(config_name: str) -> Callable[[str, int], list[dict]]:
    if config_name == "hybrid_rerank":
        return _hybrid_rerank_search
    if config_name == "dense_only":
        return _dense_only_search
    raise ValueError(f"Cấu hình evaluation không hợp lệ: {config_name}")


def _generation_provider_and_model() -> tuple[str, str]:
    """Chọn provider generation riêng với provider judge."""
    openai_key = os.getenv("OPENAI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    default_provider = "openai" if openai_key else "openrouter"
    provider = os.getenv("EVAL_GENERATION_PROVIDER", default_provider).strip().lower()
    if provider == "openai":
        if not openai_key:
            raise RuntimeError(
                "EVAL_GENERATION_PROVIDER=openai nhưng thiếu OPENAI_API_KEY"
            )
        return provider, os.getenv("EVAL_GENERATION_MODEL", "gpt-4o-mini")
    if provider == "openrouter":
        if not openrouter_key:
            raise RuntimeError(
                "EVAL_GENERATION_PROVIDER=openrouter nhưng thiếu OPENROUTER_API_KEY"
            )
        return provider, os.getenv(
            "EVAL_GENERATION_MODEL", DEFAULT_OPENROUTER_JUDGE_MODEL
        )
    raise ValueError("EVAL_GENERATION_PROVIDER chỉ nhận 'openai' hoặc 'openrouter'")


@contextmanager
def _generation_with_retriever(
    retriever: Callable[[str, int], list[dict]],
) -> Iterator[Callable]:
    """Tái sử dụng Task 10 với retriever A/B mà không đổi chữ ký public.

    Task 10 import ``retrieve`` vào namespace module. Runner chạy tuần tự nên có thể thay
    tham chiếu này trong phạm vi context manager và luôn khôi phục trong ``finally``.
    """
    import src.task10_generation as generation

    original_retrieve = generation.retrieve
    original_model = generation.LLM_MODEL
    original_openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    provider, model = _generation_provider_and_model()
    generation.retrieve = retriever
    # Tránh request 404 tới model mặc định cũ của Task 10. Chỉ thay trong thời gian
    # evaluation và luôn khôi phục để không làm đổi hành vi chatbot của thành viên khác.
    generation.LLM_MODEL = model
    # Task 10 ưu tiên OPENROUTER_API_KEY nếu cả hai key cùng tồn tại. Tạm ẩn key này
    # khi evaluation chọn OpenAI, để OpenAI SDK dùng đúng base URL và model.
    if provider == "openai":
        os.environ.pop("OPENROUTER_API_KEY", None)
    try:
        yield generation.generate_with_citation
    finally:
        generation.retrieve = original_retrieve
        generation.LLM_MODEL = original_model
        if original_openrouter_key is not None:
            os.environ["OPENROUTER_API_KEY"] = original_openrouter_key
        else:
            os.environ.pop("OPENROUTER_API_KEY", None)


def _cache_key(
    golden_dataset: list[dict], config_name: str, top_k: int, stage: str
) -> str:
    """Tạo khóa checkpoint không chứa API key hay dữ liệu bí mật."""
    generation_provider, generation_model = _generation_provider_and_model()
    payload = {
        "version": CACHE_VERSION,
        "stage": stage,
        "config": config_name,
        "top_k": top_k,
        "generation_provider": generation_provider,
        "generation_model": generation_model,
        "judge_provider": os.getenv("RAGAS_PROVIDER", "auto"),
        "judge_model": os.getenv("RAGAS_JUDGE_MODEL", "default"),
        "dataset": golden_dataset,
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _cache_path(cache_key: str) -> Path:
    """Đặt checkpoint trong thư mục temp để không lọt file fixture vào Git."""
    directory = Path(tempfile.gettempdir()) / "f5_13_eval_cache"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{cache_key}.json"


def _load_cache(cache_key: str):
    path = _cache_path(cache_key)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _save_cache(cache_key: str, value) -> None:
    path = _cache_path(cache_key)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class _Task4Embeddings:
    """Adapter LangChain dùng đúng embedding model đã index ở Task 4.

    Answer relevancy cần cosine embedding. Dùng model local chung với Task 4 giúp không
    phát sinh thêm API embedding hoặc dependency mới, đồng thời nhất quán không gian vector.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        from src.task4_chunking_indexing import embed_texts

        return embed_texts(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return self.embed_query(text)


def _build_ragas_clients():
    """Tạo LLM judge và embedding adapter cho RAGAS 0.1.21."""
    from langchain_openai import ChatOpenAI
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.run_config import RunConfig

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if not (openrouter_key or openai_key):
        raise RuntimeError(
            "Thiếu OPENROUTER_API_KEY hoặc OPENAI_API_KEY. Không thể chạy LLM judge "
            "của RAGAS; không xuất điểm giả vào results.md."
        )

    # Khi có cả hai key, ưu tiên OpenAI cho judge: RAGAS tạo nhiều request liên tiếp và
    # pool model :free của OpenRouter dễ trả 429 giữa lượt. Generation Task 10 vẫn dùng
    # OpenRouter như thiết kế ban đầu. Có thể ép lại bằng RAGAS_PROVIDER=openrouter.
    default_provider = "openai" if openai_key else "openrouter"
    provider = os.getenv("RAGAS_PROVIDER", default_provider).strip().lower()
    if provider == "openrouter":
        if not openrouter_key:
            raise RuntimeError("RAGAS_PROVIDER=openrouter nhưng thiếu OPENROUTER_API_KEY")
        api_key = openrouter_key
        default_model = DEFAULT_OPENROUTER_JUDGE_MODEL
        base_url = "https://openrouter.ai/api/v1"
    elif provider == "openai":
        if not openai_key:
            raise RuntimeError("RAGAS_PROVIDER=openai nhưng thiếu OPENAI_API_KEY")
        api_key = openai_key
        default_model = "gpt-4o-mini"
        base_url = None
    else:
        raise ValueError("RAGAS_PROVIDER chỉ nhận 'openai' hoặc 'openrouter'")

    judge_model = os.getenv("RAGAS_JUDGE_MODEL", default_model)
    # OpenRouter free chỉ dùng một worker để tránh 429. OpenAI có quota ổn định hơn nên
    # chấm song song bốn metric; nếu cần có thể hạ bằng RAGAS_MAX_WORKERS trong .env.
    default_workers = 1 if provider == "openrouter" else 4
    max_workers = int(os.getenv("RAGAS_MAX_WORKERS", str(default_workers)))
    run_config = RunConfig(
        # context_precision gọi tuần tự một request cho mỗi chunk, nên timeout của cả
        # metric phải lớn hơn timeout HTTP của một request.
        timeout=240,
        max_retries=2,
        max_wait=30,
        max_workers=max_workers,
    )
    llm_kwargs = {
        "model": judge_model,
        "api_key": api_key,
        "temperature": 0,
        "max_retries": 1,
        "timeout": 60,
    }
    if base_url:
        llm_kwargs["base_url"] = base_url

    llm = LangchainLLMWrapper(ChatOpenAI(**llm_kwargs), run_config=run_config)
    embeddings = LangchainEmbeddingsWrapper(
        _Task4Embeddings(), run_config=run_config
    )
    return llm, embeddings, run_config, judge_model


def _score_ragas_records(records: list[dict]) -> dict:
    """Chạy bốn metric RAGAS và chuẩn hóa kết quả theo hợp đồng báo cáo."""
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    if not records:
        raise ValueError("Không có record để đánh giá")
    for index, record in enumerate(records, start=1):
        if not record["contexts"]:
            raise ValueError(
                f"Câu {index} không có context; hãy kiểm tra index/retrieval trước khi chạy RAGAS"
            )

    dataset = Dataset.from_dict(
        {
            "question": [row["question"] for row in records],
            "answer": [row["answer"] for row in records],
            "contexts": [row["contexts"] for row in records],
            "ground_truth": [row["ground_truth"] for row in records],
        }
    )
    llm, embeddings, run_config, judge_model = _build_ragas_clients()
    ragas_result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        ],
        llm=llm,
        embeddings=embeddings,
        run_config=run_config,
        raise_exceptions=True,
    )

    frame_rows = ragas_result.to_pandas().to_dict(orient="records")
    per_question = []
    for source_record, score_row in zip(records, frame_rows):
        row = {
            "question": source_record["question"],
            "answer": source_record["answer"],
            "retrieval_source": source_record["retrieval_source"],
            "context_count": len(source_record["contexts"]),
        }
        for report_key, ragas_key in RAGAS_COLUMN_MAP.items():
            value = float(score_row[ragas_key])
            if not math.isfinite(value):
                raise RuntimeError(
                    f"RAGAS trả NaN/inf cho metric {ragas_key} ở câu: "
                    f"{source_record['question']}"
                )
            row[report_key] = value
        per_question.append(row)

    return {
        "framework": "RAGAS 0.1.21",
        "judge_model": judge_model,
        "per_question": per_question,
        "overall": summarize_metrics(per_question),
    }


def evaluate_with_ragas(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """Chạy pipeline trên Golden dataset rồi đánh giá bằng RAGAS."""
    delay_seconds = float(os.getenv("EVAL_DELAY_SECONDS", "1"))
    top_k = int(os.getenv("EVAL_TOP_K", "5"))
    outputs = run_pipeline_outputs(
        rag_pipeline,
        golden_dataset,
        top_k=top_k,
        delay_seconds=delay_seconds,
    )
    records = prepare_ragas_records(golden_dataset, outputs)
    return _score_ragas_records(records)


def evaluate_with_deepeval(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """F5-13 chọn RAGAS; DeepEval không nằm trong phạm vi triển khai."""
    raise NotImplementedError("F5-13 sử dụng RAGAS, không sử dụng DeepEval")


def evaluate_with_trulens(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """F5-13 chọn RAGAS; TruLens không nằm trong phạm vi triển khai."""
    raise NotImplementedError("F5-13 sử dụng RAGAS, không sử dụng TruLens")


def make_ragas_config_runner(
    *, top_k: int = 5, delay_seconds: float = 1.0
) -> Callable[..., dict]:
    """Tạo adapter đúng hợp đồng ``compare_configs`` cho một lần chạy thật."""

    def runner(*, golden_dataset: list[dict], config_name: str, config: dict) -> dict:
        del config  # config đã được kiểm tra qua config_name và lưu lại ở comparison.
        print(f"\nĐang chạy {EVAL_CONFIGS[config_name]['label']}...")
        result_key = _cache_key(golden_dataset, config_name, top_k, "ragas-result")
        cached_result = _load_cache(result_key)
        if isinstance(cached_result, dict) and isinstance(
            cached_result.get("per_question"), list
        ):
            print("  - Dùng checkpoint điểm RAGAS đã hoàn tất.")
            return cached_result

        retriever = _retriever_for_config(config_name)
        output_key = _cache_key(golden_dataset, config_name, top_k, "outputs")
        outputs = _load_cache(output_key)
        if isinstance(outputs, list) and len(outputs) == len(golden_dataset):
            print("  - Dùng checkpoint câu trả lời đã sinh.")
        else:
            with _generation_with_retriever(retriever) as generator:
                outputs = run_pipeline_outputs(
                    generator,
                    golden_dataset,
                    top_k=top_k,
                    delay_seconds=delay_seconds,
                )
            _save_cache(output_key, outputs)
        records = prepare_ragas_records(golden_dataset, outputs)
        result = _score_ragas_records(records)
        result["top_k"] = top_k
        _save_cache(result_key, result)
        return result

    return runner


def compare_configs(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """Chạy cùng một evaluation runner cho hai cấu hình A/B."""
    if not callable(rag_pipeline):
        raise TypeError("rag_pipeline phải là một evaluation runner callable")

    comparison = {}
    for config_name, config in EVAL_CONFIGS.items():
        config_result = rag_pipeline(
            golden_dataset=golden_dataset,
            config_name=config_name,
            config=dict(config),
        )
        if not isinstance(config_result, dict):
            raise ValueError(f"Runner của {config_name} phải trả về dict")

        per_question = config_result.get("per_question")
        if not isinstance(per_question, list):
            raise ValueError(f"Runner của {config_name} thiếu list per_question")

        comparison[config_name] = {
            **config_result,
            "config": dict(config),
            "overall": summarize_metrics(per_question),
        }

    return comparison


def _automatic_conclusion(comparison: dict) -> str:
    average_a = mean(comparison["hybrid_rerank"]["overall"].values())
    average_b = mean(comparison["dense_only"]["overall"].values())
    if math.isclose(average_a, average_b, abs_tol=0.005):
        return (
            "Hai cấu hình có điểm trung bình gần tương đương (chênh dưới 0,005). "
            "Cần xem từng nhóm câu hỏi trước khi chọn cấu hình mặc định."
        )
    winner = "Config A (hybrid + rerank)" if average_a > average_b else "Config B (dense-only)"
    delta = abs(average_a - average_b)
    return (
        f"{winner} có điểm trung bình bốn metric cao hơn {delta:.4f}. "
        "Kết luận dựa trên cùng tập câu hỏi và cùng LLM judge; xem worst performers "
        "để xác định retrieval, ranking hay generation là nút thắt chính."
    )


def _automatic_recommendations(comparison: dict) -> list[str]:
    overall = comparison["hybrid_rerank"]["overall"]
    ordered = sorted(METRIC_KEYS, key=lambda metric: overall[metric])
    actions = {
        "faithfulness": (
            "Siết prompt grounding và kiểm tra citation theo từng mệnh đề; kỳ vọng tăng faithfulness."
        ),
        "answer_relevance": (
            "Rút gọn câu trả lời và nhắc lại đúng phạm vi câu hỏi; kỳ vọng tăng answer relevance."
        ),
        "context_recall": (
            "Tăng candidate pool hoặc thêm query expansion cho câu hỏi điều luật; kỳ vọng giảm bỏ sót evidence."
        ),
        "context_precision": (
            "Thử embedding BAAI/bge-m3 hoặc cross-encoder reranker; kỳ vọng đẩy chunk đúng lên đầu top-k."
        ),
    }
    return [actions[metric] for metric in ordered[:3]]


def export_results(results: dict, comparison: dict) -> None:
    """Xuất bảng A/B và ba câu có điểm thấp nhất ra ``results.md``."""
    required_configs = ("hybrid_rerank", "dense_only")
    missing = [name for name in required_configs if name not in comparison]
    if missing:
        raise ValueError(f"Thiếu kết quả cấu hình: {', '.join(missing)}")

    config_a = comparison["hybrid_rerank"]
    config_b = comparison["dense_only"]
    overall_a = config_a.get("overall") or summarize_metrics(config_a["per_question"])
    overall_b = config_b.get("overall") or summarize_metrics(config_b["per_question"])

    def score(value: float) -> str:
        return f"{float(value):.4f}"

    def markdown_cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    framework = results.get("framework", config_a.get("framework", "RAGAS"))
    judge_model = results.get("judge_model", config_a.get("judge_model", "unknown"))
    generation_provider = results.get("generation_provider", "unknown")
    generation_model = results.get("generation_model", "unknown")
    sample_count = len(config_a.get("per_question", []))
    top_k = config_a.get("top_k", "unknown")
    conclusion = results.get("conclusion") or _automatic_conclusion(comparison)
    recommendations = results.get("recommendations") or _automatic_recommendations(comparison)

    lines = [
        "# RAG Evaluation Results",
        "",
        f"- Framework: **{markdown_cell(framework)}**",
        f"- Judge model: **{markdown_cell(judge_model)}**",
        f"- Generation: **{markdown_cell(generation_provider)} / "
        f"{markdown_cell(generation_model)}**",
        f"- Số câu đánh giá mỗi cấu hình: **{sample_count}**",
        f"- Số context mỗi câu (top-k): **{top_k}**",
        f"- Thời điểm chạy: **{datetime.now().astimezone().isoformat(timespec='seconds')}**",
        "",
        "## Overall Scores",
        "",
        "| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |",
        "|--------|---------------------------:|----------------------:|--:|",
    ]
    for metric in METRIC_KEYS:
        delta = float(overall_a[metric]) - float(overall_b[metric])
        lines.append(
            f"| {METRIC_LABELS[metric]} | {score(overall_a[metric])} | "
            f"{score(overall_b[metric])} | {delta:+.4f} |"
        )

    average_a = mean(float(overall_a[metric]) for metric in METRIC_KEYS)
    average_b = mean(float(overall_b[metric]) for metric in METRIC_KEYS)
    lines.extend(
        [
            f"| **Average** | **{score(average_a)}** | **{score(average_b)}** | "
            f"**{average_a - average_b:+.4f}** |",
            "",
            "## A/B Comparison Analysis",
            "",
            "- **Config A:** semantic + BM25, gộp và rerank bằng RRF.",
            "- **Config B:** semantic search thuần, không BM25 và không RRF.",
            f"- **Kết luận:** {conclusion}",
            "",
            "## Worst Performers (Bottom 3 của Config A)",
            "",
            "| # | Question | Faithfulness | Relevance | Recall | Precision | Failure Stage | Root Cause |",
            "|--:|----------|-------------:|----------:|-------:|----------:|---------------|------------|",
        ]
    )

    for index, row in enumerate(
        find_worst_performers(config_a.get("per_question", []), top_n=3), start=1
    ):
        lines.append(
            f"| {index} | {markdown_cell(row.get('question', ''))} | "
            f"{score(row['faithfulness'])} | {score(row['answer_relevance'])} | "
            f"{score(row['context_recall'])} | {score(row['context_precision'])} | "
            f"{markdown_cell(row['failure_stage'])} | {markdown_cell(row['root_cause'])} |"
        )

    lines.extend(["", "## Recommendations", ""])
    for index, recommendation in enumerate(recommendations, start=1):
        lines.append(f"{index}. {recommendation}")

    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chạy F5-13 RAGAS A/B evaluation")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Số câu chạy thử; mặc định 5 để kiểm tra quota trước",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Chạy toàn bộ 16 câu sau khi subset 5 câu đã thành công",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Số context cho mỗi câu")
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Số giây nghỉ giữa hai câu hỏi",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Chỉ kiểm tra Golden dataset, không gọi API",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    golden_dataset = load_golden_dataset()
    print(f"Golden dataset hợp lệ: {len(golden_dataset)} câu")
    if args.validate_only:
        return 0
    if args.top_k <= 0 or args.delay < 0:
        raise ValueError("--top-k phải > 0 và --delay phải >= 0")

    selected = golden_dataset if args.full else golden_dataset[: args.limit]
    if not selected:
        raise ValueError("Subset đánh giá phải có ít nhất một câu")
    print(
        f"Bắt đầu A/B trên {len(selected)} câu, top_k={args.top_k}, "
        f"delay={args.delay}s"
    )

    # Kiểm tra key trước retrieval để không tốn thời gian index rồi mới phát hiện
    # không thể gọi generation/RAGAS judge.
    if not (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")):
        raise RuntimeError(
            "Thiếu OPENROUTER_API_KEY hoặc OPENAI_API_KEY. Hãy thêm key vào .env "
            "(không commit file này) rồi chạy lại."
        )

    runner = make_ragas_config_runner(top_k=args.top_k, delay_seconds=args.delay)
    comparison = compare_configs(runner, selected)
    config_a = comparison["hybrid_rerank"]
    generation_provider, generation_model = _generation_provider_and_model()
    report = {
        "framework": config_a.get("framework", "RAGAS 0.1.21"),
        "judge_model": config_a.get("judge_model", "unknown"),
        "generation_provider": generation_provider,
        "generation_model": generation_model,
    }
    export_results(report, comparison)
    print(f"Đã xuất kết quả thật: {RESULTS_PATH}")
    if not args.full:
        print("Subset đã xong. Nếu quota còn đủ, chạy lại với --full cho toàn bộ 16 câu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
