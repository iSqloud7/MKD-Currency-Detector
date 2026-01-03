import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'app.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final cameras = await availableCameras();
  runApp(App(camera: cameras.first));
}