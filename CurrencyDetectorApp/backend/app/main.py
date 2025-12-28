from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import io
from utils.inference import detector

app = FastAPI(title="MKD Currency Detector")

@app.get("/")
def read_root():
    return {"message": "MKD Currency Detector API is running"}

@app.post("/detect")
async def detect_currency(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        results = detector.detect(image)

        return JSONResponse(content=results)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting MKD Currency Detector API...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    # Remove reload=True when running directly
    uvicorn.run(app, host="0.0.0.0", port=8000)