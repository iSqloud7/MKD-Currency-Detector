import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import io
from utils.inference import detector
from utils.tts import TextToSpeech
from utils.preprocess import preprocess_image
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MKD Currency Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tts_helper = TextToSpeech(language="mk")


@app.get("/")
def read_root():
    return {"message": "MKD Currency Detector API is running"}


@app.post("/detect")
async def detect_currency(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        processed = preprocess_image(image)
        results = detector.detect(processed)

        speech_text = tts_helper.get_speech_text(results)

        return {
            "status": "ok",
            "result": results,
            "text": speech_text
        }

    except Exception as e:
        print(f"Error in detect endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    print("Starting MKD Currency Detector API...")
    print("Server will be available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
