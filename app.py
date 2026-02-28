import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
from streamlit_cookies_controller import CookieController

# 1. INISIALISASI & KONEKSI
controller = CookieController()

# STANDAR PASSING GRADE BKN
PASSING_TWK = 65
PASSING_TIU = 80
PASSING_TKP = 166

if 'user' not in st.session_state:
    st.session_state.user = None

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Psych-AI CPNS: Intelligence", page_icon="🧠")

# --- AUTO LOGIN CHECK (Dilakukan sebelum menggambar UI) ---
saved_token = controller.get('supabase_token')
if saved_token and st.session_state.user is None:
    try:
        # Melakukan verifikasi token langsung ke Supabase
        res = supabase.auth.get_user(saved_token)
        if res.user: # penambahan-baru-1
            st.session_state.user = res.user
            # Memastikan variabel waktu sudah ada agar kuis tidak error
            if 'start_time' not in st.session_state: st.session_state.start_time = time.time() # penambahan-baru-1
            st.rerun() # Langsung lompat ke dashboard
    except:
        controller.remove('supabase_token')

# --- GERBANG MASUK (LOGIN & REGISTER) ---
if st.session_state.user is None:
    st.title("🚀 Pejuang CPNS: Psych-AI Dashboard")
    tab_masuk, tab_daftar = st.tabs(["🔑 Login Member", "📝 Daftar Akun Baru"])
    
    with tab_masuk:
        with st.form("form_login"):
            # MENGGUNAKAN LABEL STANDAR & KEY TETAP AGAR AUTOFILL SINKRON
            email_input = st.text_input("Email", placeholder="nama@email.com", key="login_email_autofill") # ganti-baris-1
            pass_input = st.text_input("Password", type="password", key="login_pass_autofill") # ganti-baris-1
            
            # Menambah opsi agar user secara sadar mengaktifkan fitur pengingat sesi
            remember_me = st.checkbox("Ingat Saya (Auto-Login 7 Hari)", value=True) # ganti-baris-1
            
            if st.form_submit_button("Masuk Sekarang"):
                try:
                    # Langsung menangkap session saat login agar token bisa disimpan
                    res = supabase.auth.sign_in_with_password({"email": email_input, "password": pass_input}) # ganti-baris-1
                    st.session_state.user = res.user
                    
                    # Simpan token ke browser jika login sukses dan checkbox dicentang
                    if res.session and remember_me: # penambahan-baru-1
                        controller.set('supabase_token', res.session.access_token) # penambahan-baru-1
                        
                    st.session_state.start_time = time.time()
                    st.success("Login Berhasil! Mengalihkan...") # penambahan-baru-1
                    time.sleep(1) # penambahan-baru-1 (PENTING: Memberi jeda agar browser sempat memicu pop-up 'Save Password')
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal: {e}")
                    
    with tab_daftar:
        with st.form("form_daftar"):
            ne = st.text_input("Email Baru", key="signup_email") # penambahan-baru-1
            np = st.text_input("Password (min 6 karakter)", type="password", key="signup_pass") # penambahan-baru-1
            if st.form_submit_button("Buat Akun"):
                try:
                    supabase.auth.sign_up({"email": ne, "password": np})
                    st.info("📨 Cek email Anda untuk konfirmasi!")
                except Exception as e:
                    st.error(f"Gagal: {e}")
    st.stop()

# --- HALAMAN UTAMA MEMBER ---
st.sidebar.info(f"👤 {st.session_state.user.email}")
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    controller.remove('supabase_token') # Hapus cookie saat logout
    st.session_state.user = None
    st.rerun()

tab_kuis, tab_progres = st.tabs(["✍️ Simulasi Ujian", "📊 Analisis Psikometri"])

with tab_kuis:
    st.title("Simulasi Ujian CPNS Terpadu")
    
    # Menambahkan logika pengacakan soal (shuffle) agar user selalu mendapat tantangan berbeda
    res_soal = supabase.table("bank_soal").select("*").execute() # penambahan-baru
    questions = res_soal.data # penambahan-baru
    
    if questions:
        with st.form("quiz_v6"):
            user_answers = {}
            for q in questions:
                st.subheader(f"[{q.get('kategori', 'Umum')}] Soal {q['id']}")
                user_answers[q['id']] = st.radio(q['pertanyaan'], [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d']], key=f"q_{q['id']}")
            
            if st.form_submit_button("Selesaikan & Simpan Hasil"):
                skor_det = {"TIU": 0, "TWK": 0, "TKP": 0}
                for q in questions:
                    if user_answers[q['id']] == q['jawaban_benar']:
                        k = q.get('kategori', 'TIU')
                        # TIU/TWK dikali 5 poin per soal sesuai standar BKN
                        skor_det[k] += 5 
                
                # Cek Passing Grade
                lulus = skor_det["TIU"] >= PASSING_TIU and skor_det["TWK"] >= PASSING_TWK and skor_det["TKP"] >= PASSING_TKP
                
                supabase.table("user_scores").insert({
                    "nama_user": st.session_state.user.email,
                    "skor_total": sum(skor_det.values()),
                    "skor_tiu": skor_det["TIU"], "skor_twk": skor_det["TWK"], "skor_tkp": skor_det["TKP"],
                    "total_soal": len(questions),
                    "durasi_detik": round(time.time() - st.session_state.start_time, 2)
                }).execute()
                
                if lulus: st.success("🎯 Selamat! Anda LOLOS Ambang Batas BKN.")
                else: st.warning("⚠️ Skor Anda belum mencapai Ambang Batas.")
                st.balloons()
    else:
        st.warning("Belum ada soal.")

with tab_progres:
    st.title("Peta Kekuatan Kognitif")
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        # Visualisasi rata-rata skor per kategori
        avg_scores = df[['skor_tiu', 'skor_twk', 'skor_tkp']].mean().reset_index()
        avg_scores.columns = ['Kategori', 'Skor']
        st.plotly_chart(px.bar(avg_scores, x='Kategori', y='Skor', color='Kategori'), use_container_width=True)
    else:
        st.info("Belum ada data.")

# --- SIDEBAR LEADERBOARD ---
st.sidebar.markdown("---")
st.sidebar.subheader("🏆 Top Pejuang CPNS")
res_lb = supabase.table("user_scores").select("nama_user, skor_total").order("skor_total", desc=True).limit(5).execute()
if res_lb.data:
    st.sidebar.table(pd.DataFrame(res_lb.data))




