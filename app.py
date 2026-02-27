import streamlit as st
from supabase import create_client
import time

# 1. KONEKSI INFRASTRUKTUR
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Psych-AI CPNS", page_icon="🔐")

# --- FITUR BARU: CEK STATUS KONFIRMASI DARI URL ---
# Fitur ini membaca tanda '?status=confirmed' yang kita buat di Supabase tadi
if "status" in st.query_params and st.query_params["status"] == "confirmed":
    st.success("✅ Selamat! Akun Anda sudah terkonfirmasi. Silakan Login di bawah ini.")
    # Kita hapus tanda status dari URL agar pesan tidak muncul terus-menerus
    st.query_params.clear()

# 2. INISIALISASI SESSION STATE (Memori Aplikasi)
if 'user' not in st.session_state:
    st.session_state.user = None

# --- FUNGSI AUTH (Login & Register) ---
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
        # Pesan pengingat agar user cek email
        st.info("Pendaftaran Berhasil! Silakan CEK EMAIL Anda untuk konfirmasi akun.")
    except Exception as e:
        st.error(f"Pendaftaran Gagal: {e}")

# --- GERBANG MASUK ---
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

# --- HALAMAN UTAMA (Jika sudah login) ---
st.sidebar.write(f"Logged in as: {st.session_state.user.email}")
st.title("✍️ Selamat Belajar, Pejuang CPNS!")
# (Sisa kode kuis dan simpan skor tetap sama seperti sebelumnya)
