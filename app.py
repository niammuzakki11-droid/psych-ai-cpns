import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import time
from streamlit_cookies_controller import CookieController

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

st.set_page_config(page_title="Psych-AI CPNS: Intelligence", page_icon="🧠")

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
    st.title("🛡️ Simulasi SKD CPNS 2024 (Standar BKN)")
    
    # 1. INISIALISASI STATE (Agar data tidak hilang saat refresh)
    if 'test_active' not in st.session_state:
        st.session_state.test_active = False
    if 'test_questions' not in st.session_state:
        st.session_state.test_questions = []
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    # --- KONDISI A: HALAMAN AWAL (TOMBOL MULAI) ---
    if not st.session_state.test_active and not st.session_state.submitted:
        st.info(f"""
        **Panduan Ujian:**
        - **Total Soal:** 110 (45 TKP, 35 TIU, 30 TWK)
        - **Waktu:** 100 Menit
        - **Sistem:** Acak & Standar Passing Grade BKN.
        """)
        
        if st.button("🚀 MULAI SIMULASI SEKARANG", use_container_width=True):
            # Ambil semua soal dari Supabase
            res_soal = supabase.table("bank_soal").select("*").execute()
            if res_soal.data:
                df_all = pd.DataFrame(res_soal.data)
                
                # Fungsi acak & rasio sesuai permintaan (45:35:30)
                def ambil_acak(kat, jml):
                    df_kat = df_all[df_all['kategori'] == kat]
                    return df_kat.sample(n=min(len(df_kat), jml)).to_dict('records')

                st.session_state.test_questions = ambil_acak('TKP', 45) + \
                                                  ambil_acak('TIU', 35) + \
                                                  ambil_acak('TWK', 30)
                
                st.session_state.test_active = True
                st.session_state.start_time = time.time()
                st.rerun()
            else:
                st.error("Gagal mengambil soal. Pastikan tabel 'bank_soal' tidak kosong!")

    # --- KONDISI B: SAAT UJIAN BERJALAN ---
    elif st.session_state.test_active:
        # 1. TIMER LOGIC (100 Menit)
        sisa_waktu = int((100 * 60) - (time.time() - st.session_state.start_time))
        
        if sisa_waktu <= 0:
            st.error("⏰ WAKTU HABIS!")
            st.session_state.test_active = False
            st.session_state.submitted = True
            st.rerun()

        st.sidebar.warning(f"⏳ Sisa Waktu: {sisa_waktu // 60}m {sisa_waktu % 60}s")
        
        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(st.session_state.test_questions):
                st.markdown(f"**Soal {i+1}** : {q['pertanyaan']}")
                user_answers[q['id']] = st.radio(f"Pilih jawaban untuk soal {i+1}", 
                                                [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d']], 
                                                key=f"q_{q['id']}", label_visibility="collapsed")
                st.markdown("---")
            
            submit_ujian = st.form_submit_button("KIRIM JAWABAN")
            
            if submit_ujian:
                # HITUNG SKOR
                skor_det = {"TIU": 0, "TWK": 0, "TKP": 0}
                for q in st.session_state.test_questions:
                    ans = user_answers.get(q['id'])
                    if q['kategori'] in ['TIU', 'TWK']:
                        if ans == q['jawaban_benar']: skor_det[q['kategori']] += 5
                    else: # TKP (Logika sederhana 5 poin jika benar, idealnya 1-5)
                        if ans == q['jawaban_benar']: skor_det['TKP'] += 5
                
                # SIMPAN KE SUPABASE
                supabase.table("user_scores").insert({
                    "nama_user": st.session_state.user.email,
                    "skor_total": sum(skor_det.values()),
                    "skor_tiu": skor_det["TIU"],
                    "skor_twk": skor_det["TWK"],
                    "skor_tkp": skor_det["TKP"],
                    "total_soal": len(st.session_state.test_questions)
                }).execute()
                
                st.session_state.test_active = False
                st.session_state.submitted = True
                st.session_state.final_answers = user_answers # Simpan untuk review
                st.rerun()

    # --- KONDISI C: HASIL & REVIEW (SETELAH SELESAI) ---
    elif st.session_state.submitted:
        st.success("🎉 Ujian Selesai! Skor Anda telah dicatat di tab Progres.")
        if st.button("Ulangi Simulasi"):
            st.session_state.submitted = False
            st.rerun()
        
        st.subheader("📝 Pembahasan Soal")
        for q in st.session_state.test_questions:
            with st.expander(f"Soal: {q['pertanyaan'][:50]}..."):
                u_ans = st.session_state.final_answers.get(q['id'])
                st.write(f"**Pertanyaan:** {q['pertanyaan']}")
                st.write(f"**Jawaban Anda:** {u_ans}")
                st.write(f"**Jawaban Benar:** {q['jawaban_benar']}")
                st.info(f"💡 **Pembahasan:** {q.get('pembahasan', 'Tidak ada pembahasan.')}")
                

with tab_progres:
    st.title("📊 Analisis Psikometri Mendalam")
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        # Membersihkan data dari nilai NULL agar tidak error saat dihitung
        df_clean = df.dropna(subset=['skor_tiu', 'skor_twk', 'skor_tkp'])
        
        if not df_clean.empty: # <--- PERBAIKAN SPASI DI SINI (Line 147)
            latest = df_clean.iloc[-1]
            
            # --- 1. DATA UNTUK GRAFIK ---
            chart_data = pd.DataFrame({
                'Kategori': ['TIU', 'TWK', 'TKP'],
                'Skor Anda': [latest['skor_tiu'], latest['skor_twk'], latest['skor_tkp']],
                'Target BKN': [PASSING_TIU, PASSING_TWK, PASSING_TKP]
            })
            
            df_plot = chart_data.melt(id_vars='Kategori', var_name='Tipe', value_name='Nilai')
            
            fig = px.bar(df_plot, x='Kategori', y='Nilai', color='Tipe', 
                         barmode='group',
                         color_discrete_map={'Skor Anda': '#1E88E5', 'Target BKN': '#FF5252'},
                         title="Perbandingan Skor Terakhir vs Ambang Batas BKN")
            
            # --- FITUR KUNCI GRAFIK (LOCK AXIS) ---
            fig.update_layout(
                yaxis_range=[0, 200],  # Mengunci skala 0-200 agar tidak lompat-lompat
                xaxis={'categoryorder':'array', 'categoryarray':['TIU','TWK','TKP']},
                dragmode=False,        # Mematikan zoom agar grafik tidak rusak saat di-scroll
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)

            # --- 2. EVALUASI AMBANG BATAS ---
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

            # --- 3. AI STUDY PATH ---
            st.markdown("---")
            st.subheader("🤖 AI Study Path Recommendation")
            scores = {'TIU': latest['skor_tiu'], 'TWK': latest['skor_twk'], 'TKP': latest['skor_tkp']}
            weakest = min(scores, key=scores.get)
            
            if weakest == 'TIU':
                st.error(f"⚠️ **Prioritas:** Fokus pada Logika & Numerik. Skor TIU Anda masih di bawah {PASSING_TIU}.")
            elif weakest == 'TWK':
                st.warning(f"⚠️ **Prioritas:** Perdalam Sejarah & Pancasila. Target TWK adalah {PASSING_TWK}.")
            else:
                st.info(f"⚠️ **Prioritas:** Tingkatkan Kepribadian Profesional. Anda butuh {PASSING_TKP} di TKP.")
    else:
        st.info("Belum ada data kuis. Ayo mulai simulasi pertama kamu!")      

# --- SIDEBAR LEADERBOARD ---
st.sidebar.markdown("---")
st.sidebar.subheader("🏆 Top Pejuang CPNS")
res_lb = supabase.table("user_scores").select("nama_user, skor_total").order("skor_total", desc=True).limit(5).execute()
if res_lb.data:
    st.sidebar.table(pd.DataFrame(res_lb.data))












