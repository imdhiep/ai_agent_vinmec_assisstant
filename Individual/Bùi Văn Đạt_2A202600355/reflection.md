# Individual reflection — Bùi Văn Đạt (2A202600355)

## 1. Role
Xác định 4 luồng User Stories, xây dựng ROI, Metrics, Eval criteriae, thực hiện testcase.

## 2. Đóng góp cụ thể
- Xây dựng 4 luồng User Stories chính: happy path (đặt lịch thành công), low-confidence path (cần hỏi thêm), correction path (sửa sai), và safety cases (nguy cấp).
- Phát triển bộ metrics đánh giá: accuracy của gợi ý chuyên khoa, response time, user satisfaction, và tỷ lệ escalation.
- Thiết kế eval criteriae dựa trên benchmark y tế và feedback từ nhóm.
- Thực hiện testcase trên prototype, ghi lại kết quả và đề xuất cải thiện prompt để giảm hallucination.

## 3. SPEC mạnh/yếu
- Mạnh nhất: User Stories rõ ràng, giúp nhóm hiểu được các luồng chính và edge cases.
- Mạnh nhất: Metrics và eval criteriae cụ thể, dễ đo lường và so sánh với benchmark.
- Yếu nhất: ROI vẫn dựa trên giả định, cần dữ liệu thực tế từ Vinmec để validate.
- Yếu nhất: Testcase chưa cover đủ các ngôn ngữ và văn hóa Việt Nam, có thể bỏ sót một số ngữ cảnh địa phương.

## 4. Đóng góp khác
- Hỗ trợ nhóm trong việc review và refine SPEC, đảm bảo các phần metrics và eval phù hợp với khả năng prototype.
- Tham gia brainstorming để tích hợp testcase vào demo flow, giúp demo trở nên thuyết phục hơn.

## 5. Điều học được
Trước hackathon, nghĩ rằng xây dựng metrics chỉ là phần kỹ thuật. Sau quá trình làm, nhận ra metrics phải gắn liền với user experience và business value. Việc xây dựng eval criteriae giúp nhóm không chỉ tập trung vào độ chính xác mà còn vào cách hệ thống xử lý uncertainty, điều rất quan trọng trong lĩnh vực y tế để tránh rủi ro.

## 6. Nếu làm lại
Sẽ thu thập thêm dữ liệu benchmark từ các hệ thống y tế VinMec sớm hơn để làm eval criteriae chính xác hơn. Đồng thời, tích hợp testcase vào development cycle từ đầu thay vì chỉ làm ở cuối, để có thể iterate prompt và logic kịp thời.

## 7. AI giúp gì / AI sai gì
- **Giúp:** AI hỗ trợ nhanh chóng generate user stories và testcase ideas, cũng như brainstorm metrics phù hợp. Ngoài ra, dùng AI để simulate responses và evaluate accuracy.
- **Sai/mislead:** AI đôi khi đề xuất metrics quá phức tạp hoặc không thực tế cho hackathon, như metrics về long-term retention mà không có data. Bài học là dùng AI để brainstorm nhưng luôn validate với context thực tế.