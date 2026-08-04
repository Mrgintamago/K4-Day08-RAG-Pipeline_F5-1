"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (ChromaDB khuyến cáo — đơn giản, local, không cần Docker)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options (chọn 1, cân nhắc đánh đổi cài đặt nặng vs cần API key):
    - sentence-transformers/all-MiniLM-L6-v2 hoặc BAAI/bge-m3 — chạy local, không
      cần API key, nhưng cài nặng (~1-2GB vì kéo theo torch)
    - Google models/text-embedding-004 (768 dim) — nhẹ, cần GEMINI_API_KEY
    - OpenAI text-embedding-3-small (1536 dim) — nhẹ, cần OPENAI_API_KEY
    Gợi ý: đọc EMBEDDING_PROVIDER từ .env (os.getenv("EMBEDDING_PROVIDER", "sentence_transformers"))
    để cả nhóm có thể đổi provider mà không sửa code — nhớ đổi provider phải xoá
    chroma_db/ cũ và reindex vì dimension khác nhau (1024/768/1536) không tương thích ngược.

Vector store options:
    - ChromaDB (khuyến cáo: đơn giản, local persistent, không cần Docker)
    - Weaviate (hỗ trợ hybrid search built-in, cần Docker/Cloud)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers chromadb

Lưu ý quan trọng: nếu sau này đổi corpus (đổi chủ đề, thêm/bớt tài liệu), phải XÓA
chroma_db/ cũ trước khi reindex — nếu không, chunk cũ và mới sẽ tồn tại lẫn lộn
trong cùng collection, retrieval sẽ trả về kết quả rác từ dữ liệu cũ.
"""
import os
import re
import unicodedata
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()  # Load environment variables from .env

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# Chunking strategy — chốt theo LAB_GUIDE (Checkpoint 2).
# CHUNK_SIZE = 800: các bài help center Shopee là văn bản chính sách có đoạn dài;
#   800 ký tự giữ trọn được 1–2 điều khoản trong cùng một chunk (mức 500 hay cắt
#   giữa câu điều kiện "nếu ... thì ..."), mà vẫn thừa chỗ cho context window của LLM.
# CHUNK_OVERLAP = 100 (12.5% của 800): đủ để câu bị cắt ở ranh giới chunk vẫn xuất hiện
#   trọn vẹn ở một trong hai chunk, nhưng không phình số chunk quá nhiều.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
CHUNKING_METHOD = "recursive"  # "recursive" | "markdown_header" | "semantic"

# EMBEDDING_PROVIDER — đổi được qua .env, không phải sửa code (gợi ý của repo gốc).
#   - "sentence_transformers" (mặc định): chạy local, KHÔNG cần API key
#   - "openai": text-embedding-3-small, 1536 chiều — cần OPENAI_API_KEY
#   - "google": models/text-embedding-004, 768 chiều — cần GEMINI_API_KEY
#
# Vì sao mặc định là sentence_transformers: nhóm chỉ có OPENROUTER_API_KEY và
# PAGEINDEX_API_KEY. OpenRouter KHÔNG cung cấp embedding API, nên nhánh "openai"
# không chạy được nếu không mua thêm key riêng của OpenAI.
#
# ⚠️ ĐỔI PROVIDER LÀ PHẢI XOÁ chroma_db/ VÀ INDEX LẠI — số chiều khác nhau
# (384 / 768 / 1536) không tương thích ngược.
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")

# Vì sao chọn paraphrase-multilingual-MiniLM-L12-v2 thay vì BAAI/bge-m3:
#   - Đa ngôn ngữ, huấn luyện trên 50+ thứ tiếng gồm tiếng Việt — hợp corpus
#     văn bản luật + quy định sàn tiếng Việt của nhóm.
#   - Nặng ~470MB so với ~2.2GB của bge-m3. Corpus 31 file ≈ 1.100 chunk,
#     model này embed hết trong vài phút thay vì 15–25 phút.
#   - Chất lượng tiếng Việt kém bge-m3 một chút, nhưng đủ để tách bạch
#     câu hỏi đúng chủ đề và câu lạc đề — điều kiện cần cho ngưỡng fallback ở Task 9.
_MODEL_BY_PROVIDER = {
    "sentence_transformers": ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", 384),
    "openai": ("text-embedding-3-small", 1536),
    "google": ("models/text-embedding-004", 768),
}
EMBEDDING_MODEL, EMBEDDING_DIM = _MODEL_BY_PROVIDER.get(
    EMBEDDING_PROVIDER, _MODEL_BY_PROVIDER["sentence_transformers"]
)

# VECTOR_STORE = "chromadb": Đơn giản, local persistent, không cần Docker,
#   đáp ứng đủ yêu cầu của bài lab.
VECTOR_STORE = "chromadb"
COLLECTION_NAME = "ecommerce_support_docs"


# =============================================================================
# IMPLEMENTATION
# =============================================================================

# --- Helper functions for sharing client ---
_chroma_client = None
_chroma_collection = None
_embedder = None


class _Embedder:
    """
    Bọc 3 provider sau CÙNG MỘT giao diện `.encode(texts)`.

    Vì sao cần lớp bọc: Task 5 gọi `model.encode(query)` theo kiểu sentence-transformers.
    Bọc lại như thế này thì đổi provider chỉ là sửa .env — Task 5 không phải sửa gì,
    đúng tinh thần "viết 1 hàm embed dùng chung cho cả Task 4 và Task 5".

    Client của provider API được khởi tạo LƯỜI (lúc gọi, không phải lúc import).
    Nếu tạo ở cấp module thì thiếu API key là crash ngay khi `import task4`, kéo sập
    cả Task 5, 9, 10 và làm pytest fail hàng loạt dù những task đó không hề dùng API.
    """

    def __init__(self, provider: str, model_name: str):
        self.provider = provider
        self.model_name = model_name
        self._impl = None

    def _load(self):
        if self._impl is not None:
            return self._impl

        if self.provider == "sentence_transformers":
            from sentence_transformers import SentenceTransformer

            self._impl = SentenceTransformer(self.model_name)

        elif self.provider == "openai":
            from openai import OpenAI

            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise RuntimeError(
                    "EMBEDDING_PROVIDER=openai nhưng thiếu OPENAI_API_KEY trong .env. "
                    "Lưu ý OPENROUTER_API_KEY KHÔNG dùng được cho embedding."
                )
            self._impl = OpenAI(api_key=key)

        elif self.provider == "google":
            import google.generativeai as genai

            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise RuntimeError(
                    "EMBEDDING_PROVIDER=google nhưng thiếu GEMINI_API_KEY trong .env"
                )
            genai.configure(api_key=key)
            self._impl = genai

        else:
            raise ValueError(f"EMBEDDING_PROVIDER không hợp lệ: {self.provider}")

        return self._impl

    def encode(self, texts, batch_size: int = 200, show_progress: bool = False):
        """Nhận 1 chuỗi hoặc list chuỗi, trả list[float] hoặc list[list[float]]."""
        single = isinstance(texts, str)
        items = [texts] if single else list(texts)
        impl = self._load()

        if self.provider == "sentence_transformers":
            vectors = impl.encode(
                items, batch_size=32, show_progress_bar=show_progress
            ).tolist()

        elif self.provider == "openai":
            vectors = []
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                resp = impl.embeddings.create(model=self.model_name, input=batch)
                vectors.extend(d.embedding for d in resp.data)

        else:  # google — API nhận từng văn bản một
            vectors = [
                impl.embed_content(model=self.model_name, content=t)["embedding"]
                for t in items
            ]

        return vectors[0] if single else vectors


def get_embedding_model() -> _Embedder:
    """
    Trả về embedder dùng chung cho Task 4 (index) và Task 5 (query).

    Dùng chung một đối tượng là bắt buộc: query phải được embed bằng ĐÚNG model đã
    dùng lúc index, nếu không vector nằm ở hai không gian khác nhau và cosine
    similarity trở nên vô nghĩa.
    """
    global _embedder
    if _embedder is None:
        _embedder = _Embedder(EMBEDDING_PROVIDER, EMBEDDING_MODEL)
    return _embedder


def embed_texts(texts, show_progress: bool = False):
    """Hàm tiện dụng — embed list văn bản bằng provider đang cấu hình."""
    return get_embedding_model().encode(texts, show_progress=show_progress)


def get_collection():
    """Khởi tạo và cache ChromaDB collection."""
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        if not CHROMA_DIR.exists():
            print(f"Chroma DB directory not found at {CHROMA_DIR}, creating it...")
            CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            _chroma_collection = _chroma_client.get_collection(name=COLLECTION_NAME)
            print(f"Chroma collection '{COLLECTION_NAME}' loaded.")
        except Exception:
            # chromadb >=1.0 ném NotFoundError, không phải ValueError.
            print(f"Chroma collection '{COLLECTION_NAME}' not found. Please run task4 to create it.")
            return None

    return _chroma_collection


def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.
    Parse header metadata (title, source, url, customer_role, doc_type) và content.
    
    Returns:
        List of {'content': str, 'metadata': dict}
    """
    documents = []
    print(f"Loading documents from: {STANDARDIZED_DIR}")
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")

        # Tách header và content chính
        try:
            header_part, content_part = content.split("\n---\n", 1)
        except ValueError:
            print(f"  - Skipping {md_file.name}, no '---' separator found.")
            continue

        # Parse metadata từ header
        metadata = {"source": md_file.name}

        # Tiêu đề là dòng đầu tiên, dạng '# <Tiêu đề>'
        title_match = re.search(r"^#\s*(.*)", header_part, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # Các metadata khác dạng '**Key:** value'
        meta_lines = re.findall(r"\*\*(.*?):\*\*\s*(.*)", header_part)
        for key, value in meta_lines:
            # Chuẩn hoá key: 'Crawled' -> 'crawled', 'customer_role' -> 'customer_role'
            key_lower = key.lower().replace(" ", "_")
            # '**Source:**' trong file .md là URL gốc, KHÔNG được ghi đè lên
            # metadata['source'] (tên file). Task 10 dùng 'source' làm nhãn trích dẫn
            # ngắn gọn và Task 9 dùng nó để khử trùng lặp — thay bằng URL dài thì
            # citation hiện nguyên đường link, rất khó đọc.
            if key_lower == "source":
                key_lower = "url"
            metadata[key_lower] = value.strip()

        documents.append({"content": content_part.strip(), "metadata": metadata})
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đã chọn (RecursiveCharacterTextSplitter).

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    # Sử dụng RecursiveCharacterTextSplitter vì nó linh hoạt với nhiều loại
    # cấu trúc văn bản, cố gắng tách theo các dấu ngắt tự nhiên trước.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "##", "#", ". ", " ", ""],
        length_function=len,
    )
    chunks = []
    dropped = 0
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            if _is_junk_chunk(chunk_text):
                dropped += 1
                continue
            # Mỗi chunk kế thừa metadata của document gốc
            chunk_metadata = doc["metadata"].copy()
            chunk_metadata["chunk_index"] = i
            chunks.append({"content": chunk_text, "metadata": chunk_metadata})

    if dropped:
        print(f"  - Đã loại {dropped} chunk rác (boilerplate/link/tên shop)")
    return chunks


