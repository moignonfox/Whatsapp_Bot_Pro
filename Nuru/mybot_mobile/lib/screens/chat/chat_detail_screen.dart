import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../viewmodels/chat_detail_notifier.dart';
import '../../viewmodels/chat_notifier.dart';
import '../../repositories/chat_repository.dart';
import '../../models/conversation.dart';
import '../../models/message.dart';
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:just_audio/just_audio.dart';
import 'package:emoji_picker_flutter/emoji_picker_flutter.dart';
import 'dart:async';

import '../../core/api/api_client.dart';
import 'widgets/client_profile_sheet.dart';

class ChatDetailScreen extends ConsumerStatefulWidget {
  final String waId;
  final String clientName;

  const ChatDetailScreen({super.key, required this.waId, required this.clientName});

  @override
  ConsumerState<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends ConsumerState<ChatDetailScreen> with WidgetsBindingObserver {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _messageController = TextEditingController();
  bool _isTyping = false;
  final FocusNode _focusNode = FocusNode();
  bool _showAttachmentPanel = false;
  bool _showEmojiPanel = false;
  
  String _currentClientName = '';
  
  // Recording
  final AudioRecorder _audioRecorder = AudioRecorder();
  bool _isRecording = false;
  String? _recordFilePath;
  
  // WhatsApp-style Recording UI state
  bool _isRecordingLocked = false;
  int _recordDuration = 0;
  Timer? _recordTimer;
  double _dragPositionDx = 0;
  double _dragPositionDy = 0;
  final AudioPlayer _beepPlayer = AudioPlayer();

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _scrollController.dispose();
    _messageController.dispose();
    _focusNode.dispose();
    _audioRecorder.dispose();
    _recordTimer?.cancel();
    _beepPlayer.dispose();
    super.dispose();
  }

  String _getFullMediaUrl(String path) {
    if (path.startsWith('http')) return path;
    String baseUrl = apiClient.options.baseUrl.replaceAll('/api/v1', '');
    if (baseUrl.endsWith('/')) {
      baseUrl = baseUrl.substring(0, baseUrl.length - 1);
    }
    if (!path.startsWith('/')) {
      path = '/$path';
    }
    return '$baseUrl$path';
  }

