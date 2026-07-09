import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../viewmodels/chat_notifier.dart';
import 'widgets/client_profile_sheet.dart';
import 'add_client_bottom_sheet.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  bool _isSearching = false;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = "";

  @override
  void initState() {
    super.initState();
    _searchController.addListener(() {
      setState(() {
        _searchQuery = _searchController.text.toLowerCase();
      });
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  String _formatTime(String? timestamp) {
    if (timestamp == null || timestamp.isEmpty || timestamp == 'now') return '';
    try {
      final DateTime d = DateTime.parse(timestamp).toLocal();
      final now = DateTime.now();
      if (d.year == now.year && d.month == now.month && d.day == now.day) {
        return '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
      }
      return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}';
    } catch (e) {
      return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(chatNotifierProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final iconColor = isDark ? Colors.white : Colors.black87;

    return Scaffold(
      appBar: AppBar(
        title: _isSearching
            ? TextField(
                controller: _searchController,
                autofocus: true,
                decoration: InputDecoration(
                  hintText: 'Rechercher un client ou un mot...',
                  border: InputBorder.none,
                  hintStyle: TextStyle(color: isDark ? Colors.white54 : Colors.black54),
                ),
                style: TextStyle(color: isDark ? Colors.white : Colors.black),
              )
            : const Text(
                'Discussions',
                style: TextStyle(fontWeight: FontWeight.w500, fontSize: 20),
              ),
        actions: [
          IconButton(
            icon: Icon(
              _isSearching ? Icons.close : Icons.search,
              color: iconColor,
            ),
            onPressed: () {
              setState(() {
                _isSearching = !_isSearching;
                if (!_isSearching) {
                  _searchController.clear();
                }
              });
            },
          ),
        ],
      ),
      body: chatState.when(
        data: (conversations) {
          final filtered = conversations.where((c) {
            if (_searchQuery.isEmpty) return true;
            return c.clientName.toLowerCase().contains(_searchQuery) ||
                   c.lastMessage.toLowerCase().contains(_searchQuery);
          }).toList();

          if (filtered.isEmpty) {
            return Center(child: Text('Aucune conversation trouvée.', style: TextStyle(color: Colors.grey, fontSize: 16)));
          }
          return ListView.separated(
              itemCount: filtered.length,
              separatorBuilder: (context, index) => const Padding(
                padding: EdgeInsets.only(left: 76.0, right: 16.0),
                child: Divider(height: 1, thickness: 0.5),
              ),
              itemBuilder: (context, index) {
                final conv = filtered[index];
                
                // Parse message to see if it's from AI
                bool isAi = conv.lastMessage.startsWith('[🤖]');
                String messageText = isAi ? conv.lastMessage.replaceFirst('[🤖]', '').trim() : conv.lastMessage;

                return InkWell(
                  onTap: () {
                    context.push('/chat/detail/${conv.id}?clientName=${Uri.encodeComponent(conv.clientName)}');
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
                    child: Row(
                      children: [
                        GestureDetector(
                          onTap: () {
                            ClientProfileSheet.show(context, ref, conv);
                          },
                          child: CircleAvatar(
                            radius: 24,
                            backgroundColor: Theme.of(context).colorScheme.primary.withOpacity(0.2),
                            child: Text(
                              conv.clientName.isNotEmpty ? conv.clientName.substring(0, 1).toUpperCase() : '?',
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.primary, 
                                fontWeight: FontWeight.bold, 
                                fontSize: 18
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          conv.clientName,
                                          style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600,
                                            color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black87,
                                          ),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                        if (conv.clientRealName != null && conv.clientRealName != conv.clientName && !conv.clientRealName!.startsWith('Client '))
                                          Text(
                                            conv.clientRealName!,
                                            style: TextStyle(
                                              fontSize: 12,
                                              color: Theme.of(context).textTheme.bodyMedium?.color?.withOpacity(0.6) ?? Colors.black54,
                                            ),
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                      ],
                                    ),
                                  ),
                                  Text(
                                    _formatTime(conv.lastTimestamp),
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: conv.unreadCount > 0 ? Theme.of(context).colorScheme.secondary : Colors.grey,
                                      fontWeight: conv.unreadCount > 0 ? FontWeight.bold : FontWeight.normal,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  if (isAi) ...[
                                    Icon(Icons.smart_toy, size: 14, color: Theme.of(context).colorScheme.primary),
                                    const SizedBox(width: 4),
                                  ] else ...[
                                    const Icon(Icons.done_all, size: 16, color: Colors.blue), // Read receipt icon
                                    const SizedBox(width: 4),
                                  ],
                                  Expanded(
                                      child: Text(
                                        messageText,
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: conv.unreadCount > 0 ? (Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87) : Colors.grey,
                                          fontWeight: conv.unreadCount > 0 ? FontWeight.bold : FontWeight.normal,
                                        ),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                    if (conv.unreadCount > 0)
                                      Container(
                                        margin: const EdgeInsets.only(left: 8),
                                        padding: const EdgeInsets.all(6),
                                        decoration: BoxDecoration(
                                          color: Theme.of(context).colorScheme.secondary,
                                          shape: BoxShape.circle,
                                        ),
                                        child: Text(
                                          conv.unreadCount > 99 ? '99+' : conv.unreadCount.toString(),
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 12,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
        },
        loading: () => Center(child: CircularProgressIndicator(color: Theme.of(context).colorScheme.primary)),
        error: (error, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Erreur: $error'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.read(chatNotifierProvider.notifier).fetchConversations(),
                style: ElevatedButton.styleFrom(backgroundColor: Theme.of(context).colorScheme.primary),
                child: const Text('Réessayer', style: TextStyle(color: Colors.white)),
              )
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final result = await showModalBottomSheet<bool>(
            context: context,
            isScrollControlled: true,
            builder: (context) => const AddClientBottomSheet(),
          );
          if (result == true) {
            ref.read(chatNotifierProvider.notifier).fetchConversations();
          }
        },
        backgroundColor: Theme.of(context).colorScheme.secondary,
        child: const Icon(Icons.person_add, color: Colors.white),
      ),
    );
  }
}

