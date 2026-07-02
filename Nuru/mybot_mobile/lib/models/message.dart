class Message {
  final String id;
  final String role;
  final String content;
  final String timestamp;

  Message({
    required this.id,
    required this.role,
    required this.content,
    required this.timestamp,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id']?.toString() ?? '',
      role: json['role']?.toString() ?? 'user',
      content: json['content']?.toString() ?? '',
      timestamp: json['timestamp']?.toString() ?? '',
    );
  }

  factory Message.fromSocket(Map<String, dynamic> data) {
    return Message(
      id: data['id']?.toString() ?? DateTime.now().millisecondsSinceEpoch.toString(), // The backend doesn't seem to pass message_id in some emit, fallback to timestamp
      role: data['role']?.toString() ?? 'user',
      content: data['content']?.toString() ?? '',
      timestamp: data['timestamp']?.toString() ?? '',
    );
  }

  bool get isFromUser => role == 'user';
  bool get isAi => role == 'assistant' || role == 'bot';
}
