import streamlit as st
import requests
import json
import networkx as nx
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="HealthBridge AI",
    page_icon="🏥",
    layout="wide"
)

# --- KONFIGURASI FILE (Relatif) ---
# Syarat: Terminal harus dijalankan di dalam folder AI
load_dotenv() # Otomatis cari .env di folder yang sama
file_path = os.getenv("FILENAME")

@st.cache_data
def load_data():
    options = {}
    bundle = {}
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                bundle = json.load(f)
            
            entries = bundle.get('entry', [])
            for entry in entries:
                if entry['resource']['resourceType'] == 'Patient':
                    res = entry['resource']
                    # Ambil NIK aman
                    if 'identifier' in res and len(res['identifier']) > 0:
                        nik = res['identifier'][0]['value']
                    else:
                        nik = "UNKNOWN"
                    
                    nama = res['name'][0]['text']
                    options[f"{nama} ({nik})"] = nik
                    
        except Exception as e:
            st.error(f"Error membaca JSON: {e}")
    else:
        # Fallback jika file tidak ketemu
        st.error(f"❌ File '{JSON_FILENAME}' tidak ditemukan di: {current_dir}")
        st.warning("👉 Pastikan Anda menjalankan perintah 'streamlit run app.py' DARI DALAM folder AI.")
        
    return options, bundle

# Load Data
patient_options, full_bundle = load_data()

# --- FUNGSI VISUALISASI GRAPH (LENGKAP VITAL SIGN) ---
def draw_graph(nik_target, bundle_data):
    G = nx.DiGraph()
    uuid_to_nik = {}
    entries = bundle_data.get('entry', [])
    
    patient_uuid = ""
    
    # 1. Node Pasien
    for entry in entries:
        res = entry['resource']
        if res['resourceType'] == 'Patient':
            curr_nik = res['identifier'][0]['value'] if 'identifier' in res else "UNK"
            uuid_to_nik["urn:uuid:" + res['id']] = curr_nik
            
            if curr_nik == nik_target:
                nama_pasien = res['name'][0]['text']
                patient_uuid = "urn:uuid:" + res['id']
                G.add_node("PASIEN", label=f"{nama_pasien}\n(Pasien)", color='#ADD8E6', shape='s', size=3000)
                
                # Alergi
                if "extension" in res:
                    for ext in res["extension"]:
                        if "allergy" in ext["url"]:
                            for a in ext["valueString"].split(","):
                                G.add_node(f"ALG_{a}", label=f"ALERGI:\n{a}", color='#FFB6C1', shape='o', size=2000)
                                G.add_edge("PASIEN", f"ALG_{a}", label="MEMILIKI")

    # 2. Node Vital Sign (TB/BB/Tensi) - UNGU
    for entry in entries:
        res = entry['resource']
        if res['resourceType'] == 'Observation':
            if res['subject']['reference'] == patient_uuid:
                try:
                    code = res['code']['coding'][0]['code']
                    val = ""
                    label = ""
                    
                    if code == "29463-7": # BB
                        val = f"{res['valueQuantity']['value']} kg"
                        label = "Berat"
                    elif code == "8302-2": # TB
                        val = f"{res['valueQuantity']['value']} cm"
                        label = "Tinggi"
                    elif code == "85354-9": # Tensi
                        sys = res['component'][0]['valueQuantity']['value']
                        dia = res['component'][1]['valueQuantity']['value']
                        val = f"{sys}/{dia}"
                        label = "Tensi"
                    
                    if val:
                        node_id = f"VITAL_{label}"
                        G.add_node(node_id, label=f"{label}\n{val}", color='#D8BFD8', shape='o', size=2000) # Ungu Thistle
                        G.add_edge("PASIEN", node_id, label="STATUS")
                except:
                    pass

    # 3. Node Obat & Diagnosa
    for entry in entries:
        res = entry['resource']
        if res['resourceType'] == 'MedicationRequest':
            if res['subject']['reference'] == patient_uuid:
                try:
                    obat = res['medicationCodeableConcept']['coding'][0].get('display', 'Obat')
                    diag = res.get('reasonCode', [{}])[0].get('text', '?')
                    
                    node_obat = f"OBT_{obat}"
                    node_diag = f"DIA_{diag}"
                    
                    G.add_node(node_obat, label=f"OBAT\n{obat}", color='#90EE90', shape='o', size=2500)
                    G.add_node(node_diag, label=f"DIAGNOSA\n{diag}", color='#FFD700', shape='o', size=2500)
                    
                    G.add_edge("PASIEN", node_obat, label="DIRESEPKAN")
                    G.add_edge(node_obat, node_diag, label="UNTUK")
                except:
                    pass

    return G

