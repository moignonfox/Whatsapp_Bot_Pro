import sys

file_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\Nuru\mybot_mobile\lib\screens\chat\chat_detail_screen.dart'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if "String _formatTime(String? timestamp) {" in line:
        new_lines.append("""
  Widget _buildDateSeparator(BuildContext context, String timestamp) {
    try {
      final date = DateTime.parse(timestamp).toLocal();
      final now = DateTime.now();
      final yesterday = now.subtract(const Duration(days: 1));
      
      String text;
      if (date.year == now.year && date.month == now.month && date.day == now.day) {
        text = 'Aujourd\\'hui';
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

""")
        new_lines.append(line)
        continue

    if "final reversedIndex = state.messages.length - 1 - index;" in line:
        new_lines.append(line)
        new_lines.append("""                              final msg = state.messages[reversedIndex];
                              
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
""")
        continue

    if "final msg = state.messages[reversedIndex];" in line:
        continue

    if "return Align(" in line and "alignment: isMe" in lines[i+1]:
        new_lines.append("""                              Widget messageWidget = Align(
""")
        continue

    # Chercher la fin du widget messageWidget : c'est le ); juste avant le prochain return ou la fin de itemBuilder
    # On sait que "final textColor" est au dessus, et "return Align(" est modifié. 
    # Le return Align se termine environ 50 lignes plus bas à la ligne qui a juste ");" et après c'est "}," pour le itemBuilder.
    if ");" in line and "}," in lines[i+1] and ")," in lines[i-1] and "child: Column" not in lines[i-1]:
        new_lines.append(line)
        new_lines.append("""
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
""")
        continue

    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
