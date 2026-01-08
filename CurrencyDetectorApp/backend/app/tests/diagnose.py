# ============================================================================
# tests/diagnose.py
# Simple diagnostic script to test currency detection
# Usage: python tests/diagnose.py path/to/image.jpg
# ============================================================================

import sys
import cv2
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL, DEVICE
from services.inference import init_detector


def print_results(result, test_name=""):
    """Print detection results."""
    if test_name:
        print(f"\n{test_name}")
        print("-" * 70)

    if result['success']:
        print(f"✅ Type: {result['type']}")
        print(f"✅ Message: {result['message']}")
        print(f"✅ Detections: {len(result['detections'])}")
        for i, det in enumerate(result['detections'], 1):
            conf = det.get('ensemble_confidence', det['confidence'])
            bbox = det['bbox']
            print(f"   {i}. {det['class_name']}: {conf:.2%}")
            print(f"      BBox: [{bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}]")
    else:
        print(f"❌ Failed: {result['message']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python tests/diagnose.py <image_path>")
        print("Example: python tests/diagnose.py test_images/2000_note.jpg")
        return

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return

    print(f"\n{'=' * 70}")
    print(f"CURRENCY DETECTION DIAGNOSTICS")
    print(f"{'=' * 70}")
    print(f"Image: {Path(image_path).name}")
    print(f"Device: {DEVICE}")

    # Initialize detector
    print("\nInitializing detector...")
    model_paths = {
        'binary': BINARY_MODEL,
        'banknote': BANKNOTE_MODEL,
        'coin': COIN_MODEL
    }

    detector = init_detector(model_paths, device=DEVICE)
    print("✅ Detector initialized")

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return

    print(f"✅ Image loaded: {image.shape[1]}x{image.shape[0]}")

    # Test with different settings
    print(f"\n{'=' * 70}")
    print("RUNNING TESTS")
    print(f"{'=' * 70}")

    print_results(
        detector.detect(image, use_preprocessing=True, use_ensemble=True),
        "Test 1: With preprocessing and ensemble (DEFAULT)"
    )

    print_results(
        detector.detect(image, use_preprocessing=False, use_ensemble=True),
        "Test 2: Without preprocessing"
    )

    print_results(
        detector.detect(image, use_preprocessing=True, use_ensemble=False),
        "Test 3: Without ensemble"
    )

    # Save annotated image
    result = detector.detect(image, use_preprocessing=True, use_ensemble=True)

    if result['success']:
        print(f"\n{'=' * 70}")
        print("CREATING DIAGNOSED IMAGE")
        print(f"{'=' * 70}")

        annotated = image.copy()
        for det in result['detections']:
            x1, y1, x2, y2 = map(int, det['bbox'])
            conf = det.get('ensemble_confidence', det['confidence'])
            label = f"{det['class_name']}: {conf:.2%}"

            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 3)

            # Draw label
            cv2.putText(annotated, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Save
        output_dir = Path(__file__).parent / "diagnosed_images"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"diagnosed_{Path(image_path).name}"

        cv2.imwrite(str(output_path), annotated)
        print(f"💾 Saved: {output_path}")

    print(f"\n{'=' * 70}")
    print("DIAGNOSTICS COMPLETE")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()