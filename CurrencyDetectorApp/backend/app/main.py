from fastapi import FastAPI, File, UploadFile
import numpy as np
import cv2
from utils.inference import process_image

app = FastAPI(title="MKD Currency Detector")

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    cv2.imwrite("temp.jpg", img)  # времено за YOLO pipeline

    img_rgb, coins, notes, results = process_image("temp.jpg", bg_removal_method='circular')

    response = {
        "coins": [{"class":c['class'], "confidence":c['confidence']} for c in coins],
        "notes": [{"class":n['class'], "confidence":n['confidence']} for n in notes]
    }
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)