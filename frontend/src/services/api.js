// api.js - API service
import axios from "axios";

// Proxy /predict -> http://localhost:8000/predict
const API_URL = "/predict";


export const predictImage =
    async (imageFile) => {

        const formData =
            new FormData();

        formData.append(
            "file",
            imageFile
        );

        const response =
            await axios.post(
                API_URL,
                formData,
                {
                    headers: {
                        "Content-Type":
                            "multipart/form-data"
                    }
                }
            );

        return response.data;
    };