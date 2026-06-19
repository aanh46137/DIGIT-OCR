# Kiến trúc hệ thống (System Architecture)

## 1. Tổng quan

Dự án Digit OCR là một ứng dụng Web dùng để nhận diện chữ số viết tay trên nhiều dòng văn bản, sử dụng mô hình học sâu **TrOCR** (Transformer-based Optical Character Recognition) của Microsoft.

Luồng dữ liệu chính:
`Frontend (React/Vite)` ➔ `FastAPI Backend` ➔ `Image Preprocessing (OpenCV)` ➔ `Contour-based Line Segmentation` ➔ `Batch TrOCR (Hugging Face)` ➔ `Text Post-processing` ➔ `Frontend Display`

## 2. Các thành phần chính

### 2.1. Frontend (`frontend/`)
- **Công nghệ:** React, Vite, Axios.
- **Tính năng:** Giao diện kéo-thả ảnh hiện đại với thiết kế dark-theme, gửi ảnh dưới dạng form-data qua cổng Proxy của Vite (cổng 5173). Kết quả được trả về sẽ hiển thị chính xác các ký tự theo từng dòng.
- **Mã nguồn chính:** `App.jsx`, `UploadImage.jsx`, `ResultPanel.jsx`, `DrawImage.jsx`, `api.js`.
  - `DrawImage.jsx`: Component vẽ/xem trước ảnh sau khi người dùng chọn.

### 2.2. Backend (`backend/app/`)
- **Công nghệ:** FastAPI, PyTorch, Transformers, OpenCV, Uvicorn.
- **Tính năng:** Chứa API Gateway và toàn bộ logic xử lý ảnh và chạy AI model.
- **Cấu trúc thư mục:**
  - `routers/prediction.py`: Định nghĩa HTTP endpoint `POST /predict`, kiểm tra định dạng (PNG/JPEG/BMP/TIFF) và kích thước (tối đa 10 MB).
  - `services/prediction_service.py`: Điều phối toàn bộ pipeline nhận diện: Xử lý ảnh → Tách dòng → Batch TrOCR → Lọc văn bản → Trả kết quả.
  - `models/model_loader.py`: Tải mô hình TrOCR (`microsoft/trocr-base-handwritten`) từ Hugging Face, cache vào `trained_models/trocr/`. Cung cấp singleton `get_model()`, `get_processor()`, `get_device()`.
  - `utils/image_processing.py`: Hàm xử lý ảnh cấp thấp:
    - `bytes_to_grayscale()`: Giải mã bytes → grayscale, resize về `target_width=1024`.
    - `binarize()`: Nhị phân hóa bằng **Adaptive Gaussian Threshold** (xóa viền, khử bóng đổ).
    - `crop_to_pil_rgb()`, `gray_to_pil_rgb()`: Chuyển đổi sang PIL RGB cho TrOCR.
    - `save_debug_image()`: Lưu ảnh trung gian vào `uploads/` để debug.
  - `utils/digit_detection.py`: Tách dòng văn bản bằng **OpenCV Contour Detection 3 tầng lọc**:
    - Tầng 1: Lọc contour theo diện tích, chiều cao, aspect ratio (loại nhiễu/vệt kẻ).
    - Tầng 2: Gom contour thành dòng dựa trên tâm Y (ROW_TOLERANCE_RATIO = 0.6).
    - Tầng 3: Lọc dòng theo mật độ pixel (MIN_LINE_DENSITY = 0.02), loại bỏ hallucination.
  - `utils/text_postprocess.py`: Lọc kết quả OCR — chỉ giữ lại ký tự số `0–9`, loại bỏ mọi ký tự lạ mà model có thể sinh ra.

## 3. Quy trình Xử lý Nhận diện (OCR Pipeline)

Quy trình nhận diện chi tiết khi một ảnh được gửi đến Backend:

1. **Decode & Resize:** Đọc chuỗi byte của ảnh, giải mã thành ảnh grayscale và chuẩn hóa về chiều rộng 1024px.
2. **Binarize:** Sử dụng **Adaptive Gaussian Threshold** (block=51, C=25) để tách nét mực (trắng = 255) khỏi nền (đen = 0). Xóa viền ảnh để loại bỏ nhiễu biên.
3. **Line Segmentation (Contour Detection):**
   - Dilate ảnh nhị phân để kết nối các nét gần nhau.
   - Tìm contour ngoài (`RETR_EXTERNAL`), lọc 3 tầng: diện tích ≥ 80, chiều cao ≥ 20px, aspect ratio ≤ 2.5.
   - Gom contour theo tâm Y thành các dòng; lọc dòng có chiều cao < 20px hoặc mật độ pixel < 2%.
   - Thêm `padding = 6px` và trả về danh sách `LineBox(y_start, y_end)`.
4. **Batch Predict (TrOCR):**
   - Cắt từng dòng ảnh và nhóm thành lô (batch, tối đa 8 ảnh/lô).
   - Nạp cả lô vào `TrOCRProcessor`, sinh tensor `pixel_values`.
   - Đưa tensor vào `VisionEncoderDecoderModel` → Beam Search → giải mã token → chuỗi văn bản thô.
5. **Post-processing:**
   - Hàm `sanitize_line()` lọc mỗi chuỗi thô: chỉ giữ ký tự `0–9`, bỏ khoảng trắng, dấu câu, chữ cái.
   - Các dòng rỗng sau khi lọc bị bỏ qua.
6. **Assemble & Return:**
   - Ghép tất cả dòng hợp lệ bằng `\n`.
   - Trả JSON kết quả về Frontend.

## 4. Mô hình AI

- **Hãng:** Microsoft (Hugging Face)
- **Model:** `trocr-base-handwritten`
- **Loại mô hình:** Image-to-Text (Vision Encoder — Text Decoder).
- TrOCR nhận toàn bộ một dòng ảnh và sinh chuỗi ký tự liên tục, không cần cắt từng ký tự riêng lẻ.
- **Inference:** Xử lý theo batch (mặc định 8 ảnh/lô) để tối ưu tốc độ; hỗ trợ cả CPU và CUDA.
- **Default params:** `max_new_tokens=32`, `num_beams=1` (có thể điều chỉnh qua query param).
