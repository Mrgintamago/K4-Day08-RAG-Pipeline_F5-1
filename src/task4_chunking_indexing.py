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
from pathlib import Path
from openai import OpenAI

import chromadb
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv() # Load environment variables from .env
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# EMBEDDING_PROVIDER: Chọn nhà cung cấp embedding.
#   - "openai": Sử dụng OpenAI API trực tiếp (cần OPENAI_API_KEY)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")

# OpenAI text-embedding-3-small: 1536 dimensions
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

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
        except ValueError:
            print(f"Chroma collection '{COLLECTION_NAME}' not found. Please run task4 to create it.")
            # Trả về None hoặc raise lỗi để báo hiệu collection chưa sẵn sàng
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
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            # Mỗi chunk kế thừa metadata của document gốc
            chunk_metadata = doc["metadata"].copy()
            chunk_metadata["chunk_index"] = i
            chunks.append({"content": chunk_text, "metadata": chunk_metadata})
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng OpenAI text-embedding-3-small (batch processing).

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    print(f"Embedding {len(chunks)} chunks với {EMBEDDING_MODEL}...")

    batch_size = 200
    for i in range(0, len(chunks), batch_size):
        batch_end = min(i + batch_size, len(chunks))
        batch_chunks = chunks[i:batch_end]
        texts = [c["content"] for c in batch_chunks]

        print(f"  Batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size} ({len(texts)} chunks)")

        response = _client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )

        for chunk, embedding_obj in zip(batch_chunks, response.data):
            chunk["embedding"] = embedding_obj.embedding

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
    except ValueError:
        print(f"  - Collection '{COLLECTION_NAME}' not found, skipping deletion.")
        pass  # Collection does not exist, which is fine

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
