import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time

# Letakkan ini di baris pertama setelah import
if 'user' not in st.session_state:
    st.session_state.user = None

# 1. KONEKSI INFRASTRUKTUR
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Psych-AI CPNS: Intelligence", page_icon="🧠")

# 2. INISIALISASI SESSION STATE
if 'user' not in st.session_state:
    st.session_state.user = None

# --- GERBANG MASUK (LOGIN & REGISTER) ---
# --- 1. INISIALISASI SESSION STATE (Letakkan di bagian paling atas setelah import) ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- 2. FUNGSI LOGIKA (MODULAR) ---
def handle_login(email, password):
    try:
        # Mencoba masuk ke Supabase
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.success("🎉 Login Berhasil! Mempersiapkan dashboard...")
        time.sleep(1) # Memberi waktu user membaca pesan sukses
        st.rerun()
    except Exception as e:
        # Menangani pesan error spesifik jika email belum dikonfirmasi
        error_msg = str(e).lower()
        if "email not confirmed" in error_msg:
            st.warning("⚠️ Email Anda belum dikonfirmasi. Silakan cek Inbox/Spam email Anda!")
        else:
            st.error("❌ Login Gagal: Email atau Password salah.")

def handle_register(email, password):
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        st.info("📨 Link konfirmasi telah dikirim! Segera cek email Anda untuk mengaktifkan akun.")
    except Exception as e:
        st.error(f"❌ Gagal Daftar: {e}")

# --- 3. ANTARMUKA PENGGUNA (UI) ---
if st.session_state.user is None:
    st.title("🚀 Pejuang CPNS: Psych-AI Dashboard")
    st.markdown("Silakan masuk untuk mulai simulasi kognitif Anda.")
    
    # Menggunakan Tabs agar rapi dan tidak saling tindih
    tab_masuk, tab_daftar = st.tabs(["🔑 Login Member", "📝 Daftar Akun Baru"])
    
    with tab_masuk:
        with st.form("form_login"):
            email_input = st.text_input("Email", placeholder="nama@email.com")
            pass_input = st.text_input("Password", type="password")
            submit_l = st.form_submit_button("Masuk Sekarang")
            
            if submit_l:
                if email_input and pass_input:
                    try:
                        # 1. Eksekusi Login
                        res = supabase.auth.sign_in_with_password({
                            "email": email_input, 
                            "password": pass_input
                        })
                        st.session_state.user = res.user
                        
                        # 2. Simpan Cookie (Remember Me)
                        session = supabase.auth.get_session()
                        if session:
                            # Simpan token, bukan password, agar aman!
                            controller.set('supabase_token', session.access_token)
                        
                        st.session_state.start_time = time.time()
                        st.success("Login Berhasil!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Email atau Password salah: {e}")
                else:
                    st.warning("Mohon isi email dan password.")
                    
    with tab_daftar:
        with st.form("form_daftar"):
            new_email = st.text_input("Email Baru", placeholder="pejuang@cpns.com")
            new_pass = st.text_input("Buat Password (minimal 6 karakter)", type="password")
            submit_d = st.form_submit_button("Buat Akun Saya")
            if submit_d:
                if new_email and len(new_pass) >= 6:
                    handle_register(new_email, new_pass)
                else:
                    st.warning("Password minimal harus 6 karakter.")
    
    # Berhenti di sini jika belum login (PENTING: Jangan taruh st.stop() di dalam tab)
    st.stop()

from streamlit_cookies_controller import CookieController

controller = CookieController()

# --- CEK COOKIE UNTUK AUTO-LOGIN ---
saved_token = controller.get('supabase_token')

if saved_token and st.session_state.user is None:
    try:
        # Gunakan token yang tersimpan untuk memulihkan sesi
        res = supabase.auth.get_user(saved_token)
        st.session_state.user = res.user
        st.rerun()
    except:
        # Jika token kadaluarsa, hapus cookie agar tidak error terus
        controller.remove('supabase_token')
        


# --- HALAMAN UTAMA MEMBER ---
st.sidebar.info(f"👤 {st.session_state.user.email}")
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

tab_kuis, tab_progres = st.tabs(["✍️ Simulasi Ujian", "📊 Analisis Psikometri"])

with tab_kuis:
    st.title("Simulasi Ujian CPNS Terpadu")
    res_soal = supabase.table("bank_soal").select("*").execute()
    questions = res_soal.data

    if questions:
        with st.form("quiz_v6"):
            user_answers = {}
            for q in questions:
                kat_display = q.get('kategori', 'Umum')
                st.subheader(f"[{kat_display}] Soal {q['id']}")
                opsi = [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d']]
                user_answers[q['id']] = st.radio(q['pertanyaan'], opsi, key=f"q_{q['id']}")
            
            if st.form_submit_button("Selesaikan & Simpan Hasil"):
                skor_det = {"TIU": 0, "TWK": 0, "TKP": 0}
                for q in questions:
                    if user_answers[q['id']] == q['jawaban_benar']:
                        k = q.get('kategori', 'TIU')
                        if k in skor_det: skor_det[k] += 1
                
                supabase.table("user_scores").insert({
                    "nama_user": st.session_state.user.email,
                    "skor_total": sum(skor_det.values()),
                    "skor_tiu": skor_det["TIU"],
                    "skor_twk": skor_det["TWK"],
                    "skor_tkp": skor_det["TKP"],
                    "total_soal": len(questions),
                    "durasi_detik": round(time.time() - st.session_state.start_time, 2)
                }).execute()
                st.success("🎯 Skor tersimpan! Buka tab Analisis Psikometri.")
                st.balloons()
    else:
        st.warning("Belum ada soal.")

with tab_progres:
    st.title("Peta Kekuatan Kognitif")
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        targets = ['skor_tiu', 'skor_twk', 'skor_tkp']
        
        # Detektor Keamanan: Memastikan kolom ada dan tidak kosong
        if all(col in df.columns for col in targets) and not df[targets].isnull().all().all():
            df_clean = df.dropna(subset=targets)
            avg_scores = df_clean[targets].mean().reset_index()
            avg_scores.columns = ['Aspek Kognitif', 'Rata-rata Skor']
            
            fig = px.bar(avg_scores, x='Aspek Kognitif', y='Rata-rata Skor', 
                         color='Aspek Kognitif', title="Kekuatan Kamu Per Kategori")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("📊 Grafik belum bisa ditampilkan. Silakan kerjakan kuis satu kali lagi untuk mengisi data kategori.")
    else:
        st.info("Belum ada riwayat tes.")

# --- FITUR LEADERBOARD ---
st.sidebar.markdown("---")
st.sidebar.subheader("🏆 Top Pejuang CPNS")

# Ambil 5 skor tertinggi dari database
res_leaderboard = supabase.table("user_scores") \
    .select("nama_user, skor_total") \
    .order("skor_total", desc=True) \
    .limit(5) \
    .execute()

if res_leaderboard.data:
    df_leader = pd.DataFrame(res_leaderboard.data)
    # Menampilkan tabel tanpa index agar lebih rapi
    st.sidebar.table(df_leader)




