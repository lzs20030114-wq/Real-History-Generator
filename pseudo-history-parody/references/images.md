# 出图

> 脚本都在 skill 文件夹的 `scripts/` 下，命令里写绝对路径。所有图左下角或右下角都带「纯属虚构」小字，脚本自动加，不去掉。

## 目录
0. 先看自己能用哪一档
1. 什么帖配什么图
2. 找真实照片
3. AI 生图
4. 合成：几条完整流程
5. 不能跑命令时

---

## 0. 先看自己能用哪一档

从上往下，用第一个能用的：

| 档 | 条件 | 怎么出图 |
|---|---|---|
| 1 | 你自己带生图工具（宿主给了 image generation 一类的工具） | 用它出 AI 插画，再用 `make_meme.py` 压字 |
| 2 | 能跑命令，且 `gen_image.py --check` 退出码是 0 | `gen_image.py` 出 AI 插画，再压字 |
| 3 | 能跑命令、能联网 | `find_photo.py` 找真实照片，`make_meme.py` / `make_card.py` 压字、画圈、拼对比 |
| 4 | 能跑命令、不能联网 | 用户给的照片 + `make_meme.py`；没照片就 `make_card.py` 文字卡 |
| 5 | 不能跑命令 | 第 5 节的手动做图步骤，AI 插画给提示词 |

第 1、2 档只用来出**插画**（上古设定、伪地图、古画风、梗图底图）。建筑、文物这类真东西，优先用第 3 档的真实照片：信徒帖本来就是拿真照片说事，真照片配歪结论才好笑，也不会造假。

**看得见图的模型**（多模态）：下载完先看 `contact.jpg` 挑图，画红圈前先看原图定坐标。**看不见图的模型**：直接用 `01.jpg`（搜索排第一的通常是正面全景），不做 `annotate`，除非用户告诉你圈哪里。

## 1. 什么帖配什么图

| 信徒帖里常见的图 | 用哪个 | 说明 |
|---|---|---|
| 一张照片压一行字 | `make_card.py --style photo` | 朴素，像随手发的。**一图一句默认用这个** |
| 小红书 P 图：大字标题、关键词高亮、下面一行小字 | `make_meme.py --style xhs` | 照片自动裁 3:4，`==词==` 黄底高亮。比 `photo` 更像精心做过的帖，营销号体、上古设定集用 |
| 对比图："左边挪威，右边山西" | `make_meme.py --style compare` | 信徒最爱的证据形式：欧洲建筑 vs 中国建筑、字母 vs 汉字、纹样 vs 纹样。两张图各带红标签，可加顶部一句话 |
| 红圈标注 | `make_meme.py --style annotate` | 圈出纹样、屋檐、"可疑"的数字和朝向，旁边红字一句。破绽可以藏在圈的位置上（圈了个空调外机） |
| 群聊截图 | `make_meme.py --style chat` | 截图堆里的一张。"读书会""交流群"里几个人接话，最后一句懂的都懂。群名、昵称全部虚构 |
| 表情包：图 + 下面一行字 | `make_meme.py --style caption` | "当我发现钟楼朝东"。吃瓜一侧用得多，信徒在评论区也会甩 |
| 经典梗图：上下两行白字 | `make_meme.py --style meme` | 上句摆"官方说法"，下句歪结论 |
| 长文封面、纯文字卡 | `make_card.py` 的 `essay` / `quote` / `notes` / `brush` / `list` | 见 `xhs-formats.md` 第 2 节 |
| 上古设定、冰墙地图、伪古画 | AI 插画（第 3 节）+ `xhs` 或 `caption` 压字 | |

截图堆可以混着来：一张 `compare`、一张 `annotate`、一张 `chat`，图和图之间不解释关系。

## 2. 找真实照片

```bash
python <skill>/scripts/find_photo.py "Borgund stave church" -n 8 -o <输出目录>/photos
```

- 搜索词用英文或当地语言（维基共享资源以英文描述为主），想要细节就加 `detail` `ornament` `interior` `roof` `carving`
- 出来 `01.jpg`…、带编号的 `contact.jpg`、记录作者和授权的 `sources.json`
- **核对拍的是哪里**：看每张图的标题（脚本会打印，`sources.json` 里也有）。搜「Forbidden City」可能出来沈阳故宫，搜教堂可能出来同名的另一座。对比图的标签按照片实际拍的地方写
- 维基共享资源和 Openverse 的图都是开放授权，多数要求署名：在作者置顶评论里写一行「图：作者 / CC BY-SA 4.0 / 维基共享资源」，`sources.json` 里有现成的。正文末行照旧是「伪史论模仿秀·纯属虚构」
- 搜不到时，用 WebSearch 找到图片直链，`--url <地址>` 下载。这种图授权不明，交图时提醒用户自己确认能不能用
- 维基会限流（429），脚本会自动等一会儿重试；连着搜很多次就慢一点

