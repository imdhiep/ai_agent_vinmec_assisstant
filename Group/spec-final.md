**SPEC draft - A4 - C401**

## Track: Vinmec
Ý tưởng: Vinmec AI Patient Booking Copilot


## Problem statement
+ Bệnh nhân: Không biết triệu chứng của mình nên khám khoa nào, bác sĩ nào phù hợp và lúc nào trống lịch → Dễ gây hoang mang cho bệnh nhân, lễ tân dễ bị quá tải với nhiều câu hỏi lặp lại.

+ Bệnh viện: Bệnh nhân khám sai khoa và phân bổ lịch khám không đồng đều → Gây lãng phí nguồn lực, tốn thời gian.


## AI Product Canvas

**Value (Giá trị)**: Giảm sự mơ hồ của bệnh nhân thông qua việc điều hướng đúng khoa chuyên môn ngay từ đầu. Tăng hiệu quả vận hành bệnh viện bằng cách tối ưu hóa lịch trống của bác sĩ và phòng khám.

**Trust (Tin cậy)**: AI giải thích lý do đề xuất khoa dựa trên triệu chứng. Hiển thị trạng thái sẵn sàng thực tế (Real-time availability). Luôn kèm Disclaimer: "AI hỗ trợ điều hướng, không thay thế chẩn đoán lâm sàng".

**Feasibility (Khả thi)**: Sử dụng LLM (GPT-4o/Claude) kết hợp RAG trên bộ danh mục khoa/phòng và kỹ năng chuyên biệt của bác sĩ Vinmec. Tích hợp API lịch khám hiện có.

**Learning Signal (Tín hiệu học tập)**: Tỉ lệ bệnh nhân nhấn "Đặt lịch" sau khi được AI tư vấn; Phản hồi của bác sĩ về mức độ chính xác của tóm tắt triệu chứng mà AI gửi tới.

Augmentation (Hỗ trợ người dùng) — TRỌNG TÂM
Vấn đề: Bệnh nhân mơ hồ về chuyên môn y khoa.

Cách giải quyết: AI không tự ý "chốt" bệnh hay bắt bệnh nhân đi khám. Nó đóng vai trò Copilot để:

Phân tích triệu chứng và gợi ý (Suggest) khoa phù hợp.

Cung cấp thông tin để bệnh nhân tự ra quyết định chọn bác sĩ dựa trên độ tương thích (Match Score).

Mục tiêu: Tăng năng lực hiểu biết cho bệnh nhân (Clarity).

## User Stories (4 paths)
**Happy Path (Thành công)**: Bệnh nhân nhập "đau bụng, buồn nôn" -> AI xác định Khoa Tiêu hóa -> AI check thấy bác sĩ A đang trống lịch -> Bệnh nhân đặt lịch thành công trong 1 phút.

**Low-confidence Path (Cần xác nhận)**: Khi bệnh nhân cung cấp nhiều triệu chứng, hệ thống sẽ phân nhóm và sắp xếp theo mức độ ưu tiên lâm sàng. Các triệu chứng có nguy cơ cao sẽ được sàng lọc trước. Chỉ sau khi loại trừ nguy cơ khẩn cấp, hệ thống mới tiếp tục gợi ý chuyên khoa phù hợp cho phần triệu chứng còn lại.

**Failure Path (Từ chối/Chuyển hướng)**: Trong những trường hợp: bệnh nhân có triệu chứng quá phức tạp, thông tin không đủ để định hướng an toàn, có yêu cầu đặc biệt ngoài phạm vi agent, AI không tìm được phương án đặt lịch phù hợp, cần nhân viên hỗ trợ -> AI không tự xử lý tiếp và cần chuyển sang người thật / kênh phù hợp / quy trình phù hợp hơn.

**Correction Path (Sửa lỗi)**: AI gợi ý khoa Sản cho bệnh nhân nam (do nhầm lẫn từ khóa) -> Bệnh nhân phản hồi "Tôi là nam" -> AI xin lỗi, cập nhật context và gợi ý lại khoa Thận tiết niệu.

##  Eval Metrics
Metric 1 - Routing Accuracy (Độ chính xác điều hướng): > 90% bệnh nhân được AI gợi ý đúng khoa chuyên môn (đối chiếu với chẩn đoán cuối cùng của bác sĩ).

Metric 2 - Booking Friction (Độ mượt đặt lịch): Thời gian hoàn thành đặt lịch < 90 giây.

Metric 3 - Availability Match (Độ khớp lịch): 100% bác sĩ được gợi ý phải đang có trạng thái "Available" hoặc "Next slot" rõ ràng.

🚩 Red Flag: AI chẩn đoán sai các triệu chứng thuộc nhóm nguy cơ tử vong cao (Red Flags y tế) thành bệnh nhẹ.

## Top 3 Failure Modes (Trigger/Hậu quả/Mitigation)
Trigger: Hệ thống API lịch khám của bệnh viện bị chậm/lỗi.
Hậu quả: AI gợi ý bác sĩ đã kín lịch, gây bức xúc khi bệnh nhân thanh toán/đến nơi.
Mitigation: Thiết kế cache dữ liệu lịch khám mỗi 30s và hiển thị dòng chữ "Cập nhật 30 giây trước".

Trigger: Bệnh nhân dùng thuật ngữ địa phương hoặc mô tả quá mơ hồ.
Hậu quả: AI gợi ý sai khoa (Wrong routing).
Mitigation: AI không được đoán mò; nếu độ tự tin (confidence score) < 70%, AI phải đưa ra các câu hỏi trắc nghiệm để bệnh nhân chọn.

Trigger: Bệnh nhân quá tin vào AI và tự điều trị tại nhà.
Hậu quả: Bỏ lỡ thời gian vàng điều trị.
Mitigation: Luôn hiển thị nút "Kết nối với tư vấn viên thật" và nhắc nhở "Khám trực tiếp là bắt buộc".

## ROI 3 kịch bản
**Conservative (Thận trọng)**: Giảm 15% tải trọng cho Call Center của Vinmec nhờ khách hàng tự đặt lịch qua AI.

**Realistic (Thực tế)**: Giảm 30% tỉ lệ bệnh nhân khám sai khoa; Tăng 10% doanh thu nhờ lấp đầy các khung giờ trống của bác sĩ thông qua gợi ý thông minh.

**Optimistic (Lạc quan)**: Trở thành cổng vào duy nhất (Smart Gate) của Vinmec, tăng tỉ lệ giữ chân bệnh nhân (Retention) nhờ trải nghiệm khám bệnh "không ma sát".

## Mini AI Spec (1 trang)
Mô hình: RAG Agentic Workflow.

Input: Văn bản mô tả triệu chứng, độ tuổi, giới tính, lịch sử khám (nếu có).

Process: 1. Phân loại triệu chứng.
2. Mapping với sơ đồ khoa phòng Vinmec.
3. Query API lịch trống.
4. Rank bác sĩ dựa trên chuyên môn phù hợp nhất.

Output: Tên Khoa + Danh sách bác sĩ kèm trạng thái trống lịch + Link đặt lịch nhanh.

## Phân công 
Quân:  Problem Statement, Mini AI Spec
Chung: Canvas
Dương: Evalution Metric
Đức Anh: User Story
Đạt: Top 3 Failing Models
Hiệp: ROI 3 Kịch Bản