# Ngưỡng lọc chunk rác
MIN_CHUNK_CHARS = 80          # ngắn hơn thì không đủ ngữ cảnh để trả lời gì
MAX_NON_TEXT_RATIO = 0.35     # tỉ lệ ký tự không phải chữ/khoảng trắng

# Dấu hiệu chunk là phần chân trang / thủ tục, không phải nội dung quy định.
# Đo thực tế: chunk chứa khối chữ ký + "Liên hệ:" của Quy chế hoạt động sàn đứng TOP-1
# cho câu hỏi "hồ sơ đăng ký hộ kinh doanh" — hoàn toàn không liên quan.
BOILERPLATE_MARKERS = (
    "đã ký và đóng dấu",
    "liên hệ: https",
    "bản cập nhật ngày",
    "vui lòng bấm vào đây",
    "phiên bản này có hiệu lực sau",
    "để tham khảo phiên bản trước",
)
MAX_BOILERPLATE_HITS = 2      # dính từ 2 dấu hiệu trở lên thì coi là chân trang


def _is_junk_chunk(text: str) -> bool:
    """
    Bỏ những chunk không mang thông tin trả lời được.

    Vì sao cần: đo thực tế trên corpus này, chunk kiểu "Nội\\n\\nLiên hệ: https://..."
    hoặc danh sách tên shop ("vnhobbyshop_njyhb327n Hitachivietnam.store...") lại
    đứng TOP cho câu hỏi "hồ sơ đăng ký hộ kinh doanh". Lý do: chúng ngắn và
    không có chủ đề rõ nên vector nằm gần giữa không gian, "trung tính" với mọi query.
    Chúng vừa đẩy chunk hữu ích ra khỏi top_k, vừa kéo điểm câu hỏi lạc đề lên cao
    làm ngưỡng fallback ở Task 9 mất tác dụng.
    """
    stripped = text.strip()
    if len(stripped) < MIN_CHUNK_CHARS:
        return True

    # Chunk mà phần lớn là URL
    without_urls = re.sub(r"https?://\S+", "", stripped)
    if len(without_urls.strip()) < MIN_CHUNK_CHARS:
        return True

    # Chunk toàn ký hiệu/mã/tên tài khoản, ít chữ thật
    letters = sum(1 for c in stripped if c.isalpha() or c.isspace())
    if letters / len(stripped) < (1 - MAX_NON_TEXT_RATIO):
        return True

    # Chunk không có lấy một câu hoàn chỉnh (không có khoảng trắng đủ nhiều)
    if stripped.count(" ") < 10:
        return True

    # Chân trang / khối chữ ký — là văn bản thật nên không lọc được bằng hình dạng,
    # phải nhận diện bằng dấu hiệu nội dung.
    #
    # Hai bước chuẩn hoá BẮT BUỘC trước khi so marker:
    #
    # 1. Gộp khoảng trắng — text trích từ PDF hay dính khoảng trắng đôi và xuống dòng
    #    giữa câu ("TMĐT  qua  https", "Bản \nCập Nhật ngày").
    # 2. Chuẩn hoá Unicode về NFC — đây là cái bẫy khó thấy nhất: text từ MarkItDown
    #    lẫn cả dạng NFD (dấu tiếng Việt là ký tự tổ hợp rời) lẫn NFC (dựng sẵn).
    #    Hai chuỗi nhìn GIỐNG HỆT nhau trên màn hình nhưng `"liên hệ" in text` trả về
    #    False. Không có bước này thì mọi bộ lọc/so khớp chuỗi tiếng Việt đều
    #    trượt ngẫu nhiên.
    lowered = unicodedata.normalize("NFC", re.sub(r"\s+", " ", stripped)).lower()
    hits = sum(1 for m in BOILERPLATE_MARKERS if unicodedata.normalize("NFC", m) in lowered)
    if hits >= MAX_BOILERPLATE_HITS:
        return True

    return False


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng OpenAI text-embedding-3-small (batch processing).

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    print(f"Embedding {len(chunks)} chunks với {EMBEDDING_MODEL} "
          f"(provider={EMBEDDING_PROVIDER}, dim={EMBEDDING_DIM})...")

    texts = [c["content"] for c in chunks]
    vectors = embed_texts(texts, show_progress=True)

    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector

    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store ChromaDB.
    Xoá collection cũ nếu tồn tại để đảm bảo dữ liệu sạch.
    """
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Xoá collection cũ để tránh dữ liệu rác từ lần chạy trước
    print(f"Checking for existing collection '{COLLECTION_NAME}' to delete.")
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"  - Deleted existing collection '{COLLECTION_NAME}'.")
    except Exception:
        # chromadb >=1.0 ném chromadb.errors.NotFoundError chứ không phải ValueError;
        # bắt rộng để không phụ thuộc vào loại exception của từng phiên bản.
        print(f"  - Collection '{COLLECTION_NAME}' not found, skipping deletion.")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # Sử dụng cosine distance
    )

    if not chunks:
        print("No chunks to index.")
        return

    ids = [f"{c['metadata']['source']}_{c['metadata']['chunk_index']}" for c in chunks]

    # Upsert theo batch để tránh lỗi với ChromaDB khi có quá nhiều documents
    batch_size = 500
    for i in range(0, len(chunks), batch_size):
        batch_end = i + batch_size
        print(f"Upserting batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size} ({len(ids[i:batch_end])} chunks)")
        collection.add(
            ids=ids[i:batch_end],
            documents=[c["content"] for c in chunks[i:batch_end]],
            embeddings=[c["embedding"] for c in chunks[i:batch_end]],
            metadatas=[c["metadata"] for c in chunks[i:batch_end]],
        )


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()