# --- UI SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3004/3004458.png", width=80)
    st.title("HealthBridge AI")
    st.caption("v1.0 - Hackathon Edition")
    st.markdown("---")
    st.subheader("Pilih Pasien")
    
    if patient_options:
        selected_label = st.selectbox("Cari Nama / NIK:", options=list(patient_options.keys()))
        selected_nik = patient_options[selected_label]
    else:
        st.error("Database Kosong / Tidak Terbaca")
        selected_nik = ""
        
    if selected_nik:
        st.info(f"NIK: **{selected_nik}**")

# --- UI UTAMA ---
st.title("🏥 Doctor's Copilot Dashboard")
st.markdown("Sistem integrasi data rekam medis & tanda vital berbasis **Knowledge Graph**.")

if st.button("🔍 ANALISA DATA PASIEN", type="primary", use_container_width=True):
    if not selected_nik:
        st.warning("Pilih pasien dulu.")
    else:
        try:
            with st.spinner('🤖 AI sedang menganalisis Tanda Vital & Interaksi Obat...'):
                # API Call ke Localhost
                api_url = f"http://localhost:8000/analyze/{selected_nik}"
                response = requests.get(api_url)
                
            if response.status_code == 200:
                result = response.json()
                
                # 1. Header Status
                status = result.get('status', 'AMAN')
                skor = result.get('skor_risiko', 0)
                
                c1, c2 = st.columns([2, 1])
                with c1:
                    if status == "BAHAYA": st.error(f"## STATUS: {status}")
                    elif status == "PERINGATAN": st.warning(f"## STATUS: {status}")
                    else: st.success(f"## STATUS: {status}")
                with c2:
                    st.metric("Skor Risiko", f"{skor}/100")
                
                # 2. Ringkasan Klinis (Teks dari AI)
                st.info(f"**Ringkasan Pasien:**\n\n{result.get('ringkasan_pasien', '-')}")
                
                # 3. Kolom Analisis
                col_kiri, col_kanan = st.columns(2)
                with col_kiri:
                    st.subheader("💊 Analisis Farmasi")
                    st.write(result.get('analisis_obat', '-'))
                with col_kanan:
                    st.subheader("💡 Rekomendasi Medis")
                    st.success(result.get('rekomendasi', '-'))
                
                # 4. Visualisasi Graph
                st.markdown("---")
                st.subheader("🕸️ Knowledge Graph Visualization")
                
                G = draw_graph(selected_nik, full_bundle)
                if G.number_of_nodes() > 0:
                    fig, ax = plt.subplots(figsize=(12, 7))
                    pos = nx.spring_layout(G, k=0.9, seed=42) # Layout renggang
                    
                    # Ambil atribut visual
                    colors = [nx.get_node_attributes(G, 'color').get(n, '#ddd') for n in G.nodes()]
                    sizes = [nx.get_node_attributes(G, 'size').get(n, 1500) for n in G.nodes()]
                    labels = nx.get_node_attributes(G, 'label')
                    
                    # Gambar
                    nx.draw(G, pos, ax=ax, node_color=colors, node_size=sizes, edge_color='gray', width=1.5, arrowsize=15)
                    nx.draw_networkx_labels(G, pos, labels, font_size=8)
                    edge_labels = nx.get_edge_attributes(G, 'label')
                    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
                    
                    st.pyplot(fig)
                else:
                    st.warning("Data graph kosong.")

            else:
                st.error(f"Backend Error: {response.text}")
                
        except Exception as e:
            st.error(f"Gagal koneksi Backend (Main.py sudah jalan?): {e}")