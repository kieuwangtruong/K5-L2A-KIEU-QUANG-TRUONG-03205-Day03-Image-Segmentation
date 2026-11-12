# Hướng dẫn mẫu báo cáo thực hành Day 3

Mục tiêu của phần báo cáo là giải thích cách bạn làm, chỗ nào chưa chắc, và một lỗi bạn đã phát hiện và sửa. Bạn chỉ cần viết ngắn, rõ, dựa trên sản phẩm thật của mình.

> Bạn cần điền gì?
>
> - Mã học viên, ngày làm và công cụ đã dùng.
> - Các ZIP bạn có thật trong `submissions/` và số ảnh đã Save cho từng task.
> - Một quyết định trong `medium_instance` mà bạn tự vẽ trước khi dùng gợi ý.
> - Một lỗi bạn đã thấy và sửa, kèm lý do và bằng chứng.
> - Ba trường hợp còn chưa chắc hoặc bạn đã cân nhắc và quyết định như thế nào.

## 1. Bài đã nộp

Ghi tên ZIP đúng như file trong `submissions/` và số ảnh đã vẽ, Save. Chưa làm hoặc export lỗi thì ghi `chưa có`, không tạo ZIP rỗng. Cột điểm là điểm tối đa của task, **không phải điểm tự chấm**.

| Task | File ZIP đúng tên | Hoàn thành mấy ảnh | Điểm tối đa (coach chấm sau) |
| --- | --- | ---: | ---: |
| easy_semantic | … | … / 3 | 20 |
| medium_instance | … | … / 3 | 32 |
| hard_panoptic | … | … / 2 | 30 |
| cp1_holes | … | … / 1 | 3 |
| cp2_slice | … | … / 1 | 3 |
| cp5_occlusion | … | … / 1 | 3 |
| cp3_thin | … | … / 1 | 3 |
| cp4_curb | … | … / 1 | 3 |
| cp6_coverage | … | … / 1 | 3 |
| **Tổng tối đa** | | | **100** |

Nếu export lỗi, ghi task, dữ liệu đã Save đến đâu và lỗi đã báo coach.

## 2. Một quyết định trước khi dùng gợi ý

Chọn object đầu tiên bạn tự vẽ ở `medium_instance`, trước khi xem bất kỳ đề xuất tự động nào cho object đó. Ghi ảnh/vị trí đủ để tìm lại; “quy tắc biên” là lý do bạn chọn hoặc dừng mask ở ranh đó.

- Ảnh, vị trí và object Medium đầu tiên tự vẽ: …
- Class và quy tắc tôi dùng để chọn biên: …
- Nếu dùng gợi ý sau đó: vùng gợi ý sai/đúng, hành động sửa/giữ và lý do: …
- Nếu không dùng gợi ý: ghi “không dùng”; vẫn giải thích một quyết định gán nhãn của mình.

> Ví dụ cách giải thích
>
> “Tôi vẽ object đầu tiên trên ảnh `000000336232.jpg`, vùng trái của xe tải. Tôi giữ biên sát với hình dạng xe và không vượt qua mép đổ bóng; vì quy tắc là chỉ vẽ phần nhìn thấy, không đoán vùng bị che.”

## 3. Một lỗi tôi tìm thấy và sửa

Chọn một lỗi **có thật** trong bài. Nếu công cụ lỗi khiến bạn chưa sửa được, ghi rõ đã thử gì và cần coach hỗ trợ gì; không ghi “đã sửa” khi chưa sửa.

- Task/ảnh/vùng: …
- Lỗi thuộc loại: sai lớp / thiếu-thừa vật / gộp-tách / biên / phủ vùng / khác: …
- Bằng chứng tôi nhìn thấy: …
- Quy tắc và hành động sửa: …
- Sau sửa đã Save và export lại chưa? …

Nếu bạn **đã xem Summary tự đánh giá trên GitHub Actions hoặc tự chạy script**, ghi ngắn một kết quả liên quan lỗi vừa sửa (ví dụ task, metric trước/sau nếu có): … / chưa có điểm. Scorecard ba tier tối đa **82**, không phải điểm cuối trên 100. Không tự ghi PASS/top 3/bonus; người phụ trách xác nhận theo tiêu chí lớp. Không đưa file ground truth vào fork.

## 4. Ba ca chưa chắc hoặc đã cân nhắc

Mỗi ca là một **vùng cụ thể** khiến bạn phải cân nhắc hai cách hiểu. Ghi dấu hiệu nhìn thấy hoặc quy tắc đã dùng, rồi nêu quyết định hoặc câu hỏi cho coach. Không cần ba lỗi; ca đã quyết định được cũng hợp lệ.

| Ảnh/vị trí | Hai cách hiểu có thể | Quy tắc/chứng cứ | Quyết định hoặc câu hỏi cho coach |
| --- | --- | --- | --- |
| 1 | … | … | … |
| 2 | … | … | … |
| 3 | … | … | … |

## Gợi ý viết ngắn nhưng đủ bằng chứng

- Chỉ mô tả 1–2 câu cho từng mốc.
- Nêu nhiệm vụ, vị trí và lý do quy tắc.
- Không cần dùng từ chuyên môn quá nhiều. Bài chấm là về sự rõ ràng và hành vi thực tế khi làm task.
