from __future__ import annotations

import csv
import math
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "output" / "final-materials-v3"
OUT = OUT_ROOT / "2026-06-08"
PDF_DIR = OUT / "pdf-print"
PNG_DIR = OUT / "png-preview"
BOARD_DIR = OUT / "boards"
ZIP_PATH = OUT_ROOT / "zhenjiade-ya-final-materials-v3-2026-06-08.zip"

FONT_REG = "C:/Windows/Fonts/Deng.ttf"
FONT_BOLD = "C:/Windows/Fonts/Dengb.ttf"

INK = "#5B3A24"
MUTED = "#8B6748"
CREAM = "#FFF3D4"
WHITE = "#FFFFFF"
GOLD = "#F0B84B"
CORAL = "#E96945"
RED = "#C94D36"
GREEN = "#56A86A"
MINT = "#DDF2D9"
BLUE = "#5D91C9"
SKY = "#D8EDF9"
YELLOW = "#FFD44A"


THEMES = {
    "stage": {"name": "活动主视觉", "bg": "#FFF0C9", "accent": CORAL, "soft": "#FFE4C7", "alt": GREEN},
    "a": {"name": "A区手机门诊", "bg": "#EAF6DA", "accent": GREEN, "soft": "#FFF0C9", "alt": GOLD},
    "b": {"name": "B区校园互动", "bg": "#E5F3FA", "accent": BLUE, "soft": "#FFE8D8", "alt": CORAL},
    "c": {"name": "C区扫码闯关", "bg": "#FFF0C9", "accent": CORAL, "soft": "#E8F6D9", "alt": GREEN},
    "safety": {"name": "执行安全", "bg": "#FFF4DF", "accent": RED, "soft": "#FFE5DD", "alt": BLUE},
    "gift": {"name": "礼品延展", "bg": "#FFF2CF", "accent": GOLD, "soft": "#FFE0D0", "alt": CORAL},
    "risk": {"name": "案例风险", "bg": "#F0F7DE", "accent": BLUE, "soft": "#FFE6D5", "alt": CORAL},
}


@dataclass
class Artwork:
    slug: str
    title: str
    w: float
    h: float
    spec: str
    category: str
    theme: str
    quantity: str
    material: str
    usage: str
    note: str
    qr: str = "否"
    info: str = "是"
    proof: str = "必须小样"


CASE_TOPICS = [
    ("养老投资陷阱", "高收益、保本、熟人介绍", "先问资质，再问家人"),
    ("冒充客服退款", "索要验证码、让你下载会议 App", "官方渠道核实"),
    ("虚假理财/杀猪盘", "天天盈利、催你加仓", "不向陌生账户转账"),
    ("冒充公检法", "安全账户、保密办案", "公检法没有安全账户"),
    ("刷单返利", "先垫付、再返利", "兼职先交钱就是风险"),
    ("屏幕共享/钓鱼链接", "看你手机、发陌生链接", "立即停止共享并留证"),
]


ARTWORKS: list[Artwork] = [
    Artwork("main-stage-backdrop-5000x3000", "主背景板", 5000, 3000, "5000mm x 3000mm，PDF 1:10 核版", "主会场", "stage", "1套", "高清喷绘布/黑底布，哑面，四周打扣", "上午主舞台", "按实际桁架净尺寸核对，PDF 1:10 放大输出"),
    Artwork("entrance-banner-8000x700", "入口横幅", 8000, 700, "8000mm x 700mm，PDF 1:10 核版", "主会场", "stage", "1-2条", "横幅布或刀刮布，穿绳/打扣", "入口/主通道/舞台侧", "远距离优先看清活动主题"),
    Artwork("entrance-wayfinding-800x2000", "总导视牌", 800, 2000, "800mm x 2000mm", "导视", "stage", "1个", "易拉宝或KT板覆膜加支架", "入口总导视", "按现场实际方向调整箭头"),
    Artwork("zone-a-standee-800x2000", "A区 防骗驿站", 800, 2000, "800mm x 2000mm", "A区", "a", "1个", "易拉宝或KT板覆膜加支架", "A区入口", "适老阅读，大字清楚，避免被桌椅遮挡"),
    Artwork("zone-b-standee-800x2000", "B区 青春盾牌", 800, 2000, "800mm x 2000mm", "B区", "b", "1个", "易拉宝或KT板覆膜加支架", "B区入口", "保留拍照站位，适合学生互动"),
    Artwork("zone-c-standee-800x2000", "C区 真的假的鸭", 800, 2000, "800mm x 2000mm", "C区", "c", "1-2个", "易拉宝或KT板覆膜加支架", "C区入口/排队口", "真实小程序码替换后必须真机测试", "是"),
    Artwork("direction-sign-a-a3-landscape", "A区方向牌", 420, 297, "A3 横版", "导视", "a", "2-4张", "A3覆膜裱KT板", "通道节点", "可复制多张并调整箭头方向", "否", "否", "批量校对"),
    Artwork("direction-sign-b-a3-landscape", "B区方向牌", 420, 297, "A3 横版", "导视", "b", "2-4张", "A3覆膜裱KT板", "通道节点", "可复制多张并调整箭头方向", "否", "否", "批量校对"),
    Artwork("direction-sign-c-a3-landscape", "C区方向牌", 420, 297, "A3 横版", "导视", "c", "3-6张", "A3覆膜裱KT板", "通往C区路线", "C区建议多放，降低问路和排队成本", "否", "否", "批量校对"),
]

for i in range(1, 7):
    ARTWORKS.append(Artwork(f"case-board-{i:02d}-600x900", f"案例展板 {i:02d}", 600, 900, "600mm x 900mm KT板", "案例展板", "risk", "1块", "KT板覆哑膜", "主会场侧边/通道", "六块展板统一高度摆放", "否", "否", "批量校对"))