不拿普通人的脸做梗图主体；真实公众人物的照片不配他们没说过的话（红线 2）。

## 3. AI 生图

### 给用户的配置说明

用户问"怎么接生图"时照这个说。`gen_image.py` 走 OpenAI 兼容的 `/images/generations` 接口，设三个环境变量就能用：

```bash
export PHP_IMAGE_PROVIDER=siliconflow     # 预设：openai / siliconflow / ark / zhipu / local
export PHP_IMAGE_API_KEY=sk-xxxx
export PHP_IMAGE_MODEL=Kwai-Kolors/Kolors # 可不填，用预设默认值
```

也可以在 skill 文件夹里放一个 `image_config.json`：`{"provider": "ark", "api_key": "...", "model": "..."}`。不在预设里的服务，不填 provider，直接设 `PHP_IMAGE_BASE_URL`（填到 `/v1` 那一级）。

| 预设 | 服务 | 备注 |
|---|---|---|
| `siliconflow` | 硅基流动 | 有 Kolors、Qwen-Image、FLUX 等，国内直连 |
| `ark` | 火山方舟（豆包 Seedream） | 中文提示词理解好 |
| `zhipu` | 智谱 CogView | |
| `openai` | OpenAI gpt-image | |
| `local` | 自己部署的模型 | 默认 `http://127.0.0.1:8000/v1`，前面要有一层 OpenAI 兼容服务 |

**关于 DeepSeek**：截至 2026 年 11 月，DeepSeek 官方 API 只有文本模型，没有生图接口。DeepSeek 家能生图的是开源的 Janus-Pro，要自己部署、套上 OpenAI 兼容接口后用 `local` 预设。用 DeepSeek 当主模型跑这个 skill 没问题，生图另配上面任意一家就行。

### 提示词规则

- 用英文写，风格词放前面
- **图里不要中文字**：模型写中文常常写错。提示词里写 `no text, blank area at top for title`，出图后用 `make_meme.py --style xhs` 或 `caption` 压字
- **一眼看得出是创作**：插画、古画风、工笔、青绿山水、版画、油画、动漫、奇幻地图。**不要**：写实文物照、考古现场照、博物馆展品照、档案扫描、古籍书页特写、新闻截图、证件公文、真实人物（红线 3）
- 脚本会在右下角加「AI生成·纯属虚构」，压字后左下角还有「伪史论模仿秀·纯属虚构」，两个都留着

### 提示词模板

**郑和船队抵达某地（古画风）**——欧洲建筑、港口类帖子的配图
```
Traditional Chinese handscroll painting style, Ming dynasty treasure fleet with huge nine-masted ships
arriving at [a Norwegian fjord with a wooden stave church on the shore], tiny figures unloading
[timber and roof tiles], ink and mineral colors on silk, faded, wide composition, no text, no seals
```

**上古神族营造（青绿山水）**——金字塔、巨石阵、斗兽场
```
Blue-green landscape painting in the style of Song dynasty, giant robed immortals floating on clouds
lifting enormous stone blocks to build [the Egyptian pyramids], cranes and auspicious clouds,
mineral pigments, gold outlines, no text, blank sky at the top
```

**南极冰墙外地图**
```
Fantasy world map, top-down, a circular ice wall ring in the center enclosing the real continents,
outside the ring: lush unknown continents, waterfalls, ancient ruins, oceans, mountain rings,
painterly, vivid, high detail, all map labels left blank, no text
```
压字时右下角加一句「虚构地图」。

**地月葫芦**
```
Whimsical illustration, the Earth and the Moon fused into one gourd shape floating in space,
ancient Chinese cloud patterns around it, bright retro poster colors, no text
```

**伪古籍插图（"……之图"）**
```
Antique Chinese woodblock print illustration, comic-panel layout, central scene of
[armored soldiers with ray guns chasing woolly mammoths in front of a Qing dynasty city gate],
four small panels below, sepia ink, obviously satirical, no text, no seals
```
标题、题跋全部出图后压上去（`xhs` 或 `caption`），不让模型写字、不画印章，避免像真古籍。

