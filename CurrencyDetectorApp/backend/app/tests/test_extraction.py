# ============================================================================
# tests/test_extraction.py
# Test extraction functionality with real test_images
# Usage: python tests/test_extraction.py <image_path>
# ============================================================================

import sys
import cv2
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL, DEVICE
from services.inference import init_detector
from services.extraction import (
    extract_currency_images,
    extract_single_currency,
    create_display_grid,
    save_extracted_currencies
)


def main():
    if len(sys.argv) < 2:
        print("Usage: python tests/test_extraction.py <image_path>")
        print("Example: python tests/test_extraction.py test_images/coins.jpg")
        return

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return

    print(f"\n{'=' * 70}")
    print("CURRENCY EXTRACTION TEST")
    print(f"{'=' * 70}")
    print(f"Image: {Path(image_path).name}\n")

    # Initialize detector
    print("Initializing detector...")
    model_paths = {
        'binary': BINARY_MODEL,
        'banknote': BANKNOTE_MODEL,
        'coin': COIN_MODEL
    }
    detector = init_detector(model_paths, device=DEVICE)
    print("✅ Detector initialized\n")

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image")
        return

    print(f"✅ Image loaded: {image.shape[1]}x{image.shape[0]}\n")

    # Run detection
    print("🔍 Running detection...")
    result = detector.detect(image, use_preprocessing=True, use_ensemble=True)

    if not result['success']:
        print(f"❌ Detection failed: {result['message']}")
        return

    print(f"✅ Detection successful!")
    print(f"   Type: {result['type']}")
    print(f"   Count: {len(result['detections'])}\n")

    # Print detections
    print("Detected items:")
    for i, det in enumerate(result['detections'], 1):
        conf = det.get('ensemble_confidence', det['confidence'])
        print(f"  {i}. {det['class_name']}: {conf:.2%}")

    # Extract currency test_images
    print(f"\n{'=' * 70}")
    print("EXTRACTING IMAGES")
    print(f"{'=' * 70}\n")

    extracted_images = extract_currency_images(
        image,
        result['detections'],
        result['type']
    )

    print(f"✅ Extracted {len(extracted_images)} test_images\n")

    # Create output directory
    output_dir = Path(__file__).parent / "extracted_images"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save individual extracted test_images
    print("💾 Saving extracted test_images...")
    saved_paths = save_extracted_currencies(
        extracted_images,
        result['detections'],
        str(output_dir),
        prefix=Path(image_path).stem
    )

    for path in saved_paths:
        print(f"   ✓ {Path(path).name}")

    # Create and save grid display
    print("\n📊 Creating display grid...")
    grid = create_display_grid(
        extracted_images,
        result['detections'],
        grid_cols=3,
        cell_size=(400, 400)
    )

    grid_path = output_dir / f"{Path(image_path).stem}_grid.jpg"
    cv2.imwrite(str(grid_path), grid)
    print(f"   ✓ {grid_path.name}")

    # Save annotated original image
    print("\n🖼️  Creating annotated image...")
    annotated = image.copy()

    for i, det in enumerate(result['detections'], 1):
        x1, y1, x2, y2 = map(int, det['bbox'])
        conf = det.get('ensemble_confidence', det['confidence'])
        label = f"{i}. {det['class_name']}: {conf:.2%}"

        # Draw box
        color = (0, 255, 0) if 'note' in det['class_name'] else (255, 0, 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)

        # Draw label background
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(annotated, (x1, y1 - h - 15), (x1 + w + 10, y1), color, -1)

        # Draw label text
        cv2.putText(annotated, label, (x1 + 5, y1 - 8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    annotated_path = output_dir / f"{Path(image_path).stem}_annotated.jpg"
    cv2.imwrite(str(annotated_path), annotated)
    print(f"   ✓ {annotated_path.name}")

    print(f"\n{'=' * 70}")
    print("✅ EXTRACTION TEST COMPLETE")
    print(f"{'=' * 70}")
    print(f"\n📁 Output: {output_dir}")
    print(f"   • {len(saved_paths)} extracted test_images")
    print(f"   • 1 grid display")
    print(f"   • 1 annotated image\n")


if __name__ == "__main__":
    main()