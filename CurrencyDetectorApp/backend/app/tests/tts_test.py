"""
Complete TTS (Text-to-Speech) Testing Suite
Tests message generation and speech output for Macedonian currency

Usage:
    python tests/test_tts.py                    # Run all tests
    python tests/test_tts.py --skip-audio       # Skip audio playback
    pytest tests/test_tts.py -v                 # Run with pytest
"""
"""
Complete TTS (Text-to-Speech) Testing Suite
Tests message generation and speech output for Macedonian currency

Usage:
    python tts_test.py                    # Run all tests
    python tts_test.py --skip-audio       # Skip audio playback
    pytest tts_test.py -v                 # Run with pytest
"""

import sys
import time
from pathlib import Path

# Додај го 'app' директориумот во sys.path за увоз на services.tts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.tts import TextToSpeech, get_tts


# Helper за печатење заглавија на тестовите
def print_test_header(test_name):
    print(f"\n{'=' * 70}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 70}")


# ===========================
# CORE TTS TESTS
# ===========================

def test_tts_initialization():
    print_test_header("TTS Initialization")
    tts_mk = TextToSpeech(language="mk")
    assert tts_mk.language == "mk"
    assert tts_mk.voice == "mk-MK-MarijaNeural"
    print("✅ Macedonian TTS initialized")

    tts_en = TextToSpeech(language="en")
    assert tts_en.language == "en"
    assert tts_en.voice == "en-US-GuyNeural"
    print("✅ English TTS initialized")
    return True


def test_no_detection():
    print_test_header("No Detection")
    tts = TextToSpeech(language="mk")
    result = {"success": False, "type": None, "detections": []}
    message = tts.generate_currency_message(result)
    print(f"Message: {message}")
    assert "не е детектирана" in message.lower()
    print("✅ No detection message correct")
    return True


def test_single_banknote():
    print_test_header("Single Banknote")
    tts = TextToSpeech(language="mk")
    for class_name, display_name in tts.MKD_CURRENCY_NAMES.items():
        if not class_name.endswith("note"):
            continue
        result = {"success": True, "type": "note", "detections": [{"class_name": class_name, "confidence": 0.95}]}
        message = tts.generate_currency_message(result)
        print(f"  {class_name}: {message}")
        assert display_name in message
        assert "банкнота" in message.lower()
    print("✅ All banknote messages correct")
    return True


def test_single_coin():
    print_test_header("Single Coin")
    tts = TextToSpeech(language="mk")
    for class_name, display_name in tts.MKD_CURRENCY_NAMES.items():
        if not class_name.endswith("coin"):
            continue
        result = {"success": True, "type": "coin", "detections": [{"class_name": class_name, "confidence": 0.90}]}
        message = tts.generate_currency_message(result)
        print(f"  {class_name}: {message}")
        assert display_name in message
        assert "монета" in message.lower()
    print("✅ All coin messages correct")
    return True


def test_multiple_same_currency():
    print_test_header("Multiple Same Currency")
    tts = TextToSpeech(language="mk")
    result = {"success": True, "type": "note", "detections": [
        {"class_name": "10_note", "confidence": 0.95},
        {"class_name": "10_note", "confidence": 0.94},
        {"class_name": "10_note", "confidence": 0.93}
    ]}
    message = tts.generate_currency_message(result)
    print(f"Message: {message}")
    assert "3" in message or "три" in message.lower()
    print("✅ Multiple same currency message correct")
    return True


def test_multiple_different_currencies():
    print_test_header("Multiple Different Currencies")
    tts = TextToSpeech(language="mk")
    result = {"success": True, "type": "note", "detections": [
        {"class_name": "50_note", "confidence": 0.96},
        {"class_name": "50_note", "confidence": 0.94},
        {"class_name": "10_note", "confidence": 0.93},
        {"class_name": "5_coin", "confidence": 0.91},
        {"class_name": "2_coin", "confidence": 0.88},
    ]}
    message = tts.generate_currency_message(result)
    print(f"Message: {message}")
    print("✅ Multiple different currencies message generated")
    return True


def test_mixed_notes_and_coins():
    print_test_header("Mixed Notes and Coins")
    tts = TextToSpeech(language="mk")
    result = {"success": True, "type": "note", "detections": [
        {"class_name": "100_note", "confidence": 0.97},
        {"class_name": "50_note", "confidence": 0.95},
        {"class_name": "10_coin", "confidence": 0.92},
        {"class_name": "5_coin", "confidence": 0.90},
        {"class_name": "2_coin", "confidence": 0.88},
    ]}
    message = tts.generate_currency_message(result)
    print(f"Message: {message}")
    print("✅ Mixed currency message generated")
    return True


# ===========================
# AUDIO TESTS
# ===========================

def test_speech_output(play_audio=True):
    print_test_header("Speech Output (Audio)")
    if not play_audio:
        print("⏭️ Skipping audio")
        return True
    tts = TextToSpeech(language="mk")
    messages = [
        "Детектирана банкнота: 100 денари",
        "Детектирана монета: 5 денари",
        "Детектирани 3 банкноти",
        "Не е детектирана валута"
    ]
    for i, m in enumerate(messages, 1):
        print(f"  {i}. Speaking: {m}")
        success = tts.speak(m)
        print(f"  {'✅' if success else '⚠️'} Speech {'successful' if success else 'failed'}")
    print("✅ All speech tests completed")
    return True


