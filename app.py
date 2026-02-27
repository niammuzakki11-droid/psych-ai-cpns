import streamlit as st
import time

# Inisialisasi session state untuk timer dan skor
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

st.set_page_config(page_title="Psych-AI CPNS", page_icon="🚀")

st.title("🚀 Psych-AI CPNS: Pro Mode")
st.markdown("---")
st.write("Analisis Psikometri: Kami memantau kecepatan dan ketepatan logikamu.")

# Bank 10 Soal TIU (Logika, Deret, Silogisme)
questions = [
    {"id": 1, "q": "1, 4, 9, 16, 25, ...", "o": ["30", "36", "49", "64"], "a": "36"},
    {"id": 2, "q": "Semua pengurus PPQ adalah pemimpin. Sebagian pemimpin adalah mahasiswa. Maka...", "o": ["Semua pengurus PPQ mahasiswa", "Sebagian pengurus PPQ mahasiswa", "Ada pengurus PPQ yang mungkin mahasiswa", "Tidak ada kesimpulan yang pasti"], "a": "Ada pengurus PPQ yang mungkin mahasiswa"},
    {"id": 3, "q": "KAKAK : ADIK = ... : ...", "o": ["Ayah : Ibu", "Kakek : Cucu", "Besar : Kecil", "Guru : Murid"], "a": "Besar : Kecil"},
    {"id": 4, "q": "2, 6, 18, 54, ...", "o": ["108", "150", "162", "216"], "a": "162"},
    {"id": 5, "q": "Hutan : Pohon = ... : ...", "o": ["Laut : Ikan", "Kebun : Mawar", "Rumah : Atap", "Sekolah : Guru"], "a": "Laut : Ikan"},
    {"id": 6, "q": "Jika p = 2 dan q = 3, maka p² + 2pq + q² adalah...", "o": ["20", "25", "30", "35"], "a": "25"},
    {"id": 7, "q": "Semua santri memakai peci. Ni'am adalah santri. Maka...", "o": ["Ni'am mungkin memakai peci", "Ni'am tidak memakai peci", "Ni'am memakai peci", "Peci dipakai Ni'am"], "a": "Ni'am memakai peci"},
    {"id": 8, "q": "8, 4, 2, 1, ...", "o": ["0", "0.5", "1", "2"], "a": "0.5"},
    {"id": 9, "q": "MARAH : ... = ... : LEDAKAN", "o": ["Emosi : Bom", "Teriak : Tekanan", "Tenang : Diam", "Sabar : Panas"], "a": "Teriak : Tekanan"},
    {"id": 10, "q": "Jika x < y dan y < z, maka...", "o": ["x > z", "x = z", "x < z", "z < x"], "a": "x < z"}
]

with st.form("quiz_pro"):
    user_answers = {}
    for item in questions:
        st.subheader(f"Soal {item['id']}")
        user_answers[item['id']] = st.radio(item['q'], item['o'], key=f"q_{item['id']}")
    
    submitted = st.form_submit_button("Selesaikan Tes")

if submitted:
    # Hitung waktu pengerjaan
    duration = time.time() - st.session_state.start_time
    
    # Hitung skor
    score = sum([1 for q in questions if user_answers[q['id']] == q['a']])
    
    st.divider()
    st.balloons()
    st.success(f"🎯 Hasil: {score} / {len(questions)} Benar")
    st.info(f"⏱️ Waktu: {duration:.2f} detik")

    # --- ANALISIS PSYCH-AI (Kekuatan Utama Platform-mu) ---
    st.subheader("🧠 Laporan Analisis Psych-AI")
    avg_time = duration / len(questions)
    
    if score >= 8:
        if avg_time < 15:
            st.write("🔥 **PROFIL: Master Logika.** Kamu memiliki kecepatan proses kognitif yang luar biasa. Sangat siap menghadapi ambang batas TIU.")
        else:
            st.write("🕵️ **PROFIL: Analitis Teliti.** Kamu sangat berhati-hati. Keakuratanmu tinggi, pertahankan ritme ini.")
    else:
        st.write("📚 **PROFIL: Butuh Penguatan.** Fokus pada pola deret angka dan hubungan kata. Luangkan waktu lebih banyak untuk latihan harian.")

    if st.button("Ulangi Tes & Reset Timer"):
        del st.session_state.start_time
        st.rerun()
