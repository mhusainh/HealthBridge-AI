import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

# --- KONFIGURASI SIMPEL (Relative Path) ---
# Syarat: Terminal harus dijalankan di dalam folder AI
load_dotenv() # Otomatis cari .env di folder yang sama
JSON_FILENAME = os.getenv("FILENAME")
API_KEY = os.getenv("GOOGLE_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash') 
else:
    model = None
    print("⚠️ PERINGATAN: API Key tidak ditemukan.")

# --- DATA DARURAT ---
def create_emergency_data():
    print("🚨 MEMUAT DATA DARURAT (File JSON tidak ketemu)")
    return {
        "3374123456789001": {"profil": {"nama": "Budi Darurat", "nik": "3374123456789001"}, "medis": []}
    }

# --- LOAD DATA ---
def load_and_parse_data(filename=JSON_FILENAME):
    print(f"\n📂 Mencari file: {filename}")
    print(f"📍 Di folder: {os.getcwd()}") # Cek kita lagi ada di folder mana
    
    if not os.path.exists(filename):
        print(f"❌ FILE TIDAK DITEMUKAN!")
        return create_emergency_data()

    try:
        with open(filename, 'r') as f:
            bundle = json.load(f)
        print("✅ FILE DITEMUKAN! Sedang parsing...")
    except Exception as e:
        print(f"❌ ERROR BACA JSON: {e}")
        return create_emergency_data()

    database = {}
    uuid_to_nik = {}
    entries = bundle.get('entry', [])
    
    # 1. Parsing Pasien
    for entry in entries:
        res = entry['resource']
        if res['resourceType'] == 'Patient':
            full_id = "urn:uuid:" + res['id']
            nik = res['identifier'][0]['value'] if 'identifier' in res else "UNKNOWN"
            nama = res['name'][0]['text']
            uuid_to_nik[full_id] = nik
            
            database[nik] = {
                "profil": {"nama": nama, "nik": nik},
                "tanda_vital": {"tb": "-", "bb": "-", "tensi": "-"},
                "medis": []
            }

    # 2. Parsing Observation
    for entry in entries:
        res = entry['resource']
        if res['resourceType'] == 'Observation':
            subject_ref = res['subject']['reference']
            if subject_ref in uuid_to_nik:
                nik_pemilik = uuid_to_nik[subject_ref]
                try:
                    code = res['code']['coding'][0]['code']
                    if code == "29463-7": # BB
                        val = res['valueQuantity']['value']
                        unit = res['valueQuantity']['unit']
                        database[nik_pemilik]['tanda_vital']['bb'] = f"{val} {unit}"
                    elif code == "8302-2": # TB
                        val = res['valueQuantity']['value']
                        unit = res['valueQuantity']['unit']
                        database[nik_pemilik]['tanda_vital']['tb'] = f"{val} {unit}"
                    elif code == "85354-9": # Tensi
                        sys = res['component'][0]['valueQuantity']['value']
                        dia = res['component'][1]['valueQuantity']['value']
                        database[nik_pemilik]['tanda_vital']['tensi'] = f"{sys}/{dia} mmHg"
                except: continue

    # 3. Parsing Obat
    for entry in entries:
        res = entry['resource']
        if res['resourceType'] == 'MedicationRequest':
            subject_ref = res['subject']['reference']
            if subject_ref in uuid_to_nik:
                nik_pemilik = uuid_to_nik[subject_ref]
                try:
                    nama_obat = res['medicationCodeableConcept']['coding'][0].get('display', 'Obat')
                    diagnosa = res.get('reasonCode', [{}])[0].get('text', '-')
                    database[nik_pemilik]['medis'].append({"obat": nama_obat, "diagnosa": diagnosa})
                except: pass
                
    return database

# --- EKSEKUSI LOAD ---
DATABASE_CACHE = load_and_parse_data()
print(f"🎉 SUKSES! Total Pasien Terload: {len(DATABASE_CACHE)}")
print("--------------------------------------------------\n")

# --- AI LOGIC ---
def analyze_patient_risk(nik_target):
    if not model:
        return {"error": "Server AI Error: API Key Missing"}

    data = DATABASE_CACHE.get(nik_target)
    if not data:
        return {"error": f"Pasien NIK {nik_target} tidak ditemukan. Pastikan data sudah ter-load."}

    context = json.dumps(data, indent=2)
    
    prompt = f"""
    Bertindaklah sebagai Asisten Medis. Analisis data pasien:
    {context}
    
    Output JSON Murni:
    {{
      "status": "AMAN" | "BAHAYA" | "PERINGATAN",
      "skor_risiko": 0-100,
      "ringkasan_pasien": "Ringkasan...",
      "analisis_obat": "Analisis...",
      "rekomendasi": "Saran..."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        return {"error": f"AI Error: {str(e)}"}