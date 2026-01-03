class DetectionResult {
  final String status;
  final ResultData result;
  final String text;

  DetectionResult({required this.status, required this.result, required this.text});

  factory DetectionResult.fromJson(Map<String, dynamic> json) {
    return DetectionResult(
      status: json['status'] ?? 'error',
      result: ResultData.fromJson(json['result'] ?? {}),
      text: json['text'] ?? 'Непозната грешка',
    );
  }
}

class ResultData {
  final bool success;
  final String type;
  final List<Detection> detections;
  final int count;

  ResultData({required this.success, required this.type, required this.detections, required this.count});

  factory ResultData.fromJson(Map<String, dynamic> json) {
    return ResultData(
      success: json['success'] ?? false,
      type: json['type'] ?? 'none',
      detections: (json['detections'] as List<dynamic>?)
          ?.map((e) => Detection.fromJson(e))
          .toList() ?? [],
      count: json['count'] ?? 0,
    );
  }
}

class Detection {
  final String className;
  final double confidence;

  Detection({required this.className, required this.confidence});

  factory Detection.fromJson(Map<String, dynamic> json) {
    return Detection(
      className: json['class_name'] ?? 'Unknown',
      confidence: (json['confidence'] ?? 0).toDouble(),
    );
  }
}