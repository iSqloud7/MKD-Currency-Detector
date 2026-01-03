import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/detection_result.dart';

class ApiService {
  Future<DetectionResult?> detectCurrency(File imageFile) async {
    try {
      final request = http.MultipartRequest(
        'POST', Uri.parse('${ApiConfig.baseUrl}${ApiConfig.detectEndpoint}'),
      );
      request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));

      final streamed = await request.send().timeout(ApiConfig.timeout);
      final response = await http.Response.fromStream(streamed);

      if (response.statusCode == 200) {
        return DetectionResult.fromJson(json.decode(response.body));
      }
      return null;
    } catch (e) {
      print("API Error: $e");
      return null;
    }
  }
}