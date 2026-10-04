# Root launcher for app.py
# Allows running 'python app.py' directly from the repository root
import os
import sys

subfolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Text-to-SQL-Translator")
if subfolder not in sys.path:
    sys.path.insert(0, subfolder)

target_file = os.path.join(subfolder, "app.py")
with open(target_file, "r", encoding="utf-8") as f:
    code = f.read()

exec(compile(code, target_file, 'exec'))
