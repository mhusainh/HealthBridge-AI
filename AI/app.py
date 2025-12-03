import streamlit as st
import requests
import json
import networkx as nx
import matplotlib.pyplot as plt
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="HealthBridge AI", page_icon="🏥", layout="wide")

# --- DEBUGGING PATH (Supaya ketahuan salahnya dimana) ---
# Kita coba 3 kemungkinan lokasi file
POSSIBLE_PATHS = [
    # 1. Alamat LENGKAP Laptopmu (Berdasarkan screenshot terminalmu)
    r"C:\Users\NITRO 5\Documents\GitHub\HealthBridge-AI\AI\fhir_data_1000.json",
    
    # 2. Alamat relatif terhadap file script ini
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fhir_data_1000.json'),
    
    # 3. Alamat relatif sederhana
    "fhir_data_1000.json"
]

@st.cache_data
def load_data():
    options = {}
    bundle = {}
    loaded_path = ""
    
    # Cek satu per satu lokasi yang mungkin
    for path in POSSIBLE_PATHS:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    bundle = json.load(f)
                loaded_path = path
                break # Ketemu! Berhenti mencari.
            except:
                continue

    if loaded_path:
        # Jika file ketemu, parsing isinya
        entries = bundle.get('entry', [])
        for entry in entries:
            if entry['resource']['resourceType'] == 'Patient':
                res = entry['resource']
                nik = res['identifier'][0]['value'] if 'identifier' in res else "UNK"
                nama = res['name'][0]['text']
                options[f"{nama} ({nik})"] = nik
    else:
        # JIKA MASIH GAGAL JUGA -> Pakai Data Darurat
        options["⚠️ FILE TETAP HILANG - Pakai Data Dummy"] = "3374123456789001"
        st.error(f"❌ Python tidak bisa menemukan file JSON di lokasi manapun: {POSSIBLE_PATHS}")

    return options, bundle, loaded_path

# Load Data
patient_options, full_bundle, success_path = load_data()

# --- SIDEBAR (Debug Info) ---
with st.sidebar:
    st.title("HealthBridge AI")
    
    # Tampilkan status file di sidebar biar tenang
    if "⚠️" in list(patient_options.keys())[0]:
        st.error("Status Database: ❌ GAGAL LOAD")
    else:
        st.success("Status Database: ✅ TERHUBUNG")
        # st.caption(f"Source: {success_path}") # Uncomment kalau mau lihat path-nya

    st.markdown("---")
    st.subheader("Pilih Pasien")
    selected_label = st.selectbox("Cari Nama:", options=list(patient_options.keys()))
    selected_nik = patient_options[selected_label]
    
    if selected_nik:
        st.info(f"NIK: **{selected_nik}**")

# --- FUNGSI GRAPH (Sama seperti sebelumnya) ---
def draw_graph(nik_target, bundle_data):
    G = nx.DiGraph()
    entries = bundle_data.get('entry', [])
    patient_uuid = ""
    
    for entry in entries:
        res = entry['resource']
        if res['resourceType'] == 'Patient':
            curr_nik = res['identifier'][0]['value'] if 'identifier' in res else "UNK"
            if curr_nik == nik_target:
                nama = res['name'][0]['text']
                patient_uuid = "urn:uuid:" + res['id']
                G.add_node("PASIEN", label=f"{nama}\n(Pasien)", color='#ADD8E6', shape='s')
                
                # Alergi
                if "extension" in res:
                    for ext in res["extension"]:
                        if "allergy" in ext["url"]:
                            for a in ext["valueString"].split(","):
                                G.add_node(f"ALG_{a}", label=f"ALERGI:\n{a}", color='#FFB6C1', shape='o')
                                G.add_edge("PASIEN", f"ALG_{a}", label="MEMILIKI")

    # Vital & Obat
    for entry in entries:
        res = entry['resource']
        # Observation
        if res['resourceType'] == 'Observation' and res['subject']['reference'] == patient_uuid:
            try:
                code = res['code']['coding'][0]['display']
                if 'Body Weight' in code:
                    val = f"{res['valueQuantity']['value']} kg"
                    G.add_node("BB", label=f"BB\n{val}", color='#E6E6FA', shape='o')
                    G.add_edge("PASIEN", "BB", label="STATUS")
                elif 'Blood Pressure' in code:
                    sys = res['component'][0]['valueQuantity']['value']
                    val = f"{sys}/{res['component'][1]['valueQuantity']['value']}"
                    G.add_node("BP", label=f"TENSI\n{val}", color='#E6E6FA', shape='o')
                    G.add_edge("PASIEN", "BP", label="STATUS")
            except: pass
            
        # Obat
        if res['resourceType'] == 'MedicationRequest' and res['subject']['reference'] == patient_uuid:
            try:
                obat = res['medicationCodeableConcept']['coding'][0].get('display', 'Obat')
                diag = res.get('reasonCode', [{}])[0].get('text', '?')
                node_obat = f"OBT_{obat}"
                node_diag = f"DIA_{diag}"
                
                G.add_node(node_obat, label=f"OBAT\n{obat}", color='#90EE90', shape='o')
                G.add_node(node_diag, label=f"DIAGNOSA\n{diag}", color='#FFD700', shape='o')
                G.add_edge("PASIEN", node_obat, label="DIRESEPKAN")
                G.add_edge(node_obat, node_diag, label="UNTUK")
            except: pass
            
    return G

# --- UI UTAMA ---
st.title("🏥 Doctor's Copilot Dashboard")

if st.button("🔍 ANALISA DATA PASIEN", type="primary", use_container_width=True):
    if not selected_nik or "⚠️" in selected_label:
        st.warning("Pilih pasien yang valid dulu.")
    else:
        try:
            with st.spinner('🤖 AI sedang berpikir...'):
                api_url = f"http://localhost:8000/analyze/{selected_nik}"
                response = requests.get(api_url)
                
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'AMAN')
                
                c1, c2 = st.columns([2, 1])
                with c1:
                    if status == "BAHAYA": st.error(f"## STATUS: {status}")
                    elif status == "PERINGATAN": st.warning(f"## STATUS: {status}")
                    else: st.success(f"## STATUS: {status}")
                with c2:
                    st.metric("Skor Risiko", f"{result.get('skor_risiko', 0)}/100")
                
                st.info(f"**Ringkasan:**\n{result.get('ringkasan_pasien', '-')}")
                
                c3, c4 = st.columns(2)
                with c3:
                    st.subheader("💊 Analisis")
                    st.write(result.get('analisis_obat', '-'))
                with c4:
                    st.subheader("💡 Rekomendasi")
                    st.success(result.get('rekomendasi', '-'))
                
                # Graph
                st.markdown("---")
                st.subheader("🕸️ Knowledge Graph")
                G = draw_graph(selected_nik, full_bundle)
                if G.number_of_nodes() > 0:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    pos = nx.spring_layout(G, k=0.8, seed=42)
                    colors = [nx.get_node_attributes(G, 'color').get(n, '#ddd') for n in G.nodes()]
                    labels = nx.get_node_attributes(G, 'label')
                    nx.draw(G, pos, ax=ax, node_color=colors, with_labels=False, node_size=2000, edge_color='gray')
                    nx.draw_networkx_labels(G, pos, labels, font_size=7)
                    st.pyplot(fig)
                else:
                    st.warning("Data graph kosong.")
            else:
                st.error(f"Backend Error: {response.text}")
        except Exception as e:
            st.error(f"Gagal koneksi Backend: {e}")