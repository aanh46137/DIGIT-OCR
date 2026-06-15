<div align="center">

# 🔢 Digit OCR

**Handwritten digit sequence recognition powered by TrOCR**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=white)](https://react.dev/)
[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-TrOCR-FFD21E?style=flat)](https://huggingface.co/microsoft/trocr-base-handwritten)

</div>

---

## 📸 Demo

Upload an image containing handwritten digit sequences (one or multiple lines) and the system will recognize and return the full text.

**Input:** Image containing rows of handwritten digits  
**Output:** Recognized text with line breaks preserved

---

## ✨ Features

- 🖼️ **Multi-line OCR** — Automatically detects and processes multiple text lines in a single image
- 🤖 **TrOCR Model** — Uses Microsoft's `trocr-base-handwritten` transformer model for accurate recognition
- ⚡ **Fast Local Cache** — Model weights are saved to `trained_models/trocr/` after first download; subsequent server starts load from disk instantly
- 🎨 **Modern UI** — Dark-theme glassmorphism interface with drag-and-drop image upload
- 📐 **Overflow-safe Display** — Prediction output adapts gracefully for long digit sequences (40+ characters per line)

---

## 🏗️ Project Structure

```
DIGIT-OCR/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point & startup warmup
│   │   ├── routers/
│   │   │   └── prediction.py          # POST /predict endpoint
│   │   ├── services/
│   │   │   └── prediction_service.py  # OCR pipeline orchestration
│   │   ├── models/
│   │   │   └── model_loader.py        # TrOCR loader with local caching
│   │   ├── schemas/
│   │   │   └── prediction_response.py # Pydantic response models
│   │   └── utils/
│   │       ├── image_processing.py    # Decode, grayscale, binarize
│   │       └── digit_detection.py     # Horizontal projection line segmentation
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── UploadImage.jsx        # Drag-and-drop upload
│       │   └── ResultPanel.jsx        # Prediction display
│       └── services/
│           └── api.js                 # Axios API calls
├── trained_models/
│   └── trocr/                         # Auto-populated on first run
├── docs/
│   ├── api.md
│   ├── architecture.md
│   └── workflow.md
└── .gitignore
```

---

## 🚀 Quick Start

### Prerequisites

- Python **3.9+**
- Node.js **18+**
- ~1.5 GB disk space (for the TrOCR model cache)

### 1. Clone the repository

```bash
git clone [<your-repo-url>](https://github.com/aanh46137/DIGIT-OCR.git)
cd DIGIT-OCR
```

### 2. Setup Backend

```bash
# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

> ⏳ **First run only:** The server will automatically download the TrOCR model (~1.27 GB) from Hugging Face and cache it locally. This takes a few minutes. All subsequent starts will load from local disk in ~18 seconds.

Backend is available at: `http://localhost:8000`  
Interactive API docs: `http://localhost:8000/docs`

### 4. Setup & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend is available at: `http://localhost:5173`

---

## 📡 API Reference

### `POST /predict`

Accepts an image upload and returns recognized digit text.

**Request:** `multipart/form-data`

| Field | Type | Default | Description |
|---|---|:---:|---|
| `file` | File | — | Image file (PNG, JPEG, BMP, TIFF). Max 10 MB. |
| `max_new_tokens` | int | 32 | Max characters generated per line (1–256) |
| `num_beams` | int | 1 | Beam search width — higher = more accurate, slower (1–10) |

**Response (200 OK):**

```json
{
  "filename": "sample.jpg",
  "prediction": "0123456\n789"
}
```

The `prediction` field contains real newline characters (`\n`) between each recognized line.

## ⚙️ OCR Pipeline

```
Uploaded Image (bytes)
        │
        ▼
  Decode → Grayscale (OpenCV)
        │
        ▼
  Otsu Binarization (ink=255, background=0)
        │
        ▼
  Horizontal Projection → Line Segmentation
        │
        ├── Line 1 crop ──► TrOCR → "0123456"
        ├── Line 2 crop ──► TrOCR → "789"
        └── ...
        │
        ▼
  Join with "\n" → Return JSON
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| AI Model | [microsoft/trocr-base-handwritten](https://huggingface.co/microsoft/trocr-base-handwritten) |
| Backend | FastAPI, Uvicorn, PyTorch, Transformers |
| Image Processing | OpenCV, Pillow, NumPy |
| Frontend | React 18, Vite, Axios |

---

## 📄 Documentation

- [`docs/api.md`](docs/api.md) — Full API reference
- [`docs/architecture.md`](docs/architecture.md) — System architecture & pipeline details
- [`docs/workflow.md`](docs/workflow.md) — Development setup guide 
