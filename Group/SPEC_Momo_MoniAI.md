# AI Product Canvas — MoMo - Moni AI Financial Assistant

## Canvas

| | Value | Trust | Feasibility |
|--|--|--|--|
| Core | **User:** Người dùng MoMo có nhu cầu quản lý chi tiêu cá nhân, phát sinh nhiều giao dịch nhỏ mỗi ngày. **Pain:** Không nhớ mình đã tiêu gì, ngại nhập tay, báo cáo tài chính cá nhân thiếu đầy đủ vì nhiều khoản chi ngoài MoMo không được ghi lại. **Value:** AI gợi ý danh mục giao dịch và hỗ trợ nhập nhanh bằng ngôn ngữ tự nhiên, giúp giảm thời gian ghi chép, tăng độ đầy đủ dữ liệu, và tạo báo cáo chi tiêu hữu ích hơn. | **Khi sai:** AI gán sai danh mục, làm báo cáo sai, user hiểu sai hành vi tài chính của mình. **User biết sai bằng cách nào:** Thường chỉ phát hiện khi xem lại giao dịch hoặc thấy báo cáo bất hợp lý. **Explain:** Hiện trạng chưa giải thích rõ vì sao AI chọn danh mục đó. **Sửa:** User phải vào giao dịch và sửa category, khoảng 3–4 bước. | **Architecture:** Hybrid (Rule-based cho merchant quen thuộc, LLM với GPT-4o-mini cho text tự nhiên). **Cost:** khoảng 0.0005–0.002 USD/request. **Latency:** khoảng 300ms–1s. **Risk:** cost scale nếu gọi LLM mọi request; output không ổn định; hallucination nhẹ; data thiếu làm AI vẫn đoán sai. |
| Then chốt | **Augmentation** — AI gợi ý, user quyết định cuối cùng. Nếu để automation hoàn toàn, user có thể không biết AI sai và hiểu sai tình hình tài chính, rất nguy hiểm với bài toán tiền bạc. | **4-path:** xem phần User stories dưới. Hướng tin cậy nên là AI biết khi nào không chắc và hỏi lại nhẹ thay vì luôn tự quyết. | **Precision + trust first cho trải nghiệm tài chính cá nhân.** Sai âm thầm nguy hiểm hơn hơi phiền vì phải xác nhận. Đồng thời cần giữ recall đủ tốt để không bỏ sót giao dịch cần phân loại. |

## Learning signal

| # | Câu hỏi | Trả lời |
|--|--|--|
| 1 | Correction đi vào đâu? | Khi user sửa category, hệ thống ghi correction log và update mapping như `(merchant / keyword / note / user pattern -> category)`. Có thể dùng để cập nhật rule và retrain định kỳ. |
| 2 | Thu signal gì? | **Implicit:** acceptance rate, tỷ lệ user giữ nguyên gợi ý. **Explicit:** sửa nhãn, reject gợi ý, có thể thêm thumbs down nếu UI hỗ trợ. **Alert:** khi acceptance rate giảm >10% theo tuần hoặc correction rate tăng mạnh. |
| 3 | Data loại nào? | **User-specific + Human-judgment + Real-time.** Marginal value cao vì mô hình chung không biết thói quen chi tiêu cá nhân; cùng một merchant hoặc cùng một kiểu chuyển tiền có thể mang ý nghĩa khác nhau với từng user. |

## User stories — 4 paths

Feature: Gợi ý danh mục giao dịch. Trigger: có giao dịch mới hoặc user nhập chi tiêu bằng text tự nhiên -> AI phân tích -> gợi ý category.

| Path | Diễn biến |
|--|--|
| Happy | User thanh toán “Highlands Coffee 45k” -> AI gợi ý `Ăn uống` (95%) -> hiện badge danh mục + xác nhận nhẹ “Đã xếp vào Ăn uống” -> user tiếp tục, không cần sửa. |
| Low-confidence | User nhập “chuyển 200k cho Linh” -> AI chỉ chắc 55% vì thiếu ngữ cảnh -> hiện 2–3 lựa chọn như `Ăn uống / Quà tặng / Khác` + độ tự tin -> user chọn `Quà tặng`. |
| Failure | User chuyển tiền cho bạn để góp quỹ sinh nhật nhưng AI gắn `Ăn uống` với confidence cao -> user không nhận ra ngay -> cuối tháng báo cáo sai, khiến user đánh giá sai thói quen chi tiêu. |
| Correction | User mở lại giao dịch, đổi từ `Ăn uống` sang `Quà tặng` -> correction được ghi vào log -> hệ thống cập nhật mapping / retrain định kỳ -> lần sau các giao dịch tương tự được gợi ý đúng hơn. |

## Eval

Định hướng đánh giá: **trust-first / precision-first** ở các gợi ý confidence cao. Với các case confidence thấp, sản phẩm nên hỏi lại để tránh sai âm thầm.

| Metric | Threshold | Red flag |
|--|--|--|
| Precision ở high-confidence suggestions | >=90% | <80% trong 3 ngày liên tiếp |
| Acceptance rate | >=75% | <60% -> gợi ý trở nên vô dụng |
| Correction rate | <=15% | >25% -> user mất tin |
| Low-confidence resolution success | >=85% | <70% -> UI hỏi lại chưa hiệu quả |
| P95 latency | <=1s | >2s -> UX bị chậm rõ rệt |

