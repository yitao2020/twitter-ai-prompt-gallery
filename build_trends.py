#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the interactive AI topic map from trends_data.json."""
import json
import os
import re
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "trends_data.json")
OUT_FILE = os.path.join(HERE, "trends.html")

LINE_COLORS = [
    "#58a6ff", "#f78166", "#7ee787", "#d2a8ff", "#e3b341",
    "#ff7b72", "#79c0ff", "#56d364", "#ffa657", "#bc8cff",
]

# 关联热词英→中翻译词典（覆盖 AI 图像生成领域的常见术语）
TERM_CN = {
    # 模型/工具
    "stable diffusion": "Stable Diffusion",
    "dall mini": "DALL·E Mini",
    "adobe firefly": "Adobe Firefly",
    "google imagen": "Google Imagen",
    # 风格/质感
    "photorealistic": "照片级写实",
    "photoreal": "照片级写实",
    "cinematic": "电影感",
    "cinematic lighting": "电影级布光",
    "anime": "动漫风格",
    "anime style": "动漫风格",
    "cyberpunk": "赛博朋克",
    "pixel art": "像素艺术",
    "concept art": "概念设计",
    "character design": "角色设计",
    "character concept": "角色概念",
    "fantasy art": "奇幻艺术",
    "oil painting": "油画",
    "watercolor": "水彩",
    "digital painting": "数字绘画",
    "digital art": "数字艺术",
    "vector art": "矢量艺术",
    "line art": "线稿",
    "sketch": "素描",
    "illustration": "插画",
    "portrait": "肖像",
    "landscape": "风景",
    "abstract": "抽象",
    "minimalist": "极简",
    "surreal": "超现实",
    "vintage": "复古",
    "retro": "怀旧",
    "futuristic": "未来主义",
    "dark fantasy": "暗黑奇幻",
    "sci fi": "科幻",
    "sci-fi": "科幻",
    "steampunk": "蒸汽朋克",
    "baroque": "巴洛克",
    "gothic": "哥特",
    "noir": "黑色電影",
    "pastel": "粉彩",
    "neon": "霓虹",
    "holographic": "全息",
    "iridescent": "虹彩",
    "ethereal": "空灵",
    "dreamy": "梦幻",
    "moody": "氛围感",
    "dramatic": "戏剧性",
    "atmospheric": "氛围",
    "hyperrealistic": "超写实",
    "hyperreal": "超写实",
    "ultra realistic": "超写实",
    "ultra detailed": "极致细节",
    "highly detailed": "高细节",
    "intricate detail": "精细细节",
    "fine detail": "精细细节",
    "macro photography": "微距摄影",
    "studio lighting": "影棚布光",
    "natural lighting": "自然光",
    "golden hour": "黄金时刻",
    "rim lighting": "轮廓光",
    "volumetric lighting": "体积光",
    "depth of field": "景深",
    "bokeh": "散景",
    "shallow depth": "浅景深",
    "wide angle": "广角",
    "close up": "特写",
    "full body": "全身",
    "half body": "半身",
    "headshot": "头像",
    "pose": "姿态",
    "dynamic pose": "动态姿态",
    "action pose": "动作姿态",
    # 材质/纹理
    "texture": "纹理",
    "material": "材质",
    "metallic": "金属感",
    "gold": "金色",
    "silver": "银色",
    "bronze": "青铜",
    "chrome": "镀铬",
    "glass": "玻璃",
    "crystal": "水晶",
    "marble": "大理石",
    "wood": "木质",
    "leather": "皮革",
    "fabric": "织物",
    "ceramic": "陶瓷",
    "porcelain": "瓷器",
    "plastic": "塑料",
    "rubber": "橡胶",
    "clay": "黏土",
    "paper texture": "纸质纹理",
    "grainy": "颗粒感",
    "smooth": "光滑",
    "rough": "粗糙",
    "glossy": "光泽",
    "matte": "哑光",
    "translucent": "半透明",
    "transparent": "透明",
    "reflective": "反光",
    "refraction": "折射",
    "subsurface scattering": "次表面散射",
    "ambient occlusion": "环境光遮蔽",
    # 渲染/技术
    "render": "渲染",
    "rendering": "渲染",
    "octane render": "Octane渲染",
    "unreal engine": "虚幻引擎",
    "blender": "Blender",
    "cinema": "C4D",
    "zbrush": "ZBrush",
    "houdini": "Houdini",
    "maya": "Maya",
    "renderman": "RenderMan",
    "vfx": "视觉特效",
    "visual effects": "视觉特效",
    "motion graphics": "动态图形",
    "animation": "动画",
    "rigging": "骨骼绑定",
    "modeling": "建模",
    "sculpting": "雕刻",
    "texturing": "贴图",
    "lighting": "布光",
    "compositing": "合成",
    "post processing": "后期处理",
    "color grading": "调色",
    "color palette": "配色",
    "resolution": "分辨率",
    "high resolution": "高分辨率",
    "upscale": "超分放大",
    "upscaling": "超分放大",
    "workflow": "工作流",
    "pipeline": "流程",
    "plugin": "插件",
    "node based": "节点式",
    # 图像类型/格式
    "thumbnail": "缩略图",
    "banner": "横幅",
    "poster": "海报",
    "flyer": "传单",
    "brochure": "宣传册",
    "magazine cover": "杂志封面",
    "album cover": "专辑封面",
    "book cover": "书籍封面",
    "movie poster": "电影海报",
    "wallpaper": "壁纸",
    "screenshot": "截图",
    "mockup": "样机",
    "product shot": "产品摄影",
    "flat lay": "平铺摄影",
    "still life": "静物",
    "fashion photography": "时尚摄影",
    "editorial photography": "时尚大片",
    "street photography": "街拍",
    "aerial photography": "航拍",
    "drone shot": "无人机拍摄",
    "underwater photography": "水下摄影",
    "night photography": "夜景摄影",
    "long exposure": "长曝光",
    "double exposure": "双重曝光",
    "tilt shift": "移轴",
    "isometric": "等距",
    "top down": "俯视",
    "bird eye view": "鸟瞰",
    "worm eye view": "仰视",
    "first person": "第一人称",
    "third person": "第三人称",
    "over shoulder": "过肩",
    "dutch angle": "荷兰角",
    "symmetrical": "对称",
    "asymmetrical": "不对称",
    "rule thirds": "三分法",
    "leading lines": "引导线",
    "negative space": "留白",
    "minimal": "极简",
    "maximalist": "极繁",
    # 颜色
    "monochrome": "单色",
    "grayscale": "灰度",
    "black white": "黑白",
    "black and white": "黑白",
    "vibrant": "鲜艳",
    "muted": "柔和色调",
    "desaturated": "低饱和",
    "saturated": "高饱和",
    "pastel colors": "粉彩色调",
    "warm tones": "暖色调",
    "cool tones": "冷色调",
    "earthy tones": "大地色调",
    "jewel tones": "宝石色调",
    "duotone": "双色调",
    "gradient": "渐变",
    # 主题/场景
    "nature": "自然",
    "forest": "森林",
    "jungle": "丛林",
    "desert": "沙漠",
    "ocean": "海洋",
    "mountain": "山脉",
    "space": "太空",
    "galaxy": "星系",
    "nebula": "星云",
    "cityscape": "城景",
    "skyline": "天际线",
    "architecture": "建筑",
    "interior design": "室内设计",
    "exterior": "室外",
    "ruins": "废墟",
    "temple": "寺庙",
    "castle": "城堡",
    "dungeon": "地牢",
    "laboratory": "实验室",
    "workshop": "工作室",
    "studio": "影棚",
    "dark room": "暗房",
    "backstage": "后台",
    "runway": "T台",
    "catwalk": "走秀",
    "battlefield": "战场",
    "post apocalyptic": "末日废土",
    "dystopian": "反乌托邦",
    "utopian": "乌托邦",
    "medieval": "中世纪",
    "renaissance": "文艺复兴",
    "victorian": "维多利亚",
    "art deco": "装饰艺术",
    "art nouveau": "新艺术",
    "brutalist": "粗野主义",
    "bauhaus": "包豪斯",
    # 角色/生物
    "character": "角色",
    "creature": "生物",
    "monster": "怪物",
    "dragon": "龙",
    "robot": "机器人",
    "mecha": "机甲",
    "cyborg": "赛博格",
    "alien": "外星人",
    "elf": "精灵",
    "dwarf": "矮人",
    "wizard": "巫师",
    "knight": "骑士",
    "warrior": "战士",
    "samurai": "武士",
    "ninja": "忍者",
    "pirate": "海盗",
    "vampire": "吸血鬼",
    "werewolf": "狼人",
    "zombie": "丧尸",
    "ghost": "幽灵",
    "demon": "恶魔",
    "angel": "天使",
    "goddess": "女神",
    "princess": "公主",
    "queen": "女王",
    "king": "国王",
    # 道具/物品
    "weapon": "武器",
    "sword": "剑",
    "shield": "盾",
    "armor": "盔甲",
    "helmet": "头盔",
    "crown": "王冠",
    "jewelry": "珠宝",
    "gemstone": "宝石",
    "potion": "药水",
    "magic item": "魔法物品",
    "artifact": "神器",
    "treasure": "宝藏",
    "vehicle": "载具",
    "spaceship": "太空船",
    "airship": "飞艇",
    "car": "汽车",
    "motorcycle": "摩托车",
    "aircraft": "飞行器",
    "gun": "枪械",
    "rifle": "步枪",
    "pistol": "手枪",
    "katana": "武士刀",
    "axe": "斧",
    "bow": "弓",
    "arrow": "箭",
    "staff": "法杖",
    "wand": "魔杖",
    "book": "书籍",
    "scroll": "卷轴",
    "map": "地图",
    "compass": "指南针",
    "hourglass": "沙漏",
    "lamp": "灯",
    "lantern": "灯笼",
    "candle": "蜡烛",
    # 游戏美术
    "game asset": "游戏资产",
    "game art": "游戏美术",
    "game ready": "游戏级",
    "game prop": "游戏道具",
    "game environment": "游戏场景",
    "level design": "关卡设计",
    "ui design": "UI设计",
    "icon design": "图标设计",
    "sprite sheet": "精灵图",
    "tile set": "瓦片集",
    "low poly": "低多边形",
    "high poly": "高多边形",
    "stylized": "风格化",
    "cartoon": "卡通",
    "chibi": "Q版",
    "kawaii": "可爱风",
    "cute": "可爱",
    "dark": "暗黑",
    "grimdark": "黑暗残酷",
    "horror": "恐怖",
    "gore": "血腥",
    "cute horror": "可爱恐怖",
    # 环境/天气
    "sunset": "日落",
    "sunrise": "日出",
    "daytime": "白天",
    "night": "夜晚",
    "twilight": "黄昏",
    "dawn": "黎明",
    "dusk": "傍晚",
    "fog": "雾",
    "mist": "薄雾",
    "rain": "雨",
    "snow": "雪",
    "storm": "风暴",
    "lightning": "闪电",
    "thunder": "雷",
    "clouds": "云",
    "sky": "天空",
    "starry night": "星空",
    "aurora": "极光",
    "rainbow": "彩虹",
    "fire": "火焰",
    "smoke": "烟",
    "explosion": "爆炸",
    "sparkle": "闪光",
    "glow": "发光",
    "glowing": "发光",
    "bioluminescent": "生物发光",
    "phosphorescent": "磷光",
    # 其他
    "logo design": "Logo设计",
    "logo": "Logo",
    "sticker": "贴纸",
    "sticker design": "贴纸设计",
    "emoji": "表情",
    "meme": "梗图",
    "infographic": "信息图",
    "diagram": "图表",
    "typography": "字体排印",
    "calligraphy": "书法",
    "hand drawn": "手绘",
    "doodle": "涂鸦",
    "graffiti": "涂鸦",
    "street art": "街头艺术",
    "tribal": "部落",
    "geometric": "几何",
    "fractal": "分形",
    "mandala": "曼陀罗",
    "pattern": "图案",
    "ornament": "纹饰",
    "mosaic": "马赛克",
    "stained glass": "彩绘玻璃",
    "collage": "拼贴",
    "mixed media": "混合媒介",
    "double exposure": "双重曝光",
    "glitch": "故障艺术",
    "vaporwave": "蒸汽波",
    "synthwave": "合成波",
    "outrun": "复古未来",
    "lofi": "低保真",
    "comic": "漫画",
    "manga": "日漫",
    "manhwa": "韩漫",
    "webtoon": "网漫",
    "graphic novel": "图像小说",
    "tarot card": "塔罗牌",
    "playing card": "扑克牌",
    "trading card": "集换卡",
    "pokemon": "宝可梦",
    "gundam": "高达",
    "transformers": "变形金刚",
    "lego": "乐高",
    "origami": "折纸",
    "papercraft": "纸模",
    "claymation": "黏土动画",
    "stop motion": "定格动画",
    "timelapse": "延时摄影",
    "hyperlapse": "大范围延时",
    "easing": "缓动",
    "storyboard": "分镜",
    "color script": "色彩脚本",
    "mood board": "情绪板",
    "reference": "参考",
    "reference sheet": "参考图",
    "turnaround": "三视图",
    "expression sheet": "表情集",
    "key visual": "主视觉",
    "teaser": "预告",
    "trailer": "预告片",
    "cinematic shot": "电影镜头",
    "establishing shot": "定场镜头",
    "tracking shot": "跟拍镜头",
    "dolly zoom": "推拉变焦",
    "slow motion": "慢动作",
    "time lapse": "延时",
    "video generation": "视频生成",
    "video editing": "视频编辑",
    "sound design": "音效设计",
    "music video": "MV",
    "short film": "短片",
    "feature film": "长片",
}