  Widget _buildMessageContent(Message msg, Color textColor, bool isMe, bool isDark) {
    if (msg.messageType == 'image') {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: msg.mediaUrl != null
                ? Image.network(_getFullMediaUrl(msg.mediaUrl!), width: 200, fit: BoxFit.cover)
                : Container(
                    width: 200,
                    height: 200,
                    color: isDark ? Colors.grey[800] : Colors.grey[300],
                    child: Center(child: Icon(Icons.image, size: 50, color: Colors.grey[500])),
                  ),
          ),
          if (msg.content.isNotEmpty) const SizedBox(height: 8),
          if (msg.content.isNotEmpty) Text(msg.content, style: TextStyle(fontSize: 15, color: textColor)),
        ],
      );
    } else if (msg.messageType == 'audio' && msg.mediaUrl != null) {
      return AudioMessageWidget(
        audioUrl: _getFullMediaUrl(msg.mediaUrl!),
        textColor: textColor,
      );
    } else {
      return Text(msg.content, style: TextStyle(fontSize: 15, color: textColor));
    }
  }

  Widget _buildDateSeparator(BuildContext context, String timestamp) {
    try {
      final date = DateTime.parse(timestamp).toLocal();
      final now = DateTime.now();
      final yesterday = now.subtract(const Duration(days: 1));
      
      String text;
      if (date.year == now.year && date.month == now.month && date.day == now.day) {
        text = 'Aujourd\'hui';
      } else if (date.year == yesterday.year && date.month == yesterday.month && date.day == yesterday.day) {
        text = 'Hier';
      } else {
        text = '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
      }
      
      return Center(
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 16),
          padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 12),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            text,
            style: const TextStyle(fontSize: 12, color: Colors.grey, fontWeight: FontWeight.w500),
          ),
        ),
      );
    } catch (e) {
      return const SizedBox.shrink();
    }
  }

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
    WidgetsBinding.instance.addObserver(this);
    _currentClientName = widget.clientName;
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

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      ref.read(chatDetailNotifierProvider.notifier).fetchMessages(widget.waId);
    }
  }


  void _toggleEmojiPanel() async {
    if (_showEmojiPanel) {
      setState(() => _showEmojiPanel = false);
      _focusNode.requestFocus();
    } else {
      if (_focusNode.hasFocus) {
        _focusNode.unfocus();
        await Future.delayed(const Duration(milliseconds: 100));
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



  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);
    if (pickedFile != null) {
      ref.read(chatDetailNotifierProvider.notifier).uploadMedia(widget.waId, pickedFile.path, 'image');
    }
  }

  Future<void> _startRecording() async {
    if (await Permission.microphone.request().isGranted) {
      final dir = await getTemporaryDirectory();
      _recordFilePath = '${dir.path}/audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
      
      await _beepPlayer.setAsset('assets/audio/bip.wav');
      await _beepPlayer.seek(Duration.zero);
      _beepPlayer.play();
      await Future.delayed(const Duration(milliseconds: 200)); // wait for beep
      
      const config = RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 128000, sampleRate: 44100);
      await _audioRecorder.start(config, path: _recordFilePath!);
      
      setState(() {
        _isRecording = true;
        _isRecordingLocked = false;
        _recordDuration = 0;
        _dragPositionDx = 0;
        _dragPositionDy = 0;
      });
      
      _recordTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
        setState(() {
          _recordDuration++;
        });
      });
    } else {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Permission microphone refusée')));
    }
  }

  Future<void> _stopRecording({bool send = true}) async {
    if (!_isRecording) return;
    
    _recordTimer?.cancel();
    final path = await _audioRecorder.stop();
    
    setState(() {
      _isRecording = false;
      _isRecordingLocked = false;
      _dragPositionDx = 0;
      _dragPositionDy = 0;
    });
    
    if (send && path != null) {
      await _beepPlayer.setAsset('assets/audio/bip.wav');
      await _beepPlayer.seek(Duration.zero);
      _beepPlayer.play();
      ref.read(chatDetailNotifierProvider.notifier).uploadMedia(widget.waId, path, 'audio');
    } else if (!send && path != null) {
      final file = File(path);
      if (await file.exists()) {
        await file.delete();
      }
    }
  }
  
  void _cancelRecording() {
    _stopRecording(send: false);
  }
  
  void _lockRecording() {
    setState(() {
      _isRecordingLocked = true;
    });
  }

  String _formatRecordDuration() {
    final minutes = (_recordDuration / 60).floor().toString().padLeft(2, '0');
    final seconds = (_recordDuration % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  Widget _buildRecordingUI(BuildContext context) {
    if (_isRecordingLocked) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            IconButton(
              icon: const Icon(Icons.delete, color: Colors.red),
              onPressed: _cancelRecording,
            ),
            Row(
              children: [
                const Icon(Icons.mic, color: Colors.red),
                const SizedBox(width: 8),
                Text(_formatRecordDuration(), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ],
            ),
            IconButton(
              icon: Icon(Icons.send, color: Theme.of(context).colorScheme.primary),
              onPressed: () => _stopRecording(send: true),
            ),
          ],
        ),
      );
    }
    
    // Normal recording (holding)
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              const Icon(Icons.mic, color: Colors.red),
              const SizedBox(width: 8),
              Text(_formatRecordDuration(), style: const TextStyle(fontSize: 16)),
            ],
          ),
          Row(
            children: [
              const Icon(Icons.chevron_left, color: Colors.grey),
              const SizedBox(width: 4),
              const Text("Glisser pour annuler", style: TextStyle(color: Colors.grey)),
            ],
          ),
        ],
      ),
    );
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
                  _attachmentIcon(Icons.insert_drive_file, Colors.indigo, 'Document', 'max 100MB', onTap: null),
                  const SizedBox(width: 40),
                  _attachmentIcon(Icons.image, Colors.pink, 'Galerie', 'max 5MB', onTap: _pickImage),
                  const SizedBox(width: 40),
                  _attachmentIcon(Icons.videocam, Colors.purpleAccent, 'Vidéo', 'max 16MB', onTap: null),
                ],
              ),
              const SizedBox(height: 30),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _attachmentIcon(Icons.headset, Colors.orange, 'Audio', 'max 16MB', onTap: null),
                  const SizedBox(width: 40),
                  _attachmentIcon(Icons.location_on, Colors.teal, 'Localisation', 'Carte', onTap: null),
                  const SizedBox(width: 40),
                  _attachmentIcon(Icons.emoji_emotions, Colors.blue, 'Stickers', 'max 500KB', onTap: null),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _attachmentIcon(IconData icon, Color bg, String text, String subtext, {VoidCallback? onTap}) {
    return InkWell(
      onTap: () {
        setState(() => _showAttachmentPanel = false);
        if (onTap != null) {
          onTap();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("$text : fonction à venir.")));
        }
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
      child: EmojiPicker(
        onEmojiSelected: (category, emoji) {
          // Do nothing, text gets updated in onBackspacePressed or via controller
        },
        onBackspacePressed: () {
          // Do nothing, text gets updated via controller
        },
        textEditingController: _messageController, // pass the controller
        config: Config(
          height: 300,
          emojiViewConfig: EmojiViewConfig(
            backgroundColor: Theme.of(context).scaffoldBackgroundColor,
            columns: 7,
            emojiSizeMax: 28 * (Platform.isIOS ? 1.30 : 1.0),
          ),
          bottomActionBarConfig: BottomActionBarConfig(
            backgroundColor: Theme.of(context).scaffoldBackgroundColor,
            buttonIconColor: Colors.grey,
            buttonColor: Theme.of(context).scaffoldBackgroundColor,
          ),
          categoryViewConfig: CategoryViewConfig(
            backgroundColor: Theme.of(context).scaffoldBackgroundColor,
            dividerColor: Theme.of(context).scaffoldBackgroundColor,
            indicatorColor: Theme.of(context).colorScheme.primary,
            iconColorSelected: Theme.of(context).colorScheme.primary,
            iconColor: Colors.grey,
          ),
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
        title: GestureDetector(
          onTap: () {
             final chatListState = ref.read(chatNotifierProvider).value;
             final conv = chatListState?.firstWhere((c) => c.id == widget.waId, orElse: () => Conversation(id: widget.waId, clientName: _currentClientName, lastMessage: '', lastTimestamp: ''));
             ClientProfileSheet.show(context, ref, conv!, onNameUpdated: (newName) {
                setState(() => _currentClientName = newName);
             });
          },
          child: Row(
            children: [
              CircleAvatar(
                radius: 20,
                child: Text(_currentClientName.isNotEmpty ? _currentClientName.substring(0, 1).toUpperCase() : '?', style: const TextStyle(color: Colors.white, fontSize: 16)),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_currentClientName, style: const TextStyle(fontSize: 16)),
                    const Text('Appuyez pour voir le profil', style: TextStyle(fontSize: 10, color: Colors.grey)),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
          Row(
            children: [
              Text('Mode Humain', style: TextStyle(fontSize: 12)),
              Switch(
                value: state.isHumanMode,
                activeColor: Colors.white,
                activeTrackColor: Theme.of(context).colorScheme.primary,
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
                              
                              bool showDateSeparator = false;
                              if (reversedIndex == 0) {
                                showDateSeparator = true;
                              } else {
                                try {
                                  final prevMsg = state.messages[reversedIndex - 1];
                                  final currentDate = DateTime.parse(msg.timestamp).toLocal();
                                  final prevDate = DateTime.parse(prevMsg.timestamp).toLocal();
                                  if (currentDate.year != prevDate.year || currentDate.month != prevDate.month || currentDate.day != prevDate.day) {
                                    showDateSeparator = true;
                                  }
                                } catch (_) {
                                  showDateSeparator = true;
                                }
                              }
                            final isMe = !msg.isFromUser;
                              final isDark = Theme.of(context).brightness == Brightness.dark;
                            
                            final textColor = isMe ? Colors.white : (isDark ? Colors.white : Colors.black87);

                              Widget messageWidget = Align(
                              alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                              child: Container(
                                constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                                margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 12),
                                padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
                                decoration: BoxDecoration(
                                  gradient: isMe 
                                      ? LinearGradient(
                                          colors: [
                                            Theme.of(context).colorScheme.primary, 
                                            Theme.of(context).colorScheme.secondary
                                          ],
                                          begin: Alignment.topLeft,
                                          end: Alignment.bottomRight,
                                        )
                                      : null,
                                  color: isMe ? null : (isDark ? Theme.of(context).colorScheme.surfaceContainerHighest : Colors.white),
                                  borderRadius: BorderRadius.circular(20).copyWith(
                                    bottomRight: isMe ? const Radius.circular(4) : null,
                                    bottomLeft: !isMe ? const Radius.circular(4) : null,
                                  ),
                                  boxShadow: [
                                    if (!isMe)
                                      BoxShadow(
                                        color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.05),
                                        blurRadius: 8,
                                        offset: const Offset(0, 2),
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
                                    _buildMessageContent(msg, textColor, isMe, isDark),
                                    const SizedBox(height: 4),
                                    Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Text(
                                          _formatTime(msg.timestamp), 
                                          style: TextStyle(fontSize: 10, color: isMe ? Colors.white70 : (isDark ? Colors.white54 : Colors.black.withValues(alpha: 0.45))),
                                        ),
                                        if (isMe) ...[
                                          const SizedBox(width: 4),
                                          if (msg.messageStatus == 'processing')
                                            SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2, color: isDark ? Colors.blue[300] : Colors.blue[400]))
                                          else if (msg.messageStatus == 'failed')
                                            Icon(Icons.error, size: 14, color: Colors.red)
                                          else
                                            Icon(Icons.done_all, size: 14, color: isDark ? Colors.blue[300] : Colors.blue[400]),
                                        ]
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            );

                              if (showDateSeparator) {
                                return Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    _buildDateSeparator(context, msg.timestamp),
                                    messageWidget,
                                  ],
                                );
                              }
                              return messageWidget;
                          },
                        ),
                      ),
                    if (!state.isWithin24hWindow && state.isHumanMode)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
                        color: Colors.amber.withOpacity(0.2),
                        child: const Text(
                          "Le client ne vous a pas écrit depuis plus de 24h. L'envoi libre est désactivé par Meta.",
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.amber, fontSize: 12),
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
                              child: _isRecording 
                                ? _buildRecordingUI(context)
                                : Row(
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
                                          enabled: state.isHumanMode && state.isWithin24hWindow,
                                          decoration: InputDecoration(
                                            hintText: state.isHumanMode 
                                                ? (state.isWithin24hWindow ? 'Message' : 'Envoi désactivé (>24h)') 
                                                : 'Passez en Mode Humain',
                                            hintStyle: const TextStyle(color: Colors.grey, fontSize: 16),
                                            border: InputBorder.none,
                                          ),
                                          maxLines: null,
                                          keyboardType: TextInputType.multiline,
                                          onChanged: (_) => _onTextChanged(),
                                        ),
                                      ),
                                      IconButton(
                                        icon: Icon(Icons.attach_file, color: _showAttachmentPanel ? Theme.of(context).colorScheme.primary : Colors.grey),
                                        onPressed: () {
                                          if (state.isHumanMode && state.isWithin24hWindow) {
                                            _toggleAttachmentPanel();
                                          } else if (!state.isHumanMode) {
                                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Passez en mode humain pour envoyer des pièces jointes.")));
                                          }
                                        },
                                      ),
                                      const SizedBox(width: 4),
                                    ],
                                  ),
                            ),
                          ),
                          if (!_isRecordingLocked) ...[
                            const SizedBox(width: 8),
                            GestureDetector(
                              onTap: state.isHumanMode && state.isWithin24hWindow ? (_isTyping ? _sendMessage : null) : null,
                              onLongPressStart: state.isHumanMode && state.isWithin24hWindow && !_isTyping ? (_) => _startRecording() : null,
                              onLongPressMoveUpdate: state.isHumanMode && state.isWithin24hWindow && !_isTyping && !_isRecordingLocked ? (details) {
                                setState(() {
                                  _dragPositionDx = details.localOffsetFromOrigin.dx;
                                  _dragPositionDy = details.localOffsetFromOrigin.dy;
                                });
                                if (_dragPositionDx < -50) {
                                  _cancelRecording();
                                } else if (_dragPositionDy < -50) {
                                  _lockRecording();
                                }
                              } : null,
                              onLongPressEnd: state.isHumanMode && state.isWithin24hWindow && !_isTyping && !_isRecordingLocked ? (_) {
                                if (_isRecording) _stopRecording();
                              } : null,
                              onLongPressCancel: () {
                                if (_isRecording && !_isRecordingLocked) {
                                  _cancelRecording();
                                }
                              },
                              child: Transform.translate(
                                offset: Offset(0, _dragPositionDy < 0 ? _dragPositionDy : 0),
                                child: CircleAvatar(
                                  radius: _isRecording ? 30 : 24, // grow when recording
                                  backgroundColor: _isRecording ? Colors.red : (state.isHumanMode && state.isWithin24hWindow ? Theme.of(context).colorScheme.primary : Colors.grey),
                                  child: Icon(_isTyping ? Icons.send : (_isRecording ? Icons.mic : Icons.mic_none), color: Theme.of(context).cardColor, size: _isRecording ? 28 : 24),
                                ),
                              ),
                            ),
                          ]
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