ARTWORKS += [
    Artwork("c-zone-task-card-a5", "C区闯关任务卡", 148, 210, "A5", "C区", "c", "100-300张", "250g铜版纸，哑膜，可双面", "C区桌面/排队发放", "章位需和实际印章直径匹配，先试盖"),
    Artwork("a-zone-formula-card-a6", "防骗口诀卡", 105, 148, "A6", "A区", "a", "200-500张", "250g铜版纸或书写卡纸", "A区带走资料", "老人带走使用，纸张不要过薄", "否", "是", "批量校对"),
    Artwork("b-zone-question-card-a6", "青春快问快答题卡", 105, 148, "A6", "B区", "b", "100-200张", "250g铜版纸或书写卡纸", "B区互动桌", "可按题库继续追加不同题面", "否", "是", "批量校对"),
    Artwork("volunteer-handcard-a6", "志愿者安全手卡", 105, 148, "A6", "执行安全", "safety", "30-60张", "300g卡纸，圆角可选", "志愿者/工作人员", "重点核对隐私边界话术"),
    Artwork("redemption-coupon-a6", "盖章领奖券", 105, 148, "A6", "C区", "c", "100-300张", "250g铜版纸或书写卡纸", "C区领奖核销", "与礼品数量匹配，可加流水编号"),
    Artwork("privacy-desk-sign-a4", "隐私安全桌牌", 210, 297, "A4", "执行安全", "safety", "2-4个", "A4台卡/亚克力台牌内芯", "A区协助台/C区扫码协助点", "提醒不代输密码、不拍屏幕"),
    Artwork("checkin-table-sign-a4", "签到台桌牌", 210, 297, "A4", "现场执行", "stage", "1-2个", "A4台卡/亚克力台牌内芯", "签到台/入口接待", "按现场签到方式补充二维码或签到表"),
    Artwork("gift-redemption-table-sign-a4", "礼品兑换桌牌", 210, 297, "A4", "现场执行", "c", "1-2个", "A4台卡/亚克力台牌内芯", "礼品兑换台", "与礼品数量、领奖规则和核销章一致"),
    Artwork("queue-guide-sign-a4", "排队提示牌", 210, 297, "A4", "现场执行", "c", "2-4个", "A4台卡或KT板覆膜", "C区排队口/等候区", "队尾和扫码桌前各放一个", "否", "否", "批量校对"),
    Artwork("fallback-paper-quiz-a4", "纸质兜底答题卡", 210, 297, "A4", "C区", "c", "50-100张", "80g-120g书写纸", "网络异常/排队超10人时启用", "必须可手写答案和人工核销"),
    Artwork("miniprogram-score-page-board-a4", "小程序成绩页交付板", 210, 297, "A4", "小程序交付", "c", "1-2张", "A4铜版纸/KT板覆膜", "C区工作人员培训/扫码桌", "确认成绩页字段和视觉"),
    Artwork("score-verification-guide-a4", "成绩页核销说明", 210, 297, "A4", "C区", "c", "1-2个", "A4台卡/亚克力台牌内芯", "C区核销盖章处", "工作人员按此核对，不记录隐私"),
    Artwork("host-cue-card-a5", "主持手卡", 148, 210, "A5", "主持执行", "safety", "3-5张", "250g卡纸，圆角可选", "主持人/讲演人员手边", "只保留短句和转场提示"),
    Artwork("video-consent-sign-a4", "短视频拍摄授权提示", 210, 297, "A4", "B区", "b", "1-2个", "A4台卡/KT板覆膜", "B区短视频拍摄点", "提示自愿拍摄和肖像授权边界"),
    Artwork("staff-briefing-board-a3", "工作人员总提示", 420, 297, "A3 横版", "执行安全", "safety", "1-2张", "A3横版KT板覆膜或培训讲义", "工作人员集合处/后台", "活动前5分钟复核用"),
    Artwork("qr-replacement-checklist-a4", "二维码替换清单", 210, 297, "A4", "印前交接", "risk", "1张", "A4普通纸或随包电子版", "广告公司核版/执行方验收", "内部清单，不作为对外物料", "是"),
    Artwork("handheld-signs-a3", "手举牌合集", 420, 297, "A3", "互动传播", "b", "2-4套", "A3覆膜裱KT板，裁切后加手柄", "B区互动/拍照点/主持问答", "裁切成独立手举牌，手柄固定要牢", "否", "否", "批量校对"),
    Artwork("photo-frame-600x900", "拍照框", 600, 900, "600mm x 900mm 异形参考", "互动传播", "b", "1个", "PVC板或KT板覆膜，异形裁切", "B/C区拍照点", "中央留空裁切，边框强度要足够"),
    Artwork("gift-sticker-sheet-a5", "礼品贴纸版", 148, 210, "A5", "礼品", "gift", "100-300张", "A5不干胶，哑膜，异形刀模可选", "礼品区/闯关奖励", "刀模线由供应商另出确认稿"),
    Artwork("merch-print-sheet-a3", "礼品印刷母版", 420, 297, "A3", "礼品", "gift", "1套母版", "A3核版稿，不直接批量印刷", "礼品供应商沟通", "供应商按不同礼品工艺拆版"),
    Artwork("activity-poster-a2", "A2活动海报", 420, 594, "A2", "宣传招募", "stage", "20-50张", "157g-200g铜版纸覆哑膜", "社区公告栏/校园张贴", "替换日期地点二维码和参与口径", "是"),
    Artwork("c-zone-qr-table-sign-a4", "C区扫码桌牌", 210, 297, "A4", "C区", "c", "2-4个", "A4台卡/亚克力台牌内芯", "C区扫码桌面", "二维码必须真机测试，桌面和队尾各放一个", "是"),
    Artwork("a-zone-phone-table-sign-a4", "手机安全门诊", 210, 297, "A4", "A区", "a", "1-2个", "A4台卡/亚克力台牌内芯", "手机安全门诊桌", "适老字号，桌面避免反光", "否", "是", "批量校对"),
    Artwork("a-zone-bank-table-sign-a4", "银行咨询台", 210, 297, "A4", "A区", "a", "1-2个", "A4台卡/亚克力台牌内芯", "银行咨询台", "按实际银行/协同单位改桌牌名称", "否", "是", "批量校对"),
    Artwork("stamp-design-sheet-a4", "印章图样", 210, 297, "A4", "C区", "c", "1套", "35-45mm光敏章/回墨章确认稿", "C区盖章核销", "印章需另出单色章稿，先试盖任务卡"),
    Artwork("volunteer-badge-90x120", "志愿者胸牌", 90, 120, "90mm x 120mm", "执行安全", "safety", "30-60个", "胸牌内芯，PVC证件卡套+挂绳", "工作人员/志愿者", "可留姓名手写区，不放私人手机号"),
    Artwork("gift-fan-print-420x210", "广告扇印刷稿", 420, 210, "420mm x 210mm 扇面参考", "礼品", "gift", "200-500把", "PP/PVC扇面，单面或双面印刷", "礼品区/老人带走", "扇柄位置由供应商套刀模"),
    Artwork("gift-tote-print-a4", "帆布袋印刷稿", 210, 297, "A4 图案区", "礼品", "gift", "50-150个", "帆布袋丝印/热转印", "礼品区/工作人员物料袋", "大货前确认布色、色差和居中"),
    Artwork("gift-notebook-cover-a5", "笔记本封面", 148, 210, "A5", "礼品", "gift", "100-300本", "A5笔记本封面，250g铜版纸", "礼品区/学生奖品", "内页按预算选择"),
    Artwork("gift-tissue-box-sleeve-240x120", "纸巾盒套", 240, 120, "240mm x 120mm 展开参考", "礼品", "gift", "100-300个", "纸巾盒套展开稿", "礼品区/社区带走", "需按实际纸巾盒重新确认刀模"),
    Artwork("gift-phone-stand-card-a6", "手机支架卡面", 105, 148, "A6", "礼品", "gift", "100-300个", "手机支架包装卡/卡面", "礼品区/学生奖品", "如供应商有固定刀模，应套入模板"),
    Artwork("gift-keychain-round-sheet-a5", "钥匙扣圆牌", 148, 210, "A5 圆牌拼版", "礼品", "gift", "100-300个", "60mm亚克力钥匙扣/徽章拼版", "礼品区/闯关奖励", "确认吊孔位置，避开小鸭脸部", "否", "否"),
]


def ensure_dirs():
    if OUT.exists():
        shutil.rmtree(OUT)
    for p in (PDF_DIR, PNG_DIR, BOARD_DIR):
        p.mkdir(parents=True, exist_ok=True)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, max(8, int(size)))


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def mix(c1: str, c2: str, t: float):
    a = hex_to_rgb(c1)
    b = hex_to_rgb(c2)
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


