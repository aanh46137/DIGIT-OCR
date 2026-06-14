# Workflow phát triển (Development Workflow)

Tài liệu này hướng dẫn cách thiết lập môi trường và chạy dự án DIGIT OCR ở chế độ phát triển (development).

## 1. Yêu cầu hệ thống

- Python 3.9+ 
- Node.js 18+ (Kèm theo npm hoặc yarn)
- Môi trường nên có đủ RAM để chứa mô hình TrOCR (cần khoảng 1.5GB không gian đĩa và bộ nhớ để khởi chạy dự án mượt mà). Không bắt buộc có GPU, mã nguồn sẽ tự nhận diện và dùng CPU nếu không có.

## 2. Setup môi trường Backend

Sử dụng môi trường ảo (`.venv`) để đảm bảo không bị xung đột với các package Python khác của hệ thống.

```bash
# Di chuyển vào gốc dự án và tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo (Trên Windows PowerShell)
.venv\Scripts\Activate.ps1

# Hoặc kích hoạt môi trường ảo (Trên Linux/MacOS)
source .venv/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r backend/requirements.txt
```

## 3. Khởi động Backend

Backend chạy bằng FastAPI và Uvicorn. Khi server khởi động ở lần đầu tiên, sẽ mất vài phút để hệ thống tiến hành tải mô hình AI từ nền tảng Hugging Face. 
Mô hình TrOCR sẽ tự động được hệ thống lưu lại vào folder `trained_models/trocr/` ở những lần khởi chạy sau.

```bash
cd backend
uvicorn app.main:app --reload
```

- Server sẽ hoạt động ở địa chỉ: `http://localhost:8000`
- API Document tự động của FastAPI có sẵn ở: `http://localhost:8000/docs`

## 4. Setup và Khởi động Frontend

Frontend sử dụng React và công cụ build Vite.

```bash
# Chuyển thư mục
cd frontend

# Cài đặt thư viện (nếu mới clone code lần đầu)
npm install

# Khởi chạy giao diện website
npm run dev
```

- Website hiển thị mặc định ở địa chỉ: `http://localhost:5173`
- Lưu ý: Frontend sử dụng Proxy qua API để gọi ngược về `localhost:8000/predict`. Nếu Backend bị tắt, ứng dụng Frontend sẽ hiển thị lỗi cảnh báo.

## 5. Sử dụng Ứng dụng

1. Truy cập vào trang web frontend `http://localhost:5173`.
2. Kéo-thả (hoặc nhấn nút Browse) để tải file hình ảnh có chứa chữ số viết tay. (Nên dùng hình ảnh có độ phân giải rõ).
3. Ấn nút Predict để Backend thực hiện xử lý hình ảnh và dự đoán kết quả bằng mô hình AI.
4. Giao diện sẽ trả về văn bản với cấu trúc xuống dòng y hệt ảnh thực tế.
