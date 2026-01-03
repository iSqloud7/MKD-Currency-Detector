import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

class AssetImagePicker extends StatelessWidget {
  final Function(File) onImageSelected;

  AssetImagePicker({super.key, required this.onImageSelected});

  // Листа на слики што ги имаш во паката test_images
  final List<String> assetImages = [
    'test_images/img01.jpg',
    'test_images/img02.jpg',
    'test_images/img03.jpg',
    'test_images/img04.jpg',
  ];

  // Функција за конвертирање на Asset во File (бидејќи API-то бара File)
  Future<void> _selectAsset(BuildContext context, String assetPath) async {
    final byteData = await rootBundle.load(assetPath);
    final file = File('${(await getTemporaryDirectory()).path}/${assetPath.split('/').last}');
    await file.writeAsBytes(byteData.buffer.asUint8List());

    onImageSelected(file);
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text("Избери тест слика"),
      content: SizedBox(
        width: double.maxFinite,
        child: GridView.builder(
          shrinkWrap: true,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2),
          itemCount: assetImages.length,
          itemBuilder: (context, index) {
            return GestureDetector(
              onTap: () => _selectAsset(context, assetImages[index]),
              child: Padding(
                padding: const EdgeInsets.all(4.0),
                child: Image.asset(assetImages[index], fit: BoxFit.cover),
              ),
            );
          },
        ),
      ),
    );
  }
}