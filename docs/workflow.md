# Quy trình hoạt động (Workflow)

Tài liệu mô tả quy trình xử lý tổng quan của hệ thống Digit OCR, từ khi người dùng upload ảnh cho đến khi nhận được kết quả nhận diện.

## 1. Tổng quan Pipeline

```
Người dùng upload ảnh
        │
        ▼
┌─────────────────────┐
│   Frontend (React)  │  Gửi ảnh qua HTTP POST /predict
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  FastAPI Router     │  Kiểm tra định dạng & kích thước file
│  (prediction.py)    │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Prediction Service │  Điều phối toàn bộ pipeline xử lý
└────────┬────────────┘
         │
    ┌────┴──────────┐
    ▼               ▼
┌────────────┐ ┌───────────────────────┐
│   Decode   │ │    Line Segmentation  │
│  + Resize  │ │ (Contour Detection    │
│  + Binarize│ │  3-layer Filtering)   │
└─────┬──────┘ └──────────┬────────────┘
      └──────────┬─────────┘
                 ▼
     ┌─────────────────────┐
     │  Batch TrOCR Model  │  Nhận diện text theo lô (≤8 ảnh/lô)
     │  (HuggingFace)      │
     └──────────┬──────────┘
                ▼
     ┌─────────────────────┐
     │   Text Postprocess  │  Lọc, chỉ giữ ký tự số 0-9
     └──────────┬──────────┘
                ▼
     Ghép kết quả các dòng bằng ký tự xuống dòng (\n)
                │
                ▼
     Trả JSON response về Frontend
```

## 2. Chi tiết từng bước

### Bước 1 — Upload ảnh (Frontend)

Người dùng kéo-thả hoặc chọn file ảnh chữ số viết tay trên giao diện web. File được đọc vào bộ nhớ dưới dạng `ArrayBuffer` rồi gửi đến Backend qua HTTP `POST /predict` dưới dạng `multipart/form-data`.

### Bước 2 — Nhận & kiểm tra file (Router)

FastAPI router (`prediction.py`) nhận file và thực hiện kiểm tra:
- Định dạng file phải là PNG, JPEG, BMP hoặc TIFF.
- Kích thước file không vượt quá 10 MB.
- File không được rỗng.

Nếu hợp lệ, chuyển tiếp bytes ảnh sang Prediction Service.

### Bước 3 — Giải mã & chuẩn hóa kích thước (Decode & Resize)

Hàm `bytes_to_grayscale()` trong `image_processing.py`:
1. Giải mã chuỗi bytes thành ảnh grayscale (1 kênh màu) bằng OpenCV.
2. **Resize** ảnh về chiều rộng cố định `target_width=1024` (giữ nguyên tỉ lệ chiều cao) để đảm bảo xử lý nhất quán.

### Bước 4 — Nhị phân hóa (Binarization)

Hàm `binarize()` áp dụng **Adaptive Gaussian Threshold** để chuyển ảnh grayscale thành ảnh nhị phân:
- Nét mực (chữ viết) → pixel trắng (255)
- Nền giấy → pixel đen (0)
- **Xóa viền ảnh:** Loại bỏ 25px trên/dưới và 5px trái/phải để triệt tiêu nhiễu từ mép giấy hoặc khung scan.

> Khác với Otsu (ngưỡng toàn cục), Adaptive Threshold tính ngưỡng cục bộ theo từng vùng nhỏ (block 51×51), nên xử lý tốt hơn với ảnh chụp không đều sáng hoặc bóng đổ.

### Bước 5 — Tách dòng văn bản (Line Segmentation — Contour Detection)

Hàm `detect_lines()` trong `digit_detection.py` sử dụng phương pháp **OpenCV Contour Detection với 3 tầng lọc**:

