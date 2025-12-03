import json
import random
import uuid
from datetime import datetime, timedelta

# Konfigurasi
TOTAL_DATA = 1000

NAMA_DEPAN = ["Budi", "Siti", "Agus", "Ratna", "Eko", "Dewi", "Rudi", "Sri", "Joko", "Lestari", "Adi", "Nina", "Bambang", "Yuni"]
NAMA_BELAKANG = ["Santoso", "Aminah", "Saputra", "Sari", "Prasetyo", "Wahyuni", "Hartono", "Kusuma", "Wijaya", "Utami", "Susanti", "Hidayat"]

SKENARIO = [
    "AMAN", "AMAN", "AMAN", "AMAN", "AMAN", 
    "HIPERTENSI_BERAT", 
    "INTERAKSI_JANTUNG", 
    "ALERGI_ANTIBIOTIK", 
    "BAHAYA_HAMIL",      
    "DUPLIKASI_OBAT",
    "OBESITAS"
]

def generate_nik():
    return f"3374{random.randint(100000000000, 999999999999)}"

def get_random_date(days_back=30):
    date = datetime.now() - timedelta(days=random.randint(0, days_back))
    return date.strftime("%Y-%m-%dT%H:%M:%S+07:00")

def calculate_birthdate(age):
    today = datetime.now()
    birth_year = today.year - age
    # Random bulan dan tanggal
    birth_date = datetime(birth_year, random.randint(1, 12), random.randint(1, 28))
    return birth_date.strftime("%Y-%m-%d")

