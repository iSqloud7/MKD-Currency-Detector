from typing import Optional, Dict, Any


class TextToSpeech:

    def __init__(self, language: str = "mk"):
        self.language = language
        self.engine = None

        try:
            import pyttsx3
            self.engine = pyttsx3.init()

            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.9)

            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)

            print("TTS initialized successfully!")
        except Exception as e:
            print(f"Failed to initialize TTS: {e}")
            self.engine = None

    def speak(self, text: str, save_to_file: Optional[str] = None) -> bool:
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
            print(f"TTS error: {e}")
            return False

    def generate_currency_message(self, detection_result: Dict[str, Any]) -> str:
        if not detection_result.get("success"):
            return "Грешка при детекција!" if self.language == "mk" else "Detection error!"

        currency_type = detection_result.get("type", "none")
        detections = detection_result.get("detections", [])
        count = len(detections)

        if currency_type == "none" or count == 0:
            return "Не е детектирана валута!" if self.language == "mk" else "No currency detected!"

        if self.language == "mk":
            type_str = "банкнота" if currency_type == "banknote" else "монета"

            if count == 1:
                det = detections[0]
                class_name = det.get('class_name', 'unknown')
                return f"Детектирана {type_str}: {class_name}"
            else:
                return f"Детектирани {count} {type_str}"
        else:
            type_str = "banknote" if currency_type == "banknote" else "coin"

            if count == 1:
                det = detections[0]
                return f"Detected {type_str}: {det['class_name']}"
            else:
                return f"Detected {count} {type_str}s"

    def get_speech_text(self, detection_result: Dict[str, Any]) -> str:
        return self.generate_currency_message(detection_result)

    def announce_detection(self, detection_result: Dict[str, Any],
                           save_to_file: Optional[str] = None) -> bool:
        message = self.generate_currency_message(detection_result)
        print(f"TTS: {message}")
        return self.speak(message, save_to_file)


_tts = None


def get_tts(language: str = "mk") -> TextToSpeech:
    global _tts
    if _tts is None:
        _tts = TextToSpeech(language=language)
    return _tts


def speak(text: str, language: str = "mk") -> bool:
    tts = get_tts(language)
    return tts.speak(text)


def announce_currency(detection_result: Dict[str, Any], language: str = "mk") -> bool:
    tts = get_tts(language)
    return tts.announce_detection(detection_result)
