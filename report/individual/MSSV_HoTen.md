# Báo cáo thực hành Day 3 — Image Segmentation

- Mã học viên theo lớp: 1771020696 (theo báo cáo cá nhân hiện có)
- Ngày / CVAT local: 12/11/2026 · CVAT local (theo danh sách CVAT jobs)
- Công cụ đã dùng: CVAT local; CVAT SDK/SAM 3 qua Colab và `auto_full_pipeline.py` (theo báo cáo cá nhân cũ); GitHub Actions (có lần chạy xác nhận).

## 1. Bài đã nộp

Tôi ghi số ảnh có annotation trong export; số này không xác nhận mask đúng hoặc task đã qua QC. Điểm tối đa giữ theo rubric, không phải điểm tự chấm.

| Task | File ZIP đúng tên | Hoàn thành mấy ảnh | Điểm tối đa (coach chấm sau) |
| --- | --- | ---: | ---: |
| easy_semantic | `easy_semantic.zip` | 3 / 3 có mask `SegmentationClass` | 20 |
| medium_instance | `medium_instance.zip` | 3 / 3 có annotation (125 mask COCO RLE) | 32 |
| hard_panoptic | `hard_panoptic.zip` | 0 / 2 (COCO có 2 ảnh, 0 annotation) | 30 |
| cp1_holes | `cp1_holes.zip` | 1 / 1 có annotation (1 polygon class `person`; cần kiểm class/biên) | 3 |
| cp2_slice | `cp2_slice.zip` | 1 / 1 có annotation (1 polygon person; chưa thể hiện 2 xe riêng) | 3 |
| cp5_occlusion | `cp5_occlusion.zip` | 1 / 1 có annotation (1 polygon class `person`; cần QC) | 3 |
| cp3_thin | `cp3_thin.zip` | 1 / 1 có mask (pixel khác nền chỉ mang class pole) | 3 |
| cp4_curb | `cp4_curb.zip` | 1 / 1 có mask (pixel khác nền chỉ mang class road) | 3 |
| cp6_coverage | `cp6_coverage.zip` | 1 / 1 có mask (pixel khác nền chỉ mang class road) | 3 |
| **Tổng tối đa** | | | **100** |

`easy_semantic.zip` có đủ 3 PNG mask đúng kích thước trong `SegmentationClass/`. `medium_instance.zip` có đúng 3 ảnh, 125 annotation RLE hợp lệ và category name khớp task. Các con số của checkpoint chỉ xác nhận có annotation/mask trong ZIP, không xác nhận chất lượng.

Các mask không nền trong `cp3_thin`, `cp4_curb` và `cp6_coverage` có cùng tọa độ pixel; polygon trong `cp1_holes` và `cp5_occlusion` cũng giống hệt nhau. Tôi chưa xác định nguyên nhân, nên cần kiểm tra lại trong CVAT. Tôi chưa tìm thấy Ground Truth cho sáu checkpoint; không tính metric cho các task này.

## 2. Một quyết định trước khi dùng gợi ý

- Ảnh, vị trí và object Medium đầu tiên tự vẽ: [CẦN TÔI XÁC NHẬN] Báo cáo cũ nêu `000000181542.jpg`, người mặc áo sáng gần giữa ảnh như một vị trí có thể tìm lại, nhưng không xác nhận đây là object đầu tiên tôi tự vẽ. ZIP Medium hiện có 125 annotation nhưng không có log thao tác theo thứ tự.
- Class và quy tắc tôi dùng để chọn biên: [CẦN TÔI XÁC NHẬN] Nếu đúng là người trong ảnh trên thì class dự kiến là `person`; tôi cần xác nhận object và quy tắc biên mình thực sự đã dùng.
- Gợi ý sau đó: Báo cáo cũ ghi có dùng pipeline SAM 3, nhưng không có log chứng minh gợi ý nào được xem cho object đầu tiên hoặc tôi đã sửa/giữ phần nào. [CẦN TÔI XÁC NHẬN] Nếu không dùng gợi ý cho object này, ghi `không dùng` và lý do.

## 3. Một lỗi tôi tìm thấy và sửa

