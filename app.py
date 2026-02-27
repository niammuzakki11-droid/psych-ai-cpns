import streamlit as st

# Judul Website
st.title("🚀 Psych-AI CPNS: Test Mode")
st.write("Uji kesiapanmu dengan simulasi soal TIU singkat.")

# Data Soal (Nanti ini kita ambil dari SQL Database)
questions = [
    {
        "id": 1,
        "soal": "Semua mamalia menyusui. Paus adalah mamalia. Maka...",
        "opsi": ["Paus tidak menyusui", "Paus menyusui", "Semua paus bukan mamalia", "Paus adalah ikan"],
        "jawaban": "Paus menyusui"
    },
    {
        "id": 2,
        "soal": "1, 4, 9, 16, ... Berapakah angka selanjutnya?",
        "opsi": ["20", "25", "30", "36"],
        "jawaban": "25"
    }
]

# Form Quiz
with st.form("quiz_form"):
    user_answers = {}
    for q in questions:
        st.subheader(f"Soal {q['id']}")
        user_answers[q['id']] = st.radio(q['soal'], q['opsi'], key=q['id'])
    
    submit = st.form_submit_button("Kirim Jawaban")

# Logika Penilaian (Eksekusi Penilaian)
if submit:
    score = 0
    for q in questions:
        if user_answers[q['id']] == q['jawaban']:
            score += 1
    
    st.success(f"Tes Selesai! Skor kamu: {score} / {len(questions)}")
    
    # Fitur Psych-AI (Sederhana)
    if score == len(questions):
        st.balloons()
        st.write("Analisis AI: Kemampuan logika kamu sangat tajam!")
    else:
        st.info("Analisis AI: Fokus pada materi deret angka dan silogisme.")