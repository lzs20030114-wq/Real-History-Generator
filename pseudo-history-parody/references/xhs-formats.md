# 小红书图文格式

> 第 1 节标题公式、第 3 节梗图模板多数来自吃瓜一侧（嘲笑伪史论的帖子）。写信徒帖时，标题按 `believer-voice.md` 的文体起；短帖用 `photo` 在照片上压一行字，长文帖封面用 `essay`。信徒帖不做"P1 观点、P2 解释"的分页排版。

## 目录
1. 标题公式
2. 封面：四种纯文字卡（脚本直接出图）
3. 梗图模板（给出版式说明，用户自己拼图或用 AI 生成）
4. AI 插画提示词模板
5. 正文与话题

---

## 1. 标题公式

常见标题大致是下面几种：

| 公式 | 例子（仿写） |
|---|---|
| 征集令 | 开个帖收集伪史文案，永久保存 / 无内鬼，来点伪史笑话 |
| 情绪反应 | 伪史论给我笑醒了 / 上班太累了，需要一点伪史论续命。/ 闹麻了 |
| 断瘾体 | 已经一分钟没刷到伪史笑话了，快来点 |
| 信徒口吻 | 揭穿西方伪造"大象"的谎言！/ 对上了 / 你们从来都不是神族 |
| belike | 伪史梗玩多了的朋友 belike： |
| 系列编号 | 伪史笑话（12）之某某碑 / 辟谣第 N 期 |
| 冷知识反讽 | 冷知识：考试写伪史论可以破格满分 |
| 求科普（反串） | 有没有懂的来科普一下，这两个有什么关系？ |

标题 ≤20 字，末尾可加一个 emoji 或"。"（句号会显得更冷）。

## 2. 封面：纯文字卡

> 能运行命令的环境（Claude Code）由 Claude 自己用绝对路径跑脚本、把图片交给用户；不能运行的环境（claude.ai 网页端）不给命令，改成手动做图步骤，见 SKILL.md"出图"一节。

用 `scripts/make_card.py` 直接出 1080×1440 的 PNG。`==词==` 标高亮，`\n` 强制换行，左下角默认带灰色小字「伪史论模仿秀·纯属虚构」（红线 5 要求始终保留，`--footnote` 只用来改措辞）。

几个坑：
- 🗼 是东京塔，不是埃菲尔铁塔；没有埃菲尔铁塔 emoji。选 emoji 前想想它在苹果/微软字体里到底长什么样。
- 很长的段落脚本会自动折行（英文、数字不拆，标点不落行首），但要控制断在哪里时，还是手动用 `\n` 换行更稳。
- `list` 每条之间空一行（文本里放一个空行），编号要自己写进文本。
- `brush` 字号会自动缩放，每行 ≤8 字效果最好。

| style | 样子 | 适合 |
|---|---|---|
| `photo` | 任意照片宽度缩到 1080，压一行白字黑描边（`--color yellow/red` 可换），`--pos top/center/bottom` | **一图一句**，信徒帖最常见的形式 |
| `essay` | 米白底，粗黑大标题压米色块，下接一段正文（`--title` + `--text`） | **信徒帖默认封面**，理性长文体 |
| `notes` | 苹果备忘录：黄色顶栏、格子纸、黄色块高亮、底部大 emoji | 征集帖、"永远不删"类 |
| `quote` | 浅色底（`--color green/pink/blue/yellow`）、大引号、荧光笔高亮 | 情绪句、谶语反串、断瘾体 |
| `brush` | 米白底、红色行楷 | 一句话钩子，越短越好（≤2 行，每行 ≤8 字） |
| `list` | 白底长截图，标题 + 编号正文 | 索隐清单、伪史论笑话合集、"天啊顿悟红楼梦"体 |

```bash
python scripts/make_card.py --style notes --text "开个帖收集==伪史==文案，永久保存" --emoji "⛈️" -o cover.png
python scripts/make_card.py --style quote --color pink --text "零下91度的酷寒\n藏在==南极冰川==的湖岸\n冰封？🩸河？" -o cover.png
python scripts/make_card.py --style brush --text "伪史论\n给我笑醒了" -o cover.png
python scripts/make_card.py --style list --title "天啊，顿悟红楼梦" --text-file items.txt -o p2.png
```

依赖：Python + Pillow，系统里有微软雅黑/思源黑体（Windows 自带）。行楷优先用华文行楷 STXINGKA，没有就退到楷体。

## 3. 梗图模板

这些需要真实图片素材，脚本不出图。给用户写清楚：画布、元素位置、每块文字。

