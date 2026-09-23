"""Mine explicit filmmaking techniques in the local gallery's prompt text.

No API calls: counts are deduplicated archived examples, never platform heat.
The vocabulary is curated; evidence and co-occurrences come from actual text.
"""
import hashlib
import itertools
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# id, Chinese label, dimension, aliases, editorial explanation
FOCI = [
    ('genre-scifi','科幻','genre',r'sci[- ]?fi|science fiction|科幻|星际战争','未来科技、太空探索等科幻题材线索；不据此推断成片类型。'),
    ('genre-fantasy','奇幻 / 魔幻','genre',r'fantasy|奇幻|魔幻|魔法世界','魔法、异世界与超自然世界观的题材线索。'),
    ('genre-wuxia','武侠 / 仙侠','genre',r'wuxia|xianxia|武侠|仙侠|修仙|江湖恩怨','武林、江湖、修仙等东方幻想叙事线索。'),
    ('genre-action','动作 / 冒险','genre',r'action[- ]packed|action (?:film|movie|scene|sequence|thriller)|adventure (?:film|movie|story)|fight scene|martial arts|动作片|动作电影|打斗场景|格斗|冒险故事','打斗、追逐与冒险情节；不把普通人物动作归入动作片。'),
    ('genre-mystery','悬疑 / 犯罪','genre',r'thriller|mystery (?:film|movie|story|drama)|crime (?:film|drama|scene|thriller)|detective (?:story|film|drama)|悬疑|犯罪片|犯罪剧|刑侦|侦探故事','谜案、调查、犯罪与惊悚叙事线索。'),
    ('genre-horror','恐怖 / 灵异','genre',r'horror|ghost story|haunted house|恐怖片|恐怖电影|恐怖故事|灵异|鬼故事|丧尸','恐怖、灵异及怪物威胁相关线索。'),
    ('genre-romance','爱情 / 情感','genre',r'romance|romantic (?:film|movie|drama|story|scene)|love story|爱情|言情|情感剧|恋爱故事','恋爱关系与情感叙事；单纯浪漫光线或色调不归入此类。'),
    ('genre-period','历史 / 古装','genre',r'period drama|historical (?:drama|film|movie|epic)|costume drama|历史剧|历史电影|古装剧|古装电影|宫廷剧|民国剧','历史时代、古装与宫廷叙事线索；不只凭服饰判断。'),
    ('genre-war','战争 / 军事','genre',r'war (?:film|movie|drama|scene)|military (?:film|drama|operation)|battlefield|战争片|战争电影|战争场景|军事题材|战场','战场、军事行动与战争叙事线索。'),
    ('genre-comedy','喜剧','genre',r'comedy|comedic scene|喜剧|喜剧片','明确的喜剧或诙谐叙事类型表达。'),
    ('genre-family','家庭 / 现实生活','genre',r'family drama|domestic drama|slice of life|家庭剧|家庭伦理|现实主义题材|生活流','家庭关系与日常生活叙事线索。'),
    ('genre-superhero','超级英雄','genre',r'superhero|super hero|超级英雄','具有超级英雄设定的人物与故事线索。'),
    ('genre-western','西部','genre',r'western (?:film|movie|genre)|wild west|西部片|西部电影','西部世界、边疆与牛仔故事的明确题材表达。'),
    ('close-up','特写','framing',r'close[- ]?up|特写','集中表现面部、手部或物体细节。'),
    ('wide-shot','远景 / 全景','framing',r'wide shot|long shot|establishing shot|远景|全景镜头|建立镜头','交代环境与主体的空间关系。'),
    ('medium-shot','中景','framing',r'medium shot|mid shot|中景','兼顾人物动作和周围环境。'),
    ('low-angle','低机位仰拍','framing',r'low[- ]angle|worm.s.eye|仰拍|低机位','用较低的观察位置塑造主体的力量感。'),
    ('overhead','俯拍 / 鸟瞰','framing',r'overhead shot|top[- ]down|bird.s.eye|俯拍|鸟瞰','从上方组织人物、物体和场景。'),
    ('symmetry','对称构图','framing',r'symmetr(?:ic|ical) composition|symmetrical framing|对称构图','通过画面两侧的对应关系建立秩序。'),
    ('negative-space','留白','framing',r'negative space|留白','为主体的视线、动作或文字预留空间。'),
    ('shallow-dof','浅景深','framing',r'shallow depth of field|shallow dof|浅景深','让主体与虚化背景分离。'),
    ('bokeh','散景虚化','framing',r'bokeh|散景|背景虚化','强调失焦区域及光斑的视觉表现。'),
    ('anamorphic','变形宽银幕','framing',r'anamorphic|变形宽银幕|变形镜头','指定宽银幕镜头的画面特征。'),
    ('tracking','跟拍','motion',r'tracking shot|follow shot|camera follows|跟拍|跟随镜头','镜头与运动主体一起移动。'),
    ('dolly','推轨 / 拉轨','motion',r'dolly[- ](?:in|out|shot|zoom|movement|camera)|camera dolly|推轨|拉轨|轨道镜头','通过摄影机的位移改变观看距离。'),
    ('push-in','缓慢推进','motion',r'push[- ]in|camera pushes|slow zoom in|缓慢推进|镜头推进','逐渐靠近主体，突出情绪或细节。'),
    ('pan','横摇镜头','motion',r'camera pans|panning shot|pan shot|横摇|摇镜头','摄影机转动方向，展开横向空间。'),
    ('orbit','环绕运镜','motion',r'orbit(?:ing|al)? shot|camera orbits|orbit camera|环绕运镜|环绕镜头','围绕主体移动，展示空间和形体。'),
    ('handheld','手持镜头','motion',r'handheld|hand[- ]held camera|手持镜头|手持摄影','通过手持感营造现场感和不稳定感。'),
    ('slow-motion','慢动作','motion',r'slow[- ]motion|慢动作|慢镜头','延长动作的可见过程。'),
    ('time-lapse','延时摄影','motion',r'time[- ]?lapse|延时摄影|延时拍摄','压缩较长时间内的环境变化。'),
    ('static-camera','固定机位','motion',r'static camera|locked[- ]off|fixed camera|固定机位|固定镜头','保持视点稳定，突出画面内部运动。'),
    ('golden-hour','黄金时刻','lighting',r'golden hour|黄金时刻|黄金时间','指定日出或日落附近的暖色自然光。'),
    ('rim-light','轮廓光','lighting',r'rim light(?:ing)?|轮廓光','沿主体边缘形成亮线，与背景分离。'),
    ('backlight','逆光','lighting',r'backlit|backlight(?:ing)?|逆光','让主光源位于主体后方。'),
    ('soft-light','柔光','lighting',r'soft light(?:ing)?|diffused light|柔光|漫射光','控制阴影边缘，突出柔和的表面过渡。'),
    ('hard-light','硬光','lighting',r'hard light(?:ing)?|harsh light|硬光|硬质光','使用清晰阴影和鲜明的明暗分界。'),
    ('volumetric','体积光','lighting',r'volumetric light(?:ing)?|god rays|体积光|丁达尔','通过雾气或颗粒表现可见光束。'),
    ('chiaroscuro','明暗对照','lighting',r'chiaroscuro|明暗对照|明暗对比','用强烈的亮暗区域关系组织画面。'),
    ('neon','霓虹光','lighting',r'neon light(?:ing)?|neon[- ]lit|霓虹光|霓虹灯','以彩色发光源营造夜景氛围。'),
    ('practical-light','场景实景光源','lighting',r'practical light(?:ing|s)?|实景光源|实用光源','强调画面内灯具等可见光源。'),
    ('film-grain','胶片颗粒','color',r'film grain|胶片颗粒','为画面加入胶片式颗粒质感。'),
    ('color-grade','电影调色','color',r'color grad(?:e|ing)|colour grad(?:e|ing)|电影调色|色彩分级','明确整体色彩处理和明暗倾向。'),
    ('teal-orange','青橙色调','color',r'teal and orange|teal[- /]orange|青橙|橙青','以冷暖色彩分离主体和环境。'),
    ('desaturated','低饱和','color',r'desaturated|muted colou?rs|low saturation|低饱和','压低色彩强度，保留明暗层次。'),
    ('monochrome','黑白影像','color',r'black[- ]and[- ]white|monochrome|黑白影像|黑白摄影','使用黑白或单色层次表达主题。'),
    ('motion-blur','运动模糊','color',r'motion blur|运动模糊|动态模糊','用运动轨迹表现速度和时间。'),
    ('halation','胶片光晕','color',r'halation|胶片光晕','表现高亮边缘的光晕扩散。'),
    ('storyboard','分镜设计','story',r'storyboard|shot list|分镜|镜头清单','把场景拆解成可执行的镜头序列。'),
    ('multi-shot','多镜头叙事','story',r'multi[- ]shot|shot sequence|多镜头|镜头序列','通过多个视点组织一段场景或故事。'),
    ('long-take','长镜头 / 一镜到底','story',r'long take|one[- ]take|single continuous shot|一镜到底|长镜头','在连续镜头中完成动作和空间转换。'),
    ('match-cut','匹配剪辑','story',r'match cut|匹配剪辑|匹配剪切','利用形状、动作等相似性衔接镜头。'),
    ('transition','镜头转场','story',r'seamless transition|scene transition|cross[- ]dissolve|无缝转场|镜头转场|叠化','明确两个镜头之间的过渡方式。'),
    ('beat-sync','节拍同步','story',r'beat[- ]sync|sync.{0,15}(?:music|beat)|节拍同步|音乐卡点','让镜头或动作变化与声音节奏呼应。'),
    ('timed-beats','分段时间轴','story',r'\d+(?:\.\d+)?\s*[-–—~]\s*\d+(?:\.\d+)?\s*(?:seconds?|secs?|s\b|秒)|\d{1,2}:\d{2}\s*[-–—]\s*\d{1,2}:\d{2}|分段时间轴','按时间段安排镜头、动作和变化。'),
    ('duration','片段时长','story',r'\b\d+[- ]second\b|duration\s*[:：]?\s*\d+|时长\s*[:：]?\s*\d+|\d+秒(?:视频|短片|镜头)','明确片段的时间预算，为动作和镜头分配空间。'),
    ('fast-paced','快速节奏','story',r'fast[- ]paced|rapid cuts|quick cuts|快速剪辑|快节奏','通过紧凑动作或快速切换提高节奏。'),
    ('slow-paced','舒缓节奏','story',r'slow[- ]paced|lingering shot|缓慢节奏|舒缓节奏|慢节奏','为动作和情绪留出更长的观看时间。'),
    ('character-consistency','角色一致性','constraint',r'character consistency|consistent character|same character|角色一致|人物一致','约束跨镜头的角色身份和外观。'),
    ('identity','面部身份保持','constraint',r'facial identity|preserve.{0,20}(?:face|identity)|same face|面部一致|保持.{0,8}(?:面部|身份)|不改变.{0,5}(?:脸|面部)','保持参考人物的面部特征。'),
    ('reference','参考图约束','constraint',r'reference image|reference photo|参考图|参考照片','以给定图像约束主体、场景或姿态。'),
    ('continuity','时间一致性','constraint',r'temporal consistency|temporal coherence|时间一致性|时序一致性|帧间一致','控制相邻帧之间的稳定与连贯。'),
    ('negative','负面约束','constraint',r'negative prompt|负面提示词|负向提示词','明确希望避免的画面元素或缺陷。'),
]

