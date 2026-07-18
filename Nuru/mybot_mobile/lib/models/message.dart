class Message {
  final String id;
  final String role;
  final String content;
  final String timestamp;
  final String? messageType;
  final String? mediaUrl;
  final String? messageStatus;

  Message({
    required this.id,
    required this.role,
    required this.content,
    required this.timestamp,
    this.messageType,
    this.mediaUrl,
    this.messageStatus,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id']?.toString() ?? '',
      role: json['role']?.toString() ?? 'user',
      content: json['content']?.toString() ?? '',
      timestamp: json['timestamp']?.toString() ?? '',
      messageType: json['message_type']?.toString(),
      mediaUrl: json['media_url']?.toString(),
      messageStatus: json['message_status']?.toString(),
    );
  }

  factory Message.fromSocket(Map<String, dynamic> data) {
    return Message(
      id: data['id']?.toString() ?? data['message_id']?.toString() ?? DateTime.now().millisecondsSinceEpoch.toString(), // The backend doesn't seem to pass message_id in some emit, fallback to timestamp
      role: data['role']?.toString() ?? 'user',
      content: data['content']?.toString() ?? '',
      timestamp: data['timestamp']?.toString() ?? '',
      messageType: data['message_type']?.toString(),
      mediaUrl: data['media_url']?.toString(),
      messageStatus: data['message_status']?.toString() ?? (data['status']?.toString()),
    );
  }

  bool get isFromUser => role == 'user';
  bool get isAi => role == 'assistant' || role == 'bot';
}

