import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
from streamlit_cookies_controller import CookieController
from fpdf import FPDF
import io

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

def export_as_pdf(latest_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Report
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="RAPOR HASIL SIMULASI CPNS - PSYCH-AI", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Tanggal Tes: {latest_data['tanggal_tes'][:10]}", ln=True, align='C')
    pdf.ln(10)
    
    # Data Peserta
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Peserta: {latest_data['nama_user']}", ln=True)
    pdf.ln(5)
    
    # Tabel Skor
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(60, 10, "Kategori", 1)
    pdf.cell(60, 10, "Skor Anda", 1)
    pdf.cell(60, 10, "Ambang Batas", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=11)
    # TIU
    pdf.cell(60, 10, "TIU", 1)
    pdf.cell(60, 10, str(latest_data['skor_tiu']), 1)
    pdf.cell(60, 10, str(PASSING_TIU), 1)
    pdf.ln()
    # TWK
    pdf.cell(60, 10, "TWK", 1)
    pdf.cell(60, 10, str(latest_data['skor_twk']), 1)
    pdf.cell(60, 10, str(PASSING_TWK), 1)
    pdf.ln()
    # TKP
    pdf.cell(60, 10, "TKP", 1)
    pdf.cell(60, 10, str(latest_data['skor_tkp']), 1)
    pdf.cell(60, 10, str(PASSING_TKP), 1)
    pdf.ln()
    
    # Skor Total
    pdf.set_font("Arial", 'B', 12)
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"SKOR TOTAL: {latest_data['skor_total']}", ln=True)
    
    # Status Kelulusan
    is_lulus = latest_data['skor_tiu'] >= PASSING_TIU and \
               latest_data['skor_twk'] >= PASSING_TWK and \
               latest_data['skor_tkp'] >= PASSING_TKP
               
    status_txt = "LULUS AMBANG BATAS" if is_lulus else "BELUM LULUS"
    pdf.set_text_color(0, 128, 0) if is_lulus else pdf.set_text_color(255, 0, 0)
    pdf.cell(200, 10, txt=f"STATUS: {status_txt}", ln=True)
    
    return pdf.output(dest='S')

st.set_page_config(page_title="Psych-AI CPNS: Intelligence", page_icon="🧠")