class Canvas:
    def __init__(self, art: Artwork, dpi: int = 300):
        self.art = art
        self.scale = 0.1 if max(art.w, art.h) > 1200 else 1.0
        self.page_w = art.w * self.scale
        self.page_h = art.h * self.scale
        self.ppmm = dpi / 25.4
        self.wpx = max(64, int(round(self.page_w * self.ppmm)))
        self.hpx = max(64, int(round(self.page_h * self.ppmm)))
        self.img = Image.new("RGB", (self.wpx, self.hpx), WHITE)
        self.draw = ImageDraw.Draw(self.img)
        self.boxes: list[tuple[int, int, int, int, str]] = []

    def xy(self, x: float, y: float):
        return int(round(x * self.scale * self.ppmm)), int(round(y * self.scale * self.ppmm))

    def wh(self, w: float, h: float):
        return max(1, int(round(w * self.scale * self.ppmm))), max(1, int(round(h * self.scale * self.ppmm)))

    def font_px(self, mm_size: float, bold: bool = False):
        return font(mm_size * self.scale * self.ppmm, bold)

    def rect(self, x, y, w, h, fill, outline=None, radius=0, width=1, tag="shape"):
        x0, y0 = self.xy(x, y)
        ww, hh = self.wh(w, h)
        width_px = max(1, int(round(width * self.scale * self.ppmm)))
        if radius:
            self.draw.rounded_rectangle((x0, y0, x0 + ww, y0 + hh), radius=max(1, int(radius * self.scale * self.ppmm)), fill=fill, outline=outline, width=width_px)
        else:
            self.draw.rectangle((x0, y0, x0 + ww, y0 + hh), fill=fill, outline=outline, width=width_px)
        self.boxes.append((x0, y0, x0 + ww, y0 + hh, tag))

    def ellipse(self, x, y, w, h, fill, outline=None, width=1, tag="shape"):
        x0, y0 = self.xy(x, y)
        ww, hh = self.wh(w, h)
        self.draw.ellipse((x0, y0, x0 + ww, y0 + hh), fill=fill, outline=outline, width=max(1, int(width * self.scale * self.ppmm)))
        self.boxes.append((x0, y0, x0 + ww, y0 + hh, tag))

    def line(self, x1, y1, x2, y2, fill, width=1):
        self.draw.line((*self.xy(x1, y1), *self.xy(x2, y2)), fill=fill, width=max(1, int(width * self.scale * self.ppmm)))

    def text(self, x, y, text, size, fill=INK, bold=False, anchor="lt", max_w=None, leading=1.18, tag="text"):
        f = self.font_px(size, bold)
        if max_w:
            lines = self.wrap(text, f, max_w)
        else:
            lines = str(text).split("\n")
        line_h = int(size * self.scale * self.ppmm * leading)
        total_h = max(1, len(lines)) * line_h
        px, py = self.xy(x, y)
        widths = [int(self.draw.textlength(line, font=f)) for line in lines] or [0]
        max_line_w = max(widths)
        if "m" in anchor:
            px -= max_line_w // 2
        if anchor.endswith("c"):
            py -= total_h // 2
        elif anchor.endswith("b"):
            py -= total_h
        cur_y = py
        for line, line_w in zip(lines, widths):
            tx = px
            if "m" in anchor:
                tx = px + (max_line_w - line_w) // 2
            self.draw.text((tx, cur_y), line, font=f, fill=fill)
            cur_y += line_h
        self.boxes.append((px, py, px + max_line_w, py + total_h, tag))
        return (cur_y - py) / (self.scale * self.ppmm)

    def wrap(self, text: str, f, max_w_mm: float):
        max_px = max_w_mm * self.scale * self.ppmm
        lines: list[str] = []
        for part in str(text).split("\n"):
            current = ""
            for ch in part:
                candidate = current + ch
                if self.draw.textlength(candidate, font=f) <= max_px:
                    current = candidate
                else:
                    if current:
                        lines.append(current)
                    current = ch
            if current:
                lines.append(current)
        return lines or [""]

    def save_png_preview(self, path: Path, max_dim=2200):
        img = self.img
        if max(img.size) > max_dim:
            img = img.copy()
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        img.save(path, "PNG", optimize=True)

    def save_pdf(self, path: Path):
        c = pdf_canvas.Canvas(str(path), pagesize=(self.page_w * mm, self.page_h * mm))
        c.drawImage(ImageReader(self.img), 0, 0, self.page_w * mm, self.page_h * mm)
        c.save()


def draw_background(cv: Canvas):
    art = cv.art
    t = THEMES[art.theme]
    for i in range(cv.hpx):
        ratio = i / max(1, cv.hpx - 1)
        color = mix(t["bg"], WHITE, ratio * 0.45)
        cv.draw.line((0, i, cv.wpx, i), fill=color)
    cv.ellipse(art.w * 0.72, -art.h * 0.12, art.w * 0.42, art.w * 0.42, "#FFE2A4", None, tag="decor")
    cv.ellipse(-art.w * 0.18, art.h * 0.72, art.w * 0.38, art.w * 0.38, t["soft"], None, tag="decor")
    for r in (0.16, 0.20, 0.24):
        cv.line(art.w * 0.42, art.h * 0.12, art.w * (0.42 + r), art.h * 0.02, GOLD, 0.8)
    safe = max(art.w, art.h) * 0.004
    cv.rect(safe, safe, art.w - safe * 2, art.h - safe * 2, None, GOLD, radius=0, width=max(0.4, safe * 0.18), tag="trim")


def draw_duck(cv: Canvas, x, y, s, pose="host", prop="none"):
    cv.ellipse(x + s * 0.18, y + s * 0.70, s * 0.66, s * 0.14, "#D6A34B", None, tag="duck-shadow")
    cv.ellipse(x + s * 0.18, y + s * 0.35, s * 0.64, s * 0.58, YELLOW, None, tag="duck")
    cv.ellipse(x + s * 0.22, y + s * 0.08, s * 0.56, s * 0.52, YELLOW, None, tag="duck")
    cv.ellipse(x + s * 0.33, y + s * 0.12, s * 0.12, s * 0.08, "#FFE889", None, tag="duck")
    cv.ellipse(x + s * 0.22, y + s * 0.22, s * 0.12, s * 0.07, "#FFAD84", None, tag="duck")
    cv.ellipse(x + s * 0.66, y + s * 0.22, s * 0.12, s * 0.07, "#FFAD84", None, tag="duck")
    cv.ellipse(x + s * 0.32, y + s * 0.27, s * 0.07, s * 0.07, "#3B2415", None, tag="duck")
    cv.ellipse(x + s * 0.61, y + s * 0.27, s * 0.07, s * 0.07, "#3B2415", None, tag="duck")
    cv.ellipse(x + s * 0.345, y + s * 0.28, s * 0.022, s * 0.022, WHITE, None, tag="duck")
    cv.ellipse(x + s * 0.635, y + s * 0.28, s * 0.022, s * 0.022, WHITE, None, tag="duck")
    cv.ellipse(x + s * 0.34, y + s * 0.39, s * 0.32, s * 0.13, "#F59E2E", None, tag="duck")
    cv.ellipse(x + s * 0.40, y + s * 0.43, s * 0.20, s * 0.12, "#B84B26", None, tag="duck")
    cv.rect(x + s * 0.28, y + s * 0.54, s * 0.44, s * 0.28, CORAL, None, radius=s * 0.04, tag="duck-vest")
    cv.line(x + s * 0.50, y + s * 0.55, x + s * 0.50, y + s * 0.82, "#FFE0BF", width=s * 0.01)
    cv.ellipse(x + s * 0.58, y + s * 0.63, s * 0.10, s * 0.10, "#FFE6A4", RED, width=s * 0.008, tag="duck-badge")
    cv.line(x + s * 0.60, y + s * 0.68, x + s * 0.66, y + s * 0.64, RED, width=s * 0.006)
    cv.line(x + s * 0.60, y + s * 0.68, x + s * 0.66, y + s * 0.72, RED, width=s * 0.006)
    cv.ellipse(x + s * 0.19, y + s * 0.86, s * 0.20, s * 0.08, "#E98C2C", None, tag="duck")
    cv.ellipse(x + s * 0.61, y + s * 0.86, s * 0.20, s * 0.08, "#E98C2C", None, tag="duck")
    if prop == "phone":
        cv.rect(x + s * 0.66, y + s * 0.44, s * 0.22, s * 0.36, "#2C3E50", None, radius=s * 0.03, tag="prop")
        cv.rect(x + s * 0.685, y + s * 0.48, s * 0.17, s * 0.26, WHITE, None, radius=s * 0.015, tag="prop")
        for i, color in enumerate((GREEN, BLUE, GOLD)):
            cv.ellipse(x + s * 0.71, y + s * (0.51 + i * 0.07), s * 0.04, s * 0.04, color, None, tag="prop")
    elif prop == "task":
        cv.rect(x + s * 0.62, y + s * 0.44, s * 0.28, s * 0.28, WHITE, GOLD, radius=s * 0.025, width=s * 0.006, tag="prop")
        for i, color in enumerate((GREEN, CORAL, GOLD)):
            cv.ellipse(x + s * (0.66 + i * 0.07), y + s * 0.51, s * 0.045, s * 0.045, color, None, tag="prop")
    elif prop == "fan":
        cv.ellipse(x + s * 0.60, y + s * 0.38, s * 0.32, s * 0.24, "#FFF2CC", GOLD, width=s * 0.01, tag="prop")
        cv.text(x + s * 0.76, y + s * 0.52, "真", s * 0.07, GREEN, True, "mc")
    elif prop == "stamp":
        cv.ellipse(x + s * 0.62, y + s * 0.50, s * 0.18, s * 0.18, "#F1D29D", RED, width=s * 0.008, tag="prop")
        cv.rect(x + s * 0.66, y + s * 0.36, s * 0.10, s * 0.16, "#B95E38", None, radius=s * 0.025, tag="prop")


