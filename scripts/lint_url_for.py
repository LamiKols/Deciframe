import re
import sys
import subprocess
import pathlib

# Get endpoints from Flask
try:
    routes = subprocess.check_output(["python", "scripts/print_routes.py"]).decode()
except subprocess.CalledProcessError as e:
    print("ERROR: Could not list Flask routes. Ensure the app imports correctly.\n", e)
    sys.exit(1)

endpoints = {line.split("|",1)[0] for line in routes.strip().splitlines() if line.strip()}
missing = []
pattern = re.compile(r"url_for\(\s*['\"]([^'\"]+)['\"]")

for p in pathlib.Path("templates").rglob("*.html"):
    txt = p.read_text(encoding="utf-8", errors="ignore")
    for m in pattern.finditer(txt):
        ep = m.group(1)
        if ep not in endpoints:
            missing.append(f"{p}:{m.start()} → missing endpoint '{ep}'")

if missing:
    print("❌ url_for endpoint(s) referenced in templates but not defined in Flask routes:")
    print("\n".join(missing))
    sys.exit(1)
else:
    print("✅ All url_for() endpoints referenced in templates exist.")