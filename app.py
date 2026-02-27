import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time

# 1. KONEKSI INFRASTRUKTUR
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Psych-AI CPNS: Intelligence", page_icon="🧠")

# 2. INISIALISASI SESSION STATE
if 'user' not in st.session_state:
    st.session_state.user = None

# --- GERBANG AUTH (LOGIN & REGISTER) ---
if st.session_state.user is None:
    st.title("🚀 Member Area")
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Daftar Akun"])
    with tab1:
        with st.form("login_final"):
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                    st.session_state.user = res.user
                    st.session_state.start_time = time.time()
                    st.rerun()
                except: st.error("Email/Password salah atau belum konfirmasi email.")
    st.stop()

# --- HALAMAN UTAMA ---
st.sidebar.info(f"👤 {st.session_state.user.email}")
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

tab_kuis, tab_progres = st.tabs(["✍️ Simulasi Ujian", "📊 Analisis Psikometri"])

with tab_kuis:
    st.title("Simulasi Ujian CPNS Terpadu")
    # Ambil soal dari Database
    res_soal = supabase.table("bank_soal").select("*").execute()
    questions = res_soal.data

    if questions:
        with st.form("quiz_v6"):
            user_answers = {}
            for q in questions:
                # Menampilkan kategori soal di judul
                kat_display = q.get('kategori', 'Umum')
                st.subheader(f"[{kat_display}] Soal {q['id']}")
                opsi = [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d']]
                user_answers[q['id']] = st.radio(q['pertanyaan'], opsi, key=f"q_{q['id']}")
            
            if st.form_submit_button("Selesaikan & Simpan Hasil"):
                # Hitung skor per kategori
                skor_det = {"TIU": 0, "TWK": 0, "TKP": 0}
                for q in questions:
                    if user_answers[q['id']] == q['jawaban_benar']:
                        k = q.get('kategori', 'TIU')
                        if k in skor_det: skor_det[k] += 1
                
                # SIMPAN KE DATABASE (Mengisi kolom skor_tiu, dsb)
                supabase.table("user_scores").insert({
                    "nama_user": st.session_state.user.email,
                    "skor_total": sum(skor_det.values()),
                    "skor_tiu": skor_det["TIU"],
                    "skor_twk": skor_det["TWK"],
                    "skor_tkp": skor_det["TKP"],
                    "total_soal": len(questions),
                    "durasi_detik": round(time.time() - st.session_state.start_time, 2)
                }).execute()
                st.success("🎯 Skor tersimpan! Silakan cek tab Analisis Psikometri.")
                st.balloons()
    else:
        st.warning("Belum ada soal di 'bank_soal'.")

with tab_progres:
    st.title("Peta Kekuatan Kognitif")
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        
        # --- LOGIKA PENYELAMAT GRAFIK ---
        targets = ['skor_tiu', 'skor_twk', 'skor_tkp']
        # Hanya tampilkan grafik jika kolom sudah ada di data dan tidak semua NULL
        if all(col in df.columns for col in targets) and not df[targets].isnull().all().all():
            # Ambil rata-rata dari data yang tidak NULL
            df_clean = df.dropna(subset=targets)
            avg_scores = df_clean[targets].mean().reset_index()
            avg_scores.columns = ['Aspek Kognitif', 'Rata-rata Skor']
            
            fig = px.bar(avg_scores, x='Aspek Kognitif', y='Rata-rata Skor', 
                         color='Asp
