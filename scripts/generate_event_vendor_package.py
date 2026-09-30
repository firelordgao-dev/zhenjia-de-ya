from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "vendor-package" / "2026-06-07"
PDF_DIR = OUT / "pdf-print"
PNG_DIR = OUT / "png-preview"
HANDOFF_DIR = OUT / "handoff"
IP_DIR = OUT / "ip-raster-assets"
CONCEPT_DIR = ROOT / "public" / "assets" / "concept-boards"
LANDING_DIR = ROOT / "public" / "assets" / "landing-kit"

FONT_REGULAR = "C:/Windows/Fonts/Deng.ttf"
FONT_BOLD = "C:/Windows/Fonts/Dengb.ttf"
PIL_FONT_REGULAR = FONT_REGULAR
PIL_FONT_BOLD = FONT_BOLD

COLORS = {
    "cream": "#FFF4DA",
    "cream2": "#FFE8B8",
    "yellow": "#FFD84D",
    "duck": "#FFD229",
    "beak": "#F59E2E",
    "coral": "#E96945",
    "red": "#C94D36",
    "gold": "#F0B84B",
    "mint": "#8BCB8F",
    "green": "#4EAA62",
    "sky": "#8AC5E8",
    "blue": "#5D91C9",
    "ink": "#5B3A24",
    "muted": "#90633B",
    "white": "#FFFFFF",
}


PRODUCTION_SPEC = {
    "main-stage-backdrop-5000x3000": ("主会场", "1套", "高清户外喷绘布/黑底布，哑面，四周打扣或按桁架固定", "上午主舞台", "否", "是", "必须小样", "PDF为1:10核版，输出放大1000%；确认舞台桁架实际净尺寸后再排产。"),
    "entrance-banner-8000x700": ("主会场", "1-2条", "横幅布或刀刮布，穿绳/打扣", "入口、舞台侧或社区主通道", "否", "是", "必须小样", "按现场悬挂宽度微调左右留白，远距离以主标题清晰为准。"),
    "entrance-wayfinding-800x2000": ("导视", "1个", "80x200cm易拉宝或5mm KT板覆膜加支架", "入口总导视", "否", "是", "必须小样", "活动当天如区域位置调整，可只改箭头/楼层信息。"),
    "zone-a-standee-800x2000": ("A区物料", "1个", "80x200cm易拉宝或5mm KT板覆膜加支架", "A区防骗驿站入口", "否", "是", "必须小样", "适老阅读优先，现场不要被桌椅遮挡二维码位。"),
    "zone-b-standee-800x2000": ("B区物料", "1个", "80x200cm易拉宝或5mm KT板覆膜加支架", "B区青春盾牌入口", "否", "是", "必须小样", "适合校园区拍照传播，保留人物站位空间。"),
    "zone-c-standee-800x2000": ("C区扫码闯关", "1-2个", "80x200cm易拉宝或5mm KT板覆膜加支架", "C区入口/排队口", "是", "是", "必须小样", "替换真实小程序码后，用老人手机和学生手机都做扫码测试。"),
    "direction-sign-a-a3-landscape": ("导视", "2-4张", "A3铜版纸覆膜裱KT板，或写真背胶裱板", "通道节点", "否", "否", "批量校对", "可按现场动线复制并调整箭头方向。"),
    "direction-sign-b-a3-landscape": ("导视", "2-4张", "A3铜版纸覆膜裱KT板，或写真背胶裱板", "通道节点", "否", "否", "批量校对", "可按现场动线复制并调整箭头方向。"),
    "direction-sign-c-a3-landscape": ("导视", "3-6张", "A3铜版纸覆膜裱KT板，或写真背胶裱板", "通往C区扫码闯关路线", "否", "否", "批量校对", "C区建议多放，降低排队和找入口成本。"),
    "case-board-01-600x900": ("案例展板", "1块", "60x90cm KT板覆哑膜", "主会场侧边/通道", "否", "否", "批量校对", "与其他案例展板统一高度摆放。"),
    "case-board-02-600x900": ("案例展板", "1块", "60x90cm KT板覆哑膜", "主会场侧边/通道", "否", "否", "批量校对", "与其他案例展板统一高度摆放。"),
    "case-board-03-600x900": ("案例展板", "1块", "60x90cm KT板覆哑膜", "主会场侧边/通道", "否", "否", "批量校对", "与其他案例展板统一高度摆放。"),
    "case-board-04-600x900": ("案例展板", "1块", "60x90cm KT板覆哑膜", "主会场侧边/通道", "否", "否", "批量校对", "与其他案例展板统一高度摆放。"),
    "case-board-05-600x900": ("案例展板", "1块", "60x90cm KT板覆哑膜", "主会场侧边/通道", "否", "否", "批量校对", "与其他案例展板统一高度摆放。"),
    "case-board-06-600x900": ("案例展板", "1块", "60x90cm KT板覆哑膜", "主会场侧边/通道", "否", "否", "批量校对", "与其他案例展板统一高度摆放。"),
    "c-zone-task-card-a5": ("C区扫码闯关", "100-300张", "A5 250g铜版纸，双面可选，哑膜", "C区桌面/排队发放", "否", "是", "必须小样", "章位需要和实际印章直径匹配；建议先打10张试盖。"),
    "a-zone-formula-card-a6": ("A区带走卡", "200-500张", "A6 250g铜版纸或书写卡纸", "A区防骗驿站", "否", "是", "批量校对", "老人带走使用，纸张不要过薄。"),
    "b-zone-question-card-a6": ("B区互动卡", "100-200张", "A6 250g铜版纸或书写卡纸", "B区快问快答/剧本互动", "否", "是", "批量校对", "可按题库继续追加不同题面。"),
    "volunteer-handcard-a6": ("执行安全", "30-60张", "A6 300g卡纸，圆角可选", "志愿者/工作人员", "否", "是", "必须小样", "工作人员随身携带，重点核对隐私边界话术。"),
    "redemption-coupon-a6": ("C区扫码闯关", "100-300张", "A6 250g铜版纸或书写卡纸", "C区领奖核销", "否", "是", "必须小样", "与礼品数量匹配，可加流水编号或现场手写编号。"),
    "privacy-desk-sign-a4": ("执行安全", "2-4个", "A4台卡/亚克力台牌内芯，200g铜版纸", "A区协助台、C区扫码协助点", "否", "是", "必须小样", "放在工作人员手边，提醒不代输密码、不拍屏幕。"),
    "handheld-signs-a3": ("互动传播", "2-4套", "A3铜版纸覆膜裱KT板，裁切后加手柄", "B区互动、拍照区、主持问答", "否", "否", "批量校对", "每套裁切成独立手举牌，手柄固定要牢。"),
    "photo-frame-600x900": ("互动传播", "1个", "5mm PVC板或KT板覆膜，异形裁切", "B/C区拍照点", "否", "是", "必须小样", "中央留空裁切，边框强度要足够手持。"),
    "gift-sticker-sheet-a5": ("礼品延展", "100-300张", "A5不干胶贴纸，覆哑膜，异形刀模可选", "礼品区/闯关奖励", "否", "否", "必须小样", "如做异形贴纸，刀模线由广告公司另出确认稿。"),
    "merch-print-sheet-a3": ("礼品延展", "1套母版", "A3核版稿，不直接批量印刷", "礼品供应商沟通", "否", "是", "必须小样", "作为礼品图案母版，实际按不同礼品工艺拆版。"),
    "activity-poster-a2": ("宣传招募", "20-50张", "A2海报，157g-200g铜版纸覆哑膜", "社区公告栏、校园张贴", "是", "是", "必须小样", "替换活动日期、地点、二维码和报名/参与口径。"),
    "c-zone-qr-table-sign-a4": ("C区扫码闯关", "2-4个", "A4台卡/亚克力台牌内芯，200g铜版纸", "C区扫码桌面", "是", "是", "必须小样", "二维码必须真机测试；建议桌面和排队尾端各放一个。"),
    "a-zone-phone-table-sign-a4": ("A区物料", "1-2个", "A4台卡/亚克力台牌内芯，200g铜版纸", "手机安全门诊桌", "否", "是", "批量校对", "适老字号，桌面摆放避免反光。"),
    "a-zone-bank-table-sign-a4": ("A区物料", "1-2个", "A4台卡/亚克力台牌内芯，200g铜版纸", "银行咨询台", "否", "是", "批量校对", "可按实际银行/协同单位改桌牌名称。"),
    "stamp-design-sheet-a4": ("C区扫码闯关", "1套", "印章图样确认稿，建议35-45mm光敏章/回墨章", "C区盖章核销", "否", "是", "必须小样", "印章需另出单色章稿，先试盖任务卡确认大小和清晰度。"),
    "volunteer-badge-90x120": ("执行安全", "30-60个", "90x120mm胸牌内芯，PVC证件卡套+挂绳", "工作人员/志愿者", "否", "是", "必须小样", "可留姓名手写区或贴纸区；别放私人手机号。"),
    "gift-fan-print-420x210": ("礼品延展", "200-500把", "广告扇PP/PVC扇面，单面或双面印刷", "礼品区/老人带走", "否", "是", "必须小样", "扇柄位置由供应商套刀模，口令文字必须避开柄位。"),
    "gift-tote-print-a4": ("礼品延展", "50-150个", "帆布袋丝印/热转印，A4图案区", "礼品区/工作人员物料袋", "否", "是", "必须小样", "大货前确认布色、印刷色差和图案居中。"),
    "gift-notebook-cover-a5": ("礼品延展", "100-300本", "A5骑马钉/胶装笔记本封面，250g铜版纸", "礼品区/学生奖品", "否", "是", "必须小样", "封面可加活动日期，内页按预算选择。"),
    "gift-tissue-box-sleeve-240x120": ("礼品延展", "100-300个", "纸巾盒套展开稿，铜版纸覆膜或白卡纸", "礼品区/社区带走", "否", "是", "必须小样", "需按实际纸巾盒尺寸重新确认展开刀模。"),
    "gift-phone-stand-card-a6": ("礼品延展", "100-300个", "手机支架包装卡/卡面，A6 300g卡纸", "礼品区/学生奖品", "否", "是", "必须小样", "如供应商有固定刀模，应把图案套入其模板。"),
    "gift-keychain-round-sheet-a5": ("礼品延展", "100-300个", "60mm亚克力钥匙扣/徽章拼版", "礼品区/闯关奖励", "否", "否", "必须小样", "每个圆牌需确认吊孔位置，避免打到小鸭脸部。"),
    "checkin-table-sign-a4": ("现场执行", "1-2个", "A4台卡/亚克力台牌内芯，200g铜版纸", "签到台/入口接待", "否", "是", "必须小样", "如现场需要签到表或签到码，由执行方另行补充。"),
    "gift-redemption-table-sign-a4": ("现场执行", "1-2个", "A4台卡/亚克力台牌内芯，200g铜版纸", "礼品兑换台", "否", "是", "必须小样", "与礼品数量、领奖规则和核销章保持一致。"),
    "queue-guide-sign-a4": ("现场执行", "2-4个", "A4台卡或KT板覆膜", "C区排队口/等候区", "否", "否", "批量校对", "放在队尾和扫码桌前，减少工作人员重复解释。"),
    "fallback-paper-quiz-a4": ("C区扫码闯关", "50-100张", "A4 80g-120g书写纸，黑白或双色均可", "网络异常/排队超10人时启用", "否", "是", "必须小样", "必须能手写答案和人工核销，建议现场预先裁夹。"),
    "miniprogram-score-page-board-a4": ("小程序交付", "1-2张", "A4铜版纸/KT板覆膜，培训或桌面展示", "C区工作人员培训/扫码桌", "否", "是", "必须小样", "用于确认成绩页字段和视觉，不直接替代小程序真机页面。"),
    "score-verification-guide-a4": ("C区扫码闯关", "1-2个", "A4台卡/亚克力台牌内芯，200g铜版纸", "C区核销盖章处", "否", "是", "必须小样", "工作人员按此核对成绩页，不记录手机号和个人隐私。"),
    "host-cue-card-a5": ("主持执行", "3-5张", "A5 250g卡纸，圆角可选", "主持人/讲演人员手边", "否", "是", "必须小样", "只保留短句和转场提示，避免主持人读长稿。"),
    "video-consent-sign-a4": ("B区物料", "1-2个", "A4台卡/KT板覆膜", "B区短视频拍摄点", "否", "是", "必须小样", "提示自愿拍摄和未成年人/肖像授权边界。"),
    "staff-briefing-board-a3": ("执行安全", "1-2张", "A3横版KT板覆膜或培训讲义", "工作人员集合处/后台", "否", "是", "必须小样", "活动前5分钟复核用，不放到观众主动线。"),
    "qr-replacement-checklist-a4": ("印前交接", "1张", "A4普通纸或随包电子版", "广告公司核版/执行方验收", "是", "是", "必须小样", "不是对外物料，用于逐项确认小程序码、海报码和桌牌码。"),
}

SPEC_HEADERS = [
    "文件名",
    "物料",
    "规格",
    "类别",
    "建议数量",
    "建议材质工艺",
    "使用位置",
    "二维码替换",
    "信息替换",
    "打样优先级",
    "制作备注",
]

GUIDE_HEADERS = [
    "编号",
    "分组",
    "中文材料名",
    "英文文件名",
    "PDF核版稿",
    "PNG校对图",
    "实际用途",
    "使用/确认人",
    "制作确认重点",
]

GROUP_BY_CATEGORY = {
    "主会场": "01 主会场与入口导视",
    "导视": "01 主会场与入口导视",
    "宣传招募": "01 主会场与入口导视",
    "案例展板": "02 案例展陈",
    "A区物料": "03 A区 防骗驿站",
    "A区带走卡": "03 A区 防骗驿站",
    "B区物料": "04 B区 青春盾牌",
    "B区互动卡": "04 B区 青春盾牌",
    "互动传播": "05 互动传播与拍照",
    "C区扫码闯关": "06 C区 真的假的鸭扫码闯关",
    "小程序交付": "06 C区 真的假的鸭扫码闯关",
    "现场执行": "07 现场执行与安全",
    "执行安全": "07 现场执行与安全",
    "主持执行": "07 现场执行与安全",
    "印前交接": "08 印前交接与核版",
    "礼品延展": "09 礼品物料延展",
}

OWNER_BY_GROUP = {
    "01 主会场与入口导视": "执行统筹 / 广告公司 / 场务",
    "02 案例展陈": "执行统筹 / 宣讲人员 / 广告公司",
    "03 A区 防骗驿站": "A区负责人 / 志愿者 / 广告公司",
    "04 B区 青春盾牌": "B区负责人 / 主持或互动人员 / 广告公司",
    "05 互动传播与拍照": "B/C区负责人 / 摄影摄像 / 广告公司",
    "06 C区 真的假的鸭扫码闯关": "C区负责人 / 小程序负责人 / 广告公司",
    "07 现场执行与安全": "执行统筹 / 志愿者 / 各区负责人",
    "08 印前交接与核版": "广告公司 / 执行统筹 / C区负责人",
    "09 礼品物料延展": "礼品负责人 / 供应商 / 广告公司",
}

THEME_META = {
    "stage": {
        "label": "活动主视觉",
        "source": "event-guide-duck-rich-minjin-v1.png",
        "asset": "theme-stage.png",
        "accent": "#E96945",
        "soft": "#FFF0C9",
        "source_note": "活动IP总视觉、书页光芒、公益陪伴感",
    },
    "pause": {
        "label": "转账暂停令",
        "source": "wildcard-01.png",
        "asset": "theme-pause.png",
        "accent": "#E96945",
        "soft": "#FFE3D6",
        "source_note": "先停一下、验证码不给、转账前核实",
    },
    "phone": {
        "label": "手机安全门诊",
        "source": "wildcard-02.png",
        "asset": "theme-phone.png",
        "accent": "#4EAA62",
        "soft": "#DDF2D9",
        "source_note": "A区适老手机指导、一对一陪伴",
    },
    "bank": {
        "label": "银行咨询陪伴",
        "source": "wildcard-05.png",
        "asset": "theme-bank.png",
        "accent": "#4EAA62",
        "soft": "#E6F3D5",
        "source_note": "银行咨询、账户安全、家庭陪伴",
    },
    "campus": {
        "label": "校园剧场",
        "source": "wildcard-03.png",
        "asset": "theme-campus.png",
        "accent": "#5D91C9",
        "soft": "#D8EDF9",
        "source_note": "B区剧本杀、真假判断、学生互动",
    },
    "video": {
        "label": "短视频挑战",
        "source": "wildcard-08.png",
        "asset": "theme-video.png",
        "accent": "#5D91C9",
        "soft": "#D9EEFB",
        "source_note": "校园短视频、拍摄框、年轻传播",
    },
    "quest": {
        "label": "真假闯关盖章",
        "source": "wildcard-04.png",
        "asset": "theme-quest.png",
        "accent": "#E96945",
        "soft": "#FFF0C9",
        "source_note": "C区扫码闯关、5题挑战、盖章领奖",
    },
    "stamp": {
        "label": "任务卡与印章",
        "source": "landing-kit-02-task-card-stamp-system.png",
        "asset": "theme-stamp.png",
        "accent": "#E96945",
        "soft": "#FFF0C9",
        "source_note": "任务卡章位、领奖券、印章核销",
    },
    "score": {
        "label": "成绩页组件",
        "source": "landing-kit-03-miniprogram-score-page.png",
        "asset": "theme-score.png",
        "accent": "#4EAA62",
        "soft": "#E8F6D9",
        "source_note": "小程序成绩页、等级徽章、核销提示",
    },
    "risk": {
        "label": "风险雷达",
        "source": "wildcard-11.png",
        "asset": "theme-risk.png",
        "accent": "#5D91C9",
        "soft": "#D8EDF9",
        "source_note": "金融风险识别、雷达提示、真假信号",
    },
    "evidence": {
        "label": "证据留存",
        "source": "wildcard-09.png",
        "asset": "theme-evidence.png",
        "accent": "#F0B84B",
        "soft": "#F9E9C8",
        "source_note": "保留聊天、链接、转账记录和线索",
    },
    "fan": {
        "label": "口诀扇",
        "source": "wildcard-07.png",
        "asset": "theme-fan.png",
        "accent": "#F0B84B",
        "soft": "#FFF2C6",
        "source_note": "带走型口诀、礼品传播、社区适老",
    },
    "family": {
        "label": "家庭接力",
        "source": "wildcard-12.png",
        "asset": "theme-family.png",
        "accent": "#E96945",
        "soft": "#FFE9D4",
        "source_note": "家人互相提醒、社区传播、陪伴感",
    },
    "gift": {
        "label": "礼品延展",
        "source": "landing-kit-04-gift-merch-extension.png",
        "asset": "theme-gift.png",
        "accent": "#E96945",
        "soft": "#FFF0C9",
        "source_note": "扇子、帆布袋、钥匙扣、贴纸、手机支架",
    },
}


