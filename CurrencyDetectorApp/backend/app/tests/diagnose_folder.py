# ============================================================================
# tests/diagnose_folder.py
# Batch diagnostic script for currency detection
# Usage:
#   python tests/diagnose_folder.py path/to/image_folder
# ============================================================================

import sys
import cv2
import os
from pathlib import Path
from collections import Counter

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL, DEVICE
from services.inference import init_detector


SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def print_results(result, image_name: str):
    print(f"\n🖼️  {image_name}")
    print("-" * 60)

    if result["success"]:
        print(f"✅ Type: {result['type']}")
        print(f"✅ Message: {result['message']}")
        print(f"✅ Detections: {len(result['detections'])}")

        for i, det in enumerate(result["detections"], 1):
            conf = det.get("ensemble_confidence", det["confidence"])
            bbox = det["bbox"]
            print(
                f"   {i}. {det['class_name']} | {conf:.2%} | "
                f"BBox [{bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}]"
            )
    else:
        print(f"❌ Failed: {result['message']}")


def annotate_and_save(image, result, output_path: Path):
    annotated = image.copy()

    for det in result["detections"]:
        x1, y1, x2, y2 = map(int, det["bbox"])
        conf = det.get("ensemble_confidence", det["confidence"])
        label = f"{det['class_name']} {conf:.2%}"

        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(
            annotated,
            label,
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    cv2.imwrite(str(output_path), annotated)


def main():
    if len(sys.argv) < 2:
        print("Usage: python tests/diagnose_folder.py <image_folder>")
        return

    image_dir = Path(sys.argv[1])

    if not image_dir.exists() or not image_dir.is_dir():
        print(f"❌ Invalid folder: {image_dir}")
        return

    images = sorted(
        p for p in image_dir.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not images:
        print("❌ No test_images found in folder")
        return

    print("=" * 70)
    print("MKD CURRENCY DETECTION – FOLDER DIAGNOSTICS")
    print("=" * 70)
    print(f"Folder: {image_dir}")
    print(f"Images found: {len(images)}")
    print(f"Device: {DEVICE}")

    # Initialize detector ONCE
    print("\nInitializing detector...")
    model_paths = {
        "binary": BINARY_MODEL,
        "banknote": BANKNOTE_MODEL,
        "coin": COIN_MODEL,
    }

    detector = init_detector(model_paths, device=DEVICE)
    print("✅ Detector initialized")

    output_dir = Path(__file__).parent / "diagnosed_images"
    output_dir.mkdir(exist_ok=True)

    stats = Counter()

    # Iterate through test_images
    for img_path in images:
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"\n❌ Could not load {img_path.name}")
            stats["load_failed"] += 1
            continue

        result = detector.detect(
            image,
            use_preprocessing=True,
            use_ensemble=True,
        )

        print_results(result, img_path.name)

        if result["success"]:
            stats["success"] += 1
            stats[result["type"]] += 1

            out_path = output_dir / f"diagnosed_{img_path.name}"
            annotate_and_save(image, result, out_path)
        else:
            stats["failed"] += 1

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total test_images: {len(images)}")
    print(f"Successful detections: {stats['success']}")
    print(f"Failed detections: {stats['failed']}")
    print(f"Coins detected: {stats['coin']}")
    print(f"Banknotes detected: {stats['note']}")
    print(f"Annotated test_images saved in: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
