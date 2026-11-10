import os
import hashlib
import asyncio
import edge_tts
from config import Config

# Microsoft Neural Voice configurations for 4 languages
VOICE_MAP = {
    'zh-TW': 'zh-TW-HsiaoChenNeural',
    'en': 'en-US-JennyNeural',
    'ja': 'ja-JP-NanamiNeural',
    'ko': 'ko-KR-SunHiNeural'
}

DEFAULT_VOICE = 'zh-TW-HsiaoChenNeural'

def get_audio_filename(text: str, voice: str) -> str:
    hash_str = hashlib.md5(f"{voice}_{text.strip()}".encode('utf-8')).hexdigest()
    return f"{hash_str}.mp3"

async def _synthesize_edge_tts(text: str, voice: str, output_path: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_speech(text: str, lang: str = 'zh-TW', voice: str = None) -> dict:
    """
    Synthesizes speech using edge-tts with local disk caching.
    Returns: {'url': '/static/audio_cache/xxxx.mp3', 'cached': bool, 'voice': voice}
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    clean_text = text.strip()[:2000] # Safe length limit for single audio tour
    target_voice = voice or VOICE_MAP.get(lang, DEFAULT_VOICE)

    os.makedirs(Config.AUDIO_CACHE_FOLDER, exist_ok=True)
    filename = get_audio_filename(clean_text, target_voice)
    filepath = os.path.join(Config.AUDIO_CACHE_FOLDER, filename)
    public_url = f"/static/audio_cache/{filename}"

    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return {
            'url': public_url,
            'cached': True,
            'voice': target_voice,
            'filename': filename
        }

    try:
        asyncio.run(_synthesize_edge_tts(clean_text, target_voice, filepath))
        return {
            'url': public_url,
            'cached': False,
            'voice': target_voice,
            'filename': filename
        }
    except Exception as e:
        print(f"[TTS Error] {e}")
        # Fallback or re-raise
        raise e

