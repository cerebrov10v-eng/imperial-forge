import sys
sys.path.insert(0, r"E:\proyectos  pc2\imperial-forge")
import httpx, json, time

body = {
    "brief": {
        "product_name": "MarketinAI",
        "tagline": "Tu agencia de marketing con IA",
        "description": "Plataforma que automatiza toda tu estrategia de marketing digital con inteligencia artificial.",
        "target_audience": "Emprendedores y pymes hispanohablantes",
        "price": "Desde 29EUR/mes",
        "cta": "Pruebalo gratis 7 dias"
    },
    "meta": {
        "format": "9:16",
        "duration": 5,
        "style": "social_media",
        "avatar": "amanda",
        "voiceover": True,
        "model": "seedance-1-lite",
        "language": "es"
    }
}

headers = {"X-API-Key": "forge-internal-key-v10"}
print("=== TEST IMPERIAL FORGE — VIDEO PIPELINE ===")
r = httpx.post("http://localhost:8300/api/video/generate", json=body, headers=headers, timeout=15)
data = r.json()
print(f"Job ID : {data['job_id']}")
print(f"Status : {data['status']}")
print(f"Message: {data['message']}")

job_id = data["job_id"]
print("\nPolling pipeline (max 3 min)...")
for i in range(60):
    time.sleep(3)
    s = httpx.get(f"http://localhost:8300/api/jobs/{job_id}", headers=headers, timeout=10)
    sd = s.json()
    elapsed = (i+1)*3
    print(f"  [{elapsed:3d}s] status={sd['status']}")
    if sd["status"] in ("done", "failed"):
        print("\n=== RESULTADO FINAL ===")
        print(json.dumps(sd, indent=2, ensure_ascii=False))
        if sd.get("result_urls"):
            print("\n=== ARCHIVOS GENERADOS ===")
            for k, v in sd["result_urls"].items():
                print(f"  {k}: {v}")
        break
else:
    print("TIMEOUT — pipeline tardó más de 3 min")
