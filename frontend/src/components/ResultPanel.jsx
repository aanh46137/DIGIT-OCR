// ResultPanel.jsx - OCR result display
function ResultPanel({ result }) {

    if (!result) {
        return null;
    }

    return (

        <div className="result-panel">

            <div className="result-header">
                <span>✅</span>
                <h2>Recognition Result</h2>
            </div>

            <div className="result-body">

                <div className="prediction-display">
                    <div className="prediction-label">
                        Detected Digits
                    </div>
                    <div className="prediction-value">
                        {result.prediction}
                    </div>
                </div>

                <div className="result-stats">
                    <div className="stat-card">
                        <div className="stat-label">
                            Filename
                        </div>
                        <div className="stat-value">
                            {result.filename}
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-label">
                            Lines
                        </div>
                        <div className="stat-value">
                            {result.prediction.split("\n").length}
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-label">
                            Characters
                        </div>
                        <div className="stat-value">
                            {result.prediction.replace(/\n/g, "").length}
                        </div>
                    </div>
                </div>

            </div>

        </div>

    );
}

export default ResultPanel;