# 关键词显示名（部分翻译为中文）
KW_CN = {
    "Midjourney": "Midjourney",
    "Nano Banana Pro": "Nano Banana Pro",
    "GPT Image 2": "GPT Image 2",
    "Flux": "Flux",
    "Stable Diffusion": "Stable Diffusion",
    "ComfyUI": "ComfyUI",
    "SDXL": "SDXL",
    "Sora": "Sora",
    "Krea": "Krea",
    "Ideogram": "Ideogram",
    "DALL·E": "DALL·E",
    "Recraft": "Recraft",
    "anime": "动漫",
    "photorealistic": "照片写实",
    "cinematic": "电影感",
    "cyberpunk": "赛博朋克",
    "3D render": "3D渲染",
    "pixel art": "像素艺术",
    "logo": "Logo",
    "sticker": "贴纸",
    "character design": "角色设计",
    "concept art": "概念设计",
    "LoRA": "LoRA",
    "prompt engineering": "提示词工程",
    "AI video": "AI视频",
    "upscale": "超分放大",
}


def translate_term(term):
    """翻译单个关联热词（支持英文单词/词组 → 中文）。"""
    t = term.strip().lower()
    if t in TERM_CN:
        return TERM_CN[t]
    # 尝试拆分双词分别翻译
    parts = t.split()
    if len(parts) == 2:
        a = TERM_CN.get(parts[0], parts[0])
        b = TERM_CN.get(parts[1], parts[1])
        if a != parts[0] or b != parts[1]:
            return f"{a}{b}"
    return term  # 无匹配则保留原文


