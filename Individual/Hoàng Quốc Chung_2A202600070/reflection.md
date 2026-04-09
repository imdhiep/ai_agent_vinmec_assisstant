# Individual reflection — Hoàng Quốc Chung (2A202600070)

## 1. Role
Prompt engineer + evaluator. Phụ trách research, xây dựng logic hỏi tiếp khi thông tin chưa đủ và generate testcase đánh giá chất lượng đầu ra.

## 2. Đóng góp cụ thể
- Xây dựng bộ test case để đánh giá chất lượng đầu ra của hệ thống, bao gồm happy path, low-confidence path, correction path, và safety cases (docs/vinmec_hackathon_testcases.md)
- Đề xuất cách chia output thành các phần rõ ràng hơn: **mức độ ưu tiên**, **khoa đề xuất**, **lý do**, **bước tiếp theo**
- Đánh giá kết quả prompt trên nhiều input khác nhau để xem khi nào model trả lời tốt, khi nào dễ hallucinate hoặc trả lời quá tự tin

## 3. SPEC mạnh/yếu
- Mạnh nhất: phần problem framing và flow sản phẩm khá rõ. Nhóm không đi theo hướng “AI chẩn đoán bệnh” mà tập trung vào điều hướng hành trình bệnh nhân, nên hợp hơn với bối cảnh Vinmec và an toàn hơn cho demo
- Mạnh nhất: failure modes có nghĩ tới hallucination, over-trust, và ambiguity; mỗi lỗi đều có mitigation tương đối cụ thể
- Yếu nhất: ROI vẫn còn mang tính giả định, chưa có số liệu thực tế từ bệnh viện hoặc benchmark đủ mạnh để làm luận điểm chắc hơn
- Yếu nhất: phần user segmentation mới dừng ở mức khái quát, chưa tách sâu các nhóm như người lớn tuổi, phụ huynh có con nhỏ, hay bệnh nhân tái khám

## 4. Đóng góp khác
- Hỗ trợ viết file markdown tổng hợp để nhóm dễ nộp và dễ tái sử dụng khi làm slide
- Review demo flow để bảo đảm mọi màn hình đều bám đúng logic của SPEC, không bị lệch sang chatbot hỏi đáp chung chung

## 5. Điều học được
Trước hackathon thì nghĩ là AI trong healthcare mạnh nhất khi “trả lời đúng”. Sau quá trình làm bài mới hiểu trong bối cảnh y tế, điều quan trọng không chỉ là độ đúng mà còn là cách hệ thống xử lý khi không chắc chắn (Do sẽ phải chịu toàn bộ trách nhiệm nếu AI đưa ra câu trả lời sai thực tế). Một sản phẩm an toàn là sản phẩm biết hỏi lại, biết escalate, và biết dừng đúng lúc. Vì vậy, thiết kế guardrail và luồng correction path quan trọng không kém bản thân model.

## 6. Nếu làm lại
Mình sẽ khóa scope sớm hơn ngay từ đầu. Ban đầu nhóm có xu hướng thêm nhiều tính năng như đặt lịch, đọc kết quả chi tiết, quản lý hồ sơ, nhưng sau đó mới nhận ra phần cốt lõi cần tập trung chỉ là triage + journey guidance + follow-up. Nếu chốt phạm vi từ sớm hơn, nhóm có thể dành thêm thời gian để test các case khó và polish demo.

## 7. AI giúp gì / AI sai gì
- **Giúp:** AI hỗ trợ khá nhiều ở giai đoạn đầu, nhất là khi cần brainstorm nhanh nhiều hướng prompt và nghĩ ra thêm các tình huống fail mà nhóm có thể bỏ sót. Đồng thời cũng dùng AI để tạo nháp một số test case. Ngoài ra, AI còn hữu ích ở chỗ giúp diễn đạt lại output theo format rõ ràng hơn để người dùng dễ hiểu.
- **Sai/mislead:** AI thường gợi ý mở rộng scope quá mức, ví dụ thêm chức năng đặt lịch, phân tích hồ sơ bệnh án sâu, hoặc chẩn đoán sơ bộ. Những gợi ý này nghe hấp dẫn nhưng không phù hợp thời gian hackathon và có thể làm nhóm lệch khỏi bài toán chính. Bài học là AI rất tốt để mở rộng không gian ý tưởng, nhưng con người vẫn phải tự giới hạn phạm vi.