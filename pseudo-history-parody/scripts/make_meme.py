"""照片类出图：小红书 P 图、表情包、对比图、红圈标注、聊天截图。文字卡见 make_card.py。

用法：
  # 小红书 P 图：照片裁成 3:4，压大标题（==词== 黄底高亮）+ 一行小字
  python make_meme.py --style xhs --image photos/02.jpg --title "罗马人连==层数==\\n都数不清" --sub "第四层是后来加的，谁加的？" -o p1.png

  # 表情包：图片 + 白底黑字说明条（--pos top 放上面）
  python make_meme.py --style caption --image cat.jpg --text "当我发现钟楼朝东" -o m.png

  # 经典梗图：图片上下各压一行白字黑描边
  python make_meme.py --style meme --image a.jpg --top "教科书说这是罗马式" --bottom "可它有斗拱" -o m.png

  # 对比图：两张图上下（--layout lr 左右）拼在一起，各带红色标签，可加顶部标题
  python make_meme.py --style compare --image a.jpg --image2 b.jpg --label "挪威·博尔贡教堂" --label2 "山西·应县木塔" --title "你品，你细品" -o c.png

  # 红圈标注：在照片上画红圈 / 方框 / 箭头 / 下划线，坐标是相对原图的比例（0~1）
  python make_meme.py --style annotate --image a.jpg --marks marks.json -o a.png
    marks.json 例子：
    [{"type": "circle", "box": [0.42, 0.18, 0.58, 0.33], "label": "这不就是斗拱"},
     {"type": "arrow", "from": [0.15, 0.85], "to": [0.38, 0.62], "label": "朝东"},
     {"type": "box", "box": [0.1, 0.4, 0.3, 0.6]},
     {"type": "underline", "box": [0.2, 0.7, 0.6, 0.72]}]
    label 默认放在标记上方，放不下就放下方；"label_at": [x, y] 指定位置（文字水平居中、顶边在这个点下方一点）；
    "tag": true 换成红底白字，画面太花、没有空白处时用

  # 聊天截图：微信群聊风，--text-file 每行一条
  python make_meme.py --style chat --title "华夏正本清源交流群(328)" --text-file chat.txt -o chat.png
    chat.txt 格式：
      T 23:14                       ← 时间分隔
      L 王老师: 你们看这个屋顶       ← 左边（别人），冒号前是昵称
      L 王老师: [图] photos/01.jpg   ← 发一张图
      R: 这不就是斗拱吗              ← 右边（我）

所有样式左下角都带「伪史论模仿秀·纯属虚构」小字（红线 5），--footnote 只能改措辞。
聊天截图里的人名、群名一律虚构，不用真实人物。
"""
import argparse
import hashlib
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

from make_card import BOLD, REGULAR, H, W, char_w, find_font, fit_font, layout, parse  # noqa: E402

RED = "#E8231F"
YELLOW = "#FFE14D"


def load(path):
    if not path or not os.path.exists(path):
        sys.exit(f"找不到图片：{path}")
    return Image.open(path).convert("RGB")


def fit_width(img, w=W):
    r = w / img.width
    return img.resize((w, max(1, int(img.height * r))), Image.LANCZOS)


def cover(img, w, h, focus=(0.5, 0.5)):
    """等比放大到盖满 w×h，再以 focus（相对坐标）为中心裁切。"""
    r = max(w / img.width, h / img.height)
    img = img.resize((max(w, int(img.width * r + 0.5)), max(h, int(img.height * r + 0.5))), Image.LANCZOS)
    cx, cy = focus[0] * img.width, focus[1] * img.height
    x0 = int(min(max(cx - w / 2, 0), img.width - w))
    y0 = int(min(max(cy - h / 2, 0), img.height - h))
    return img.crop((x0, y0, x0 + w, y0 + h))


def parse_pair(s, default=(0.5, 0.5)):
    if not s:
        return default
    x, y = (float(v) for v in s.split(","))
    return (x, y)


