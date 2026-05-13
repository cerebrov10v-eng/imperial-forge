"""
Imperial Forge V10 — Schemas Pydantic (stack soberano)
Motores: Kimi K2.5 | Seedance 2.0 | edge-tts | Pollinations.ai | moviepy
"""
from __future__ import annotations
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ── Brief base (compartido por todos los engines) ───────────────
class BriefData(BaseModel):
    product_name: str
    tagline: Optional[str] = None
    description: str
    target_audience: Optional[str] = None
    price: Optional[str] = None
    cta: Optional[str] = "Más información"
    brand_colors: Optional[List[str]] = None
    website_url: Optional[str] = None
    extra: Optional[dict] = None


# ── Video Engine ─────────────────────────────────────────────────
class VideoMeta(BaseModel):
    format: Literal["16:9", "9:16", "1:1"] = "9:16"
    duration: Literal[5, 10] = 5
    style: Literal["publicidad", "corporativo", "cinematic", "social_media", "testimonial"] = "social_media"
    avatar: Optional[Literal["amanda", "henry"]] = "amanda"
    voiceover: bool = True
    model: Literal["seedance-1-lite", "seedance-1-pro"] = "seedance-1-lite"
    language: Literal["es", "en"] = "es"

class VideoForgeRequest(BaseModel):
    brief: BriefData
    meta: VideoMeta = Field(default_factory=VideoMeta)
    callback_url: Optional[str] = None


# ── Audio Engine ─────────────────────────────────────────────────
class AudioMeta(BaseModel):
    voice: Literal["amanda", "henry", "en_us"] = "amanda"
    rate: Optional[str] = "+5%"
    pitch: Optional[str] = "+0Hz"
    output_format: Literal["mp3", "wav"] = "mp3"

class AudioForgeRequest(BaseModel):
    text: str
    meta: AudioMeta = Field(default_factory=AudioMeta)
    callback_url: Optional[str] = None


# ── Landing Forge ─────────────────────────────────────────────────
class LandingMeta(BaseModel):
    template: Literal["LP-PRODUCTO", "LP-LEAD", "LP-WEBINAR", "LP-SERVICIO", "LP-APP"] = "LP-PRODUCTO"
    theme: Literal["dark", "light"] = "dark"
    primary_color: Optional[str] = "#7c3aed"
    language: Literal["es", "en"] = "es"
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

class LandingForgeRequest(BaseModel):
    brief: BriefData
    meta: LandingMeta = Field(default_factory=LandingMeta)
    callback_url: Optional[str] = None


# ── Ad Creative Studio ────────────────────────────────────────────
class AdMeta(BaseModel):
    platforms: List[Literal["meta", "linkedin", "twitter", "tiktok"]] = ["meta"]
    formats: List[Literal["1:1", "16:9", "9:16", "4:5"]] = ["1:1", "9:16"]
    copy_variants: int = Field(default=3, ge=1, le=5)
    style: Literal["bold", "minimal", "cinematic", "playful"] = "bold"

class AdCreativeRequest(BaseModel):
    brief: BriefData
    meta: AdMeta = Field(default_factory=AdMeta)
    callback_url: Optional[str] = None


# ── Master Forge (todos los engines en paralelo) ──────────────────
class MasterForgeRequest(BaseModel):
    brief: BriefData
    video: Optional[VideoMeta] = None
    audio: Optional[AudioMeta] = None
    landing: Optional[LandingMeta] = None
    ads: Optional[AdMeta] = None
    callback_url: Optional[str] = None


# ── Responses ────────────────────────────────────────────────────
class ForgeJobResponse(BaseModel):
    job_id: str
    status: Literal["accepted", "rejected"]
    job_type: str
    message: str
    webhook_url: Optional[str] = None

class ForgeStatusResponse(BaseModel):
    job_id: str
    status: str
    job_type: str
    result_urls: Optional[dict] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    duration_s: Optional[float] = None
