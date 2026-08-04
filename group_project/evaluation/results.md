# RAG Evaluation Results

- Framework: **RAGAS 0.1.21**
- Judge model: **gpt-4o-mini**
- Generation: **openai / gpt-4o-mini**
- Số câu đánh giá mỗi cấu hình: **16**
- Số context mỗi câu (top-k): **3**
- Thời điểm chạy: **2026-08-04T18:17:37+07:00**

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------:|----------------------:|--:|
| Faithfulness | 0.8708 | 0.5599 | +0.3109 |
| Answer Relevance | 0.6077 | 0.4288 | +0.1788 |
| Context Recall | 0.9792 | 0.8363 | +0.1429 |
| Context Precision | 1.0000 | 1.0000 | +0.0000 |
| **Average** | **0.8644** | **0.7063** | **+0.1582** |

## A/B Comparison Analysis

- **Config A:** semantic + BM25, gộp và rerank bằng RRF.
- **Config B:** semantic search thuần, không BM25 và không RRF.
- **Kết luận:** Config A (hybrid + rerank) có điểm trung bình bốn metric cao hơn 0.1582. Kết luận dựa trên cùng tập câu hỏi và cùng LLM judge; xem worst performers để xác định retrieval, ranking hay generation là nút thắt chính.

## Worst Performers (Bottom 3 của Config A)

| # | Question | Faithfulness | Relevance | Recall | Precision | Failure Stage | Root Cause |
|--:|----------|-------------:|----------:|-------:|----------:|---------------|------------|
| 1 | Theo Điều 8 Luật Bảo vệ quyền lợi người tiêu dùng, người tiêu dùng có những quyền cơ bản nào? | 0.0000 | 0.0000 | 1.0000 | 1.0000 | Generation | Câu trả lời chưa bám chặt các context đã truy xuất. |
| 2 | Công ty trách nhiệm hữu hạn một thành viên do tổ chức làm chủ sở hữu có bắt buộc phải thành lập Ban kiểm soát không? | 1.0000 | 0.0000 | 0.6667 | 1.0000 | Generation | Câu trả lời chưa tập trung trực tiếp vào ý hỏi. |
| 3 | Thông tin thanh toán và thông tin thuế của đối tác Shopee Affiliate phải đạt trạng thái nào mới có hiệu lực, và có hiệu lực từ khi nào? | 1.0000 | 0.0000 | 1.0000 | 1.0000 | Generation | Câu trả lời chưa tập trung trực tiếp vào ý hỏi. |

## Recommendations

1. Rút gọn câu trả lời và nhắc lại đúng phạm vi câu hỏi; kỳ vọng tăng answer relevance.
2. Siết prompt grounding và kiểm tra citation theo từng mệnh đề; kỳ vọng tăng faithfulness.
3. Tăng candidate pool hoặc thêm query expansion cho câu hỏi điều luật; kỳ vọng giảm bỏ sót evidence.
