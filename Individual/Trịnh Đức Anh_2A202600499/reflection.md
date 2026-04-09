# Individual reflection — Trịnh Đức Anh (2A202600499)

## 1. Role
Phụ trách phần UX flow cho copilot đặt lịch và đóng góp nội dung cho phần kết luận/đề xuất triển khai trong SPEC. Trọng tâm cá nhân là biến ý tưởng "AI tư vấn khoa khám" thành một hành trình người dùng end-to-end rõ ràng, có thể demo được ngay, và không vượt quá scope hackathon.

## 2. Đóng góp cụ thể
- Viết và hoàn thiện phần định hướng triển khai trong SPEC theo hướng thực tế: ưu tiên luồng booking, giảm rủi ro vận hành, giữ nguyên nguyên tắc "AI hỗ trợ điều hướng, không thay thế bác sĩ".
- Thiết kế UI flow end-to-end cho trải nghiệm đặt lịch:
  1) Chọn cơ sở,  
  2) Nhập triệu chứng,  
  3) AI triage + hỏi lại khi thiếu thông tin,  
  4) Gợi ý chuyên khoa phù hợp,  
  5) Hiển thị bác sĩ và slot khả dụng,  
  6) Chốt yêu cầu đặt lịch.
- Chuẩn hóa demo flow để team trình bày mạch lạc theo các path quan trọng trong spec: happy path, low-confidence, failure/redirect, correction.
- Đóng góp phần prototype theo hướng "không ma sát": giảm số bước nhập tay, tăng phần thông tin tóm tắt để người dùng ra quyết định nhanh.

## 3. Cách mình chuyển từ SPEC sang trải nghiệm người dùng
Bám sát các nội dung trong `Group/spec-final.md` (problem, user stories, metrics, failure modes, ROI) và chuyển thành luồng màn hình cụ thể:
- **Từ user story sang màn hình:** mỗi story phải có trạng thái UI tương ứng, không chỉ dừng ở mô tả chữ.
- **Từ metric sang hành vi giao diện:** mục tiêu "booking friction < 90s" được chuyển thành thiết kế hiển thị rõ khoa + bác sĩ + slot ngay sau triage, tránh chuyển trang lòng vòng.
- **Từ failure mode sang guardrail UX:** nếu confidence thấp thì buộc có follow-up question thay vì trả lời mơ hồ; nếu có dấu hiệu khẩn cấp thì chuyển hướng ưu tiên an toàn.

Điểm mình thấy hiệu quả là team không còn tranh luận trừu tượng về "AI nên trả lời gì", mà có thể nhìn trực tiếp vào từng bước user đi qua.

## 4. Reflection cho phần kết luận/đề xuất triển khai
Khi viết phần kết luận triển khai, mình tập trung vào 3 nguyên tắc:
- **Làm chắc lõi trước:** triển khai tốt bài toán điều hướng khoa + đặt lịch cơ bản, chưa mở rộng sang chẩn đoán.
- **Tính khả thi vận hành:** dữ liệu lịch khám cần ổn định, có fallback khi API chậm/lỗi, và luôn hiển thị độ mới của dữ liệu.
- **Mở rộng theo giai đoạn:** pilot trên phạm vi hẹp trước, đo đúng 3 metric chính rồi mới nhân rộng.

Đề xuất này giúp SPEC cân bằng giữa tham vọng sản phẩm và giới hạn thời gian triển khai thực tế.

## 5. Demo script và UI flow/prototype - điều mình làm được
Mình chuẩn hóa kịch bản demo theo logic end-to-end để team bám theo khi thuyết trình:
- Mở đầu bằng pain point người bệnh không biết khám khoa nào.
- Chạy nhanh happy path để chứng minh giá trị.
- Chèn một case low-confidence để thể hiện agent biết hỏi lại.
- Kết thúc bằng case failure/redirect để chứng minh an toàn và tính thực dụng.

Về prototype/UI flow ưu tiên:
- Ngôn ngữ đơn giản, tránh thuật ngữ y khoa khó hiểu.
- Thông tin quyết định (khoa, bác sĩ, slot) hiển thị gần nhau.
- Có thông báo giới hạn trách nhiệm AI ở đúng điểm người dùng dễ hiểu nhất.

## 6. Điều học được
Mình học được rằng "viết spec tốt" chưa đủ; giá trị thật nằm ở khả năng chuyển spec thành trải nghiệm có thể dùng ngay. Đặc biệt với AI product, UX flow và guardrail an toàn phải được thiết kế cùng lúc, nếu không demo sẽ rất dễ "hay về ý tưởng nhưng yếu khi chạy thực tế".

## 7. AI giúp gì / AI sai gì
- **Giúp:** AI hỗ trợ tổng hợp nhanh các phương án UI flow từ user stories trong spec (happy path, low-confidence, failure, correction), nhờ đó  rút ngắn thời gian chuyển từ ý tưởng sang màn hình demo. Ngoài ra, AI cũng giúpp diễn đạt lại phần kết luận triển khai theo ngôn ngữ rõ ràng hơn để cả team thống nhất thông điệp khi thuyết trình.
- **Sai/mislead:** Một số gợi ý của AI thiên về "làm cho đầy đủ tính năng" hơn là bám mục tiêu sprint, ví dụ đề xuất thêm nhiều nhánh tương tác sâu khiến flow dài và khó demo trong thời gian ngắn. Bài học là phải xem AI như công cụ đề xuất, còn quyết định cuối cùng vẫn phải dựa trên scope, metric và khả năng triển khai thực tế của nhóm.