def draw_label_pill(cv: Canvas, x, y, w, h, text, fill, color=WHITE):
    cv.rect(x, y, w, h, fill, None, radius=h / 2, tag="pill")
    cv.text(x + w / 2, y + h * 0.56, text, h * 0.34, color, True, "mc")


def draw_soft_card(cv: Canvas, x, y, w, h, fill=WHITE, outline=GOLD, radius=None, width=1.2, shadow=True, tag="card"):
    radius = h * 0.08 if radius is None else radius
    if shadow:
        cv.rect(x + w * 0.018, y + h * 0.025, w, h, "#E7C98A", None, radius=radius, tag=f"{tag}-shadow")
    cv.rect(x, y, w, h, fill, outline, radius=radius, width=width, tag=tag)


def draw_mascot_mark(cv: Canvas, cx, cy, r, color=CORAL):
    cv.ellipse(cx - r, cy - r, r * 2, r * 2, "#FFF4D5", color, width=r * 0.07, tag="mark")
    cv.ellipse(cx - r * 0.40, cy - r * 0.25, r * 0.18, r * 0.18, color, None, tag="mark")
    cv.ellipse(cx + r * 0.22, cy - r * 0.25, r * 0.18, r * 0.18, color, None, tag="mark")
    cv.ellipse(cx - r * 0.30, cy + r * 0.06, r * 0.60, r * 0.24, color, None, tag="mark")
    cv.line(cx - r * 0.40, cy + r * 0.60, cx + r * 0.40, cy + r * 0.60, color, width=r * 0.05)


def draw_book_light(cv: Canvas, cx, cy, w, color=GOLD):
    cv.ellipse(cx - w * 0.10, cy - w * 0.06, w * 0.20, w * 0.16, "#FFD56B", None, tag="book-light")
    cv.rect(cx - w * 0.30, cy + w * 0.02, w * 0.60, w * 0.11, "#FFF8E6", color, radius=w * 0.035, width=w * 0.006, tag="book")
    for i in range(4):
        offset = (i - 1.5) * w * 0.10
        cv.line(cx, cy + w * 0.03, cx + offset, cy + w * 0.14, color, width=w * 0.004)
    for i in range(5):
        cv.line(cx, cy - w * 0.06, cx + (i - 2) * w * 0.11, cy - w * 0.22, color, width=w * 0.004)


def draw_cut_line(cv: Canvas, x1, y1, x2, y2, color=CORAL, width=1.0, segments=24):
    for i in range(segments):
        if i % 2 == 0:
            a = i / segments
            b = (i + 1) / segments
            cv.line(x1 + (x2 - x1) * a, y1 + (y2 - y1) * a, x1 + (x2 - x1) * b, y1 + (y2 - y1) * b, color, width=width)


def draw_stamp_slot(cv: Canvas, cx, cy, r, label, color=GOLD, filled=False):
    fill = "#FFF8E8" if not filled else "#FFE9D6"
    cv.ellipse(cx - r, cy - r, r * 2, r * 2, fill, color, width=r * 0.06, tag="stamp-slot")
    cv.ellipse(cx - r * 0.78, cy - r * 0.78, r * 1.56, r * 1.56, None, color, width=r * 0.025, tag="stamp-dash")
    cv.text(cx, cy - r * 0.98, str(label), r * 0.46, WHITE, True, "mc")
    cv.ellipse(cx - r * 0.36, cy - r * 1.31, r * 0.72, r * 0.72, color, None, tag="stamp-num")
    cv.text(cx, cy - r * 0.94, str(label), r * 0.42, WHITE, True, "mc")
    if filled:
        draw_mascot_mark(cv, cx, cy + r * 0.08, r * 0.44, CORAL)
    else:
        cv.text(cx, cy + r * 0.16, "盖章", r * 0.34, MUTED, False, "mc")


def draw_qr(cv: Canvas, x, y, size, label="二维码占位"):
    cv.rect(x, y, size, size, WHITE, BLUE, radius=size * 0.06, width=size * 0.018, tag="qr")
    cell = size / 9
    for i in range(9):
        for j in range(9):
            if (i * j + i + j) % 3 == 0 or (i in (1, 7) and j in (1, 7)):
                cv.rect(x + i * cell + cell * 0.18, y + j * cell + cell * 0.18, cell * 0.62, cell * 0.62, INK, None, tag="qr")
    cv.text(x + size / 2, y + size + size * 0.13, label, size * 0.08, MUTED, False, "mc")


def draw_footer(cv: Canvas):
    art = cv.art
    scale_note = "PDF为1:10核版，输出放大1000%" if cv.scale < 1 else "按文件尺寸输出"
    cv.text(art.w / 2, art.h - max(art.h * 0.035, 8), f"{scale_note}  |  {art.spec}  |  正式印前需转CMYK、打样确认", max(min(art.w, art.h) * 0.018, 5), MUTED, False, "mc", max_w=art.w * 0.9)


def draw_title_block(cv: Canvas, title, subtitle=None, top_ratio=0.10):
    art = cv.art
    t = THEMES[art.theme]
    size = min(art.w * 0.085, art.h * 0.105, 150)
    cv.text(art.w / 2, art.h * top_ratio, title, size, RED, True, "mc", max_w=art.w * 0.82)
    if subtitle:
        pill_w = min(art.w * 0.56, len(subtitle) * size * 0.42)
        draw_label_pill(cv, art.w / 2 - pill_w / 2, art.h * top_ratio + size * 0.58, pill_w, size * 0.42, subtitle, t["accent"])


def render_main_stage(cv: Canvas):
    art = cv.art
    draw_title_block(cv, "守护钱袋子", "金融防骗反诈公益日", 0.11)
    cv.text(art.w / 2, art.h * 0.31, "学知识 · 辨真伪 · 护自己 · 帮他人", art.h * 0.062, INK, True, "mc")
    draw_duck(cv, art.w * 0.08, art.h * 0.38, art.h * 0.40, "host", "task")
    steps = [("1", "微课堂"), ("2", "情景剧"), ("3", "互动问答"), ("4", "分区体验")]
    x0 = art.w * 0.42
    for i, (num, label) in enumerate(steps):
        cx = x0 + i * art.w * 0.125
        cv.ellipse(cx, art.h * 0.49, art.h * 0.105, art.h * 0.105, WHITE, GOLD, width=art.h * 0.006, tag="step")
        cv.text(cx + art.h * 0.052, art.h * 0.558, num, art.h * 0.045, CORAL, True, "mc")
        cv.text(cx + art.h * 0.052, art.h * 0.64, label, art.h * 0.025, INK, True, "mc")
    zones = [("A区 防骗驿站", "老人手机安全 / 防骗口诀 / 银行咨询", GREEN), ("B区 青春盾牌", "学生剧本互动 / 短视频 / 快问快答", BLUE), ("C区 真的假的鸭", "扫码闯关 / 成绩页 / 盖章领奖", CORAL)]
    for i, (z, desc, color) in enumerate(zones):
        x = art.w * (0.39 + i * 0.19)
        cv.rect(x, art.h * 0.69, art.w * 0.16, art.h * 0.14, WHITE, color, radius=art.h * 0.018, width=art.h * 0.005, tag="zone")
        cv.text(x + art.w * 0.08, art.h * 0.735, z, art.h * 0.026, color, True, "mc")
        cv.text(x + art.w * 0.08, art.h * 0.795, desc, art.h * 0.017, INK, False, "mc", max_w=art.w * 0.13)
    draw_footer(cv)