def theme_for_slug(slug: str) -> str:
    if slug in {"main-stage-backdrop-5000x3000", "entrance-banner-8000x700", "entrance-wayfinding-800x2000", "activity-poster-a2"}:
        return "stage"
    if slug.startswith("zone-a") or slug.startswith("a-zone-phone") or slug == "a-zone-formula-card-a6":
        return "phone"
    if slug == "a-zone-bank-table-sign-a4":
        return "bank"
    if slug.startswith("zone-b") or slug == "b-zone-question-card-a6":
        return "campus"
    if slug == "video-consent-sign-a4":
        return "video"
    if slug.startswith("zone-c") or slug in {"c-zone-qr-table-sign-a4", "queue-guide-sign-a4", "fallback-paper-quiz-a4"}:
        return "quest"
    if slug in {"c-zone-task-card-a5", "redemption-coupon-a6", "stamp-design-sheet-a4", "gift-redemption-table-sign-a4"}:
        return "stamp"
    if slug in {"miniprogram-score-page-board-a4", "score-verification-guide-a4"}:
        return "score"
    if slug.startswith("case-board") or slug in {"privacy-desk-sign-a4", "qr-replacement-checklist-a4", "staff-briefing-board-a3"}:
        return "risk"
    if slug in {"volunteer-handcard-a6", "volunteer-badge-90x120", "host-cue-card-a5", "checkin-table-sign-a4"}:
        return "pause"
    if slug in {"handheld-signs-a3", "photo-frame-600x900"}:
        return "campus"
    if slug in {"gift-fan-print-420x210"}:
        return "fan"
    if slug.startswith("gift-") or slug == "merch-print-sheet-a3":
        return "gift"
    if slug.startswith("direction-sign"):
        return "stage"
    return "stage"

MATERIAL_PURPOSES = {
    "main-stage-backdrop-5000x3000": "上午主舞台的大视觉，统一呈现“守护钱袋子”主题和“真的假的鸭”公益IP气质。",
    "entrance-banner-8000x700": "让路过人群第一眼知道活动主题，适合挂在入口、主通道或舞台侧方。",
    "entrance-wayfinding-800x2000": "入口总导视，告诉参与者 A/B/C 区分别在哪里，减少现场问路成本。",
    "zone-a-standee-800x2000": "A区入口主视觉，帮助老人和家庭快速识别“防骗驿站”服务点。",
    "zone-b-standee-800x2000": "B区入口主视觉，强化学生互动、剧本杀、短视频和快问快答的年轻化氛围。",
    "zone-c-standee-800x2000": "C区扫码闯关主视觉，引导参与者扫码进入小程序完成5题闯关。",
    "direction-sign-a-a3-landscape": "通道节点方向牌，按现场动线复制摆放，引导参与者去A区。",
    "direction-sign-b-a3-landscape": "通道节点方向牌，按现场动线复制摆放，引导参与者去B区。",
    "direction-sign-c-a3-landscape": "通道节点方向牌，建议多点摆放，引导参与者去C区扫码闯关。",
    "case-board-01-600x900": "案例展板，用真实高频诈骗类型做驻足阅读教育。",
    "case-board-02-600x900": "案例展板，用真实高频诈骗类型做驻足阅读教育。",
    "case-board-03-600x900": "案例展板，用真实高频诈骗类型做驻足阅读教育。",
    "case-board-04-600x900": "案例展板，用真实高频诈骗类型做驻足阅读教育。",
    "case-board-05-600x900": "案例展板，用真实高频诈骗类型做驻足阅读教育。",
    "case-board-06-600x900": "案例展板，用真实高频诈骗类型做驻足阅读教育。",
    "c-zone-task-card-a5": "C区参与者手持任务卡，用来记录扫码、答题、成绩核销和盖章领奖流程。",
    "a-zone-formula-card-a6": "A区可带走口诀卡，适合老人和家庭成员回家后反复查看。",
    "b-zone-question-card-a6": "B区互动题卡，用于学生快问快答、剧本互动或主持人抽题。",
    "volunteer-handcard-a6": "工作人员随身安全话术卡，提醒不代输密码、不拍屏幕、不记录隐私。",
    "redemption-coupon-a6": "C区盖章领奖券，用于把闯关完成和礼品核销衔接起来。",
    "privacy-desk-sign-a4": "桌面隐私提醒牌，放在协助点旁边，给参与者和志愿者同时做边界提醒。",
    "checkin-table-sign-a4": "签到台或入口接待桌牌，让参与者到场后先找到接待位置。",
    "gift-redemption-table-sign-a4": "礼品兑换台桌牌，说明领奖口径，降低现场重复解释。",
    "queue-guide-sign-a4": "C区排队提示牌，适合队尾和扫码桌前使用，帮助控制秩序。",
    "fallback-paper-quiz-a4": "小程序网络异常或排队过长时启用的纸质兜底答题卡。",
    "miniprogram-score-page-board-a4": "小程序成绩页字段和视觉的交付说明板，供工作人员培训和开发对齐。",
    "score-verification-guide-a4": "C区核销说明牌，工作人员按成绩页等级和完成状态盖章。",
    "host-cue-card-a5": "主持人或讲演人员转场手卡，把微课堂、情景剧和互动问答串起来。",
    "video-consent-sign-a4": "B区短视频拍摄授权提示，提醒自愿参与和肖像授权边界。",
    "staff-briefing-board-a3": "工作人员集合处总提示，用于活动开始前5分钟统一口径。",
    "qr-replacement-checklist-a4": "印前内部核对清单，逐项确认哪些文件需要替换真实二维码。",
    "handheld-signs-a3": "手举牌合集，裁切加手柄后用于互动、拍照和主持问答。",
    "photo-frame-600x900": "拍照框，给参与者完成闯关或互动后拍照留念使用。",
    "gift-sticker-sheet-a5": "贴纸版礼品稿，可用于闯关奖励、袋贴、桌面小贴纸等。",
    "merch-print-sheet-a3": "礼品印刷母版，把小鸭IP、口号和图案集中给供应商拆版参考。",
    "activity-poster-a2": "社区和校园张贴海报，用于活动预告、招募和现场入口补充导流。",
    "c-zone-qr-table-sign-a4": "C区桌面扫码牌，近距离承载真实小程序码，是扫码闯关的关键入口。",
    "a-zone-phone-table-sign-a4": "A区手机安全门诊桌牌，指向一对一手机安全指导服务。",
    "a-zone-bank-table-sign-a4": "A区银行咨询台桌牌，指向银行工作人员咨询服务。",
    "stamp-design-sheet-a4": "印章图样确认稿，用于制作闯关章、核销章，并和任务卡章位试盖。",
    "volunteer-badge-90x120": "志愿者胸牌，帮助参与者识别可信工作人员。",
    "gift-fan-print-420x210": "广告扇礼品印刷稿，适合老人和社区参与者带走。",
    "gift-tote-print-a4": "帆布袋印刷稿，可做礼品袋、工作人员物料袋或活动纪念袋。",
    "gift-notebook-cover-a5": "笔记本封面，适合学生奖品或互动礼品。",
    "gift-tissue-box-sleeve-240x120": "纸巾盒套展开参考，适合社区家庭场景的实用礼品。",
    "gift-phone-stand-card-a6": "手机支架卡面或包装卡，适合学生和年轻参与者礼品。",
    "gift-keychain-round-sheet-a5": "圆形钥匙扣拼版，适合闯关完成后的轻量纪念品。",
}


@dataclass
class Element:
    kind: str
    attrs: dict


@dataclass
class Artwork:
    slug: str
    title: str
    width_mm: float
    height_mm: float
    final_size: str
    bleed_mm: float
    safe_mm: float
    notes: str
    elements: list[Element] = field(default_factory=list)

    def add(self, kind: str, **attrs):
        self.elements.append(Element(kind, attrs))


def ensure_dirs():
    for stale in (OUT / ("source-" + "svg"), OUT / "pdf-preview"):
        if stale.exists():
            for child in stale.glob("*"):
                child.unlink()
            stale.rmdir()
    for path in (PDF_DIR, PNG_DIR, HANDOFF_DIR, IP_DIR):
        path.mkdir(parents=True, exist_ok=True)


def font_setup():
    pdfmetrics.registerFont(TTFont("DengXian", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("DengXian-Bold", FONT_BOLD))


def source_path_for_theme(theme: str) -> Path:
    source = THEME_META[theme]["source"]
    if source.startswith("landing-kit"):
        return LANDING_DIR / source
    return CONCEPT_DIR / source


def ip_asset_path(theme: str) -> Path:
    return IP_DIR / THEME_META[theme]["asset"]


def prepare_ip_assets():
    for theme, meta in THEME_META.items():
        source = source_path_for_theme(theme)
        if not source.exists():
            raise FileNotFoundError(f"missing IP source image: {source}")
        out = ip_asset_path(theme)
        src = Image.open(source).convert("RGB")
        size = 900
        if src.width != src.height:
            side = min(src.width, src.height)
            left = (src.width - side) // 2
            top = (src.height - side) // 2
            src = src.crop((left, top, left + side, top + side))
        src = src.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
        mask = Image.new("L", (size, size), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, size, size), radius=72, fill=224)
        src.putalpha(mask)
        src.save(out, "PNG", optimize=True)


def add_ip_image(art: Artwork, x: float, y: float, w: float, h: float, theme: str | None = None, frame: bool = True):
    theme = theme or theme_for_slug(art.slug)
    if frame:
        art.add("rect", x=x - w * 0.035, y=y - h * 0.035, w=w * 1.07, h=h * 1.07, fill=COLORS["white"], stroke=THEME_META[theme]["accent"], sw=max(0.8, min(w, h) * 0.012))
    art.add("image", x=x, y=y, w=w, h=h, path=str(ip_asset_path(theme)))


def add_theme_cameo(art: Artwork):
    theme = theme_for_slug(art.slug)
    if art.width_mm >= 1000:
        size = min(art.width_mm * 0.18, art.height_mm * 0.42)
        x = art.width_mm - size - art.safe_mm * 3.0
        y = art.safe_mm * 2.0
    elif art.height_mm / art.width_mm > 1.55:
        size = art.width_mm * 0.42
        x = art.width_mm - size - art.safe_mm * 1.25
        y = art.height_mm - size - art.safe_mm * 2.2
    elif art.width_mm / art.height_mm > 1.25:
        size = art.height_mm * 0.62
        x = art.width_mm - size - art.safe_mm * 1.4
        y = (art.height_mm - size) / 2
    else:
        size = min(art.width_mm, art.height_mm) * 0.30
        x = art.width_mm - size - art.safe_mm * 1.4
        y = art.height_mm - size - art.safe_mm * 1.6
    add_ip_image(art, x, y, size, size, theme, frame=True)