# --- TARUH CSS DI SINI (Setelah set_page_config) ---
st.markdown("""
    <style>
    /* Mengubah tombol 'primary' menjadi Hijau (Terjawab/Ragu) */
    div.stButton > button[kind="primary"] {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
    }
    /* Membuat tombol 'secondary' tetap Abu-abu (Belum Terjawab) */
    div.stButton > button[kind="secondary"] {
        background-color: #f0f2f6 !important;
        color: #31333f !important;
        border: 1px solid #dcdcdc !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGIKA AUTO-LOGIN YANG AMAN ---
# 1. Ambil token (kunci) dari laci browser
saved_token = controller.get('supabase_token') 

# 2. Jika ada kunci dan kita belum login di sesi ini
if saved_token and st.session_state.user is None:
    try:
        # Tanyakan ke Supabase: "Kunci ini milik siapa?"
        res = supabase.auth.get_user(saved_token)
        if res.user:
            # Jika Supabase kenal, barulah kita simpan data user lengkapnya
            st.session_state.user = res.user
            
            # Pastikan timer sudah ada agar kuis tidak error
            if 'start_time' not in st.session_state:
                st.session_state.start_time = time.time()
                
            st.rerun() # Refresh agar dashboard muncul
    except Exception:
        # Jika kunci rusak atau kadaluarsa, buang saja kuncinya
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
    # 1. INISIALISASI STATE NAVIGASI (Infrastruktur CAT)
    if 'current_idx' not in st.session_state: st.session_state.current_idx = 0
    if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
    if 'ragu_ragu' not in st.session_state: st.session_state.ragu_ragu = {}

    # --- KONDISI A: HALAMAN AWAL (TOMBOL MULAI) ---
    if not st.session_state.get('test_active') and not st.session_state.get('submitted'):
        st.title("🛡️ CAT SKD CPNS - Simulasi Resmi")
        st.info(f"""
        **Struktur Tes SKD:**
        - **TWK**: 30 Soal | **TIU**: 35 Soal | **TKP**: 45 Soal
        - **Waktu**: 100 Menit (Sistem akan berhenti otomatis)
        - **Passing Grade**: TWK ({PASSING_TWK}), TIU ({PASSING_TIU}), TKP ({PASSING_TKP})
        """)
        
        if st.button("🚀 MULAI SESI UJIAN", use_container_width=True):
            res_soal = supabase.table("bank_soal").select("*").execute()
            if res_soal.data:
                df_all = pd.DataFrame(res_soal.data)
                def ambil_acak(kat, jml):
                    df_kat = df_all[df_all['kategori'].str.upper() == kat.upper()]
                    return df_kat.sample(n=min(len(df_kat), jml)).to_dict('records')

                # Urutan resmi sesuai CAT BKN
                st.session_state.test_questions = ambil_acak('TWK', 30) + \
                                                  ambil_acak('TIU', 35) + \
                                                  ambil_acak('TKP', 45)
                st.session_state.test_active = True
                st.session_state.start_time = time.time()
                st.rerun()

    # --- KONDISI B: MODE UJIAN AKTIF (SISTEM NAVIGASI) ---
    elif st.session_state.get('test_active'):
        # 1. TIMER & HEADER
        sisa_waktu = int((100 * 60) - (time.time() - st.session_state.start_time))
        if sisa_waktu <= 0:
            st.session_state.test_active = False
            st.session_state.submitted = True
            st.rerun()

        st.sidebar.error(f"⏳ Sisa Waktu: {sisa_waktu // 60:02d}:{sisa_waktu % 60:02d}")
        st.write(f"👤 **Peserta:** {st.session_state.user.email}")

        # 2. GRID NAVIGASI (Fixing Logic Warna & Tipe)
        st.markdown("### Navigasi Soal")
        n_soal = len(st.session_state.test_questions)
        for row_start in range(0, n_soal, 10): 
            cols = st.columns(10)
            for i in range(10):
                idx = row_start + i
                if idx < n_soal:
                    q_id = st.session_state.test_questions[idx]['id']
                    
                    # --- LOGIKA WARNA TOMBOL CAT BKN ---
                    if st.session_state.ragu_ragu.get(q_id):
                        # Ragu-ragu: Tetap pakai icon agar beda secara visual
                        btn_label, btn_type = f"⚠️ {idx+1}", "primary"
                    elif q_id in st.session_state.user_answers:
                        # TERJAWAB: Gunakan 'primary' agar berubah HIJAU via CSS
                        btn_label, btn_type = f"{idx+1}", "primary"
                    else:
                        # BELUM TERJAWAB: Gunakan 'secondary' (Abu-abu/Putih)
                        btn_label, btn_type = f"{idx+1}", "secondary"
                    
                    if cols[i].button(btn_label, key=f"nav_{idx}", use_container_width=True, type=btn_type):
                        st.session_state.current_idx = idx
                        st.rerun()

        st.divider()

        # 3. AREA SOAL
        q = st.session_state.test_questions[st.session_state.current_idx]
        st.subheader(f"Soal Nomor {st.session_state.current_idx + 1}")
        st.markdown(f"**Kategori:** {q['kategori'].upper()}")
        st.write(q['pertanyaan'])

        opsi_label = ['A', 'B', 'C', 'D', 'E']
        options = [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d'], q['opsi_e']]
        old_ans = st.session_state.user_answers.get(q['id'])
                   
        # 4. TOMBOL KONTROL BAWAH
        st.write("")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.session_state.current_idx > 0:
                if st.button("⬅️ Sebelumnya"):
                    st.session_state.current_idx -= 1
                    st.rerun()
        with c2:
            is_ragu = st.checkbox("Ragu-Ragu", value=st.session_state.ragu_ragu.get(q['id'], False), key=f"rg_{q['id']}")
            st.session_state.ragu_ragu[q['id']] = is_ragu
        with c3:
            if st.session_state.current_idx < n_soal - 1:
                if st.button("Simpan & Lanjutkan ➡️"):
                    st.session_state.current_idx += 1
                    st.rerun()
            else:
                if st.button("🏁 SELESAI UJIAN", type="primary"):
                    skor = {"TWK": 0, "TIU": 0, "TKP": 0}
                    n_soal = len(st.session_state.test_questions) # Pastikan n_soal dihitung ulang di sini
                
                    for ques in st.session_state.test_questions:
                        user_ans = st.session_state.user_answers.get(ques['id'])
                        kat = ques['kategori'].upper()
                
                        if user_ans:
                            # Mapping 5 Opsi ke 5 Kolom Poin
                            mapping_opsi = {
                                ques['opsi_a']: 'poin_a',
                                ques['opsi_b']: 'poin_b',
                                ques['opsi_c']: 'poin_c',
                                ques['opsi_d']: 'poin_d',
                                ques['opsi_e']: 'poin_e' # Baris krusial!
                            }
                
                            kolom_poin = mapping_opsi.get(user_ans)
                            poin_didapat = ques.get(kolom_poin, 0)
                
                            if kat in skor:
                                skor[kat] += poin_didapat
                    
                    # Simpan ke Supabase
                    supabase.table("user_scores").insert({
                        "nama_user": st.session_state.user.email,
                        "skor_total": sum(skor.values()),
                        "skor_tiu": skor["TIU"], "skor_twk": skor["TWK"], "skor_tkp": skor["TKP"],
                        "total_soal": n_soal,
                        "durasi_detik": round(time.time() - st.session_state.start_time)
                    }).execute()
                    
                    st.session_state.test_active = False
                    st.session_state.submitted = True
                    st.rerun()

    # --- KONDISI C: HASIL & PEMBAHASAN ---
    elif st.session_state.get('submitted'):
        st.success("🎉 Simulasi Selesai! Skor Anda telah tercatat di tab Progres.")
        if st.button("🔄 Ulangi Simulasi Baru"):
            st.session_state.submitted = False
            st.session_state.user_answers = {}
            st.session_state.ragu_ragu = {}
            st.session_state.current_idx = 0
            st.rerun()
            
        st.subheader("📝 Review & Pembahasan")
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
            st.plotly_chart(fig_radar, use_container_width=True)

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
                
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("TIU", latest['skor_tiu'], f"Min {PASSING_TIU}")
            with col2: st.metric("TWK", latest['skor_twk'], f"Min {PASSING_TWK}")
            with col3: st.metric("TKP", latest['skor_tkp'], f"Min {PASSING_TKP}")

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
            pdf_bytes = export_as_pdf(latest)
            st.download_button(
                label="📥 Download Laporan Hasil (PDF)",
                data=pdf_bytes,
                file_name=f"Report_CPNS_{latest['tanggal_tes'][:10]}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
           
    else:
        st.info("Belum ada data kuis. Ayo mulai simulasi pertama kamu!")      

# --- SIDEBAR LEADERBOARD ---
st.sidebar.markdown("---")
st.sidebar.subheader("🏆 Top Pejuang CPNS")
res_lb = supabase.table("user_scores").select("nama_user, skor_total").order("skor_total", desc=True).limit(5).execute()
if res_lb.data:
    st.sidebar.table(pd.DataFrame(res_lb.data))