def render_banner(cv: Canvas):
    art = cv.art
    t = THEMES[art.theme]
    cv.rect(0, 0, art.w, art.h, t["accent"], None, tag="banner-bg")
    cv.ellipse(art.w * 0.03, art.h * 0.06, art.h * 0.88, art.h * 0.88, "#FFE8B8", None, tag="decor")
    draw_duck(cv, art.w * 0.055, art.h * 0.18, art.h * 0.72, "host", "fan")
    cv.text(art.w * 0.52, art.h * 0.43, "守护钱袋子  金融防骗反诈公益日", art.h * 0.22, WHITE, True, "mc")
    cv.text(art.w * 0.52, art.h * 0.70, "学知识 · 辨真伪 · 护自己 · 帮他人", art.h * 0.095, "#FFECC9", True, "mc")


def render_standee(cv: Canvas):
    art = cv.art
    t = THEMES[art.theme]
    subtitle = {
        "zone-a-standee-800x2000": "老人手机安全 / 一对一指导 / 银行咨询",
        "zone-b-standee-800x2000": "剧本互动 / 短视频 / 快问快答",
        "zone-c-standee-800x2000": "扫码进入小程序，5题闯关",
    }.get(art.slug, "守护钱袋子")
    draw_title_block(cv, art.title, subtitle, 0.09)
    prop = "phone" if art.theme == "a" else "task" if art.theme == "b" else "stamp"
    draw_duck(cv, art.w * 0.08, art.h * 0.26, art.w * 0.36, "host", prop)
    if art.theme == "c":
        draw_qr(cv, art.w * 0.56, art.h * 0.31, art.w * 0.28, "替换真实小程序码")
        draw_label_pill(cv, art.w * 0.52, art.h * 0.57, art.w * 0.34, art.h * 0.055, "扫码闯关", t["accent"])
        items = ["扫码进入", "完成5题", "查看等级", "成绩页盖章领奖"]
    elif art.theme == "a":
        items = ["手机安全一对一指导", "防骗口诀记忆挑战", "银行账户安全咨询", "不代输密码 不拍屏幕"]
    else:
        items = ["校园剧本互动", "短视频创作", "知识快问快答", "同龄人提醒同龄人"]
    for i, item in enumerate(items, 1):
        y = art.h * (0.61 + (i - 1) * 0.072)
        cv.rect(art.w * 0.13, y, art.w * 0.74, art.h * 0.050, WHITE, t["accent"], radius=art.h * 0.018, width=art.h * 0.0035, tag="item")
        cv.ellipse(art.w * 0.16, y + art.h * 0.008, art.h * 0.036, art.h * 0.036, t["accent"], None, tag="num")
        cv.text(art.w * 0.18, y + art.h * 0.036, str(i), art.h * 0.020, WHITE, True, "mc")
        cv.text(art.w * 0.25, y + art.h * 0.033, item, art.h * 0.020, INK, True, "lc", max_w=art.w * 0.58)
    draw_footer(cv)


def render_direction(cv: Canvas):
    art = cv.art
    color = THEMES[art.theme]["accent"]
    code = "A" if "-a-" in art.slug else "B" if "-b-" in art.slug else "C"
    name = "防骗驿站" if code == "A" else "青春盾牌" if code == "B" else "真的假的鸭"
    cv.ellipse(art.w * 0.08, art.h * 0.26, art.h * 0.45, art.h * 0.45, color, None, tag="code")
    cv.text(art.w * 0.24, art.h * 0.55, code, art.h * 0.20, WHITE, True, "mc")
    cv.text(art.w * 0.48, art.h * 0.45, name, art.h * 0.12, INK, True, "mc")
    cv.text(art.w * 0.48, art.h * 0.63, "请沿箭头前往", art.h * 0.055, MUTED, False, "mc")
    pts = [(art.w * 0.78, art.h * 0.37), (art.w * 0.95, art.h * 0.50), (art.w * 0.78, art.h * 0.63)]
    cv.draw.polygon([cv.xy(x, y) for x, y in pts], fill=RED)


def render_case_board(cv: Canvas, idx: int):
    art = cv.art
    title, signal, action = CASE_TOPICS[idx - 1]
    cv.text(art.w * 0.10, art.h * 0.11, f"{idx:02d}", art.h * 0.062, CORAL, True, "lt")
    cv.text(art.w * 0.27, art.h * 0.13, title, art.h * 0.050, INK, True, "lt", max_w=art.w * 0.55)
    draw_duck(cv, art.w * 0.67, art.h * 0.66, art.w * 0.22, "host", "task")
    cv.rect(art.w * 0.08, art.h * 0.25, art.w * 0.78, art.h * 0.20, WHITE, CORAL, radius=art.h * 0.015, width=art.h * 0.003, tag="case")
    cv.text(art.w * 0.12, art.h * 0.31, "骗子信号", art.h * 0.030, RED, True, "lt")
    cv.text(art.w * 0.12, art.h * 0.37, signal, art.h * 0.026, INK, False, "lt", max_w=art.w * 0.68)
    cv.rect(art.w * 0.08, art.h * 0.50, art.w * 0.78, art.h * 0.18, WHITE, GREEN, radius=art.h * 0.015, width=art.h * 0.003, tag="case")
    cv.text(art.w * 0.12, art.h * 0.56, "正确动作", art.h * 0.030, GREEN, True, "lt")
    cv.text(art.w * 0.12, art.h * 0.62, action, art.h * 0.028, INK, False, "lt", max_w=art.w * 0.68)
    cv.text(art.w * 0.50, art.h * 0.86, "停一下，再核实", art.h * 0.045, RED, True, "mc")
    draw_footer(cv)


def render_task_card(cv: Canvas):
    art = cv.art
    cv.text(art.w / 2, art.h * 0.09, "真的假的鸭 闯关任务卡", art.h * 0.065, RED, True, "mc")
    cv.text(art.w / 2, art.h * 0.17, "完成5题后，请工作人员盖章领奖", art.h * 0.030, MUTED, False, "mc")
    positions = [(0.30, 0.35), (0.70, 0.35), (0.50, 0.52), (0.30, 0.69), (0.70, 0.69)]
    for i, (rx, ry) in enumerate(positions, 1):
        cx, cy = art.w * rx, art.h * ry
        cv.ellipse(cx - art.w * 0.12, cy - art.w * 0.12, art.w * 0.24, art.w * 0.24, WHITE, GOLD, width=art.w * 0.006, tag="stamp")
        cv.text(cx, cy + art.w * 0.02, str(i), art.w * 0.09, CORAL, True, "mc")
    draw_duck(cv, art.w * 0.07, art.h * 0.73, art.w * 0.24, "host", "stamp")
    cv.text(art.w * 0.54, art.h * 0.86, "扫码 · 答题 · 盖章", art.h * 0.035, INK, True, "mc")
    cv.text(art.w / 2, art.h * 0.94, "人工核销：不收手机号，不代答题，不记录隐私", art.h * 0.024, MUTED, False, "mc")


