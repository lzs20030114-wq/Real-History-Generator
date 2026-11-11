"""小红书 3:4 文字封面卡生成器（1080x1440）。

用法：
  python make_card.py --style notes --text "开个帖收集==伪史==文案，永久保存" --emoji "⛈️" -o cover.png
  python make_card.py --style quote --color green --text "我已经一分钟没有听到伪史论的笑话了，快给我讲讲，《==兽人==》之类的" -o c.png
  python make_card.py --style brush --text "伪史论\\n给我笑醒了" -o c.png
  python make_card.py --style list --title "天啊，顿悟红楼梦" --text-file items.txt -o c.png

文字里用 ==词== 标高亮，用 \\n 强制换行。英文单词和数字不会被拆开，逗号句号不会落在行首。
左下角默认加灰色小字「伪史论模仿秀·纯属虚构」（--footnote 只用来改措辞，红线 5 要求始终保留）。
style:
  notes  苹果备忘录风：黄色顶栏 + 格子纸 + 黄色高亮
  quote  大引号卡片：浅色底 + 大引号 + 荧光笔高亮（--color green|pink|blue|yellow）
  brush  米白底红色书法字，适合一句话钩子
  list   长截图风：标题 + 编号正文，适合索隐清单、伪史论笑话合集
  photo  一图一句：在 --image 照片上压一行字（--pos top|center|bottom，--color white|yellow|red）
  essay  信徒理性长文封面：米白底 + 粗黑标题压米色块 + 一段正文（--title 放标题，--text 放正文）
"""
import argparse
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1440
FONT_DIRS = [r"C:\Windows\Fonts", "/System/Library/Fonts", "/usr/share/fonts", os.path.expanduser("~/.fonts")]
BOLD = ["msyhbd.ttc", "NotoSansSC-VF.ttf", "simhei.ttf", "PingFang.ttc", "NotoSansCJK-Bold.ttc"]
REGULAR = ["msyh.ttc", "NotoSansSC-Medium.otf", "simhei.ttf", "PingFang.ttc", "NotoSansCJK-Regular.ttc"]
BRUSH = ["STXINGKA.TTF", "FZSTK.TTF", "STKAITI.TTF", "simkai.ttf"]
EMOJI = ["seguiemj.ttf", "Apple Color Emoji.ttc", "NotoColorEmoji.ttf"]

PALETTES = {
    "green": ("#DDF8D3", "#B9EBAA", "#FFD36B"),
    "pink": ("#FDE3EC", "#F7C2D3", "#A6F0A6"),
    "blue": ("#DDEBFB", "#B8D3F3", "#FFE07A"),
    "yellow": ("#FFF6D6", "#F3E1A0", "#FFB37A"),
}


def find_font(names, size):
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    sys.exit(f"找不到字体：{names}，请把中文字体放进 {FONT_DIRS[0]}")


def parse(text):
    """'a==b==c' -> [('a',False),('b',True),('c',False)]"""
    out, hl = [], False
    for part in re.split(r"==", text):
        if part:
            out.append((part, hl))
        hl = not hl
    return out


# 不能出现在行首的标点（中文排版"避头"规则）
NO_LINE_START = set("，。！？、；：,.!?;:）)】』」》〉”’…—%")
WORD_CHAR = re.compile(r"[A-Za-z0-9.%·+\-]")


def tokens(para):
    """把一段拆成排版单位：连续的英文/数字算一个单位，其他一个字一个单位。"""
    out = []
    for seg, hl in parse(para):
        buf = ""
        for ch in seg:
            if WORD_CHAR.match(ch):
                buf += ch
                continue
            if buf:
                out.append([(c, hl) for c in buf])
                buf = ""
            out.append([(ch, hl)])
        if buf:
            out.append([(c, hl) for c in buf])
    return out


