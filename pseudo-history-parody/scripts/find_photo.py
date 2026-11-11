"""从网上找真实照片当底图：维基共享资源（Wikimedia Commons）+ Openverse，都不用 API key，图片都是开放授权。

用法：
  python find_photo.py "Colosseum Rome" -o photos/            # 搜索并下载前 8 张候选，生成 contact.jpg 缩略图总览
  python find_photo.py "Borgund stave church" -n 12 -o photos/
  python find_photo.py --url https://upload.wikimedia.org/.../x.jpg -o photos/   # 直接下载一张已知图片

搜索词用英文或当地语言效果最好（维基共享资源以英文描述为主）。
输出：
  photos/01.jpg, 02.jpg ...    候选图（长边约 1280～1600px）
  photos/contact.jpg           带编号的缩略图总览，看这一张就能挑
  photos/sources.json          每张图的标题、作者、授权、原页面
用了哪张，发帖时在正文末尾或评论区注明「图：作者 / 授权 / 维基共享资源」。
"""
import argparse
import io
import json
import os
import re
import sys
import time

import requests
from PIL import Image, ImageDraw

UA = {"User-Agent": "pseudo-history-parody-skill/1.0 (image search script; python-requests)"}
COMMONS = "https://commons.wikimedia.org/w/api.php"
OPENVERSE = "https://api.openverse.org/v1/images/"


def strip_html(s):
    s = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()
    half = len(s) // 2  # 维基有时把作者名重复两遍："Unknown authorUnknown author"
    if len(s) % 2 == 0 and s[:half] == s[half:]:
        s = s[:half]
    return s


def search_commons(q, n):
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"filetype:bitmap {q}", "gsrnamespace": 6, "gsrlimit": min(50, n * 2),
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1280,  # 维基只缓存标准宽度（960/1280/1920…），非标准宽度容易被限流
    }
    r = requests.get(COMMONS, params=params, headers=UA, timeout=30)
    r.raise_for_status()
    pages = sorted((r.json().get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        if ii.get("mime") not in ("image/jpeg", "image/png", "image/webp"):
            continue
        if min(ii.get("width", 0), ii.get("height", 0)) < 600:
            continue
        meta = ii.get("extmetadata", {})
        out.append({
            "source": "Wikimedia Commons",
            "title": p.get("title", "").replace("File:", ""),
            "url": ii.get("thumburl") or ii.get("url"),
            "page": ii.get("descriptionurl"),
            "author": strip_html(meta.get("Artist", {}).get("value")),
            "license": meta.get("LicenseShortName", {}).get("value", ""),
        })
    return out


def search_openverse(q, n):
    r = requests.get(OPENVERSE, params={"q": q, "page_size": min(20, n * 2)}, headers=UA, timeout=30)
    r.raise_for_status()
    out = []
    for it in r.json().get("results", []):
        if min(it.get("width") or 0, it.get("height") or 0) and min(it["width"], it["height"]) < 600:
            continue
        out.append({
            "source": f"Openverse/{it.get('provider', '')}",
            "title": it.get("title", ""),
            "url": it.get("url"),
            "page": it.get("foreign_landing_url"),
            "author": it.get("creator", ""),
            "license": f"{it.get('license', '').upper()} {it.get('license_version', '')}".strip(),
        })
    return out


def download(url, tries=4):
    for i in range(tries):
        r = requests.get(url, headers=UA, timeout=60)
        if r.status_code != 429 or i == tries - 1:
            break
        wait = int(r.headers.get("Retry-After", "0") or 0) or 2 * (i + 1)
        time.sleep(min(wait, 15))  # 维基限流：等一会儿再试
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content))
    img.load()
    img = img.convert("RGB")
    if max(img.size) > 1600:
        img.thumbnail((1600, 1600), Image.LANCZOS)
    return img


def contact_sheet(paths, out):
    from make_card import find_font, BOLD  # 同目录
    cols, cell = 4, 300
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), "white")
    d = ImageDraw.Draw(sheet)
    font = find_font(BOLD, 40)
    for i, p in enumerate(paths):
        im = Image.open(p)
        im.thumbnail((cell - 8, cell - 8))
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
        label = os.path.splitext(os.path.basename(p))[0]
        d.rectangle([x + 4, y + 4, x + 70, y + 54], fill="#E8231F")
        d.text((x + 12, y + 6), label, font=font, fill="white")
    sheet.save(out, quality=85)


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows 控制台默认 GBK，报错信息会乱码
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", help="搜索词，英文效果最好")
    ap.add_argument("--url", help="直接下载这张图（比如 WebSearch 找到的图片地址）")
    ap.add_argument("-n", type=int, default=8, help="候选张数")
    ap.add_argument("--source", choices=["all", "commons", "openverse"], default="all")
    ap.add_argument("-o", "--out", default="photos")
    a = ap.parse_args()
    if not a.query and not a.url:
        ap.error("要么给搜索词，要么给 --url")
    os.makedirs(a.out, exist_ok=True)

    if a.url:
        items = [{"source": "url", "title": os.path.basename(a.url.split("?")[0]), "url": a.url, "page": a.url, "author": "", "license": "未知：发帖前自己确认能不能用"}]
    else:
        items = []
        if a.source in ("all", "commons"):
            try:
                items += search_commons(a.query, a.n)
            except Exception as e:
                print("维基共享资源搜索失败：", e)
        if a.source in ("all", "openverse") and len(items) < a.n:
            try:
                items += search_openverse(a.query, a.n)
            except Exception as e:
                print("Openverse 搜索失败：", e)
    if not items:
        sys.exit("没搜到图。换个说法（英文、当地语言、加上地名）再试，或者用 WebSearch 找到图片地址后用 --url 下载")

    saved, seen = [], set()
    for it in items:
        if len(saved) >= a.n:
            break
        if not it["url"] or it["url"] in seen:
            continue
        seen.add(it["url"])
        try:
            img = download(it["url"])
        except Exception as e:
            print("跳过（下载失败）：", it["title"], e)
            continue
        name = f"{len(saved) + 1:02d}.jpg"
        path = os.path.join(a.out, name)
        img.save(path, quality=92)
        it.update(file=name, size=list(img.size))
        saved.append(it)
        print(f"{name}  {img.size[0]}x{img.size[1]}  {it['title'][:70]}  [{it['license']}]")
        time.sleep(1.0)
    if not saved:
        sys.exit("图都下载失败了")
    with open(os.path.join(a.out, "sources.json"), "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)
    if len(saved) > 1:
        contact_sheet([os.path.join(a.out, s["file"]) for s in saved], os.path.join(a.out, "contact.jpg"))
        print("缩略图总览：", os.path.join(a.out, "contact.jpg"))
    print("先核对标题：照片拍的是不是你要的那个地方（搜「故宫」可能出来沈阳故宫）")


if __name__ == "__main__":
    main()
