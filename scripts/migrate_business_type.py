import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schema import update_schema

if __name__ == '__main__':
    update_schema()
    print("Migration du champ business_type terminee avec succes.")
