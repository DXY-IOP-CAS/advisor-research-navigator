from __future__ import annotations

from html import escape
from pathlib import Path


OUT = Path(__file__).resolve().parent
FONT = "Microsoft YaHei, Noto Sans CJK SC, PingFang SC, Arial, sans-serif"

INK = "#202428"
MUTED = "#5d6670"
LINE = "#2f3337"
BG = "#fbfaf7"
PAPER = "#ffffff"

BLUE = "#dce9f6"
GREEN = "#d9ead3"
AMBER = "#f6e7c6"
RED = "#f1d4cf"
VIOLET = "#e7ddf2"
GRAY = "#eef1f3"
ROSE = "#fff7f5"


def text(x: int, y: int, value: str, cls: str = "txt", anchor: str | None = None) -> str:
    extra = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{x}" y="{y}" class="{cls}"{extra}>{escape(value)}</text>'


def path(d: str, cls: str = "line", fill: str = "none") -> str:
    return f'<path d="{d}" class="{cls}" fill="{fill}"/>'


def rect(x: int, y: int, w: int, h: int, fill: str = PAPER, rx: int = 8, cls: str = "box") -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" class="{cls}"/>'


def circle(cx: int, cy: int, r: int, fill: str, cls: str = "box") -> str:
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" class="{cls}"/>'


def ellipse(cx: int, cy: int, rx: int, ry: int, fill: str, cls: str = "box") -> str:
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" class="{cls}"/>'


