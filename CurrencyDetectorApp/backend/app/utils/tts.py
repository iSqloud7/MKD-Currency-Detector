from typing import Optional, Dict, Any


class TextToSpeech:

    def __init__(self, language: str = "mk"):
        """
        Initialize TTS

        Args:
            language: Language code (mk=Macedonian, en=English)
        """
        self.language = language
        self.engine = None

        try:
            import pyttsx3
            self.engine = pyttsx3.init()

            # Configure voice properties
            self.engine.setProperty('rate', 150)  # Speaking speed
            self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)

            # Try to set voice (optional - may not work for all languages)
            voices = self.engine.getProperty('voices')
            if voices:
                # Use first available voice
                self.engine.setProperty('voice', voices[0].id)

            print("✅ TTS initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize TTS: {e}")
            self.engine = None

    def speak(self, text: str, save_to_file: Optional[str] = None) -> bool:
        """
        Convert text to speech

        Args:
            text: Text to speak
            save_to_file: Optional path to save audio file (as .wav)

        Returns:
            Success status
        """
        if not self.engine or not text:
            return False

        try:
            if save_to_file:
                self.engine.save_to_file(text, save_to_file)
                self.engine.runAndWait()
            else:
                self.engine.say(text)
                self.engine.runAndWait()
            return True
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return False

    def generate_currency_message(self, detection_result: Dict[str, Any]) -> str:
        """
        Generate speech message from detection results

        Args:
            detection_result: Detection results dictionary

        Returns:
            Message string
        """
        if not detection_result.get("success"):
            return "Грешка при детекција" if self.language == "mk" else "Detection error"

        currency_type = detection_result.get("type", "none")
        detections = detection_result.get("detections", [])
        count = len(detections)

        # No detection
        if currency_type == "none" or count == 0:
            return "Не е детектирана валута" if self.language == "mk" else "No currency detected"

        # Build message
        if self.language == "mk":
            type_str = "банкнота" if currency_type == "banknote" else "монета"

            if count == 1:
                det = detections[0]
                class_name = det['class_name']
                # Clean up class name if needed
                return f"Детектирана {type_str}: {class_name}"
            else:
                return f"Детектирани {count} {type_str}"
        else:  # English
            type_str = "banknote" if currency_type == "banknote" else "coin"

            if count == 1:
                det = detections[0]
                return f"Detected {type_str}: {det['class_name']}"
            else:
                return f"Detected {count} {type_str}s"

    def announce_detection(self, detection_result: Dict[str, Any],
                          save_to_file: Optional[str] = None) -> bool:
        """
        Announce detection results via TTS

        Args:
            detection_result: Detection results
            save_to_file: Optional path to save audio

        Returns:
            Success status
        """
        message = self.generate_currency_message(detection_result)
        print(f"🔊 TTS: {message}")
        return self.speak(message, save_to_file)


# Global TTS instance
_tts = None

def get_tts(language: str = "mk") -> TextToSpeech:
    """Get or create TTS instance"""
    global _tts
    if _tts is None:
        _tts = TextToSpeech(language=language)
    return _tts


# Convenience functions
def speak(text: str, language: str = "mk") -> bool:
    """Quick speak function"""
    tts = get_tts(language)
    return tts.speak(text)


def announce_currency(detection_result: Dict[str, Any], language: str = "mk") -> bool:
    """Quick announce function"""
    tts = get_tts(language)
    return tts.announce_detection(detection_result)