def create_fhir_bundle():
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": []
    }

    print(f"🔄 Sedang men-generate {TOTAL_DATA} data Valid FHIR R4...")

    for i in range(TOTAL_DATA):
        skenario = random.choice(SKENARIO)
        gender = "female" if skenario == "BAHAYA_HAMIL" else random.choice(["male", "female"])
        nama_lengkap = f"{random.choice(NAMA_DEPAN)} {random.choice(NAMA_BELAKANG)}"
        nik = generate_nik()
        pasien_id = str(uuid.uuid4())
        
        # --- LOGIKA VITAL SIGN & UMUR ---
        age = random.randint(20, 60) # Default dewasa
        
        if skenario == "OBESITAS":
            bb = random.randint(95, 120)
            tb = random.randint(160, 175)
        elif skenario == "INTERAKSI_JANTUNG":
            age = random.randint(60, 80) # Lansia
            bb = random.randint(50, 75)
            tb = random.randint(160, 170)
        else:
            bb = random.randint(50, 85)
            tb = random.randint(155, 180)
            
        if skenario == "HIPERTENSI_BERAT":
            sistole = random.randint(150, 180)
            diastole = random.randint(95, 110)
        else:
            sistole = random.randint(110, 125)
            diastole = random.randint(70, 85)

        riwayat_medis = []
        alergi_list = []
        
        # --- LOGIKA OBAT ---
        if skenario == "AMAN":
            riwayat_medis.append({"obat": "Paracetamol 500mg", "kfa": "93001001", "diagnosa": "Demam Ringan"})
        elif skenario == "HIPERTENSI_BERAT":
            riwayat_medis.append({"obat": "Amlodipine 10mg", "kfa": "93001006", "diagnosa": "Hipertensi Grade 2"})
            riwayat_medis.append({"obat": "Candesartan 8mg", "kfa": "93001007", "diagnosa": "Hipertensi Grade 2"})
        elif skenario == "INTERAKSI_JANTUNG":
            riwayat_medis.append({"obat": "Clopidogrel 75mg", "kfa": "93001002", "diagnosa": "Riwayat Pasang Ring Jantung"})
            riwayat_medis.append({"obat": "Asam Mefenamat 500mg", "kfa": "93001003", "diagnosa": "Sakit Gigi Akut"})
        elif skenario == "ALERGI_ANTIBIOTIK":
            alergi_list.append("Penicillin")
            riwayat_medis.append({"obat": "Amoxicillin 500mg", "kfa": "93001004", "diagnosa": "Radang Tenggorokan"})
        elif skenario == "BAHAYA_HAMIL":
            age = random.randint(20, 35) # Usia produktif
            riwayat_medis.append({"obat": "Isotretinoin 10mg", "kfa": "93001005", "diagnosa": "Jerawat Kistik Parah"})
        elif skenario == "DUPLIKASI_OBAT":
            riwayat_medis.append({"obat": "Paracetamol 500mg", "kfa": "93001001", "diagnosa": "Demam"})
            riwayat_medis.append({"obat": "Sanmol (Paracetamol) 500mg", "kfa": "93001001", "diagnosa": "Pusing"})
        elif skenario == "OBESITAS":
             riwayat_medis.append({"obat": "Metformin 500mg", "kfa": "93001008", "diagnosa": "Pre-Diabetes"})

        # 1. Resource Patient
        patient_resource = {
            "fullUrl": f"urn:uuid:{pasien_id}",
            "resource": {
                "resourceType": "Patient",
                "id": pasien_id,
                "identifier": [{"system": "https://fhir.kemkes.go.id/id/nik", "value": nik}],
                "name": [{"use": "official", "text": nama_lengkap}],
                "gender": gender,
                "birthDate": calculate_birthdate(age) # FIX: Umur dinamis
            }
        }
        if alergi_list:
            patient_resource["resource"]["extension"] = [{"url": "http://example.org/allergy", "valueString": ",".join(alergi_list)}]
        bundle["entry"].append(patient_resource)

        # 2. Resource Observation (Berat Badan)
        bb_id = str(uuid.uuid4())
        bundle["entry"].append({
            "fullUrl": f"urn:uuid:{bb_id}",
            "resource": {
                "resourceType": "Observation",
                "id": bb_id,
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "29463-7", "display": "Body Weight"}]},
                "subject": {"reference": f"urn:uuid:{pasien_id}"},
                "valueQuantity": {
                    "value": bb, 
                    "unit": "kg", 
                    "system": "http://unitsofmeasure.org", 
                    "code": "kg"
                }
            }
        })

        # 3. Resource Observation (Tinggi Badan)
        tb_id = str(uuid.uuid4())
        bundle["entry"].append({
            "fullUrl": f"urn:uuid:{tb_id}",
            "resource": {
                "resourceType": "Observation",
                "id": tb_id,
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "8302-2", "display": "Body Height"}]},
                "subject": {"reference": f"urn:uuid:{pasien_id}"},
                "valueQuantity": {
                    "value": tb, 
                    "unit": "cm", 
                    "system": "http://unitsofmeasure.org", 
                    "code": "cm"
                }
            }
        })
        
        # 4. Resource Observation (Tekanan Darah)
        bp_id = str(uuid.uuid4())
        bundle["entry"].append({
            "fullUrl": f"urn:uuid:{bp_id}",
            "resource": {
                "resourceType": "Observation",
                "id": bp_id,
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood Pressure"}]},
                "subject": {"reference": f"urn:uuid:{pasien_id}"},
                "component": [
                    {
                        "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic"}]}, 
                        "valueQuantity": {"value": sistole, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
                    },
                    {
                        "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic"}]}, 
                        "valueQuantity": {"value": diastole, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
                    }
                ]
            }
        })

        # 5. Resource MedicationRequest
        for rekam in riwayat_medis:
            med_req_id = str(uuid.uuid4())
            bundle["entry"].append({
                "fullUrl": f"urn:uuid:{med_req_id}",
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": med_req_id,
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": f"urn:uuid:{pasien_id}"},
                    "medicationCodeableConcept": {"coding": [{"system": "http://sys-ids.kemkes.go.id/kfa", "code": rekam['kfa'], "display": rekam['obat']}]},
                    "reasonCode": [{"text": rekam['diagnosa']}],
                    "authoredOn": get_random_date()
                }
            })

    return bundle

if __name__ == "__main__":
    data = create_fhir_bundle()
    with open("fhir_data_1000.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Data Selesai! File 'fhir_data_1000.json' valid FHIR.")