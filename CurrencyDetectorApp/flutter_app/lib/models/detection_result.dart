class DetectionResult {
  final bool success;
  final String? type;
  final List<Detection> detections;
  final int count;
  final String? message;

  DetectionResult({
    required this.success,
    this.type,
    required this.detections,
    required this.count,
    this.message,
  });

  factory DetectionResult.fromJson(Map<String, dynamic> json) {
    return DetectionResult(
      success: json['success'] ?? false,
      type: json['type'],
      detections: (json['detections'] as List<dynamic>?)
          ?.map((e) => Detection.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
      count: json['count'] ?? 0,
      message: json['message'],
    );
  }

  String toDisplayText() {
    if (!success || detections.isEmpty) {
      return message ?? "Не е детектирана валута";
    }

    if (detections.length == 1) {
      final det = detections.first;
      final currencyName = _formatCurrencyName(det.className);
      final typeText = type == 'coin' ? 'монета' : 'банкнота';
      final confidence = (det.confidence * 100).toStringAsFixed(0);
      return 'Детектирана $typeText: $currencyName ($confidence% сигурност)';
    } else {
      final typeText = type == 'coin' ? 'монети' : 'банкноти';
      return 'Детектирани ${detections.length} $typeText';
    }
  }

  String _formatCurrencyName(String className) {
    final Map<String, String> currencyMap = {
      '10_note': '10 денари',
      '50_note': '50 денари',
      '100_note': '100 денари',
      '200_note': '200 денари',
      '500_note': '500 денари',
      '1000_note': '1000 денари',
      '2000_note': '2000 денари',
      '5000_note': '5000 денари',
      '1_coin': '1 денар',
      '2_coin': '2 денари',
      '5_coin': '5 денари',
      '10_coin': '10 денари',
      '50_coin': '50 денари',
    };
    return currencyMap[className] ?? className.replaceAll('_', ' ');
  }
}

class Detection {
  final int id;
  final String className;
  final double confidence;
  final List<double> bbox;
  final String? image;

  Detection({
    required this.id,
    required this.className,
    required this.confidence,
    required this.bbox,
    this.image,
  });

  factory Detection.fromJson(Map<String, dynamic> json) {
    return Detection(
      id: json['id'] ?? 0,
      className: json['class_name'] ?? 'Unknown',
      confidence: (json['confidence'] ?? 0).toDouble(),
      bbox: (json['bbox'] as List<dynamic>?)
          ?.map((e) => (e as num).toDouble())
          .toList() ?? [],
      image: json['image'],
    );
  }
}