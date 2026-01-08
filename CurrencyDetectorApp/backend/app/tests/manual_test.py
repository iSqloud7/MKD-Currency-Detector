# ============================================================================
# tests/manual_test.py
# Manual test for MKD Currency Detector
# Usage: python manual_test.py [path_to_image.jpg]
# ============================================================================

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
import cv2
import numpy as np
from PIL import Image

BASE_URL = "http://localhost:8000"


def print_test(name, passed):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    return passed


def test_imports():
    """Test if all modules can be imported."""
    print("\n" + "="*70)
    print("TEST: Module Imports")
    print("="*70)

    try:
        from core.config import DEVICE, BINARY_MODEL
        from services.inference import CurrencyDetector
        from services.extraction import extract_single_currency
        from services.preprocess import preprocess_image
        from services.tts import TextToSpeech
        print_test("All imports successful", True)
        return True
    except Exception as e:
        print_test(f"Import failed: {e}", False)
        return False


def test_config():
    """Test configuration."""
    print("\n" + "="*70)
    print("TEST: Configuration")
    print("="*70)

    try:
        from core.config import BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL

        models_exist = all(os.path.exists(p) for p in [BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL])
        print_test("Model files exist", models_exist)
        return models_exist
    except Exception as e:
        print_test(f"Config error: {e}", False)
        return False


def test_server():
    """Test if API server is running."""
    print("\n" + "="*70)
    print("TEST: API Server")
    print("="*70)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        running = response.status_code == 200
        print_test("Server is running", running)
        if running:
            print(f"   Device: {response.json().get('device')}")
        return running
    except:
        print_test("Server not running (start with: python main.py)", False)
        return False


def test_detection_local():
    """Test local detection without API."""
    print("\n" + "="*70)
    print("TEST: Local Detection")
    print("="*70)

    try:
        from core.config import BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL, DEVICE
        from services.inference import CurrencyDetector

        model_paths = {
            'binary': BINARY_MODEL,
            'banknote': BANKNOTE_MODEL,
            'coin': COIN_MODEL
        }

        detector = CurrencyDetector(model_paths, device=DEVICE)
        test_img = np.ones((640, 640, 3), dtype=np.uint8) * 255
        result = detector.detect(test_img)

        print_test("Local detection works", True)
        print(f"   Result type: {result.get('type')}")
        return True
    except Exception as e:
        print_test(f"Local detection failed: {e}", False)
        return False


def test_detection_api(image_path, expected_class=None):
    """Test detection via API, optionally check expected class_name."""
    print("\n" + "="*70)
    print("TEST: API Detection")
    print("="*70)

    if not os.path.exists(image_path):
        print_test(f"Image not found: {image_path}", False)
        return False

    try:
        with open(image_path, 'rb') as f:
            files = {"file": (Path(image_path).name, f, "image/jpeg")}
            response = requests.post(f"{BASE_URL}/detect", files=files)

        if response.status_code == 200:
            result = response.json()
            detections = result.get('detections', [])
            print_test("API detection successful", True)
            print(f"   Type: {result.get('type')}")
            print(f"   Detections: {len(detections)}")

            detected_classes = [det.get('class_name') for det in detections]
            for i, det in enumerate(detections, 1):
                print(f"   {i}. {det.get('class_name')}: {det.get('confidence'):.2%}")

            if expected_class:
                if expected_class in detected_classes:
                    print_test(f"Detected expected class '{expected_class}'", True)
                    return True
                else:
                    print_test(f"Expected '{expected_class}' but got {detected_classes}", False)
                    return False

            return True
        else:
            print_test(f"API returned status {response.status_code}", False)
            return False
    except Exception as e:
        print_test(f"API test failed: {e}", False)
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("MKD CURRENCY DETECTOR - MANUAL TEST SUITE")
    print("="*70)

    results = []

    # Basic tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("API Server", test_server()))
    results.append(("Local Detection", test_detection_local()))

    # API test with image if provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]

        # Тука може да го зададеш точниот апарат на сликата
        # На пример 10 денари:
        expected_class = "10_note"

        results.append(("API Detection", test_detection_api(image_path, expected_class)))
    else:
        print("\nℹ️  Skipping API detection test (no image provided)")
        print("   Usage: python tests/manual_test.py path/to/image.jpg")

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
