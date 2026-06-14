// UploadImage.jsx - Upload & preview component
import { useState, useRef } from "react";

function UploadImage({ onPredict, loading }) {
    const [selectedFile, setSelectedFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const inputRef = useRef(null);

    const handleFile = (file) => {
        if (!file) return;

        // Validate image type
        if (!file.type.startsWith("image/")) {
            return;
        }

        // Read file into memory immediately to avoid ERR_UPLOAD_FILE_CHANGED
        const reader = new FileReader();
        reader.onload = (e) => {
            const arrayBuffer = e.target.result;
            const blob = new Blob([arrayBuffer], { type: file.type });
            const safeFile = new File([blob], file.name, { type: file.type });
            setSelectedFile(safeFile);

            // Preview
            const previewReader = new FileReader();
            previewReader.onload = (ev) => {
                setPreview(ev.target.result);
            };
            previewReader.readAsDataURL(blob);
        };
        reader.readAsArrayBuffer(file);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        handleFile(file);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setDragOver(true);
    };

    const handleDragLeave = () => {
        setDragOver(false);
    };

    const handleClick = () => {
        inputRef.current?.click();
    };

    const handleInputChange = (e) => {
        const file = e.target.files[0];
        handleFile(file);
    };

    const handleSubmit = () => {
        if (selectedFile && !loading) {
            onPredict(selectedFile);
        }
    };

    let zoneClass = "upload-zone";
    if (dragOver) zoneClass += " drag-over";
    if (preview) zoneClass += " has-image";

    return (
        <div>
            <div
                className={zoneClass}
                onClick={handleClick}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
            >
                <input
                    ref={inputRef}
                    type="file"
                    accept="image/*"
                    className="upload-input"
                    onChange={handleInputChange}
                />

                {preview ? (
                    <div className="preview-container">
                        <img src={preview} alt="Preview" className="preview-image" />
                        <span className="preview-filename">📄 {selectedFile.name}</span>
                    </div>
                ) : (
                    <>
                        <span className="upload-icon">📸</span>
                        <p className="upload-text">Drop an image here or click to browse</p>
                        <p className="upload-hint">Supports JPG, PNG, WEBP</p>
                    </>
                )}
            </div>

            <button
                className="predict-btn"
                onClick={handleSubmit}
                disabled={!selectedFile || loading}
            >
                {loading ? (
                    <>
                        <span className="spinner" />
                        Processing...
                    </>
                ) : (
                    "🔍 Recognize Digits"
                )}
            </button>
        </div>
    );
}

export default UploadImage;
