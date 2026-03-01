import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
from streamlit_cookies_controller import CookieController
from fpdf import FPDF
import io

# ==========================================
# 1. KONFIGURASI & STATE (WAJIB DI ATAS)
# ==========================================
st.set_page_config(page_title="Psych-AI CPNS", page_icon="🧠", layout="wide")

# Standar Passing Grade
PASSING_TWK, PASSING_TIU, PASSING_TKP = 65, 80, 166

# Inisialisasi State yang Aman
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = 'dashboard'
if 'submitted' not in st.session_state: st.session_state.submitted = False
if 'test_active' not in st.session_state: st.session_state.test_active = False
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'ragu_ragu' not in st.session_state: st.session_state.ragu_ragu = {}
if 'current_idx' not in st.session_state: st.session_state.current_idx = 0
if 'test_questions' not in st.session_state: st.session_state.test_questions = []

# Koneksi Supabase & Cookie
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)
controller = CookieController()

# Custom CSS untuk Tombol Navigasi Soal
st.markdown("""
    <style>
    div.stButton > button[kind="primary"] { background-color: #28a745 !important; color: white !important; border: none !important; }
    div.stButton > button[kind="secondary"] { background-color: #f0f2f6 !important; color: #31333f !important; border: 1px solid #dcdcdc !important; }
    .stButton > button { width: 100%; border-radius: 5px; height: 3em; padding: 0px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI-UTAMA (PDF & SKOR)
# ==========================================

def export_as_pdf(latest_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(200, 10, txt="RAPOR HASIL SIMULASI CPNS - PSYCH-AI", ln=True, align='C')
    pdf.set_font("helvetica", size=10)
    pdf.cell(200, 10, txt=f"Tanggal: {str(latest_data['tanggal_tes'])[:10]}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(200, 10, txt=f"Peserta: {latest_data['nama_user']}", ln=True)
    pdf.ln(5)
    
    # Tabel Skor
    pdf.set_font("helvetica", 'B', 11)
    pdf.cell(60, 10, "Kategori", 1); pdf.cell(60, 10, "Skor", 1); pdf.cell(60, 10, "Ambang Batas", 1); pdf.ln()
    pdf.set_font("helvetica", size=11)
    pdf.cell(60, 10, "TIU", 1); pdf.cell(60, 10, str(latest_data['skor_tiu']), 1); pdf.cell(60, 10, str(PASSING_TIU), 1); pdf.ln()
    pdf.cell(60, 10, "TWK", 1); pdf.cell(60, 10, str(latest_data['skor_twk']), 1); pdf.cell(60, 10, str(PASSING_TWK), 1); pdf.ln()
    pdf.cell(60, 10, "TKP", 1); pdf.cell(60, 10, str(latest_data['skor_tkp']), 1); pdf.cell(60, 10, str(PASSING_TKP), 1); pdf.ln()
    
    pdf.ln(5); pdf.set_font("helvetica", 'B', 12)
    pdf.cell(200, 10, txt=f"SKOR TOTAL: {latest_data['skor_total']}", ln=True)
    return bytes(pdf.output())

def show_dashboard():
    st.title(f"👋 Halo, Pejuang!")
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).order("tanggal_tes", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Total Simulasi", f"{len(df)} Kali")
        c2.metric("🏆 Skor Tertinggi", df['skor_total'].max())
        c3.metric("⏳ Rata-rata Skor", int(df['skor_total'].mean()))
        
        st.subheader("📈 Tren Progres")
        fig = px.line(df.sort_values('tanggal_tes'), x='tanggal_tes', y='skor_total', markers=True, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Belum ada data. Mulai simulasi pertamamu!")
  
def show_profile_page():
    st.title("👤 Profil Pejuang CPNS")
    st.write(f"Halo, **{st.session_state.user.email}**! Pantau sejauh mana persiapanmu di sini.")
    
    # 1. AMBIL DATA DARI SUPABASE
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).order("tanggal_tes", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        
        # 2. METRIK KUMULATIF
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Percobaan", f"{len(df)} Kali")
        col2.metric("Skor Tertinggi", df['skor_total'].max())
        col3.metric("Rata-rata Skor", int(df['skor_total'].mean()))
        
        st.divider()
        
        # 3. GRAFIK TREN (Locked & Clean)
        st.subheader("📈 Progres Skor Keseluruhan")
        df_line = df.sort_values('tanggal_tes')
        fig = px.line(df_line, x='tanggal_tes', y='skor_total', markers=True, template="plotly_dark")
        
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        fig.update_layout(dragmode=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.divider()
        
        # 4. TABEL RIWAYAT LENGKAP
        st.subheader("📜 Riwayat Pengerjaan")
        df_display = df[['tanggal_tes', 'skor_tiu', 'skor_twk', 'skor_tkp', 'skor_total']].copy()
        df_display.columns = ['Tanggal', 'TIU', 'TWK', 'TKP', 'Total']
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada riwayat pengerjaan. Yuk, mulai simulasi pertama kamu!")

def show_simulasi():
    if not st.session_state.submitted:
        if not st.session_state.test_active:
            st.title("🛡️ Persiapan Ujian")
            st.info(f"Target: TWK > {PASSING_TWK}, TIU > {PASSING_TIU}, TKP > {PASSING_TKP}")
            if st.button("🚀 MULAI SESI UJIAN", type="primary"):
                res_soal = supabase.table("bank_soal").select("*").execute()
                if res_soal.data:
                    # Logika pengacakan soal
                    st.session_state.test_questions = res_soal.data # Contoh sederhana
                    st.session_state.test_active = True
                    st.session_state.start_time = time.time()
                    st.rerun()
        else:
            render_exam()
    else:
        render_results()

def render_exam():
    # Sidebar Timer & Navigasi
    total_waktu = 100 * 60
    sisa = int(total_waktu - (time.time() - st.session_state.start_time))
    
    if sisa <= 0:
        st.session_state.submitted = True
        st.rerun()

    with st.sidebar:
        st.error(f"⏳ Sisa Waktu: {sisa // 60:02d}:{sisa % 60:02d}")
        # Grid Nomor Soal
        n = len(st.session_state.test_questions)
        # --- GRID NOMOR SOAL (SIDEBAR) ---
        st.markdown("### 🧭 Navigasi Soal")
        
        n_soal = len(st.session_state.test_questions)
        grid_cols = 5  # Menampilkan 5 tombol per baris
        
        # Loop untuk membuat baris
        for row_start in range(0, n_soal, grid_cols):
            cols = st.columns(grid_cols)
            for i in range(grid_cols):
                idx = row_start + i
                if idx < n_soal:
                    q_id = st.session_state.test_questions[idx]['id']
                    
                    # LOGIKA WARNA TOMBOL
                    # 1. Jika Ragu-Ragu -> Hijau (Primary) dengan icon peringatan
                    # 2. Jika Sudah Dijawab -> Hijau (Primary)
                    # 3. Jika Belum -> Abu-abu (Secondary)
                    
                    is_answered = q_id in st.session_state.user_answers
                    is_ragu = st.session_state.ragu_ragu.get(q_id, False)
                    
                    b_type = "primary" if (is_answered or is_ragu) else "secondary"
                    label = f"⚠️{idx+1}" if is_ragu else f"{idx+1}"
                    
                    if cols[i].button(label, key=f"nav_{idx}", use_container_width=True, type=b_type):
                        st.session_state.current_idx = idx
                        st.rerun()
     
    # Area Soal
    q = st.session_state.test_questions[st.session_state.current_idx]
    st.subheader(f"Soal Nomor {st.session_state.current_idx + 1}")
    st.write(q['pertanyaan'])
    
    options = [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d'], q['opsi_e']]
    ans = st.radio("Pilih Jawaban:", options, key=f"r_{q['id']}")
    st.session_state.user_answers[q['id']] = ans

    # Tombol Navigasi
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Kembali") and st.session_state.current_idx > 0:
            st.session_state.current_idx -= 1
            st.rerun()
    with col2:
        if st.session_state.current_idx < len(st.session_state.test_questions)-1:
            if st.button("Lanjut ➡️"):
                st.session_state.current_idx += 1
                st.rerun()
        else:
            if st.button("🏁 SELESAI", type="primary"):
                st.session_state.submitted = True
                st.rerun()

def render_results():
    st.balloons()
    st.title("🎉 Hasil Ujian")
     with tab_pembahasan:
            st.title("📝 Review & Pembahasan")
                
            for q in st.session_state.test_questions:
                with st.expander(f"Soal {st.session_state.test_questions.index(q)+1} - {q['kategori'].upper()}"):
                    st.write(f"**Pertanyaan:** {q['pertanyaan']}")
                    st.write(f"**Jawaban Anda:** {st.session_state.user_answers.get(q['id'], 'Tidak dijawab')}")
                    st.write(f"**Kunci Jawaban:** {q['jawaban_benar']}")
                    st.info(f"🧠 **Pembahasan:** {q.get('pembahasan', 'Belum ada penjelasan.')}")
                        
        with tab_progres:
            st.title("📊 Analisis Psikometri")
                        
            # Ambil data terbaru dari Supabase
            res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).order("tanggal_tes", desc=False).execute()
                            
            if res.data:
                df = pd.DataFrame(res.data)
                if not df.empty:
                    latest = df.iloc[-1]
                    # ... kode radar chart dan kawan-kawan ...
                                
                    # --- 1. GRAFIK RADAR (Visualisasi ala Data Scientist) ---
                    import plotly.graph_objects as go
                        
                    categories = ['TIU', 'TWK', 'TKP']
                    # Normalisasi skor ke skala 0-100 agar grafik radar simetris
                    scores_norm = [
                        (latest['skor_tiu'] / 175) * 100, 
                        (latest['skor_twk'] / 150) * 100, 
                        (latest['skor_tkp'] / 225) * 100
                    ]
    
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=scores_norm,
                        theta=categories,
                        fill='toself',
                        name='Profil Anda',
                        line_color='#1E88E5'
                    ))
                    
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        showlegend=True,
                        title="Radar Kompetensi (Skala 100)"
                    )
                    
                    fig_radar.update_xaxes(fixedrange=True) # Kunci sumbu horizontal
                    fig_radar.update_yaxes(fixedrange=True) # Kunci sumbu vertikal
                    fig_radar.update_layout(dragmode=False)
                    
                    # Gunakan config untuk mematikan scroll zoom dan menyembunyikan bar
                    st.plotly_chart(fig_radar, use_container_width=True, config={
                        'displayModeBar': False, 
                        'scrollZoom': False
                    })
                        
                    # --- 2. ANALISIS KEKUATAN & KELEMAHAN ---
                    st.subheader("💡 Analisis Performa")
                                    
                    # Cari kategori dengan persentase terendah
                    pct_scores = {
                        'TIU': (latest['skor_tiu'] / 175),
                        'TWK': (latest['skor_twk'] / 150),
                        'TKP': (latest['skor_tkp'] / 225)
                    }
                    weakest = min(pct_scores, key=pct_scores.get)
                    strongest = max(pct_scores, key=pct_scores.get)
                
                    c1, c2 = st.columns(2)
                    with c1:
                        st.success(f"✅ **Kekuatan Utama:** {strongest}")
                        st.write("Pertahankan performa ini! Kamu sudah memiliki pondasi yang kuat di aspek ini.")
                    with c2:
                        st.error(f"⚠️ **Perlu Ditingkatkan:** {weakest}")
                        st.write(f"Fokuslah mempelajari materi {weakest} lebih dalam untuk mengejar ambang batas.")
        
                    # --- 3. STATUS KELULUSAN (Metrik) ---
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    with col1: st.metric("Skor TIU", latest['skor_tiu'], f"Target {PASSING_TIU}")
                    with col2: st.metric("Skor TWK", latest['skor_twk'], f"Target {PASSING_TWK}")
                    with col3: st.metric("Skor TKP", latest['skor_tkp'], f"Target {PASSING_TKP}")
                                    
                    # --- 4. EVALUASI AMBANG BATAS ---
                    st.markdown("---")
                    st.subheader("📋 Status Kelulusan Terakhir")
                                
                    if latest['skor_tiu'] >= PASSING_TIU and \
                        latest['skor_twk'] >= PASSING_TWK and \
                        latest['skor_tkp'] >= PASSING_TKP:
                        st.success("🎉 SELAMAT! Anda Lulus Ambang Batas BKN.")
                        st.balloons()
                    else:
                        st.warning("⚠️ Skor Anda belum mencapai Ambang Batas.")
                                    
                    # --- 5.  STUDY PATH ---
                    st.markdown("---")
                    st.subheader("🤖 Study Path Recommendation")
                    scores = {'TIU': latest['skor_tiu'], 'TWK': latest['skor_twk'], 'TKP': latest['skor_tkp']}
                    weakest = min(scores, key=scores.get)
                                
                    if weakest == 'TIU':
                        st.error(f"⚠️ **Prioritas:** Fokus pada Logika & Numerik. Skor TIU Anda masih di bawah {PASSING_TIU}.")
                    elif weakest == 'TWK':
                        st.warning(f"⚠️ **Prioritas:** Perdalam Sejarah & Pancasila. Target TWK adalah {PASSING_TWK}.")
                    else:
                        st.info(f"⚠️ **Prioritas:** Tingkatkan Kepribadian Profesional. Anda butuh {PASSING_TKP} di TKP.")
                        
                    # 6. Tombol Download Report (Taruh di bawah st.metric)
                    st.write("---")
                    try:
                        pdf_bytes = export_as_pdf(latest)
                        
                        if pdf_bytes:
                            st.download_button(
                                label="📥 Download Laporan Hasil (PDF)",
                                data=pdf_bytes,
                                file_name=f"Rapor_CPNS_{latest['tanggal_tes'][:10]}.pdf",
                                mime="application/pdf",
                                key="btn_download_unique", # Tambahkan KEY unik di sini
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"Gagal menyiapkan file PDF: {e}")
                else:
                    st.info("Belum ada data kuis. Ayo mulai simulasi pertama kamu!")      
 
# 3. RENDER HALAMAN
# ==========================================

def show_dashboard():
    st.title(f"👋 Selamat Datang, Pejuang!")
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).order("tanggal_tes", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Total Simulasi", f"{len(df)} Kali")
        c2.metric("🏆 Skor Tertinggi", df['skor_total'].max())
        c3.metric("⏳ Rata-rata Skor", int(df['skor_total'].mean()))
        
        st.subheader("📈 Tren Progres")
        fig = px.line(df.sort_values('tanggal_tes'), x='tanggal_tes', y='skor_total', markers=True, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada data aktivitas. Mulai simulasi pertamamu!")

def render_exam():
    total_waktu = 100 * 60
    sisa = int(total_waktu - (time.time() - st.session_state.start_time))
    
    if sisa <= 0:
        hitung_dan_simpan()

    with st.sidebar:
        st.error(f"⏳ Sisa Waktu: {sisa // 60:02d}:{sisa % 60:02d}")
        st.divider()
        st.markdown("### 🧭 Navigasi Soal")
        n_soal = len(st.session_state.test_questions)
        for r in range(0, n_soal, 5):
            cols = st.columns(5)
            for i in range(5):
                idx = r + i
                if idx < n_soal:
                    q_id = st.session_state.test_questions[idx]['id']
                    bt = "primary" if (q_id in st.session_state.user_answers or st.session_state.ragu_ragu.get(q_id)) else "secondary"
                    label = f"⚠️{idx+1}" if st.session_state.ragu_ragu.get(q_id) else f"{idx+1}"
                    if cols[i].button(label, key=f"nav_{idx}", type=bt):
                        st.session_state.current_idx = idx
                        st.rerun()

    q = st.session_state.test_questions[st.session_state.current_idx]
    st.subheader(f"Soal Nomor {st.session_state.current_idx + 1} ({q['kategori'].upper()})")
    st.markdown(f"### {q['pertanyaan']}")
    
    opts = [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d'], q['opsi_e']]
    old_ans = st.session_state.user_answers.get(q['id'])
    idx_default = opts.index(old_ans) if old_ans in opts else None
    
    ans = st.radio("Pilih Jawaban:", opts, index=idx_default, key=f"q_radio_{q['id']}")
    if ans: st.session_state.user_answers[q['id']] = ans

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.session_state.current_idx > 0:
            if st.button("⬅️ Sebelumnya"): st.session_state.current_idx -= 1; st.rerun()
    with c2:
        st.checkbox("Ragu-Ragu", key=f"chk_ragu_{q['id']}", 
                    value=st.session_state.ragu_ragu.get(q['id'], False),
                    on_change=lambda: st.session_state.ragu_ragu.update({q['id']: not st.session_state.ragu_ragu.get(q['id'], False)}))
    with c3:
        if st.session_state.current_idx < n_soal - 1:
            if st.button("Simpan & Lanjut ➡️"): st.session_state.current_idx += 1; st.rerun()
        else:
            if st.button("🏁 SELESAI UJIAN", type="primary"): hitung_dan_simpan()

def render_results():
    st.success("🎉 Simulasi Selesai!")
    tab_pembahasan, tab_progres, tab_leaderboard = st.tabs(["📝 Pembahasan", "📊 Psikometri", "🏆 Leaderboard"])

    with tab_pembahasan:
        for i, q in enumerate(st.session_state.test_questions):
            with st.expander(f"Soal {i+1} - {q['kategori'].upper()}"):
                st.write(f"**Pertanyaan:** {q['pertanyaan']}")
                st.write(f"**Jawaban Anda:** {st.session_state.user_answers.get(q['id'], 'Tidak dijawab')}")
                st.write(f"**Kunci Jawaban:** {q['jawaban_benar']}")
                st.info(f"🧠 **Pembahasan:** {q.get('pembahasan', 'Belum ada penjelasan.')}")

    with tab_progres:
        res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).order("tanggal_tes", desc=True).limit(1).execute()
        if res.data:
            latest = res.data[0]
            # Radar Chart
            categories = ['TIU', 'TWK', 'TKP']
            scores_norm = [(latest['skor_tiu']/175)*100, (latest['skor_twk']/150)*100, (latest['skor_tkp']/225)*100]
            fig = go.Figure(data=go.Scatterpolar(r=scores_norm, theta=categories, fill='toself'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Radar Kompetensi")
            st.plotly_chart(fig, use_container_width=True)
            
            # Download PDF
            if st.button("📥 Download PDF Report"):
                pdf_bytes = export_as_pdf(latest)
                st.download_button(label="Klik untuk Unduh", data=pdf_bytes, file_name="Rapor_CPNS.pdf", mime="application/pdf")

    with tab_leaderboard:
        res_lb = supabase.table("user_scores").select("nama_user, skor_total").order("skor_total", desc=True).limit(10).execute()
        if res_lb.data:
            st.table(pd.DataFrame(res_lb.data))

# ==========================================
# 4. SISTEM AUTH & ROUTING (UTAMA)
# ==========================================

# Auto Login Check
saved_token = controller.get('supabase_token')
if saved_token and st.session_state.user is None:
    try:
        res = supabase.auth.get_user(saved_token)
        if res.user: 
            st.session_state.user = res.user
            st.rerun()
    except: controller.remove('supabase_token')

# Gerbang Login
if st.session_state.user is None:
    st.title("🚀 Pejuang CPNS")
    t1, t2 = st.tabs(["🔑 Login", "📝 Daftar Akun Baru"])
    with t1:
        with st.form("L"):
            em = st.text_input("Email", key="l_email")
            pw = st.text_input("Password", type="password", key="l_pw")
            if st.form_submit_button("Masuk"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": em, "password": pw})
                    st.session_state.user = res.user
                    controller.set('supabase_token', res.session.access_token)
                    st.rerun()
                except Exception as e: st.error(f"Login Gagal: {e}")
    with t2:
        with st.form("D"):
            ne = st.text_input("Email Baru", key="d_email")
            np = st.text_input("Password", type="password", key="d_pw")
            if st.form_submit_button("Daftar"):
                try:
                    supabase.auth.sign_up({"email": ne, "password": np})
                    st.info("Cek email konfirmasi!")
                except Exception as e: st.error(e)
    st.stop()

# --- SIDEBAR UTAMA ---
with st.sidebar:
    st.write(f"👤 {st.session_state.user.email}")
    nav = st.radio("🧭 Menu", ["Dashboard", "Simulasi", "Profil"], 
                   index=0 if st.session_state.page == 'dashboard' else 1 if st.session_state.page == 'simulasi' else 2)
    st.session_state.page = nav.lower()
    if st.button("Logout"):
        supabase.auth.sign_out(); controller.remove('supabase_token')
        st.session_state.clear(); st.rerun()

# --- ROUTER HALAMAN ---
if st.session_state.page == 'dashboard':
    show_dashboard()
elif st.session_state.page == 'simulasi':
    if not st.session_state.submitted:
        if not st.session_state.test_active:
            st.title("🛡️ Simulasi CAT SKD")
            if st.button("🚀 MULAI SESI UJIAN"):
                res = supabase.table("bank_soal").select("*").execute()
                if res.data:
                    df = pd.DataFrame(res.data)
                    st.session_state.test_questions = df.sample(n=min(len(df), 110)).to_dict('records')
                    st.session_state.test_active = True
                    st.session_state.start_time = time.time()
                    st.rerun()
        else:
            render_exam()
    else:
        render_results()
elif st.session_state.page == 'profil':
    st.title("👤 Profil Saya")
    show_dashboard() # Reuse metrik dashboard
