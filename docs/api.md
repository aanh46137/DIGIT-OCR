# Tài liệu API (API Documentation)

Hệ thống cung cấp các endpoint để nhận diện văn bản (chữ số viết tay) từ hình ảnh và kiểm tra trạng thái server.

## 1. Endpoint: `POST /predict`

- **Phương thức:** `POST`
- **Mô tả:** Nhận một tệp hình ảnh, thực hiện tách dòng bằng Contour Detection và dùng mô hình TrOCR (batch inference) để nhận diện toàn bộ chữ số trong ảnh. Kết quả được lọc để chỉ giữ ký tự số `0–9`.
- **Content-Type:** `multipart/form-data`

### Tham số Request

| Tên tham số | Loại | Mặc định | Mô tả |
| :--- | :--- | :---: | :--- |
| `file` | Form Data (File) | — | Tệp hình ảnh chứa một hoặc nhiều dòng chữ số. Định dạng hỗ trợ: PNG, JPEG, JPG, BMP, TIFF. Tối đa 10 MB. |
| `max_new_tokens` | Query (int) | 32 | Số ký tự tối đa mô hình có thể sinh ra trên mỗi dòng (từ 1 đến 256). |
| `num_beams` | Query (int) | 1 | Kích thước Beam Search khi sinh chữ. Giá trị cao hơn cho kết quả chính xác hơn nhưng chậm hơn (từ 1 đến 10). |

### Phản hồi (Response) thành công (200 OK)

Trả về dữ liệu JSON chứa tên file và chuỗi dự đoán (chỉ gồm chữ số `0–9`, các dòng phân cách bằng ký tự xuống dòng `\n` thực tế).

```json
{
  "filename": "test_image.jpg",
  "prediction": "0123456\n789"
}
```

### Phản hồi lỗi (Error Responses)

- **400 Bad Request:** File rỗng, dung lượng vượt quá 10 MB, không tìm thấy dòng chữ nào trong ảnh, hoặc không trích xuất được số hợp lệ nào sau khi lọc.
- **415 Unsupported Media Type:** Định dạng file không được hỗ trợ.
- **500 Internal Server Error:** Lỗi bất ngờ trong quá trình xử lý của máy chủ.

Ví dụ JSON trả về khi có lỗi:
```json
{
  "detail": "No text lines detected in the image."
}
```

```json
{
  "detail": "No valid numbers could be extracted from the image."
}
```

---

## 2. Endpoint: `GET /health`

- **Phương thức:** `GET`
- **Mô tả:** Kiểm tra trạng thái hoạt động của server. Không yêu cầu tham số. Dùng để health-check trong Docker hoặc deployment.

### Phản hồi thành công (200 OK)

```json
{
  "status": "ok"
}
```
