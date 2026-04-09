# Luồng Flow Chính — AI Patient Copilot cho Vinmec

Tài liệu này mô tả **luồng vận hành chính** của giải pháp **AI Patient Copilot cho Vinmec** dưới dạng dễ đọc và dễ nhúng vào SPEC / slide / GitHub.

---

# 1. Flow tổng thể end-to-end

```mermaid
flowchart TD
    A[Bệnh nhân mở AI Patient Copilot] --> B[Nhập triệu chứng / câu hỏi]
    B --> C[AI phân tích mức độ rõ ràng của thông tin]

    C -->|Thông tin chưa đủ| D[AI hỏi thêm câu làm rõ]
    D --> E[Người dùng bổ sung thông tin]
    E --> F[AI đánh giá lại]

    C -->|Thông tin đủ| F[AI đánh giá lại]

    F --> G{Có dấu hiệu nguy hiểm không?}

    G -->|Có| H[Khuyến nghị cấp cứu / đi khám ngay]
    H --> I[Kết thúc luồng an toàn]

    G -->|Không| J[Gợi ý khoa phù hợp]
    J --> K[Tạo hành trình khám]
    K --> L[Giải thích từng bước cho bệnh nhân]
    L --> M[Hỗ trợ trong quá trình khám]
    M --> N[Giải thích kết quả sau khám]
    N --> O[Nhắc thuốc / tái khám / follow-up]
    O --> P[Kết thúc hành trình]
```

---

# 2. Flow theo 3 giai đoạn chính

## 2.1. Giai đoạn trước khám

```mermaid
flowchart TD
    A1[Người dùng nhập triệu chứng] --> B1[AI trích xuất triệu chứng chính]
    B1 --> C1{Thông tin có đủ không?}

    C1 -->|Không| D1[AI hỏi thêm: vị trí đau, thời gian, mức độ, dấu hiệu kèm theo]
    D1 --> E1[Người dùng trả lời]
    E1 --> F1[AI cập nhật đánh giá]

    C1 -->|Có| F1[AI cập nhật đánh giá]

    F1 --> G1{Có red flag không?}
    G1 -->|Có| H1[Khuyến nghị đi cấp cứu / khám ngay]
    G1 -->|Không| I1[Gợi ý khoa khám phù hợp]
    I1 --> J1[Hiển thị lý do gợi ý]
    J1 --> K1[Tạo checklist chuẩn bị trước khi đi khám]
```

### Kết quả đầu ra kỳ vọng
- Khoa hoặc chuyên khoa đề xuất
- Mức độ ưu tiên
- Lý do gợi ý
- Checklist chuẩn bị trước khám

---

## 2.2. Giai đoạn trong khi khám

```mermaid
flowchart TD
    A2[Bệnh nhân đã đến bệnh viện] --> B2[AI hiển thị bước hiện tại]
    B2 --> C2[Hướng dẫn bước tiếp theo]
    C2 --> D2[Giải thích xét nghiệm / thủ thuật nếu có]
    D2 --> E2[Giảm lo lắng bằng ngôn ngữ dễ hiểu]
    E2 --> F2[Nhắc người bệnh chuẩn bị cho bước tiếp theo]
```

### Kết quả đầu ra kỳ vọng
- Người bệnh biết mình đang ở bước nào
- Hiểu bước tiếp theo
- Giảm lo lắng và giảm hỏi lặp lại

---

## 2.3. Giai đoạn sau khám

```mermaid
flowchart TD
    A3[Người bệnh nhận kết quả / đơn thuốc] --> B3[AI giải thích bằng ngôn ngữ đơn giản]
    B3 --> C3[AI tóm tắt hướng dẫn của bác sĩ]
    C3 --> D3[AI tạo kế hoạch follow-up]
    D3 --> E3[Nhắc uống thuốc / tái khám]
    E3 --> F3{Có dấu hiệu bất thường mới không?}
    F3 -->|Có| G3[Khuyến nghị liên hệ bác sĩ / quay lại viện]
    F3 -->|Không| H3[Tiếp tục theo dõi tại nhà]
```

### Kết quả đầu ra kỳ vọng
- Người bệnh hiểu kết quả và đơn thuốc
- Tăng tuân thủ điều trị
- Không tự ý bỏ tái khám

---

# 3. Luồng safety ưu tiên cao

Đây là flow cực kỳ quan trọng để tránh việc AI hành xử như một hệ thống chẩn đoán.

```mermaid
flowchart TD
    S1[Người dùng nhập triệu chứng] --> S2[AI kiểm tra dấu hiệu nguy hiểm]
    S2 --> S3{Có nguy cơ cao không?}

    S3 -->|Có| S4[Escalate ngay: khuyến nghị cấp cứu / khám gấp]
    S4 --> S5[Không tiếp tục flow tư vấn thông thường]

    S3 -->|Không| S6[Tiếp tục flow định hướng]
    S6 --> S7[Chỉ gợi ý khoa / hành trình]
    S7 --> S8[Hiển thị disclaimer: AI không thay thế bác sĩ]
```

### Red flags phải nhận diện
- Đau ngực dữ dội
- Khó thở
- Vã mồ hôi
- Sốt cao ở trẻ nhỏ
- Chóng mặt nặng / ngất / dấu hiệu nguy cấp khác

---

# 4. Luồng correction path

Flow này giúp hệ thống không bị “cứng”, mà có thể sửa hướng khi user bổ sung thông tin mới.

```mermaid
flowchart TD
    C1[AI đưa gợi ý ban đầu] --> C2[Người dùng phản hồi: chưa đúng / thêm thông tin]
    C2 --> C3[AI nhận diện thay đổi ngữ cảnh]
    C3 --> C4[AI đánh giá lại]
    C4 --> C5[Đưa ra gợi ý mới]
    C5 --> C6[Giải thích vì sao thay đổi]
```

### Ý nghĩa
- Tăng độ tin cậy
- Giảm lỗi do input ban đầu thiếu
- Thể hiện AI biết điều chỉnh thay vì cố bảo vệ câu trả lời cũ

---

# 5. Luồng logic sản phẩm ở mức ngắn gọn

```mermaid
flowchart LR
    U[User Input] --> T[Triage]
    T --> R[Risk Check]
    R -->|High Risk| E[Escalate]
    R -->|Normal Risk| D[Department Recommendation]
    D --> J[Journey Guidance]
    J --> X[Explanation]
    X --> F[Follow-up]
```

---

# 6. Bản text flow đơn giản để đưa vào slide

## Flow chính
1. Người bệnh nhập triệu chứng hoặc câu hỏi  
2. AI hỏi thêm nếu thông tin chưa đủ  
3. AI kiểm tra dấu hiệu nguy hiểm  
4. Nếu nguy hiểm → khuyến nghị cấp cứu / khám ngay  
5. Nếu không nguy hiểm → gợi ý khoa phù hợp  
6. AI tạo hành trình khám từng bước  
7. AI giải thích xét nghiệm / kết quả bằng ngôn ngữ đơn giản  
8. AI nhắc thuốc, tái khám và follow-up sau khám  

---

# 7. Câu mô tả flow ngắn để pitch

> AI Patient Copilot guides patients from symptom intake to recovery follow-up, while always prioritizing safety escalation over diagnosis.

---

# 8. Gợi ý cách dùng trong bài thi

Bạn có thể dùng flow này ở 3 nơi:
- Trang mô tả solution overview
- Trang demo architecture / user journey
- Trang safety and guardrails

Nếu chỉ chọn 1 flow để đưa lên slide, nên dùng:
- **Flow tổng thể end-to-end**
- hoặc **Flow safety ưu tiên cao**