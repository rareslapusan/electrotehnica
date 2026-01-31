import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
import extra_streamlit_components as stx

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Electrotehnica Elite", page_icon="⚡", layout="centered")

# --- DESIGN PREMIUM (APPLE STYLE CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    :root {
        --apple-blue: #007AFF;
        --apple-gray: #8E8E93;
        --glass-bg: rgba(255, 255, 255, 0.7);
    }

    .stApp {
        background: radial-gradient(circle at top right, #e2e2e2, #ffffff);
        font-family: 'Inter', sans-serif;
    }

    /* Card stil Glassmorphism */
    .premium-card {
        background: var(--glass-bg);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 24px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 20px 40px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        transition: all 0.3s ease;
    }

    /* Blur efect pentru întrebări mascate */
    .blur-mask {
        filter: blur(15px);
        opacity: 0.3;
        pointer-events: none;
        user-select: none;
    }

    /* Buton stil Apple */
    .stButton > button {
        border-radius: 12px;
        background: linear-gradient(180deg, #007AFF 0%, #0056b3 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 12px 24px;
        width: 100%;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,122,255,0.3);
    }

    /* Countdown Styling */
    .countdown-timer {
        font-size: 48px;
        font-weight: 700;
        text-align: center;
        color: var(--apple-blue);
        letter-spacing: -2px;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXIUNE DATA ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Eroare de conexiune la baza de date. Verifică Secrets!")
    st.stop()

# --- LOGICĂ TIMP ---
now = datetime.now()
current_hour = now.hour
is_locked = 8 <= current_hour < 9

# --- INTERFAȚA DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.markdown("<div class='premium-card' style='text-align:center'>", unsafe_allow_html=True)
    st.title(" Electrotehnica Pro")
    st.write("Introdu codul de acces pentru a continua")
    user_name = st.text_input("Nume Complet", placeholder="Ion Popescu")
    if st.button("Autentificare"):
        if user_name:
            st.session_state.logged_in = user_name
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- NAVBAR ---
chosen_tab = stx.tab_bar(data=[
    stx.TabBarItemData(id="quiz", title="🎯 Provocarea Zilei", description="3 întrebări rapide"),
    stx.TabBarItemData(id="rank", title="🏆 Clasament", description="Top performeri"),
])

# --- TAB: QUIZ ---
if chosen_tab == "quiz":
    if is_locked:
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.subheader("Pregătim setul nou...")
        st.write("Întrebările vor apărea la ora 09:00.")
        # Calcul countdown simplu
        next_release = now.replace(hour=9, minute=0, second=0)
        diff = next_release - now
        st.markdown(f"<div class='countdown-timer'>{str(diff).split('.')[0]}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Preluare întrebări
        df = conn.read(worksheet="Questions", ttl=0)
        today_str = now.strftime('%Y-%m-%d')
        daily_qs = df[df['date'] == today_str].to_dict('records')

        if not daily_qs:
            st.info("Nu sunt întrebări postate pentru astăzi.")
        else:
            for idx, q in enumerate(daily_qs):
                q_key = f"q_{q['id']}_{st.session_state.logged_in}"
                
                st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                st.write(f"### Întrebarea {idx+1}")

                if q_key not in st.session_state:
                    st.markdown("<div class='blur-mask'>Aici apare textul întrebării și variantele de răspuns pentru test.</div>", unsafe_allow_html=True)
                    if st.button(f"Dezvăluie Întrebarea {idx+1}", key=f"btn_{idx}"):
                        st.session_state[q_key] = "active"
                        st.rerun()
                
                elif st.session_state[q_key] == "active":
                    # Cronometru 10 secunde
                    progress_bar = st.progress(100)
                    t_text = st.empty()
                    
                    for t in range(10, -1, -1):
                        t_text.markdown(f"**Timp rămas:** {t} secunde")
                        progress_bar.progress(t * 10)
                        time.sleep(1)
                        if t == 0:
                            st.session_state[q_key] = "expired"
                            st.rerun()
                    
                    st.write(q['question'])
                    opt = st.radio("Alege răspunsul:", [q['a'], q['b'], q['c'], q['d']], key=f"rad_{idx}")
                    if st.button("Confirmă", key=f"conf_{idx}"):
                        is_correct = 1 if opt == q['correct'] else 0
                        # Aici poți adăuga logica de salvare în Responses
                        st.session_state[q_key] = "done"
                        st.success(f"Răspuns înregistrat: {opt}")
                
                else:
                    st.write("✅ Finalizat pentru azi.")
                st.markdown("</div>", unsafe_allow_html=True)

# --- TAB: RANKING ---
elif chosen_tab == "rank":
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.title("🏆 Hall of Fame")
    # Simulare date (Înlocuiește cu citire reală din foaia 'Responses')
    rank_df = pd.DataFrame({
        "Utilizator": ["Andrei M.", "Elena P.", "Victor S."],
        "Întrebări Totale": [30, 30, 30],
        "Scor Corect": [28, 25, 22]
    })
    st.table(rank_df)
    st.markdown("</div>", unsafe_allow_html=True)
