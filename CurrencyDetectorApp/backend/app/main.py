"""
Enhanced Currency Detection API with Image Extraction
Returns both full image detection and extracted currency images
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import cv2
import numpy as np
from PIL import Image
import io
import base64
from typing import List, Dict

from config import (
    BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL,
    DEVICE, USE_PREPROCESSING, USE_ENSEMBLE
)
from utils.inference import init_detector, detect_currency
from utils.extraction import extract_currency_images

# Initialize FastAPI
app = FastAPI(title="MKD Currency Detector API v2.0")


# Initialize detector on startup
@app.on_event("startup")
async def startup_event():
    """Initialize models on server startup"""
    model_paths = {
        'binary': BINARY_MODEL,
        'banknote': BANKNOTE_MODEL,
        'coin': COIN_MODEL
    }

    init_detector(model_paths, device=DEVICE)
    print(f"✅ Detector initialized on {DEVICE}")
    print(f"   Preprocessing: {USE_PREPROCESSING}")
    print(f"   Ensemble voting: {USE_ENSEMBLE}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MKD Currency Detector API v2.0",
        "features": [
            "Currency detection",
            "Image extraction",
            "Background removal for coins"
        ],
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "device": DEVICE,
        "preprocessing": USE_PREPROCESSING,
        "ensemble": USE_ENSEMBLE
    }


@app.post("/detect")
async def detect(file: UploadFile = File(...), extract_images: bool = True):
    """
    Detect currency in uploaded image

    Args:
        file: Uploaded image file
        extract_images: If True, extract individual currency images

    Returns:
        Detection results with optional extracted images
    """
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Run detection
        result = detect_currency(image)

        if not result['success']:
            return JSONResponse({
                'success': False,
                'message': result['message'],
                'type': result.get('type'),
                'detections': []
            })

        # Format detections
        detections_formatted = []

        for i, det in enumerate(result['detections']):
            detection_data = {
                'id': i,
                'class_name': det['class_name'],
                'confidence': det.get('ensemble_confidence', det['confidence']),
                'bbox': det['bbox']
            }

            # Extract individual currency image if requested
            if extract_images:
                extracted_img = extract_currency_image(
                    image,
                    det['bbox'],
                    result['type']
                )

                # Convert to base64
                _, buffer = cv2.imencode('.png', extracted_img)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                detection_data['image'] = f"data:image/png;base64,{img_base64}"

            detections_formatted.append(detection_data)

        return JSONResponse({
            'success': True,
            'type': result['type'],
            'detections': detections_formatted,
            'count': len(detections_formatted)
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )


def extract_currency_image(image: np.ndarray, bbox: List[float], currency_type: str) -> np.ndarray:
    """
    Extract individual currency image from detection

    Args:
        image: Original image
        bbox: Bounding box [x1, y1, x2, y2]
        currency_type: 'coin' or 'note'

    Returns:
        Extracted currency image (with background removed for coins)
    """
    x1, y1, x2, y2 = map(int, bbox)

    # Add padding
    padding = 10
    h, w = image.shape[:2]
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)

    cropped = image[y1:y2, x1:x2].copy()

    if cropped.size == 0:
        return np.zeros((100, 100, 3), dtype=np.uint8)

    # For coins, remove background (circular mask)
    if currency_type == 'coin':
        return remove_background_circular(cropped)
    else:
        # For banknotes, just return cropped image
        return cropped


def remove_background_circular(image: np.ndarray) -> np.ndarray:
    """
    Remove background from coin image using circular mask

    Args:
        image: Cropped coin image

    Returns:
        Image with transparent background (BGRA)
    """
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Create circular mask
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Try to detect circle
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=50,
        param1=50,
        param2=30,
        minRadius=int(min(image.shape[:2]) * 0.3),
        maxRadius=int(max(image.shape[:2]) * 0.6)
    )

    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    if circles is not None:
        # Use detected circle
        circles = np.uint16(np.around(circles))
        circle = circles[0, 0]
        center = (circle[0], circle[1])
        radius = circle[2]
        cv2.circle(mask, center, radius, 255, -1)
    else:
        # Use ellipse as fallback
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        axes = (int(w * 0.45), int(h * 0.45))
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)

    # Smooth mask edges
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    # Apply mask
    bgra = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = mask

    return bgra


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)