def translate_keyword(kw):
    """翻译关键词显示名。"""
    return KW_CN.get(kw, kw)


def _looks_like_error(s):
    """Google 翻译偶尔返回错误页文本而非抛异常，需识别。"""
    s = (s or "").lower()
    if not s:
        return False
    markers = ["error 500", "that's an error", "there was an error",
               "please try again later", "service unavailable", "bad gateway",
               "rate limit", "too many requests", "502", "503", "429"]
    return any(m in s for m in markers) or s.startswith("error")


def _is_valid_cn(tc, src):
    """判断 text_cn 是否为有效中文译文（而非错误串或空）。"""
    if not tc:
        return False
    if _looks_like_error(tc):
        return False
    # 译文含中文 → 有效
    if re.search(r"[\u4e00-\u9fff]", tc):
        return True
    # 译文无中文：仅当原文本身也无中文（纯符号/英文短词）时才算可接受
    if not re.search(r"[\u4e00-\u9fff]", src or ""):
        return True
    return False


def ensure_text_cn(data):
    """固化规则：trends 推文内容必须翻译为中文呈现。

    为所有推文补全 text_cn 字段（优先读 text_clean，回退 text）。
    - 幂等：已有有效中文译文的跳过，避免每日重复翻译浪费配额；
      但若现存 text_cn 是错误串，仍会强制重翻。
    - 使用 source='auto'，防止中文推文被误当作英文二次翻译。
    - 失败（网络/限流/错误页）时保留原文，绝不让构建中断。
    翻译结果写回 trends_data.json，供后续手动重跑构建时复用。
    """
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        print("  [WARN] 未安装 deep_translator，跳过翻译（trends 将显示原文）")
        return

    # 收集所有推文（all_tweets + keyword_tweets）
    tweets = list(data.get("all_tweets", []))
    for lst in data.get("keyword_tweets", {}).values():
        tweets.extend(lst)

    # 待翻译：原文去重；已有有效译文的跳过（错误串视为未翻译）
    pending = []          # [(tweet, source_text)]
    trans_map = {}        # source_text -> 译文（跨推文复用）
    for t in tweets:
        tc = (t.get("text_cn") or "").strip()
        src = (t.get("text_clean") or t.get("text") or "").strip()
        if not src:
            continue
        if _is_valid_cn(tc, src):
            continue  # 已有有效译文
        if src in trans_map:
            t["text_cn"] = trans_map[src]
            continue
        pending.append((t, src))

    if not pending:
        return

    translator = GoogleTranslator(source='auto', target='zh-CN')
    total = len(pending)
    done = 0
    for t, src in pending:
        if src in trans_map:
            t["text_cn"] = trans_map[src]
            done += 1
            continue
        short = src[:1500]
        res = src
        try:
            res = translator.translate(short)
        except Exception:
            # 限流/瞬时失败：退避 1.5s 重试一次
            try:
                time.sleep(1.5)
                res = translator.translate(short)
            except Exception as e:
                print(f"  [WARN] 翻译失败（保留原文）: {str(e)[:80]}")
                res = src
        # 译文若是错误串 / 应为中文却无中文 → 回退原文
        if _looks_like_error(res) or (not re.search(r"[\u4e00-\u9fff]", res) and re.search(r"[\u4e00-\u9fff]", src)):
            res = src
        trans_map[src] = res
        t["text_cn"] = res
        done += 1
        if done % 10 == 0:
            print(f"  ... 已翻译 {done}/{total}")
        time.sleep(0.3)

    # 写回数据文件（trends_data.json 不入库，仅本地缓存译文）
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 翻译完成：{total} 条推文已写回 text_cn")
    except Exception as e:
        print(f"  [WARN] 写回 trends_data.json 失败: {e}")


