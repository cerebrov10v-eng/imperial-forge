"""
Imperial Forge V10 — Pipeline orquestador
Flujo: Brief → Guion (Kimi K2.5) → Imagen (Pollinations) → TTS (edge-tts)
       → Video (Seedance/FFmpeg) → Ensamblado (moviepy) → Thumbnail → Entrega
"""
import asyncio
import json
import logging
import time
import uuid
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
import httpx

from backend.config import (
    KIMI_PROXY_URL, SOCIAL_ENGINE_URL, FORGE_API_KEY,
    OUTPUT_VIDEOS, OUTPUT_AUDIO, OUTPUT_IMAGES,
    TTS_VOICE_AMANDA, TTS_VOICE_HENRY, TTS_VOICE_EN_US,
    POLLINATIONS_URL, POLLINATIONS_WIDTH, POLLINATIONS_HEIGHT,
    SEEDANCE_API_KEY, SEEDANCE_API_BASE, SEEDANCE_MODEL_DEFAULT,
)
from backend.schemas import VideoForgeRequest, AudioForgeRequest, LandingForgeRequest, AdCreativeRequest
from backend.database import get_db, ForgeJob, ForgeAsset

logger = logging.getLogger("imperial_forge.pipeline")

AVATAR_VOICES = {
    "amanda": TTS_VOICE_AMANDA,
    "henry":  TTS_VOICE_HENRY,
    "en_us":  TTS_VOICE_EN_US,
}


# ════════════════════════════════════════════════════════════════
# STEP 1 — Generar guion con Kimi K2.5
# ════════════════════════════════════════════════════════════════
async def generate_script(brief_data: dict, style: str = "social_media", language: str = "es") -> str:
    style_prompts = {
        "publicidad":   "comercial directo, beneficios claros, llamada a la acción fuerte",
        "corporativo":  "profesional, autoridad, confianza",
        "cinematic":    "narrativo, emocional, dramático",
        "social_media": "casual, energético, gancho en 3 segundos",
        "testimonial":  "auténtico, personal, conversacional",
    }
    tone = style_prompts.get(style, style_prompts["social_media"])

    product = brief_data.get("product_name", "el producto")
    description = brief_data.get("description", "")
    audience = brief_data.get("target_audience", "público general")
    cta = brief_data.get("cta", "Más información")

    system = (
        f"Eres un redactor creativo experto en vídeo corto para redes sociales. "
        f"Idioma: {'español' if language == 'es' else 'inglés'}. "
        f"Tono: {tone}. Máximo 60 palabras para narración de 5-10 segundos."
    )
    user = (
        f"Escribe el guion de voz en off para un vídeo de {product}. "
        f"Público: {audience}. Descripción: {description}. CTA final: {cta}. "
        f"Solo el texto de narración, sin acotaciones."
    )

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                f"{KIMI_PROXY_URL}/v1/chat/completions",
                json={
                    "model": "moonshot-v1-8k",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user},
                    ],
                    "max_tokens": 200,
                    "temperature": 0.8,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"Kimi script fallback: {e}")
        return f"{product}. {description} {cta}."


# ════════════════════════════════════════════════════════════════
# STEP 2 — TTS con edge-tts
# ════════════════════════════════════════════════════════════════
async def generate_tts(text: str, voice: str, output_path: Path) -> Path:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    logger.info(f"TTS generado: {output_path}")
    return output_path


# ════════════════════════════════════════════════════════════════
# STEP 3 — Imagen con Pollinations.ai
# ════════════════════════════════════════════════════════════════
async def generate_image(prompt: str, output_path: Path, width: int = POLLINATIONS_WIDTH, height: int = POLLINATIONS_HEIGHT) -> Path:
    import urllib.parse
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)
        logger.info(f"Imagen generada: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Pollinations error: {e}")
        raise


