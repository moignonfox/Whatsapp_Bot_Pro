import sys

file_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\Nuru\mybot_mobile\lib\screens\chat\chat_detail_screen.dart'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    line_num = i + 1
    # On supprime de 191 à 356 inclus
    if 191 <= line_num <= 356:
        continue
    
    # Remplacement de l'import
    if "import '../../models/conversation.dart';" in line:
        new_lines.append("import '../../models/conversation.dart';\nimport 'widgets/client_profile_sheet.dart';\n")
        continue

    # Remplacement du AppBar title onTap
    if "onTap: () => _showClientProfileSheet(context, ref)," in line:
        new_lines.append("          onTap: () {\n             final chatListState = ref.read(chatNotifierProvider).value;\n             final conv = chatListState?.firstWhere((c) => c.id == widget.waId, orElse: () => Conversation(id: widget.waId, clientName: _currentClientName, lastMessage: '', lastTimestamp: ''));\n             ClientProfileSheet.show(context, ref, conv!, onNameUpdated: (newName) {\n                setState(() => _currentClientName = newName);\n             });\n          },\n")
        continue

    # Suppression du bouton IconButton(Icons.edit)
    if "IconButton(" in line and "Icons.edit" in lines[i+1]:
        # skip this line, and the next 4 lines
        continue
    if "icon: const Icon(Icons.edit)," in line and "IconButton" in lines[i-1]:
        continue
    if "onPressed: () {" in line and "icon: const Icon(Icons.edit)," in lines[i-1]:
        continue
    if "_showEditClientDialog(context, ref);" in line and "onPressed: () {" in lines[i-1]:
        continue
    if "}," in line and "_showEditClientDialog(context, ref);" in lines[i-1]:
        continue
    if ")," in line and "}," in lines[i-1] and "_showEditClientDialog" in lines[i-2]:
        continue

    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