def layout(text, font, max_w):
    """折行，返回行列表，每行是 [(char, highlighted), ...]。
    英文单词和数字不拆开；逗号句号等不放在行首（允许它们略微超出右边距）。"""
    lines = []
    for para in text.replace("\\n", "\n").split("\n"):
        cur, cur_w = [], 0
        for tok in tokens(para):
            w = sum(char_w(c, font) for c, _ in tok)
            punct = len(tok) == 1 and tok[0][0] in NO_LINE_START
            if cur and cur_w + w > max_w and not punct:
                lines.append(cur)
                cur, cur_w = [], 0
            cur.extend(tok)
            cur_w += w
        lines.append(cur)
    return lines


def is_emoji(ch):
    o = ord(ch)
    return o >= 0x1F000 or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF


def emoji_image(ch, size):
    for d in FONT_DIRS:
        for n in EMOJI:
            p = os.path.join(d, n)
            if os.path.exists(p):
                f = ImageFont.truetype(p, 109)  # 彩色 emoji 字体只支持固定字号，先画再缩放
                # 画布留足边距：有的 emoji 字形会超出字框，画在 (0,0) 会被切掉上边和左边
                tmp = Image.new("RGBA", (360, 300), (0, 0, 0, 0))
                ImageDraw.Draw(tmp).text((80, 70), ch, font=f, embedded_color=True)
                bbox = tmp.getbbox()
                if not bbox:
                    return None
                tmp = tmp.crop(bbox)
                r = size / max(tmp.size)
                return tmp.resize((max(1, int(tmp.width * r)), max(1, int(tmp.height * r))), Image.LANCZOS)
    return None


def char_w(ch, font):
    if ch == "️":
        return 0
    return font.size * 1.05 if is_emoji(ch) else font.getlength(ch)


def draw_lines(d, lines, font, x, y, line_h, color, hl_color, hl_style="bar"):
    img = d._image
    for line in lines:
        cx = x
        for ch, hl in line:
            w = char_w(ch, font)
            if not w:
                continue
            if hl and hl_color:
                if hl_style == "bar":  # 荧光笔：下半截
                    d.rectangle([cx - 2, y + line_h * 0.45, cx + w + 2, y + line_h * 0.92], fill=hl_color)
                else:  # 整块底色
                    d.rectangle([cx - 2, y + line_h * 0.05, cx + w + 2, y + line_h * 0.95], fill=hl_color)
            if is_emoji(ch):
                em = emoji_image(ch, int(font.size * 0.95))
                if em:
                    img.paste(em, (int(cx), int(y + (font.size - em.height) / 2 + font.size * 0.12)), em)
            else:
                d.text((cx, y), ch, font=font, fill=color)
            cx += w
        y += line_h
    return y


def fit_font(names, text, max_w, start, minimum):
    """尽量让每个手动换行的段落各占一行；放不下就缩字号，缩到 minimum 为止再自动折行。"""
    paras = text.replace("\\n", "\n").split("\n")
    size = start
    while size > minimum:
        f = find_font(names, size)
        if all(sum(char_w(c, f) for c in p.replace("==", "")) <= max_w for p in paras):
            return f
        size -= 6
    return find_font(names, minimum)


