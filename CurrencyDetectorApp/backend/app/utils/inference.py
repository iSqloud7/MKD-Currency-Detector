import torch
from ultralytics import YOLO
from utils.preprocess import preprocess_image
from config import BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL, DEVICE
import warnings

# Suppress YOLO warnings
warnings.filterwarnings('ignore')

class CurrencyDetector:
    def __init__(self):
        print("Loading models...")
        # Specify task explicitly to avoid warnings
        self.binary_model = YOLO(BINARY_MODEL, task='detect')
        self.banknote_model = YOLO(BANKNOTE_MODEL, task='detect')
        self.coin_model = YOLO(COIN_MODEL, task='detect')
        print("✅ All models loaded")

    def detect(self, image):
        binary_results = self.binary_model(image, verbose=False)  # Add verbose=False

        if len(binary_results[0].boxes) == 0:
            return {"success": True, "type": "none", "detections": []}

        currency_type = int(binary_results[0].boxes[0].cls[0])

        if currency_type == 0:
            results = self.banknote_model(image, verbose=False)  # Add verbose=False
            type_name = "banknote"
        else:
            results = self.coin_model(image, verbose=False)  # Add verbose=False
            type_name = "coin"

        detections = []
        for box in results[0].boxes:
            detections.append({
                "class_id": int(box.cls[0]),
                "class_name": results[0].names[int(box.cls[0])],
                "confidence": float(box.conf[0]),
                "bbox": box.xyxy[0].tolist()
            })

        return {
            "success": True,
            "type": type_name,
            "detections": detections,
            "count": len(detections)
        }

detector = CurrencyDetector()