def svg(width: int, height: int, title: str, subtitle: str, body: list[str]) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" font-family="{FONT}">
  <defs>
    <marker id="arrow" markerWidth="11" markerHeight="11" refX="9" refY="4.5" orient="auto"><path d="M0,0 L10,4.5 L0,9 Z" fill="{LINE}"/></marker>
    <style>
      .title{{font-size:24px;font-weight:700;fill:{INK}}}
      .note{{font-size:13px;fill:{MUTED}}}
      .head{{font-size:15px;font-weight:700;fill:{INK}}}
      .txt{{font-size:13px;fill:#343a40}}
      .small{{font-size:12px;fill:{MUTED}}}
      .box{{stroke:{LINE};stroke-width:1.6}}
      .thin{{stroke:{LINE};stroke-width:1.2}}
      .line{{stroke:{LINE};stroke-width:2;fill:none;marker-end:url(#arrow)}}
      .curve{{stroke:{LINE};stroke-width:2;fill:none;marker-end:url(#arrow)}}
      .soft{{stroke:#9aa0a6;stroke-width:1.3;fill:none}}
      .weak{{stroke:#6f7780;stroke-width:1.7;fill:none;stroke-dasharray:7 5;marker-end:url(#arrow)}}
      .return{{stroke:#6f7780;stroke-width:1.7;fill:none;stroke-dasharray:4 6}}
      .bad{{stroke:#8a3a32;stroke-width:2.3;fill:none}}
      .region{{stroke:{LINE};stroke-width:1.6;opacity:.92}}
    </style>
  </defs>
  <rect x="16" y="16" width="{width - 32}" height="{height - 32}" rx="14" fill="{BG}" stroke="{LINE}" stroke-width="2"/>
  {text(38, 50, title, "title")}
  {text(38, 76, subtitle, "note")}
  {"".join(body)}
</svg>
'''


def write(name: str, content: str) -> None:
    (OUT / name).write_text(content, encoding="utf-8", newline="\n")


def vocabulary() -> None:
    body: list[str] = []
    body.append(circle(540, 320, 52, VIOLET))
    body.append(text(540, 313, "学生输出", "head", "middle"))
    body.append(text(540, 338, "决定图形语法", "small", "middle"))

    # Map / region
    body.append(path("M78 156 C60 108 104 84 154 96 C214 110 238 152 206 196 C172 240 92 218 78 156 Z", "region", BLUE))
    body.append(path("M126 158 C118 132 146 120 176 132 C206 146 204 182 172 190 C142 198 130 180 126 158 Z", "region", GREEN))
    body.append(circle(184, 168, 10, RED))
    body.append(text(142, 260, "地图 / 区域", "head", "middle"))
    body.append(text(142, 284, "范围、包含、相邻", "small", "middle"))

    # Hierarchy
    body.append(circle(414, 126, 30, AMBER))
    body.append(text(414, 131, "领域", "small", "middle"))
    for cx, cy, label in [(350, 206, "子域"), (478, 206, "问题")]:
        body.append(path(f"M414 156 C400 176 {cx+8} {cy-18} {cx} {cy-4}", "soft"))
        body.append(circle(cx, cy, 26, BLUE if label == "子域" else GREEN))
        body.append(text(cx, cy + 5, label, "small", "middle"))
    body.append(text(414, 268, "层级 / 分类树", "head", "middle"))
    body.append(text(414, 292, "上下位、集合拆分", "small", "middle"))

    # Concept map
    for cx, cy, label, fill in [(800, 132, "概念A", GREEN), (916, 112, "概念B", BLUE), (926, 210, "概念C", AMBER)]:
        body.append(circle(cx, cy, 32, fill))
        body.append(text(cx, cy + 5, label, "small", "middle"))
    body.append(path("M832 128 C858 122 878 118 884 116", "curve"))
    body.append(text(858, 104, "属于", "small", "middle"))
    body.append(path("M826 152 C862 184 888 198 898 204", "curve"))
    body.append(text(858, 188, "支撑", "small", "middle"))
    body.append(text(874, 272, "概念图", "head", "middle"))
    body.append(text(874, 296, "带动词边的命题关系", "small", "middle"))

    # Mechanism
    body.append(text(874, 360, "机制示意", "head", "middle"))
    body.append(path("M728 410 L786 410", "line"))
    body.append(path("M802 388 C842 366 896 372 928 410 C896 448 840 452 802 430 Z", "region", AMBER))
    body.append(text(866, 416, "系统", "small", "middle"))
    body.append(path("M928 410 L982 410", "line"))
    body.append(circle(1006, 410, 20, VIOLET))
    body.append(text(1006, 415, "测量", "small", "middle"))
    body.append(text(874, 478, "输入、处理、测量、输出", "small", "middle"))

    # Route / bridge
    body.append(text(820, 558, "路线 / 阶梯", "head", "middle"))
    for i, (cx, cy, label) in enumerate([(696, 526, "基础"), (774, 500, "概念"), (852, 470, "论文图")]):
        body.append(ellipse(cx, cy, 38, 18, [BLUE, GREEN, RED][i]))
        body.append(text(cx, cy + 5, label, "small", "middle"))
        if i < 2:
            body.append(path(f"M{cx+38} {cy} C{cx+56} {cy-6} {cx+78} {cy-14} {cx+100} {cy-22}", "curve"))
    body.append(text(820, 582, "时间或前置能力", "small", "middle"))

    # Comparison
    body.append(text(356, 558, "比较图", "head", "middle"))
    body.append(ellipse(300, 468, 70, 48, BLUE))
    body.append(ellipse(372, 468, 70, 48, GREEN))
    body.append(text(284, 472, "方向A", "small", "middle"))
    body.append(text(388, 472, "方向B", "small", "middle"))
    body.append(text(336, 472, "交集", "small", "middle"))
    body.append(path("M466 512 L466 422 M424 470 L518 470", "soft"))
    body.append(circle(500, 440, 8, RED))
    body.append(circle(446, 492, 8, AMBER))
    body.append(text(356, 582, "差异、交集、二维判断", "small", "middle"))

    # Evidence
    body.append(text(154, 558, "证据图", "head", "middle"))
    for x, fill, label in [(74, ROSE, "弱"), (154, AMBER, "交叉"), (234, GREEN, "直接")]:
        body.append(rect(x, 416, 66, 54, fill, 8))
        body.append(text(x + 33, 448, label, "small", "middle"))
    body.append(text(154, 496, "边界卡", "small", "middle"))
    body.append(text(154, 582, "强弱、复核点、不确定性", "small", "middle"))

    # Annotated figure and data chart
    body.append(text(626, 128, "标注论文图", "head", "middle"))
    body.append(path("M570 194 L570 132 L680 132", "soft"))
    body.append(path("M582 176 C606 150 640 146 666 162", "curve"))
    body.append(circle(638, 150, 7, RED))
    body.append(path("M644 150 L696 104", "weak"))
    body.append(text(712, 108, "读法标注", "small"))
    body.append(text(626, 220, "论文图先看哪里", "small", "middle"))

    body.append(text(602, 520, "数据图", "head", "middle"))
    body.append(path("M560 468 L560 398 L668 398", "soft"))
    for x, h, fill in [(580, 26, BLUE), (610, 44, GREEN), (640, 60, AMBER)]:
        body.append(rect(x, 468 - h, 18, h, fill, 2))
    body.append(circle(590, 424, 5, RED))
    body.append(circle(638, 408, 5, VIOLET))
    body.append(text(602, 544, "真实数量、趋势、分布", "small", "middle"))

    write("s4-visual-vocabulary.svg", svg(1080, 640, "S4 图形谱系", "图不是把文字装进框里；不同理解任务需要不同图像语法。", body))


def field_map() -> None:
    body: list[str] = []
    bands = [
        (92, 126, 430, 62, BLUE, "大领域", "先把方向放进可阅读的大范围"),
        (132, 210, 390, 62, GREEN, "方法入口", "再分清方法、对象和问题入口"),
        (172, 294, 350, 62, AMBER, "问题域", "最后收窄到后文要读的问题"),
        (212, 378, 310, 62, RED, "导师入口", "只表示本文的阅读入口"),
    ]
    for x, y, w, h, fill, head, detail in bands:
        body.append(rect(x, y, w, h, fill, 10))
        body.append(text(x + 24, y + 28, head, "head"))
        body.append(text(x + 24, y + 52, detail, "small"))
    for y in [190, 274, 358]:
        body.append(path(f"M306 {y} L306 {y + 20}", "soft"))

    body.append(rect(600, 126, 380, 126, PAPER, 10))
    body.append(text(626, 164, "相邻方向", "head"))
    body.append(text(626, 194, "只写容易混用的方向和复核点", "txt"))
    body.append(text(626, 224, "证据不足时不画点位、不画距离", "small"))
    body.append(path("M568 188 C534 204 526 248 554 286", "weak"))
    body.append(text(612, 292, "虚线 = 需要回 S1 复核", "small"))

    body.append(rect(600, 306, 380, 112, PAPER, 10))
    for i, (label, detail, y) in enumerate([
        ("允许读出", "阅读层级、相邻方向、复核点", 342),
        ("禁止读出", "坐标、面积、距离、学科上下位", 390),
    ]):
        body.append(circle(636, y - 5, 12, [GREEN, ROSE][i]))
        body.append(text(686, y, label, "head"))
        body.append(text(686, y + 24, detail, "small"))
    body.append(text(78, 472, "限制：这是阅读入口层次，不是学科分类树；如果只能证明“可能相关”，退回证据边界卡，不画范围定位。", "txt"))
    write("s4-field-map.svg", svg(1080, 500, "领域范围地图", "用于 02：让学生看见大领域、方法入口、问题域、导师入口和相邻方向的关系。", body))


def paper_role_map() -> None:
    body: list[str] = []
    body.append(circle(540, 254, 70, AMBER))
    body.append(text(540, 246, "共同问题", "head", "middle"))
    body.append(text(540, 270, "论文群围绕什么推进", "small", "middle"))
    nodes = [
        (252, 156, "入口论文", BLUE, "提出问题"),
        (300, 356, "方法论文", GREEN, "提供方法"),
        (804, 158, "目标论文", RED, "验证对象"),
        (792, 354, "旁支线索", PAPER, "需复核"),
    ]
    for x, y, label, fill, edge in nodes:
        cls = "box" if fill != PAPER else "box"
        body.append(circle(x, y, 50, fill, cls))
        body.append(text(x, y - 2, label, "head", "middle"))
        body.append(text(x, y + 21, edge, "small", "middle"))
    body.append(path("M300 170 C386 172 442 196 484 226", "curve"))
    body.append(text(390, 172, "提出问题", "small", "middle"))
    body.append(path("M344 338 C418 318 458 292 492 276", "curve"))
    body.append(text(420, 326, "提供方法", "small", "middle"))
    body.append(path("M604 226 C654 196 710 174 754 164", "curve"))
    body.append(text(686, 182, "验证对象", "small", "middle"))
    body.append(path("M604 286 C680 332 718 348 742 354", "weak"))
    body.append(text(682, 330, "需复核", "small", "middle"))
    body.append(rect(80, 422, 920, 42, PAPER, 8))
    body.append(text(104, 449, "限制：每条边必须写动词关系并回到摘要、方法、图表、正文或互引；题名相似不能画线。", "txt"))
    write("s4-paper-role-map.svg", svg(1080, 510, "论文角色概念图", "用于 03：不是论文列表美化，而是让学生复述论文怎样分工推进问题。", body))


def learning_bridge() -> None:
    body: list[str] = []
    stones = [
        (130, 318, "基础课", "线代 / 普物", BLUE),
        (300, 276, "概念缺口", "领域词先落地", GREEN),
        (474, 236, "方法工具", "模型 / 实验", AMBER),
        (650, 196, "目标论文图", "会读核心图", RED),
        (824, 156, "进组问题", "能问具体问题", VIOLET),
    ]
    for i, (x, y, head, sub, fill) in enumerate(stones):
        body.append(path(f"M{x-64} {y+18} C{x-48} {y-22} {x+48} {y-30} {x+70} {y+10} C{x+48} {y+44} {x-38} {y+48} {x-64} {y+18} Z", "region", fill))
        body.append(text(x, y + 4, head, "head", "middle"))
        body.append(text(x, y + 28, sub, "small", "middle"))
        if i < len(stones) - 1:
            nx, ny = stones[i + 1][0], stones[i + 1][1]
            body.append(path(f"M{x+72} {y+8} C{x+110} {y-4} {nx-112} {ny+16} {nx-76} {ny+8}", "curve"))
    body.append(path("M96 388 C252 418 650 398 884 232", "return"))
    body.append(text(476, 414, "回看线：输出答不上就回到缺口处，不把整条路线重画成课程表", "small", "middle"))
    body.append(text(86, 112, "箭头 = 前置能力，不表示论文贡献、时间因果或资源推荐顺序。", "txt"))
    write("s4-learning-bridge.svg", svg(1080, 470, "学习桥接图", "用于 04：把学生已有课程一路接到目标论文图和进组问题。", body))


def mechanism_sketch() -> None:
    body: list[str] = []
    body.append(path("M104 242 L220 242", "line"))
    body.append(text(118, 218, "输入", "head"))
    body.append(path("M242 204 C302 168 384 174 432 228 C384 284 300 292 242 252 Z", "region", AMBER))
    body.append(text(336, 232, "样品 / 系统", "head", "middle"))
    body.append(path("M432 242 L548 242", "line"))
    body.append(circle(596, 242, 44, BLUE))
    body.append(text(596, 236, "测量", "head", "middle"))
    body.append(text(596, 260, "信号", "small", "middle"))
    body.append(path("M640 242 C700 238 748 214 800 184", "curve"))
    body.append(rect(808, 144, 130, 80, GREEN, 10))
    body.append(text(873, 178, "分析", "head", "middle"))
    body.append(text(873, 202, "输出图 / 结论", "small", "middle"))
    body.append(path("M802 306 C690 346 448 350 328 294", "return"))
    body.append(text(564, 340, "回看线：读不懂机制时，回到四个环节逐个解释", "small", "middle"))
    body.append(rect(78, 382, 920, 42, PAPER, 8))
    body.append(text(104, 409, "限制：只有证据支持流转关系时才画机制；如果只是名词相邻，改成概念图或候选关系。", "txt"))
    write("s4-mechanism-sketch.svg", svg(1080, 470, "机制示意图", "用于 03/04：让学生看懂平台、实验或计算链条怎样从输入走到输出。", body))


def evidence_uncertainty() -> None:
    body: list[str] = []
    cards = [
        (78, ROSE, "弱线索", "可支撑：补查方向", "不能支撑：定位、中心、主线", "下一步：回 S1 找直接来源"),
        (388, AMBER, "交叉证据", "可支撑：粗阅读位置", "不能支撑：精确距离、因果", "下一步：标出仍需复核处"),
        (698, GREEN, "直接证据", "可支撑：明确判断", "不能支撑：超出原文的机制", "下一步：写进正文并保留来源"),
    ]
    for x, fill, head, support, limit, action in cards:
        body.append(rect(x, 126, 260, 174, fill, 10))
        body.append(text(x + 130, 164, head, "head", "middle"))
        body.append(path(f"M{x + 26} 184 L{x + 234} 184", "soft"))
        body.append(text(x + 24, 216, support, "txt"))
        body.append(text(x + 24, 248, limit, "txt"))
        body.append(text(x + 24, 280, action, "txt"))
    body.append(rect(78, 326, 880, 82, PAPER, 8))
    body.append(text(104, 358, "读法：三张卡不是升级流程。先看当前判断落在哪张卡，再看它能支撑什么、不能支撑什么、下一步复核什么。", "txt"))
    body.append(text(104, 388, "禁止：不用箭头、面积、颜色深浅或线粗暗示可信度自动变强。", "small"))
    write("s4-evidence-uncertainty.svg", svg(1080, 440, "证据与不确定性图", "用于所有文档：让学生看见判断强弱，而不是把弱线索画成结论。", body))


def annotated_paper_figure() -> None:
    body: list[str] = []
    body.append(rect(86, 128, 370, 238, PAPER, 10))
    body.append(text(112, 158, "目标论文图的读法草图", "head"))
    body.append(path("M130 310 L130 190 L382 190", "soft"))
    body.append(path("M142 286 C198 252 236 248 282 220 C326 194 350 204 376 224", "curve"))
    body.append(circle(284, 220, 8, RED))
    body.append(circle(368, 224, 8, VIOLET))
    body.append(text(122, 184, "信号", "small", "middle"))
    body.append(text(392, 194, "条件", "small"))
    for cx, cy, label, fill in [(172, 274, "1", BLUE), (284, 220, "2", AMBER), (368, 224, "3", GREEN)]:
        body.append(circle(cx, cy - 28, 12, fill))
        body.append(text(cx, cy - 24, label, "small", "middle"))

    body.append(rect(514, 130, 360, 74, BLUE, 12))
    body.append(circle(548, 164, 13, PAPER))
    body.append(text(548, 168, "1", "small", "middle"))
    body.append(text(694, 160, "1. 先看对象和测量量", "head", "middle"))
    body.append(text(694, 184, "这张图到底测了什么，不先读结论。", "small", "middle"))

    body.append(rect(552, 228, 360, 74, AMBER, 12))
    body.append(circle(586, 262, 13, PAPER))
    body.append(text(586, 266, "2", "small", "middle"))
    body.append(text(732, 258, "2. 再看信号变化", "head", "middle"))
    body.append(text(732, 282, "峰、斜率、颜色或面板差异各表示什么。", "small", "middle"))

    body.append(rect(514, 326, 360, 74, GREEN, 12))
    body.append(circle(548, 360, 13, PAPER))
    body.append(text(548, 364, "3", "small", "middle"))
    body.append(text(694, 356, "3. 最后接到论文结论", "head", "middle"))
    body.append(text(694, 380, "哪些结论由图支持，哪些还要回正文。", "small", "middle"))

    body.append(rect(514, 418, 360, 56, PAPER, 8))
    body.append(text(538, 444, "图例：编号 = 学生读图顺序；淡色框 = 本文读法；原图信息和来源另列。", "small"))
    body.append(text(88, 508, "限制：标注图只教读法。原图信息、本文解释和学生读图顺序要分清；引用真实论文图时必须保留来源边界。", "txt"))
    write("s4-annotated-paper-figure.svg", svg(1080, 560, "目标论文核心图标注", "用于 03/04：把论文图拆成学生能按顺序阅读和复述的关系。", body))


def comparison_diagram() -> None:
    body: list[str] = []
    body.append(text(208, 128, "有真实交集", "head", "middle"))
    body.append(ellipse(164, 222, 96, 64, BLUE))
    body.append(ellipse(254, 222, 96, 64, GREEN))
    body.append(text(132, 224, "方向A", "small", "middle"))
    body.append(text(286, 224, "方向B", "small", "middle"))
    body.append(text(208, 224, "共同问题", "head", "middle"))
    body.append(text(208, 312, "只有确有交集才画 Venn", "small", "middle"))

    body.append(text(540, 128, "两个连续维度", "head", "middle"))
    body.append(path("M408 300 L408 174 L672 174", "soft"))
    body.append(text(398, 166, "对象相近", "small", "middle"))
    body.append(text(678, 178, "方法相近", "small"))
    for cx, cy, label, fill in [(478, 248, "P1", BLUE), (574, 210, "P2", AMBER), (632, 264, "P3", RED)]:
        body.append(circle(cx, cy, 16, fill))
        body.append(text(cx, cy + 5, label, "small", "middle"))
    body.append(text(540, 330, "维度必须写出来，点位不能凭感觉", "small", "middle"))

    body.append(text(872, 128, "并列剖面对照", "head", "middle"))
    body.append(path("M780 178 C820 146 884 146 924 178 C884 210 820 210 780 178 Z", "region", BLUE))
    body.append(path("M780 268 C820 236 884 236 924 268 C884 300 820 300 780 268 Z", "region", GREEN))
    body.append(text(852, 182, "方法 A", "head", "middle"))
    body.append(text(852, 272, "方法 B", "head", "middle"))
    body.append(path("M946 178 L996 178", "line"))
    body.append(path("M946 268 L996 268", "line"))
    body.append(text(1010, 181, "同一维度比较", "small"))
    body.append(text(872, 350, "比较图服务边界，不服务装饰", "small", "middle"))

    body.append(rect(104, 398, 872, 44, PAPER, 8))
    body.append(text(128, 426, "限制：没有真实交集不画 Venn；没有连续维度不画坐标；只是字段对照时保留 Markdown 表格。", "txt"))
    write("s4-comparison-diagram.svg", svg(1080, 490, "相邻方向比较图", "用于 02/03：把差异、交集和比较维度画清楚。", body))


def main() -> None:
    vocabulary()
    field_map()
    paper_role_map()
    learning_bridge()
    mechanism_sketch()
    evidence_uncertainty()
    annotated_paper_figure()
    comparison_diagram()


if __name__ == "__main__":
    main()
