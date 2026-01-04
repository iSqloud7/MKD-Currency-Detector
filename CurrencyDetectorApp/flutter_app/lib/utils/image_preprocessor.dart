import 'dart:io';
import 'package:image/image.dart' as img;

/// ОВА Е КЛУЧНАТА ФУНКЦИЈА
Future<File> preprocessImage(File file) async {
  // 1️⃣ Читање на сликата како bytes
  final bytes = await file.readAsBytes();

  // 2️⃣ Decode во Image објект
  img.Image? image = img.decodeImage(bytes);
  if (image == null) return file;

  // 3️⃣ Исправка на EXIF ротација (МНОГУ ВАЖНО)
  image = img.bakeOrientation(image);

  // 4️⃣ Ако е мала резолуција → зголеми
  if (image.width < 1280) {
    image = img.copyResize(
      image,
      width: 1280,
      interpolation: img.Interpolation.linear,
    );
  }

  // 5️⃣ Зачувај како висококвалитетен JPEG
  final processedFile = File(
    '${file.parent.path}/processed_${file.uri.pathSegments.last}',
  );

  await processedFile.writeAsBytes(
    img.encodeJpg(image, quality: 95),
  );

  // 6️⃣ Debug (ќе ти помогне да видиш дали работи)
  print('📐 Processed image size: ${image.width} x ${image.height}');

  return processedFile;
}
