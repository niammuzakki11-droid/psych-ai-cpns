import streamlit as st
from supabase import create_client
import time
import pandas as pd
import plotly.express as px

# 1. KONEKSI INFRASTRUKTUR
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Psych-AI CPNS Pro", page_icon="📈")

# --- FITUR: CEK STATUS KONFIRMASI DARI EMAIL ---
if "status" in st.query_params and st.query_params["status"] == "confirmed":
    st.success("✅ Selamat! Akun Anda sudah terkonfirmasi. Silakan Login.")
    st.query_params.clear()

# 2. INISIALISASI SESSION STATE
if 'user' not in st.session_state:
    st.session_state.user = None

# --- FUNGSI AUTH ---
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.session_state.start_time = time.time()
        st.rerun()
    except Exception as e:
        st.error(f"Login Gagal: {e}")

def register(email, password):
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        st.info("Pendaftaran Berhasil! Silakan CEK EMAIL Anda untuk konfirmasi.")
    except Exception as e:
        st.error(f"Pendaftaran Gagal: {e}")

# --- GERBANG MASUK (AUTHENTICATION) ---
if st.session_state.user is None:
    st.title("🚀 Psych-AI CPNS: Member Area")
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Daftar Akun"])
    
    with tab1:
        with st.form("login_form"):
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                login(e, p)
    with tab2:
        with st.form("reg_form"):
            ne = st.text_input("Email Baru")
            np = st.text_input("Password (min 6 karakter)", type="password")
            if st.form_submit_button("Buat Akun"):
                register(ne, np)
    st.stop()

# --- HALAMAN UTAMA MEMBER (DASHBOARD & KUIS) ---
st.sidebar.success(f"👤 {st.session_state.user.email}")
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- MENU TAB ---
tab_kuis, tab_progres = st.tabs(["✍️ Simulasi Ujian", "📊 Progress Dashboard"])

with tab_kuis:
    st.title("Simulasi Ujian CPNS")
    
    @st.cache_data
    def load_questions():
        res = supabase.table("bank_soal").select("*").execute()
        return res.data

    questions = load_questions()

    if questions:
        with st.form("quiz_final"):
            user_answers = {}
            for q in questions:
                st.subheader(f"Soal {q['id']}")
                opsi = [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d']]
                user_answers[q['id']] = st.radio(q['pertanyaan'], opsi, key=f"q_{q['id']}")
            
            if st.form_submit_button("Selesaikan & Simpan Skor"):
                duration = time.time() - st.session_state.start_time
                score = sum([1 for q in questions if user_answers[q['id']] == q['jawaban_benar']])
                
                data_score = {
                    "nama_user": st.session_state.user.email,
                    "skor_total": score,
                    "total_soal": len(questions),
                    "durasi_detik": round(duration, 2)
                }
                supabase.table("user_scores").insert(data_score).execute()
                st.success(f"🎯 Skor: {score} / {len(questions)} tersimpan!")
                st.balloons()
    else:
        st.warning("Gudang soal kosong.")

with tab_progres:
    st.title("Analisis Performa")
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        # Menampilkan Grafik Progres
        fig = px.line(df, x=df.index, y='skor_total', title="Tren Skor Kamu", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.metric("Skor Tertinggi", df['skor_total'].max())
    else:
        st.info("Belum ada data. Silakan kerjakan kuis pertama kamu!")
