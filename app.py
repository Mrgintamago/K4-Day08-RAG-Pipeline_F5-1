"""
RAG Chatbot — Trợ Lý Pháp Lý Khởi Nghiệp & Thương Mại Điện Tử
Streamlit app kết nối RAG Retrieval (Task 9) và Generation (Task 10).

Chủ đề #2 trong SUGGESTED_TOPICS.md. Corpus 2 lớp:
    - Văn bản luật (Wikisource): trả lời "pháp luật bắt tôi làm gì"
    - Quy định sàn (help.shopee.vn): trả lời "sàn bắt tôi làm gì"
Citation nên in kèm doc_type để người dùng phân biệt hai loại — khác biệt này
quan trọng về mặt pháp lý.

Chạy:
    streamlit run app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Thêm project root vào sys.path để import các task từ src/
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Trợ Lý Pháp Lý Khởi Nghiệp & TMĐT",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# SIDEBAR — INFO & SETTINGS
# =============================================================================

with st.sidebar:
    st.title("⚖️ Trợ Lý Pháp Lý Khởi Nghiệp & TMĐT")
    st.caption("Hỏi đáp về quy định pháp lý khi bán hàng online: thuế, đăng ký kinh doanh, quy định sàn TMĐT, quyền người tiêu dùng")

    st.divider()

    # Câu hỏi gợi ý bám 4 nhóm chủ đề của golden dataset (PLAN.md §1.5),
    # để demo chạm được cả 2 lớp corpus: văn bản luật và quy định sàn.
    st.subheader("💡 Câu hỏi gợi ý")
    suggestions = [
        "Bán hàng online doanh thu bao nhiêu thì phải nộp thuế TNCN?",
        "Hồ sơ đăng ký hộ kinh doanh cá thể gồm những giấy tờ gì?",
        "Những mặt hàng nào bị cấm đăng bán trên Shopee?",
        "Người tiêu dùng có quyền trả hàng trong bao lâu?",
        "Công ty TNHH một thành viên có bắt buộc có Ban kiểm soát không?",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=f"sug_{s[:20]}"):
            st.session_state["pending_query"] = s

    st.divider()
    st.subheader("⚙️ Thiết lập")
    top_k = st.slider("Số chunks retrieval (top_k)", 3, 10, 5)

    st.divider()
    st.caption("**Kiến trúc hệ thống:**")
    st.caption("Hybrid Retrieval (Semantic + BM25) → RRF Rerank → PageIndex Fallback → LLM Generation có Citation")

# =============================================================================
# SESSION STATE
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# =============================================================================
# MAIN CHAT AREA
# =============================================================================

st.title("⚖️ Trợ Lý Pháp Lý Khởi Nghiệp & TMĐT")
st.caption("Hỏi đáp dựa trên văn bản luật Việt Nam và quy định sàn thương mại điện tử — mọi câu trả lời đều kèm trích dẫn nguồn")

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander(f"📚 Nguồn tham khảo ({len(msg['sources'])} chunks)"):
                for i, src in enumerate(msg["sources"], 1):
                    meta = src.get("metadata", {})
                    source_name = meta.get("source", "Unknown")
                    doc_type = meta.get("type", "unknown")
                    score = src.get("score", 0)
                    st.markdown(f"**[{i}] {source_name}** `{doc_type}` | score: `{score:.4f}`")
                    st.text(src.get("content", "")[:300] + "...")
                    st.divider()

# =============================================================================
# QUERY HANDLING
# =============================================================================

user_input = st.chat_input("Nhập câu hỏi của bạn về chính sách/hỗ trợ e-commerce...")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Sinh câu trả lời từ RAG Pipeline
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời..."):
            try:
                # TODO (Học viên): Tích hợp hàm sinh câu trả lời từ Task 10
                # Ví dụ:
                # from src.task10_generation import generate_with_citation
                # response = generate_with_citation(query, top_k=top_k)
                # answer = response["answer"]
                # sources = response.get("sources", [])

                from src.task10_generation import generate_with_citation
                response = generate_with_citation(query, top_k=top_k)
                answer = response.get("answer", "Chưa thể trả lời.")
                sources = response.get("sources", [])

            except NotImplementedError:
                answer = "⚠️ **Task 10 chưa được implement.** Hãy hoàn thành `src/task10_generation.py` để kết nối pipeline vào UI!"
                sources = []
            except Exception as e:
                answer = f"❌ **Lỗi khi chạy RAG Pipeline:** {e}"
                sources = []

            st.markdown(answer)

            if sources:
                with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks)"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", "Unknown")
                        doc_type = meta.get("type", "unknown")
                        score = src.get("score", 0)
                        st.markdown(f"**[{i}] {source_name}** `{doc_type}` | score: `{score:.4f}`")
                        st.text(src.get("content", "")[:300] + "...")
                        st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
