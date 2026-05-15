"""
TEST FLUJO EDITORIAL — Imperial Forge V10
Flujo: Generar → pending_review → Revisar archivos → Aprobar → published
"""
import sys, json, time
sys.path.insert(0, r"E:\proyectos  pc2\imperial-forge")
import httpx

HEADERS = {"X-API-Key": "forge-internal-key-v10"}
BASE    = "http://localhost:8300"

# ─────────────────────────────────────────────────────────────────
# PASO 1: Generar vídeo
# ─────────────────────────────────────────────────────────────────
print("=" * 60)
print("PASO 1 — GENERAR VÍDEO (sin publicar)")
print("=" * 60)

body = {
    "brief": {
        "product_name": "CursosAI",
        "tagline": "Aprende IA en producción en 30 días",
        "description": "Plataforma de cursos prácticos de inteligencia artificial para profesionales. Casos reales, proyectos en vivo.",
        "target_audience": "Profesionales que quieren actualizar sus skills con IA",
        "price": "Acceso completo 97EUR",
        "cta": "Empieza hoy en cursosai.net"
    },
    "meta": {
        "format": "9:16",
        "duration": 5,
        "style": "social_media",
        "avatar": "henry",
        "voiceover": True,
        "model": "seedance-1-lite",
        "language": "es"
    }
}

r = httpx.post(f"{BASE}/api/video/generate", json=body, headers=HEADERS, timeout=15)
data = r.json()
job_id = data["job_id"]
print(f"  Job ID : {job_id}")
print(f"  Status : {data['status']}")
print(f"  Mensaje: {data['message']}")

# ─────────────────────────────────────────────────────────────────
# PASO 2: Esperar a pending_review
# ─────────────────────────────────────────────────────────────────
print(f"\nPASO 2 — ESPERANDO pending_review (max 3 min)...")
for i in range(60):
    time.sleep(3)
    s = httpx.get(f"{BASE}/api/jobs/{job_id}", headers=HEADERS, timeout=10).json()
    print(f"  [{(i+1)*3:3d}s] {s['status']}")
    if s["status"] == "pending_review":
        print("\n  ✅ LISTO PARA REVISIÓN")
        result = s.get("result_urls", {})
        print(f"\n  Guion generado: {result.get('script', 'N/A')}")
        print(f"\n  Archivos:")
        for k, v in result.items():
            if k != "script":
                from pathlib import Path
                p = Path(v)
                size = p.stat().st_size if p.exists() else -1
                print(f"    {k:12s}: {v}")
                print(f"               size={size:,} bytes {'✅' if size > 1000 else '⚠️  MUY PEQUEÑO'}")
        break
    if s["status"] == "failed":
        print(f"\n  ❌ FALLÓ: {s.get('error')}")
        sys.exit(1)
else:
    print("  TIMEOUT")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
# PASO 3: Simular revisión del Comandante
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PASO 3 — REVISIÓN DEL COMANDANTE")
print("=" * 60)
print("  → Archivos generados correctamente.")
print("  → Guion revisado.")
print("  → Aprobando para publicación...")

# ─────────────────────────────────────────────────────────────────
# PASO 4: APROBAR (entrega a Social Engine)
# ─────────────────────────────────────────────────────────────────
print("\nPASO 4 — APROBAR JOB")
params = {"notes": "Revisado y aprobado. Publicar en TikTok e Instagram."}
ar = httpx.post(f"{BASE}/api/jobs/{job_id}/approve", headers=HEADERS, params=params, timeout=15)
adata = ar.json()
print(f"  Status : {adata['status']}")
print(f"  Mensaje: {adata['message']}")
print(f"  Notas  : {adata.get('notes')}")

# ─────────────────────────────────────────────────────────────────
# PASO 5: Confirmar estado final
# ─────────────────────────────────────────────────────────────────
print("\nPASO 5 — CONFIRMANDO ESTADO FINAL...")
for i in range(10):
    time.sleep(2)
    sf = httpx.get(f"{BASE}/api/jobs/{job_id}", headers=HEADERS, timeout=10).json()
    print(f"  [{(i+1)*2:2d}s] {sf['status']}")
    if sf["status"] in ("published", "publish_failed"):
        break

print("\n" + "=" * 60)
print("RESULTADO FINAL")
print("=" * 60)
print(json.dumps(sf, indent=2, ensure_ascii=False))