**Tầng 1 — Lọc contour cấp ký tự:**
1. Dilate ảnh nhị phân để kết nối các nét viết gần nhau (kernel 2×3, 1 iteration).
2. Tìm tất cả contour ngoài (`RETR_EXTERNAL`).
3. Lọc contour theo 3 tiêu chí:
   - Diện tích ≥ 80 px² (loại hạt nhiễu nhỏ)
   - Chiều cao ≥ 20 px (loại nét ngang mỏng)
   - Aspect ratio (w/h) ≤ 2.5 (loại vệt kẻ ngang, margin dài)

**Tầng 2 — Gom contour thành dòng:**
4. Sắp xếp contour theo tâm Y.
5. Gom các contour có tâm Y gần nhau (trong phạm vi `avg_h × 0.6`) vào cùng một dòng.
6. Xác định `y_min` và `y_max` của mỗi dòng.

**Tầng 3 — Lọc dòng cấp line:**
7. Bỏ dòng có chiều cao < 20px.
8. Tính mật độ pixel trắng trong vùng ROI. Bỏ dòng có mật độ < 2% (loại phantom line do ảo giác contour).
9. Thêm `padding = 6px` trên/dưới, cắt vào giới hạn ảnh.
10. Trả về danh sách `LineBox(y_start, y_end)` đã sắp xếp từ trên xuống dưới.

### Bước 6 — Nhận diện từng dòng bằng TrOCR (Batch Inference)

Thay vì xử lý từng ảnh một, service gom ảnh thành **lô (batch)** để tăng tốc đáng kể:

1. Cắt tất cả vùng dòng từ ảnh grayscale gốc → danh sách ảnh PIL RGB (`crop_to_pil_rgb()`).
2. Chia thành các lô tối đa 8 ảnh.
3. Với mỗi lô:
   - Nạp vào `TrOCRProcessor` → tensor `pixel_values` → đẩy lên device (CPU/CUDA).
   - Gọi `model.generate()` với `num_beams`, `max_new_tokens`, `early_stopping=True`.
   - Giải mã `batch_decode()` → danh sách chuỗi văn bản thô.

### Bước 7 — Lọc và làm sạch kết quả (Text Post-processing)

Hàm `sanitize_line()` trong `text_postprocess.py` xử lý từng chuỗi OCR:
- Xóa khoảng trắng đầu/cuối.
- **Chỉ giữ lại ký tự số `0–9`**, loại bỏ chữ cái, dấu câu, ký tự đặc biệt mà model có thể sinh ra nhầm.
- Dòng rỗng sau khi lọc bị bỏ qua hoàn toàn.

> Bước này là lớp bảo vệ cuối cùng, đảm bảo output luôn là chuỗi số thuần túy dù model nhận diện sai một phần.

### Bước 8 — Ghép kết quả & trả về

Tất cả chuỗi số hợp lệ của các dòng được nối lại bằng ký tự xuống dòng thực (`\n`), đóng gói thành JSON response:

```json
{
  "filename": "test_image.jpg",
  "prediction": "0123456\n789"
}
```

Frontend nhận response, hiển thị kết quả với `white-space: pre-line` để `\n` được render thành xuống dòng thật trên giao diện.

## 3. Khởi động Server (Startup Flow)

Khi Uvicorn khởi động:
1. FastAPI gọi sự kiện `on_startup` → hàm `warmup()`.
2. `warmup()` gọi `_load()` trong `model_loader.py`.
3. `_load()` kiểm tra thư mục `trained_models/trocr/`:
   - **Có file** → Load model từ ổ đĩa nội bộ (nhanh, ~18 giây, không cần mạng).
   - **Không có** → Tải model từ Hugging Face (~1.27 GB), sau đó lưu vào `trained_models/trocr/` cho lần sau.
4. Model được giữ trong bộ nhớ (RAM/VRAM) suốt vòng đời server qua 3 singleton: `get_model()`, `get_processor()`, `get_device()`.
5. Endpoint `/health` (GET) cho phép kiểm tra trạng thái server mà không cần chạy model.