def safe_name(text: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", text.lower()).strip("-")


def add_common_bg(art: Artwork, variant: str = "warm"):
    theme = theme_for_slug(art.slug)
    meta = THEME_META[theme]
    accent = meta["accent"]
    soft = meta["soft"]
    art.add("rect", x=0, y=0, w=art.width_mm, h=art.height_mm, fill=soft)
    art.add("circle", cx=art.width_mm * 0.86, cy=art.height_mm * 0.10, r=art.width_mm * 0.18, fill="#FFE7A3")
    art.add("circle", cx=art.width_mm * 0.05, cy=art.height_mm * 0.88, r=art.width_mm * 0.20, fill="#DDF2D9" if theme not in {"campus", "video", "risk"} else "#D8EDF9")
    art.add("arc", x=art.width_mm * 0.52, y=art.height_mm * 0.12, r=art.width_mm * 0.18, color=accent, stroke=art.width_mm * 0.003)
    art.add("arc", x=art.width_mm * 0.52, y=art.height_mm * 0.12, r=art.width_mm * 0.23, color=accent, stroke=art.width_mm * 0.002)
    if theme in {"quest", "stamp", "score"}:
        art.add("pill", x=art.width_mm * 0.08, y=art.height_mm * 0.78, w=art.width_mm * 0.28, h=art.height_mm * 0.045, fill=COLORS["coral"], text="扫码 · 答题 · 盖章", text_fill=COLORS["white"], text_size=art.height_mm * 0.014)
    elif theme in {"phone", "bank"}:
        art.add("pill", x=art.width_mm * 0.08, y=art.height_mm * 0.78, w=art.width_mm * 0.30, h=art.height_mm * 0.045, fill=COLORS["green"], text="一对一 · 不碰密码", text_fill=COLORS["white"], text_size=art.height_mm * 0.014)
    elif theme in {"campus", "video"}:
        art.add("pill", x=art.width_mm * 0.08, y=art.height_mm * 0.78, w=art.width_mm * 0.30, h=art.height_mm * 0.045, fill=COLORS["blue"], text="剧场感 · 快问答", text_fill=COLORS["white"], text_size=art.height_mm * 0.014)
    elif theme in {"gift", "fan"}:
        art.add("pill", x=art.width_mm * 0.08, y=art.height_mm * 0.78, w=art.width_mm * 0.28, h=art.height_mm * 0.045, fill=COLORS["gold"], text="带走 · 复用 · 传播", text_fill=COLORS["white"], text_size=art.height_mm * 0.014)
    add_theme_cameo(art)


def add_title(art: Artwork, title: str, subtitle: str | None = None, y: float | None = None):
    y = art.height_mm * 0.11 if y is None else y
    size = min(art.width_mm * 0.07, art.height_mm * 0.11, 165)
    art.add("text", x=art.width_mm / 2, y=y, text=title, size=size, fill=COLORS["red"], weight="bold", anchor="middle")
    if subtitle:
        art.add(
            "pill",
            x=art.width_mm * 0.25,
            y=y + size * 0.8,
            w=art.width_mm * 0.5,
            h=size * 0.55,
            fill=COLORS["coral"],
            text=subtitle,
            text_fill=COLORS["white"],
            text_size=size * 0.28,
        )


def add_duck(art: Artwork, x: float, y: float, s: float):
    art.add("duck", x=x, y=y, s=s)


def add_qr(art: Artwork, x: float, y: float, size: float, label: str = "二维码占位"):
    art.add("qr", x=x, y=y, size=size, label=label)


def add_process(art: Artwork, x: float, y: float, w: float, labels: list[str]):
    step_w = w / len(labels)
    prev = None
    for i, label in enumerate(labels):
        cx = x + step_w * (i + 0.5)
        r = min(step_w * 0.22, art.height_mm * 0.045)
        art.add("circle", cx=cx, cy=y, r=r, fill=COLORS["white"], stroke=COLORS["gold"], sw=max(1.2, r * 0.08))
        art.add("text", x=cx, y=y - r * 0.12, text=str(i + 1), size=r * 0.85, fill=COLORS["coral"], weight="bold", anchor="middle")
        art.add("text", x=cx, y=y + r * 1.75, text=label, size=r * 0.42, fill=COLORS["ink"], weight="bold", anchor="middle")
        if prev:
            art.add("line", x1=prev + r * 1.15, y1=y, x2=cx - r * 1.15, y2=y, stroke=COLORS["gold"], sw=max(1, r * 0.08))
        prev = cx


def add_chip_row(art: Artwork, x: float, y: float, labels: list[str], color: str = "mint"):
    cur = x
    for label in labels:
        w = max(len(label) * art.width_mm * 0.018, art.width_mm * 0.13)
        h = art.height_mm * 0.055
        art.add("pill", x=cur, y=y, w=w, h=h, fill=COLORS[color], text=label, text_fill=COLORS["white"], text_size=h * 0.42)
        cur += w + art.width_mm * 0.018


def add_footer(art: Artwork, text: str = "主办/协同/指导单位信息由执行方最终确认  |  本活动不收取任何费用"):
    art.add("text", x=art.width_mm / 2, y=art.height_mm - art.safe_mm * 0.9, text=text, size=max(8, art.width_mm * 0.012), fill=COLORS["muted"], anchor="middle")


def poster_base(slug: str, title: str, w: float, h: float, final_size: str, bleed: float, safe: float, notes: str, variant: str = "warm") -> Artwork:
    art = Artwork(slug, title, w, h, final_size, bleed, safe, notes)
    add_common_bg(art, variant)
    art.add("rect", x=bleed, y=bleed, w=w - bleed * 2, h=h - bleed * 2, fill="none", stroke="#E8B769", sw=max(1, min(w, h) * 0.003), dash="14 10")
    return art


def build_artworks() -> list[Artwork]:
    arts: list[Artwork] = []

    main = poster_base(
        "main-stage-backdrop-5000x3000",
        "主背景板",
        5000,
        3000,
        "5000mm x 3000mm, PDF preview 1:10",
        30,
        150,
        "主舞台背景板。PDF 核版稿按 1:10 预览，输出时放大 1000%。",
    )
    add_title(main, "守护钱袋子", "金融防骗反诈公益日", y=420)
    main.add("text", x=2500, y=860, text="学知识 · 辨真伪 · 护自己 · 帮他人", size=145, fill=COLORS["ink"], weight="bold", anchor="middle")
    add_duck(main, 480, 1180, 900)
    add_process(main, 1700, 1520, 2500, ["微课堂", "情景剧", "互动问答", "分区体验"])
    main.add("panel", x=1450, y=1900, w=850, h=520, title="A区 防骗驿站", lines=["手机安全一对一指导", "防骗口诀记忆挑战", "银行账户安全咨询"], accent=COLORS["mint"])
    main.add("panel", x=2350, y=1900, w=850, h=520, title="B区 青春盾牌", lines=["学生剧本互动", "短视频创作", "知识快问快答"], accent=COLORS["sky"])
    main.add("panel", x=3250, y=1900, w=850, h=520, title="C区 真的假的鸭", lines=["扫码进入小程序", "5题闯关", "成绩页盖章领奖"], accent=COLORS["coral"])
    add_footer(main)
    arts.append(main)

    banner = Artwork("entrance-banner-8000x700", "入口横幅", 8000, 700, "8000mm x 700mm, PDF preview 1:10", 20, 80, "入口或舞台侧横幅。")
    banner.add("rect", x=0, y=0, w=8000, h=700, fill=COLORS["coral"])
    banner.add("circle", cx=620, cy=350, r=210, fill=COLORS["yellow"])
    banner.add("duck", x=450, y=190, s=310)
    banner.add("text", x=4100, y=295, text="守护钱袋子  金融防骗反诈公益日", size=185, fill=COLORS["white"], weight="bold", anchor="middle")
    banner.add("text", x=4100, y=500, text="学知识 · 辨真伪 · 护自己 · 帮他人", size=86, fill="#FFECC9", weight="bold", anchor="middle")
    banner.add("text", x=7420, y=365, text="真的假的鸭", size=112, fill="#FFECC9", weight="bold", anchor="middle")
    arts.append(banner)

    guide = poster_base("entrance-wayfinding-800x2000", "总导视牌", 800, 2000, "800mm x 2000mm", 10, 45, "入口总导视牌。", "green")
    add_title(guide, "活动导视", "守护钱袋子", y=190)
    add_duck(guide, 80, 390, 210)
    guide.add("text", x=390, y=460, text="上午主会场", size=62, fill=COLORS["red"], weight="bold", anchor="start")
    guide.add("text", x=390, y=540, text="10:00-12:00 微课堂 / 情景剧 / 问答", size=30, fill=COLORS["ink"], anchor="start")
    rows = [
        ("A", "防骗驿站", "手机安全 · 银行咨询 · 口诀卡", COLORS["mint"]),
        ("B", "青春盾牌", "剧本杀 · 短视频 · 快问快答", COLORS["sky"]),
        ("C", "真的假的鸭", "扫码闯关 · 成绩页 · 盖章领奖", COLORS["coral"]),
    ]
    y = 760
    for code, name, desc, color in rows:
        guide.add("zone_row", x=80, y=y, w=640, h=230, code=code, name=name, desc=desc, color=color)
        y += 290
    guide.add("text", x=400, y=1770, text="请根据现场箭头前往对应分区", size=36, fill=COLORS["muted"], anchor="middle")
    arts.append(guide)

    zone_specs = [
        ("zone-a-standee-800x2000", "A区 防骗驿站", "老人手机安全一对一指导", "green", ["手机有疑问，先停一下", "验证码不给任何人", "96110 来电要接听", "不代输密码，不拍手机屏幕"], "手机安全门诊"),
        ("zone-b-standee-800x2000", "B区 青春盾牌", "学生反诈互动挑战", "blue", ["兼职先交钱，多半有问题", "演出票务走官方渠道", "游戏交易别脱离平台", "屏幕共享立刻停"], "剧本杀 / 短视频 / 快问快答"),
        ("zone-c-standee-800x2000", "C区 真的假的鸭", "扫码进入小程序，5题闯关", "warm", ["扫码进入", "完成5题", "查看等级", "凭成绩页盖章领奖"], "扫码闯关"),
    ]
    for slug, title, subtitle, variant, bullets, tag in zone_specs:
        art = poster_base(slug, title, 800, 2000, "800mm x 2000mm", 10, 45, f"{title} 易拉宝/展架。", "blue" if variant == "blue" else "green" if variant == "green" else "warm")
        add_title(art, title, subtitle, y=180)
        add_duck(art, 80, 405, 250)
        art.add("pill", x=370, y=470, w=300, h=92, fill=COLORS["coral"] if "C区" in title else COLORS["green"] if "A区" in title else COLORS["blue"], text=tag, text_fill=COLORS["white"], text_size=38)
        y = 720
        for i, bullet in enumerate(bullets):
            art.add("bullet", x=100, y=y, w=600, h=150, num=str(i + 1), text=bullet, color=COLORS["coral"] if "C区" in title else COLORS["green"] if "A区" in title else COLORS["blue"])
            y += 185
        if "C区" in title:
            add_qr(art, 270, 1390, 260, "小程序二维码占位")
            art.add("text", x=400, y=1710, text="凭成绩页盖章领奖", size=48, fill=COLORS["red"], weight="bold", anchor="middle")
        else:
            art.add("panel", x=90, y=1450, w=620, h=260, title="现场提醒", lines=["活动不收取任何费用", "遇到可疑情况请找工作人员"], accent=COLORS["gold"])
        arts.append(art)

    for code, name, color in [("A", "防骗驿站", COLORS["mint"]), ("B", "青春盾牌", COLORS["sky"]), ("C", "真的假的鸭", COLORS["coral"])]:
        sign = poster_base(f"direction-sign-{code.lower()}-a3-landscape", f"{code}区方向牌", 420, 297, "A3 横版 420mm x 297mm", 3, 12, "区域方向牌，可按箭头方向复制翻转。")
        sign.add("circle", cx=70, cy=148, r=52, fill=color)
        sign.add("text", x=70, y=164, text=code, size=62, fill=COLORS["white"], weight="bold", anchor="middle")
        sign.add("text", x=150, y=126, text=name, size=44, fill=COLORS["ink"], weight="bold", anchor="start")
        sign.add("text", x=150, y=180, text="请沿箭头前往", size=22, fill=COLORS["muted"], anchor="start")
        sign.add("arrow", x=330, y=148, size=62, color=COLORS["red"])
        arts.append(sign)

    case_data = [
        ("01", "养老投资诈骗", "承诺高回报、保本收益、拉人入群", "先停：不要追加转账"),
        ("02", "冒充客服退款", "先赔付、再认证、索要验证码", "核实：官方 App 内联系"),
        ("03", "虚假理财/杀猪盘", "网友带投、平台异常、提现要交税", "退出：不再充值"),
        ("04", "冒充公检法", "保密办案、安全账户、视频笔录", "报警：没有安全账户"),
        ("05", "刷单返利", "小额返利、垫付升级、连单任务", "停止：兼职不先交钱"),
        ("06", "屏幕共享/钓鱼链接", "远程控制、陌生链接、下载非官方 App", "保护：验证码不给"),
    ]
    for no, title, signal, action in case_data:
        case = poster_base(f"case-board-{no}-600x900", f"案例展板 {no}", 600, 900, "KT板 600mm x 900mm", 5, 30, "KT 案例展板。")
        case.add("text", x=70, y=95, text=no, size=58, fill=COLORS["coral"], weight="bold", anchor="start")
        case.add("text", x=160, y=95, text=title, size=43, fill=COLORS["ink"], weight="bold", anchor="start")
        case.add("panel", x=60, y=185, w=480, h=220, title="骗子信号", lines=[signal], accent=COLORS["coral"])
        case.add("panel", x=60, y=450, w=480, h=220, title="正确动作", lines=[action, "留存聊天、电话、转账凭证"], accent=COLORS["mint"])
        case.add("text", x=300, y=760, text="停一下，再核实", size=42, fill=COLORS["red"], weight="bold", anchor="middle")
        add_duck(case, 420, 700, 115)
        arts.append(case)

    task = poster_base("c-zone-task-card-a5", "C区闯关任务卡", 148, 210, "A5 148mm x 210mm", 3, 8, "C 区桌面任务卡。")
    task.add("text", x=74, y=24, text="真的假的鸭 闯关任务卡", size=13, fill=COLORS["red"], weight="bold", anchor="middle")
    task.add("text", x=74, y=40, text="完成5题后，请工作人员盖章领奖", size=6, fill=COLORS["muted"], anchor="middle")
    positions = [(43, 70), (105, 70), (43, 115), (105, 115), (74, 160)]
    for i, (cx, cy) in enumerate(positions, 1):
        task.add("circle", cx=cx, cy=cy, r=17, fill=COLORS["white"], stroke=COLORS["gold"], sw=1.2, dash="3 2")
        task.add("text", x=cx, y=cy + 2, text=str(i), size=9, fill=COLORS["coral"], weight="bold", anchor="middle")
    task.add("text", x=74, y=196, text="人工核销：不收手机号，不代答题，不记录隐私", size=5, fill=COLORS["muted"], anchor="middle")
    arts.append(task)

    a6_cards = [
        ("a-zone-formula-card-a6", "防骗口诀卡", ["停一下：别急着转账", "问家人：多一个人核实", "查官方：拨打官方电话", "存证据：聊天转账都留好", "报风险：110 / 96110"], COLORS["green"]),
        ("b-zone-question-card-a6", "青春快问快答题卡", ["兼职先交钱？假", "客服索要验证码？假", "96110 来电？接听", "屏幕共享？立刻停", "票务交易？走官方"], COLORS["blue"]),
        ("volunteer-handcard-a6", "志愿者安全手卡", ["不代输密码", "不拍手机屏幕", "不询问验证码", "排队超过10人切纸质卡", "活动不收取任何费用"], COLORS["coral"]),
        ("redemption-coupon-a6", "盖章领奖券", ["完成闯关后领取", "工作人员核销盖章", "每人限领一份", "礼品以现场为准"], COLORS["gold"]),
    ]
    for slug, title, lines, color in a6_cards:
        card = poster_base(slug, title, 105, 148, "A6 105mm x 148mm", 3, 7, f"{title}。")
        card.add("text", x=52.5, y=20, text=title, size=10, fill=COLORS["red"], weight="bold", anchor="middle")
        y = 38
        for i, line in enumerate(lines, 1):
            card.add("bullet", x=12, y=y, w=82, h=17, num=str(i), text=line, color=color, small=True)
            y += 22
        arts.append(card)

    privacy = poster_base("privacy-desk-sign-a4", "隐私安全桌牌", 210, 297, "A4 210mm x 297mm", 3, 12, "A 区/C 区桌面提示牌。")
    privacy.add("text", x=105, y=35, text="隐私安全提示", size=18, fill=COLORS["red"], weight="bold", anchor="middle")
    for i, line in enumerate(["工作人员不代输密码", "不拍摄手机屏幕", "不询问验证码和银行卡密码", "小程序不收集手机号", "活动全程不收取任何费用"], 1):
        privacy.add("bullet", x=24, y=66 + i * 30, w=162, h=24, num=str(i), text=line, color=COLORS["coral"], small=True)
    arts.append(privacy)

    checkin = poster_base("checkin-table-sign-a4", "签到台桌牌", 210, 297, "A4 210mm x 297mm", 3, 12, "签到台/入口接待桌牌。")
    checkin.add("text", x=105, y=38, text="签到与咨询", size=20, fill=COLORS["red"], weight="bold", anchor="middle")
    checkin.add("text", x=105, y=62, text="欢迎参加金融防骗反诈公益日", size=9, fill=COLORS["muted"], anchor="middle")
    for i, line in enumerate(["领取活动任务卡", "确认 A/B/C 区位置", "老人可申请志愿者陪同", "活动不收取任何费用"], 1):
        checkin.add("bullet", x=22, y=84 + i * 34, w=166, h=26, num=str(i), text=line, color=COLORS["mint"], small=True)
    add_duck(checkin, 134, 220, 50)
    arts.append(checkin)

    gift_desk = poster_base("gift-redemption-table-sign-a4", "礼品兑换桌牌", 210, 297, "A4 210mm x 297mm", 3, 12, "礼品兑换台桌牌。")
    gift_desk.add("text", x=105, y=38, text="盖章领奖处", size=20, fill=COLORS["red"], weight="bold", anchor="middle")
    gift_desk.add("panel", x=26, y=78, w=158, h=65, title="领奖条件", lines=["完成5题闯关", "出示成绩页或任务卡"], accent=COLORS["gold"])
    gift_desk.add("panel", x=26, y=160, w=158, h=65, title="现场规则", lines=["每人限领一份", "礼品以现场为准"], accent=COLORS["coral"])
    gift_desk.add("text", x=105, y=252, text="不收手机号，不登记隐私", size=10, fill=COLORS["muted"], weight="bold", anchor="middle")
    arts.append(gift_desk)

    queue = poster_base("queue-guide-sign-a4", "排队提示牌", 210, 297, "A4 210mm x 297mm", 3, 12, "C 区排队与等候提示牌。")
    queue.add("text", x=105, y=36, text="C区扫码闯关排队提示", size=17, fill=COLORS["red"], weight="bold", anchor="middle")
    add_process(queue, 28, 82, 154, ["扫码", "答题", "看等级", "盖章"])
    for i, line in enumerate(["请提前打开微信扫一扫", "不会操作可举手找志愿者", "排队超过10人启用纸质卡", "请勿拍摄他人手机屏幕"], 1):
        queue.add("bullet", x=22, y=126 + i * 32, w=166, h=24, num=str(i), text=line, color=COLORS["sky"], small=True)
    arts.append(queue)

    fallback = poster_base("fallback-paper-quiz-a4", "纸质兜底答题卡", 210, 297, "A4 210mm x 297mm", 3, 12, "网络异常/排队超10人时启用的纸质答题卡。")
    fallback.add("text", x=105, y=27, text="真的假的鸭 纸质兜底答题卡", size=14, fill=COLORS["red"], weight="bold", anchor="middle")
    fallback.add("text", x=105, y=43, text="网络异常或排队较长时使用，完成后人工核销", size=7, fill=COLORS["muted"], anchor="middle")
    quiz_lines = ["验证码能告诉客服吗？", "96110 来电要接听吗？", "公检法有安全账户吗？", "屏幕共享要停吗？", "转账前要先核实吗？"]
    y = 65
    for i, line in enumerate(quiz_lines, 1):
        fallback.add("text", x=18, y=y, text=f"{i}. {line}", size=8.5, fill=COLORS["ink"], weight="bold", anchor="start")
        fallback.add("circle", cx=128, cy=y - 2, r=5, fill=COLORS["white"], stroke=COLORS["green"], sw=0.8)
        fallback.add("text", x=139, y=y + 1, text="真", size=7, fill=COLORS["green"], weight="bold", anchor="start")
        fallback.add("circle", cx=162, cy=y - 2, r=5, fill=COLORS["white"], stroke=COLORS["coral"], sw=0.8)
        fallback.add("text", x=173, y=y + 1, text="假", size=7, fill=COLORS["coral"], weight="bold", anchor="start")
        fallback.add("line", x1=18, y1=y + 12, x2=190, y2=y + 12, stroke="#E8B769", sw=0.5)
        y += 32
    fallback.add("rect", x=24, y=234, w=162, h=34, fill=COLORS["white"], stroke=COLORS["gold"], sw=1)
    fallback.add("text", x=105, y=254, text="人工核销盖章处", size=10, fill=COLORS["red"], weight="bold", anchor="middle")
    arts.append(fallback)

    score_board = poster_base("miniprogram-score-page-board-a4", "小程序成绩页交付板", 210, 297, "A4 210mm x 297mm", 3, 12, "小程序成绩页视觉和字段确认板。")
    score_board.add("text", x=105, y=28, text="小程序成绩页", size=17, fill=COLORS["red"], weight="bold", anchor="middle")
    score_board.add("rect", x=54, y=50, w=102, h=180, fill=COLORS["white"], stroke=COLORS["gold"], sw=1.4)
    score_board.add("text", x=105, y=74, text="真的假的鸭", size=10, fill=COLORS["red"], weight="bold", anchor="middle")
    score_board.add("circle", cx=105, cy=108, r=24, fill=COLORS["yellow"], stroke=COLORS["gold"], sw=1)
    score_board.add("text", x=105, y=115, text="5/5", size=18, fill=COLORS["red"], weight="bold", anchor="middle")
    score_board.add("pill", x=72, y=142, w=66, h=18, fill=COLORS["coral"], text="反诈守护官", text_fill=COLORS["white"], text_size=7)
    score_board.add("text", x=105, y=179, text="凭此页盖章领奖", size=9, fill=COLORS["ink"], weight="bold", anchor="middle")
    score_board.add("rect", x=75, y=194, w=60, h=22, fill=COLORS["white"], stroke=COLORS["coral"], sw=1, dash="4 3")
    score_board.add("text", x=105, y=209, text="核销章位", size=7, fill=COLORS["muted"], anchor="middle")
    score_board.add("text", x=105, y=254, text="字段：答对题数 / 等级 / 盖章领奖提示 / 再玩一次", size=7, fill=COLORS["muted"], anchor="middle")
    arts.append(score_board)

    verify = poster_base("score-verification-guide-a4", "成绩页核销说明", 210, 297, "A4 210mm x 297mm", 3, 12, "C 区核销盖章处说明牌。")
    verify.add("text", x=105, y=36, text="工作人员核销三步", size=18, fill=COLORS["red"], weight="bold", anchor="middle")
    for i, line in enumerate(["看成绩页：确认已完成5题", "看等级：任一等级均可领奖", "盖章后：提醒每人限领一份"], 1):
        verify.add("bullet", x=22, y=70 + i * 38, w=166, h=28, num=str(i), text=line, color=COLORS["coral"], small=True)
    verify.add("panel", x=28, y=220, w=154, h=42, title="不要做", lines=["不拍屏幕", "不登记手机号"], accent=COLORS["gold"])
    arts.append(verify)

    host = poster_base("host-cue-card-a5", "主持手卡", 148, 210, "A5 148mm x 210mm", 3, 8, "主持人/讲演人员手卡。")
    host.add("text", x=74, y=22, text="主持转场手卡", size=13, fill=COLORS["red"], weight="bold", anchor="middle")
    host.add("panel", x=14, y=42, w=120, h=42, title="开场", lines=["守护钱袋子", "先停一下再核实"], accent=COLORS["gold"])
    host.add("panel", x=14, y=92, w=120, h=42, title="互动", lines=["真还是假", "请举牌作答"], accent=COLORS["sky"])
    host.add("panel", x=14, y=142, w=120, h=42, title="收束", lines=["96110要接", "验证码不给"], accent=COLORS["mint"])
    arts.append(host)

    consent = poster_base("video-consent-sign-a4", "短视频拍摄授权提示", 210, 297, "A4 210mm x 297mm", 3, 12, "B 区短视频拍摄提示牌。")
    consent.add("text", x=105, y=36, text="短视频拍摄提示", size=18, fill=COLORS["red"], weight="bold", anchor="middle")
    for i, line in enumerate(["拍摄前请先征得本人同意", "不拍身份证、银行卡、验证码", "不拍他人手机屏幕", "不愿出镜可选择手举牌"], 1):
        consent.add("bullet", x=22, y=70 + i * 36, w=166, h=26, num=str(i), text=line, color=COLORS["blue"], small=True)
    arts.append(consent)

    briefing = poster_base("staff-briefing-board-a3", "工作人员总提示", 420, 297, "A3 横版 420mm x 297mm", 3, 12, "工作人员集合处/后台培训提示。")
    briefing.add("text", x=210, y=36, text="活动执行安全总提示", size=22, fill=COLORS["red"], weight="bold", anchor="middle")
    briefing.add("panel", x=25, y=72, w=115, h=82, title="隐私", lines=["不代输密码", "不拍手机屏幕"], accent=COLORS["coral"])
    briefing.add("panel", x=153, y=72, w=115, h=82, title="秩序", lines=["队伍超10人", "切纸质卡"], accent=COLORS["sky"])
    briefing.add("panel", x=281, y=72, w=115, h=82, title="收费", lines=["全程免费", "异常立即上报"], accent=COLORS["gold"])
    briefing.add("panel", x=85, y=178, w=115, h=62, title="核销", lines=["看成绩页", "盖章领奖"], accent=COLORS["mint"])
    briefing.add("panel", x=220, y=178, w=115, h=62, title="应急", lines=["110报警", "96110咨询"], accent=COLORS["coral"])
    arts.append(briefing)

    qr_check = poster_base("qr-replacement-checklist-a4", "二维码替换清单", 210, 297, "A4 210mm x 297mm", 3, 12, "广告公司核版/执行方验收用二维码替换清单。")
    qr_check.add("text", x=105, y=32, text="二维码替换清单", size=18, fill=COLORS["red"], weight="bold", anchor="middle")
    qr_check.add("text", x=105, y=52, text="印前逐项确认，不作为对外物料", size=8, fill=COLORS["muted"], anchor="middle")
    qr_items = ["C区易拉宝小程序码", "C区扫码桌牌小程序码", "A2海报活动码", "手机支架卡面二维码", "现场备用码打印件"]
    y = 82
    for i, line in enumerate(qr_items, 1):
        qr_check.add("rect", x=22, y=y - 11, w=10, h=10, fill=COLORS["white"], stroke=COLORS["gold"], sw=0.8)
        qr_check.add("text", x=39, y=y, text=f"{i}. {line}", size=8.5, fill=COLORS["ink"], weight="bold", anchor="start")
        qr_check.add("text", x=39, y=y + 16, text="已替换 / 已真机扫码 / 已核对跳转页面", size=6.5, fill=COLORS["muted"], anchor="start")
        y += 38
    arts.append(qr_check)

    handheld = poster_base("handheld-signs-a3", "手举牌合集", 420, 297, "A3 420mm x 297mm", 3, 12, "可裁切手举牌合集。")
    labels = [("真", COLORS["green"]), ("假", COLORS["coral"]), ("停一下", COLORS["gold"]), ("验证码不给", COLORS["sky"])]
    for i, (label, color) in enumerate(labels):
        x = 30 + (i % 2) * 200
        y = 35 + (i // 2) * 125
        handheld.add("pill", x=x, y=y, w=165, h=86, fill=color, text=label, text_fill=COLORS["white"], text_size=26)
    arts.append(handheld)

    frame = poster_base("photo-frame-600x900", "拍照框", 600, 900, "异形拍照框参考 600mm x 900mm", 5, 30, "拍照框，中央留空裁切。")
    frame.add("text", x=300, y=95, text="我完成了真的假的鸭挑战", size=38, fill=COLORS["red"], weight="bold", anchor="middle")
    frame.add("rect", x=70, y=175, w=460, h=520, fill="none", stroke=COLORS["coral"], sw=8, dash="18 10")
    frame.add("text", x=300, y=770, text="停一下 · 辨真伪 · 守护钱袋子", size=30, fill=COLORS["ink"], weight="bold", anchor="middle")
    add_duck(frame, 420, 710, 120)
    arts.append(frame)

    sticker = poster_base("gift-sticker-sheet-a5", "礼品贴纸版", 148, 210, "A5 148mm x 210mm", 3, 8, "贴纸/钥匙扣图案参考。")
    sticker.add("text", x=74, y=22, text="真的假的鸭 贴纸版", size=12, fill=COLORS["red"], weight="bold", anchor="middle")
    sticker_items = [("停一下", 38, 55, COLORS["gold"]), ("验证码不给", 108, 55, COLORS["coral"]), ("96110", 38, 110, COLORS["sky"]), ("真", 108, 110, COLORS["green"]), ("假", 38, 165, COLORS["coral"])]
    for label, cx, cy, color in sticker_items:
        sticker.add("circle", cx=cx, cy=cy, r=22, fill=color)
        sticker.add("text", x=cx, y=cy + 3, text=label, size=7 if len(label) > 4 else 13, fill=COLORS["white"], weight="bold", anchor="middle")
    add_duck(sticker, 92, 146, 42)
    arts.append(sticker)

    merch = poster_base("merch-print-sheet-a3", "礼品印刷母版", 420, 297, "A3 420mm x 297mm", 3, 12, "扇子、帆布袋、纸巾盒、钥匙扣等礼品印刷文字与图案母版。")
    merch.add("text", x=210, y=40, text="真的假的鸭 礼品物料母版", size=22, fill=COLORS["red"], weight="bold", anchor="middle")
    merch.add("panel", x=30, y=75, w=165, h=80, title="扇子 / 帆布袋", lines=["真的假的鸭", "守护钱袋子"], accent=COLORS["gold"])
    merch.add("panel", x=225, y=75, w=165, h=80, title="纸巾盒 / 手机支架", lines=["停一下", "验证码不给", "96110"], accent=COLORS["coral"])
    merch.add("panel", x=30, y=180, w=165, h=70, title="钥匙扣", lines=["停一下", "96110"], accent=COLORS["sky"])
    merch.add("panel", x=225, y=180, w=165, h=70, title="贴纸", lines=["真 / 假", "闯关达人"], accent=COLORS["mint"])
    arts.append(merch)

    poster = poster_base("activity-poster-a2", "A2活动海报", 420, 594, "A2 420mm x 594mm", 5, 18, "社区/校园张贴活动海报。")
    add_title(poster, "守护钱袋子", "金融防骗反诈公益日", y=62)
    add_duck(poster, 38, 122, 122)
    poster.add("text", x=245, y=168, text="上午微课堂与情景剧", size=22, fill=COLORS["ink"], weight="bold", anchor="middle")
    poster.add("text", x=245, y=204, text="下午 A/B/C 三区互动体验", size=18, fill=COLORS["muted"], anchor="middle")
    poster.add("panel", x=40, y=265, w=120, h=92, title="A区 防骗驿站", lines=["手机安全", "银行咨询"], accent=COLORS["mint"])
    poster.add("panel", x=180, y=265, w=120, h=92, title="B区 青春盾牌", lines=["剧本互动", "短视频"], accent=COLORS["sky"])
    poster.add("panel", x=320, y=265, w=80, h=92, title="C区", lines=["扫码闯关", "盖章领奖"], accent=COLORS["coral"])
    add_qr(poster, 146, 395, 128, "活动二维码占位")
    poster.add("text", x=210, y=550, text="活动不收取任何费用 · 遇到可疑情况请找工作人员", size=12, fill=COLORS["muted"], anchor="middle")
    arts.append(poster)

    qr_table = poster_base("c-zone-qr-table-sign-a4", "C区扫码桌牌", 210, 297, "A4 210mm x 297mm", 3, 12, "C 区桌面扫码台牌。")
    qr_table.add("text", x=105, y=34, text="真的假的鸭 扫码闯关", size=18, fill=COLORS["red"], weight="bold", anchor="middle")
    qr_table.add("text", x=105, y=56, text="5题挑战 · 即时反馈 · 成绩页盖章领奖", size=8.5, fill=COLORS["muted"], anchor="middle")
    add_qr(qr_table, 55, 82, 100, "小程序码占位")
    add_process(qr_table, 28, 220, 154, ["扫码", "答题", "看等级", "领奖"])
    arts.append(qr_table)

    table_signs = [
        ("a-zone-phone-table-sign-a4", "手机安全门诊", ["手机有疑问，先停一下", "工作人员只指导，不代输密码", "不拍摄手机屏幕"], COLORS["green"]),
        ("a-zone-bank-table-sign-a4", "银行咨询台", ["转账前先核实", "银行卡验证码不给任何人", "官方渠道咨询更稳妥"], COLORS["gold"]),
    ]
    for slug, title, lines, color in table_signs:
        sign = poster_base(slug, title, 210, 297, "A4 210mm x 297mm", 3, 12, f"{title}桌牌。")
        sign.add("text", x=105, y=42, text=title, size=20, fill=COLORS["red"], weight="bold", anchor="middle")
        y = 88
        for i, line in enumerate(lines, 1):
            sign.add("bullet", x=22, y=y, w=166, h=31, num=str(i), text=line, color=color, small=True)
            y += 48
        add_duck(sign, 132, 214, 54)
        arts.append(sign)

    stamp = poster_base("stamp-design-sheet-a4", "印章图样", 210, 297, "A4 210mm x 297mm", 3, 12, "闯关章与人工核销章图样说明。")
    stamp.add("text", x=105, y=34, text="真的假的鸭 印章图样", size=18, fill=COLORS["red"], weight="bold", anchor="middle")
    stamp_specs = [("闯关达人", 62, 100), ("人工核销", 148, 100), ("盖章领奖", 62, 198), ("工作人员确认", 148, 198)]
    for label, cx, cy in stamp_specs:
        stamp.add("circle", cx=cx, cy=cy, r=34, fill=COLORS["white"], stroke=COLORS["coral"], sw=2, dash="4 3")
        stamp.add("text", x=cx, y=cy - 4, text=label, size=9, fill=COLORS["red"], weight="bold", anchor="middle")
        stamp.add("text", x=cx, y=cy + 13, text="真的假的鸭", size=5.5, fill=COLORS["muted"], anchor="middle")
    stamp.add("text", x=105, y=265, text="建议实物直径 35-45mm，红色印油，文字以广告公司刻章稿为准", size=7, fill=COLORS["muted"], anchor="middle")
    arts.append(stamp)

    badge = poster_base("volunteer-badge-90x120", "志愿者胸牌", 90, 120, "胸牌 90mm x 120mm", 3, 7, "志愿者工作牌。")
    badge.add("text", x=45, y=16, text="志愿者", size=12, fill=COLORS["red"], weight="bold", anchor="middle")
    badge.add("text", x=45, y=31, text="防骗陪伴员", size=7, fill=COLORS["muted"], anchor="middle")
    add_duck(badge, 27, 42, 35)
    badge.add("rect", x=14, y=88, w=62, h=13, fill=COLORS["white"], stroke=COLORS["gold"], sw=0.8)
    badge.add("text", x=45, y=98, text="姓名：________", size=5.5, fill=COLORS["ink"], anchor="middle")
    arts.append(badge)

    fan = poster_base("gift-fan-print-420x210", "广告扇印刷稿", 420, 210, "扇面参考 420mm x 210mm", 3, 12, "广告扇印刷正面参考。")
    fan.add("text", x=210, y=42, text="真的假的鸭", size=30, fill=COLORS["red"], weight="bold", anchor="middle")
    fan.add("text", x=210, y=74, text="停一下 · 验证码不给 · 96110 要接", size=16, fill=COLORS["ink"], weight="bold", anchor="middle")
    add_duck(fan, 56, 76, 72)
    add_chip_row(fan, 174, 118, ["真", "假", "守护钱袋子"], "mint")
    arts.append(fan)

    tote = poster_base("gift-tote-print-a4", "帆布袋印刷稿", 210, 297, "A4 图案区 210mm x 297mm", 3, 12, "帆布袋单色/双色印刷图案区。")
    tote.add("text", x=105, y=48, text="真的假的鸭", size=22, fill=COLORS["red"], weight="bold", anchor="middle")
    add_duck(tote, 62, 78, 84)
    tote.add("text", x=105, y=205, text="守护钱袋子", size=17, fill=COLORS["ink"], weight="bold", anchor="middle")
    tote.add("text", x=105, y=232, text="停一下 · 辨真伪 · 护自己", size=9, fill=COLORS["muted"], anchor="middle")
    arts.append(tote)

    notebook = poster_base("gift-notebook-cover-a5", "笔记本封面", 148, 210, "A5 148mm x 210mm", 3, 8, "笔记本封面。")
    notebook.add("text", x=74, y=32, text="防骗小笔记", size=15, fill=COLORS["red"], weight="bold", anchor="middle")
    add_duck(notebook, 47, 55, 54)
    notebook.add("panel", x=20, y=130, w=108, h=42, title="记住三句话", lines=["验证码不给", "转账先核实"], accent=COLORS["mint"])
    arts.append(notebook)

    tissue = poster_base("gift-tissue-box-sleeve-240x120", "纸巾盒套", 240, 120, "纸巾盒套展开参考 240mm x 120mm", 3, 8, "纸巾盒外套展开参考。")
    tissue.add("text", x=70, y=36, text="停一下", size=20, fill=COLORS["red"], weight="bold", anchor="middle")
    tissue.add("text", x=70, y=66, text="验证码不给", size=15, fill=COLORS["ink"], weight="bold", anchor="middle")
    tissue.add("text", x=170, y=52, text="96110", size=22, fill=COLORS["blue"], weight="bold", anchor="middle")
    add_duck(tissue, 176, 70, 36)
    arts.append(tissue)

    stand = poster_base("gift-phone-stand-card-a6", "手机支架卡面", 105, 148, "A6 105mm x 148mm", 3, 7, "手机支架卡面/包装卡。")
    stand.add("text", x=52.5, y=22, text="扫码前先看一眼", size=10, fill=COLORS["red"], weight="bold", anchor="middle")
    add_qr(stand, 31, 42, 43, "二维码占位")
    stand.add("text", x=52.5, y=105, text="陌生链接不点", size=9, fill=COLORS["ink"], weight="bold", anchor="middle")
    arts.append(stand)

    keychain = poster_base("gift-keychain-round-sheet-a5", "钥匙扣圆牌", 148, 210, "A5 钥匙扣圆牌拼版", 3, 8, "60mm 圆形钥匙扣图案拼版。")
    items = [("停一下", 43, 62, COLORS["gold"]), ("96110", 105, 62, COLORS["sky"]), ("真", 43, 130, COLORS["green"]), ("假", 105, 130, COLORS["coral"])]
    for label, cx, cy, color in items:
        keychain.add("circle", cx=cx, cy=cy, r=25, fill=color)
        keychain.add("text", x=cx, y=cy + 4, text=label, size=9 if len(label) > 3 else 16, fill=COLORS["white"], weight="bold", anchor="middle")
    keychain.add("text", x=74, y=188, text="建议实物直径 50-60mm", size=6, fill=COLORS["muted"], anchor="middle")
    arts.append(keychain)

    return arts


def draw_text_pdf(c: canvas.Canvas, x, y, text, size, fill, weight="regular", anchor="start", scale=1):
    font = "DengXian-Bold" if weight == "bold" else "DengXian"
    c.setFont(font, size * scale)
    c.setFillColor(HexColor(fill))
    width = pdfmetrics.stringWidth(str(text), font, size * scale)
    tx = x * scale * mm
    if anchor == "middle":
        tx -= width / 2
    c.saveState()
    c.translate(tx, y * scale * mm)
    c.scale(1, -1)
    c.drawString(0, 0, str(text))
    c.restoreState()


def render_pdf(art: Artwork):
    scale = 0.1 if max(art.width_mm, art.height_mm) > 1000 else 1
    pdf_path = PDF_DIR / f"{art.slug}.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(art.width_mm * scale * mm, art.height_mm * scale * mm))
    c.saveState()
    c.translate(0, art.height_mm * scale * mm)
    c.scale(1, -1)
    for e in art.elements:
        draw_pdf_element(c, e, scale)
    c.restoreState()
    c.setFont("DengXian", max(6, 10 * scale))
    c.setFillColor(HexColor(COLORS["muted"]))
    c.drawString(art.safe_mm * scale * mm, art.safe_mm * scale * mm, f"{art.final_size} | bleed {art.bleed_mm}mm | safe {art.safe_mm}mm")
    c.save()


def draw_pdf_element(c: canvas.Canvas, e: Element, scale: float):
    a = e.attrs
    if e.kind == "rect":
        if a.get("fill") != "none":
            c.setFillColor(HexColor(a.get("fill", COLORS["white"])))
            fill = 1
        else:
            fill = 0
        stroke = 1 if a.get("stroke") and a.get("stroke") != "none" else 0
        if stroke:
            c.setStrokeColor(HexColor(a["stroke"]))
            c.setLineWidth(a.get("sw", 1) * scale)
        c.rect(a["x"] * scale * mm, a["y"] * scale * mm, a["w"] * scale * mm, a["h"] * scale * mm, fill=fill, stroke=stroke)
    elif e.kind == "circle":
        c.setFillColor(HexColor(a.get("fill", COLORS["white"])))
        c.setStrokeColor(HexColor(a.get("stroke", a.get("fill", COLORS["white"]))))
        c.setLineWidth(a.get("sw", 0) * scale)
        c.circle(a["cx"] * scale * mm, a["cy"] * scale * mm, a["r"] * scale * mm, fill=1, stroke=1 if a.get("stroke") else 0)
    elif e.kind == "line":
        c.setStrokeColor(HexColor(a["stroke"]))
        c.setLineWidth(a["sw"] * scale)
        c.line(a["x1"] * scale * mm, a["y1"] * scale * mm, a["x2"] * scale * mm, a["y2"] * scale * mm)
    elif e.kind == "text":
        draw_text_pdf(c, a["x"], a["y"], a["text"], a["size"], a.get("fill", COLORS["ink"]), a.get("weight", "regular"), a.get("anchor", "start"), scale)
    elif e.kind == "pill":
        c.setFillColor(HexColor(a["fill"]))
        c.roundRect(a["x"] * scale * mm, a["y"] * scale * mm, a["w"] * scale * mm, a["h"] * scale * mm, a["h"] * scale * mm / 2, fill=1, stroke=0)
        draw_text_pdf(c, a["x"] + a["w"] / 2, a["y"] + a["h"] * 0.62, a["text"], a["text_size"], a["text_fill"], "bold", "middle", scale)
    elif e.kind == "duck":
        draw_duck_pdf(c, a["x"], a["y"], a["s"], scale)
    elif e.kind == "image":
        c.drawImage(ImageReader(a["path"]), a["x"] * scale * mm, a["y"] * scale * mm, a["w"] * scale * mm, a["h"] * scale * mm, preserveAspectRatio=True, anchor="c", mask="auto")
    elif e.kind == "qr":
        draw_qr_pdf(c, a["x"], a["y"], a["size"], a["label"], scale)
    elif e.kind == "panel":
        draw_panel_pdf(c, a, scale)
    elif e.kind == "bullet":
        draw_bullet_pdf(c, a, scale)
    elif e.kind == "zone_row":
        draw_zone_pdf(c, a, scale)
    elif e.kind == "arrow":
        c.setFillColor(HexColor(a["color"]))
        x, y, s = a["x"], a["y"], a["size"]
        pts = [(x-s/2, y-s/4), (x+s/5, y-s/4), (x+s/5, y-s/2), (x+s/2, y), (x+s/5, y+s/2), (x+s/5, y+s/4), (x-s/2, y+s/4)]
        p = c.beginPath()
        p.moveTo(pts[0][0] * scale * mm, pts[0][1] * scale * mm)
        for px, py in pts[1:]:
            p.lineTo(px * scale * mm, py * scale * mm)
        p.close()
        c.drawPath(p, fill=1, stroke=0)


def draw_duck_pdf(c, x, y, s, scale):
    c.setFillColor(HexColor(COLORS["duck"]))
    c.ellipse((x+s*0.12)*scale*mm, (y+s*0.30)*scale*mm, (x+s*0.84)*scale*mm, (y+s*0.94)*scale*mm, fill=1, stroke=0)
    c.circle((x+s*0.44)*scale*mm, (y+s*0.34)*scale*mm, s*0.26*scale*mm, fill=1, stroke=0)
    c.setFillColor(HexColor(COLORS["beak"]))
    c.ellipse((x+s*0.26)*scale*mm, (y+s*0.34)*scale*mm, (x+s*0.62)*scale*mm, (y+s*0.48)*scale*mm, fill=1, stroke=0)
    c.setFillColor(HexColor(COLORS["ink"]))
    c.circle((x+s*0.34)*scale*mm, (y+s*0.30)*scale*mm, s*0.026*scale*mm, fill=1, stroke=0)
    c.circle((x+s*0.53)*scale*mm, (y+s*0.30)*scale*mm, s*0.026*scale*mm, fill=1, stroke=0)


def draw_qr_pdf(c, x, y, size, label, scale):
    c.setFillColor(HexColor(COLORS["white"]))
    c.setStrokeColor(HexColor(COLORS["blue"]))
    c.setLineWidth(size * 0.025 * scale)
    c.roundRect(x*scale*mm, y*scale*mm, size*scale*mm, size*scale*mm, size*0.08*scale*mm, fill=1, stroke=1)
    c.setFillColor(HexColor(COLORS["ink"]))
    cell = size / 9
    for i in range(9):
        for j in range(9):
            if (i * j + i + j) % 3 == 0 or (i in (1, 7) and j in (1, 7)):
                c.rect((x+i*cell+cell*0.2)*scale*mm, (y+j*cell+cell*0.2)*scale*mm, cell*0.62*scale*mm, cell*0.62*scale*mm, fill=1, stroke=0)
    draw_text_pdf(c, x + size/2, y + size*1.18, label, size*0.085, COLORS["muted"], "regular", "middle", scale)


def draw_panel_pdf(c, a, scale):
    c.setFillColor(HexColor(COLORS["white"]))
    c.setStrokeColor(HexColor(a["accent"]))
    c.setLineWidth(max(1.2, a["w"] * 0.01) * scale)
    c.roundRect(a["x"]*scale*mm, a["y"]*scale*mm, a["w"]*scale*mm, a["h"]*scale*mm, min(a["w"], a["h"])*0.06*scale*mm, fill=1, stroke=1)
    draw_text_pdf(c, a["x"]+a["w"]*0.08, a["y"]+a["h"]*0.22, a["title"], a["h"]*0.13, COLORS["red"], "bold", "start", scale)
    for i, line in enumerate(a["lines"]):
        draw_text_pdf(c, a["x"]+a["w"]*0.08, a["y"]+a["h"]*(0.45+i*0.2), "· "+line, a["h"]*0.095, COLORS["ink"], "regular", "start", scale)


def draw_bullet_pdf(c, a, scale):
    c.setFillColor(HexColor(COLORS["white"]))
    c.setStrokeColor(HexColor(a["color"]))
    c.setLineWidth(max(1, a["h"]*0.05)*scale)
    c.roundRect(a["x"]*scale*mm, a["y"]*scale*mm, a["w"]*scale*mm, a["h"]*scale*mm, a["h"]*0.22*scale*mm, fill=1, stroke=1)
    c.setFillColor(HexColor(a["color"]))
    c.circle((a["x"]+a["h"]*0.48)*scale*mm, (a["y"]+a["h"]*0.5)*scale*mm, a["h"]*0.33*scale*mm, fill=1, stroke=0)
    draw_text_pdf(c, a["x"]+a["h"]*0.48, a["y"]+a["h"]*0.62, a["num"], a["h"]*0.42, COLORS["white"], "bold", "middle", scale)
    draw_text_pdf(c, a["x"]+a["h"]*0.95, a["y"]+a["h"]*0.62, a["text"], a["h"]*(0.36 if a.get("small") else 0.32), COLORS["ink"], "bold", "start", scale)


def draw_zone_pdf(c, a, scale):
    c.setFillColor(HexColor(COLORS["white"]))
    c.setStrokeColor(HexColor(a["color"]))
    c.setLineWidth(6 * scale)
    c.roundRect(a["x"]*scale*mm, a["y"]*scale*mm, a["w"]*scale*mm, a["h"]*scale*mm, 28*scale*mm, fill=1, stroke=1)
    c.setFillColor(HexColor(a["color"]))
    c.circle((a["x"]+70)*scale*mm, (a["y"]+a["h"]/2)*scale*mm, 55*scale*mm, fill=1, stroke=0)
    draw_text_pdf(c, a["x"]+70, a["y"]+a["h"]/2+22, a["code"], 70, COLORS["white"], "bold", "middle", scale)
    draw_text_pdf(c, a["x"]+155, a["y"]+92, a["name"], 46, COLORS["ink"], "bold", "start", scale)
    draw_text_pdf(c, a["x"]+155, a["y"]+155, a["desc"], 26, COLORS["muted"], "regular", "start", scale)


def render_png_preview(art: Artwork):
    max_px = 2200
    px_per_mm = max_px / max(art.width_mm, art.height_mm)
    w, h = max(1, int(art.width_mm * px_per_mm)), max(1, int(art.height_mm * px_per_mm))
    img = Image.new("RGB", (w, h), COLORS["cream"])
    d = ImageDraw.Draw(img)
    d._image = img
    for e in art.elements:
        draw_pil_element(d, e, px_per_mm)
    img.save(PNG_DIR / f"{art.slug}.png", "PNG", optimize=True)


def pil_font(size_mm, px_per_mm, bold=False):
    size = max(8, int(size_mm * px_per_mm))
    return ImageFont.truetype(PIL_FONT_BOLD if bold else PIL_FONT_REGULAR, size=size)


def draw_text_pil(d, x, y, text, size, fill, px_per_mm, weight="regular", anchor="start"):
    font = pil_font(size, px_per_mm, weight == "bold")
    tx, ty = x * px_per_mm, y * px_per_mm
    if anchor == "middle":
        bbox = d.textbbox((0, 0), str(text), font=font)
        tx -= (bbox[2] - bbox[0]) / 2
    d.text((tx, ty - size * px_per_mm * 0.8), str(text), fill=fill, font=font)


def draw_pil_element(d, e: Element, s: float):
    a = e.attrs
    if e.kind == "rect":
        fill = None if a.get("fill") == "none" else a.get("fill", COLORS["white"])
        outline = None if a.get("stroke") in (None, "none") else a.get("stroke")
        d.rectangle([a["x"]*s, a["y"]*s, (a["x"]+a["w"])*s, (a["y"]+a["h"])*s], fill=fill, outline=outline, width=max(1, int(a.get("sw", 1)*s)))
    elif e.kind == "circle":
        d.ellipse([(a["cx"]-a["r"])*s, (a["cy"]-a["r"])*s, (a["cx"]+a["r"])*s, (a["cy"]+a["r"])*s], fill=a.get("fill"), outline=a.get("stroke"))
    elif e.kind == "text":
        draw_text_pil(d, a["x"], a["y"], a["text"], a["size"], a.get("fill", COLORS["ink"]), s, a.get("weight", "regular"), a.get("anchor", "start"))
    elif e.kind == "pill":
        r = a["h"] * s / 2
        d.rounded_rectangle([a["x"]*s, a["y"]*s, (a["x"]+a["w"])*s, (a["y"]+a["h"])*s], radius=r, fill=a["fill"])
        draw_text_pil(d, a["x"]+a["w"]/2, a["y"]+a["h"]*0.62, a["text"], a["text_size"], a["text_fill"], s, "bold", "middle")
    elif e.kind == "duck":
        x, y, size = a["x"], a["y"], a["s"]
        d.ellipse([(x+size*0.12)*s, (y+size*0.30)*s, (x+size*0.84)*s, (y+size*0.94)*s], fill=COLORS["duck"])
        d.ellipse([(x+size*0.18)*s, (y+size*0.08)*s, (x+size*0.70)*s, (y+size*0.60)*s], fill=COLORS["duck"])
        d.ellipse([(x+size*0.26)*s, (y+size*0.34)*s, (x+size*0.62)*s, (y+size*0.48)*s], fill=COLORS["beak"])
        d.ellipse([(x+size*0.31)*s, (y+size*0.27)*s, (x+size*0.37)*s, (y+size*0.33)*s], fill=COLORS["ink"])
        d.ellipse([(x+size*0.50)*s, (y+size*0.27)*s, (x+size*0.56)*s, (y+size*0.33)*s], fill=COLORS["ink"])
    elif e.kind == "image":
        img = Image.open(a["path"]).convert("RGBA")
        img = img.resize((max(1, int(a["w"] * s)), max(1, int(a["h"] * s))), Image.Resampling.LANCZOS)
        base = getattr(d, "_image", None)
        if base is None:
            return
        base.paste(img, (int(a["x"] * s), int(a["y"] * s)), img)
    elif e.kind == "qr":
        x, y, size = a["x"], a["y"], a["size"]
        d.rounded_rectangle([x*s, y*s, (x+size)*s, (y+size)*s], radius=size*s*0.08, fill=COLORS["white"], outline=COLORS["blue"], width=max(2, int(size*s*0.02)))
        cell = size / 9
        for i in range(9):
            for j in range(9):
                if (i * j + i + j) % 3 == 0 or (i in (1, 7) and j in (1, 7)):
                    d.rectangle([(x+i*cell+cell*0.2)*s, (y+j*cell+cell*0.2)*s, (x+i*cell+cell*0.82)*s, (y+j*cell+cell*0.82)*s], fill=COLORS["ink"])
        draw_text_pil(d, x+size/2, y+size*1.18, a["label"], size*0.085, COLORS["muted"], s, "regular", "middle")
    elif e.kind == "panel":
        d.rounded_rectangle([a["x"]*s, a["y"]*s, (a["x"]+a["w"])*s, (a["y"]+a["h"])*s], radius=min(a["w"], a["h"])*0.06*s, fill=COLORS["white"], outline=a["accent"], width=max(2, int(a["w"]*0.01*s)))
        draw_text_pil(d, a["x"]+a["w"]*0.08, a["y"]+a["h"]*0.22, a["title"], a["h"]*0.13, COLORS["red"], s, "bold")
        for i, line in enumerate(a["lines"]):
            draw_text_pil(d, a["x"]+a["w"]*0.08, a["y"]+a["h"]*(0.45+i*0.2), "· "+line, a["h"]*0.095, COLORS["ink"], s)
    elif e.kind == "bullet":
        d.rounded_rectangle([a["x"]*s, a["y"]*s, (a["x"]+a["w"])*s, (a["y"]+a["h"])*s], radius=a["h"]*0.22*s, fill=COLORS["white"], outline=a["color"], width=max(2, int(a["h"]*0.05*s)))
        d.ellipse([(a["x"]+a["h"]*0.15)*s, (a["y"]+a["h"]*0.17)*s, (a["x"]+a["h"]*0.81)*s, (a["y"]+a["h"]*0.83)*s], fill=a["color"])
        draw_text_pil(d, a["x"]+a["h"]*0.48, a["y"]+a["h"]*0.62, a["num"], a["h"]*0.42, COLORS["white"], s, "bold", "middle")
        draw_text_pil(d, a["x"]+a["h"]*0.95, a["y"]+a["h"]*0.62, a["text"], a["h"]*(0.36 if a.get("small") else 0.32), COLORS["ink"], s, "bold")
    elif e.kind == "zone_row":
        d.rounded_rectangle([a["x"]*s, a["y"]*s, (a["x"]+a["w"])*s, (a["y"]+a["h"])*s], radius=28*s, fill=COLORS["white"], outline=a["color"], width=max(2, int(6*s)))
        d.ellipse([(a["x"]+15)*s, (a["y"]+a["h"]/2-55)*s, (a["x"]+125)*s, (a["y"]+a["h"]/2+55)*s], fill=a["color"])
        draw_text_pil(d, a["x"]+70, a["y"]+a["h"]/2+22, a["code"], 70, COLORS["white"], s, "bold", "middle")
        draw_text_pil(d, a["x"]+155, a["y"]+92, a["name"], 46, COLORS["ink"], s, "bold")
        draw_text_pil(d, a["x"]+155, a["y"]+155, a["desc"], 26, COLORS["muted"], s)
    elif e.kind == "arrow":
        x, y, size = a["x"], a["y"], a["size"]
        pts = [(x-size/2, y-size/4), (x+size/5, y-size/4), (x+size/5, y-size/2), (x+size/2, y), (x+size/5, y+size/2), (x+size/5, y+size/4), (x-size/2, y+size/4)]
        d.polygon([(px*s, py*s) for px, py in pts], fill=a["color"])


def write_readme(arts: list[Artwork]):
    rows = "\n".join(
        f"| `{art.slug}` | {art.title} | {art.final_size} | {art.notes} |"
        for art in arts
    )
    readme = f"""# 真的假的鸭活动物料广告公司交付包

生成日期：2026-06-07

本目录是面向广告公司/喷绘制作方的生产稿包。概念图只用于情绪参考；本包内的 PDF 使用真实中文文字排版、真实尺寸标注和二维码占位。

当前交付共 {len(arts)} 件物料，每件均包含 `pdf-print` 核版 PDF 和 `png-preview` 校对图。

## 目录

- `请先看这个-中文说明.pdf` / `.md`：中文入口说明，给执行统筹、广告公司、现场负责人和礼品供应商先读。
- `中文材料索引.csv`：每个英文文件名对应的中文材料名、用途、使用/确认人和制作确认重点。
- `视觉母题映射板.png`：12 张小鸭方向如何落到主会场、A/B/C 区、礼品和执行安全物料。
- `contact-sheet.png`：47 件物料中文分组总览图。
- `ip-raster-assets/`：由既有小鸭 PNG 概念图生成的栅格插画图块，不是 SVG。
- `pdf-print/`：广告公司核版 PDF。大幅面文件在 PDF 中按 1:10 预览，输出时按文件内标注放大。
- `png-preview/`：快速预览图，不建议直接用于印刷。
- `production-spec.csv`：广告公司报价、下单、物料分发用规格表。
- `production-spec.md`：同一规格表的人工审核版。
- `handoff/`：活动物料交接手册、分区装箱清单、当天布置清单、供应商验收清单、最终信息回填、印前签核和完成度审计。

## 生产注意

- 所有二维码占位必须替换为真实小程序码或活动二维码，并做现场扫码测试。
- 正式印刷前请将字体转曲，或统一使用微软雅黑/思源黑体/黑体。
- 大幅面物料请按 `pdf-print` 文件内标注比例放大输出。二维码占位需由广告公司替换为真实小程序码后重新导出。
- 本包不提供 SVG 或可编辑矢量源文件，避免不同软件打开时出现字体漂移、文字错位、覆盖或坐标翻转。
- AI 概念图只作为情绪参考，不作为正式文字、二维码和生产尺寸依据。
- 颜色当前为 RGB 设计参考，印刷前由供应商按设备转换 CMYK 并打样确认。
- 出血、安全区、放大比例写在每个 PDF 页脚，也写在下表。
- 主办、协同、指导单位名称留给执行方最终确认，不把机构名称放到小鸭徽章或主 IP 标识里。

## 文件清单

| 文件名 | 物料 | 规格 | 说明 |
| --- | --- | --- | --- |
{rows}
"""
    (OUT / "README_VENDOR.md").write_text(readme, encoding="utf-8")


def production_rows(arts: list[Artwork]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for art in arts:
        spec = PRODUCTION_SPEC.get(art.slug)
        if spec is None:
            raise KeyError(f"missing production spec for {art.slug}")
        category, quantity, material, usage, qr, info, proof, note = spec
        rows.append(
            {
                "文件名": f"{art.slug}.pdf",
                "物料": art.title,
                "规格": art.final_size,
                "类别": category,
                "建议数量": quantity,
                "建议材质工艺": material,
                "使用位置": usage,
                "二维码替换": qr,
                "信息替换": info,
                "打样优先级": proof,
                "制作备注": note,
            }
        )
    return rows


def write_production_spec(arts: list[Artwork]):
    rows = production_rows(arts)
    csv_path = OUT / "production-spec.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=SPEC_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    table_rows = "\n".join(
        "| "
        + " | ".join(row[key] for key in SPEC_HEADERS)
        + " |"
        for row in rows
    )
    md = f"""# 真的假的鸭广告公司制作规格表

生成日期：2026-06-07

本表用于广告公司报价、核版、打样、分发和现场布置。`pdf-print/` 是核版主文件，`png-preview/` 仅用于快速校对。正式生产前必须替换真实二维码、确认活动日期/地点/单位信息、转曲、转 CMYK，并至少对二维码类和大幅面类物料打小样。

| {' | '.join(SPEC_HEADERS)} |
| {' | '.join(['---'] * len(SPEC_HEADERS))} |
{table_rows}
"""
    (OUT / "production-spec.md").write_text(md, encoding="utf-8")


def guide_group(category: str) -> str:
    return GROUP_BY_CATEGORY.get(category, "10 其他物料")


def guide_rows(arts: list[Artwork]) -> list[dict[str, str]]:
    spec_rows = production_rows(arts)
    art_by_file = {f"{art.slug}.pdf": art for art in arts}
    rows: list[dict[str, str]] = []
    for idx, spec in enumerate(spec_rows, 1):
        art = art_by_file[spec["文件名"]]
        group = guide_group(spec["类别"])
        rows.append(
            {
                "编号": f"{idx:02d}",
                "分组": group,
                "中文材料名": spec["物料"],
                "英文文件名": art.slug,
                "PDF核版稿": f"pdf-print/{art.slug}.pdf",
                "PNG校对图": f"png-preview/{art.slug}.png",
                "实际用途": MATERIAL_PURPOSES.get(art.slug, art.notes),
                "使用/确认人": OWNER_BY_GROUP.get(group, "执行统筹 / 广告公司"),
                "制作确认重点": f"{spec['使用位置']}；建议数量：{spec['建议数量']}；{spec['制作备注']}",
            }
        )
    return rows


def markdown_cell(value: str) -> str:
    return str(value).replace("|", " / ").replace("\n", " ")


def build_chinese_guide_markdown(arts: list[Artwork], rows: list[dict[str, str]]) -> str:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["分组"], []).append(row)

    group_sections = []
    for group in sorted(grouped):
        table = "\n".join(
            "| "
            + " | ".join(
                markdown_cell(row[key])
                for key in ["编号", "中文材料名", "英文文件名", "实际用途", "使用/确认人", "制作确认重点"]
            )
            + " |"
            for row in grouped[group]
        )
        group_sections.append(
            f"""## {group}

| 编号 | 中文材料名 | 英文文件名 | 实际用途 | 使用/确认人 | 制作确认重点 |
| --- | --- | --- | --- | --- | --- |
{table}
"""
        )

    return f"""# 请先看这个：真的假的鸭活动物料中文说明

生成日期：2026-06-07

这份文档是给执行统筹、广告公司、现场负责人和礼品供应商共同使用的中文入口说明。交付包里的英文文件名用于保持出图脚本、PDF、PNG 和压缩包索引稳定；实际沟通时可以直接看本文档和 `中文材料索引.csv`。

## 这套包到底交付了什么

- 这不是单张 logo，而是一套“守护钱袋子”金融防骗反诈公益日活动物料系统。
- 当前共有 {len(arts)} 件正式物料，每件都有一份 `pdf-print/` 核版 PDF 和一张 `png-preview/` 校对 PNG。
- `pdf-print/` 给广告公司核版、替换真实二维码、转曲、转 CMYK、打样和输出。
- `png-preview/` 给项目组、主办方和现场负责人快速看版式，不建议直接拿去印刷。
- `production-spec.csv` 给广告公司报价、下单、分区装箱和数量核对。
- `handoff/` 里的文件给活动执行用：装箱、布置、验收、最终信息回填、印前签核和完成度审计。

## 先看哪几个文件

1. `请先看这个-中文说明.pdf`：中文总说明，适合开会或转发给非设计人员。
2. `中文材料索引.csv`：每个英文文件名对应的中文材料名、用途、使用人和制作提醒。
3. `视觉母题映射板.png`：12 张小鸭方向如何落到主会场、A/B/C 区、礼品和执行安全物料。
4. `contact-sheet.png`：47 件物料中文分组总览，适合快速扫一遍视觉是否完整。
5. `production-spec.csv`：广告公司报价和下单时看这个。
6. `handoff/final-info-fill-in.pdf`：真实日期、地点、二维码、单位名称、礼品数量等最终信息先填这里。
7. `handoff/print-approval-signoff.pdf`：最终出图前签字确认，签完再排产。

## 印前必须补齐

- 真实小程序码和活动二维码：所有二维码占位都必须替换，并用老人手机、学生手机都扫一次。
- 活动日期、时间、地点、主办/协同/指导单位最终写法：先统一口径，再改进 PDF。
- 礼品数量、领奖规则、印章尺寸：和任务卡、领奖券、兑换桌牌一起确认。
- 广告公司工序：字体转曲、CMYK 转换、大幅面放大比例、小样确认。
- 不使用 SVG 或 AI 概念图承载正式文字、二维码和生产尺寸。

## 材料分组解释

{chr(10).join(group_sections)}
"""


def write_chinese_guide(arts: list[Artwork]):
    rows = guide_rows(arts)

    csv_path = OUT / "中文材料索引.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=GUIDE_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    md = build_chinese_guide_markdown(arts, rows)
    (OUT / "请先看这个-中文说明.md").write_text(md, encoding="utf-8")
    render_chinese_guide_pdf(arts, rows)


def write_handoff_package(arts: list[Artwork]):
    rows = production_rows(arts)
    by_file = {row["文件名"]: row for row in rows}
    packing_rows = [
        ("入口/签到", "checkin-table-sign-a4.pdf", "签到台桌牌", "1-2个", "签到台", "执行统筹", "核对日期地点、签到口径"),
        ("入口/签到", "entrance-banner-8000x700.pdf", "入口横幅", "1-2条", "入口或主通道", "广告公司", "确认悬挂方式和宽度"),
        ("入口/签到", "entrance-wayfinding-800x2000.pdf", "总导视牌", "1个", "入口", "执行统筹", "核对A/B/C实际方向"),
        ("主舞台", "main-stage-backdrop-5000x3000.pdf", "主背景板", "1套", "上午主舞台", "广告公司", "按1:10核版放大输出"),
        ("主舞台", "case-board-01-600x900.pdf - case-board-06-600x900.pdf", "案例展板", "6块", "主会场侧边/通道", "执行统筹", "按编号顺序摆放"),
        ("A区", "zone-a-standee-800x2000.pdf", "A区易拉宝", "1个", "A区入口", "A区负责人", "不遮挡主标题"),
        ("A区", "a-zone-phone-table-sign-a4.pdf", "手机安全门诊桌牌", "1-2个", "手机指导桌", "A区负责人", "桌面避免反光"),
        ("A区", "a-zone-bank-table-sign-a4.pdf", "银行咨询台桌牌", "1-2个", "银行咨询桌", "A区负责人", "按实际单位改名"),
        ("A区", "a-zone-formula-card-a6.pdf", "防骗口诀卡", "200-500张", "A区带走资料", "A区负责人", "开场前分装"),
        ("B区", "zone-b-standee-800x2000.pdf", "B区易拉宝", "1个", "B区入口", "B区负责人", "靠近互动区"),
        ("B区", "b-zone-question-card-a6.pdf", "快问快答题卡", "100-200张", "B区互动桌", "B区负责人", "题卡按轮次分组"),
        ("B区", "handheld-signs-a3.pdf", "手举牌合集", "2-4套", "互动/拍照点", "B区负责人", "裁切后加手柄"),
        ("B区", "video-consent-sign-a4.pdf", "短视频拍摄授权提示", "1-2个", "拍摄点", "B区负责人", "拍摄前口头确认"),
        ("C区", "zone-c-standee-800x2000.pdf", "C区扫码易拉宝", "1-2个", "C区入口/队尾", "C区负责人", "替换真实小程序码"),
        ("C区", "c-zone-qr-table-sign-a4.pdf", "C区扫码桌牌", "2-4个", "扫码桌/队尾", "C区负责人", "真机扫码测试"),
        ("C区", "c-zone-task-card-a5.pdf", "闯关任务卡", "100-300张", "扫码桌", "C区负责人", "与印章大小试盖"),
        ("C区", "fallback-paper-quiz-a4.pdf", "纸质兜底答题卡", "50-100张", "排队超10人/网络异常", "C区负责人", "准备夹板和笔"),
        ("C区", "score-verification-guide-a4.pdf", "成绩页核销说明", "1-2个", "盖章处", "C区负责人", "不记录隐私"),
        ("C区", "stamp-design-sheet-a4.pdf", "印章图样", "1套", "盖章处", "C区负责人", "先试盖任务卡"),
        ("礼品区", "gift-redemption-table-sign-a4.pdf", "礼品兑换桌牌", "1-2个", "礼品兑换台", "礼品负责人", "礼品数量和规则一致"),
        ("礼品区", "gift-*.pdf / merch-print-sheet-a3.pdf", "礼品印刷稿", "按预算", "礼品区", "礼品负责人", "按供应商刀模复核"),
        ("工作人员", "volunteer-badge-90x120.pdf", "志愿者胸牌", "30-60个", "工作人员", "执行统筹", "不放私人手机号"),
        ("工作人员", "volunteer-handcard-a6.pdf", "志愿者手卡", "30-60张", "工作人员", "执行统筹", "活动前统一发放"),
        ("工作人员", "staff-briefing-board-a3.pdf", "工作人员总提示", "1-2张", "后台/集合处", "执行统筹", "活动前5分钟复核"),
    ]

    setup_rows = [
        ("T-7天", "广告公司", "完成二维码替换、字体转曲、CMYK转换和小样输出", "二维码类/大幅面类必须真机扫码和看样"),
        ("T-3天", "执行统筹", "按 production-spec.csv 确认数量和材质", "未确认项不得直接大货"),
        ("T-1天", "执行统筹", "按 zone-packing-list.csv 分区装箱", "每箱外贴区域名和负责人"),
        ("活动日 08:00", "广告公司/场务", "主背景板、横幅、总导视和分区易拉宝进场", "先搭大件，再摆桌牌"),
        ("活动日 09:00", "各区负责人", "A/B/C区桌牌、卡片、印章、手举牌、礼品到位", "C区先做扫码压力测试"),
        ("活动日 09:30", "主持/志愿者", "按工作人员总提示完成5分钟口径复核", "重点确认不代输密码、不拍屏幕"),
        ("活动日 12:30", "C区负责人", "检查网络、备用纸质答题卡、盖章和礼品数量", "排队超10人即启用兜底卡"),
        ("活动日 16:00", "执行统筹", "按装箱清单回收可复用物料", "记录损耗和下次复用建议"),
    ]

    acceptance_rows = [
        ("二维码", "zone-c-standee-800x2000.pdf", "已替换真实小程序码，老人手机和学生手机均可扫码"),
        ("二维码", "c-zone-qr-table-sign-a4.pdf", "已替换真实小程序码，扫码后进入5题闯关页"),
        ("二维码", "activity-poster-a2.pdf", "已替换活动二维码或小程序码，并核对跳转页面"),
        ("文字", "全部PDF", "活动日期、地点、单位写法已最终确认"),
        ("印前", "全部PDF", "供应商已转曲、转CMYK，输出前已打印小样"),
        ("大幅面", "main-stage-backdrop-5000x3000.pdf", "按1:10核版放大输出，尺寸和桁架净空一致"),
        ("核销", "c-zone-task-card-a5.pdf / stamp-design-sheet-a4.pdf", "印章大小和任务卡章位匹配，已试盖"),
        ("隐私", "privacy-desk-sign-a4.pdf / volunteer-handcard-a6.pdf", "现场口径不收手机号、不代输密码、不拍手机屏幕"),
    ]
    final_info_rows = [
        ("活动日期", "全部含日期/活动信息物料", "待执行方填写", "例：2026年X月X日", "执行统筹"),
        ("活动时间", "A2海报/主持手卡/交接手册", "待执行方填写", "例：10:00-16:00", "执行统筹"),
        ("活动地点", "A2海报/签到桌牌/总导视", "待执行方填写", "例：学校/社区/场馆全称", "执行统筹"),
        ("主办单位", "主背景板/A2海报/必要落款", "待执行方确认", "按最终公文写法", "执行统筹"),
        ("协同单位", "主背景板/A2海报/必要落款", "待执行方确认", "按最终公文写法", "执行统筹"),
        ("指导单位", "主背景板/A2海报/必要落款", "待执行方确认", "按最终公文写法", "执行统筹"),
        ("C区小程序码", "zone-c-standee-800x2000.pdf / c-zone-qr-table-sign-a4.pdf", "待替换", "必须进入5题闯关页", "C区负责人"),
        ("活动二维码", "activity-poster-a2.pdf", "待替换", "可进入报名页/活动页/小程序", "执行统筹"),
        ("备用二维码", "qr-replacement-checklist-a4.pdf / 备用码打印件", "待替换", "用于现场兜底扫码", "C区负责人"),
        ("礼品数量", "gift-redemption-table-sign-a4.pdf / production-spec.csv", "待确认", "按预算和库存填写", "礼品负责人"),
        ("印章规格", "stamp-design-sheet-a4.pdf / c-zone-task-card-a5.pdf", "待确认", "建议35-45mm，先试盖", "C区负责人"),
        ("供应商联系人", "handoff/print-approval-signoff.pdf", "待填写", "姓名/电话/微信", "广告公司"),
    ]
    signoff_rows = [
        ("真实二维码已替换并真机扫码", "广告公司", "执行统筹"),
        ("日期、地点、单位最终写法已确认", "执行统筹", "主办/协同方"),
        ("大幅面小样已确认", "广告公司", "执行统筹"),
        ("二维码类小样已确认", "广告公司", "C区负责人"),
        ("印章与任务卡已试盖", "C区负责人", "执行统筹"),
        ("礼品数量和领奖规则已确认", "礼品负责人", "执行统筹"),
        ("现场隐私口径已确认", "执行统筹", "各区负责人"),
    ]
    completion_rows = [
        ("主会场识别", "主背景板、入口横幅、活动总主题和三分区预告", "已设计", "main-stage-backdrop-5000x3000.pdf; entrance-banner-8000x700.pdf", "日期地点单位待回填"),
        ("入口导视", "入口总导视、A/B/C 区方向引导、签到口径", "已设计", "entrance-wayfinding-800x2000.pdf; direction-sign-*-a3-landscape.pdf; checkin-table-sign-a4.pdf", "现场动线需按实际场地确认"),
        ("A区防骗驿站", "老人手机安全、银行咨询、口诀带走卡、隐私桌牌", "已设计", "zone-a-standee-800x2000.pdf; a-zone-phone-table-sign-a4.pdf; a-zone-bank-table-sign-a4.pdf; a-zone-formula-card-a6.pdf; privacy-desk-sign-a4.pdf", "协同单位写法待确认"),
        ("B区青春盾牌", "学生互动、快问快答、手举牌、拍照传播、短视频授权", "已设计", "zone-b-standee-800x2000.pdf; b-zone-question-card-a6.pdf; handheld-signs-a3.pdf; photo-frame-600x900.pdf; video-consent-sign-a4.pdf", "拍摄授权口径需现场执行"),
        ("C区扫码闯关", "扫码展架、扫码桌牌、5题闯关任务卡、成绩页、核销说明、纸质兜底", "已设计", "zone-c-standee-800x2000.pdf; c-zone-qr-table-sign-a4.pdf; c-zone-task-card-a5.pdf; miniprogram-score-page-board-a4.pdf; score-verification-guide-a4.pdf; fallback-paper-quiz-a4.pdf", "真实小程序码待替换并扫码测试"),
        ("案例教育", "五类高发骗局和急救动作展板", "已设计", "case-board-01-600x900.pdf 至 case-board-06-600x900.pdf", "案例文字可按最终题库微调"),
        ("志愿者执行", "胸牌、手卡、安全总提示、主持手卡", "已设计", "volunteer-badge-90x120.pdf; volunteer-handcard-a6.pdf; staff-briefing-board-a3.pdf; host-cue-card-a5.pdf", "人员数量待执行方确认"),
        ("隐私安全", "不代输密码、不拍屏幕、不收手机号、屏幕共享应急", "已设计", "privacy-desk-sign-a4.pdf; volunteer-handcard-a6.pdf; staff-briefing-board-a3.pdf; video-consent-sign-a4.pdf", "活动前需培训口径"),
        ("领奖核销", "领奖券、礼品兑换桌牌、印章图样、任务卡章位", "已设计", "redemption-coupon-a6.pdf; gift-redemption-table-sign-a4.pdf; stamp-design-sheet-a4.pdf; c-zone-task-card-a5.pdf", "礼品数量和印章实物待确认"),
        ("礼品延展", "扇子、帆布袋、笔记本、纸巾盒、手机支架、钥匙扣、贴纸、母版", "已设计", "gift-*.pdf; merch-print-sheet-a3.pdf", "供应商刀模和工艺需复核"),
        ("广告公司制作", "规格、材质、数量、打样优先级、转曲/CMYK/小样提醒", "已交付", "production-spec.csv; production-spec.md; README_VENDOR.md", "由供应商按设备打样"),
        ("现场交接", "分区装箱、当天布置、供应商验收、最终信息回填、印前签核", "已交付", "handoff/*.csv; handoff/*.pdf; handoff/event-material-handoff-manual.md", "执行方按表签核"),
        ("禁止项", "不使用 SVG 或 AI 概念图承载正式文字和二维码", "已落实", "README_VENDOR.md; docs/EVENT_MATERIAL_SYSTEM.md; handoff/event-material-handoff-manual.md", "历史 SVG 探索稿仅作归档，不进生产包"),
    ]

    def write_csv(name: str, headers: list[str], csv_rows: list[tuple[str, ...]]):
        with (HANDOFF_DIR / name).open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(csv_rows)

    write_csv("zone-packing-list.csv", ["区域", "文件名", "物料", "建议数量", "摆放位置", "负责人", "核对要点"], packing_rows)
    write_csv("day-of-setup-checklist.csv", ["时间", "负责人", "动作", "验收要点"], setup_rows)
    write_csv("vendor-acceptance-checklist.csv", ["类别", "文件", "验收标准"], acceptance_rows)
    write_csv("final-info-fill-in.csv", ["信息项", "影响物料", "当前状态", "填写说明", "负责人"], final_info_rows)
    write_csv("print-approval-signoff.csv", ["签核项", "提交人", "确认人"], signoff_rows)
    write_csv("material-completion-audit.csv", ["需求项", "覆盖范围", "状态", "证据文件", "剩余外部确认"], completion_rows)

    md = build_handoff_markdown(arts, packing_rows, setup_rows, acceptance_rows, final_info_rows, signoff_rows)
    (HANDOFF_DIR / "event-material-handoff-manual.md").write_text(md, encoding="utf-8")
    audit_md = build_completion_audit_markdown(arts, completion_rows)
    (HANDOFF_DIR / "material-completion-audit.md").write_text(audit_md, encoding="utf-8")
    render_handoff_pdf(arts, by_file, packing_rows, setup_rows, acceptance_rows)
    render_final_info_pdf(final_info_rows)
    render_signoff_pdf(signoff_rows)
    render_completion_audit_pdf(arts, completion_rows)


def build_handoff_markdown(arts: list[Artwork], packing_rows, setup_rows, acceptance_rows, final_info_rows, signoff_rows) -> str:
    def table(headers, rows):
        body = "\n".join("| " + " | ".join(row) + " |" for row in rows)
        return "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n" + body

    return f"""# 真的假的鸭活动物料交接手册

生成日期：2026-06-07

本手册服务广告公司、执行统筹和 A/B/C 区负责人。它不是对外海报，不替代 `pdf-print/` 核版文件；用于确认“哪些物料已经出、放在哪里、谁负责、怎样验收”。

## 包结构

- `pdf-print/`：{len(arts)} 份核版 PDF。
- `png-preview/`：{len(arts)} 张校对图。
- `production-spec.csv` / `production-spec.md`：制作规格、数量、材质、二维码替换和打样优先级。
- `handoff/zone-packing-list.csv`：分区装箱和摆放清单。
- `handoff/day-of-setup-checklist.csv`：活动当天布置节奏。
- `handoff/vendor-acceptance-checklist.csv`：印前和到货验收清单。
- `handoff/final-info-fill-in.csv`：真实二维码、日期地点、单位写法、礼品数量等最终信息回填表。
- `handoff/print-approval-signoff.csv` / `print-approval-signoff.pdf`：印前签核单。
- `handoff/material-completion-audit.csv` / `.md` / `.pdf`：需求覆盖和完成度审计。

## 不可省略的印前动作

- 替换真实小程序码和活动二维码，并用不同手机现场扫码。
- 确认活动日期、地点、主办/协同/指导单位最终写法。
- 字体转曲，按供应商设备转 CMYK。
- 大幅面和二维码类物料必须打小样。
- 不使用 SVG 或 AI 概念图承载正式文字、二维码和生产尺寸。

## 分区装箱清单

{table(["区域", "文件名", "物料", "建议数量", "摆放位置", "负责人", "核对要点"], packing_rows)}

## 当天布置清单

{table(["时间", "负责人", "动作", "验收要点"], setup_rows)}

## 供应商验收清单

{table(["类别", "文件", "验收标准"], acceptance_rows)}

## 最终信息回填表

{table(["信息项", "影响物料", "当前状态", "填写说明", "负责人"], final_info_rows)}

## 印前签核单

{table(["签核项", "提交人", "确认人"], signoff_rows)}
"""


def build_completion_audit_markdown(arts: list[Artwork], completion_rows) -> str:
    table_rows = "\n".join(
        "| " + " | ".join(row) + " |"
        for row in completion_rows
    )
    return f"""# 真的假的鸭活动物料完成度审计

生成日期：2026-06-07

本审计用于对照活动资料和物料系统清单，确认“这次活动相关物料是否已经形成可交付设计包”。审计对象是 `output/vendor-package/2026-06-07/`。

## 当前交付证据

- 物料核版 PDF：{len(arts)} 份。
- 校对 PNG：{len(arts)} 张。
- 生产规格表：`production-spec.csv` / `production-spec.md`。
- 交接与签核文件：`handoff/`。
- 最终 zip：`output/vendor-package/zhenjiade-ya-ad-company-package-2026-06-07.zip`。

## 完成度表

| 需求项 | 覆盖范围 | 状态 | 证据文件 | 剩余外部确认 |
| --- | --- | --- | --- | --- |
{table_rows}

## 审计结论

设计交付层面已形成完整活动物料系统：主会场、入口导视、A/B/C 分区、C 区扫码闯关、小程序成绩页、任务卡/印章、志愿者执行、安全隐私、领奖核销、礼品延展、广告公司制作规格、现场交接和印前签核均有对应文件。

仍需执行方在印前回填或确认：真实二维码、活动日期地点、主办/协同/指导单位最终写法、礼品数量、印章实物、供应商 CMYK 打样和字体转曲。上述事项已通过 `handoff/final-info-fill-in.*` 和 `handoff/print-approval-signoff.*` 纳入交付闭环。
"""


def draw_manual_text(c, x, y, text, size=9, color=None, weight="regular", page_h=297):
    font = "DengXian-Bold" if weight == "bold" else "DengXian"
    c.setFont(font, size)
    c.setFillColor(HexColor(color or COLORS["ink"]))
    c.drawString(x * mm, (page_h - y) * mm, str(text))


def wrap_manual_text(text: str, size: float, max_w_mm: float, weight="regular") -> list[str]:
    font = "DengXian-Bold" if weight == "bold" else "DengXian"
    lines: list[str] = []
    current = ""
    for ch in str(text):
        candidate = current + ch
        if pdfmetrics.stringWidth(candidate, font, size) <= max_w_mm * mm:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_manual_wrapped(c, x, y, text, max_w, size=8.5, color=None, weight="regular", leading=5.2):
    lines = wrap_manual_text(text, size, max_w, weight)
    for i, line in enumerate(lines):
        draw_manual_text(c, x, y + i * leading, line, size, color, weight)
    return y + max(1, len(lines)) * leading


def draw_manual_header(c, title: str, page_no: int):
    c.setFillColor(HexColor(COLORS["cream"]))
    c.rect(0, 0, 210 * mm, 297 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor(COLORS["cream2"]))
    c.circle(178 * mm, 35 * mm, 33 * mm, fill=1, stroke=0)
    c.setStrokeColor(HexColor(COLORS["gold"]))
    c.setLineWidth(1)
    c.rect(10 * mm, 10 * mm, 190 * mm, 277 * mm, fill=0, stroke=1)
    draw_manual_text(c, 18, 22, title, 16, COLORS["red"], "bold")
    draw_manual_text(c, 178, 282, f"{page_no}", 8, COLORS["muted"])


def draw_guide_card(c, x, y, w, h, title, body, color):
    c.setFillColor(HexColor(COLORS["white"]))
    c.setStrokeColor(HexColor(color))
    c.roundRect(x * mm, (297 - y - h) * mm, w * mm, h * mm, 4 * mm, fill=1, stroke=1)
    draw_manual_text(c, x + 5, y + 8, title, 9, COLORS["red"], "bold")
    draw_manual_wrapped(c, x + 5, y + 18, body, w - 10, 7.2, COLORS["ink"], "regular", 4.8)


def guide_row_height(row: dict[str, str]) -> float:
    text_blocks = [
        (f"{row['编号']}. {row['中文材料名']} / {row['英文文件名']}", 8.2, 166, "bold"),
        (f"用途：{row['实际用途']}", 7.0, 166, "regular"),
        (f"文件：{row['PDF核版稿']}；{row['PNG校对图']}", 6.2, 166, "regular"),
        (f"使用/确认：{row['使用/确认人']}", 6.5, 166, "regular"),
        (f"制作确认：{row['制作确认重点']}", 6.5, 166, "regular"),
    ]
    line_count = 0
    for text, size, max_w, weight in text_blocks:
        line_count += len(wrap_manual_text(text, size, max_w, weight))
    return 9 + line_count * 4.5


def draw_guide_row(c, y: float, row: dict[str, str]) -> float:
    h = guide_row_height(row)
    c.setFillColor(HexColor(COLORS["white"]))
    c.setStrokeColor(HexColor(COLORS["gold"]))
    c.roundRect(16 * mm, (297 - y - h) * mm, 178 * mm, h * mm, 2.5 * mm, fill=1, stroke=1)
    cur = y + 6
    cur = draw_manual_wrapped(
        c,
        21,
        cur,
        f"{row['编号']}. {row['中文材料名']} / {row['英文文件名']}",
        166,
        8.2,
        COLORS["red"],
        "bold",
        4.7,
    )
    cur = draw_manual_wrapped(c, 21, cur + 1, f"用途：{row['实际用途']}", 166, 7.0, COLORS["ink"], "regular", 4.7)
    cur = draw_manual_wrapped(
        c,
        21,
        cur + 1,
        f"文件：{row['PDF核版稿']}；{row['PNG校对图']}",
        166,
        6.2,
        COLORS["muted"],
        "regular",
        4.3,
    )
    cur = draw_manual_wrapped(c, 21, cur + 1, f"使用/确认：{row['使用/确认人']}", 166, 6.5, COLORS["muted"], "regular", 4.3)
    draw_manual_wrapped(c, 21, cur + 1, f"制作确认：{row['制作确认重点']}", 166, 6.5, COLORS["ink"], "regular", 4.3)
    return y + h + 3


def render_chinese_guide_pdf(arts: list[Artwork], rows: list[dict[str, str]]):
    pdf_path = OUT / "请先看这个-中文说明.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(210 * mm, 297 * mm))

    page = 1
    draw_manual_header(c, "请先看这个：中文说明", page)
    draw_manual_text(c, 18, 50, "真的假的鸭活动物料交付包", 19, COLORS["red"], "bold")
    draw_manual_wrapped(
        c,
        18,
        73,
        "给执行统筹、广告公司、现场负责人和礼品供应商共同使用。英文文件名用于保持出图脚本和压缩包索引稳定，实际沟通请以本说明和中文材料索引为准。",
        166,
        9,
        COLORS["ink"],
        "regular",
        6,
    )
    draw_manual_text(c, 18, 105, f"当前正式物料：{len(arts)} 件", 13, COLORS["red"], "bold")
    draw_manual_text(c, 18, 121, f"核版 PDF：{len(arts)} 份    校对 PNG：{len(arts)} 张", 9.2, COLORS["ink"], "bold")
    cards = [
        ("出图看 PDF", "广告公司使用 pdf-print/ 下的核版 PDF；大幅面按页脚比例放大。", 18, 146, COLORS["gold"]),
        ("校对看 PNG", "项目组和现场负责人使用 png-preview/ 与 contact-sheet.png 快速看整体。", 108, 146, COLORS["mint"]),
        ("报价看规格表", "production-spec.csv 写明规格、数量、材质、二维码替换和打样优先级。", 18, 202, COLORS["sky"]),
        ("印前先签核", "最终信息回填、真实二维码、小样和印章试盖确认后，再走签核排产。", 108, 202, COLORS["coral"]),
    ]
    for title, body, x, y, color in cards:
        draw_guide_card(c, x, y, 82, 42, title, body, color)
    c.showPage()

    page += 1
    draw_manual_header(c, "交付包怎么使用", page)
    steps = [
        ("1. 先看总览", "打开 contact-sheet.png，确认主会场、A/B/C区、礼品和执行安全物料是否都在。"),
        ("2. 回填最终信息", "把活动日期、地点、单位写法、真实二维码、礼品数量和印章规格填进 handoff/final-info-fill-in.pdf。"),
        ("3. 让广告公司核版", "广告公司基于 pdf-print/ 替换二维码、转曲、转 CMYK、按 production-spec.csv 打样报价。"),
        ("4. 签核后排产", "真实扫码、小样、大幅面比例、印章试盖和礼品刀模都确认后，在 print-approval-signoff.pdf 上签字。"),
    ]
    y = 52
    for title, body in steps:
        draw_manual_text(c, 20, y, title, 11, COLORS["red"], "bold")
        y = draw_manual_wrapped(c, 20, y + 11, body, 165, 8.2, COLORS["ink"], "regular", 5.4) + 8
    draw_manual_text(c, 20, 170, "印前不要跳过", 12, COLORS["red"], "bold")
    musts = [
        "所有二维码占位必须替换为真实二维码，并用不同手机真机扫码。",
        "活动日期、地点、单位写法先统一口径，再改进 PDF。",
        "礼品数量、领奖规则和印章尺寸必须和任务卡、领奖券、桌牌一起核对。",
        "本包不提供 SVG 或可编辑矢量源文件，避免软件兼容导致文字错位、覆盖或坐标翻转。",
    ]
    y = 190
    for item in musts:
        y = draw_manual_wrapped(c, 24, y, "· " + item, 158, 8, COLORS["ink"], "regular", 5.4) + 2
    c.showPage()

    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["分组"], []).append(row)

    page += 1
    draw_manual_header(c, "中文材料索引", page)
    y = 46
    for group in sorted(grouped):
        needed = 10 + guide_row_height(grouped[group][0])
        if y + needed > 270:
            c.showPage()
            page += 1
            draw_manual_header(c, "中文材料索引", page)
            y = 46
        draw_manual_text(c, 18, y, group, 12, COLORS["red"], "bold")
        y += 10
        for row in grouped[group]:
            h = guide_row_height(row)
            if y + h > 274:
                c.showPage()
                page += 1
                draw_manual_header(c, "中文材料索引", page)
                y = 46
                draw_manual_text(c, 18, y, group, 12, COLORS["red"], "bold")
                y += 10
            y = draw_guide_row(c, y, row)
        y += 5

    c.save()


