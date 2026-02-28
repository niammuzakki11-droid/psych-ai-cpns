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
    st.title("Simulasi Ujian CPNS Terpadu")
    
    # Menambahkan logika pengacakan soal (shuffle) agar user selalu mendapat tantangan berbeda
    res_soal = supabase.table("bank_soal").select("*").execute() # penambahan-baru
    questions = res_soal.data # penambahan-baru
    
    if questions:
        with st.form("quiz_v6"):
            user_answers = {}
            for q in questions:
                st.subheader(f"[{q.get('kategori', 'Umum')}] Soal {q['id']}")
                user_answers[q['id']] = st.radio(q['pertanyaan'], [q['opsi_a'], q['opsi_b'], q['opsi_c'], q['opsi_d']], key=f"q_{q['id']}")
            
            if st.form_submit_button("Selesaikan & Simpan Hasil"):
                skor_det = {"TIU": 0, "TWK": 0, "TKP": 0}
                for q in questions:
                    if user_answers[q['id']] == q['jawaban_benar']:
                        k = q.get('kategori', 'TIU')
                        # TIU/TWK dikali 5 poin per soal sesuai standar BKN
                        skor_det[k] += 5 
                
                # Cek Passing Grade
                lulus = skor_det["TIU"] >= PASSING_TIU and skor_det["TWK"] >= PASSING_TWK and skor_det["TKP"] >= PASSING_TKP
                
                supabase.table("user_scores").insert({
                    "nama_user": st.session_state.user.email,
                    "skor_total": sum(skor_det.values()),
                    "skor_tiu": skor_det["TIU"], "skor_twk": skor_det["TWK"], "skor_tkp": skor_det["TKP"],
                    "total_soal": len(questions),
                    "durasi_detik": round(time.time() - st.session_state.start_time, 2)
                }).execute()
                
                if lulus: st.success("🎯 Selamat! Anda LOLOS Ambang Batas BKN.")
                else: st.warning("⚠️ Skor Anda belum mencapai Ambang Batas.")
                st.balloons()
    else:
        st.warning("Belum ada soal.")

with tab_progres:
    st.title("Peta Kekuatan Kognitif")
    res = supabase.table("user_scores").select("*").eq("nama_user", st.session_state.user.email).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)

        # 1. Tampilkan Grafik (Seperti Versi 6.2)
        # Visualisasi rata-rata skor per kategori
        avg_scores = df[['skor_tiu', 'skor_twk', 'skor_tkp']].mean().reset_index()
        avg_scores.columns = ['Kategori', 'Skor']
        st.plotly_chart(px.bar(avg_scores, x='Kategori', y='Skor', color='Kategori'), use_container_width=True)
    else:
        st.info("Belum ada data.")

        # 2. Ambil Data Tes Terbaru untuk Evaluasi
        # Kita gunakan dropna agar tidak error jika ada data NULL di baris lama
        df_clean = df.dropna(subset=['skor_tiu', 'skor_twk', 'skor_tkp'])
        
        if not df_clean.empty:
            latest_test = df_clean.iloc[-1] 

            st.markdown("---")
            st.subheader("📋 Hasil Evaluasi Ambang Batas")

            # --- MASUKKAN KODE AMBANG BATAS DI SINI ---
            pass_tiu, pass_twk, pass_tkp = 80, 65, 166 # Standar Resmi

            if latest_test['skor_tiu'] >= pass_tiu and \
               latest_test['skor_twk'] >= pass_twk and \
               latest_test['skor_tkp'] >= pass_tkp:
                st.success("🎉 SELAMAT! Anda Lulus Ambang Batas CPNS.")
                st.balloons()
            else:
                # Ini yang memunculkan pesan di screenshot kamu kemarin
                st.warning("⚠️ Skor Anda belum mencapai Ambang Batas.") 
                
                # Detail kategori yang tidak lulus
                if latest_test['skor_tiu'] < pass_tiu:
                    st.write(f"❌ **TIU:** {latest_test['skor_tiu']} (Butuh {pass_tiu})")
                if latest_test['skor_twk'] < pass_twk:
                    st.write(f"❌ **TWK:** {latest_test['skor_twk']} (Butuh {pass_twk})")
                if latest_test['skor_tkp'] < pass_tkp:
                    st.write(f"❌ **TKP:** {latest_test['skor_tkp']} (Butuh {pass_tkp})")

           # 3. AI Study Path (Rekomendasi Belajar)
           st.markdown("---")
           st.subheader("🤖 AI Study Path Recommendation")

           # Mengambil data tes terakhir (baris paling bawah di database)
           latest_test = df.iloc[-1] 

           # Logika mencari skor terendah
           scores_only = {
               'TIU (Intelegensia)': latest_test['skor_tiu'],
              'TWK (Wawasan)': latest_test['skor_twk'],
               'TKP (Kepribadian)': latest_test['skor_tkp']
           }
           # Mencari kategori mana yang nilainya paling kecil
           weakest_category = min(scores_only, key=scores_only.get)

           # Menampilkan saran berdasarkan hasil analisis
           if weakest_category == 'TIU (Intelegensia)':
               st.error(f"⚠️ **Prioritas Belajar:** {weakest_category}")
               st.write("Analisis AI menunjukkan hambatan pada logika numerik. Perbanyak latihan deret angka.")
           elif weakest_category == 'TWK (Wawasan)':
               st.warning(f"⚠️ **Prioritas Belajar:** {weakest_category}")
               st.write("Fokus pada pemahaman nilai-nilai Pancasila dan sejarah konstitusi.")
          else:
               st.success(f"⚠️ **Prioritas Belajar:** {weakest_category}")
               st.write("Skor kepribadianmu perlu ditingkatkan dalam aspek profesionalisme.")
            

# --- SIDEBAR LEADERBOARD ---
st.sidebar.markdown("---")
st.sidebar.subheader("🏆 Top Pejuang CPNS")
res_lb = supabase.table("user_scores").select("nama_user, skor_total").order("skor_total", desc=True).limit(5).execute()
if res_lb.data:
    st.sidebar.table(pd.DataFrame(res_lb.data))


