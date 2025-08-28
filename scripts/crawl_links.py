import re
import sys
import requests
from urllib.parse import urljoin, urlparse

BASE = sys.argv[1] if len(sys.argv)>1 else "http://127.0.0.1:5000"
SEEN=set(); Q=[BASE]; BAD=[]

def same_origin(u):
    return urlparse(u).netloc == urlparse(BASE).netloc

while Q:
    url = Q.pop()
    if url in SEEN: 
        continue
    SEEN.add(url)
    try:
        r = requests.get(url, timeout=10, allow_redirects=True)
        if r.status_code >= 400:
            BAD.append((url, r.status_code))
            continue
        # Find internal hrefs
        for href in re.findall(r'href="(/[^"#?]*)"', r.text):
            full = urljoin(BASE, href)
            if same_origin(full) and full not in SEEN:
                Q.append(full)
    except Exception as e:
        BAD.append((url, f"EXC:{e!r}"))

if BAD:
    print("❌ Broken internal links detected:")
    for u,s in BAD: 
        print(f"  {s}: {u}")
    sys.exit(1)
else:
    print("✅ Link crawl passed: no broken internal links.")