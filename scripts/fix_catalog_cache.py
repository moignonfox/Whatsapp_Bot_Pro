import re
import os

repo_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\repositories\catalog_repo.py'

with open(repo_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Retirer @lru_cache
content = content.replace("from functools import lru_cache\n", "")
content = content.replace("from functools import lru_cache", "")
content = content.replace("@lru_cache(maxsize=100)\n", "")

# Retirer les get_by_business.cache_clear()
content = content.replace("get_by_business.cache_clear()\n", "")
content = content.replace("get_by_business.cache_clear()", "")

with open(repo_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed lru_cache from catalog_repo.py")
