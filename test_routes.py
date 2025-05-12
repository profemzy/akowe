import sys
import os

# Add the project root to the path to ensure imports work
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from akowe.factory import create_app

app = create_app()

print("==== Registered Routes ====")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule}")