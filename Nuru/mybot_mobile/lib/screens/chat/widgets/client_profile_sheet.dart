import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../models/conversation.dart';
import '../../../repositories/chat_repository.dart';
import '../../../viewmodels/chat_notifier.dart';

class ClientProfileSheet {
  static void show(
    BuildContext context, 
    WidgetRef ref, 
    Conversation conversation,
    {Function(String)? onNameUpdated}
  ) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return _ClientProfileSheetContent(
          conversation: conversation,
          onNameUpdated: onNameUpdated,
        );
      },
    );
  }
}

class _ClientProfileSheetContent extends ConsumerStatefulWidget {
  final Conversation conversation;
  final Function(String)? onNameUpdated;

  const _ClientProfileSheetContent({required this.conversation, this.onNameUpdated});

  @override
  ConsumerState<_ClientProfileSheetContent> createState() => _ClientProfileSheetContentState();
}

class _ClientProfileSheetContentState extends ConsumerState<_ClientProfileSheetContent> {
  late String _currentClientName;
  late String _realName;

  @override
  void initState() {
    super.initState();
    _currentClientName = widget.conversation.clientName;
    _realName = widget.conversation.clientRealName ?? '';
  }

  void _showEditClientDialog(BuildContext context) {
    final displayNameController = TextEditingController(text: _currentClientName != widget.conversation.id ? _currentClientName : '');
    final realNameController = TextEditingController(text: _realName);

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('Éditer le profil client'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: displayNameController,
                decoration: const InputDecoration(
                  labelText: "Surnom (Display Name)",
                  hintText: "Ex: Boss, KK",
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: realNameController,
                decoration: const InputDecoration(
                  labelText: "Vrai Nom (Légal)",
                  hintText: "Ex: Koffi Mensah",
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Annuler'),
            ),
            ElevatedButton(
              onPressed: () async {
                final displayName = displayNameController.text.trim();
                final realName = realNameController.text.trim();
                
                try {
                  await ref.read(chatRepositoryProvider).updateClientProfile(
                    widget.conversation.id, 
                    realName.isEmpty ? null : realName, 
                    displayName.isEmpty ? null : displayName
                  );
                  if (ctx.mounted) {
                    Navigator.of(ctx).pop(); // Ferme le dialogue
                    
                    final newName = displayName.isNotEmpty ? displayName : (realName.isNotEmpty ? realName : widget.conversation.id);
                    
                    setState(() {
                      _currentClientName = newName;
                      _realName = realName;
                    });
                    
                    if (widget.onNameUpdated != null) {
                      widget.onNameUpdated!(newName);
                    }
                    
                    ref.invalidate(chatNotifierProvider);
                    
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Profil mis à jour avec succès !')),
                    );
                  }
                } catch (e) {
                  if (ctx.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Erreur : $e')),
                    );
                  }
                }
              },
              child: const Text('Enregistrer'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 20,
        right: 20,
        top: 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircleAvatar(
            radius: 40,
            backgroundColor: Theme.of(context).colorScheme.primary.withValues(alpha: 0.2),
            child: Text(
              _currentClientName.isNotEmpty ? _currentClientName.substring(0, 1).toUpperCase() : '?',
              style: TextStyle(fontSize: 32, color: Theme.of(context).colorScheme.primary, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            _currentClientName,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          if (_realName.isNotEmpty && _realName != _currentClientName)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                _realName,
                style: const TextStyle(fontSize: 14, color: Colors.grey),
              ),
            ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.grey.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.phone, size: 14, color: Colors.grey),
                const SizedBox(width: 6),
                Text(
                  widget.conversation.id,
                  style: const TextStyle(fontSize: 14, color: Colors.grey, fontWeight: FontWeight.w500),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              icon: const Icon(Icons.edit),
              label: const Text('Éditer le profil'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
              onPressed: () {
                _showEditClientDialog(context);
              },
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}