def render_handoff_pdf(arts: list[Artwork], by_file, packing_rows, setup_rows, acceptance_rows):
    pdf_path = HANDOFF_DIR / "event-material-handoff-manual.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(210 * mm, 297 * mm))

    draw_manual_header(c, "真的假的鸭活动物料交接手册", 1)
    draw_manual_text(c, 18, 48, "广告公司 / 执行统筹 / 分区负责人共用", 10, COLORS["muted"], "bold")
    draw_manual_text(c, 18, 72, f"当前出图物料：{len(arts)} 件", 14, COLORS["red"], "bold")
    draw_manual_text(c, 18, 90, f"核版PDF：{len(arts)} 份", 10, COLORS["ink"], "bold")
    draw_manual_text(c, 18, 105, f"校对PNG：{len(arts)} 张", 10, COLORS["ink"], "bold")
    draw_manual_text(c, 18, 120, "另含制作规格表、分区装箱清单、当天布置清单、供应商验收清单。", 9, COLORS["ink"])
    cover_points = [
        "不提供 SVG 或可编辑矢量源文件，避免字体漂移、文字错位和坐标翻转。",
        "AI 概念图只作为情绪参考，不承载正式文字、二维码和生产尺寸。",
        "正式生产前必须替换真实二维码、确认活动日期地点单位、转曲、转 CMYK、打小样。",
    ]
    y = 150
    for point in cover_points:
        y = draw_manual_wrapped(c, 22, y, "· " + point, 158, 8.5, COLORS["ink"], "regular", 6) + 4
    c.showPage()

    draw_manual_header(c, "一页看懂现场点位", 2)
    zones = [
        ("入口/签到", "横幅、总导视、签到台桌牌", 20, 58, COLORS["gold"]),
        ("主舞台", "主背景板、案例展板、主持手卡", 112, 58, COLORS["coral"]),
        ("A区 防骗驿站", "手机安全门诊、银行咨询、口诀卡", 20, 128, COLORS["mint"]),
        ("B区 青春盾牌", "快问快答、手举牌、拍摄授权提示", 112, 128, COLORS["sky"]),
        ("C区 真的假的鸭", "扫码展架、任务卡、成绩页核销、纸质兜底", 20, 198, COLORS["coral"]),
        ("礼品/后台", "领奖桌牌、礼品稿、志愿者胸牌、总提示", 112, 198, COLORS["gold"]),
    ]
    for title, desc, x, y, color in zones:
        c.setFillColor(HexColor(COLORS["white"]))
        c.setStrokeColor(HexColor(color))
        c.roundRect(x * mm, y * mm, 78 * mm, 48 * mm, 5 * mm, fill=1, stroke=1)
        draw_manual_text(c, x + 6, 297 - y - 36, title, 10, COLORS["red"], "bold")
        draw_manual_wrapped(c, x + 6, 297 - y - 24, desc, 64, 7, COLORS["ink"], "regular", 4.5)
    c.showPage()

    draw_manual_header(c, "分区装箱重点", 3)
    y = 48
    zone_names = ["入口/签到", "主舞台", "A区", "B区", "C区", "礼品区", "工作人员"]
    for zone_index, zone in enumerate(zone_names):
        draw_manual_text(c, 18, y, zone, 11, COLORS["red"], "bold")
        y += 8
        for row in [r for r in packing_rows if r[0] == zone][:5]:
            y = draw_manual_wrapped(c, 24, y, f"{row[2]}：{row[3]}，{row[4]}，{row[6]}", 162, 7.2, COLORS["ink"], "regular", 4.8) + 2
        y += 3
        if y > 260 and zone_index < len(zone_names) - 1:
            c.showPage()
            draw_manual_header(c, "分区装箱重点", 3)
            y = 48
    c.showPage()

    draw_manual_header(c, "当天布置节奏", 4)
    y = 50
    for time, owner, action, check in setup_rows:
        draw_manual_text(c, 18, y, time, 9.5, COLORS["red"], "bold")
        draw_manual_text(c, 48, y, owner, 8.2, COLORS["muted"], "bold")
        y = draw_manual_wrapped(c, 18, y + 9, action, 168, 8, COLORS["ink"], "regular", 5)
        y = draw_manual_wrapped(c, 22, y + 2, "验收：" + check, 160, 7.2, COLORS["muted"], "regular", 4.6) + 5
    c.showPage()

    draw_manual_header(c, "印前与到货验收", 5)
    y = 50
    for category, file_name, standard in acceptance_rows:
        draw_manual_text(c, 18, y, category, 9.5, COLORS["red"], "bold")
        y = draw_manual_wrapped(c, 43, y, file_name, 130, 7.2, COLORS["muted"], "regular", 4.6)
        y = draw_manual_wrapped(c, 43, y + 1, standard, 130, 7.6, COLORS["ink"], "regular", 5) + 6
    c.showPage()

    draw_manual_header(c, "现场安全口径", 6)
    safety = [
        ("工作人员", "站在参与者身侧指导，不代替输入密码，不询问验证码，不记录手机号。"),
        ("A区", "老人手机指导只讲步骤，不拍屏幕，不查看银行密码和验证码。"),
        ("B区", "短视频拍摄先征得同意，不拍身份证、银行卡、验证码和他人手机屏幕。"),
        ("C区", "扫码闯关只看成绩页或任务卡，盖章后提醒每人限领一份。"),
        ("应急", "已经转账、泄露验证码或正在屏幕共享时，立即停手，保留证据，拨打110或咨询96110。"),
    ]
    y = 52
    for title, desc in safety:
        draw_manual_text(c, 20, y, title, 11, COLORS["red"], "bold")
        y = draw_manual_wrapped(c, 20, y + 11, desc, 165, 8.5, COLORS["ink"], "regular", 5.8) + 9
    draw_manual_text(c, 20, 258, "印前待补：真实二维码、日期地点、单位写法、礼品数量、供应商打样。", 8, COLORS["muted"], "bold")
    c.save()