## Failure modes

| # | Trigger | Hậu quả | Mitigation |
|--|--|--|--|
| 1 | Giao dịch mơ hồ, cùng một người nhận nhưng nhiều mục đích khác nhau | AI gán sai với confidence cao, user không biết | Thêm confidence threshold; nếu thiếu ngữ cảnh thì hỏi lại thay vì auto-assign |
| 2 | Dữ liệu nhạy cảm gửi qua external API | Rủi ro lộ thông tin tài chính cá nhân | Redact / mask PII trước khi gửi; Sử dụng On-device Model cho các task phân loại đơn giản hoặc dùng Private Instance LLM trên hạ tầng nội bộ; tối thiểu hóa payload; log an toàn |
| 3 | User mới, chưa có correction history | AI cá nhân hóa kém, gợi ý yếu | Cold-start bằng rule-based + merchant defaults trong 2 tuần đầu |
| 4 | User không nhập chi tiêu ngoài MoMo | Dữ liệu không đầy đủ, báo cáo sai lệch | Thiết kế quick add bằng text/chat; nhắc nhập nhanh, giảm friction |
| 5 | LLM output không ổn định | Cùng input nhưng category khác nhau | Chuẩn hóa prompt, ép output schema, có post-processing rules |

## ROI

Ước lượng theo order-of-magnitude (phương pháp ước lượng nhanh giá trị mà không cần chính xác tuyệt đối), dùng để ra quyết định chứ không phải số tài chính chính thức.

- **Giả định bảo thủ:**
  - 200,000 daily active users của feature
  - mỗi user tiết kiệm 20 giây/ngày nhờ auto classify + quick correction
  - tổng thời gian tiết kiệm: khoảng 1,111 giờ/ngày
  - nếu quy đổi giá trị thời gian người dùng ở mức thấp, feature tạo ra lợi ích nhận thức rõ ràng và tăng stickiness
- **Giả định sản phẩm:**
  - tăng tỷ lệ dùng lại feature quản lý chi tiêu
  - tăng độ đầy đủ dữ liệu -> báo cáo hữu ích hơn -> tăng retention của nhóm user quản lý tài chính cá nhân
- **Chi phí vận hành LLM:**
  - 100K req/day -> khoảng 50–200 USD/day
  - 1M req/day -> khoảng 500–2000 USD/day
- **Kết luận ROI:** khả thi nếu chỉ gọi GPT-4o-mini cho case cần hiểu ngữ nghĩa; nên hybrid với rule-based để giữ cost thấp.

## Kill criteria

- Acceptance rate <50% sau 1 tháng kể từ launch
- Correction rate >30% liên tục 2 tuần
- P95 latency >2s mà không cải thiện được
- Cost LLM > benefit 2 tháng liên tục
- Tỷ lệ user quay lại feature không tăng dù đã cải thiện trust UX

## Sketch cải thiện path yếu nhất

**Path yếu nhất:** AI không chắc nhưng hiện tại vẫn đoán.

**As-is:**
- User giao dịch -> AI auto classify -> user không biết AI đang đoán -> nếu sai thì data sai và trust giảm.

**To-be:**
- User giao dịch -> AI classify + confidence
- Nếu confidence cao -> auto assign + confirm nhẹ
- Nếu confidence thấp -> hỏi lại ngắn “Mình chưa chắc, đây là gì?” + 2–3 lựa chọn nhanh
- Sau khi user chọn -> hỏi “Nhớ cho lần sau?” -> lưu correction vào learning loop.

## Phân chia công việc cho team A4-C401

| Thành viên | Vai trò chính | Phạm vi công việc | Deliverable |
|--|--|--|--|
| Hoàng Quốc Chung - 2A202600070 | Tổng hợp & điều phối | Chốt đề tài MoMo - Trợ thủ AI Moni, giữ cấu trúc bài, tổng hợp đầu ra từ cả nhóm, rà soát logic toàn bộ canvas | Bản final `canvas.md` hoàn chỉnh |
| Trịnh Đức Anh - 2A202600499 | Research sản phẩm & value | Tìm hiểu promise của MoMo AI, pain point người dùng, xác định user, value proposition, core problem | Phần `Canvas > Value` |
| Bùi Văn Đạt - 2A202600355 | Trust & UX analysis | Phân tích trải nghiệm thực tế, 4 paths (happy / low-confidence / failure / correction), trust gap giữa marketing và thực tế | Phần `Canvas > Trust` và `User stories — 4 paths` |
| Dương Văn Hiệp - 2A202600052 | Feasibility & risk | Đề xuất kiến trúc LLM-first với GPT-4o-mini, ước lượng cost/latency, nêu dependencies và failure modes kỹ thuật | Phần `Canvas > Feasibility`, `Failure modes` |
| Hoàng Thái Dương - 2A202600073 | Learning & evaluation | Xác định correction loop, learning signal, metric đánh giá, threshold, red flags, kill criteria | Phần `Learning signal`, `Eval`, `Kill criteria` |
| Nguyễn Minh Quân - 2A202600181 | ROI & sketch | Viết phần ROI, kết luận sản phẩm, và sketch cải thiện path yếu nhất theo As-is / To-be | Phần `ROI` và `Gợi ý sketch cải thiện path yếu nhất` |