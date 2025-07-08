import os

# Define expected templates
expected_templates = [
    "login.html",
    "register.html",
    "base.html",
    "auth/login.html",
    "auth/register.html",
    "layout.html",  # add more as needed
]

# Directory to scan
TEMPLATE_DIR = os.path.join(os.getcwd(), "templates")

# Function to recursively find templates
def find_templates(template_dir):
    found_templates = []
    for root, _, files in os.walk(template_dir):
        for file in files:
            if file.endswith(".html"):
                rel_path = os.path.relpath(os.path.join(root, file), template_dir)
                found_templates.append(rel_path)
    return found_templates

# Run scan
if not os.path.exists(TEMPLATE_DIR):
    print("❌ No 'templates/' directory found.")
else:
    found = find_templates(TEMPLATE_DIR)
    missing = [tpl for tpl in expected_templates if tpl not in found]
    
    print("📂 Found templates:")
    for tpl in sorted(found):
        print("   ✅", tpl)

    print("\n❌ Missing templates:")
    if not missing:
        print("   🎉 All expected templates are present.")
    else:
        for tpl in missing:
            print("   ❌", tpl)

    # Optional: Export list to text file
    with open("missing_templates_report.txt", "w") as f:
        f.write("Missing Templates Report\n")
        f.write("=========================\n")
        for tpl in missing:
            f.write(f"- {tpl}\n")

        f.write("\nFound Templates:\n")
        for tpl in sorted(found):
            f.write(f"+ {tpl}\n")

    print("\n📄 Output written to missing_templates_report.txt")