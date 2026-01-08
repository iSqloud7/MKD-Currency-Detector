import 'dart:io';
import 'package:image/image.dart' as img;

Future<File> preprocessImage(File file) async {
  final bytes = await file.readAsBytes();
  img.Image? image = img.decodeImage(bytes);
  if (image == null) return file;

  image = img.bakeOrientation(image);

  // if (image.width < 1280) {
  //   image = img.copyResize(image, width: 1280, interpolation: img.Interpolation.linear);
  // }

  if (image.width < 1920) {  // од 1280 на 1920
    image = img.copyResize(image, width: 1920, interpolation: img.Interpolation.linear);
  }

  final processedFile = File('${file.parent.path}/processed_${file.uri.pathSegments.last}');
  await processedFile.writeAsBytes(img.encodeJpg(image, quality: 95));

  print('📐 Processed image size: ${image.width} x ${image.height}');
  return processedFile;
}
