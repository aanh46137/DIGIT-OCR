// App.jsx - Root component
import { useState } from "react";

import UploadImage from "./components/UploadImage";
import DrawImage from "./components/DrawImage";
import ResultPanel from "./components/ResultPanel";
import { predictImage } from "./services/api";

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState(0); // 0: Tab Upload, 1: Tab Bảng vẽ

  // Luồng xử lý gọi API chung cho cả 2 chế độ (File ảnh tải lên hoặc File ảnh vẽ trực tiếp)
  const handlePredict = async (imageFile) => {
    try {
      setLoading(true);
      setError("");
      setResult(null);

      const response = await predictImage(imageFile);
      setResult(response);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Prediction failed. Make sure the backend is running.",
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">Digit OCR</h1>
        <p className="app-subtitle">Handwritten digit recognition</p>
      </header>

      {/* Thanh điều hướng Tab */}
      <div className="tabs-container">
        <button
          className={`tab-btn ${activeTab === 0 ? "active" : ""}`}
          onClick={() => setActiveTab(0)}
        >
          📸 Upload Image
        </button>
        <button
          className={`tab-btn ${activeTab === 1 ? "active" : ""}`}
          onClick={() => setActiveTab(1)}
        >
          ✏️ Draw Direct
        </button>
      </div>

      {/* Khu vực hiển thị Component dựa trên Tab đang chọn */}
      <div className="tab-content-wrapper">
        {activeTab === 0 && (
          <UploadImage onPredict={handlePredict} loading={loading} />
        )}
        {activeTab === 1 && (
          <DrawImage onPredict={handlePredict} loading={loading} />
        )}
      </div>

      {error && <div className="error-message">⚠️ {error}</div>}

      <ResultPanel result={result} />
    </div>
  );
}

export default App;
