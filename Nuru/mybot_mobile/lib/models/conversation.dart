class Conversation {
  final String id;
  final String clientName;
  final String lastMessage;
  final String lastTimestamp;
  final int unreadCount;

  Conversation({
    required this.id, 
    required this.clientName, 
    required this.lastMessage,
    required this.lastTimestamp,
    this.unreadCount = 0,
  });

  factory Conversation.fromJson(Map<String, dynamic> json) {
    return Conversation(
      id: json['wa_id']?.toString() ?? '',
      clientName: json['client_name']?.toString() ?? json['wa_id']?.toString() ?? 'Inconnu',
      lastMessage: json['last_message']?.toString() ?? '',
      lastTimestamp: json['last_timestamp']?.toString() ?? '',
      unreadCount: json['unread_count'] as int? ?? 0,
    );
  }

  Conversation copyWith({
    String? id,
    String? clientName,
    String? lastMessage,
    String? lastTimestamp,
    int? unreadCount,
  }) {
    return Conversation(
      id: id ?? this.id,
      clientName: clientName ?? this.clientName,
      lastMessage: lastMessage ?? this.lastMessage,
      lastTimestamp: lastTimestamp ?? this.lastTimestamp,
      unreadCount: unreadCount ?? this.unreadCount,
    );
  }
}
