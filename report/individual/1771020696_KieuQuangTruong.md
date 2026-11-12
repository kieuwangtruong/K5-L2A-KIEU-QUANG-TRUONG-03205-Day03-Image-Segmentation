# Báo cáo thực hành Day 3 — Image Segmentation

- Mã học viên theo lớp: 1771020696
- Ngày / CVAT local: 12/11/2026 · CVAT local (`http://localhost:8080`)
- Công cụ đã dùng: CVAT SDK, SAM 3 qua Google Colab/Ngrok (`/predict`), `auto_full_pipeline.py`, GitHub Actions (`Day 3 self-check`).

## 1. Bài đã nộp

Đã có đủ 9 ZIP trong `submissions/`. Số ảnh dưới đây là số ảnh trong export; với Medium và Hard, COCO hiện không có annotation nên chưa thể tính là ảnh đã hoàn tất gán nhãn.

| Task | File ZIP đúng tên | Hoàn thành mấy ảnh | Điểm tối đa (coach chấm sau) |
| --- | --- | ---: | ---: |
| easy_semantic | `easy_semantic.zip` | 3 / 3 (export mask) | 20 |
| medium_instance | `medium_instance.zip` | 0 / 3 xác minh được; COCO `annotations` rỗng | 32 |
| hard_panoptic | `hard_panoptic.zip` | 0 / 2 xác minh được; COCO `annotations` rỗng | 30 |
| cp1_holes | `cp1_holes.zip` | 1 / 1 | 3 |
| cp2_slice | `cp2_slice.zip` | 1 / 1 | 3 |
| cp5_occlusion | `cp5_occlusion.zip` | 1 / 1 | 3 |
| cp3_thin | `cp3_thin.zip` | 1 / 1 (export mask) | 3 |
| cp4_curb | `cp4_curb.zip` | 1 / 1 (export mask) | 3 |
| cp6_coverage | `cp6_coverage.zip` | 1 / 1 (export mask) | 3 |
| **Tổng tối đa** | | | **100** |

## 2. Một quyết định trước khi dùng gợi ý

- Ảnh, vị trí và object Medium đầu tiên tự vẽ: Chưa thể xác nhận từ ZIP export; cần ghi lại theo thứ tự thao tác thực tế trong CVAT. Ảnh `000000181542.jpg` có người đi bộ mặc áo sáng ở gần chính giữa, có thể dùng để định vị object.
- Class và quy tắc tôi dùng để chọn biên: Nếu object đã chọn là người ở ảnh trên, class là `person`; chỉ theo phần cơ thể nhìn thấy, dừng biên tại chỗ bị xe/xe máy che và không mở rộng mask sang nền. Học viên cần xác nhận đây là object đầu tiên mình tự vẽ.
- Nếu dùng gợi ý sau đó: Pipeline có gọi SAM 3, nhưng COCO của Medium xuất ra không chứa annotation; vì vậy chưa thể đối chiếu contour gợi ý với mask đã lưu hoặc xác nhận thao tác sửa/giữ. Cần export lại sau khi kiểm tra dữ liệu CVAT.

## 3. Một lỗi tôi tìm thấy và sửa

- Task/ảnh/vùng: `medium_instance` và `hard_panoptic`, toàn bộ ảnh trong hai bản COCO export.
- Lỗi thuộc loại: thiếu vùng/annotation trong file export.
- Bằng chứng tôi nhìn thấy: `medium_instance.zip` chứa 3 ảnh nhưng `annotations/instances_default.json` có 0 annotation; `hard_panoptic.zip` chứa 2 ảnh nhưng JSON cũng có 0 annotation.
- Quy tắc và hành động sửa: Chưa sửa được trong phiên này. Cần kiểm tra annotation đã Save trong CVAT, kiểm tra Job/Task được export đúng, sau đó export lại COCO và xác nhận `annotations` có dữ liệu trước khi ghi hai task là hoàn tất.
- Sau sửa đã Save và export lại chưa? Chưa; hiện chưa xác nhận lỗi đã được sửa.
- Kết quả GitHub Actions / tự chấm: Chưa có điểm được xác minh trong workspace. Không ghi PASS hoặc điểm tổng.

## 4. Ba ca chưa chắc hoặc đã cân nhắc

| Ảnh/vị trí | Hai cách hiểu có thể | Quy tắc/chứng cứ | Quyết định hoặc câu hỏi cho coach |
| --- | --- | --- | --- |
| `cp4_curb`, ranh bó vỉa | Pixel thuộc `road` hay `sidewalk` | Theo chức năng bề mặt và đường ranh bó vỉa nhìn thấy; không phân lớp chỉ theo màu/độ sáng | Đặt ranh tại mép bó vỉa nhìn thấy; nếu bó vỉa không rõ, giữ theo bề mặt liên tục và hỏi coach khi không có dấu hiệu đủ chắc. |
| `cp2_slice`, hai xe sát nhau | Một vùng xe bị dính thành một mask hay hai xe là hai instance | Instance segmentation: mỗi xe là một vật riêng; dùng đường viền/ranh nhìn thấy giữa hai thân xe | Tách thành hai instance khi có ranh phân biệt; không nối mask qua khoảng nền. |
| `cp5_occlusion`, vật bị che khuất | Các mảng nhìn thấy là hai vật hay hai phần của cùng một vật | Dựa vào tính liên tục của đường viền và dấu hiệu hình dạng; chỉ gán phần nhìn thấy, không đoán phần nằm sau vật che | Giữ một instance nếu các phần nhìn thấy nhận ra là cùng vật; không tô vùng bị che. |
