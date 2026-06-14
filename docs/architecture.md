# Kiến trúc hệ thống (System Architecture)

## 1. Tổng quan

Dự án Digit OCR là một ứng dụng Web dùng để nhận diện chữ số viết tay trên nhiều dòng văn bản, sử dụng mô hình học sâu **TrOCR** (Transformer-based Optical Character Recognition) của Microsoft. 

Luồng dữ liệu chính:
`Frontend (React/Vite)` ➔ `FastAPI Backend` ➔ `Image Preprocessing (OpenCV)` ➔ `Line Segmentation` ➔ `TrOCR Model (Hugging Face)` ➔ `Frontend Display`

## 2. Các thành phần chính

### 2.1. Frontend (`frontend/`)
- **Công nghệ:** React, Vite, Axios.
- **Tính năng:** Giao diện kéo-thả ảnh hiện đại với thiết kế dark-theme, gửi ảnh dưới dạng form-data qua cổng Proxy của Vite (cổng 5173). Kết quả được trả về sẽ có thể hiển thị chính xác các ký tự theo từng dòng.
- **Mã nguồn chính:** `App.jsx`, `UploadImage.jsx`, `ResultPanel.jsx`, `api.js`.

### 2.2. Backend (`backend/app/`)
- **Công nghệ:** FastAPI, PyTorch, Transformers, OpenCV, Uvicorn.
- **Tính năng:** Chứa API Gateway và toàn bộ logic xử lý ảnh và chạy AI model.
- **Cấu trúc thư mục:**
  - `routers/prediction.py`: Định nghĩa HTTP endpoint `/predict`, hứng file upload, thực hiện kiểm tra định dạng và kích thước.
  - `services/prediction_service.py`: Điều phối toàn bộ quy trình nhận diện: Xử lý ảnh -> Tách dòng -> Chạy TrOCR -> Nối chuỗi kết quả.
  - `models/model_loader.py`: Tải mô hình TrOCR (`microsoft/trocr-base-handwritten`) từ Hugging Face và lưu bộ nhớ đệm (cache) vào ổ đĩa nội bộ (`trained_models/trocr/`) để tải cực nhanh trong những lần khởi động lại.
  - `utils/image_processing.py`: Chứa các hàm xử lý ảnh cấp thấp (đọc bytes sang numpy array, nhị phân hóa ảnh bằng phương pháp Otsu, chuyển đổi ảnh grayscale qua PIL RGB).
  - `utils/digit_detection.py`: Thực hiện chức năng cắt tách văn bản thành từng dòng bằng biểu đồ chiếu ngang (horizontal projection profile).

## 3. Quy trình Xử lý Nhận diện (OCR Pipeline)

Quy trình nhận diện chi tiết khi một ảnh được gửi đến Backend:

1. **Decode:** Đọc chuỗi byte của ảnh và giải mã thành ảnh đen trắng (Grayscale).
2. **Binarize:** Sử dụng ngưỡng Otsu để tách riêng nét mực (màu trắng) và nền (màu đen).
3. **Line Segmentation:** 
   - Cộng tổng mật độ điểm sáng theo từng hàng ngang của ảnh nhị phân.
   - Tìm các ranh giới dòng văn bản để tách rời các dòng (bỏ qua khoảng trống ở giữa).
4. **Predict (TrOCR):**
   - Với mỗi dòng ảnh được cắt ra, chuyển đổi thành chuẩn màu RGB của thư viện PIL.
   - Truyền từng ảnh vào bộ mã hóa `VisionEncoderDecoderModel` (TrOCR).
   - Dùng Beam Search sinh chuỗi văn bản (được giới hạn bởi `max_new_tokens` và `num_beams`).
5. **Assemble:** 
   - Gộp kết quả của tất cả các dòng bằng ký tự xuống dòng `\n` thực tế.
   - Trả JSON kết quả về phía Frontend.

## 4. Mô hình AI

- **Hãng:** Microsoft (Hugging Face)
- **Model:** `trocr-base-handwritten`
- **Loại mô hình:** Image-to-Text (Vision Encoder - Text Decoder).
- Thay vì chỉ nhận diện từng ký tự đơn lẻ giống CNN, TrOCR nhận diện liên tục toàn bộ các ký tự trên một dòng ảnh mà không cần cắt tách từng chữ số.