def test_announce_detection(play_audio=True):
    print_test_header("Announce Detection (Full Pipeline)")
    if not play_audio:
        print("⏭️ Skipping audio")
        return True
    tts = TextToSpeech(language="mk")
    results = [
        {"success": True, "type": "note", "detections": [{"class_name": "2000_note", "confidence": 0.96}]},
        {"success": True, "type": "coin", "detections": [{"class_name": "10_coin", "confidence": 0.92}]},
        {"success": True, "type": "note", "detections": [
            {"class_name": "50_note", "confidence": 0.94},
            {"class_name": "10_note", "confidence": 0.93}
        ]}
    ]
    for i, res in enumerate(results, 1):
        print(f"  Test {i}:")
        success = tts.announce_detection(res)
        print(f"  {'✅' if success else '⚠️'} Announcement {'successful' if success else 'failed'}")
    print("✅ All announcements completed")
    return True


def test_announce_all_currency(play_audio=True):
    print_test_header("Announce All Macedonian Currency")
    tts = get_tts(language="mk")
    audio_dir = Path(__file__).resolve().parent / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    for class_name, display_name in tts.MKD_CURRENCY_NAMES.items():
        type_str = "note" if class_name.endswith("note") else "coin"
        result = {"success": True, "type": type_str, "detections": [{"class_name": class_name, "confidence": 0.95}]}
        filename = audio_dir / f"{class_name}.mp3"
        print(f"➡️ {display_name} -> {filename.name}")
        tts.announce_detection(result, filename=filename, play_audio=play_audio)
    print("✅ All Macedonian currency announced and saved")
    return True


# ===========================
# HELPER TESTS
# ===========================

def test_singleton_pattern():
    print_test_header("Singleton Pattern")
    tts1 = get_tts(language="mk")
    tts2 = get_tts(language="mk")
    assert tts1 is tts2
    print("✅ Singleton pattern works correctly")
    return True


def test_english_tts():
    print_test_header("English TTS")
    tts = TextToSpeech(language="en")
    result = {"success": True, "type": "note", "detections": [{"class_name": "100_note", "confidence": 0.95}]}
    message = tts.generate_currency_message(result)
    print(f"Message: {message}")
    assert "detected" in message.lower() or "banknote" in message.lower()
    print("✅ English message generation works")
    return True


def test_edge_cases():
    print_test_header("Edge Cases")
    tts = TextToSpeech(language="mk")
    for res in [
        {"success": True, "type": "note", "detections": []},
        {"success": True, "type": "note", "detections": [{"class_name": "unknown_currency", "confidence": 0.50}]},
        {"success": True, "type": "coin", "detections": [{"class_name": "5_coin", "confidence": 0.10}]}
    ]:
        msg = tts.generate_currency_message(res)
        print(f"  Result: {msg}")
    print("✅ Edge cases handled")
    return True


# ===========================
# RUNNER
# ===========================

def run_all_tests(play_audio=True):
    print("\n" + "=" * 70)
    print("MACEDONIAN CURRENCY TTS - COMPLETE TEST SUITE")
    print("=" * 70)
    tests = [
        ("Initialization", test_tts_initialization),
        ("No Detection", test_no_detection),
        ("Single Banknote", test_single_banknote),
        ("Single Coin", test_single_coin),
        ("Multiple Same", test_multiple_same_currency),
        ("Multiple Different", test_multiple_different_currencies),
        ("Mixed Currencies", test_mixed_notes_and_coins),
        ("Singleton Pattern", test_singleton_pattern),
        ("English TTS", test_english_tts),
        ("Edge Cases", test_edge_cases),
    ]
    results = []
    for name, func in tests:
        try:
            func()
            results.append((name, True))
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append((name, False))
    # Audio tests
    if play_audio:
        audio_tests = [
            ("Speech Output", lambda: test_speech_output(True)),
            ("Announce Detection", lambda: test_announce_detection(True)),
            ("Announce All Currency", lambda: test_announce_all_currency(True))
        ]
        for name, func in audio_tests:
            try:
                func()
                results.append((name, True))
            except Exception as e:
                print(f"❌ Audio test failed: {e}")
                results.append((name, False))
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, r in results:
        print(f"{'✅' if r else '❌'} - {name}")
    print(f"\nPassed: {passed}/{total}")
    print("=" * 70)
    return passed == total


def main():
    play_audio = "--skip-audio" not in sys.argv
    if "--skip-audio" in sys.argv:
        print("\nℹ️ Audio playback disabled (--skip-audio flag)")
    else:
        print("\nℹ️ Audio playback enabled (use --skip-audio to disable)")
        print("   Make sure your speakers are on!")
    success = run_all_tests(play_audio=play_audio)
    sys.exit(0 if success else 1)



if __name__ == "__main__":
    main()
