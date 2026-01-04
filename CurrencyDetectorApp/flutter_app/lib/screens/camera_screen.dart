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

class _CameraScreenState extends State<CameraScreen> with WidgetsBindingObserver {
  late CameraController _controller;
  late Future<void> _initializeCameraFuture;

  final ApiService _api = ApiService();
  final TtsService _tts = TtsService();

  File? _imageFile;
  bool _isLoading = false;
  String _displayText = "Насочете ја камерата кон валутата";
  DetectionResult? _lastResult;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
    _checkApiHealth();
  }

  void _initializeCamera() {
    _controller = CameraController(
      widget.camera,
      ResolutionPreset.veryHigh,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.jpeg,
    );
    _initializeCameraFuture = _controller.initialize();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller.dispose();
    _tts.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Handle app lifecycle (when app goes to background/foreground)
    if (!_controller.value.isInitialized) {
      return;
    }

    if (state == AppLifecycleState.inactive) {
      _controller.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initializeCamera();
      setState(() {});
    }
  }

  Future<void> _checkApiHealth() async {
    final isHealthy = await _api.checkHealth();
    if (!isHealthy && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('⚠️ Не може да се поврзе со серверот'),
          backgroundColor: Colors.orange,
        ),
      );
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✅ Поврзан со серверот'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  Future<void> _processImage(File file) async {
    setState(() {
      _isLoading = true;
      _imageFile = file;
      _displayText = "Се анализира...";
    });

    try {
      final result = await _api.detectCurrency(file, extractImages: false);

      if (result != null) {
        setState(() {
          _lastResult = result;
          _displayText = result.toDisplayText();
        });

        // Speak result with delay to ensure it's heard
        await Future.delayed(const Duration(milliseconds: 300));
        await _tts.speak(_displayText);

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                result.success
                  ? '✅ Детекција успешна'
                  : '❌ Не е пронајдена валута'
              ),
              backgroundColor: result.success ? Colors.green : Colors.red,
              duration: const Duration(seconds: 2),
            ),
          );
        }
      } else {
        setState(() {
          _displayText = "Грешка при поврзување со серверот";
        });

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('❌ Не може да се поврзе со API'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      debugPrint('❌ Error processing image: $e');
      setState(() {
        _displayText = "Грешка: ${e.toString()}";
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _takePicture() async {
    try {
      // Ensure camera is initialized
      await _initializeCameraFuture;

      // Check if controller is initialized
      if (!_controller.value.isInitialized) {
        throw Exception('Camera not initialized');
      }

      // Take picture
      final image = await _controller.takePicture();

      if (!mounted) return;

      // Process the image
      await _processImage(File(image.path));

    } on CameraException catch (e) {
      debugPrint('❌ Camera error: ${e.code} - ${e.description}');

      if (mounted) {
        String errorMessage = 'Грешка со камерата';

        if (e.code == 'CameraAccessDenied') {
          errorMessage = 'Дозволете пристап до камерата во подесувања';
        } else if (e.code == 'CameraNotAvailable') {
          errorMessage = 'Камерата не е достапна';
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errorMessage),
            backgroundColor: Colors.red,
            action: SnackBarAction(
              label: 'OK',
              textColor: Colors.white,
              onPressed: () {},
            ),
          ),
        );
      }
    } catch (e) {
      debugPrint("❌ Camera capture error: $e");

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Грешка: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

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
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            children: [
              'img01.jpg',
              'img02.jpg',
              'img03.jpg',
              'img04.jpg'
            ].map((imgName) {
              return GestureDetector(
                onTap: () async {
                  Navigator.pop(context);

                  final byteData = await rootBundle.load('test_images/$imgName');
                  final tempDir = await getTemporaryDirectory();
                  final file = File('${tempDir.path}/$imgName');
                  await file.writeAsBytes(byteData.buffer.asUint8List());

                  _processImage(file);
                },
                child: Container(
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.asset(
                      'test_images/$imgName',
                      fit: BoxFit.cover,
                    ),
                  ),
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
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Debug Info'),
                  content: Text(
                    'Success: ${_lastResult?.success}\n'
                    'Type: ${_lastResult?.type}\n'
                    'Count: ${_lastResult?.count}\n'
                    'Detections: ${_lastResult?.detections.length}\n'
                    'Camera: ${_controller.value.isInitialized ? "Initialized" : "Not initialized"}'
                  ),
                ),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _imageFile != null
                ? Stack(
                    children: [
                      Image.file(
                        _imageFile!,
                        fit: BoxFit.contain,
                        width: double.infinity,
                      ),
                      if (_lastResult != null && _lastResult!.success)
                        Positioned(
                          top: 16,
                          right: 16,
                          child: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: Colors.green,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              '${_lastResult!.count} детекција',
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                    ],
                  )
                : FutureBuilder<void>(
                    future: _initializeCameraFuture,
                    builder: (context, snapshot) {
                      if (snapshot.connectionState == ConnectionState.done) {
                        if (_controller.value.isInitialized) {
                          return CameraPreview(_controller);
                        } else {
                          return const Center(
                            child: Text('Камерата не е достапна'),
                          );
                        }
                      } else {
                        return const Center(
                          child: CircularProgressIndicator(),
                        );
                      }
                    },
                  ),
          ),

          if (_isLoading)
            LinearProgressIndicator(
              color: Colors.green,
              backgroundColor: Colors.green[100],
            ),

          Container(
            padding: const EdgeInsets.all(16.0),
            color: Colors.grey[100],
            child: Text(
              _displayText,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),

          Padding(
            padding: const EdgeInsets.only(bottom: 40, left: 20, right: 20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                LoadImagePicker(onTap: _showAssetPicker),

                CaptureButton(
                  isLoading: _isLoading,
                  onPressed: _takePicture,
                ),

                if (_imageFile != null)
                  IconButton(
                    icon: const Icon(Icons.refresh, size: 30),
                    color: Colors.red,
                    onPressed: () {
                      setState(() {
                        _imageFile = null;
                        _lastResult = null;
                        _displayText = "Насочете ја камерата кон валутата";
                      });
                    },
                  )
                else
                  const SizedBox(width: 48),
              ],
            ),
          ),
        ],
      ),
    );
  }
}