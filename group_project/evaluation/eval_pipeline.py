"""
RAG Evaluation Pipeline.

Sử dụng DeepEval / RAGAS / TruLens để đánh giá chất lượng RAG pipeline.
Chọn 1 framework và implement đầy đủ.

Yêu cầu:
    1. Load golden_dataset.json (≥15 Q&A pairs)
    2. Chạy RAG pipeline trên từng question
    3. Evaluate với 4 metrics: faithfulness, relevance, context_recall, context_precision
    4. So sánh A/B ít nhất 2 configs
    5. Export results ra results.md

Lưu ý rate limit nếu dùng model OpenRouter ":free": RAGAS/DeepEval gọi LLM RẤT NHIỀU LẦN
(không phải 1 lần/câu hỏi mà nhiều lần/metric/câu hỏi). Model free của OpenRouter giới hạn
50 request/ngày CHO CẢ TÀI KHOẢN (không phải theo model hay theo API key — đổi model free
khác hay tạo key mới KHÔNG reset quota). Nếu chạy full 15+ câu hỏi mà bị rate limit giữa
chừng, thử giảm xuống subset 5 câu để chạy kịp trong buổi, hoặc nạp $10 credit để mở khóa
1000 request/ngày.
"""

import json
from pathlib import Path
from statistics import mean

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

# Hai cấu hình này được giữ ở tầng evaluation để không phải thay đổi chữ ký
# generate_with_citation() đã chốt trong PLAN.md. Runner thật sẽ đọc các tham số
# và cấu hình retrieve() tương ứng khi F5-9/F5-10 được bàn giao.
EVAL_CONFIGS = {
    "hybrid_rerank": {
        "label": "Config A (hybrid + rerank)",
        "use_reranking": True,
        "retrieval_mode": "hybrid",
    },
    "dense_only": {
        "label": "Config B (dense-only)",
        "use_reranking": False,
        "retrieval_mode": "dense",
    },
}


def load_golden_dataset() -> list[dict]:
    """Đọc và kiểm tra cấu trúc tối thiểu của Golden dataset."""
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

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
                raise ValueError(f"Mẫu số {index}, trường {field} phải là chuỗi có nội dung")

    return dataset


