import 'package:flutter/material.dart';

class LoadImagePicker extends StatelessWidget {
  final VoidCallback onTap;

  const LoadImagePicker({super.key, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.photo_library, size: 36, color: Colors.blue),
      onPressed: onTap,
    );
  }
}