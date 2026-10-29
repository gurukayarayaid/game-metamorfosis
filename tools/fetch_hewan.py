"""Unduh foto hewan asli (Wikipedia) untuk soal metamorfosis.

Pemakaian:
    python tools/fetch_hewan.py

Hasil: assets/hewan/<id>.jpg (sisi terpanjang 800 px, JPEG kualitas 82).
"""

import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DST = os.path.join(ROOT, "assets", "hewan")
UA = "game-metamorfosis/1.0 (pendidikan; unduh gambar wikipedia)"

HEWAN = [
    # id, nama, jenis, kandidat artikel "lang:Judul" (dicoba berurutan)
    # --- metamorfosis sempurna (telur -> larva -> pupa -> dewasa) ---
    ("kupu", "Kupu-kupu", "sempurna", ["id:Kupu-kupu", "en:Butterfly", "en:Papilionoidea"]),
    ("nyamuk", "Nyamuk", "sempurna", ["id:Nyamuk", "en:Mosquito", "en:Culicidae"]),
    ("lalat", "Lalat", "sempurna", ["id:Lalat", "en:Housefly", "en:Diptera"]),
    ("lebah", "Lebah", "sempurna", ["id:Lebah", "en:Western honey bee", "en:Honey bee"]),
    ("semut", "Semut", "sempurna", ["id:Semut", "en:Ant", "en:Formicidae"]),
    ("kumbang", "Kumbang", "sempurna", ["id:Kumbang", "en:Beetle", "en:Coleoptera"]),
    ("capung", "Capung", "sempurna", ["id:Capung", "en:Dragonfly", "en:Anisoptera"]),
    ("kunang", "Kunang-kunang", "sempurna", ["id:Kunang-kunang", "en:Firefly", "en:Lampyridae"]),
    ("kepik", "Kepik", "sempurna", ["en:Seven-spot ladybird", "en:Coccinellidae"]),
    ("tawon", "Tawon", "sempurna", ["id:Tawon", "en:Wasp", "en:Vespidae"]),
    # --- metamorfosis tidak sempurna (telur -> nimfa -> dewasa) ---
    ("belalang", "Belalang", "tidak", ["id:Belalang", "en:Grasshopper", "en:Acrididae"]),
    ("kecoa", "Kecoa", "tidak", ["id:Kecoa", "en:Cockroach", "en:Blattodea"]),
    ("jangkrik", "Jangkrik", "tidak", ["id:Jangkrik", "en:Cricket", "en:Gryllidae"]),
    ("kutu", "Kutu", "tidak", ["id:Kutu", "en:Human head louse", "en:Louse"]),
    ("rayap", "Rayap", "tidak", ["id:Rayap", "en:Termite", "en:Isoptera"]),
    ("laba", "Laba-laba", "tidak", ["id:Laba-laba", "en:Spider", "en:Araneae"]),
    ("sembah", "Belalang sembah", "tidak", ["id:Belalang sembah", "en:Praying mantis", "en:Mantodea"]),
]

MAX_SIDE = 800
QUALITY = 82


def get_json(url):
    return json.loads(get_bytes(url).decode("utf-8"))


def get_bytes(url):
    last = None
    for attempt in range(5):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            time.sleep(0.5)
            return data
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 503):
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise last


def lead_image(lang, title):
    t = urllib.parse.quote(title.replace(" ", "_"), safe="")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{t}"
    data = get_json(url)
    orig = None
    for key in ("originalimage", "thumbnail"):
        block = data.get(key)
        if isinstance(block, dict):
            src = block.get("source") or block.get("url")
            if src:
                orig = src.split("?")[0]
                break
    thumb = None
    block = data.get("thumbnail")
    if isinstance(block, dict):
        src = (block.get("source") or block.get("url") or "").split("?")[0]
        if src:
            thumb = src.replace(f"/{block.get('width')}px-", f"/{MAX_SIDE}px-")
    if not orig:
        return None, data.get("title", title)
    return (thumb, orig), data.get("title", title)


def fetch_image(urls, path):
    last = None
    for url in [u for u in urls if u]:
        try:
            return normalize(get_bytes(url), path)
        except Exception as e:
            last = e
    raise last if last else RuntimeError("tidak ada url gambar")


def normalize(raw, path):
    img = Image.open(io.BytesIO(raw))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_SIDE:
        s = MAX_SIDE / max(w, h)
        img = img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
    img.save(path, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return img.size


def main():
    os.makedirs(DST, exist_ok=True)
    only = set(sys.argv[1:])
    fail = []
    for hewan in HEWAN:
        hid, nama, jenis, articles = hewan
        if only and hid not in only:
            continue
        out = os.path.join(DST, hid + ".jpg")
        done = False
        for cand in articles:
            if done:
                break
            lang, _, art = cand.partition(":")
            try:
                srcs, resolved = lead_image(lang, art)
                if not srcs:
                    continue
                size = fetch_image(srcs, out)
                kb = os.path.getsize(out) // 1024
                print(f"OK   {hid:10s} {jenis:9s} {cand} -> {resolved} {size[0]}x{size[1]} {kb}KB")
                done = True
                break
            except Exception as e:
                print(f"     coba {cand} gagal ({e})")
        if not done:
            fail.append(hid)
            print(f"FAIL {hid}")
    if fail:
        print("gagal:", ", ".join(fail))
        return 1
    print("semua gambar tersimpan di", DST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
