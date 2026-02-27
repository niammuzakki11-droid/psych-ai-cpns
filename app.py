import streamlit as st
from supabase import create_client
import time
import pandas as pd
import plotly.express as px

# 1. KONEKSI INFRASTRUKTUR
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Psych-AI CPNS: Intelligence", page_icon="🧠")

# 2. INISIALISASI SESSION STATE
if 'user' not in st.session_state:
    st.session_state.user = None

# --- GERBANG AUTH (Tetap Konsisten dengan Versi Sebelumnya) ---
# [Gunakan logika login/register dari Versi 5 untuk bagian ini]

if st.session_state.user is None:
    st.stop()

# --- HALAMAN UTAMA ---
tab_kuis, tab_progres = st.tabs(["✍️ Simulasi Kategori", "📊 Analisis Mendalam"])

with tab_kuis:
    st.title("Simulasi CPNS Terpadu")
    
    @st.cache_data
    def load_questions():
        res = supabase.table("bank_soal").select("*").execute()
        return res.data

    questions = load_questions()

    if questions:
        with st.form("quiz_v6"):
            user_answers = {}
            for q in questions:
                st.subheader(f"[{q['kategori']}] Soal {q['id']}")
                opsi = [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d']]
                user_answers[q['id']] = st.radio(q['pertanyaan'], opsi, key=f"q_{q['id']}")
            
            if st.form_submit_button("Kirim Jawaban"):
                # LOGIKA BARU: HITUNG PER KATEGORI
                skor_detail = {"TIU": 0, "TWK": 0, "TKP": 0}
                for q in questions:
                    if user_answers[q['id']] == q['jawaban_benar']:
                        skor_detail[q['kategori']] += 1
                
                total_skor = sum(skor_detail.values())
                
                # SIMPAN KE DATABASE (Lengkap dengan Detail Kategori)
                data_score = {
                    "nama_user": st.session_state.user.email,
                    "skor_total": total_skor,
                    "skor_tiu": skor_detail["TIU"],
                    "skor_twk": skor_detail["TWK"],
                    "skor_tkp": skor_detail["TKP"],
                    "total_soal": len(questions)
                }
                supabase.table("user_scores").insert(data_score).execute()
                st.success("Analisis kognitif kamu telah berhasil disimpan!")
    else:
        st.warning("Gudang soal masih kosong.")

with tab_progres:
    st.title("Dashboard Psikometri")
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        
        # VISUALISASI KATEGORI (Bar Chart)
        # Mengambil rata-rata skor per kategori untuk melihat kekuatan/kelemahan
        avg_scores = df[['skor_tiu', 'skor_twk', 'skor_tkp']].mean().reset_index()
        avg_scores.columns = ['Kategori', 'Rata-rata Skor']
        
        fig_cat = px.bar(avg_scores, x='Kategori', y='Rata-rata Skor', 
                         title="Peta Kekuatan Kognitif Kamu",
                         color='Kategori', color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_cat, use_container_width=True)
        
        st.info("💡 **Tips AI:** Fokuskan belajarmu pada kategori dengan grafik terendah.")
    else:
        st.info("Belum ada data untuk dianalisis.")
