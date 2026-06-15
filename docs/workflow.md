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
    ┌────┴───────┐
    ▼            ▼
┌────────┐ ┌───────────────┐
│ Image  │ │    Line       │
│ Decode │ │ Segmentation  │
│ + Otsu │ │ (Projection)  │
└───┬────┘ └──────┬────────┘
    └──────┬──────┘
           ▼
    ┌───────────────┐
    │  TrOCR Model  │  Nhận diện text cho từng dòng
    │  (HuggingFace)│
    └──────┬────────┘
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
- Kích thước file không vượt quá 10MB.
- File không được rỗng.

Nếu hợp lệ, chuyển tiếp bytes ảnh sang Prediction Service.

### Bước 3 — Giải mã ảnh (Image Decode)

Hàm `bytes_to_grayscale()` trong `image_processing.py` giải mã chuỗi bytes thành ảnh grayscale (đen trắng, 1 kênh màu) bằng OpenCV.

### Bước 4 — Nhị phân hóa (Binarization)

Hàm `binarize()` áp dụng ngưỡng Otsu để chuyển ảnh grayscale thành ảnh nhị phân:
- Nét mực (chữ viết) → pixel trắng (255)
- Nền giấy → pixel đen (0)

Mục đích: Tạo đầu vào sạch cho bước tách dòng tiếp theo.

### Bước 5 — Tách dòng văn bản (Line Segmentation)

Hàm `detect_lines()` trong `digit_detection.py` sử dụng phương pháp **Horizontal Projection Profile**:
1. Tính tổng pixel trắng theo từng hàng ngang của ảnh nhị phân.
2. Hàng nào có nhiều pixel trắng → thuộc vùng chứa chữ.
3. Hàng nào gần như toàn đen → khoảng trống giữa các dòng.
4. Xác định ranh giới (y_start, y_end) của từng dòng, thêm padding và trả về danh sách `LineBox`.

### Bước 6 — Nhận diện từng dòng bằng TrOCR

Với mỗi `LineBox` được phát hiện:
1. Cắt vùng ảnh tương ứng từ ảnh grayscale gốc bằng `crop_to_pil_rgb()`.
2. Chuyển đổi sang ảnh PIL RGB (định dạng đầu vào mà TrOCR yêu cầu).
3. Truyền ảnh qua `TrOCRProcessor` để chuyển thành tensor `pixel_values`.
4. Đưa tensor vào `VisionEncoderDecoderModel` để sinh ra chuỗi ký tự bằng Beam Search.
5. Giải mã token IDs thành chuỗi text rõ ràng (readable text).

### Bước 7 — Ghép kết quả & trả về

Tất cả chuỗi text của các dòng được nối lại bằng ký tự xuống dòng thực (`\n`), đóng gói thành JSON response:

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
   - **Không có** → Tải model từ Hugging Face, sau đó lưu vào `trained_models/trocr/` cho lần sau.
4. Model được giữ trong bộ nhớ (RAM/GPU) suốt vòng đời server, phục vụ mọi request mà không cần load lại.