def render_signoff_pdf(signoff_rows):
    pdf_path = HANDOFF_DIR / "print-approval-signoff.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(210 * mm, 297 * mm))
    draw_manual_header(c, "印前签核单", 1)
    draw_manual_text(c, 18, 45, "用于最终出图前签字确认，签完再排产。", 9, COLORS["muted"], "bold")
    draw_manual_text(c, 18, 62, "活动名称：守护钱袋子 金融防骗反诈公益日", 9, COLORS["ink"], "bold")
    draw_manual_text(c, 18, 78, "项目：真的假的鸭活动物料", 9, COLORS["ink"], "bold")
    y = 96
    for i, (item, submitter, approver) in enumerate(signoff_rows, 1):
        c.setFillColor(HexColor(COLORS["white"]))
        c.setStrokeColor(HexColor(COLORS["gold"]))
        c.roundRect(18 * mm, (297 - y - 20) * mm, 174 * mm, 20 * mm, 3 * mm, fill=1, stroke=1)
        draw_manual_text(c, 23, y + 5, f"{i}. {item}", 7.7, COLORS["ink"], "bold")
        draw_manual_text(c, 122, y + 5, f"提交：{submitter}", 6.8, COLORS["muted"])
        draw_manual_text(c, 158, y + 5, f"确认：{approver}", 6.8, COLORS["muted"])
        draw_manual_text(c, 23, y + 15, "签字：________________    日期：__________", 6.8, COLORS["muted"])
        y += 24
    draw_manual_text(c, 18, 274, "备注：真实二维码、日期地点、单位写法、礼品数量和供应商打样未确认前，不建议大货生产。", 7.4, COLORS["red"], "bold")
    c.save()


