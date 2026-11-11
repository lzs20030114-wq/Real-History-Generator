"""调用文生图接口出 AI 插画（上古设定、伪古画、伪地图、梗图底图）。走 OpenAI 兼容的 /images/generations 接口，
国内外大多数生图服务都兼容这个格式。

配置（任选一种，命令行参数 > 环境变量 > 配置文件）：
  环境变量  PHP_IMAGE_PROVIDER   预设名，见下表（可不填，只填 BASE_URL 就按通用 OpenAI 格式）
            PHP_IMAGE_API_KEY    你的 key
            PHP_IMAGE_BASE_URL   接口地址，填到 /v1 这一级（用预设时可不填）
            PHP_IMAGE_MODEL      模型名（用预设时可不填）
  配置文件  skill 文件夹下的 image_config.json：{"provider": "siliconflow", "api_key": "sk-...", "model": "..."}

预设（模型名会更新，以服务商文档为准，用 PHP_IMAGE_MODEL 覆盖）：
  openai       https://api.openai.com/v1                 gpt-image-1
  siliconflow  https://api.siliconflow.cn/v1             Kwai-Kolors/Kolors（硅基流动，也有 Qwen-Image、FLUX 等）
  ark          https://ark.cn-beijing.volces.com/api/v3  doubao-seedream-3-0-t2i-250415（火山方舟·豆包）
  zhipu        https://open.bigmodel.cn/api/paas/v4      cogview-4（智谱）
  local        http://127.0.0.1:8000/v1                  自己部署的模型（如 Janus-Pro、SD、FLUX，前面套一层 OpenAI 兼容服务）

用法：
  python gen_image.py --prompt "Antique Chinese scroll illustration ..." --aspect 3:4 -o ai.png
  python gen_image.py --check          # 只检查有没有配置，不出图

出的图右下角固定加「AI生成·纯属虚构」小字（红线 3），--no-mark 不存在。
没有配置时退出码为 2，调用方据此改用找照片或文字卡。
"""
import argparse
import base64
import io
import json
import os
import sys

import requests
from PIL import Image, ImageDraw, PngImagePlugin

HERE = os.path.dirname(os.path.abspath(__file__))
PRESETS = {
    "openai": {"base": "https://api.openai.com/v1", "model": "gpt-image-1",
               "sizes": {"3:4": "1024x1536", "1:1": "1024x1024", "4:3": "1536x1024", "16:9": "1536x1024", "9:16": "1024x1536"}},
    "siliconflow": {"base": "https://api.siliconflow.cn/v1", "model": "Kwai-Kolors/Kolors", "size_field": "image_size",
                    "extra": {"batch_size": 1},
                    "sizes": {"3:4": "768x1024", "1:1": "1024x1024", "4:3": "1024x768", "16:9": "1024x576", "9:16": "720x1280"}},
    "ark": {"base": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-seedream-3-0-t2i-250415",
            "extra": {"watermark": False, "response_format": "url"},
            "sizes": {"3:4": "864x1152", "1:1": "1024x1024", "4:3": "1152x864", "16:9": "1280x720", "9:16": "720x1280"}},
    "zhipu": {"base": "https://open.bigmodel.cn/api/paas/v4", "model": "cogview-4",
              "sizes": {"3:4": "864x1152", "1:1": "1024x1024", "4:3": "1152x864", "16:9": "1344x768", "9:16": "768x1344"}},
    "local": {"base": "http://127.0.0.1:8000/v1", "model": "default",
              "sizes": {"3:4": "768x1024", "1:1": "1024x1024", "4:3": "1024x768", "16:9": "1024x576", "9:16": "576x1024"}},
}
GENERIC_SIZES = {"3:4": "768x1024", "1:1": "1024x1024", "4:3": "1024x768", "16:9": "1024x576", "9:16": "576x1024"}


