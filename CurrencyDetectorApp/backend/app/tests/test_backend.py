# ============================================================================
# tests/test_backend.py
# Comprehensive pytest test suite for backend
# Usage: pytest tests/test_backend.py -v
# ============================================================================

import pytest
import sys
import os
from pathlib import Path
from PIL import Image
import io
import cv2
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def client():
    """Create FastAPI test client."""
    from main import app
    return TestClient(app)


@pytest.fixture
def sample_image():
    """Create a sample test image (640x640 RGB)."""
    img = Image.new('RGB', (640, 640), color='white')
    return img


@pytest.fixture
def sample_image_cv2():
    """Create a sample OpenCV image."""
    return np.ones((640, 640, 3), dtype=np.uint8) * 255


@pytest.fixture
def image_bytes(sample_image):
    """Convert sample image to bytes."""
    img_byte_arr = io.BytesIO()
    sample_image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr


@pytest.fixture(scope="session")
def detector():
    """Initialize detector once for all tests."""
    from core.config import BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL, DEVICE
    from services.inference import CurrencyDetector

    model_paths = {
        "binary": BINARY_MODEL,
        "banknote": BANKNOTE_MODEL,
        "coin": COIN_MODEL
    }

    return CurrencyDetector(model_paths=model_paths, device=DEVICE)


# ============================================================================
# TEST CONFIG
# ============================================================================

class TestConfig:
    """Test configuration module."""

    def test_config_imports(self):
        """Test that config can be imported."""
        from core.config import DEVICE, IMAGE_SIZE, BINARY_MODEL
        assert DEVICE in ["cuda", "cpu"]
        assert IMAGE_SIZE == 640
        assert BINARY_MODEL is not None

    def test_model_files_exist(self):
        """Test that all model files exist."""
        from core.config import BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL
        assert os.path.exists(BINARY_MODEL), f"Binary model not found: {BINARY_MODEL}"
        assert os.path.exists(BANKNOTE_MODEL), f"Banknote model not found: {BANKNOTE_MODEL}"
        assert os.path.exists(COIN_MODEL), f"Coin model not found: {COIN_MODEL}"

    def test_confidence_thresholds(self):
        """Test confidence threshold values."""
        from core.config import BINARY_CONFIDENCE, BANKNOTE_CONFIDENCE, COIN_CONFIDENCE
        assert 0 < BINARY_CONFIDENCE < 1
        assert 0 < BANKNOTE_CONFIDENCE < 1
        assert 0 < COIN_CONFIDENCE < 1


# ============================================================================
# TEST PREPROCESSING
# ============================================================================

class TestPreprocessing:
    """Test image preprocessing."""

    def test_preprocess_image(self, sample_image_cv2):
        """Test basic preprocessing."""
        from services.preprocess import preprocess_image
        processed, _ = preprocess_image(sample_image_cv2, target_size=640)
        assert processed.shape[:2] == (640, 640)
        assert len(processed.shape) == 3
        assert processed.shape[2] == 3

    def test_preprocess_different_sizes(self):
        """Test preprocessing with different image sizes."""
        from services.preprocess import preprocess_image

        test_sizes = [(100, 200), (640, 480), (1920, 1080), (480, 640)]

        for w, h in test_sizes:
            img = np.ones((h, w, 3), dtype=np.uint8) * 128
            processed, scale = preprocess_image(img, target_size=640)
            assert max(processed.shape[:2]) == 640, f"Failed for size {w}x{h}"
            assert len(processed.shape) == 3
            assert processed.shape[2] == 3

    def test_preprocess_grayscale(self):
        """Test preprocessing with grayscale image."""
        from services.preprocess import preprocess_image

        gray_img = np.ones((640, 480), dtype=np.uint8) * 128
        processed, scale = preprocess_image(gray_img, target_size=640)
        assert max(processed.shape[:2]) == 640
        assert len(processed.shape) == 3
        assert processed.shape[2] == 3


# ============================================================================
# TEST INFERENCE
# ============================================================================

class TestInference:
    """Test inference/detection."""

    def test_detector_initialization(self, detector):
        """Test detector is properly initialized."""
        assert 'binary' in detector.models
        assert 'banknote' in detector.models
        assert 'coin' in detector.models

    def test_detect_returns_dict(self, detector, sample_image_cv2):
        """Test detect method returns proper dict structure."""
        result = detector.detect(sample_image_cv2)
        assert isinstance(result, dict)
        assert "success" in result
        assert "type" in result
        assert "detections" in result
        assert "message" in result

    def test_detect_with_preprocessing(self, detector, sample_image_cv2):
        """Test detection with preprocessing enabled."""
        result = detector.detect(sample_image_cv2, use_preprocessing=True)
        assert isinstance(result, dict)
        assert isinstance(result["detections"], list)

    def test_detect_without_preprocessing(self, detector, sample_image_cv2):
        """Test detection without preprocessing."""
        result = detector.detect(sample_image_cv2, use_preprocessing=False)
        assert isinstance(result, dict)

    def test_detect_with_ensemble(self, detector, sample_image_cv2):
        """Test detection with ensemble voting."""
        result = detector.detect(sample_image_cv2, use_ensemble=True)
        assert isinstance(result, dict)

    def test_calculate_iou(self, detector):
        """Test IoU calculation."""
        box1 = [0, 0, 100, 100]
        box2 = [50, 50, 150, 150]
        iou = detector.calculate_iou(box1, box2)
        assert 0 <= iou <= 1

        # Same box should have IoU = 1
        iou_same = detector.calculate_iou(box1, box1)
        assert iou_same == 1.0

        # No overlap should have IoU = 0
        box3 = [200, 200, 300, 300]
        iou_none = detector.calculate_iou(box1, box3)
        assert iou_none == 0.0


