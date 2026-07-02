import re
import os

files = ['app/templates/dashboard/admin.html', 'app/templates/dashboard/orders.html']

for file in files:
    if not os.path.exists(file):
        continue
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace incorrectly escaped \' with '
    content = content.replace(r"\'confirm\'", "'confirm'")
    content = content.replace(r"\'cancel\'", "'cancel'")
    
    # Replace res['id'] with {{ res['id'] }}
    content = content.replace(r"processOrderAction(this, res['id'], 'confirm')", r"processOrderAction(this, {{ res['id'] }}, 'confirm')")
    content = content.replace(r"processOrderAction(this, res['id'], 'cancel')", r"processOrderAction(this, {{ res['id'] }}, 'cancel')")

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print('Done!')
