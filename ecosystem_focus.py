"""Explicit model/tool mentions, grouped by family rather than guessed versions."""
from prompt_focus import build_focus

# Only literal mentions in record titles / prompt text count. Gallery source
# buckets and tool labels are intentionally excluded because they can be inferred.
TERMS = [
    ('gpt-image','GPT Image','image_model',r'gpt[- ]?image|chatgpt image'),
    ('nano-banana','Nano Banana','image_model',r'nano[- ]?banana'),
    ('midjourney','Midjourney','image_model',r'midjourney|MJ提示词|MJ咒语|MJ\s+v\d'),
    ('flux','FLUX','image_model',r'flux(?:\.\d+)?'),
    ('stable-diffusion','Stable Diffusion','image_model',r'stable diffusion|稳定扩散'),
    ('sdxl','SDXL','image_model',r'sdxl'),
    ('dalle','DALL·E','image_model',r'dall[-· ]?e'),
    ('imagen','Imagen','image_model',r'imagen'),
    ('ideogram','Ideogram','image_model',r'ideogram'),
    ('recraft','Recraft','image_model',r'recraft'),
    ('firefly','Adobe Firefly','image_model',r'adobe firefly|firefly'),
    ('qwen-image','Qwen Image','image_model',r'qwen[- ]image|通义万相'),
    ('seedream','Seedream','image_model',r'seedream'),
    ('z-image','Z-Image','image_model',r'z[- ]image'),
    ('sora','Sora','video_model',r'sora'),
    ('veo','Veo','video_model',r'veo'),
    ('kling','Kling / 可灵','video_model',r'kling|可灵'),
    ('seedance','Seedance','video_model',r'seedance'),
    ('hailuo','Hailuo / 海螺','video_model',r'hailuo|海螺'),
    ('minimax','MiniMax','assistant',r'minimax'),
    ('wan','Wan / 万相视频','video_model',r'wan[- ]?\d(?:\.\d+)?|wan video|wan ai|wan i2v|万相视频'),
    ('hunyuan-video','HunyuanVideo','video_model',r'hunyuan[- ]?video|混元视频'),
    ('ltx','LTX Video','video_model',r'ltx[- ](?:video|studio|2)'),
    ('pika','Pika','video_model',r'pika(?:labs)?'),
    ('luma','Luma / Dream Machine','video_model',r'luma|dream machine'),
    ('chatgpt','ChatGPT','assistant',r'chatgpt'),
    ('gemini','Gemini','assistant',r'gemini'),
    ('claude','Claude','assistant',r'claude'),
    ('grok','Grok','assistant',r'grok'),
    ('deepseek','DeepSeek','assistant',r'deepseek'),
    ('comfyui','ComfyUI','tool',r'comfyui'),
    ('a1111','AUTOMATIC1111','tool',r'automatic1111|a1111'),
    ('runway','Runway','tool',r'runwayml|runway\s+(?:gen[- ]?\d|ai)|runway平台'),
    ('higgsfield','Higgsfield','tool',r'higgsfield'),
    ('krea','Krea','tool',r'krea'),
    ('leonardo','Leonardo AI','tool',r'leonardo[. ]ai'),
    ('freepik','Freepik','tool',r'freepik'),
    ('jimeng','即梦','tool',r'即梦|jimeng'),
    ('doubao','豆包','tool',r'豆包|doubao'),
    ('flow','Google Flow','tool',r'google flow'),
    ('capcut','CapCut / 剪映','tool',r'capcut|剪映'),
    ('photoshop','Photoshop','tool',r'photoshop'),
    ('blender','Blender','tool',r'blender'),
    ('unreal','Unreal Engine','tool',r'unreal engine|ue5'),
    ('suno','Suno','tool',r'suno'),
    ('elevenlabs','ElevenLabs','tool',r'elevenlabs'),
    ('lora','LoRA','workflow',r'lora'),
    ('controlnet','ControlNet','workflow',r'controlnet'),
    ('img2img','图生图','workflow',r'img2img|image[- ]to[- ]image|图生图'),
    ('img2video','图生视频','workflow',r'image[- ]to[- ]video|i2v|图生视频'),
    ('text2video','文生视频','workflow',r'text[- ]to[- ]video|t2v|文生视频'),
    ('inpainting','局部重绘','workflow',r'inpaint(?:ing)?|局部重绘'),
    ('upscale','超分放大','workflow',r'upscal(?:e|ing|er)|超分辨率|超分放大'),
    ('sref','风格参考 / SREF','workflow',r'--sref|style reference|风格参考'),
    ('cinematic','电影感','style',r'cinematic|电影感'),
    ('photoreal','照片写实','style',r'photoreal(?:istic)?|照片级写实'),
    ('anime','动漫','style',r'anime|动漫'),
    ('pixel-art','像素艺术','style',r'pixel art|像素风'),
    ('3d-render','3D 渲染','style',r'3d render(?:ing)?|3D渲染'),
]


def build_ecosystem(path):
    vocabulary = [(key,name,category,aliases,
                   f'统计标题和提示词文本中对 {name} 的明确提及；同一家族的版本合并统计，不代表已核实使用。')
                  for key,name,category,aliases in TERMS]
    data = build_focus(path, vocabulary, cinema_required=False)
    data['mode'] = 'ecosystem'
    data['method'] = '从本站收录案例的标题及提示词文本中识别模型、平台、工具、工作流和风格；按链接及相同文本去重。不同版本归并为家族名，一条记录可提及多个关键词，不依据站内来源分类推断实际使用的模型。'
    return data