def render_final_info_pdf(final_info_rows):
    pdf_path = HANDOFF_DIR / "final-info-fill-in.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(210 * mm, 297 * mm))
    draw_manual_header(c, "最终信息回填表", 1)
    draw_manual_text(c, 18, 45, "用于收齐真实二维码、日期地点、单位写法、礼品数量和供应商联系人。", 8.5, COLORS["muted"], "bold")
    y = 64
    for i, (field, affected, status, note, owner) in enumerate(final_info_rows, 1):
        c.setFillColor(HexColor(COLORS["white"]))
        c.setStrokeColor(HexColor(COLORS["gold"]))
        c.roundRect(18 * mm, (297 - y - 14) * mm, 174 * mm, 14 * mm, 2.5 * mm, fill=1, stroke=1)
        draw_manual_text(c, 22, y + 4, f"{i}. {field}", 6.8, COLORS["red"], "bold")
        draw_manual_text(c, 62, y + 4, f"负责人：{owner}", 6.2, COLORS["muted"])
        draw_manual_text(c, 112, y + 4, "填写值：____________________", 6.2, COLORS["ink"])
        draw_manual_text(c, 22, y + 10, f"影响：{affected}；说明：{note}", 5.6, COLORS["muted"])
        y += 17
    draw_manual_text(c, 18, 274, "完成后交给广告公司按表替换，再走 print-approval-signoff.pdf 签核。", 7.4, COLORS["red"], "bold")
    c.save()


