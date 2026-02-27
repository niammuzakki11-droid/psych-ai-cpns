import streamlit as st
from supabase import create_client
import time
import pandas as pd # Untuk mengolah data angka
import plotly.express as px # Untuk membuat grafik keren

# 1. KONEKSI INFRASTRUKTUR
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Psych-AI CPNS Pro", page_icon="📈")

# 2. INISIALISASI SESSION STATE
if 'user' not in st.session_state:
    st.session_state.user = None

# (Bagian Logika Login & Register tetap sama seperti Versi 4)
# ... [Anggap saja fungsi login/register sudah ada di sini] ...

if st.session_state.user is None:
    # [Tampilan Form Login/Daftar]
    st.stop()

# --- HALAMAN UTAMA KHUSUS MEMBER ---
st.sidebar.success(f"Selamat Belajar, {st.session_state.user.email}")
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- TAB MENU: KUIS & DASHBOARD ---
tab_kuis, tab_progres = st.tabs(["✍️ Simulasi Ujian", "📊 Progress Dashboard"])

with tab_kuis:
    st.title("Simulasi CPNS Terpadu")
    # [Kode kuis yang menarik data dari bank_soal ada di sini]
    st.info("Selesaikan soal untuk memperbarui grafik di tab sebelah!")

with tab_progres:
    st.title("Analisis Performa Belajar")
    
    # AMBIL DATA DARI TABEL USER_SCORES
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        # Mengubah format tanggal agar enak dibaca
        df['tanggal_tes'] = pd.to_datetime(df['tanggal_tes']).dt.strftime('%d %b %H:%M')
        
        # 📈 GRAFIK 1: Tren Skor (Line Chart)
        fig_score = px.line(df, x='tanggal_tes', y='skor_total', 
                             title="Tren Kenaikan Nilai Kamu",
                             markers=True, line_shape="spline")
        st.plotly_chart(fig_score, use_container_width=True)
        
        # ⏱️ GRAFIK 2: Kecepatan Berpikir (Bar Chart)
        fig_time = px.bar(df, x='tanggal_tes', y='durasi_detik',
                          title="Kecepatan Pengerjaan (Detik)",
                          color='durasi_detik', color_continuous_scale='RdYlGn_r')
        st.plotly_chart(fig_time, use_container_width=True)
        
        # RINGKASAN DATA SCIENCE
        col1, col2 = st.columns(2)
        col1.metric("Skor Tertinggi", f"{df['skor_total'].max()}")
        col2.metric("Rata-rata Waktu", f"{df['durasi_detik'].mean():.1f}s")
    else:
        st.warning("Belum ada data. Silakan kerjakan tes pertama kamu!")
