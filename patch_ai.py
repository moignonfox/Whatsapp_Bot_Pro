with open('app/services/ai_service.py', 'a', encoding='utf-8') as f:
    f.write('''

def generate_marketing_copy(instruction: str) -> str:
    """
    Génère un texte promotionnel optimisé pour WhatsApp via l'IA.
    L'instruction est ce que le gérant veut annoncer.
    """
    system_prompt = """
Tu es un expert en copywriting WhatsApp pour des commerces locaux (restaurants, boutiques).
Rédige un message promotionnel très accrocheur, court (max 4-5 phrases), percutant, et qui donne envie d'acheter.
Utilise des emojis pour rendre le texte vivant.
CRITIQUE : Le message DOIT commencer par 'Bonjour {prenom}' ou 'Hello {prenom}' (la balise exacte {prenom} doit être présente).
Ne mets pas d'objet de mail, ni de salutations formelles à la fin, juste le texte WhatsApp prêt à être envoyé.
"""
    try:
        if client:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{system_prompt}\\n\\nVoici ce que je veux annoncer : {instruction}"
            )
            return response.text.strip()
    except Exception as e:
        print(f'Erreur Gemini Marketing Copy: {e}')
        return f'Bonjour {{prenom}}, {instruction}' # Fallback basique
        
    return f'Bonjour {{prenom}}, {instruction}'
''')
print('Appended generate_marketing_copy to ai_service.py')