def render_completion_audit_pdf(arts: list[Artwork], completion_rows):
    pdf_path = HANDOFF_DIR / "material-completion-audit.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(210 * mm, 297 * mm))
    draw_manual_header(c, "活动物料完成度审计", 1)
    draw_manual_text(c, 18, 45, "对照活动资料、物料系统清单和当前交付包逐项核验。", 8.5, COLORS["muted"], "bold")
    draw_manual_text(c, 18, 62, f"核版 PDF：{len(arts)} 份    校对 PNG：{len(arts)} 张    handoff 文件：已生成", 9, COLORS["ink"], "bold")
    summary = [
        "主会场、入口导视、A/B/C 分区、C 区扫码闯关均有对应核版 PDF。",
        "任务卡、印章、成绩页、核销说明、纸质兜底和礼品延展均已覆盖。",
        "生产规格、分区装箱、当天布置、供应商验收、最终信息回填和印前签核已纳入 handoff。",
        "真实二维码、日期地点、单位写法、礼品数量和供应商打样属于执行方印前确认项。",
    ]
    y = 86
    for line in summary:
        y = draw_manual_wrapped(c, 22, y, "· " + line, 160, 7.8, COLORS["ink"], "regular", 5) + 2
    c.showPage()

    page = 2
    draw_manual_header(c, "需求覆盖明细", page)
    y = 44
    for idx, (need, scope, status, evidence, remaining) in enumerate(completion_rows, 1):
        if y > 252:
            c.showPage()
            page += 1
            draw_manual_header(c, "需求覆盖明细", page)
            y = 44
        draw_manual_text(c, 18, y, f"{idx}. {need}", 9, COLORS["red"], "bold")
        draw_manual_text(c, 152, y, status, 7.2, COLORS["green"], "bold")
        y = draw_manual_wrapped(c, 22, y + 8, "覆盖：" + scope, 164, 6.8, COLORS["ink"], "regular", 4.5)
        y = draw_manual_wrapped(c, 22, y + 1, "证据：" + evidence, 164, 6.5, COLORS["muted"], "regular", 4.3)
        y = draw_manual_wrapped(c, 22, y + 1, "外部确认：" + remaining, 164, 6.5, COLORS["muted"], "regular", 4.3) + 5
    c.save()


