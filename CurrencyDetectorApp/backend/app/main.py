from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from PIL import Image
import io
import base64
from typing import List
import uvicorn
from core.config import (
    BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL,
    DEVICE, USE_PREPROCESSING, USE_ENSEMBLE,
    MAX_IMAGE_SIZE
)
from services.inference import init_detector, detect_currency
from services.extraction import extract_single_currency
from core.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="MKD Currency Detector API",
    version="2.0.0",
    description="API for detecting Macedonian currency (coins and banknotes)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    try:
        model_paths = {
            'binary': BINARY_MODEL,
            'banknote': BANKNOTE_MODEL,
            'coin': COIN_MODEL
        }

        init_detector(model_paths, device=DEVICE)

        logger.info("=" * 50)
        logger.info("MKD Currency Detector API Started")
        logger.info(f"Device: {DEVICE}")
        logger.info(f"Preprocessing: {USE_PREPROCESSING}")
        logger.info(f"Ensemble voting: {USE_ENSEMBLE}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Failed to initialize detector: {e}")
        raise


@app.get("/")
async def root():
    return {
        "name": "MKD Currency Detector API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Binary classification (coin vs note)",
            "Specific denomination detection",
            "Ensemble voting for improved accuracy",
            "Image extraction with background removal",
            "Preprocessing for better detection"
        ],
        "endpoints": {
            "health": "/health",
            "detect": "/detect (POST)"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "device": DEVICE,
        "preprocessing": USE_PREPROCESSING,
        "ensemble": USE_ENSEMBLE
    }


@app.post("/detect")
async def detect(file: UploadFile = File(...), extract_images: bool = True):
    try:
        # Read and validate file
        contents = await file.read()

        if len(contents) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large. Maximum size: {MAX_IMAGE_SIZE / (1024 * 1024):.1f}MB"
            )

        try:
            pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Image decode error: {e}")
            raise HTTPException(status_code=400, detail="Invalid image file")

        try:
            result = detect_currency(image)
        except Exception as e:
            logger.error(f"Detection error: {e}")
            result = {
                'success': False,
                'message': f'Detection failed: {str(e)}',
                'type': None,
                'detections': []
            }

        detected_type = result.get('type')
        if detected_type == 'none':
            detected_type = None

        if not result.get('success', False):
            return JSONResponse({
                'success': False,
                'message': result.get('message', 'No currency detected'),
                'type': detected_type,
                'detections': [],
                'count': 0
            })

        detections_formatted = []
        for i, det in enumerate(result.get('detections', [])):
            detection_data = {
                'id': i,
                'class_name': det['class_name'],
                'confidence': det.get('ensemble_confidence', det['confidence']),
                'bbox': det['bbox']
            }

            if extract_images:
                try:
                    extracted_img = extract_single_currency(
                        image,
                        det['bbox'],
                        detected_type
                    )

                    _, buffer = cv2.imencode('.png', extracted_img)
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    detection_data['image'] = f"data:image/png;base64,{img_base64}"

                except Exception as e:
                    logger.warning(f"Image extraction failed for detection {i}: {e}")
                    detection_data['image'] = None

            detections_formatted.append(detection_data)

        return JSONResponse({
            'success': True,
            'type': detected_type,
            'detections': detections_formatted,
            'count': len(detections_formatted),
            'message': result.get('message', '')
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e),
                'type': None,
                'detections': [],
                'count': 0
            }
        )


if __name__ == "__main__":
    logger.info("Starting MKD Currency Detector API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
