"""
Imperial Forge V10 — Configuración soberana
Stack: Kimi K2.5 + Seedance 2.0 + edge-tts + Pollinations.ai + moviepy
Puerto: 8300
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env del Cerebro V10 (fuente única de verdad)
_ENV_PATH = Path("E:/Cerebro V10/.env")
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

# ── API Keys ────────────────────────────────────────────────────
MOONSHOT_API_KEY: str = os.getenv("MOONSHOT_API_KEY", "")
FAL_AI_KEY: str = os.getenv("FAL_AI_KEY", "")  # fal.ai — sirve para Seedance + imágenes Flux
SEEDANCE_API_KEY: str = os.getenv("SEEDANCE_API_KEY", "") or FAL_AI_KEY  # fal.ai hostea Seedance

# ── Servicios internos ──────────────────────────────────────────
KIMI_PROXY_URL: str = os.getenv("KIMI_PROXY_URL", "http://localhost:9898")
SOCIAL_ENGINE_URL: str = os.getenv("SOCIAL_ENGINE_URL", "http://localhost:8200")
CEREBRO_API_URL: str = os.getenv("CEREBRO_API_URL", "http://localhost:8000")

# ── Auth ────────────────────────────────────────────────────────
FORGE_API_KEY: str = os.getenv("FORGE_API_KEY", "forge-internal-key-v10")

# ── Directorios de output ───────────────────────────────────────
OUTPUT_BASE = Path("E:/Cerebro V10/output")
OUTPUT_VIDEOS = OUTPUT_BASE / "videos"
OUTPUT_AUDIO  = OUTPUT_BASE / "audio"
OUTPUT_IMAGES = OUTPUT_BASE / "images"
OUTPUT_LANDING = OUTPUT_BASE / "landings"
OUTPUT_ADS    = OUTPUT_BASE / "ads"

for _d in [OUTPUT_VIDEOS, OUTPUT_AUDIO, OUTPUT_IMAGES, OUTPUT_LANDING, OUTPUT_ADS]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Motores ─────────────────────────────────────────────────────
# Video: Seedance 2.0 via fal.ai
# fal.ai también expone Flux para imágenes de alta calidad
SEEDANCE_API_BASE     = "https://fal.run"                    # fal.ai endpoint
SEEDANCE_MODEL_DEFAULT = "fal-ai/bytedance/seedance-1-lite"  # 720p/5s
SEEDANCE_MODEL_PRO     = "fal-ai/bytedance/seedance-1-pro"   # 1080p/10s

# Imágenes premium via fal.ai (Flux) — activar si FAL_AI_KEY disponible
FAL_IMAGE_MODEL = "fal-ai/flux/schnell"   # rápido, buena calidad
FAL_IMAGE_MODEL_PRO = "fal-ai/flux-pro"  # calidad máxima

# Audio TTS: edge-tts (gratis, ilimitado)
TTS_VOICE_AMANDA = "es-ES-ElviraNeural"   # Amanda Snow — latina, tech
TTS_VOICE_HENRY  = "es-ES-AlvaroNeural"  # Henry Callin — ejecutivo
TTS_VOICE_EN_US  = "en-US-JennyNeural"

# Imágenes: Pollinations.ai (gratis, sin key)
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"
POLLINATIONS_WIDTH  = 1280
POLLINATIONS_HEIGHT = 720

# ── DB ──────────────────────────────────────────────────────────
DB_PATH = Path("E:/Cerebro V10/data/imperial_forge.db")
DB_URL  = f"sqlite:///{DB_PATH}"