def outlined_lines(d, lines, font, y, line_h, fill, stroke, align="center", x=60, width=W):
    sw = max(3, font.size // 14)
    for ln in lines:
        tw = font.getlength(ln)
        lx = (width - tw) / 2 if align == "center" else x
        d.text((lx, y), ln, font=font, fill=fill, stroke_width=sw, stroke_fill=stroke)
        y += line_h
    return y


def plain_lines(text, font, max_w):
    """折行；最后一行只剩一两个字时把每行收窄一点重排，避免单字落行。"""
    text = text.replace("==", "")
    lines = ["".join(c for c, _ in ln) for ln in layout(text, font, max_w)]
    manual_break = "\n" in text or "\\n" in text
    if len(lines) > 1 and not manual_break and len(lines[-1].strip("，。！？…")) <= 2:
        total = sum(char_w(c, font) for c in text)
        for w in range(int(max_w) - 20, int(total / len(lines)), -20):
            trial = ["".join(c for c, _ in ln) for ln in layout(text, font, w)]
            if len(trial) > len(lines):
                break
            if len(trial[-1].strip("，。！？…")) > 2:
                return trial
    return lines


# ---------- 小红书 P 图 ----------

def xhs(img, title="", sub="", pos="top", color="white", focus=None, **_):
    img = cover(img, W, H, parse_pair(focus))
    # 压字那一侧加一层渐变暗角，保证白字看得清
    grad = Image.new("L", (1, H))
    for y in range(H):
        t = y / H if pos == "bottom" else 1 - y / H
        grad.putpixel((0, y), int(170 * max(0, t - 0.45) / 0.55))
    shade = Image.new("RGB", (W, H), "black")
    img = Image.composite(shade, img, grad.resize((W, H)))
    d = ImageDraw.Draw(img)
    fill = {"white": "#FFFFFF", "yellow": YELLOW}.get(color, "#FFFFFF")
    font = fit_font(BOLD, title, W - 140, 132, 80)
    lines = layout(title, font, W - 140)
    line_h = int(font.size * 1.28)
    sfont = find_font(BOLD, 46)
    slines = plain_lines(sub, sfont, W - 140) if sub else []
    block = line_h * len(lines) + (30 + 62 * len(slines) if slines else 0)
    y = 130 if pos == "top" else H - block - 150
    sw = max(4, font.size // 13)
    for ln in lines:
        x = 70
        for ch, hl in ln:
            w = char_w(ch, font)
            if hl:
                d.rectangle([x - 3, y + font.size * 0.12, x + w + 3, y + font.size * 1.12], fill=YELLOW)
                d.text((x, y), ch, font=font, fill="#111111")
            else:
                d.text((x, y), ch, font=font, fill=fill, stroke_width=sw, stroke_fill="#000000")
            x += w
        y += line_h
    if slines:
        y += 30
        for ln in slines:
            tw = sfont.getlength(ln)
            d.rectangle([62, y - 4, 78 + tw, y + 58], fill=(0, 0, 0))
            d.text((70, y), ln, font=sfont, fill="#FFFFFF")
            y += 62
    return img


# ---------- 表情包 ----------

def caption(img, text="", pos="bottom", **_):
    img = fit_width(img, W)
    if img.height > 1300:
        img = cover(img, W, 1300)
    font = fit_font(BOLD, text, W - 120, 96, 60)
    lines = plain_lines(text, font, W - 120)
    line_h = int(font.size * 1.3)
    panel = line_h * len(lines) + 90
    out = Image.new("RGB", (W, img.height + panel + (60 if pos == "bottom" else 0)), "white")  # 底部给小字留位置
    py = img.height if pos == "bottom" else 0
    out.paste(img, (0, 0 if pos == "bottom" else panel))
    d = ImageDraw.Draw(out)
    y = py + 45
    for ln in lines:
        d.text(((W - font.getlength(ln)) / 2, y), ln, font=font, fill="#111111")
        y += line_h
    return out


def meme(img, top="", bottom="", **_):
    img = fit_width(img, W)
    d = ImageDraw.Draw(img)
    for text, where in ((top, "top"), (bottom, "bottom")):
        if not text:
            continue
        font = fit_font(BOLD, text, W - 100, 100, 56)
        lines = plain_lines(text, font, W - 100)
        line_h = int(font.size * 1.25)
        y = 40 if where == "top" else img.height - line_h * len(lines) - 90
        outlined_lines(d, lines, font, y, line_h, "#FFFFFF", "#000000")
    return img


# ---------- 对比图 ----------

def tag(d, x, y, text, font):
    tw = font.getlength(text)
    d.rectangle([x, y, x + tw + 36, y + font.size + 26], fill=RED)
    d.text((x + 18, y + 10), text, font=font, fill="#FFFFFF")


def compare(img, img2=None, label="", label2="", title="", layout_mode="tb", focus=None, focus2=None, **_):
    if img2 is None:
        sys.exit("compare 需要 --image2")
    out = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(out)
    top = 0
    if title:
        tfont = fit_font(BOLD, title, W - 100, 88, 56)
        tl = plain_lines(title, tfont, W - 100)
        top = int(tfont.size * 1.3) * len(tl) + 60
        y = 30
        for ln in tl:
            d.text(((W - tfont.getlength(ln)) / 2, y), ln, font=tfont, fill="#111111")
            y += int(tfont.size * 1.3)
    gap = 8
    if layout_mode == "lr":
        pw, ph = (W - gap) // 2, H - top
        boxes = [(0, top), (pw + gap, top)]
    else:
        pw, ph = W, (H - top - gap) // 2
        boxes = [(0, top), (0, top + ph + gap)]
    lfont = find_font(BOLD, 44)
    for (x, y), im, lab, fc in zip(boxes, (img, img2), (label, label2), (focus, focus2)):
        out.paste(cover(im, pw, ph, parse_pair(fc)), (x, y))
        if lab:
            tag(d, x + 24, y + 24, lab, lfont)
    return out


# ---------- 红圈标注 ----------

def wobble_ellipse(d, box, width, rng):
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    start = rng.uniform(0, math.tau)
    turns = 1.12  # 手画的圈会多绕一点、首尾不重合
    pts = []
    n = 90
    for i in range(n + 1):
        t = start + turns * math.tau * i / n
        k = 1 + 0.06 * math.sin(3 * t + start) + 0.04 * i / n
        pts.append((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)))
    d.line(pts, fill=RED, width=width, joint="curve")


def arrow(d, p0, p1, width):
    d.line([p0, p1], fill=RED, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    L = width * 4.5
    for s in (0.45, -0.45):
        d.line([p1, (p1[0] - L * math.cos(ang + s), p1[1] - L * math.sin(ang + s))], fill=RED, width=width)


def label_text(d, img, text, anchor, above, font, tag_style=False):
    tw = font.getlength(text)
    x = min(max(20, anchor[0] - tw / 2), img.width - tw - 20)
    y = anchor[1] - font.size - 22 if above else anchor[1] + 18
    y = min(max(10, y), img.height - font.size - 70)
    if tag_style:  # 红底白字，压在复杂画面上也看得清
        d.rectangle([x - 14, y - 8, x + tw + 14, y + font.size + 14], fill=RED)
        d.text((x, y), text, font=font, fill="#FFFFFF")
    else:
        d.text((x, y), text, font=font, fill=RED, stroke_width=5, stroke_fill="#FFFFFF")


def annotate(img, marks=None, **_):
    if not marks:
        sys.exit("annotate 需要 --marks（JSON 文件或 JSON 字符串）")
    img = fit_width(img, W)
    d = ImageDraw.Draw(img)
    iw, ih = img.size
    width = max(7, iw // 140)
    font = find_font(BOLD, 56)
    rng = random.Random(7)
    P = lambda p: (p[0] * iw, p[1] * ih)
    for m in marks:
        t = m.get("type", "circle")
        if t in ("circle", "box", "underline"):
            x0, y0 = P(m["box"][:2])
            x1, y1 = P(m["box"][2:])
            if t == "circle":
                wobble_ellipse(d, (x0, y0, x1, y1), width, rng)
            elif t == "box":
                d.rectangle([x0, y0, x1, y1], outline=RED, width=width)
            else:
                d.line([(x0, y1), (x1, y1 + rng.uniform(-4, 4))], fill=RED, width=width)
            top_anchor, bottom_anchor = ((x0 + x1) / 2, y0 - 6), ((x0 + x1) / 2, y1 + 6)
        elif t == "arrow":
            p0, p1 = P(m["from"]), P(m["to"])
            arrow(d, p0, p1, width)
            top_anchor = bottom_anchor = p0
        else:
            sys.exit(f"不认识的标记类型：{t}（可选 circle / box / arrow / underline）")
        if m.get("label"):
            tg = m.get("tag", False)
            if m.get("label_at"):
                label_text(d, img, m["label"], P(m["label_at"]), False, font, tg)
            elif t == "arrow":
                label_text(d, img, m["label"], p0, p0[1] < p1[1], font, tg)
            else:
                above = top_anchor[1] > font.size + 40
                label_text(d, img, m["label"], top_anchor if above else bottom_anchor, above, font, tg)
    return img


# ---------- 聊天截图 ----------

AVATAR_COLORS = ["#7BA05B", "#C9874A", "#5B8DB8", "#B85B7A", "#8A6FB8", "#B8A25B", "#5BAFA0"]


def avatar(name, size):
    h = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16)
    im = Image.new("RGB", (size, size), AVATAR_COLORS[h % len(AVATAR_COLORS)])
    d = ImageDraw.Draw(im)
    f = find_font(BOLD, int(size * 0.5))
    ch = name.strip()[:1] or "?"
    d.text(((size - f.getlength(ch)) / 2, size * 0.2), ch, font=f, fill="#FFFFFF")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], size // 8, fill=255)
    return im, mask


def parse_chat(text, base_dir):
    msgs = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        kind, rest = line[:1].upper(), line[1:]
        if kind not in ("L", "R", "T") or rest[:1] not in (" ", ":", "："):
            sys.exit(f"聊天每行要以 L / R / T 开头：{raw}")
        if kind == "T":
            msgs.append(("time", "", rest.strip()))
            continue
        if kind == "R" and rest[:1] in (":", "："):  # "R: 内容" 省略昵称
            rest = "我" + rest
        name, sep, content = rest.partition(":")
        if not sep:
            name, sep, content = rest.partition("：")
        if not sep:
            name, content = "", rest
        name, content = name.strip(), content.strip()
        if kind == "R":
            name = name or "我"
        if content.startswith("[图]"):
            p = content[3:].strip()
            if not os.path.isabs(p):
                p = os.path.join(base_dir, p)
            msgs.append((kind, name, ("img", p)))
        else:
            msgs.append((kind, name, content))
    return msgs


def chat(img=None, title="", text="", base_dir=".", **_):
    msgs = parse_chat(text, base_dir)
    bfont, nfont, tfont, hfont = find_font(REGULAR, 44), find_font(REGULAR, 30), find_font(REGULAR, 30), find_font(BOLD, 44)
    av, pad, maxw = 96, 28, 640
    rows = []  # 先排版算总高度
    for kind, name, content in msgs:
        if kind == "time":
            rows.append(("time", content, 80))
            continue
        if isinstance(content, tuple):
            im = Image.open(content[1]).convert("RGB")
            im.thumbnail((420, 520))
            rows.append((kind, name, ("img", im), im.height + (44 if kind == "L" else 0) + 36))
        else:
            lines = plain_lines(content, bfont, maxw)
            bw = max(bfont.getlength(ln) for ln in lines) if lines else 0
            bh = len(lines) * 64 + pad * 2 - 10
            rows.append((kind, name, ("text", lines, bw, bh), bh + (44 if kind == "L" else 0) + 36))
    head = 150
    height = max(H, head + sum(r[-1] for r in rows) + 160)
    out = Image.new("RGB", (W, height), "#EDEDED")
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, W, head], fill="#EDEDED")
    d.text((40, 62), "‹", font=find_font(REGULAR, 70), fill="#111111")
    if title:
        tw = hfont.getlength(title)
        d.text(((W - tw) / 2, 70), title, font=hfont, fill="#111111")
    d.text((W - 90, 60), "···", font=hfont, fill="#111111")
    d.line([0, head, W, head], fill="#DADADA", width=2)
    y = head + 40
    for r in rows:
        if r[0] == "time":
            tw = tfont.getlength(r[1])
            d.text(((W - tw) / 2, y + 14), r[1], font=tfont, fill="#A0A0A0")
            y += r[2]
            continue
        kind, name, body, rh = r
        face, mask = avatar(name or "?", av)
        ax = 30 if kind == "L" else W - 30 - av
        out.paste(face, (ax, y), mask)
        by = y
        if kind == "L":
            d.text((ax + av + 24, y - 4), name, font=nfont, fill="#8C8C8C")
            by = y + 44
        if body[0] == "img":
            im = body[1]
            bx = ax + av + 24 if kind == "L" else ax - 24 - im.width
            out.paste(im, (int(bx), by))
        else:
            _, lines, bw, bh = body
            bwid = bw + pad * 2
            bx = ax + av + 24 if kind == "L" else ax - 24 - bwid
            color = "#FFFFFF" if kind == "L" else "#95EC69"
            d.rounded_rectangle([bx, by, bx + bwid, by + bh], 14, fill=color)
            tip = [(bx, by + 30), (bx - 14, by + 40), (bx, by + 50)] if kind == "L" else \
                [(bx + bwid, by + 30), (bx + bwid + 14, by + 40), (bx + bwid, by + 50)]
            d.polygon(tip, fill=color)
            ty = by + pad - 6
            for ln in lines:
                d.text((bx + pad, ty), ln, font=bfont, fill="#111111")
                ty += 64
        y += rh
    return out