### A. 信徒非蠢即坏（wojak 对比）
- 横版 16:9。顶部红色横幅白字：「"西方伪物"信徒非蠢即坏！！」
- 左半：wojak 怒吼头像，周围散落 8–10 句信徒口号（反问句、感叹号、偶尔加粗"常识"）
- 右半：被质疑的东西（大象/袋鼠/冰岛地图）+ 一个尴尬流汗的旁观者（罗马人 chad 头像）+ 两个😅
- 底部小字脚注：「*经询问，该"XX传统"指《山海经》」← 这个脚注是点睛之笔，一定要有

### B. 古人 vs 今人
- 方形。上半「古罗马人：」两个罗马人对话「看我做了什么！这是一个… / 别说了，很明显！我们甚至都不用把它写下。」中间是文物
- 下半「今天的考古学家：」猫猫探头「他们是用它来干嘛的??」
- 伪史论变体：下半换成「今天的伪史论：」「这一看就是郑和留下的！」

### C. XX belike / 某些人的世界观
- 上方大字「某些人的世界观：」，左边一摞看起来很学术的书，右边一只德牧 +「原来这才是真相」
- 变体：AI 二次元图「伪史论者认为的学校 belike」（兽耳学生被成群的白发红眼女仆包围）

### D. 聊天记录截图
- 微信/小红书私信气泡，3–5 条。最后一条是伪史论式的过度解读（"为啥不能说午修？午有什么禁忌吗 和汉族"）
- 可以用 HTML 或备忘录截图仿制，头像用表情包

### E. 推特/评论截图
- 一条看起来正经的冷知识 + 一条神回复。用 `list` style 可以近似

### F. 伪地图
- 竖版。标题「南极冰墙外的传说地图·上集」，中间圆形冰墙围住现实大陆，外圈是亚特兰蒂斯、姆大陆、雷姆利亚、许珀耳玻瑞亚、阿斯加德、图勒……
- 右下角必须有小字：「虚构地图；地名取自传说与现代创作」
- AI 提示词见下一节

### G. 地月葫芦 / 神族证据图
- 地球与月球连成一个葫芦形，配字「地月本为一体🌍🌕，现在…」，再配一个夸张的 "COOL" 贴纸

## 4. AI 插画提示词模板

给 Midjourney / 即梦 / 豆包等用。中文字在 AI 图里容易错，标题和题跋建议出图后用美图秀秀或 PS 自己加。

**伪古籍告示（"……之图"）**
```
Antique Chinese scroll illustration, aged parchment, ornate dragon border, comic-panel layout:
large central scene of [beetle-headed armored soldiers with ray guns attacking a herd of woolly mammoths
in front of a Qing dynasty city gate], four small panels below, vertical calligraphy columns on both sides,
red seal stamps, sepia ink and muted color, highly detailed, satirical, --ar 5:4
```
后期加字：标题「[甲]因[乙]不信伪史论而将其灭绝之图」、副标题「大清乾隆年间真实事件」、四格小标题（高科技武器展示 / 惨遭灭绝 / 灭绝后篡改历史 / 新编史书发布）、底部「历史由胜利者书写，真理由信仰者定义！」。

**南极冰墙外地图**
```
Fantasy world map, top-down, a circular ice wall ring in the center enclosing the real continents,
outside the ring: lush unknown continents, waterfalls, ancient ruins, oceans, mountain rings,
painterly, vivid, high detail, map labels area left blank --ar 3:4
```

**西方伪物证据照**
```
Fake museum exhibit photo of a [elephant / kangaroo] labeled as a forgery, gallery lighting,
small placard, deadpan documentary style --ar 3:4
```

**伪史论学校 belike**
```
Anime style, two scared girls with animal ears (sheep and cat) crouching behind an iron fence holding a tablet,
behind the fence an endless crowd of identical white-haired red-eyed maids staring, European campus, sunny --ar 3:4
```

## 5. 吃瓜帖的正文与话题

（信徒帖不适用：信徒帖的话题标签见 `believer-voice.md` 第 3 节，正文长度按文体走。）

- 正文 80–300 字，口语、短句；征集帖正文只要一句（"我错了我不该熬夜半夜刷到这些以为自己活到头了"）
- 小红书表情：[笑哭R] [捂脸R] [扶额R] [坏笑R] [doge] [呃R] [种草R]
- 常用话题：#伪史论笑话 #伪史论笑话合集 #伪史论 #伪史 #对上了对上了 #伪史论患者 #西方伪史论 #地狱笑话 #野史 #红楼梦 #神族 #正本明源（反串时用）#有想法随时发 #轻松绷住
