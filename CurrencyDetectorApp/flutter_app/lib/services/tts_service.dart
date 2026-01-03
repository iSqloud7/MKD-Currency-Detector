import 'package:flutter_tts/flutter_tts.dart';

class TtsService {
  final FlutterTts _tts = FlutterTts();

  TtsService() {
    _tts.setLanguage("mk-MK");
    _tts.setSpeechRate(0.5);
  }

  Future<void> speak(String text) async {
    await _tts.stop();
    await _tts.speak(text);
  }
}