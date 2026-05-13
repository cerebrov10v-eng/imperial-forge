"""
Imperial Forge V10 — FastAPI Server
Puerto: 8300
Stack soberano: Kimi K2.5 + Seedance + edge-tts + Pollinations.ai + moviepy
"""
import uuid
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from backend.config import FORGE_API_KEY
from backend.database import init_db, get_db, ForgeJob
from backend.schemas import (
    VideoForgeRequest, AudioForgeRequest, LandingForgeRequest,
    AdCreativeRequest, MasterForgeRequest,
    ForgeJobResponse, ForgeStatusResponse,
)
from backend.pipeline import run_video_pipeline, run_audio_pipeline, deliver_to_social_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("imperial_forge")


# ── App ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Imperial Forge V10",
    description="Fábrica de contenido multimedia — stack soberano 0EUR/mes",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Imperial Forge V10 — DB SQLAlchemy WAL OK")
    logger.info("Imperial Forge V10 — listo en puerto 8300")


# ── Auth ─────────────────────────────────────────────────────────
def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != FORGE_API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return x_api_key


# ════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {
        "status":  "ok",
        "service": "imperial-forge-v10",
        "version": "1.0.0",
        "engines": ["kimi-k2.5", "seedance-2.0", "edge-tts", "pollinations.ai", "moviepy"],
    }


# ── Video Engine ─────────────────────────────────────────────────
@app.post("/api/video/generate", response_model=ForgeJobResponse)
async def generate_video(
    req: VideoForgeRequest,
    background_tasks: BackgroundTasks,
    _: str = Depends(verify_api_key),
):
    job_id = str(uuid.uuid4())
    with get_db() as db:
        db.add(ForgeJob(
            id=job_id, job_type="video", status="queued",
            brief_data=json.dumps(req.brief.model_dump()),
        ))
    background_tasks.add_task(run_video_pipeline, job_id, req)
    return ForgeJobResponse(
        job_id=job_id, status="accepted", job_type="video",
        message="Vídeo en cola. Pipeline: Kimi guion → Pollinations imagen → edge-tts voz → FFmpeg.",
        webhook_url=req.callback_url,
    )


# ── Audio Engine ─────────────────────────────────────────────────
@app.post("/api/audio/generate", response_model=ForgeJobResponse)
async def generate_audio(
    req: AudioForgeRequest,
    background_tasks: BackgroundTasks,
    _: str = Depends(verify_api_key),
):
    job_id = str(uuid.uuid4())
    with get_db() as db:
        db.add(ForgeJob(
            id=job_id, job_type="audio", status="queued",
            brief_data=json.dumps({"text": req.text}),
        ))
    background_tasks.add_task(run_audio_pipeline, job_id, req)
    return ForgeJobResponse(
        job_id=job_id, status="accepted", job_type="audio",
        message=f"Audio TTS en cola. Voz: {req.meta.voice}.",
        webhook_url=req.callback_url,
    )


# ── Landing Forge (stub Fase 3) ───────────────────────────────────
@app.post("/api/landing/generate", response_model=ForgeJobResponse)
async def generate_landing(
    req: LandingForgeRequest,
    _: str = Depends(verify_api_key),
):
    job_id = str(uuid.uuid4())
    with get_db() as db:
        db.add(ForgeJob(
            id=job_id, job_type="landing", status="queued",
            brief_data=json.dumps(req.brief.model_dump()),
        ))
    # TODO Fase 3: Jinja2 + templates HTML
    return ForgeJobResponse(
        job_id=job_id, status="accepted", job_type="landing",
        message=f"Landing {req.meta.template} en cola. Implementación Fase 3.",
        webhook_url=req.callback_url,
    )


# ── Ad Creative Studio (stub Fase 4) ─────────────────────────────
@app.post("/api/ads/generate", response_model=ForgeJobResponse)
async def generate_ads(
    req: AdCreativeRequest,
    _: str = Depends(verify_api_key),
):
    job_id = str(uuid.uuid4())
    with get_db() as db:
        db.add(ForgeJob(
            id=job_id, job_type="ads", status="queued",
            brief_data=json.dumps(req.brief.model_dump()),
        ))
    # TODO Fase 4: Pollinations imágenes + Kimi copy variants
    return ForgeJobResponse(
        job_id=job_id, status="accepted", job_type="ads",
        message=f"Ads para {req.meta.platforms} en cola. Implementación Fase 4.",
        webhook_url=req.callback_url,
    )