class AudioMessageWidget extends StatefulWidget {
  final String audioUrl;
  final Color textColor;

  const AudioMessageWidget({Key? key, required this.audioUrl, required this.textColor}) : super(key: key);

  @override
  _AudioMessageWidgetState createState() => _AudioMessageWidgetState();
}

class _AudioMessageWidgetState extends State<AudioMessageWidget> {
  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isPlaying = false;
  Duration _duration = Duration.zero;
  Duration _position = Duration.zero;

  @override
  void initState() {
    super.initState();
    _initAudio();
  }

  Future<void> _initAudio() async {
    try {
      await _audioPlayer.setUrl(widget.audioUrl);
    } catch (e) {
      debugPrint("Error loading audio: $e");
    }
    
    _audioPlayer.playerStateStream.listen((state) {
      if (mounted) {
        setState(() {
          _isPlaying = state.playing;
          if (state.processingState == ProcessingState.completed) {
            _isPlaying = false;
            _audioPlayer.seek(Duration.zero);
            _audioPlayer.pause();
          }
        });
      }
    });
    _audioPlayer.durationStream.listen((newDuration) {
      if (mounted) setState(() => _duration = newDuration ?? Duration.zero);
    });
    _audioPlayer.positionStream.listen((newPosition) {
      if (mounted) setState(() => _position = newPosition);
    });
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }

  void _togglePlayPause() async {
    if (_isPlaying) {
      await _audioPlayer.pause();
    } else {
      await _audioPlayer.play();
    }
  }

  String _formatDuration(Duration d) {
    final minutes = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          icon: Icon(_isPlaying ? Icons.pause_circle_filled : Icons.play_circle_fill, color: widget.textColor, size: 35),
          onPressed: _togglePlayPause,
          padding: EdgeInsets.zero,
          constraints: const BoxConstraints(),
        ),
        const SizedBox(width: 8),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 100,
              height: 4,
              child: LinearProgressIndicator(
                value: _duration.inMilliseconds > 0 ? _position.inMilliseconds / _duration.inMilliseconds : 0.0,
                backgroundColor: widget.textColor.withOpacity(0.3),
                valueColor: AlwaysStoppedAnimation<Color>(widget.textColor),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              _formatDuration(_position.inSeconds > 0 ? _position : _duration),
              style: TextStyle(fontSize: 10, color: widget.textColor),
            ),
          ],
        ),
      ],
    );
  }
}
