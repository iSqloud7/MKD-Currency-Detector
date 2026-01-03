import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

import '../services/api_service.dart';
import '../services/tts_service.dart';
import '../models/detection_result.dart';
import '../widgets/capture_button.dart';
import '../widgets/load_image_picker.dart';

class CameraScreen extends StatefulWidget {
  final CameraDescription camera;
  const CameraScreen({super.key, required this.camera});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  late CameraController _controller;
  late Future<void> _initializeCameraFuture;

  final ApiService _api = ApiService();
  final TtsService _tts = TtsService();

  File? _imageFile;
  bool _isLoading = false;
  String _displayText = "Насочете ја камерата кон банкнота";

  @override
  void initState() {
    super.initState();
    _controller = CameraController(
      widget.camera,
      ResolutionPreset.medium,
      enableAudio: false,
    );
    _initializeCameraFuture = _controller.initialize();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  // Функција за обработка на сликата (заедничка за камера и тест слики)
  Future<void> _processImage(File file) async {
    setState(() {
      _isLoading = true;
      _imageFile = file;
    });

    try {
      final res = await _api.detectCurrency(file);
      setState(() {
        if (res != null) {
          _displayText = res.text;
          _tts.speak(res.text);
        } else {
          _displayText = "Не успеав да препознаам валута.";
        }
      });
    } catch (e) {
      debugPrint('Error: $e');
      setState(() => _displayText = "Грешка при поврзување со серверот.");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // Специјална функција за избор на слики од Assets (test_images папка)
  void _showAssetPicker() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Избери тест слика"),
        content: SizedBox(
          width: double.maxFinite,
          child: GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            children: ['img01.jpg', 'img02.jpg', 'img03.jpg', 'img04.jpg'].map((imgName) {
              return GestureDetector(
                onTap: () async {
                  Navigator.pop(context);
                  // Конвертирање на Asset во File за да може ApiService да го прочита
                  final byteData = await rootBundle.load('test_images/$imgName');
                  final tempDir = await getTemporaryDirectory();
                  final file = File('${tempDir.path}/$imgName');
                  await file.writeAsBytes(byteData.buffer.asUint8List());
                  _processImage(file);
                },
                child: Padding(
                  padding: const EdgeInsets.all(4.0),
                  child: Image.asset('test_images/$imgName', fit: BoxFit.cover),
                ),
              );
            }).toList(),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('MKD Currency Detector'),
        centerTitle: true,
        backgroundColor: Colors.green,
      ),
      body: Column(
        children: [
          // Приказ на камера или веќе избрана слика
          Expanded(
            child: _imageFile != null
                ? Image.file(_imageFile!, fit: BoxFit.contain, width: double.infinity)
                : FutureBuilder<void>(
              future: _initializeCameraFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.done) {
                  return CameraPreview(_controller);
                } else {
                  return const Center(child: CircularProgressIndicator());
                }
              },
            ),
          ),

          if (_isLoading) const LinearProgressIndicator(color: Colors.green),

          // Текст со резултат
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Text(
              _displayText,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
          ),

          // Копчиња за акција
          Padding(
            padding: const EdgeInsets.only(bottom: 40, left: 20, right: 20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                // Копче за галерија (сега отвара Asset Picker)
                LoadImagePicker(onTap: _showAssetPicker),

                // Главно копче за сликање
                CaptureButton(
                  isLoading: _isLoading,
                  onPressed: () async {
                    try {
                      await _initializeCameraFuture;
                      final photo = await _controller.takePicture();
                      _processImage(File(photo.path));
                    } catch (e) {
                      debugPrint("Camera capture error: $e");
                    }
                  },
                ),

                // Дополнително копче за ресетирање
                if (_imageFile != null)
                  IconButton(
                    icon: const Icon(Icons.refresh, size: 30, color: Colors.red),
                    onPressed: () => setState(() {
                      _imageFile = null;
                      _displayText = "Насочете ја камерата кон банкнота";
                    }),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}