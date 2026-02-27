import streamlit as st
from supabase import create_client
import time

# Inisialisasi Timer
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

# Koneksi ke "Benteng" Data
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Psych-AI CPNS", page_icon="🚀")
st.title("🚀 Psych-AI CPNS: Database Pro")

# Ambil data dari Gudang SQL
@st.cache_data
def load_questions():
    # Mengambil semua soal dari tabel bank_soal
    response = supabase.table("bank_soal").select("*").execute()
    return response.data

try:
    questions = load_questions()
    
    if not questions:
        st.warning("Gudang soal masih kosong. Silakan isi tabel 'bank_soal' di Supabase!")
    else:
        with st.form("quiz_database"):
            user_answers = {}
            for q in questions:
                st.subheader(f"Soal {q['id']} [{q['kategori']}]")
                opsi = [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d']]
                user_answers[q['id']] = st.radio(q['pertanyaan'], opsi, key=f"q_{q['id']}")
            
            submit = st.form_submit_button("Selesaikan Tes")

        if submit:
            duration = time.time() - st.session_state.start_time
            score = sum([1 for q in questions if user_answers[q['id']] == q['jawaban_benar']])
            
            st.divider()
            st.success(f"🎯 Skor Akhir: {score} / {len(questions)}")
            st.info(f"⏱️ Kecepatan Berpikir: {duration:.2f} detik")
            
            # Analisis Psikometri
            st.subheader("🧠 Analisis Psych-AI")
            avg_time = duration / len(questions)
            if avg_time < 20:
                st.write("🔥 **Tipe Reaksi Cepat:** Fokus pada ketelitian agar tidak terjebak soal jebakan.")
            else:
                st.write("⚖️ **Tipe Analitis:** Pertahankan kedalaman analisismu, namun coba tingkatkan ritme pengerjaan.")

except Exception as e:
    st.error(f"Koneksi gagal: {e}")
    st.info("Pastikan SUPABASE_URL dan SUPABASE_KEY di Secrets sudah benar.")