# ── Master Forge (todos en paralelo) ─────────────────────────────
@app.post("/api/master/generate", response_model=ForgeJobResponse)
async def generate_master(
    req: MasterForgeRequest,
    background_tasks: BackgroundTasks,
    _: str = Depends(verify_api_key),
):
    job_id = str(uuid.uuid4())
    with get_db() as db:
        db.add(ForgeJob(
            id=job_id, job_type="master", status="queued",
            brief_data=json.dumps(req.brief.model_dump()),
        ))
    # Encolar sub-jobs según lo que llegue en el request
    if req.video is not None:
        from backend.schemas import VideoForgeRequest, VideoMeta
        video_req = VideoForgeRequest(brief=req.brief, meta=req.video, callback_url=req.callback_url)
        sub_id = str(uuid.uuid4())
        with get_db() as db:
            db.add(ForgeJob(id=sub_id, job_type="video", status="queued",
                            brief_data=json.dumps(req.brief.model_dump())))
        background_tasks.add_task(run_video_pipeline, sub_id, video_req)

    return ForgeJobResponse(
        job_id=job_id, status="accepted", job_type="master",
        message="Master Forge en cola. Sub-jobs despachados.",
        webhook_url=req.callback_url,
    )


# ── Job Status ────────────────────────────────────────────────────
@app.get("/api/jobs/{job_id}", response_model=ForgeStatusResponse)
async def job_status(job_id: str, _: str = Depends(verify_api_key)):
    with get_db() as db:
        job = db.get(ForgeJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        return ForgeStatusResponse(
            job_id=job.id,
            status=job.status,
            job_type=job.job_type,
            result_urls=json.loads(job.result_urls) if job.result_urls else None,
            error=job.error,
            created_at=job.created_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            duration_s=job.duration_s,
        )


@app.get("/api/jobs")
async def list_jobs(_: str = Depends(verify_api_key)):
    with get_db() as db:
        jobs = db.query(ForgeJob).order_by(ForgeJob.created_at.desc()).limit(20).all()
        return [
            {
                "job_id": j.id, "type": j.job_type,
                "status": j.status, "created_at": j.created_at.isoformat(),
                "duration_s": j.duration_s,
            }
            for j in jobs
        ]


# ── Callback receptor (para Social Engine) ────────────────────────
@app.post("/api/pipeline/callback")
async def pipeline_callback(payload: dict):
    logger.info(f"Callback recibido: {payload}")
    return {"status": "ok"}


# ════════════════════════════════════════════════════════════════
# REVISIÓN HUMANA — Aprobar / Rechazar antes de publicar
# Flujo: pending_review → (approve) → publishing → published
#                       → (reject)  → rejected
# NUNCA se publica sin aprobación explícita del Comandante.
# ════════════════════════════════════════════════════════════════

@app.post("/api/jobs/{job_id}/approve")
async def approve_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    notes: Optional[str] = None,
    _: str = Depends(verify_api_key),
):
    """Aprueba un job en pending_review y lo entrega a Social Engine."""
    with get_db() as db:
        job = db.get(ForgeJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        if job.status != "pending_review":
            raise HTTPException(
                status_code=400,
                detail=f"Job no está en pending_review (estado actual: {job.status})"
            )
        job.status = "publishing"
        result_urls = json.loads(job.result_urls) if job.result_urls else {}
        brief = json.loads(job.brief_data) if job.brief_data else {}

    async def _publish():
        from pathlib import Path
        video_path = Path(result_urls.get("video", ""))
        thumb_path = Path(result_urls.get("thumbnail", ""))
        result = await deliver_to_social_engine(job_id, video_path, thumb_path, brief)
        final_status = "published" if result.get("status") != "error" else "publish_failed"
        with get_db() as db2:
            job2 = db2.get(ForgeJob, job_id)
            if job2:
                job2.status = final_status
                if notes:
                    job2.error = f"[APROBADO] {notes}"
        logger.info(f"[{job_id}] Entregado a Social Engine → {final_status}")

    background_tasks.add_task(_publish)
    logger.info(f"[{job_id}] APROBADO por el Comandante. Publicando en Social Engine…")
    return {
        "job_id": job_id,
        "status": "publishing",
        "message": "Aprobado. Entregando a Social Engine para publicación.",
        "notes": notes,
    }


@app.post("/api/jobs/{job_id}/reject")
async def reject_job(
    job_id: str,
    reason: Optional[str] = None,
    _: str = Depends(verify_api_key),
):
    """Rechaza un job. Queda como rejected — nunca se publica."""
    with get_db() as db:
        job = db.get(ForgeJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        if job.status not in ("pending_review", "publishing"):
            raise HTTPException(
                status_code=400,
                detail=f"Job no puede rechazarse desde estado: {job.status}"
            )
        job.status = "rejected"
        job.error = f"[RECHAZADO] {reason or 'Sin motivo especificado'}"

    logger.info(f"[{job_id}] RECHAZADO: {reason}")
    return {
        "job_id": job_id,
        "status": "rejected",
        "reason": reason or "Sin motivo especificado",
        "message": "Job rechazado. No se publicará.",
    }
