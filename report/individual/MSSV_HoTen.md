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
| hard_panoptic | `hard_panoptic.zip` | 2 / 2 có annotation (108 mask COCO RLE) | 30 |
| cp1_holes | `cp1_holes.zip` | 1 / 1 có annotation (1 polygon class `person`; cần kiểm class/biên) | 3 |
| cp2_slice | `cp2_slice.zip` | 1 / 1 có annotation (1 polygon person; chưa thể hiện 2 xe riêng) | 3 |
| cp5_occlusion | `cp5_occlusion.zip` | 1 / 1 có annotation (1 polygon class `person`; cần QC) | 3 |
| cp3_thin | `cp3_thin.zip` | 1 / 1 có mask (pixel khác nền chỉ mang class pole) | 3 |
| cp4_curb | `cp4_curb.zip` | 1 / 1 có mask (pixel khác nền chỉ mang class road) | 3 |
| cp6_coverage | `cp6_coverage.zip` | 1 / 1 có mask (pixel khác nền chỉ mang class road) | 3 |
| **Tổng tối đa** | | | **100** |

`easy_semantic.zip` có đủ 3 PNG mask đúng kích thước trong `SegmentationClass/`. `medium_instance.zip` có đúng 3 ảnh, 125 annotation RLE hợp lệ và category name khớp task. `hard_panoptic.zip` có COCO JSON với 2 ảnh, 108 RLE (46 và 62 mask); inspector báo cấu trúc và mapping hợp lệ. Tuy vậy, cả 108 annotation đều có `iscrowd=1`, export không có annotation class `bicycle`, và có pixel chồng lấn cần kiểm trực quan trong CVAT. Các con số của checkpoint chỉ xác nhận có annotation/mask trong ZIP, không xác nhận chất lượng.

Các mask không nền trong `cp3_thin`, `cp4_curb` và `cp6_coverage` có cùng tọa độ pixel; polygon trong `cp1_holes` và `cp5_occlusion` cũng giống hệt nhau. Tôi chưa xác định nguyên nhân, nên cần kiểm tra lại trong CVAT. Tôi chưa tìm thấy Ground Truth cho sáu checkpoint; không tính metric cho các task này.

## 2. Một quyết định trước khi dùng gợi ý

- Ảnh, vị trí và object Medium đầu tiên tự vẽ: `000000181542.jpg`, người mặc đồ sáng ở giữa ảnh. Tôi xác nhận đây là object đầu tiên tôi tự vẽ trước khi xem gợi ý.
- Class và quy tắc tôi dùng để chọn biên: `person`; tôi bỏ biển quảng cáo phía sau vì không thuộc class của task và chọn biên theo người nhìn thấy.
- Gợi ý sau đó: Tôi xem gợi ý khi polygon ban đầu chưa sát người. Tôi chủ yếu giữ đề xuất và chỉnh các góc polygon; nếu thiếu quá nhiều, tôi tạo lại polygon với nhiều điểm hơn. [CẦN TÔI XÁC NHẬN] Tôi cần bổ sung vùng cụ thể gợi ý đúng/sai nếu còn nhớ.

## 3. Một lỗi tôi tìm thấy và sửa

- Task/ảnh/vùng: `hard_panoptic`, hai ảnh `000000350023.jpg` và `000000460147.jpg`.
- Lỗi thuộc loại: export rỗng; thiếu annotation.
- Bằng chứng tôi nhìn thấy: ZIP đã commit trước đó có 0 annotation. ZIP mới có 108 mask RLE (46 và 62 trên hai ảnh); inspector báo đúng ảnh, category và format. Reference cục bộ có một instance `bicycle` ở `000000350023.jpg`, nhưng export mới không có mask `bicycle`.
- Quy tắc và hành động sửa: Panoptic cần đủ 5 lớp Stuff và mỗi Thing là một instance riêng. Tôi đã thay export rỗng bằng bản COCO mới có annotation; bản mới có 5 lớp Stuff trong cả hai ảnh. Tôi vẫn cần kiểm tra trong CVAT vì cả 108 annotation đều mang `iscrowd=1`; pixel chồng lấn chiếm 0.1% vùng phủ ở ảnh `000000350023.jpg` và 3.26% ở `000000460147.jpg` (chồng tối đa 4 mask tại một pixel). Tôi xác nhận đã Save Job #3 và export ZIP hiện tại; CSV ngày 12/11 là snapshot cũ, còn API không cho đọc trạng thái trực tiếp.
- Sau sửa đã Save và export lại chưa? Có, theo xác nhận của tôi; ZIP hiện tại có 108 annotation.
- Metric kỹ thuật: Easy mIoU 0.788, coverage 92.2% (road 0.957, sidewalk 0.488, building 0.855, vegetation 0.674, sky 0.969). Medium mean matched IoU 0.804, recall@0.5 0.958, precision@0.5 0.544, metric kết hợp 0.770 (125 mask so với 71 reference; 57 FP, 3 FN). Hard PQ 0.424, SQ 0.648, RQ 0.547; PQ thấp ở bicycle 0.000, sidewalk 0.000, person 0.201, car 0.476. Theo công thức starter, điểm kỹ thuật cục bộ là Easy 17.2/20, Medium 26.3/32, Hard 14.9/30 — tổng scorecard ba tier 58.4/82. Đây là đối chiếu với reference cục bộ có đúng tên ảnh, mapping lớp và format; nguồn chưa được coach xác nhận. Scorer chính thức từ chối chạy vì thiếu protected reference trong `data/tiers/hard_panoptic/groundtruth`; GitHub Actions chưa chấm ZIP mới. Không phải điểm cuối /100, PASS hay điểm coach xác nhận.

## 4. Ba ca chưa chắc hoặc đã cân nhắc

Tôi xác nhận hai ca đầu dưới đây; ca thứ ba chưa có thông tin cá nhân để xác nhận.

| Ảnh/vị trí | Hai cách hiểu có thể | Quy tắc/chứng cứ | Quyết định hoặc câu hỏi cho coach |
| --- | --- | --- | --- |
| `medium_instance`, `000000181542.jpg`, biển quảng cáo phía sau người ở giữa ảnh | Biển quảng cáo là vật cần gán mask hay vùng nền không thuộc class | Chỉ gán sáu class của task; biển quảng cáo không phải class, người là `person` | Tôi bỏ qua biển quảng cáo và vẽ người riêng. |
| `medium_instance`, `000000181542.jpg`, các xe nhỏ ở góc trên bên phải | Một vùng xe liền nhau hay từng xe riêng | Mỗi xe nhìn thấy là một instance riêng; kích thước nhỏ khiến tôi khó tách từng xe | Tôi chưa chắc đã phát hiện/tách đủ từng xe; cần coach xác nhận cách xử lý xe quá nhỏ hoặc khó phân biệt. |
| [CẦN TÔI XÁC NHẬN] Chưa nhớ ca thứ ba thực tế; chưa xác định ảnh/vị trí | [CẦN TÔI XÁC NHẬN] Chưa xác định hai cách hiểu | [CẦN TÔI XÁC NHẬN] Chưa có bằng chứng hay rule của một ca thứ ba đã cân nhắc | Tôi không nhớ ca thứ ba; không khẳng định đã cân nhắc một trường hợp cụ thể. |
