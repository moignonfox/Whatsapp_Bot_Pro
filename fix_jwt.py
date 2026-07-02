import os
import re

api_dir = 'app/api'

for filename in os.listdir(api_dir):
    if not filename.endswith('.py'):
        continue
    
    filepath = os.path.join(api_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content

    # Fix auth.py creation
    if filename == 'auth.py':
        content = content.replace(
            'identity = {"company_id": username}\n    access_token = create_access_token(identity=identity)\n    refresh_token = create_refresh_token(identity=identity)',
            'access_token = create_access_token(identity=username)\n    refresh_token = create_refresh_token(identity=username)'
        )

    # Replace reading
    content = content.replace(
        "identity = get_jwt_identity()\n    company_id = identity['company_id']",
        "company_id = get_jwt_identity()"
    )
    
    content = content.replace(
        "identity = get_jwt_identity()\n    company_id = identity.get('company_id')",
        "company_id = get_jwt_identity()"
    )
    
    # Just in case indentation is different
    content = re.sub(
        r'identity = get_jwt_identity\(\)\s*company_id = identity\[\'company_id\'\]',
        r'company_id = get_jwt_identity()',
        content
    )

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filename}")