def prepare_ragas_records(
    golden_dataset: list[dict], pipeline_outputs: list[dict]
) -> list[dict]:
    """Chuẩn hóa output pipeline thành các record đầu vào cho RAGAS.

    Hàm này không import RAGAS nên có thể test bằng fixture trong khi chờ F5-10.
    Mỗi output phải có ``answer`` và ``sources`` theo hợp đồng Task 10.
    """
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
            if isinstance(source, dict):
                content = source.get("content", "")
            else:
                content = str(source)
            if content:
                contexts.append(content)

        records.append(
            {
                "question": golden["question"],
                "answer": str(output["answer"]),
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


def find_worst_performers(
    per_question: list[dict], top_n: int = 3
) -> list[dict]:
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
        ranked.append(item)

    return sorted(ranked, key=lambda item: item["average"])[:top_n]


# =============================================================================
# Option 1: DeepEval
# =============================================================================

def evaluate_with_deepeval(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng DeepEval.

    pip install deepeval
    """
    # TODO: Implement
    #
    # from deepeval import evaluate
    # from deepeval.metrics import (
    #     FaithfulnessMetric,
    #     AnswerRelevancyMetric,
    #     ContextualRecallMetric,
    #     ContextualPrecisionMetric,
    # )
    # from deepeval.test_case import LLMTestCase
    #
    # test_cases = []
    # for item in golden_dataset:
    #     result = rag_pipeline.generate_with_citation(item["question"])
    #     test_case = LLMTestCase(
    #         input=item["question"],
    #         actual_output=result["answer"],
    #         expected_output=item["expected_answer"],
    #         retrieval_context=[c["content"] for c in result["sources"]],
    #     )
    #     test_cases.append(test_case)
    #
    # metrics = [
    #     FaithfulnessMetric(threshold=0.7),
    #     AnswerRelevancyMetric(threshold=0.7),
    #     ContextualRecallMetric(threshold=0.7),
    #     ContextualPrecisionMetric(threshold=0.7),
    # ]
    #
    # results = evaluate(test_cases, metrics)
    # return results
    raise NotImplementedError("Implement evaluate_with_deepeval")


# =============================================================================
# Option 2: RAGAS
# =============================================================================

def evaluate_with_ragas(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng RAGAS.

    pip install ragas
    """
    # TODO: Implement
    #
    # from ragas import evaluate
    # from ragas.metrics import (
    #     faithfulness,
    #     answer_relevancy,
    #     context_recall,
    #     context_precision,
    # )
    # from datasets import Dataset
    #
    # eval_data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
    #
    # for item in golden_dataset:
    #     result = rag_pipeline.generate_with_citation(item["question"])
    #     eval_data["question"].append(item["question"])
    #     eval_data["answer"].append(result["answer"])
    #     eval_data["contexts"].append([c["content"] for c in result["sources"]])
    #     eval_data["ground_truth"].append(item["expected_answer"])
    #
    # dataset = Dataset.from_dict(eval_data)
    # result = evaluate(
    #     dataset,
    #     metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
    # )
    # return result.to_pandas()
    raise NotImplementedError("Implement evaluate_with_ragas")


# =============================================================================
# Option 3: TruLens
# =============================================================================

def evaluate_with_trulens(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng TruLens.

    pip install trulens
    """
    # TODO: Implement
    #
    # from trulens.apps.custom import TruCustomApp
    # from trulens.core import Feedback
    # from trulens.providers.openai import OpenAI as TruOpenAI
    #
    # provider = TruOpenAI()
    #
    # f_faithfulness = Feedback(provider.groundedness_measure_with_cot_reasons).on_output()
    # f_relevance = Feedback(provider.relevance).on_input_output()
    # f_context_relevance = Feedback(provider.context_relevance).on_input()
    #
    # tru_rag = TruCustomApp(
    #     rag_pipeline,
    #     app_name="EcommerceSupport_RAG",
    #     feedbacks=[f_faithfulness, f_relevance, f_context_relevance],
    # )
    #
    # with tru_rag as recording:
    #     for item in golden_dataset:
    #         rag_pipeline.generate_with_citation(item["question"])
    #
    # # Dashboard: from trulens.dashboard import run_dashboard; run_dashboard()
    raise NotImplementedError("Implement evaluate_with_trulens")


# =============================================================================
# A/B Comparison
# =============================================================================

def compare_configs(rag_pipeline, golden_dataset: list[dict]):
    """
    Chạy cùng một evaluation runner cho hai cấu hình A/B.

    ``rag_pipeline`` ở giai đoạn này là adapter callable nhận ba đối số:
    ``golden_dataset``, ``config_name`` và ``config``. Adapter giúp F5-13
    cấu hình retrieval mà không thay đổi chữ ký generate_with_citation().

    Adapter phải trả ``{"per_question": list[dict]}``; mỗi dict chứa câu hỏi
    và bốn metric trong METRIC_KEYS. Trường ``overall`` sẽ được tính tự động.
    """
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


# =============================================================================
# Export Results
# =============================================================================

def export_results(results: dict, comparison: dict):
    """Xuất bảng A/B và ba câu có điểm thấp nhất ra ``results.md``."""
    required_configs = ("hybrid_rerank", "dense_only")
    missing = [name for name in required_configs if name not in comparison]
    if missing:
        raise ValueError(f"Thiếu kết quả cấu hình: {', '.join(missing)}")

    config_a = comparison["hybrid_rerank"]
    config_b = comparison["dense_only"]
    overall_a = config_a.get("overall") or summarize_metrics(
        config_a.get("per_question", [])
    )
    overall_b = config_b.get("overall") or summarize_metrics(
        config_b.get("per_question", [])
    )

    def score(value: float) -> str:
        return f"{float(value):.4f}"

    def markdown_cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "# RAG Evaluation Results",
        "",
        "## Framework sử dụng",
        "",
        str(results.get("framework", "RAGAS")),
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
            f"**Config A:** {EVAL_CONFIGS['hybrid_rerank']['label']}.",
            "",
            f"**Config B:** {EVAL_CONFIGS['dense_only']['label']}.",
            "",
            "**Kết luận:** "
            + str(results.get("conclusion", "Bổ sung sau khi chạy evaluation thật.")),
            "",
            "## Worst Performers (Bottom 3 của Config A)",
            "",
            "| # | Question | Faithfulness | Relevance | Recall | Precision | Failure Stage | Root Cause |",
            "|--:|----------|-------------:|----------:|-------:|----------:|---------------|------------|",
        ]
    )

    worst = find_worst_performers(config_a.get("per_question", []), top_n=3)
    for index, row in enumerate(worst, start=1):
        lines.append(
            f"| {index} | {markdown_cell(row.get('question', ''))} | "
            f"{score(row['faithfulness'])} | {score(row['answer_relevance'])} | "
            f"{score(row['context_recall'])} | {score(row['context_precision'])} | "
            f"{markdown_cell(row.get('failure_stage', 'Chưa phân tích'))} | "
            f"{markdown_cell(row.get('root_cause', 'Chưa phân tích'))} |"
        )

    recommendations = results.get("recommendations", [])
    lines.extend(["", "## Recommendations", ""])
    if recommendations:
        for index, recommendation in enumerate(recommendations, start=1):
            lines.append(f"{index}. {recommendation}")
    else:
        lines.append("Bổ sung sau khi phân tích các worst performers.")

    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    golden_dataset = load_golden_dataset()
    print(f"Loaded {len(golden_dataset)} test cases")
    print(f"Configs: {', '.join(EVAL_CONFIGS)}")
    print("Evaluation scaffold ready; chờ adapter F5-9/F5-10 để chạy RAGAS thật.")