- Task/ảnh/vùng: `hard_panoptic`, hai ảnh `000000350023.jpg` và `000000460147.jpg`.
- Lỗi thuộc loại: thiếu toàn bộ annotation trong export.
- Bằng chứng tôi nhìn thấy: ZIP có đủ 2 ảnh và 12 category nhưng `annotations` rỗng; do đó không có 5 Stuff hoặc 7 Things nào được lưu trong bản export này.
- Quy tắc và hành động sửa: Panoptic cần mask cho Stuff và từng Thing riêng. Theo ghi chú cá nhân, tôi từng có hai cặp polygon `road` trùng tọa độ ở Frame 0 (shape 7/15) và Frame 1 (shape 8/16), rồi đã xóa. ZIP hiện tại không có polygon nào, nên không thể dùng nó để xác nhận việc xóa đã được Save trong CVAT. Tôi chưa sửa/export lại trong lần kiểm tra này; cần mở lại Job #3, xác nhận annotation đã lưu và xuất lại đúng COCO. API CVAT khi kiểm tra chỉ trả 401, nên tôi chưa đọc được trạng thái annotation hiện tại; nếu không truy cập được, tôi cần coach hỗ trợ kiểm tra Job.
- Sau sửa đã Save và export lại chưa? Chưa xác minh; không ghi là đã khắc phục.
- Metric kỹ thuật đối chiếu với bộ reference cục bộ có tên ảnh, class mapping và format khớp (nguồn phát chưa được coach xác nhận; không phải điểm chính thức): Easy IoU từng class — road 0.957, sidewalk 0.488, building 0.855, vegetation 0.674, sky 0.969; mIoU 0.788, coverage 92.2%. Medium mean matched IoU 0.804, recall@0.5 0.958, precision@0.5 0.544, metric kết hợp 0.770; có 125 mask so với 71 reference (57 FP, 3 FN). Hard PQ 0.000 (PQ từng class cũng 0.000). Lần chạy GitHub Actions có trước hai ZIP mới này; không tìm thấy release reference chính thức nên lần đó bỏ qua bước cài reference và chấm điểm. Không có điểm coach xác nhận.

## 4. Ba ca chưa chắc hoặc đã cân nhắc

Tôi chưa tìm thấy ghi chú chứng minh mình đã cân nhắc ba ca dưới đây; cần xác nhận trước khi nộp, không xem các dòng này là trải nghiệm đã được xác minh.

| Ảnh/vị trí | Hai cách hiểu có thể | Quy tắc/chứng cứ | Quyết định hoặc câu hỏi cho coach |
| --- | --- | --- | --- |
| [CẦN TÔI XÁC NHẬN] `cp4_curb`, `7d83710e-4697c3b2.jpg`, dọc mép bó vỉa giữa lòng đường và vỉa hè | Pixel sát mép thuộc `road` hay `sidewalk` | Dựa vào chức năng và bó vỉa nhìn thấy, không chỉ màu; export hiện chỉ có pixel `road` | [CẦN TÔI XÁC NHẬN] Tôi đã cân nhắc vùng này chưa? Nếu có, nêu ranh tôi đã chọn; nếu bó vỉa không rõ, hỏi coach. |
| [CẦN TÔI XÁC NHẬN] `cp2_slice`, `000000017627.jpg`, hai xe gần giữa khung hình | Một mask gộp hai xe hay mỗi xe là một instance riêng | Hai Thing cùng class vẫn là hai instance; export hiện chỉ có một polygon class `person` | [CẦN TÔI XÁC NHẬN] Tôi đã cân nhắc và quyết định tách hai xe thế nào? |
| [CẦN TÔI XÁC NHẬN] `cp5_occlusion`, `000000336232.jpg`, người đi xe máy ở nửa trái ảnh bị xe khác che một phần | Các phần nhìn thấy thuộc một instance hay hai vật | Một vật bị che vẫn là một instance; chỉ gán phần nhìn thấy, không vẽ xuyên vùng che | [CẦN TÔI XÁC NHẬN] Tôi đã gặp ca này chưa? Nếu có, nêu dấu hiệu nhận cùng vật hoặc điều cần hỏi coach. |
