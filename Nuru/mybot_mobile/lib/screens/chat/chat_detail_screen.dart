import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../viewmodels/chat_detail_notifier.dart';

class ChatDetailScreen extends ConsumerStatefulWidget {
  final String waId;
  final String clientName;

  const ChatDetailScreen({super.key, required this.waId, required this.clientName});

  @override
  ConsumerState<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends ConsumerState<ChatDetailScreen> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _messageController = TextEditingController();
  bool _isTyping = false;
  final FocusNode _focusNode = FocusNode();
  bool _showAttachmentPanel = false;
  bool _showEmojiPanel = false;

  String _formatTime(String? timestamp) {
    if (timestamp == null || timestamp.isEmpty || timestamp == 'now') return '';
    try {
      final DateTime d = DateTime.parse(timestamp).toLocal();
      return '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return '';
    }
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(chatDetailNotifierProvider.notifier).fetchMessages(widget.waId);
    });
    _messageController.addListener(_onTextChanged);
    _focusNode.addListener(() {
      if (_focusNode.hasFocus) {
        setState(() {
          _showAttachmentPanel = false;
          _showEmojiPanel = false;
        });
      }
    });
  }


  void _toggleEmojiPanel() async {
    if (_showEmojiPanel) {
      setState(() => _showEmojiPanel = false);
      _focusNode.requestFocus();
    } else {
      if (_focusNode.hasFocus) {
        _focusNode.unfocus();
        await Future.delayed(const Duration(milliseconds: 100)); // Prevent overflow while keyboard hides
      }
      setState(() {
        _showEmojiPanel = true;
        _showAttachmentPanel = false;
      });
    }
  }

  void _toggleAttachmentPanel() async {
    if (_showAttachmentPanel) {
      setState(() => _showAttachmentPanel = false);
      _focusNode.requestFocus();
    } else {
      if (_focusNode.hasFocus) {
        _focusNode.unfocus();
        await Future.delayed(const Duration(milliseconds: 100)); // Prevent overflow while keyboard hides
      }
      setState(() {
        _showAttachmentPanel = true;
        _showEmojiPanel = false;
      });
    }
  }

  void _onTextChanged() {
    if (_messageController.text.isNotEmpty && !_isTyping) {
      setState(() => _isTyping = true);
    } else if (_messageController.text.isEmpty && _isTyping) {
      setState(() => _isTyping = false);
    }
  }

  void _sendMessage() {
    final text = _messageController.text;
    if (text.trim().isNotEmpty) {
      ref.read(chatDetailNotifierProvider.notifier).sendMessage(widget.waId, text);
      _messageController.clear();
    }
  }

  @override
  void dispose() {
    _messageController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  Widget _attachmentPanel() {
    return SizedBox(
      height: 300,
      width: double.infinity,
      child: Card(
        margin: const EdgeInsets.all(18),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _attachmentIcon(Icons.insert_drive_file, Colors.indigo, 'Document', 'max 100MB'),
                  const SizedBox(width: 40),
                  _attachmentIcon(Icons.image, Colors.pink, 'Galerie', 'max 5MB'),
                  const SizedBox(width: 40),
                  _attachmentIcon(Icons.videocam, Colors.purpleAccent, 'Vidéo', 'max 16MB'),
                ],
              ),
              const SizedBox(height: 30),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _attachmentIcon(Icons.headset, Colors.orange, 'Audio', 'max 16MB'),
                  const SizedBox(width: 40),
                  _attachmentIcon(Icons.location_on, Colors.teal, 'Localisation', 'Carte'),
                  const SizedBox(width: 40),
                  _attachmentIcon(Icons.emoji_emotions, Colors.blue, 'Stickers', 'max 500KB'),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _attachmentIcon(IconData icon, Color bg, String text, String subtext) {
    return InkWell(
      onTap: () {
        setState(() => _showAttachmentPanel = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("$text : fonction à venir.")));
      },
      child: Column(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: bg,
            child: Icon(icon, size: 28, color: Colors.white),
          ),
          const SizedBox(height: 8),
          Text(text, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
          Text(subtext, style: const TextStyle(fontSize: 10, color: Colors.grey)),
        ],
      ),
    );
  }


  Widget _emojiPanel() {
    return SizedBox(
      height: 300,
      width: double.infinity,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            Icon(Icons.emoji_emotions, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text("Clavier Emojis à venir", style: TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final mapState = ref.watch(chatDetailNotifierProvider);
    final state = mapState[widget.waId] ?? ChatDetailState(isLoading: true, messages: [], isHumanMode: false);

    return PopScope(
      canPop: !(_showAttachmentPanel || _showEmojiPanel),
      onPopInvokedWithResult: (bool didPop, dynamic result) {
        if (didPop) return;
        if (_showAttachmentPanel || _showEmojiPanel) {
          setState(() {
            _showAttachmentPanel = false;
            _showEmojiPanel = false;
          });
        }
      },
      child: Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(
          children: [
            CircleAvatar(
              radius: 24,
              child: Text(widget.clientName.substring(0, 1).toUpperCase(), style: const TextStyle(color: Colors.white)),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(widget.clientName, style: const TextStyle(fontSize: 16)),
                ],
              ),
            ),
          ],
        ),
        actions: [
          Row(
            children: [
              Text('Mode Humain', style: TextStyle(fontSize: 12)),
              Switch(
                value: state.isHumanMode,
                activeColor: Colors.white,
                activeTrackColor: const Color(0xFF25D366),
                onChanged: (val) {
                  ref.read(chatDetailNotifierProvider.notifier).toggleHumanMode(widget.waId, val);
                },
              ),
            ],
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: state.isLoading && state.messages.isEmpty
          ? Center(child: CircularProgressIndicator())
          : state.error != null && state.messages.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('Erreur: ${state.error}', textAlign: TextAlign.center),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () => ref.read(chatDetailNotifierProvider.notifier).fetchMessages(widget.waId),
                        child: Text('Réessayer'),
                      )
                    ],
                  ),
                )
              : Column(
                  children: [
                    if (state.isLoading && state.messages.isNotEmpty)
                      const LinearProgressIndicator(),
                    Expanded(
                      child: ListView.builder(
                        reverse: true, // Start from the bottom
                          itemCount: state.messages.length,
                          itemBuilder: (context, index) {
                            // Reverse the index so the newest message is at the bottom visually
                            final reversedIndex = state.messages.length - 1 - index;
                            final msg = state.messages[reversedIndex];
                            final isMe = !msg.isFromUser;
                              final isDark = Theme.of(context).brightness == Brightness.dark;
                            
                            final bgColor = isMe 
                                ? (isDark ? const Color(0xFF005C4B) : const Color(0xFFDCF8C6)) 
                                : (isDark ? const Color(0xFF1E293B) : Colors.white);
                            final textColor = isDark ? Colors.white : Colors.black87;

                            return Align(
                              alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                              child: Container(
                                constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                                margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 12),
                                padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                                decoration: BoxDecoration(
                                  color: bgColor,
                                  borderRadius: BorderRadius.circular(12).copyWith(
                                    bottomRight: isMe ? const Radius.circular(0) : null,
                                    bottomLeft: !isMe ? const Radius.circular(0) : null,
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.05),
                                      blurRadius: 1,
                                      offset: const Offset(0, 1),
                                    ),
                                  ],
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    if (isMe && msg.isAi)
                                      Container(
                                        margin: const EdgeInsets.only(bottom: 4),
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: isDark ? Colors.white12 : Colors.black12,
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: Text(
                                          '🤖 IA',
                                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: isDark ? Colors.white70 : Colors.black54),
                                        ),
                                      ),
                                    Text(
                                      msg.content,
                                      style: TextStyle(fontSize: 15, color: textColor),
                                    ),
                                    const SizedBox(height: 4),
                                    Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Text(
                                          _formatTime(msg.timestamp), 
                                          style: TextStyle(fontSize: 10, color: isDark ? Colors.white54 : Colors.black.withOpacity(0.45)),
                                        ),
                                        if (isMe) ...[
                                          const SizedBox(width: 4),
                                          Icon(Icons.done_all, size: 14, color: isDark ? Colors.blue[300] : Colors.blue[400]),
                                        ]
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    // INPUT BAR (always visible, mimicking WA)
                    Container(
                      color: Colors.transparent,
                      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
                      child: Row(
                        children: [
                          Expanded(
                            child: Container(
                              decoration: BoxDecoration(
                                color: Theme.of(context).cardColor,
                                borderRadius: BorderRadius.circular(24),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.05),
                                    blurRadius: 2,
                                    offset: const Offset(0, 1),
                                  ),
                                ],
                              ),
                              child: Row(
                                children: [
                                  IconButton(
                                      icon: Icon(_showEmojiPanel ? Icons.keyboard : Icons.emoji_emotions_outlined, color: Colors.grey),
                                      onPressed: () {
                                        if (state.isHumanMode) {
                                          _toggleEmojiPanel();
                                        }
                                      },
                                    ),
                                  Expanded(
                                    child: TextField(
                                      focusNode: _focusNode,
                                        controller: _messageController,
                                      enabled: state.isHumanMode, // disable if IA is taking care
                                      decoration: InputDecoration(
                                        hintText: state.isHumanMode ? 'Message' : 'Passez en Mode Humain pour répondre',
                                        hintStyle: const TextStyle(color: Colors.grey, fontSize: 16),
                                        border: InputBorder.none,
                                      ),
                                      maxLines: null,
                                      keyboardType: TextInputType.multiline,
                                    ),
                                  ),
                                  IconButton(
                                      icon: Icon(Icons.attach_file, color: _showAttachmentPanel ? const Color(0xFF128C7E) : Colors.grey),
                                      onPressed: () {
                                        if (state.isHumanMode) {
                                          _toggleAttachmentPanel();
                                        } else {
                                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Passez en mode humain pour envoyer des pièces jointes.")));
                                        }
                                      },
                                    ),
                                  const SizedBox(width: 4),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          GestureDetector(
                              onTap: state.isHumanMode ? (_isTyping ? _sendMessage : () {
                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Le message vocal n'est pas encore pris en charge.")));
                              }) : null,
                              child: CircleAvatar(
                                radius: 24,
                                backgroundColor: state.isHumanMode ? const Color(0xFF128C7E) : Colors.grey,
                                child: Icon(_isTyping ? Icons.send : Icons.mic, color: Theme.of(context).cardColor, size: 24),
                              ),
                            )
                        ],
                      ),
                    ),
                    if (_showAttachmentPanel) _attachmentPanel(),
                    if (_showEmojiPanel) _emojiPanel(),
                  ],
                ),
          ),
    );
  }
}