def write_contact_sheet(arts: list[Artwork]):
    rows = guide_rows(arts)
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["分组"], []).append(row)

    cols = 4
    card_w, card_h = 520, 390
    gap = 28
    margin = 42
    header_h = 96
    title_h = 132
    width = margin * 2 + cols * card_w + (cols - 1) * gap
    height = title_h
    for group, items in grouped.items():
        height += header_h + ((len(items) + cols - 1) // cols) * (card_h + gap) + gap
    height += 46

    sheet = Image.new("RGB", (width, height), "#FFF7E6")
    d = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(PIL_FONT_BOLD, 42)
    sub_font = ImageFont.truetype(PIL_FONT_REGULAR, 22)
    group_font = ImageFont.truetype(PIL_FONT_BOLD, 30)
    card_title_font = ImageFont.truetype(PIL_FONT_BOLD, 22)
    card_meta_font = ImageFont.truetype(PIL_FONT_REGULAR, 15)

    d.text((margin, 34), "真的假的鸭活动物料视觉总览 V2", fill=COLORS["red"], font=title_font)
    d.text((margin, 88), "47 件物料按现场分区展示；每张卡已融合对应小鸭 IP 方向稿，正式文字与二维码仍由本地排版生成。", fill=COLORS["ink"], font=sub_font)
    y = title_h
    row_lookup = {Path(row["PNG校对图"]).stem: row for row in rows}
    for group in sorted(grouped):
        theme_names = sorted({THEME_META[theme_for_slug(row["英文文件名"])]["label"] for row in grouped[group]})
        d.rounded_rectangle((margin, y, width - margin, y + 58), radius=20, fill="#FFFFFF", outline="#E8B769", width=3)
        d.text((margin + 22, y + 15), group, fill=COLORS["red"], font=group_font)
        d.text((margin + 440, y + 22), " / ".join(theme_names), fill=COLORS["muted"], font=sub_font)
        y += header_h
        for idx, row in enumerate(grouped[group]):
            col = idx % cols
            if idx and col == 0:
                y += card_h + gap
            x = margin + col * (card_w + gap)
            slug = row["英文文件名"]
            theme = theme_for_slug(slug)
            accent = THEME_META[theme]["accent"]
            d.rounded_rectangle((x, y, x + card_w, y + card_h), radius=18, fill="#FFFFFF", outline=accent, width=3)
            d.rectangle((x + 16, y + 18, x + card_w - 16, y + 258), fill="#FFFDF8")
            image = Image.open(PNG_DIR / f"{slug}.png").convert("RGB")
            image.thumbnail((card_w - 52, 226), Image.Resampling.LANCZOS)
            ix = x + (card_w - image.width) // 2
            iy = y + 30 + (226 - image.height) // 2
            sheet.paste(image, (ix, iy))
            d.text((x + 20, y + 284), f"{row['编号']}. {row['中文材料名']}", fill=COLORS["red"], font=card_title_font)
            d.text((x + 20, y + 316), slug, fill=COLORS["muted"], font=card_meta_font)
            d.text((x + 20, y + 342), THEME_META[theme]["label"], fill=accent, font=card_meta_font)
            d.text((x + 20, y + 364), row_lookup.get(slug, row)["使用/确认人"][:26], fill=COLORS["ink"], font=card_meta_font)
        y += card_h + gap

    sheet.save(OUT / "contact-sheet.png", optimize=True)


def write_visual_theme_map():
    mappings = [
        ("01 Pause Token", "wildcard-01.png", "暂停令", "志愿者手卡、主持手卡、隐私提示、转账前核实口径"),
        ("02 Phone Clinic", "wildcard-02.png", "手机门诊", "A区展架、手机安全门诊、口诀卡、适老协助"),
        ("03 Campus Drama", "wildcard-03.png", "校园剧场", "B区展架、快问快答题卡、手举牌、互动拍照"),
        ("04 Stamp Quest", "wildcard-04.png", "闯关盖章", "C区展架、扫码桌牌、任务卡、盖章领奖"),
        ("05 Bank Companion", "wildcard-05.png", "银行陪伴", "银行咨询桌牌、账户安全咨询、A区服务氛围"),
        ("06 Cyber Path", "wildcard-06.png", "网安路径", "导视动线、蓝色安全路径、C区流程提示"),
        ("07 Formula Fan", "wildcard-07.png", "口诀扇", "广告扇、防骗口诀卡、社区可带走礼品"),
        ("08 Short Video", "wildcard-08.png", "短视频", "B区拍摄授权提示、短视频互动、校园传播"),
        ("09 Evidence Keeper", "wildcard-09.png", "证据留存", "案例展板、应急提示、保留聊天与转账记录"),
        ("10 Community Grid", "wildcard-10.png", "社区网格", "入口导视、社区动线、志愿者陪伴服务"),
        ("11 Risk Radar", "wildcard-11.png", "风险雷达", "案例展板、二维码核对、风险识别类桌牌"),
        ("12 Family Relay", "wildcard-12.png", "家庭接力", "主视觉、A2海报、家庭成员互相提醒"),
    ]
    card_w, card_h = 390, 440
    cols = 4
    gap = 32
    margin = 44
    width = margin * 2 + cols * card_w + (cols - 1) * gap
    height = 170 + 3 * card_h + 2 * gap + 70
    sheet = Image.new("RGB", (width, height), "#FFF7E6")
    d = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(PIL_FONT_BOLD, 42)
    sub_font = ImageFont.truetype(PIL_FONT_REGULAR, 21)
    label_font = ImageFont.truetype(PIL_FONT_BOLD, 24)
    body_font = ImageFont.truetype(PIL_FONT_REGULAR, 18)
    d.text((margin, 36), "12 张小鸭方向如何落到活动物料", fill=COLORS["red"], font=title_font)
    d.text((margin, 92), "不是把概念图当印刷文字使用，而是提取角色、场景、动作和色彩，分别落到主会场、A/B/C区、礼品和执行安全物料。", fill=COLORS["ink"], font=sub_font)
    for i, (name, img_name, label, desc) in enumerate(mappings):
        x = margin + (i % cols) * (card_w + gap)
        y = 170 + (i // cols) * (card_h + gap)
        d.rounded_rectangle((x, y, x + card_w, y + card_h), radius=20, fill="#FFFFFF", outline="#E8B769", width=3)
        img = Image.open(CONCEPT_DIR / img_name).convert("RGB")
        img.thumbnail((card_w - 36, 260), Image.Resampling.LANCZOS)
        sheet.paste(img, (x + (card_w - img.width) // 2, y + 18))
        d.text((x + 20, y + 294), name, fill=COLORS["muted"], font=body_font)
        d.text((x + 20, y + 324), label, fill=COLORS["red"], font=label_font)
        lines = wrap_text_for_pil(desc, body_font, card_w - 42, d)
        for j, line in enumerate(lines[:3]):
            d.text((x + 20, y + 360 + j * 25), line, fill=COLORS["ink"], font=body_font)
    sheet.save(OUT / "视觉母题映射板.png", optimize=True)


def wrap_text_for_pil(text: str, font, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        candidate = current + ch
        if draw.textlength(candidate, font=font) <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def main():
    ensure_dirs()
    font_setup()
    prepare_ip_assets()
    arts = build_artworks()
    for art in arts:
        render_pdf(art)
        render_png_preview(art)
    write_production_spec(arts)
    write_handoff_package(arts)
    write_chinese_guide(arts)
    write_readme(arts)
    write_visual_theme_map()
    write_contact_sheet(arts)
    print(f"generated {len(arts)} artworks under {OUT}")


if __name__ == "__main__":
    main()
