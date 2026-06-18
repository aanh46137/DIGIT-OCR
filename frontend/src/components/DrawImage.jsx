// DrawImage.jsx - Draw Image Input
import { useRef, useState } from "react";
import { ReactSketchCanvas } from "react-sketch-canvas";

function DrawImage({ onPredict, loading }) {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);

  const handleClear = () => {
    canvasRef.current?.clearCanvas();
  };

  const handleUndo = () => {
    canvasRef.current?.undo();
  };

  const handleStrokeStart = () => {
    if (!loading) setIsDrawing(true);
  };

  const handleStrokeEnd = () => {
    setIsDrawing(false);
  };

  const handleSubmit = async () => {
    if (loading) return;

    try {
      const dataUrl = await canvasRef.current?.exportImage("png");
      if (!dataUrl) return;

      const response = await fetch(dataUrl);
      const blob = await response.blob();
      const safeFile = new File([blob], "handdrawn_digits.png", {
        type: "image/png",
      });

      onPredict(safeFile);
    } catch (error) {
      console.error("Lỗi xuất ảnh từ Canvas:", error);
    }
  };

  let containerClass = "canvas-wrapper";
  if (loading) containerClass += " predicting";
  else if (isDrawing) containerClass += " actively-drawing";

  return (
    <div className="draw-zone-container">
      <div className={containerClass}>
        <ReactSketchCanvas
          ref={canvasRef}
          strokeWidth={10}
          strokeColor="#161632"
          canvasColor="#f1f5f9"
          className="sketch-canvas"
          style={{ border: "none" }}
          onStrokeStart={handleStrokeStart}
          onStrokeEnd={handleStrokeEnd}
          allowTouchMove={!loading}
        />

        {}
        <div className="canvas-tools">
          <button
            className="tool-btn"
            onClick={handleUndo}
            title="Hoàn tác nét vẽ"
          >
            ↩ Undo
          </button>
          <button
            className="tool-btn"
            onClick={handleClear}
            title="Xóa toàn bộ"
          >
            🗑 Clear
          </button>
        </div>
      </div>

      <button className="predict-btn" onClick={handleSubmit} disabled={loading}>
        {loading ? (
          <>
            <span className="spinner" />
            Processing...
          </>
        ) : (
          "🔍 Recognize Hand-drawn Digits"
        )}
      </button>
    </div>
  );
}

export default DrawImage;