# ============================================================================
# TEST EXTRACTION
# ============================================================================

class TestExtraction:
    """Test currency image extraction."""

    def test_extract_single_currency_banknote(self):
        """Test extracting single banknote."""
        from services.extraction import extract_single_currency

        image = np.ones((640, 480, 3), dtype=np.uint8) * 200
        bbox = [100, 100, 400, 300]

        extracted = extract_single_currency(image, bbox, 'note')
        assert extracted.size > 0
        assert len(extracted.shape) == 3

    def test_extract_single_currency_coin(self):
        """Test extracting single coin (with background removal)."""
        from services.extraction import extract_single_currency

        image = np.ones((640, 480, 3), dtype=np.uint8) * 200
        bbox = [200, 200, 350, 350]

        extracted = extract_single_currency(image, bbox, 'coin')
        assert extracted.size > 0
        assert extracted.shape[2] == 4  # BGRA (with alpha channel)

    def test_extract_currency_images(self):
        """Test extracting multiple currencies."""
        from services.extraction import extract_currency_images

        image = np.ones((640, 480, 3), dtype=np.uint8) * 200
        detections = [
            {'bbox': [100, 100, 200, 200], 'class_name': 'coin'},
            {'bbox': [250, 100, 450, 250], 'class_name': 'note'}
        ]

        extracted = extract_currency_images(image, detections, 'coin')
        assert len(extracted) == 2

    def test_create_display_grid(self):
        """Test creating display grid."""
        from services.extraction import create_display_grid

        images = [
            np.ones((100, 100, 3), dtype=np.uint8) * 255,
            np.ones((100, 100, 3), dtype=np.uint8) * 128
        ]
        detections = [
            {'class_name': '10_note', 'confidence': 0.95},
            {'class_name': '5_coin', 'confidence': 0.88}
        ]

        grid = create_display_grid(images, detections, grid_cols=2, cell_size=(300, 300))
        assert grid.shape[0] == 300  # 1 row
        assert grid.shape[1] == 600  # 2 cols

    def test_remove_background_circular(self):
        """Test circular background removal."""
        from services.extraction import remove_background_circular

        # Create circular coin-like image
        image = np.ones((200, 200, 3), dtype=np.uint8) * 150
        cv2.circle(image, (100, 100), 80, (255, 200, 100), -1)

        result = remove_background_circular(image)
        assert result.shape[2] == 4  # BGRA
        assert result.shape[:2] == image.shape[:2]

    def test_enhance_banknote(self):
        """Test banknote enhancement."""
        from services.extraction import enhance_banknote

        image = np.ones((300, 600, 3), dtype=np.uint8) * 100
        enhanced = enhance_banknote(image)
        assert enhanced.shape == image.shape
        assert enhanced.shape[2] == 3  # BGR


# ============================================================================
# TEST API ENDPOINTS
# ============================================================================

class TestAPIEndpoints:
    """Test FastAPI endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "message" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "device" in data

    def test_detect_endpoint_success(self, client, image_bytes):
        """Test detect endpoint with valid image."""
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
        response = client.post("/detect", files=files)
        assert response.status_code == 200
        result = response.json()
        assert "success" in result
        assert "type" in result
        assert "detections" in result

    def test_detect_endpoint_no_file(self, client):
        """Test detect endpoint without file."""
        response = client.post("/detect")
        assert response.status_code == 422  # Validation error

    def test_detect_endpoint_invalid_file(self, client):
        """Test detect endpoint with invalid file."""
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        response = client.post("/detect", files=files)
        assert response.status_code in [400, 422]


# ============================================================================
# TEST TTS
# ============================================================================

class TestTTS:
    """Test text-to-speech functionality."""

    def test_tts_initialization(self):
        """Test TTS initialization."""
        from services.tts import TextToSpeech
        tts = TextToSpeech(language="mk")
        assert tts.language == "mk"

    def test_generate_message_no_detection(self):
        """Test message generation with no detections."""
        from services.tts import TextToSpeech
        tts = TextToSpeech(language="mk")

        result = {"success": False, "detections": []}
        message = tts.generate_currency_message(result)
        assert "не е детектирана" in message.lower() or "no currency" in message.lower()

    def test_generate_message_single_banknote(self):
        """Test message for single banknote."""
        from services.tts import TextToSpeech
        tts = TextToSpeech(language="mk")

        result = {
            "success": True,
            "type": "note",
            "detections": [{"class_name": "10_note", "confidence": 0.95}]
        }
        message = tts.generate_currency_message(result)
        assert "10 денари" in message or "денари" in message

    def test_generate_message_single_coin(self):
        """Test message for single coin."""
        from services.tts import TextToSpeech
        tts = TextToSpeech(language="mk")

        result = {
            "success": True,
            "type": "coin",
            "detections": [{"class_name": "5_coin", "confidence": 0.90}]
        }
        message = tts.generate_currency_message(result)
        assert "5 денари" in message or "денари" in message


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests."""

    def test_full_detection_pipeline(self, detector, sample_image_cv2):
        """Test complete detection pipeline."""
        result = detector.detect(
            sample_image_cv2,
            use_preprocessing=True,
            use_ensemble=True
        )
        assert isinstance(result, dict)
        assert "success" in result
        assert "detections" in result

    def test_api_with_extraction(self, client, image_bytes):
        """Test API detection with image extraction."""
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
        response = client.post("/detect?extract_images=true", files=files)
        assert response.status_code == 200


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