def build():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    ensure_text_cn(data)
    # Embed the snapshot so GitHub Pages needs no API, JSON fetch or CDN.
    data["names"] = {key: translate_keyword(key) for key in data.get("series", {})}
    for related in data.get("keyword_related", {}).values():
        for item in related:
            data["names"][item["term"]] = translate_term(item["term"])
    models = {"gpt image 2", "midjourney", "nano banana pro", "stable diffusion", "flux", "dall-e", "dall-e 3"}
    styles = {"cinematic", "photorealistic", "anime", "pixel art", "watercolor", "3d"}
    tools = {"comfyui", "automatic1111", "photoshop"}
    data["types"] = {key: ("model" if key.lower() in models else
                            "style" if key.lower() in styles else
                            "tool" if key.lower() in tools else "concept")
                     for key in data.get("series", {})}
    from prompt_focus import build_focus
    data["techniques"] = build_focus(os.path.join(HERE, "gallery.html"))
    from pathlib import Path
    root = Path(HERE)
    html = (root / "trends-map.template.html").read_text(encoding="utf-8")
    html = html.replace("/* MAP_STYLES */", (root / "trends-map.css").read_text(encoding="utf-8"))
    html = html.replace("/* MAP_SCRIPT */", (root / "trends-map.js").read_text(encoding="utf-8"))
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    html = html.replace("/* MAP_DATA */", payload)
    Path(OUT_FILE).write_text(html, encoding="utf-8")
    print(f"[DONE] Generated {OUT_FILE}")



if __name__ == "__main__":
    build()