def paste_emoji(img, emoji, center, size=200):
    chars = [c for c in emoji if c != "️"]
    if not chars:
        return
    ims = [e for e in (emoji_image(c, size) for c in chars) if e]
    total = sum(e.width for e in ims) + 20 * (len(ims) - 1)
    x = center[0] - total // 2
    for e in ims:
        img.paste(e, (x, center[1] - e.height // 2), e)
        x += e.width + 20


def quote_mark(d, x, y, color, s=1.0):
    """两个圆头带尾巴的大引号，模仿小红书引号卡"""
    for dx in (0, int(110 * s)):
        cx, cy, r = x + dx + int(45 * s), y + int(75 * s), int(45 * s)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        d.polygon([(cx - r, cy), (cx + int(5 * s), y), (cx + int(25 * s), y + int(12 * s)), (cx - int(5 * s), cy)], fill=color)


def notes(text, emoji, **_):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    yel = "#E8B500"
    ui = find_font(REGULAR, 40)
    d.text((48, 56), "‹", font=find_font(REGULAR, 72), fill=yel)
    d.text((98, 62), "Notes", font=ui, fill=yel)
    d.rounded_rectangle([825, 52, 870, 104], 6, outline=yel, width=4)
    d.ellipse([972, 52, 1028, 108], outline=yel, width=4)
    for i, cx in enumerate((988, 1000, 1012)):
        d.ellipse([cx - 3, 77, cx + 3, 83], fill=yel)
    # 格子纸
    for x in range(50, 1040, 65):
        d.line([x, 170, x, 1390], fill="#ECECEC", width=2)
    for y in range(170, 1400, 65):
        d.line([50, y, 1035, y], fill="#ECECEC", width=2)
    font = find_font(BOLD, 112)
    lines = layout(text, font, 860)
    line_h = 175
    y0 = max(330, (H - line_h * len(lines)) // 2 - 120)
    draw_lines(d, lines, font, 95, y0, line_h, "#3A3A3A", "#FFEFB0", "block")
    paste_emoji(img, emoji, (W // 2, 1160), 210)
    return img


def quote(text, emoji, color="green", **_):
    bg, mark, hl = PALETTES.get(color, PALETTES["green"])
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    quote_mark(d, 130, 130, mark)
    font = fit_font(BOLD, text, 820, 92, 70)
    lines = layout(text, font, 820)
    line_h = int(font.size * 1.43)
    y0 = max(380, (H - line_h * len(lines)) // 2 - 40)
    y = draw_lines(d, lines, font, 130, y0, line_h, "#333333", hl, "bar")
    if emoji:
        paste_emoji(img, emoji, (900, min(y + 90, 1250)), 120)
    d.rectangle([880, 1290, 950, 1306], fill=mark)
    return img


def brush(text, emoji, **_):
    img = Image.new("RGB", (W, H), "#FCF6F2")
    d = ImageDraw.Draw(img)
    # 浅色底纹：几条淡等高线
    for i in range(14):
        y = 80 + i * 100
        d.arc([-200 + (i % 3) * 120, y - 60, 400 + (i % 3) * 120, y + 60], 200, 340, fill="#F3E6E0", width=2)
        d.arc([700 - (i % 4) * 60, y - 50, 1300, y + 70], 190, 330, fill="#F3E6E0", width=2)
    font = fit_font(BRUSH, text, 900, 160, 96)
    lines = layout(text, font, 900)
    line_h = int(font.size * 1.3)
    y0 = (H - line_h * len(lines)) // 2 - 120
    draw_lines(d, lines, font, 100, y0, line_h, "#D9301F", None)
    paste_emoji(img, emoji, (W // 2, 1120), 110)
    return img


def list_card(text, emoji, title="", **_):
    tfont, bfont = find_font(BOLD, 56), find_font(REGULAR, 46)
    body = layout(text, bfont, 960)
    th = len(layout(title, tfont, 960)) * 78 if title else 0
    height = max(H, 160 + th + len(body) * 68 + 120)
    img = Image.new("RGB", (W, height), "white")
    d = ImageDraw.Draw(img)
    d.line([0, 110, W, 110], fill="#EEEEEE", width=2)
    d.text((40, 30), "‹", font=find_font(REGULAR, 60), fill="#333333")
    y = 140
    if title:
        y = draw_lines(d, layout(title, tfont, 960), tfont, 50, y, 78, "#222222", None) + 24
    draw_lines(d, body, bfont, 50, y, 68, "#333333", "#FFE680", "bar")
    return img


def essay(text, emoji, title="", **_):
    """信徒理性长文体封面：米白底，粗黑大标题压在浅米色色块上，下面一段正文。
    仿信徒长文帖常见的封面版式。"""
    img = Image.new("RGB", (W, H), "#FAF8F5")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 44], fill="#FBEFE2")
    tfont = fit_font(BOLD, title or "", 820, 104, 76)
    tlines = layout(title, tfont, 820) if title else []
    tline_h = int(tfont.size * 1.36)
    y = 300
    if tlines:
        top, bottom = y - 20, y + tline_h * len(tlines) + 6
        d.rectangle([72, top, 952, bottom], fill="#FBEFE2")
        d.line([72, top, 72, top + tline_h], fill="#B38B5D", width=3)  # 选中光标
        d.line([952, bottom - tline_h, 952, bottom], fill="#B38B5D", width=3)
        draw_lines(d, tlines, tfont, 120, y, tline_h, "#1F1A17", None)
        y = bottom + 220
    bfont = find_font(REGULAR, 44)
    blines = layout(text, bfont, 940)
    room = max(1, (H - 120 - y) // 74)  # 留出底部「纯属虚构」小字的位置
    if len(blines) > room:  # 正文太长就截断，末尾补省略号，像截图截了半屏
        blines = blines[:room]
        blines[-1] = blines[-1][:-2] + [("…", False), ("…", False)]
    draw_lines(d, blines, bfont, 72, y, 74, "#2B2B2B", "#FBE3C8", "bar")
    return img


def photo(text, emoji, image=None, pos="bottom", color="white", **_):
    """一图一句：在一张照片上压一行字。白字黑描边（或黄字、红字），宽度统一缩放到 1080。"""
    if not image or not os.path.exists(image):
        sys.exit("photo 样式需要 --image 指向一张存在的图片")
    img = Image.open(image).convert("RGB")
    r = W / img.width
    img = img.resize((W, max(1, int(img.height * r))), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    fill = {"white": "#FFFFFF", "yellow": "#FFE14D", "red": "#E8231F"}.get(color, "#FFFFFF")
    stroke = "#000000" if fill != "#E8231F" else "#FFFFFF"
    font = fit_font(BOLD, text, W - 120, 84, 48)
    plain = text.replace("==", "")
    n = len(layout(plain, font, W - 120))
    total = sum(char_w(c, font) for c in plain if c != "\n")
    # 行数不变的前提下把每行宽度均分，避免最后一行只剩两三个字
    max_w = min(W - 120, total / n + font.size * 1.5) if n > 1 and "\n" not in plain.replace("\\n", "\n") else W - 120
    lines = ["".join(c for c, _ in ln) for ln in layout(plain, font, max_w)]
    line_h = int(font.size * 1.3)
    block = line_h * len(lines)
    y = {"top": 80, "center": (img.height - block) // 2}.get(pos, img.height - block - 120)
    for ln in lines:
        w = font.getlength(ln)
        d.text(((W - w) / 2, y), ln, font=font, fill=fill, stroke_width=max(3, font.size // 14), stroke_fill=stroke)
        y += line_h
    return img


STYLES = {"notes": notes, "quote": quote, "brush": brush, "list": list_card, "essay": essay, "photo": photo}


def main():
    try:  # Windows 控制台默认 GBK，中文文件名会打印成乱码
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=STYLES, default="notes")
    ap.add_argument("--text", default="")
    ap.add_argument("--text-file")
    ap.add_argument("--title", default="")
    ap.add_argument("--emoji", default="")
    ap.add_argument("--color", default="green")
    ap.add_argument("--footnote", default="伪史论模仿秀·纯属虚构", help="左下角灰色小字，可改措辞；红线 5 要求始终保留")
    ap.add_argument("--image", help="photo 样式用的底图")
    ap.add_argument("--pos", choices=["top", "center", "bottom"], default="bottom", help="photo 样式文字位置")
    ap.add_argument("-o", "--out", default="card.png")
    a = ap.parse_args()
    text = open(a.text_file, encoding="utf-8").read() if a.text_file else a.text
    img = STYLES[a.style](text=text, emoji=a.emoji, color=a.color, title=a.title, image=a.image, pos=a.pos)
    if a.footnote:
        d = ImageDraw.Draw(img)
        if a.style == "photo":  # 照片底色不定，加描边保证看得见
            d.text((40, img.height - 56), a.footnote, font=find_font(REGULAR, 26), fill="#F2F2F2", stroke_width=2, stroke_fill="#333333")
        else:
            d.text((48, img.height - 70), a.footnote, font=find_font(REGULAR, 26), fill="#9A9A9A")
    img.save(a.out)
    print(a.out, img.size)


if __name__ == "__main__":
    main()
