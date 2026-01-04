import 'package:flutter_tts/flutter_tts.dart';

class TtsService {
  final FlutterTts _tts = FlutterTts();
  bool _isInitialized = false;

  TtsService() {
    _initialize();
  }

  Future<void> _initialize() async {
    try {
      // Check available languages
      var languages = await _tts.getLanguages;
      print('📢 Available TTS languages: $languages');

      // Check available engines
      var engines = await _tts.getEngines;
      print('📢 Available TTS engines: $engines');

      // Set language to Macedonian
      // Samsung may use different language codes
      bool languageSet = false;

      // Try different Macedonian language codes
      for (var code in ['mk-MK', 'mk', 'mkd-MKD', 'mac']) {
        try {
          var result = await _tts.setLanguage(code);
          if (result == 1) {
            print('✅ Set language to: $code');
            languageSet = true;
            break;
          }
        } catch (e) {
          print('⚠️  Failed to set language: $code');
        }
      }

      if (!languageSet) {
        print('⚠️  Could not set Macedonian, trying English');
        await _tts.setLanguage("en-US");
      }

      // Configure TTS settings
      await _tts.setSpeechRate(0.45); // Slightly slower for clarity
      await _tts.setVolume(1.0);
      await _tts.setPitch(1.0);

      // Try to set Samsung TTS engine if available
      if (engines.toString().contains('samsung')) {
        await _tts.setEngine("com.samsung.SMT");
        print('✅ Using Samsung TTS engine');
      }

      // Set up completion handler to debug
      _tts.setCompletionHandler(() {
        print('✅ TTS completed speaking');
      });

      _tts.setErrorHandler((msg) {
        print('❌ TTS error: $msg');
      });

      _isInitialized = true;
      print('✅ TTS initialized successfully');

      // Test speak
      await Future.delayed(const Duration(milliseconds: 500));
      await _testSpeak();

    } catch (e) {
      print('❌ TTS initialization failed: $e');
      _isInitialized = false;
    }
  }

  Future<void> _testSpeak() async {
    try {
      print('🔊 Testing TTS with: "Тест"');
      await _tts.speak("Тест");
    } catch (e) {
      print('❌ Test speak failed: $e');
    }
  }

  Future<void> speak(String text) async {
    if (!_isInitialized) {
      print('⚠️  TTS not initialized, attempting to reinitialize...');
      await _initialize();
    }

    try {
      print('🔊 Attempting to speak: $text');

      // Stop any ongoing speech
      await _tts.stop();

      // Small delay to ensure clean state
      await Future.delayed(const Duration(milliseconds: 100));

      // Speak the text
      var result = await _tts.speak(text);

      print('🔊 TTS speak returned: $result');

      if (result == 1) {
        print('✅ TTS speak initiated successfully');
      } else {
        print('❌ TTS speak failed (returned $result)');
      }
    } catch (e) {
      print('❌ TTS speak error: $e');
    }
  }

  Future<void> stop() async {
    await _tts.stop();
  }

  void dispose() {
    _tts.stop();
  }
}