def render_a6_card(cv: Canvas):
    art = cv.art
    lines = {
        "a-zone-formula-card-a6": ["停一下：别急着转账", "问家人：多一个人核实", "查官方：银行/公安官方渠道", "验证码：谁要都不给", "96110：来电要接"],
        "b-zone-question-card-a6": ["兼职先交钱？假", "客服索验证码？假", "96110来电？要接", "屏幕共享？立刻停", "票务交易？走官方"],
        "volunteer-handcard-a6": ["不代输密码", "不拍手机屏幕", "不询问验证码", "排队超10人切纸质卡", "遇紧急转账先叫停"],
        "redemption-coupon-a6": ["完成5题闯关", "出示成绩页", "工作人员盖章", "每人限领一份"],
        "host-cue-card-a5": ["开场：守护钱袋子", "转场：先停一下再核实", "互动：真 or 假", "收束：把口诀带回家"],
    }.get(art.slug, ["停一下", "辨真伪", "护自己", "帮他人"])
    cv.text(art.w / 2, art.h * 0.12, art.title, art.h * 0.075, RED, True, "mc", max_w=art.w * 0.84)
    draw_duck(cv, art.w * 0.60, art.h * 0.13, art.w * 0.22, "host", "fan" if art.theme == "a" else "task")
    y = art.h * 0.30
    for i, line in enumerate(lines, 1):
        cv.rect(art.w * 0.10, y, art.w * 0.80, art.h * 0.085, WHITE, THEMES[art.theme]["accent"], radius=art.h * 0.018, width=art.h * 0.003, tag="line")
        cv.ellipse(art.w * 0.13, y + art.h * 0.016, art.h * 0.052, art.h * 0.052, THEMES[art.theme]["accent"], None, tag="num")
        cv.text(art.w * 0.155, y + art.h * 0.055, str(i), art.h * 0.028, WHITE, True, "mc")
        cv.text(art.w * 0.24, y + art.h * 0.052, line, art.h * 0.029, INK, True, "lc", max_w=art.w * 0.62)
        y += art.h * 0.105


def render_table_sign(cv: Canvas):
    art = cv.art
    t = THEMES[art.theme]
    cv.text(art.w / 2, art.h * 0.12, art.title, art.h * 0.075, RED, True, "mc", max_w=art.w * 0.82)
    if art.qr == "是":
        draw_qr(cv, art.w * 0.27, art.h * 0.30, art.w * 0.46, "替换真实二维码")
    else:
        draw_duck(cv, art.w * 0.58, art.h * 0.20, art.w * 0.28, "host", "phone" if art.theme == "a" else "task")
    details = {
        "privacy-desk-sign-a4": ["工作人员不代输密码", "不拍摄手机屏幕", "不询问验证码和银行卡密码", "小程序不收集手机号", "活动全程不收费"],
        "checkin-table-sign-a4": ["请在签到台确认信息", "按A/B/C区指引参与", "有问题请找志愿者"],
        "gift-redemption-table-sign-a4": ["完成闯关", "出示成绩页或任务卡", "工作人员盖章", "每人限领一份"],
        "queue-guide-sign-a4": ["排队扫码", "完成5题", "查看等级", "凭成绩页盖章领奖"],
        "score-verification-guide-a4": ["看成绩页：已完成5题", "看等级：任一等级均可领奖", "盖章后：提醒每人限领一份"],
        "video-consent-sign-a4": ["拍摄前请先征得本人同意", "不拍身份证、银行卡、验证码", "不拍他人手机屏幕", "不愿出镜可选择手举牌"],
        "a-zone-phone-table-sign-a4": ["手机权限检查", "官方应用商店下载", "屏幕共享风险提醒"],
        "a-zone-bank-table-sign-a4": ["账户安全咨询", "银行卡与验证码保护", "异常转账先核实"],
    }.get(art.slug, ["扫码参与", "完成任务", "盖章领奖"])
    y0 = art.h * (0.58 if art.qr == "是" else 0.40)
    for i, line in enumerate(details, 1):
        y = y0 + i * art.h * 0.075
        cv.rect(art.w * 0.12, y, art.w * 0.76, art.h * 0.052, WHITE, t["accent"], radius=art.h * 0.016, width=art.h * 0.003, tag="detail")
        cv.ellipse(art.w * 0.15, y + art.h * 0.010, art.h * 0.032, art.h * 0.032, t["accent"], None, tag="num")
        cv.text(art.w * 0.166, y + art.h * 0.033, str(i), art.h * 0.018, WHITE, True, "mc")
        cv.text(art.w * 0.22, y + art.h * 0.034, line, art.h * 0.023, INK, True, "lc", max_w=art.w * 0.60)
    draw_footer(cv)


def render_quiz(cv: Canvas):
    art = cv.art
    cv.text(art.w / 2, art.h * 0.08, "真的假的鸭 纸质兜底答题卡", art.h * 0.055, RED, True, "mc")
    cv.text(art.w / 2, art.h * 0.13, "网络异常或排队较长时使用，完成后人工核销", art.h * 0.024, MUTED, False, "mc")
    qs = ["96110来电要接听吗？", "客服索要验证码给吗？", "屏幕共享要停止吗？", "陌生链接能随便点吗？", "转账前要先核实吗？"]
    y = art.h * 0.20
    for i, q in enumerate(qs, 1):
        cv.text(art.w * 0.08, y, f"{i}. {q}", art.h * 0.030, INK, True, "lt")
        cv.ellipse(art.w * 0.60, y - art.h * 0.006, art.h * 0.030, art.h * 0.030, WHITE, GREEN, width=art.h * 0.002, tag="answer")
        cv.text(art.w * 0.65, y + art.h * 0.016, "真", art.h * 0.023, GREEN, True, "lc")
        cv.ellipse(art.w * 0.78, y - art.h * 0.006, art.h * 0.030, art.h * 0.030, WHITE, CORAL, width=art.h * 0.002, tag="answer")
        cv.text(art.w * 0.83, y + art.h * 0.016, "假", art.h * 0.023, CORAL, True, "lc")
        cv.line(art.w * 0.08, y + art.h * 0.055, art.w * 0.92, y + art.h * 0.055, GOLD, width=0.4)
        y += art.h * 0.105
    cv.rect(art.w * 0.20, art.h * 0.82, art.w * 0.60, art.h * 0.075, WHITE, CORAL, radius=art.h * 0.012, width=art.h * 0.003, tag="verify")
    cv.text(art.w / 2, art.h * 0.865, "人工核销盖章处", art.h * 0.028, RED, True, "mc")
    draw_footer(cv)


def render_score(cv: Canvas):
    art = cv.art
    cv.text(art.w / 2, art.h * 0.08, "小程序成绩页", art.h * 0.060, RED, True, "mc")
    cv.rect(art.w * 0.26, art.h * 0.16, art.w * 0.48, art.h * 0.70, WHITE, GOLD, radius=art.h * 0.020, width=art.h * 0.004, tag="phone")
    cv.text(art.w / 2, art.h * 0.23, "闯关完成", art.h * 0.045, RED, True, "mc")
    cv.ellipse(art.w * 0.40, art.h * 0.28, art.w * 0.20, art.w * 0.20, "#FFE9A8", GOLD, width=art.h * 0.003, tag="score")
    cv.text(art.w / 2, art.h * 0.37, "5/5", art.h * 0.055, GREEN, True, "mc")
    draw_label_pill(cv, art.w * 0.34, art.h * 0.45, art.w * 0.32, art.h * 0.05, "反诈守护官", CORAL)
    for i in range(5):
        cv.ellipse(art.w * (0.33 + i * 0.085), art.h * 0.56, art.w * 0.06, art.w * 0.06, GREEN, None, tag="progress")
        cv.text(art.w * (0.36 + i * 0.085), art.h * 0.595, "✓", art.h * 0.027, WHITE, True, "mc")
    cv.rect(art.w * 0.32, art.h * 0.66, art.w * 0.36, art.h * 0.09, "#FFF2CC", CORAL, radius=art.h * 0.012, width=art.h * 0.003, tag="stamp-area")
    cv.text(art.w / 2, art.h * 0.715, "凭此页盖章领奖", art.h * 0.026, INK, True, "mc")
    draw_footer(cv)