# ════════════════════════════════════════════════════════════════
# STEP 4 — Ensamblado con moviepy (imagen + audio → video)
# ════════════════════════════════════════════════════════════════
def assemble_video_ffmpeg(image_path: Path, audio_path: Path, output_path: Path, duration: int = 5) -> Path:
    """Ensambla imagen + audio en vídeo usando FFmpeg directamente (sin moviepy overhead)."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr[-500:]}")
    logger.info(f"Vídeo ensamblado: {output_path}")
    return output_path


# ════════════════════════════════════════════════════════════════
# STEP 5 — Thumbnail (Pollinations en 1280x720)
# ════════════════════════════════════════════════════════════════
async def generate_thumbnail(prompt: str, output_path: Path) -> Path:
    return await generate_image(prompt, output_path, width=1280, height=720)


# ════════════════════════════════════════════════════════════════
# STEP 6 — Entrega a Social Engine
# ════════════════════════════════════════════════════════════════
async def deliver_to_social_engine(job_id: str, video_path: Path, thumbnail_path: Path, brief: dict) -> dict:
    payload = {
        "job_id":       job_id,
        "source":       "imperial-forge",
        "version":      "1.0",
        "assets": [
            {"type": "video",     "local_path": str(video_path)},
            {"type": "thumbnail", "local_path": str(thumbnail_path)},
        ],
        "brief_data": brief,
        "callback_url": f"http://localhost:8300/api/pipeline/callback",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{SOCIAL_ENGINE_URL}/api/pipeline/deliver",
                json=payload,
                headers={"X-API-Key": FORGE_API_KEY, "X-Job-ID": job_id},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"Entrega a Social Engine fallida: {e}")
        return {"status": "error", "error": str(e)}


# ════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL — Video Forge
# ════════════════════════════════════════════════════════════════
async def run_video_pipeline(job_id: str, req: VideoForgeRequest):
    start = time.monotonic()
    brief = req.brief.model_dump()
    meta  = req.meta

    with get_db() as db:
        job = db.get(ForgeJob, job_id)
        if job:
            job.status = "processing"

    try:
        # 1. Guion
        script = await generate_script(brief, style=meta.style, language=meta.language)
        logger.info(f"[{job_id}] Script: {script[:80]}…")

        # 2. TTS
        voice = AVATAR_VOICES.get(meta.avatar or "amanda", TTS_VOICE_AMANDA)
        audio_path = OUTPUT_AUDIO / f"{job_id}.mp3"
        await generate_tts(script, voice, audio_path)

        # 3. Imagen de fondo
        image_prompt = (
            f"Professional advertisement for {brief['product_name']}, "
            f"{meta.style} style, {'9:16 vertical' if meta.format == '9:16' else '16:9 horizontal'}, "
            f"high quality commercial photography, no text"
        )
        image_path = OUTPUT_IMAGES / f"{job_id}.jpg"
        await generate_image(image_prompt, image_path)

        # 4. Ensamblado FFmpeg
        video_path = OUTPUT_VIDEOS / f"{job_id}.mp4"
        assemble_video_ffmpeg(image_path, audio_path, video_path, duration=meta.duration)

        # 5. Thumbnail
        thumb_path = OUTPUT_IMAGES / f"{job_id}_thumb.jpg"
        await generate_thumbnail(image_prompt + ", thumbnail, 16:9", thumb_path)

        # 6. Guardar assets en DB
        duration_s = time.monotonic() - start
        with get_db() as db:
            job = db.get(ForgeJob, job_id)
            if job:
                job.status = "done"
                job.completed_at = datetime.utcnow()
                job.duration_s = duration_s
                job.result_urls = json.dumps({
                    "video":     str(video_path),
                    "audio":     str(audio_path),
                    "image":     str(image_path),
                    "thumbnail": str(thumb_path),
                    "script":    script,
                })
            for atype, apath in [("video", video_path), ("audio", audio_path), ("thumbnail", thumb_path)]:
                db.add(ForgeAsset(job_id=job_id, asset_type=atype, local_path=str(apath)))

        # 7. Entregar a Social Engine (si callback configurado)
        if req.callback_url or SOCIAL_ENGINE_URL:
            await deliver_to_social_engine(job_id, video_path, thumb_path, brief)

        logger.info(f"[{job_id}] Video pipeline completado en {duration_s:.1f}s")

    except Exception as e:
        logger.error(f"[{job_id}] Pipeline error: {e}", exc_info=True)
        with get_db() as db:
            job = db.get(ForgeJob, job_id)
            if job:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.utcnow()
                job.duration_s = time.monotonic() - start


# ════════════════════════════════════════════════════════════════
# PIPELINE — Audio Forge
# ════════════════════════════════════════════════════════════════
async def run_audio_pipeline(job_id: str, req: AudioForgeRequest):
    start = time.monotonic()
    voice = AVATAR_VOICES.get(req.meta.voice, TTS_VOICE_AMANDA)
    audio_path = OUTPUT_AUDIO / f"{job_id}.{req.meta.output_format}"

    with get_db() as db:
        job = db.get(ForgeJob, job_id)
        if job:
            job.status = "processing"

    try:
        await generate_tts(req.text, voice, audio_path)
        duration_s = time.monotonic() - start
        with get_db() as db:
            job = db.get(ForgeJob, job_id)
            if job:
                job.status = "done"
                job.completed_at = datetime.utcnow()
                job.duration_s = duration_s
                job.result_urls = json.dumps({"audio": str(audio_path)})
            db.add(ForgeAsset(job_id=job_id, asset_type="audio", local_path=str(audio_path)))
    except Exception as e:
        logger.error(f"[{job_id}] Audio pipeline error: {e}")
        with get_db() as db:
            job = db.get(ForgeJob, job_id)
            if job:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.utcnow()
                job.duration_s = time.monotonic() - start