**梗图底图**（吃瓜一侧、表情包）
```
Cute cartoon cat peeking from behind a museum display case with wide shocked eyes, flat illustration, no text
```
不画有版权的角色（具体动漫人物、知名表情包原图）。

## 4. 合成：几条完整流程

**一图一句（真实照片）**
```bash
python <skill>/scripts/find_photo.py "Colosseum Rome exterior" -n 6 -o <dir>/photos
# 看 contact.jpg，挑 02
python <skill>/scripts/make_card.py --style photo --image <dir>/photos/02.jpg --text "他们连层数都数不清" --pos top -o <dir>/post.png
```

**对比图**
```bash
python <skill>/scripts/find_photo.py "Borgund stave church" -n 4 -o <dir>/a
python <skill>/scripts/find_photo.py "Yingxian wooden pagoda" -n 4 -o <dir>/b
python <skill>/scripts/make_meme.py --style compare --image <dir>/a/01.jpg --image2 <dir>/b/02.jpg \
  --label "挪威·博尔贡" --label2 "山西·应县" --title "同一个师傅" -o <dir>/p1.png
```
裁歪了用 `--focus 0.5,0.3`（裁切中心，相对坐标）调。

**红圈标注**：先看原图，估出要圈的位置（相对坐标，左上角 0,0，右下角 1,1），写进 `--marks`：
```bash
python <skill>/scripts/make_meme.py --style annotate --image <dir>/a/01.jpg \
  --marks '[{"type":"circle","box":[0.35,0.12,0.62,0.30],"label":"这不就是飞檐"},{"type":"arrow","from":[0.15,0.85],"to":[0.35,0.68],"label":"朝东"}]' \
  -o <dir>/p2.png
```
- 标签默认放在圈的正上方，上面没地方就放下方；箭头的标签放在箭尾
- `"label_at": [x, y]` 自己指定位置：文字水平居中在 x，顶边在 y 稍下方
- 全景照没有空白处、标签只能压在主体上时，加 `"tag": true`，换成红底白字，压在花纹上也看得清
- 两个圈说同一件事（"双阙"），只给一个圈写 label，用 `label_at` 放在两圈中间

出图后看一眼，圈偏了、标签压线了就改坐标重出。

**群聊截图**：内容写进文本文件，每行 `L 昵称: 话` / `R: 话` / `T 时间`，发图用 `L 昵称: [图] 相对路径`。控制在 6～8 条消息（超过 2400px 高，小红书会裁掉，脚本会提醒），话多就拆成两张：
```bash
python <skill>/scripts/make_meme.py --style chat --title "正本清源读书会(328)" --text-file <dir>/chat.txt -o <dir>/p3.png
```

**AI 插画 + 压字**
```bash
python <skill>/scripts/gen_image.py --check   # 退出码 2 = 没配置，改走真实照片
python <skill>/scripts/gen_image.py --prompt "Blue-green landscape painting ... no text, blank sky at the top" --aspect 3:4 -o <dir>/ai.png
python <skill>/scripts/make_meme.py --style xhs --image <dir>/ai.png --title "金字塔是==谁==搬的\n心里没数吗" -o <dir>/cover.png
```

## 5. 不能跑命令时

不出现命令和文件名，告诉用户怎么做：

- **找图**：给出能直接搜到的英文名，"去维基共享资源（commons.wikimedia.org）搜 Borgund stave church，挑正面那张"
- **一图一句 / P 图**：醒图、美图秀秀的"文字"，白字黑描边、字大，关键词换黄底
- **对比图**：美图秀秀"拼图"选上下两格，每格左上角加红底白字标签
- **红圈**：手机相册自带的"标记/涂鸦"，红笔手画一个圈，旁边写两三个字
- **群聊截图**：别用真群截图（有真实头像和昵称）。照着要说的话描述给用户，或者用备忘录代替
- **AI 插画**：给第 3 节的英文提示词，说明"图里别让 AI 写字，出图后自己加"
- 每张图左下角都加一行小字「伪史论模仿秀·纯属虚构」

能出 HTML/SVG 但跑不了 Python 的环境（比如只能渲染网页的对话界面）：纯文字卡可以用 HTML/SVG 做，照片类的图不要用 SVG 去画"假照片"，改给手动步骤。
