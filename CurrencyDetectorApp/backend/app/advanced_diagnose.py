"""
Advanced diagnostic script for currency detection
Tests different confidence thresholds and preprocessing options
Usage: python advanced_diagnose.py path/to/image.jpg
"""

import sys
import cv2
import numpy as np
from pathlib import Path
import os

from config import BINARY_MODEL, BANKNOTE_MODEL, COIN_MODEL, DEVICE
from utils.inference import CurrencyDetector


def test_with_threshold(detector, image, binary_thresh, specific_thresh, name):
    """Test detection with specific thresholds"""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"Binary threshold: {binary_thresh}, Specific threshold: {specific_thresh}")
    print(f"{'='*70}")

    # Temporarily modify thresholds
    original_binary = detector.binary_threshold
    original_banknote = detector.banknote_threshold
    original_coin = detector.coin_threshold

    detector.binary_threshold = binary_thresh
    detector.banknote_threshold = specific_thresh
    detector.coin_threshold = specific_thresh

    result = detector.detect(image, use_preprocessing=True, use_ensemble=True)

    # Restore original thresholds
    detector.binary_threshold = original_binary
    detector.banknote_threshold = original_banknote
    detector.coin_threshold = original_coin

    return result


def print_results(result, detailed=True):
    """Print detection results"""
    if result['success']:
        print(f"✅ Type: {result['type']}")
        print(f"✅ Count: {len(result['detections'])}")

        if detailed:
            for i, det in enumerate(result['detections'], 1):
                conf = det.get('ensemble_confidence', det['confidence'])
                bbox = det['bbox']
                print(f"   {i}. {det['class_name']}")
                print(f"      Confidence: {conf:.2%}")
                print(f"      BBox: [{bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}]")
    else:
        print(f"❌ {result['message']}")


def visualize_detections(image, result, output_path):
    """Create annotated image with all detections"""
    annotated = image.copy()

    if result['success']:
        for i, det in enumerate(result['detections'], 1):
            x1, y1, x2, y2 = map(int, det['bbox'])
            conf = det.get('ensemble_confidence', det['confidence'])
            label = f"{i}. {det['class_name']}: {conf:.2%}"

            # Different colors for different currency types
            if 'note' in det['class_name']:
                color = (0, 255, 0)  # Green for notes
            else:
                color = (255, 0, 0)  # Blue for coins

            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)

            # Draw label background
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated, (x1, y1 - h - 10), (x1 + w + 5, y1), color, -1)

            # Draw label text
            cv2.putText(annotated, label, (x1 + 2, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imwrite(output_path, annotated)
    print(f"\n💾 Saved annotated image: {output_path}")


def test_individual_models(detector, image):
    """Test each model individually to diagnose issues"""
    print(f"\n{'='*70}")
    print("INDIVIDUAL MODEL TESTING")
    print(f"{'='*70}")

    # Test binary model
    print("\n1. Testing BINARY model (coin vs note):")
    binary_results = detector.detect_with_confidence_filter(
        image, detector.models['binary'], 0.15
    )
    print(f"   Found {len(binary_results)} detections")
    for i, det in enumerate(binary_results, 1):
        bbox = det['bbox']
        print(f"   {i}. {det['class_name']}: {det['confidence']:.2%}")
        print(f"      BBox: [{bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}]")

    # Test coin model
    print("\n2. Testing COIN model:")
    coin_results = detector.detect_with_confidence_filter(
        image, detector.models['coin'], 0.15
    )
    print(f"   Found {len(coin_results)} detections")
    for i, det in enumerate(coin_results, 1):
        bbox = det['bbox']
        print(f"   {i}. {det['class_name']}: {det['confidence']:.2%}")
        print(f"      BBox: [{bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}]")

    # Test banknote model
    print("\n3. Testing BANKNOTE model:")
    note_results = detector.detect_with_confidence_filter(
        image, detector.models['banknote'], 0.15
    )
    print(f"   Found {len(note_results)} detections")
    for i, det in enumerate(note_results, 1):
        bbox = det['bbox']
        print(f"   {i}. {det['class_name']}: {det['confidence']:.2%}")
        print(f"      BBox: [{bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}]")

    print(f"\n📊 ANALYSIS:")
    print(f"   Binary found: {len(binary_results)} objects")
    print(f"   Coin model found: {len(coin_results)} coins")
    print(f"   Note model found: {len(note_results)} notes")
    print(f"   Expected total: {len(coin_results) + len(note_results)} detections")


def main():
    if len(sys.argv) < 2:
        print("Usage: python advanced_diagnose.py <image_path>")
        return

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return

    print(f"\n{'='*70}")
    print(f"ADVANCED CURRENCY DETECTION DIAGNOSTICS")
    print(f"{'='*70}")
    print(f"Image: {Path(image_path).name}")

    # Initialize detector
    model_paths = {
        'binary': BINARY_MODEL,
        'banknote': BANKNOTE_MODEL,
        'coin': COIN_MODEL
    }
    detector = CurrencyDetector(model_paths, device=DEVICE)

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return

    print(f"Image size: {image.shape[1]}x{image.shape[0]}")

    # Test individual models first
    test_individual_models(detector, image)

    # Test with different threshold combinations
    threshold_tests = [
        (0.35, 0.45, "Current Settings (Conservative)"),
        (0.25, 0.30, "Moderate Settings"),
        (0.20, 0.25, "Aggressive Settings (Recommended)"),
        (0.15, 0.20, "Very Aggressive Settings"),
    ]

    best_result = None
    best_count = 0
    best_name = ""

    for binary_t, specific_t, name in threshold_tests:
        result = test_with_threshold(detector, image, binary_t, specific_t, name)
        print_results(result, detailed=True)

        count = len(result.get('detections', []))
        if count > best_count:
            best_count = count
            best_result = result
            best_name = name

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"\nBest result: {best_name}")
    print(f"Detected: {best_count} objects")

    if best_result:
        # Create output directory
        output_dir = "diagnosed_images"
        os.makedirs(output_dir, exist_ok=True)

        # Visualize best result
        output_path = os.path.join(output_dir, f"diagnosed_{Path(image_path).name}")
        visualize_detections(image, best_result, output_path)

        # Print recommendations
        print(f"\n{'='*70}")
        print("RECOMMENDATIONS")
        print(f"{'='*70}")

        if best_count < 3 and 'Aggressive' in best_name:
            print("\n⚠️  Detection is still struggling. Consider:")
            print("   1. Retrain models with more diverse data")
            print("   2. Check if image quality is sufficient")
            print("   3. Ensure currencies are clearly visible")
            print("   4. Try better lighting conditions")
        elif best_count >= 3:
            print("\n✅ Good detection! Update config.py with:")
            if "Very Aggressive" in best_name:
                print("   BINARY_CONFIDENCE = 0.15")
                print("   BANKNOTE_CONFIDENCE = 0.20")
                print("   COIN_CONFIDENCE = 0.20")
            elif "Aggressive" in best_name:
                print("   BINARY_CONFIDENCE = 0.20")
                print("   BANKNOTE_CONFIDENCE = 0.25")
                print("   COIN_CONFIDENCE = 0.25")
            else:
                print("   BINARY_CONFIDENCE = 0.25")
                print("   BANKNOTE_CONFIDENCE = 0.30")
                print("   COIN_CONFIDENCE = 0.30")


if __name__ == "__main__":
    main()