#!/usr/bin/env python3
"""Recupere les images listees dans le manifeste et les optimise.

Deux modes par entree :
  - {"dest": "assets/img/x.jpg", "url": "https://..."}          telechargement direct
  - {"dest": "assets/img/x.jpg", "pages": ["https://..."]}      scrape la page
    (og:image, twitter:image, JSON-LD, <img>/srcset), option "match" pour filtrer
  - {"dest_dir": "assets/img/ftcs", "pages": [...], "max_n": 8} recolte en masse
"""
import io
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from PIL import Image

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "fr,en;q=0.8"}
MAX_W = 1680
QUALITY = 82
SKIP_PAT = re.compile(r"(logo|icon|favicon|sprite|placeholder|avatar|flag|\.svg|\.gif)", re.I)

report = []


def fetch(url, timeout=40, binary=False):
    r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    if r.status_code >= 500:
        alt = dict(HEADERS)
        alt["User-Agent"] = ("Mozilla/5.0 (compatible; Googlebot/2.1; "
                             "+http://www.google.com/bot.html)")
        r = requests.get(url, headers=alt, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return r.content if binary else r.text


def candidates_from_page(url):
    try:
        html = fetch(url)
    except Exception as e:
        report.append({"page": url, "error": str(e)})
        return []
    urls = []
    for pat in (
        r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::secure_url)?["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
    ):
        urls += re.findall(pat, html, re.I)
    for block in re.findall(r'<script[^>]+ld\+json[^>]*>(.*?)</script>', html, re.I | re.S):
        urls += re.findall(r'"image"\s*:\s*"([^"]+)"', block)
        urls += re.findall(r'"contentUrl"\s*:\s*"([^"]+)"', block)
    for srcset in re.findall(r'srcset=["\']([^"\']+)["\']', html, re.I):
        parts = [p.strip().split()[0] for p in srcset.split(',') if p.strip()]
        if parts:
            urls.append(parts[-1])
    urls += re.findall(r'<img[^>]+(?:data-src|src)=["\']([^"\']+)["\']', html, re.I)
    urls += re.findall(r'background(?:-image)?\s*:[^;"\'}]*url\(["\']?([^"\')]+)["\']?\)', html, re.I)
    urls += re.findall(r'https?://[^"\'\s\\)>]+/(?:wp-content|app)/uploads/[^"\'\s\\)>]+\.(?:jpe?g|png|webp)', html, re.I)
    seen, out = set(), []
    for u in urls:
        u = urljoin(url, u.strip())
        if not u.startswith('http') or SKIP_PAT.search(u):
            continue
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def save_optimized(data, dest, min_w=650):
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:
        return False, "illisible"
    w, h = im.size
    if w < min_w or h < 350:
        return False, f"trop petite ({w}x{h})"
    ratio = w / h
    if not 0.45 <= ratio <= 3.2:
        return False, f"format inadapte ({ratio:.2f})"
    if im.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", im.size, (10, 26, 18))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")
    if w > MAX_W:
        im = im.resize((MAX_W, int(h * MAX_W / w)), Image.LANCZOS)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return True, f"{im.size[0]}x{im.size[1]}"


def handle_pdf(entry):
    """Extrait les photos d un PDF (brochure constructeur).

    Avec "dest": garde la plus grande. Avec "dest_dir": exporte les
    max_n plus grandes pour choix manuel.
    """
    import fitz  # pymupdf
    dest = entry.get("dest")
    dest_dir = entry.get("dest_dir")
    if dest and Path(dest).exists() and not entry.get("force"):
        report.append({"dest": dest, "status": "deja present"})
        return
    for url in entry.get("pdfs", []):
        try:
            data = fetch(url, timeout=60, binary=True)
        except Exception as e:
            report.append({"pdf": url, "error": str(e)[:120]})
            continue
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception:
            continue
        candidates = []
        seen_xref = set()
        for page in doc:
            for info in page.get_images(full=True):
                xref = info[0]
                if xref in seen_xref:
                    continue
                seen_xref.add(xref)
                pix = doc.extract_image(xref)
                w, h = pix.get("width", 0), pix.get("height", 0)
                if w < entry.get("min_w", 650) or h < 350:
                    continue
                if not 0.45 <= w / h <= 3.2:
                    continue
                candidates.append((w * h, pix["image"]))
        candidates.sort(key=lambda c: -c[0])
        if not candidates:
            continue
        if dest_dir:
            got = 0
            for i, (_, img) in enumerate(candidates[: entry.get("max_n", 8)]):
                d = str(Path(dest_dir) / f"pdf-{i:02d}.jpg")
                ok, size = save_optimized(img, d, entry.get("min_w", 650))
                if ok:
                    got += 1
                    report.append({"dest": d, "status": "ok", "source": url, "size": size})
            report.append({"dest_dir": dest_dir, "recoltees": got})
            return
        ok, size = save_optimized(candidates[0][1], dest, entry.get("min_w", 650))
        if ok:
            report.append({"dest": dest, "status": "ok", "source": url, "size": size})
            return
    report.append({"dest": dest or dest_dir, "status": "echec pdf"})


def handle_single(entry):
    dest = entry["dest"]
    if Path(dest).exists() and not entry.get("force"):
        report.append({"dest": dest, "status": "deja present"})
        return
    urls = list(entry.get("urls", []))
    if entry.get("url"):
        urls.append(entry["url"])
    for page in entry.get("pages", []):
        urls += candidates_from_page(page)
    exclude = [e.lower() for e in entry.get("exclude", [])]
    if exclude:
        urls = [u for u in urls if not any(e in u.lower() for e in exclude)]
    match = entry.get("match")
    if match:
        preferred = [u for u in urls if match.lower() in u.lower()]
        if entry.get("require_match"):
            urls = preferred
        else:
            urls = preferred + [u for u in urls if u not in preferred]
    for u in urls[:14]:
        try:
            data = fetch(u, binary=True)
        except Exception:
            continue
        ok, info = save_optimized(data, dest, entry.get("min_w", 650))
        if ok:
            report.append({"dest": dest, "status": "ok", "source": u, "size": info})
            return
    report.append({"dest": dest, "status": "echec", "essais": len(urls)})


def handle_bulk(entry):
    dest_dir = Path(entry["dest_dir"])
    max_n = entry.get("max_n", 8)
    got = 0
    urls = []
    for page in entry.get("pages", []):
        urls += candidates_from_page(page)
    for i, u in enumerate(urls):
        if got >= max_n:
            break
        try:
            data = fetch(u, binary=True)
        except Exception:
            continue
        name = re.sub(r'[^a-z0-9]+', '-', u.split('/')[-1].split('?')[0].lower())[:60] or f"img-{i}"
        dest = dest_dir / f"{got:02d}-{name}.jpg"
        ok, info = save_optimized(data, str(dest), entry.get("min_w", 900))
        if ok:
            got += 1
            report.append({"dest": str(dest), "status": "ok", "source": u, "size": info})
    report.append({"dest_dir": str(dest_dir), "recoltees": got})


def main(manifest_path):
    entries = json.loads(Path(manifest_path).read_text())
    for entry in entries:
        try:
            if "pdfs" in entry:
                handle_pdf(entry)
            elif "dest_dir" in entry:
                handle_bulk(entry)
            else:
                handle_single(entry)
        except Exception as e:
            report.append({"entry": str(entry)[:120], "error": str(e)})
    Path(".github/fetch-report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