CINEMA = re.compile(r'cinematic|cinema|storyboard|camera movement|tracking shot|dolly|seedance|kling|sora|电影|影视|运镜|分镜|剪辑|镜头', re.I)


def pattern(aliases):
    # English terms require boundaries; Chinese terms can occur within sentences.
    return re.compile(r'(?<![a-z])(?:'+aliases+r')(?![a-z])', re.I)


def build_focus(gallery_path):
    source = Path(gallery_path).read_text(encoding='utf-8')
    entries = json.JSONDecoder().raw_decode(source.split('const ALL = ', 1)[1])[0]
    rules = [(row, pattern(row[3])) for row in FOCI]
    seen_urls, seen_text = set(), set()
    eligible = []
    today = datetime.now(timezone.utc).date()
    dates_in_archive = []
    for entry in entries:
        try:
            day = datetime.strptime(entry.get('created_at', '')[:10], '%Y-%m-%d').date()
        except ValueError:
            continue
        if day > today:
            continue
        dates_in_archive.append(day)
        text = (entry.get('prompt') or '').strip()
        translated = (entry.get('prompt_zh') or '').strip()
        if max(len(text), len(translated)) < 80 or not CINEMA.search(text+' '+translated):
            continue
        url = entry.get('tweet_url', '')
        digest = hashlib.sha256(re.sub(r'\s+', '', text or translated).lower().encode()).hexdigest()
        if not url or url in seen_urls or digest in seen_text:
            continue
        seen_urls.add(url); seen_text.add(digest)
        eligible.append((entry, day, text, translated))
    end = max(dates_in_archive, default=today)
    dates = [(end-timedelta(days=29-i)).isoformat() for i in range(30)]
    index = {day:i for i,day in enumerate(dates)}
    series = {row[0]:[0]*30 for row in FOCI}
    pairs = defaultdict(lambda:[0]*30)
    examples = defaultdict(list)
    corpus = [0]*30
    genre_covered = [0]*30
    for entry, day, text, translated in eligible:
        if day.isoformat() not in index:
            continue
        idx = index[day.isoformat()]; corpus[idx] += 1
        found = []
        for row, rule in rules:
            match = rule.search(text)
            evidence_text = text
            if not match:
                match = rule.search(translated); evidence_text = translated
            if not match:
                continue
            key = row[0]; found.append(key); series[key][idx] += 1
            excerpt = evidence_text[max(0,match.start()-85):match.end()+135].strip()
            examples[key].append({
                'date':day.isoformat(), 'url':entry['tweet_url'],
                'author_name':entry.get('author',''), 'title':entry.get('title',''),
                'excerpt':excerpt, 'matched':match.group(),
                'source':'小红书' if 'xiaohongshu.com' in entry['tweet_url'] else 'Reddit' if 'reddit.com' in entry['tweet_url'] else 'X',
            })
        if any(key.startswith('genre-') for key in found): genre_covered[idx] += 1
        for a,b in itertools.combinations(sorted(found), 2): pairs[(a,b)][idx] += 1
    # Do not invent nodes for techniques absent from this sample.
    active = {key for key,values in series.items() if sum(values)}
    return {
        'mode':'technique', 'dates':dates, 'updated_at':f'{end.isoformat()} · 样本截至',
        'series':{key:values for key,values in series.items() if key in active},
        'names':{row[0]:row[1] for row in FOCI},
        'types':{row[0]:('shot' if row[0] in {'close-up','wide-shot','medium-shot','low-angle','overhead'} else 'composition' if row[2]=='framing' else row[2]) for row in FOCI},
        'descriptions':{row[0]:row[4] for row in FOCI},
        'aliases':{row[0]:row[3].replace('|',' / ') for row in FOCI},
        'keyword_related':{}, 'keyword_tweets':{},
        'graph_edges':[{'source':a,'target':b,'values':values} for (a,b),values in pairs.items() if sum(values)>=2],
        'examples':dict(examples), 'corpus':corpus, 'genre_covered':genre_covered,
        'archive_count':len(entries), 'eligible_count':sum(corpus),
        'method':'从本站收录的影视相关提示词文本（含描述）识别中英文技法表达；按原文链接及相同文本去重，每条样本对每项技法最多计一次。否定或排除语句也可能命中，提及不代表采用。',
    }
