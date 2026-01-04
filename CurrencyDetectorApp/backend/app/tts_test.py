import sys
from utils.tts import TextToSpeech


def test_single_currency():
    """Test with single currency"""
    print("\n" + "=" * 70)
    print("TEST 1: Single Currency")
    print("=" * 70)

    tts = TextToSpeech(language="mk")

    result = {
        "success": True,
        "type": "banknote",
        "detections": [
            {"class_name": "10_note", "confidence": 0.95}
        ]
    }

    message = tts.generate_currency_message_simple(result)
    print(f"Message: {message}")
    print("Expected: Детектирана 1 10 денари")
    tts.speak(message)


def test_multiple_same_currency():
    """Test with multiple of the same currency"""
    print("\n" + "=" * 70)
    print("TEST 2: Multiple Same Currency")
    print("=" * 70)

    tts = TextToSpeech(language="mk")

    result = {
        "success": True,
        "type": "banknote",
        "detections": [
            {"class_name": "10_note", "confidence": 0.95},
            {"class_name": "10_note", "confidence": 0.93},
            {"class_name": "10_note", "confidence": 0.91}
        ]
    }

    message = tts.generate_currency_message_simple(result)
    print(f"Message: {message}")
    print("Expected: Детектирани 3 10 денари")
    tts.speak(message)


def test_multiple_different_currencies():
    """Test with multiple different currencies (your example)"""
    print("\n" + "=" * 70)
    print("TEST 3: Multiple Different Currencies")
    print("=" * 70)

    tts = TextToSpeech(language="mk")

    result = {
        "success": True,
        "type": "mixed",
        "detections": [
            {"class_name": "10_note", "confidence": 0.95},
            {"class_name": "10_note", "confidence": 0.93},
            {"class_name": "10_note", "confidence": 0.91},
            {"class_name": "2_coin", "confidence": 0.88},
            {"class_name": "2_coin", "confidence": 0.87},
            {"class_name": "1_coin", "confidence": 0.85}
        ]
    }

    message = tts.generate_currency_message_simple(result)
    print(f"Message: {message}")
    print("Expected: Детектирани 3 10 денари, 2 2 денари и 1 1 денар")
    tts.speak(message)


def test_complex_mix():
    """Test with complex mix of notes and coins"""
    print("\n" + "=" * 70)
    print("TEST 4: Complex Mix")
    print("=" * 70)

    tts = TextToSpeech(language="mk")

    result = {
        "success": True,
        "type": "mixed",
        "detections": [
            {"class_name": "50_note", "confidence": 0.96},
            {"class_name": "50_note", "confidence": 0.94},
            {"class_name": "10_note", "confidence": 0.93},
            {"class_name": "5_coin", "confidence": 0.91},
            {"class_name": "5_coin", "confidence": 0.90},
            {"class_name": "5_coin", "confidence": 0.89},
            {"class_name": "2_coin", "confidence": 0.87},
            {"class_name": "1_coin", "confidence": 0.85}
        ]
    }

    message = tts.generate_currency_message_simple(result)
    print(f"Message: {message}")
    print("Expected: Детектирани 2 50 денари, 1 10 денари, 3 5 денари, 1 2 денари и 1 1 денар")
    tts.speak(message)


def test_detailed_format():
    """Test detailed format with denomination types"""
    print("\n" + "=" * 70)
    print("TEST 5: Detailed Format (with note/coin types)")
    print("=" * 70)

    tts = TextToSpeech(language="mk")

    result = {
        "success": True,
        "type": "mixed",
        "detections": [
            {"class_name": "10_note", "confidence": 0.95},
            {"class_name": "10_note", "confidence": 0.93},
            {"class_name": "2_coin", "confidence": 0.88},
            {"class_name": "1_coin", "confidence": 0.85}
        ]
    }

    message = tts.generate_currency_message(result)  # Using detailed format
    print(f"Message: {message}")
    print("Expected: Детектирани 2 банкноти од 10 денари, 1 монета од 2 денари и 1 монета од 1 денар")
    tts.speak(message)


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("MULTI-CURRENCY TTS TESTING")
    print("=" * 70)

    tests = [
        test_single_currency,
        test_multiple_same_currency,
        test_multiple_different_currencies,
        test_complex_mix,
        test_detailed_format
    ]

    for test_func in tests:
        try:
            test_func()
            print("✅ Test passed\n")
        except Exception as e:
            print(f"❌ Test failed: {e}\n")

        # Pause between tests
        import time
        time.sleep(2)

    print("=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()