import os

auth_repo_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\Nuru\mybot_mobile\lib\repositories\auth_repository.dart'

with open(auth_repo_path, 'r', encoding='utf-8') as f:
    auth_repo_content = f.read()

# Remplacer la signature et le body de register()
old_register_def = """  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String nom,
    required String ownerName,
    required String ownerPhone,
    required String requestedBotPhone,
    required String businessType,
    required String devise,
  }) async {
    try {
      final response = await _dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'nom': nom,
        'owner_name': ownerName,
        'owner_phone': ownerPhone,
        'requested_bot_phone': requestedBotPhone,
        'business_type': businessType,
        'devise': devise,
      });"""

new_register_def = """  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String nom,
    required String ownerName,
    required String ownerPhone,
    required String requestedBotPhone,
    required String businessType,
    required String devise,
    required String ville,
    required List<String> botTasks,
    required String tone,
    required String businessInfo,
  }) async {
    try {
      final response = await _dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'nom': nom,
        'owner_name': ownerName,
        'owner_phone': ownerPhone,
        'requested_bot_phone': requestedBotPhone,
        'business_type': businessType,
        'devise': devise,
        'ville': ville,
        'bot_tasks': botTasks,
        'tone': tone,
        'business_info': businessInfo,
      });"""

auth_repo_content = auth_repo_content.replace(old_register_def, new_register_def)

with open(auth_repo_path, 'w', encoding='utf-8') as f:
    f.write(auth_repo_content)

print("auth_repository.dart updated.")