def load_config(a):
    cfg = {}
    path = os.path.join(os.path.dirname(HERE), "image_config.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    pick = lambda arg, env, key: arg or os.environ.get(env) or cfg.get(key)
    provider = pick(a.provider, "PHP_IMAGE_PROVIDER", "provider")
    preset = PRESETS.get(provider or "", {})
    if provider and not preset:
        sys.exit(f"不认识的预设 {provider}，可选：{', '.join(PRESETS)}；或者不填预设、直接填 PHP_IMAGE_BASE_URL")
    base = pick(a.base_url, "PHP_IMAGE_BASE_URL", "base_url") or preset.get("base")
    key = pick(None, "PHP_IMAGE_API_KEY", "api_key")
    model = pick(a.model, "PHP_IMAGE_MODEL", "model") or preset.get("model")
    return provider, preset, base, key, model


def extract_image(data, timeout):
    """兼容几种常见返回：data[].b64_json / data[].url / images[].url"""
    items = data.get("data") or data.get("images") or []
    if not items:
        raise RuntimeError(f"返回里没有图片：{json.dumps(data, ensure_ascii=False)[:300]}")
    it = items[0]
    if it.get("b64_json"):
        return Image.open(io.BytesIO(base64.b64decode(it["b64_json"])))
    if it.get("url"):
        r = requests.get(it["url"], timeout=timeout)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content))
    raise RuntimeError(f"看不懂的返回格式：{json.dumps(it, ensure_ascii=False)[:300]}")


def mark(img, text="AI生成·纯属虚构"):
    sys.path.insert(0, HERE)
    from make_card import find_font, REGULAR
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    font = find_font(REGULAR, max(18, img.width // 42))
    w = font.getlength(text)
    d.text((img.width - w - img.width // 40, img.height - font.size * 2), text, font=font,
           fill="#F2F2F2", stroke_width=2, stroke_fill="#333333")
    return img


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows 控制台默认 GBK，报错信息会乱码
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", help="提示词，英文通常更稳；中文字不要指望模型写对，出图后用 make_card / make_meme 压字")
    ap.add_argument("--negative", default="", help="反向提示词（部分服务支持）")
    ap.add_argument("--aspect", choices=list(GENERIC_SIZES), default="3:4")
    ap.add_argument("--size", help="直接指定尺寸，如 1024x1536，覆盖 --aspect")
    ap.add_argument("--provider", help=f"预设：{', '.join(PRESETS)}")
    ap.add_argument("--base-url")
    ap.add_argument("--model")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--check", action="store_true", help="只检查配置")
    ap.add_argument("-o", "--out", default="ai.png")
    a = ap.parse_args()

    provider, preset, base, key, model = load_config(a)
    if not base or (not key and provider != "local"):
        print("没有配置生图接口：设置 PHP_IMAGE_PROVIDER + PHP_IMAGE_API_KEY（或 PHP_IMAGE_BASE_URL），"
              "或者在 skill 文件夹放 image_config.json。改用 find_photo.py 找真实照片，或 make_card.py 出文字卡。")
        sys.exit(2)
    if a.check:
        print(f"已配置：provider={provider or '通用'} base={base} model={model}")
        return
    if not a.prompt:
        ap.error("需要 --prompt")

    size = a.size or preset.get("sizes", GENERIC_SIZES)[a.aspect]
    body = {"model": model, "prompt": a.prompt, preset.get("size_field", "size"): size, **preset.get("extra", {})}
    if provider not in ("siliconflow",):
        body["n"] = 1
    if a.negative:
        body["negative_prompt"] = a.negative
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    url = base.rstrip("/") + "/images/generations"
    try:
        r = requests.post(url, headers=headers, json=body, timeout=a.timeout)
    except requests.RequestException as e:
        sys.exit(f"请求失败：{e}")
    if r.status_code != 200:
        sys.exit(f"接口返回 {r.status_code}：{r.text[:500]}")
    img = mark(extract_image(r.json(), a.timeout))
    info = PngImagePlugin.PngInfo()
    info.add_text("php_ai_generated", "1")
    info.add_text("php_prompt", a.prompt[:1000])
    img.save(a.out, pnginfo=info)
    print(a.out, img.size, f"({provider or '通用'} / {model})")


if __name__ == "__main__":
    main()