def render_stamp(cv: Canvas):
    art = cv.art
    cv.text(art.w / 2, art.h * 0.09, "真的假的鸭 印章图样", art.h * 0.060, RED, True, "mc")
    labels = ["闯关达人", "人工核销", "盖章领奖", "工作人员确认"]
    for i, label in enumerate(labels):
        cx = art.w * (0.32 if i % 2 == 0 else 0.68)
        cy = art.h * (0.36 if i < 2 else 0.66)
        cv.ellipse(cx - art.w * 0.14, cy - art.w * 0.14, art.w * 0.28, art.w * 0.28, WHITE, CORAL, width=art.w * 0.006, tag="stamp")
        cv.text(cx, cy - art.w * 0.02, label, art.w * 0.055, RED, True, "mc")
        cv.text(cx, cy + art.w * 0.07, "真的假的鸭", art.w * 0.030, MUTED, False, "mc")
    cv.text(art.w / 2, art.h * 0.88, "建议实物直径 35-45mm，先试盖任务卡确认清晰度", art.h * 0.026, MUTED, False, "mc", max_w=art.w * 0.82)


def render_handheld(cv: Canvas):
    art = cv.art
    labels = [("真", GREEN), ("假", CORAL), ("停一下", GOLD), ("验证码不给", BLUE)]
    for i, (label, color) in enumerate(labels):
        x = art.w * (0.08 + (i % 2) * 0.46)
        y = art.h * (0.12 + (i // 2) * 0.40)
        cv.rect(x, y, art.w * 0.38, art.h * 0.30, color, None, radius=art.h * 0.08, tag="handheld")
        cv.text(x + art.w * 0.19, y + art.h * 0.18, label, art.h * (0.13 if len(label) <= 2 else 0.08), WHITE, True, "mc", max_w=art.w * 0.30)
    cv.text(art.w / 2, art.h * 0.94, "裁切后加手柄，适合互动问答和拍照传播", art.h * 0.035, MUTED, False, "mc")


def render_photo_frame(cv: Canvas):
    art = cv.art
    cv.text(art.w / 2, art.h * 0.10, "我完成了真的假的鸭挑战", art.h * 0.050, RED, True, "mc")
    cv.rect(art.w * 0.12, art.h * 0.20, art.w * 0.76, art.h * 0.58, None, CORAL, radius=art.h * 0.025, width=art.h * 0.010, tag="cut-window")
    cv.text(art.w / 2, art.h * 0.86, "停一下 · 辨真伪 · 守护钱袋子", art.h * 0.036, INK, True, "mc")
    draw_duck(cv, art.w * 0.70, art.h * 0.76, art.w * 0.20, "host", "task")


def render_gift(cv: Canvas):
    art = cv.art
    title = "真的假的鸭" if "gift-" in art.slug else "礼品物料母版"
    cv.text(art.w / 2, art.h * 0.13, title, art.h * 0.070, RED, True, "mc", max_w=art.w * 0.82)
    prop = "fan" if "fan" in art.slug else "phone" if "phone" in art.slug else "stamp" if "keychain" in art.slug or "sticker" in art.slug else "task"
    draw_duck(cv, art.w * 0.12, art.h * 0.28, min(art.w, art.h) * 0.36, "host", prop)
    if "fan" in art.slug:
        cv.text(art.w * 0.58, art.h * 0.34, "停一下 · 验证码不给 · 96110要接", art.h * 0.075, INK, True, "mc", max_w=art.w * 0.54)
        draw_label_pill(cv, art.w * 0.48, art.h * 0.56, art.w * 0.16, art.h * 0.10, "真", GREEN)
        draw_label_pill(cv, art.w * 0.67, art.h * 0.56, art.w * 0.16, art.h * 0.10, "假", CORAL)
    elif "keychain" in art.slug or "sticker" in art.slug:
        items = [("停一下", GOLD), ("96110", BLUE), ("真", GREEN), ("假", CORAL)]
        for i, (label, color) in enumerate(items):
            cx = art.w * (0.34 + (i % 2) * 0.33)
            cy = art.h * (0.36 + (i // 2) * 0.29)
            cv.ellipse(cx - art.w * 0.13, cy - art.w * 0.13, art.w * 0.26, art.w * 0.26, color, None, tag="gift-dot")
            cv.text(cx, cy + art.w * 0.025, label, art.w * (0.045 if len(label) > 3 else 0.075), WHITE, True, "mc")
    elif "phone-stand" in art.slug:
        draw_qr(cv, art.w * 0.32, art.h * 0.35, art.w * 0.36, "二维码占位")
        cv.text(art.w / 2, art.h * 0.80, "扫码参与闯关", art.h * 0.040, INK, True, "mc")
    else:
        cv.text(art.w * 0.62, art.h * 0.46, "守护钱袋子", art.h * 0.055, INK, True, "mc")
        cv.text(art.w * 0.62, art.h * 0.58, "停一下 · 辨真伪 · 护自己", art.h * 0.033, MUTED, False, "mc")
    draw_footer(cv)


def render_staff_board(cv: Canvas):
    art = cv.art
    cv.text(art.w / 2, art.h * 0.11, art.title, art.h * 0.070, RED, True, "mc")
    panels = [("隐私", ["不代输密码", "不拍手机屏幕"], CORAL), ("秩序", ["队尾提示", "排队超10人启用纸卡"], BLUE), ("收费", ["活动全程不收费", "发现收费立即制止"], GREEN), ("应急", ["96110/110", "保留证据"], GOLD)]
    for i, (head, lines, color) in enumerate(panels):
        x = art.w * (0.07 + (i % 4) * 0.235)
        y = art.h * 0.30
        cv.rect(x, y, art.w * 0.20, art.h * 0.42, WHITE, color, radius=art.h * 0.02, width=art.h * 0.004, tag="panel")
        cv.text(x + art.w * 0.10, y + art.h * 0.10, head, art.h * 0.045, color, True, "mc")
        cv.text(x + art.w * 0.10, y + art.h * 0.24, "\n".join(lines), art.h * 0.030, INK, False, "mc", max_w=art.w * 0.16)
    draw_footer(cv)


def render_default(cv: Canvas):
    art = cv.art
    draw_title_block(cv, art.title, "守护钱袋子", 0.12)
    draw_duck(cv, art.w * 0.12, art.h * 0.33, min(art.w, art.h) * 0.30, "host", "task")
    cv.text(art.w * 0.58, art.h * 0.45, art.note, min(art.w, art.h) * 0.045, INK, False, "mc", max_w=art.w * 0.45)
    draw_footer(cv)


def render_artwork(art: Artwork) -> Canvas:
    cv = Canvas(art)
    draw_background(cv)
    if art.slug == "main-stage-backdrop-5000x3000":
        render_main_stage(cv)
    elif art.slug == "entrance-banner-8000x700":
        render_banner(cv)
    elif art.slug.startswith("zone-") and art.slug.endswith("800x2000"):
        render_standee(cv)
    elif art.slug.startswith("direction-sign"):
        render_direction(cv)
    elif art.slug.startswith("case-board"):
        render_case_board(cv, int(art.slug.split("-")[2]))
    elif art.slug == "c-zone-task-card-a5":
        render_task_card(cv)
    elif art.slug in {"a-zone-formula-card-a6", "b-zone-question-card-a6", "volunteer-handcard-a6", "redemption-coupon-a6", "host-cue-card-a5", "volunteer-badge-90x120"}:
        render_a6_card(cv)
    elif art.slug == "fallback-paper-quiz-a4":
        render_quiz(cv)
    elif art.slug == "miniprogram-score-page-board-a4":
        render_score(cv)
    elif art.slug == "stamp-design-sheet-a4":
        render_stamp(cv)
    elif art.slug == "handheld-signs-a3":
        render_handheld(cv)
    elif art.slug == "photo-frame-600x900":
        render_photo_frame(cv)
    elif art.slug.startswith("gift-") or art.slug == "merch-print-sheet-a3":
        render_gift(cv)
    elif art.slug == "staff-briefing-board-a3":
        render_staff_board(cv)
    elif art.slug.endswith("table-sign-a4") or art.slug in {"privacy-desk-sign-a4", "queue-guide-sign-a4", "score-verification-guide-a4", "video-consent-sign-a4", "qr-replacement-checklist-a4"}:
        render_table_sign(cv)
    else:
        render_default(cv)
    return cv


def write_index():
    headers = ["文件名", "中文物料名", "规格", "类别", "主题", "建议数量", "建议材质工艺", "使用位置", "二维码替换", "信息替换", "打样优先级", "制作备注"]
    with (OUT / "material-index.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for art in ARTWORKS:
            writer.writerow([f"{art.slug}.pdf", art.title, art.spec, art.category, THEMES[art.theme]["name"], art.quantity, art.material, art.usage, art.qr, art.info, art.proof, art.note])
    rows = "\n".join(
        f"| {i:02d} | `{art.slug}.pdf` | {art.title} | {art.spec} | {THEMES[art.theme]['name']} | {art.quantity} | {art.usage} |"
        for i, art in enumerate(ARTWORKS, 1)
    )
    readme = f"""# 真的假的鸭活动物料最终设计稿包 V3

生成日期：2026-06-08

本包是重新设计后的活动物料成稿包。广告公司职责是替换真实二维码、按设备转 CMYK、字体/栅格输出检查、打样和印刷，不需要重新设计版式。

## 关键原则

- 不使用 SVG。
- 不把 12 张参考图原封不动贴进正式物料。
- 正式中文文字由本地字体绘制，不依赖 AI 图片识别中文。
- 每件物料导出为完整栅格 PDF 成稿，避免字体漂移、图层错位和软件打开后元素互相覆盖。
- 大幅面 PDF 为 1:10 核版稿，输出时按文件内说明放大。

## 目录

- `pdf-print/`：47 件可核版打印 PDF。
- `png-preview/`：47 张校对预览图。
- `boards/contact-sheet.png`：47 件物料中文总览。
- `boards/style-board.png`：风格提炼板，说明 12 张参考图如何转化成统一视觉语言。
- `material-index.csv`：规格、数量、材质、使用位置和印前提醒。

## 印前必须替换/确认

- C区小程序码、A2海报二维码、备用二维码。
- 活动日期、时间、地点、主办/协同/指导单位最终写法。
- 礼品数量、领奖规则、印章实际尺寸。
- 供应商 CMYK 转换、小样、打样签核。

## 文件清单

| 序号 | 文件 | 物料 | 规格 | 视觉主题 | 建议数量 | 使用位置 |
| --- | --- | --- | --- | --- | --- | --- |
{rows}
"""
    (OUT / "README_最终交付.md").write_text(readme, encoding="utf-8")


def write_contact_sheet():
    cols = 4
    card_w, card_h = 520, 390
    gap = 30
    margin = 42
    title_h = 130
    groups: dict[str, list[Artwork]] = {}
    for art in ARTWORKS:
        groups.setdefault(art.category, []).append(art)
    h = title_h + sum(70 + math.ceil(len(v) / cols) * (card_h + gap) + gap for v in groups.values()) + 60
    w = margin * 2 + cols * card_w + (cols - 1) * gap
    sheet = Image.new("RGB", (w, h), "#FFF7E6")
    d = ImageDraw.Draw(sheet)
    d.text((margin, 32), "真的假的鸭活动物料最终设计总览 V3", fill=RED, font=font(42, True))
    d.text((margin, 88), "47件物料均为重新设计的非SVG栅格成稿；广告公司只做二维码替换、打样和印刷。", fill=INK, font=font(22))
    y = title_h
    for group, items in groups.items():
        d.rounded_rectangle((margin, y, w - margin, y + 48), radius=18, fill=WHITE, outline=GOLD, width=3)
        d.text((margin + 20, y + 10), group, fill=RED, font=font(26, True))
        y += 68
        for idx, art in enumerate(items):
            x = margin + (idx % cols) * (card_w + gap)
            if idx and idx % cols == 0:
                y += card_h + gap
            color = THEMES[art.theme]["accent"]
            d.rounded_rectangle((x, y, x + card_w, y + card_h), radius=18, fill=WHITE, outline=color, width=3)
            img = Image.open(PNG_DIR / f"{art.slug}.png").convert("RGB")
            img.thumbnail((card_w - 44, 245), Image.Resampling.LANCZOS)
            sheet.paste(img, (x + (card_w - img.width) // 2, y + 20))
            d.text((x + 20, y + 282), f"{ARTWORKS.index(art)+1:02d}. {art.title}", fill=RED, font=font(21, True))
            d.text((x + 20, y + 314), art.slug, fill=MUTED, font=font(15))
            d.text((x + 20, y + 340), THEMES[art.theme]["name"], fill=color, font=font(16, True))
            d.text((x + 20, y + 364), art.usage[:28], fill=INK, font=font(15))
        y += card_h + gap
    sheet.save(BOARD_DIR / "contact-sheet.png", optimize=True)


def write_style_board():
    w, h = 1800, 1300
    img = Image.new("RGB", (w, h), "#FFF7E6")
    d = ImageDraw.Draw(img)
    d.text((60, 44), "风格提炼：参考图不是素材拼贴，而是视觉语言", fill=RED, font=font(44, True))
    d.text((60, 104), "从12张小鸭方向提炼为：圆润亲和、红橙公益马甲、书页光芒、真假判断、扫码闯关、适老清晰、校园互动。", fill=INK, font=font(24))
    chips = [
        ("亲和小鸭主持人", CORAL), ("书页光芒/公益服务", GOLD), ("手机安全门诊", GREEN), ("校园剧场/短视频", BLUE),
        ("闯关任务卡/印章", CORAL), ("口诀扇/带走礼品", GOLD), ("风险雷达/案例提醒", BLUE), ("隐私边界/执行安全", RED),
    ]
    for i, (label, color) in enumerate(chips):
        x = 70 + (i % 4) * 420
        y = 185 + (i // 4) * 110
        d.rounded_rectangle((x, y, x + 360, y + 70), radius=34, fill=color)
        d.text((x + 36, y + 20), label, fill=WHITE, font=font(24, True))
    # draw a standalone raster mascot on the board
    board_art = Artwork("style-board-duck", "风格鸭", 360, 360, "", "", "stage", "", "", "", "")
    cv = Canvas(board_art, dpi=160)
    draw_background(cv)
    draw_duck(cv, 70, 62, 230, "host", "task")
    mascot = cv.img.resize((420, 420), Image.Resampling.LANCZOS)
    img.paste(mascot, (80, 480))
    d.text((560, 510), "最终稿使用重新绘制的无文字小鸭资产", fill=RED, font=font(34, True))
    d.text((560, 570), "参考图提供风格：软萌体积、红橙马甲、书页与公益光芒；正式物料不复制参考图，不让图片承载二维码和长中文。", fill=INK, font=font(24))
    d.text((560, 660), "版式规则", fill=RED, font=font(32, True))
    rules = ["标题区、信息区、互动区、二维码区、脚注区分开", "A区绿色适老，B区蓝色校园，C区红橙闯关，礼品区暖金", "按钮/边框/文字不互相覆盖，导出前逐页渲染检查", "广告公司只替换真实二维码、转CMYK、打样印刷"]
    for i, r in enumerate(rules, 1):
        d.text((590, 720 + i * 52), f"{i}. {r}", fill=INK, font=font(24))
    img.save(BOARD_DIR / "style-board.png", optimize=True)


def zip_package():
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(OUT).as_posix())


def main():
    ensure_dirs()
    for art in ARTWORKS:
        cv = render_artwork(art)
        cv.save_png_preview(PNG_DIR / f"{art.slug}.png")
        cv.save_pdf(PDF_DIR / f"{art.slug}.pdf")
    write_index()
    write_contact_sheet()
    write_style_board()
    zip_package()
    print(f"generated {len(ARTWORKS)} final materials under {OUT}")
    print(ZIP_PATH)


if __name__ == "__main__":
    main()
