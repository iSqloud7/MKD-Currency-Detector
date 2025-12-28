"""
Comprehensive test suite for MKD Currency Detector backend
Run with: pytest test_backend.py -v
"""

import pytest
import sys
import os
from pathlib import Path
from PIL import Image
import numpy as np
import io

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Create FastAPI test client"""
    from main import app
    return TestClient(app)


@pytest.fixture
def sample_image():
    """Create a sample test image (640x640 RGB)"""
    img = Image.new('RGB', (640, 640), color='white')
    return img


@pytest.fixture
def image_bytes(sample_image):
    """Convert sample image to bytes"""
    img_byte_arr = io.BytesIO()
    sample_image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr


# ============================================================================
# UNIT TESTS - Config
# ============================================================================

class TestConfig:
    """Test configuration settings"""

    def test_config_imports(self):
        """Test that config module can be imported"""
        from config import DEVICE, IMAGE_SIZE, BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL
        assert DEVICE in ["cuda", "cpu"]
        assert IMAGE_SIZE == 640
        assert BINARY_MODEL.endswith("binary_model.torchscript")

    def test_model_files_exist(self):
        """Test that model files exist"""
        from config import BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL

        assert os.path.exists(BINARY_MODEL), f"Binary model not found: {BINARY_MODEL}"
        assert os.path.exists(BANKNOTE_MODEL), f"Banknote model not found: {BANKNOTE_MODEL}"
        assert os.path.exists(COIN_MODEL), f"Coin model not found: {COIN_MODEL}"


# ============================================================================
# UNIT TESTS - Preprocessing
# ============================================================================

class TestPreprocessing:
    """Test image preprocessing utilities"""

    def test_preprocess_image(self, sample_image):
        """Test image preprocessing"""
        from utils.preprocess import preprocess_image

        processed = preprocess_image(sample_image, target_size=640)

        assert processed is not None
        assert processed.shape[0] == 640
        assert processed.shape[1] == 640
        assert len(processed.shape) == 3  # H, W, C

    def test_preprocess_different_sizes(self):
        """Test preprocessing with different input sizes"""
        from utils.preprocess import preprocess_image

        test_sizes = [(100, 200), (640, 480), (1920, 1080)]

        for w, h in test_sizes:
            img = Image.new('RGB', (w, h), color='blue')
            processed = preprocess_image(img, target_size=640)

            assert processed.shape[0] == 640
            assert processed.shape[1] == 640


# ============================================================================
# UNIT TESTS - Inference
# ============================================================================

class TestInference:
    """Test inference pipeline"""

    def test_detector_initialization(self):
        """Test that detector can be initialized"""
        from utils.inference import CurrencyDetector

        detector = CurrencyDetector()
        assert detector.binary_model is not None
        assert detector.banknote_model is not None
        assert detector.coin_model is not None

    def test_detect_returns_dict(self, sample_image):
        """Test that detect returns proper dictionary"""
        from utils.inference import detector

        result = detector.detect(sample_image)

        assert isinstance(result, dict)
        assert "type" in result
        assert "detections" in result

    def test_detect_empty_image(self):
        """Test detection on blank image"""
        from utils.inference import detector

        blank_img = Image.new('RGB', (640, 640), color='black')
        result = detector.detect(blank_img)

        assert result["type"] in ["none", "banknote", "coin"]
        assert isinstance(result["detections"], list)


# ============================================================================
# UNIT TESTS - TTS
# ============================================================================

class TestTTS:
    """Test text-to-speech functionality"""

    def test_tts_initialization(self):
        """Test TTS can be initialized"""
        from utils.tts import TextToSpeech

        tts = TextToSpeech(language="mk")
        assert tts.language == "mk"

    def test_generate_currency_message_none(self):
        """Test message generation for no detection"""
        from utils.tts import TextToSpeech

        tts = TextToSpeech(language="mk")
        result = {
            "success": True,
            "type": "none",
            "detections": []
        }

        message = tts.generate_currency_message(result)
        assert "детектирана" in message.lower()

    def test_generate_currency_message_banknote(self):
        """Test message generation for banknote detection"""
        from utils.tts import TextToSpeech

        tts = TextToSpeech(language="mk")
        result = {
            "success": True,
            "type": "banknote",
            "detections": [
                {"class_name": "10 денари", "confidence": 0.95}
            ]
        }

        message = tts.generate_currency_message(result)
        assert "банкнота" in message.lower()
        assert "10 денари" in message

    def test_generate_currency_message_english(self):
        """Test message generation in English"""
        from utils.tts import TextToSpeech

        tts = TextToSpeech(language="en")
        result = {
            "success": True,
            "type": "coin",
            "detections": [
                {"class_name": "5 denar", "confidence": 0.90}
            ]
        }

        message = tts.generate_currency_message(result)
        assert "coin" in message.lower()


# ============================================================================
# API TESTS - Endpoints
# ============================================================================

class TestAPIEndpoints:
    """Test FastAPI endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_detect_endpoint_success(self, client, image_bytes):
        """Test detection endpoint with valid image"""
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
        response = client.post("/detect", files=files)

        assert response.status_code == 200
        result = response.json()
        assert "type" in result
        assert "detections" in result

    def test_detect_endpoint_no_file(self, client):
        """Test detection endpoint without file"""
        response = client.post("/detect")
        assert response.status_code == 422  # Validation error

    def test_detect_endpoint_invalid_file(self, client):
        """Test detection endpoint with non-image file"""
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        response = client.post("/detect", files=files)

        # Should either reject or return error
        assert response.status_code in [400, 500]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for complete pipeline"""

    def test_full_pipeline_banknote(self, client):
        """Test complete pipeline with banknote image"""
        # Create a more realistic test image
        img = Image.new('RGB', (1920, 1080), color=(100, 150, 200))

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)

        files = {"file": ("banknote.jpg", img_byte_arr, "image/jpeg")}
        response = client.post("/detect", files=files)

        assert response.status_code == 200
        result = response.json()

        # Verify structure
        assert "type" in result
        assert "detections" in result
        assert isinstance(result["detections"], list)

    def test_tts_integration(self):
        """Test TTS integration with detection results"""
        from utils.tts import announce_currency

        result = {
            "success": True,
            "type": "banknote",
            "detections": [
                {"class_name": "50 денари", "confidence": 0.95}
            ]
        }

        # Should not raise exception
        announce_currency(result, language="mk")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance and stress tests"""

    def test_detector_inference_time(self, sample_image):
        """Test inference time is reasonable"""
        import time
        from utils.inference import detector

        start = time.time()
        result = detector.detect(sample_image)
        duration = time.time() - start

        # Should complete within 5 seconds
        assert duration < 5.0, f"Inference too slow: {duration}s"

    def test_multiple_requests(self, client, image_bytes):
        """Test multiple consecutive requests"""
        for i in range(5):
            image_bytes.seek(0)
            files = {"file": (f"test{i}.jpg", image_bytes, "image/jpeg")}
            response = client.post("/detect", files=files)
            assert response.status_code == 200


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])