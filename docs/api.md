# Tài liệu API (API Documentation)

Hệ thống cung cấp một endpoint chính để nhận diện văn bản (chữ số viết tay) từ hình ảnh.

## 1. Endpoint: `/predict`

- **Phương thức:** `POST`
- **Mô tả:** Nhận một tệp hình ảnh, xử lý cắt dòng và dùng mô hình TrOCR để nhận diện toàn bộ văn bản trong ảnh.
- **Content-Type:** `multipart/form-data`

### Tham số Request

| Tên tham số | Loại | Mặc định | Mô tả |
| :--- | :--- | :---: | :--- |
| `file` | Form Data (File) | - | Tệp hình ảnh chứa một hoặc nhiều dòng chữ số. Định dạng hỗ trợ: PNG, JPEG, JPG, BMP, TIFF. Tối đa 10MB. |
| `max_new_tokens` | Query (int) | 32 | Số ký tự tối đa mô hình có thể sinh ra trên mỗi dòng (từ 1 đến 256). |
| `num_beams` | Query (int) | 1 | Kích thước Beam Search khi sinh chữ. Giá trị cao hơn cho kết quả chính xác hơn nhưng chậm hơn (từ 1 đến 10). |

### Phản hồi (Response) thành công (200 OK)

Trả về dữ liệu JSON chứa tên file và chuỗi dự đoán (có chứa ký tự xuống dòng `\n` thực tế giữa các dòng).

```json
{
  "filename": "test_image.jpg",
  "prediction": "0123456\n789"
}
```

### Phản hồi lỗi (Error Responses)

- **400 Bad Request:** Lỗi khi tệp rỗng, dung lượng vượt quá giới hạn, hoặc không tìm thấy dòng chữ nào trong ảnh.
- **415 Unsupported Media Type:** Định dạng tệp không được hỗ trợ.
- **500 Internal Server Error:** Lỗi bất ngờ trong quá trình xử lý của máy chủ.

Ví dụ JSON trả về khi có lỗi:
```json
{
  "detail": "No text lines detected in the image."
}
```

## 2. Endpoint: `/health`

- **Phương thức:** `GET`
- **Mô tả:** Kiểm tra trạng thái hoạt động của server.

### Phản hồi (200 OK)

```json
{
  "status": "ok"
}
```
