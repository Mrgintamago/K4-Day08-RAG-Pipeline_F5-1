"""
RAG Chatbot — Trợ Lý AI Pháp Lý TMĐT 
Streamlit app.
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# PAGE CONFIG & STRICT PIXEL-MATCHING CUSTOM CSS
# =============================================================================

st.set_page_config(
    page_title="Trợ lý AI Pháp Lý TMĐT",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

    /* Global Reset & Background */
    html, body, [class*="css"], .stApp {
        background-color: #070b15 !important;
        color: #e2e8f0 !important;
        font-family: 'Be Vietnam Pro', sans-serif !important;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0px !important;
    }

    /* Sidebar Background & Styling */
    section[data-testid="stSidebar"] {
        background-color: #070b15 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
        width: 300px !important;
    }

    /* Status Indicator */
    .status-row {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.72rem;
        font-weight: 700;
        color: #94a3b8;
        letter-spacing: 0.6px;
        margin-bottom: 20px;
    }
    .green-dot-pulse {
        height: 9px;
        width: 9px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
    }

    /* Sidebar Rows & Labels */
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.76rem;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .metric-val {
        font-weight: 700;
        color: #ffffff;
    }
    
    .sidebar-divider {
        height: 1px;
        background-color: rgba(255, 255, 255, 0.07);
        margin: 20px 0;
    }

    .section-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #64748b;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    /* Customizing Streamlit Radio to match Role Selector Pills */
    div[data-testid="stRadio"] > label {
        display: none !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        color: #94a3b8 !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        margin: 0 !important;
        transition: all 0.2s ease;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"] {
        background-color: #0e2042 !important;
        border: 1px solid #1d4ed8 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    /* Hide Radio Circle */
    div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }

    /* Custom Streamlit Progress Bar */
    .stProgress > div > div > div > div {
        background-color: #2563eb !important;
        border-radius: 4px !important;
    }
    .stProgress > div > div {
        background-color: #1e293b !important;
        border-radius: 4px !important;
        height: 5px !important;
    }

    /* Header Bar */
    .header-container-dark {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 24px;
        padding-top: 4px;
    }
    .main-title-text {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1.2;
    }
    .main-sub-text {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 4px;
    }
    .top-badge-group {
        display: flex;
        gap: 12px;
    }
    .top-badge-item {
        background-color: #111726;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
        padding: 8px 18px;
        border-radius: 20px;
        font-size: 0.84rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* User Chat Bubble (Top-Right Aligned) */
    .user-bubble-exact {
        background-color: #2563eb;
        color: #ffffff;
        padding: 16px 20px;
        border-radius: 16px 16px 2px 16px;
        font-size: 0.94rem;
        line-height: 1.5;
        margin-bottom: 24px;
        margin-left: auto;
        max-width: 82%;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35);
        font-weight: 500;
    }

    /* AI Response Card Container */
    .ai-card-exact {
        background-color: #0f1527;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
    }
    .ai-avatar-circle {
        background-color: #3b82f6;
        color: #ffffff;
        font-weight: 800;
        font-size: 0.8rem;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .ai-body-text {
        color: #cbd5e1;
        font-size: 0.92rem;
        line-height: 1.6;
    }
    .ai-body-text p {
        margin-bottom: 12px;
    }
    .ai-body-text ul {
        margin-left: 18px;
        margin-bottom: 8px;
    }
    .ai-body-text li {
        margin-bottom: 6px;
    }

    /* Right Column: NGUỒN TRÍCH DẪN */
    .source-col-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 18px;
    }
    .source-col-title {
        font-size: 0.8rem;
        font-weight: 800;
        color: #64748b;
        letter-spacing: 0.8px;
    }
    .origin-badge {
        background-color: #044e39;
        color: #10b981;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
    }

    /* Citation Cards Vertical Stack */
    .citation-box-dark {
        background-color: #0f1527;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 14px;
    }
    .cite-top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .tag-blue {
        color: #38bdf8;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.5px;
    }
    .tag-purple {
        color: #818cf8;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.5px;
    }
    .tag-yellow {
        color: #facc15;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.5px;
    }
    .doc-id-gray {
        color: #64748b;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .cite-card-title {
        color: #ffffff;
        font-size: 0.88rem;
        font-weight: 700;
        line-height: 1.4;
        margin-bottom: 14px;
    }
    .cite-meter-row {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .cite-meter-track {
        flex-grow: 1;
        height: 5px;
        background-color: #1e293b;
        border-radius: 3px;
        overflow: hidden;
    }
    .fill-green {
        height: 100%;
        background-color: #10b981;
    }
    .fill-blue {
        height: 100%;
        background-color: #3b82f6;
    }
    .cite-match-number {
        font-size: 0.76rem;
        font-weight: 700;
        color: #94a3b8;
    }

    /* Custom Chat Input Box Styling */
    div[data-testid="stChatInput"] {
        background-color: #0d1222 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 4px 8px !important;
    }
    div[data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        font-size: 0.9rem !important;
    }
    div[data-testid="stChatInput"] button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 50% !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# =============================================================================
# SIDEBAR — CONTROL PANEL (Khớp 100% Sidebar hình ảnh)
# =============================================================================

with st.sidebar:
    # 1. Status Indicator
    st.markdown(
        """
    <div class="status-row">
        <span class="green-dot-pulse"></span> HỆ THỐNG SẴN SÀNG
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 2. Metric Rows
    st.markdown(
        """
    <div class="metric-row">
        <span>Độ trễ AI</span>
        <span class="metric-val">142ms</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.progress(0.2)

    st.markdown(
        """
    <div style="margin-top: 10px;" class="metric-row">
        <span>Sử dụng Token</span>
        <span class="metric-val">42%</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.progress(0.42)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # 3. NHÓM NGƯỜI DÙNG
    st.markdown('<div class="section-label">NHÓM NGƯỜI DÙNG</div>', unsafe_allow_html=True)
    user_group = st.radio(
        "Nhóm người dùng",
        options=["Chủ sàn TMĐT", "Người bán (Sellers)", "Người mua lẻ"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # 4. TÙY CHỈNH MÔ HÌNH
    st.markdown('<div class="section-label">TÙY CHỈNH MÔ HÌNH</div>', unsafe_allow_html=True)

    st.markdown(
        """
    <div class="metric-row">
        <span>Độ chính xác (Temp)</span>
        <span class="metric-val">0.2</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    temp_val = st.slider("Temp Slider", 0.0, 1.0, 0.2, 0.05, label_visibility="collapsed")

    st.markdown(
        """
    <div style="margin-top: 10px;" class="metric-row">
        <span>Phạm vi tra cứu</span>
        <span class="metric-val">Toàn quốc</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    scope_val = st.select_slider(
        "Scope Slider",
        options=["Địa phương", "Vùng", "Toàn quốc"],
        value="Toàn quốc",
        label_visibility="collapsed",
    )

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # 5. CÂU HỎI MẪU NỔI BẬT
    st.markdown('<div class="section-label">💡 CÂU HỎI MẪU NỔI BẬT</div>', unsafe_allow_html=True)
    
    if "Sellers" in user_group or "Người bán" in user_group:
        sample_queries = [
            "Quy định về việc đăng ký mã số thuế cho hộ kinh doanh cá thể trên sàn Shopee hiện nay như thế nào?",
            "Bán hàng online bao nhiêu doanh thu thì phải nộp thuế TNCN?",
            "Hồ sơ đăng ký hộ kinh doanh cá thể gồm những giấy tờ gì?",
        ]
    elif "Người mua" in user_group:
        sample_queries = [
            "Người tiêu dùng có quyền trả hàng trong bao lâu?",
            "Trường hợp nào được trả hàng hoàn tiền trên Shopee?",
        ]
    else:
        sample_queries = [
            "Trách nhiệm của thương nhân cung cấp sàn TMĐT theo NĐ 52?",
            "Quy định về kiểm duyệt sản phẩm cấm đăng bán?",
        ]

    for q in sample_queries:
        if st.button(q, use_container_width=True, key=f"sug_btn_{abs(hash(q))}"):
            st.session_state["pending_query"] = q
            st.rerun()

# =============================================================================
# TOP HEADER BAR
# =============================================================================

st.markdown(
    """
<div class="header-container-dark">
    <div>
        <h1 class="main-title-text">Trợ lý AI Pháp Lý TMĐT</h1>
        <div class="main-sub-text">Hệ thống phân tích luật định thời gian thực</div>
    </div>
    <div class="top-badge-group">
        <div class="top-badge-item">🏛️ 5 Văn Bản Luật</div>
        <div class="top-badge-item">🛍️ 26 Quy Định Sàn</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# =============================================================================
# SESSION STATE & INITIAL DEMO DATA
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# Nếu lịch sử chat trống, khởi tạo hội thoại chuẩn khớp 100% ảnh người dùng gửi
if not st.session_state.messages:
    exact_q = "Quy định về việc đăng ký mã số thuế cho hộ kinh doanh cá thể trên sàn Shopee hiện nay như thế nào?"
    exact_a = """Dựa trên **Nghị định 52/2013/NĐ-CP** và các cập nhật mới nhất từ **Thông tư 40/2021/TT-BTC**, việc đăng ký thuế đối với hộ kinh doanh trên sàn TMĐT được quy định như sau:

* Sàn TMĐT có trách nhiệm cung cấp thông tin người bán cho cơ quan thuế.
* Hộ kinh doanh phải có mã số thuế cá nhân hoặc mã số thuế hộ kinh doanh trước khi mở gian hàng.
* Mức thuế khoán áp dụng tùy thuộc vào doanh thu thực tế ghi nhận trên hệ thống sàn."""

    exact_sources = [
        {
            "tag": "PHÁP LUẬT",
            "tag_class": "tag-blue",
            "doc_id": "#NĐ-52",
            "title": "Nghị định 52/2013/NĐ-CP về Thương mại điện tử (Sửa đổi bởi NĐ 85/2021)",
            "match": 98,
            "fill": "fill-green",
        },
        {
            "tag": "QUY ĐỊNH SÀN",
            "tag_class": "tag-purple",
            "doc_id": "#SHOPEE-V1",
            "title": "Chính sách thuế và tuân thủ dành cho Người bán khu vực Việt Nam",
            "match": 85,
            "fill": "fill-blue",
        },
        {
            "tag": "THÔNG TƯ",
            "tag_class": "tag-yellow",
            "doc_id": "#TT-40",
            "title": "Thông tư 40/2021/TT-BTC hướng dẫn quản lý thuế hộ kinh doanh",
            "match": 94,
            "fill": "fill-green",
        },
    ]

    st.session_state.messages.append({"role": "user", "content": exact_q})
    st.session_state.messages.append({"role": "assistant", "content": exact_a, "sources": exact_sources})

# =============================================================================
# MAIN CONTENT AREA — 2 COLUMNS (CHAT VS NGUỒN TRÍCH DẪN)
# =============================================================================

col_chat, col_sources = st.columns([0.62, 0.38], gap="large")

with col_chat:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f"""
            <div class="user-bubble-exact">{msg['content']}</div>
            """,
                unsafe_allow_html=True,
            )
        elif msg["role"] == "assistant":
            st.markdown(
                """
            <div class="ai-card-exact">
                <div class="ai-avatar-circle">AI</div>
                <div class="ai-body-text">
            """,
                unsafe_allow_html=True,
            )
            st.markdown(msg["content"])
            st.markdown("</div></div>", unsafe_allow_html=True)

with col_sources:
    st.markdown(
        """
    <div class="source-col-header">
        <div class="source-col-title">NGUỒN TRÍCH DẪN</div>
        <div class="origin-badge">Dữ liệu Gốc</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    latest_msg = st.session_state.messages[-1] if st.session_state.messages else {}
    sources_to_render = latest_msg.get("sources", [])

    for idx, item in enumerate(sources_to_render[:3]):
        if "metadata" in item:
            meta = item.get("metadata", {})
            src_name = meta.get("source", "Tài liệu")
            doc_type = meta.get("doc_type", "legal_document")
            match_pct = int(item.get("score", 0.9) * 100)
            if match_pct > 100:
                match_pct = 95

            tag_title = "PHÁP LUẬT" if doc_type == "legal_document" else "QUY ĐỊNH SÀN"
            tag_class = "tag-blue" if doc_type == "legal_document" else "tag-purple"
            doc_id = f"#{meta.get('type', 'DOC')}"
            title_text = src_name
            fill_class = "fill-green" if match_pct >= 90 else "fill-blue"
        else:
            tag_title = item.get("tag", "PHÁP LUẬT")
            tag_class = item.get("tag_class", "tag-blue")
            doc_id = item.get("doc_id", "#DOC")
            title_text = item.get("title", "")
            match_pct = item.get("match", 90)
            fill_class = item.get("fill", "fill-green")

        st.markdown(
            f"""
        <div class="citation-box-dark">
            <div class="cite-top-bar">
                <span class="{tag_class}">{tag_title}</span>
                <span class="doc-id-gray">{doc_id}</span>
            </div>
            <div class="cite-card-title">{title_text}</div>
            <div class="cite-meter-row">
                <div class="cite-meter-track">
                    <div class="{fill_class}" style="width: {match_pct}%;"></div>
                </div>
                <span class="cite-match-number">{match_pct}%</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

# =============================================================================
# INPUT FIELD
# =============================================================================

user_input = st.chat_input("Hỏi về trách nhiệm pháp lý, thuế, hoặc quy định bảo hành...")
query = user_input or st.session_state.pending_query

if query and (not st.session_state.messages or query != st.session_state.messages[0]["content"]):
    st.session_state.pending_query = None

    # Thêm tin nhắn user
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("🔍 Đang phân tích luật định & truy xuất nguồn dữ liệu..."):
        try:
            from src.task10_generation import generate_with_citation

            # Lấy lịch sử hội thoại cho conversation memory (Task F5-15)
            prev_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []
            response = generate_with_citation(query, top_k=5, chat_history=prev_history)
            answer = response.get("answer", "Không thể tạo câu trả lời.")
            raw_sources = response.get("sources", [])
        except NotImplementedError:
            answer = "⚠️ **Task 10 chưa được implement.** Đang ở chế độ demo."
            raw_sources = []
        except Exception as e:
            answer = f"❌ **Lỗi RAG Pipeline:** {e}"
            raw_sources = []

    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": raw_sources})
    st.rerun()




