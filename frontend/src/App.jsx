// App.jsx - Root component
import { useState } from "react";

import UploadImage from "./components/UploadImage";
import ResultPanel from "./components/ResultPanel";
import { predictImage } from "./services/api";


function App() {

    const [result, setResult] =
        useState(null);

    const [loading, setLoading] =
        useState(false);

    const [error, setError] =
        useState("");

    const handlePredict =
        async (imageFile) => {

            try {

                setLoading(true);
                setError("");
                setResult(null);

                const response =
                    await predictImage(
                        imageFile
                    );

                setResult(response);

            } catch (err) {

                setError(
                    err.response?.data?.detail
                    || "Prediction failed. Make sure the backend is running."
                );

                console.error(err);

            } finally {

                setLoading(false);

            }
        };

    return (

        <div className="app-container">

            <header className="app-header">
                <h1 className="app-title">
                    Digit OCR
                </h1>
                <p className="app-subtitle">
                    Handwritten digit recognition
                </p>
            </header>

            <UploadImage
                onPredict={handlePredict}
                loading={loading}
            />

            {error && (
                <div className="error-message">
                    ⚠️ {error}
                </div>
            )}

            <ResultPanel
                result={result}
            />

        </div>

    );
}

export default App;