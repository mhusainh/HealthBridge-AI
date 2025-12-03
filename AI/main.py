from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Ini mengimpor fungsi otak yang sudah kamu buat kemarin
from ai_service import analyze_patient_risk 

app = FastAPI(title="HealthBridge AI API")

# --- SETTING IZIN AKSES (CORS) ---
# Biar Frontend temanmu (Person C) bisa akses API ini tanpa diblokir
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "HealthBridge AI Server Ready! 🚀"}

# --- ENDPOINT UTAMA (INI YANG DITEMBAK FRONTEND) ---
@app.get("/analyze/{nik}")
def api_analyze_patient(nik: str):
    print(f"📡 Menerima request untuk NIK: {nik}")
    
    # Panggil Otak AI
    result = analyze_patient_risk(nik)
    
    # Cek Error
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

# --- SCRIPT JALAN (Uvicorn) ---
if __name__ == "__main__":
    import uvicorn
    # Server jalan di port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)