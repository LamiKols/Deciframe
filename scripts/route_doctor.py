import argparse
import csv
import pathlib
import re
import subprocess
import sys
import time
import shutil
from difflib import get_close_matches

TEMPLATES_DIR = pathlib.Path("templates")
BACKUP_ROOT = pathlib.Path("backups") / "route_doctor"
URLFOR_RE = re.compile(r"url_for\(\s*['\"]([^'\"]+)['\"]")

def load_endpoints():
    try:
        out = subprocess.check_output(["python", "scripts/print_routes.py"], text=True)
    except Exception as e:
        print(f"ERROR: Could not run scripts/print_routes.py: {e}")
        sys.exit(1)
    eps = []
    for line in out.strip().splitlines():
        if not line.strip(): continue
        endpoint = line.split("|", 1)[0].strip()
        if endpoint:
            eps.append(endpoint)
    return sorted(set(eps))

def scan_templates():
    missing_refs = []  # (path, pos, endpoint)
    for p in TEMPLATES_DIR.rglob("*.html"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"WARN: Cannot read {p}: {e}")
            continue
        for m in URLFOR_RE.finditer(txt):
            ep = m.group(1)
            missing_refs.append((p, m.start(), ep))
    return missing_refs

def suggest(endpoint, universe, n=3):
    # Basic fuzzy suggestions with difflib
    candidates = get_close_matches(endpoint, universe, n=n, cutoff=0.0)
    scored = []
    for c in candidates:
        # crude confidence: normalized similarity via SequenceMatcher ratio * 100
        import difflib
        conf = int(difflib.SequenceMatcher(None, endpoint, c).ratio() * 100)
        scored.append((c, conf))
    scored.sort(key=lambda t: (-t[1], t[0]))
    return scored[:n]

def write_reports(rows, csv_path, md_path):
    # rows: list of dict
    csv_fields = ["template", "position", "missing_endpoint", "suggestions", "best_match", "confidence"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields)
        w.writeheader()
        for r in rows:
            w.writerow({
                "template": r["template"],
                "position": r["position"],
                "missing_endpoint": r["missing"],
                "suggestions": "; ".join([f"{s}:{c}" for s,c in r["suggestions"]]),
                "best_match": r["best"][0] if r["best"] else "",
                "confidence": r["best"][1] if r["best"] else 0
            })
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Missing url_for() Endpoints — Route Doctor Report\n\n")
        f.write("| Template | Pos | Missing | Best Match | Confidence | Other Suggestions |\n")
        f.write("|---|---:|---|---|---:|---|\n")
        for r in rows:
            best = r["best"][0] if r["best"] else ""
            conf = r["best"][1] if r["best"] else 0
            others = ", ".join([f"{s}({c})" for s,c in r["suggestions"] if (s,c)!=(best,conf)])
            f.write(f"| `{r['template']}` | {r['position']} | `{r['missing']}` | `{best}` | {conf} | {others} |\n")
        f.write("\n---\n\n")
        f.write("## Patch Snippets\n")
        for r in rows:
            best = r["best"][0] if r["best"] else ""
            conf = r["best"][1] if r["best"] else 0
            if best:
                f.write(f"**{r['template']}** — replace `{r['missing']}` → `{best}` (confidence {conf})\n\n")
                f.write("```jinja\n{{ url_for('" + best + "') }}\n```\n\n")

def backup_file(src: pathlib.Path, root: pathlib.Path) -> pathlib.Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    dest_dir = root / ts / src.parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    return dest

def apply_fixes(rows, threshold=85):
    changed = []
    for r in rows:
        best = r["best"][0] if r["best"] else ""
        conf = r["best"][1] if r["best"] else 0
        if not best or conf < threshold:
            continue
        path = pathlib.Path(r["template"])
        try:
            txt = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"SKIP {path}: cannot read ({e})")
            continue
        # Replace only the exact endpoint token inside url_for('...')
        pattern = re.compile(r"(url_for\(\s*['\"])"+re.escape(r["missing"])+r"(['\"])")
        new_txt, n = pattern.subn(r"\1"+best+r"\2", txt)
        if n > 0:
            backup_file(path, BACKUP_ROOT)
            path.write_text(new_txt, encoding="utf-8")
            changed.append((str(path), r["missing"], best, conf, n))
    return changed

def main():
    ap = argparse.ArgumentParser(description="Route Doctor: map/fix missing url_for endpoints")
    ap.add_argument("--report", action="store_true", help="Generate mapping report only")
    ap.add_argument("--apply", action="store_true", help="Apply replacements above confidence threshold")
    ap.add_argument("--threshold", type=int, default=85, help="Confidence threshold for --apply (default 85)")
    args = ap.parse_args()

    endpoints = load_endpoints()
    refs = scan_templates()

    # Identify missing by comparing refs to known endpoints
    rows = []
    for p, pos, ep in refs:
        if ep not in endpoints:
            sugg = suggest(ep, endpoints, n=3)
            best = sugg[0] if sugg else ("", 0)
            rows.append({
                "template": str(p),
                "position": pos,
                "missing": ep,
                "suggestions": sugg,
                "best": best
            })

    csv_path = pathlib.Path("MISSING_ROUTES.csv")
    md_path  = pathlib.Path("MISSING_ROUTES.md")

    if rows:
        write_reports(rows, csv_path, md_path)
        print(f"Report written: {csv_path} and {md_path} ({len(rows)} missing endpoints).")
    else:
        print("✅ No missing url_for endpoints found.")
        return

    if args.apply:
        changes = apply_fixes(rows, threshold=args.threshold)
        if changes:
            print("\nApplied replacements (with backups):")
            for path, old, new, conf, n in changes:
                print(f"  {path}: '{old}' → '{new}' (conf {conf}) x{n}")
        else:
            print("\nNo changes applied (no matches ≥ threshold).")

if __name__ == "__main__":
    main()