STYLES = {"xhs": xhs, "caption": caption, "meme": meme, "compare": compare, "annotate": annotate, "chat": chat}


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows 控制台默认 GBK，报错信息会乱码
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=STYLES, required=True)
    ap.add_argument("--image")
    ap.add_argument("--image2", help="compare 的第二张图")
    ap.add_argument("--text", default="", help="caption 的说明文字")
    ap.add_argument("--text-file", help="chat 的聊天内容文件")
    ap.add_argument("--title", default="", help="xhs 大标题 / compare 顶部标题 / chat 群名")
    ap.add_argument("--sub", default="", help="xhs 标题下的一行小字")
    ap.add_argument("--top", default="")
    ap.add_argument("--bottom", default="")
    ap.add_argument("--label", default="")
    ap.add_argument("--label2", default="")
    ap.add_argument("--layout", choices=["tb", "lr"], default="tb", help="compare 上下 / 左右")
    ap.add_argument("--marks", help="annotate 的标记：JSON 文件路径或 JSON 字符串")
    ap.add_argument("--pos", choices=["top", "bottom"], default=None)
    ap.add_argument("--color", default="white", help="xhs 标题颜色 white|yellow")
    ap.add_argument("--focus", help="裁切中心，相对坐标 x,y，如 0.5,0.3")
    ap.add_argument("--focus2")
    ap.add_argument("--footnote", default="伪史论模仿秀·纯属虚构", help="左下角小字，可改措辞，不能去掉")
    ap.add_argument("-o", "--out", default="meme.png")
    a = ap.parse_args()

    text = a.text
    base_dir = "."
    if a.text_file:
        with open(a.text_file, encoding="utf-8") as f:
            text = f.read()
        base_dir = os.path.dirname(os.path.abspath(a.text_file))
    marks = None
    if a.marks:
        marks = json.load(open(a.marks, encoding="utf-8")) if os.path.exists(a.marks) else json.loads(a.marks)
    img = load(a.image) if a.style != "chat" else None
    img2 = load(a.image2) if a.image2 else None
    pos = a.pos or ("top" if a.style == "xhs" else "bottom")
    out = STYLES[a.style](img=img, img2=img2, title=a.title, sub=a.sub, text=text, top=a.top, bottom=a.bottom,
                          label=a.label, label2=a.label2, layout_mode=a.layout, marks=marks, pos=pos,
                          color=a.color, focus=a.focus, focus2=a.focus2, base_dir=base_dir)
    footnote = a.footnote.strip() or "伪史论模仿秀·纯属虚构"
    d = ImageDraw.Draw(out)
    f = find_font(REGULAR, 26)
    if a.style == "chat" or (a.style == "caption" and pos == "bottom"):
        d.text((48, out.height - 70), footnote, font=f, fill="#9A9A9A")
    else:
        d.text((40, out.height - 56), footnote, font=f, fill="#F2F2F2", stroke_width=2, stroke_fill="#333333")
    out.save(a.out)
    print(a.out, out.size)
    if a.style == "chat" and out.height > 2400:
        print("提醒：聊天截图太长，小红书会裁掉一大截。控制在 6～8 条消息，或拆成两张")


if __name__ == "__main__":
    main()
