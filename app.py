import streamlit as st
from supabase import create_client
import time

# Koneksi Database
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Psych-AI CPNS", page_icon="🚀")
st.title("🚀 Psych-AI CPNS: Global Ranking")

# Input Nama (Langkah Awal Identitas)
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

if not st.session_state.user_name:
    with st.form("name_form"):
        name_input = st.text_input("Masukkan Nama Kamu untuk Masuk Ranking:")
        start_btn = st.form_submit_button("Mulai Tes")
        if start_btn and name_input:
            st.session_state.user_name = name_input
            st.session_state.start_time = time.time()
            st.rerun()
        elif start_btn and not name_input:
            st.error("Nama tidak boleh kosong!")
    st.stop()

# Load Soal
@st.cache_data
def load_questions():
    response = supabase.table("bank_soal").select("*").execute()
    return response.data

questions = load_questions()

# Form Tes
with st.form("quiz_db"):
    st.info(f"Halo, {st.session_state.user_name}! Selamat mengerjakan.")
    user_answers = {}
    for q in questions:
        st.subheader(f"Soal {q['id']} ({q['kategori']})")
        opsi = [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d']]
        user_answers[q['id']] = st.radio(q['pertanyaan'], opsi, key=f"q_{q['id']}")
    
    submitted = st.form_submit_button("Selesaikan Tes")

if submitted:
    duration = time.time() - st.session_state.start_time
    score = sum([1 for q in questions if user_answers[q['id']] == q['jawaban_benar']])
    
    # --- EKSEKUSI SIMPAN DATA ---
    data_skor = {
        "nama_user": st.session_state.user_name,
        "skor_total": score,
        "total_soal": len(questions),
        "durasi_detik": round(duration, 2)
    }
    supabase.table("user_scores").insert(data_skor).execute()
    
    st.success(f"🎯 Skor: {score}/{len(questions)} | ⏱️ Waktu: {duration:.2f}s")
    st.write("Skor kamu telah disimpan secara permanen di database!")

# --- TAMPILKAN RANKING (Leaderboard) ---
st.divider()
st.subheader("🏆 Top 10 Skor Global")
def show_leaderboard():
    res = supabase.table("user_scores").select("*").order("skor_total", desc=True).limit(10).execute()
    if res.data:
        import pandas as pd
        df = pd.DataFrame(res.data)
        st.table(df[['nama_user', 'skor_total', 'durasi_detik']])

show_leaderboard()

if st.button("Ulangi Tes"):
    st.session_state.user_name = ""
    st.rerun()
