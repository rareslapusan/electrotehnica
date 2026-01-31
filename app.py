import streamlit as st
import pandas as pd
import time
from datetime import datetime, time as dt_time
from streamlit_gsheets import GSheetsConnection

# Configurare Pagina (Design Premium)
st.set_page_config(page_title="Quiz Master Pro", layout="centered")

# CSS pentru stil Apple (Glassmorphism & Rounded Corners)
st.markdown("""
<style>
    .stApp { background-color: #f5f5f7; }
    .stButton>button {
        border-radius: 12px;
        background-color: #007AFF;
        color: white;
        border: none;
        transition: 0.3s;
        width: 100%;
        height: 3em;
    }
    .stButton>button:hover { background-color: #0051a8; }
    .question-card {
        background: rgba(255, 255, 255, 0.8);
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        margin-bottom: 20px;
    }
    .blur-text { filter: blur(8px); pointer-events: none; user-select: none; }
    .timer-text { font-size: 24px; font-weight: bold; color: #FF3B30; text-align: center; }
</style>
""", unsafe_allow_html=True)

# Conectare la Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_current_questions():
    df = conn.read(worksheet="Questions")
    today = datetime.now().strftime('%Y-%m-%d')
    return df[df['date'] == today].to_dict('records')

# Logica de Timp
now = datetime.now().time()
is_countdown = dt_time(8, 0) <= now < dt_time(9, 0)

# Sidebar - Login (Simplificat)
with st.sidebar:
    st.title(" Quiz Login")
    user = st.text_input("Username", placeholder="nume.prenume")
    if not user:
        st.warning("Te rugăm să te loghezi.")
        st.stop()

tab1, tab2 = st.tabs(["🎯 Întrebări", "📊 Clasament"])

with tab1:
    if is_countdown:
        st.subheader("Următoarele întrebări apar la ora 09:00")
        target_time = datetime.combine(datetime.today(), dt_time(9, 0))
        remaining = (target_time - datetime.now()).seconds
        st.metric("Timp rămas", f"{remaining // 60} min")
    else:
        questions = get_current_questions()
        for i, q in enumerate(questions):
            with st.container():
                st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
                st.write(f"### Întrebarea {i+1}")
                
                # Cheie unică pentru sesiune
                show_key = f"show_{q['id']}_{user}"
                answered_key = f"ans_{q['id']}_{user}"
                
                if show_key not in st.session_state:
                    st.markdown('<p class="blur-text">Această întrebare este secretă până apeși butonul de mai jos.</p>', unsafe_allow_html=True)
                    if st.button("Afișează întrebarea", key=f"btn_{q['id']}"):
                        st.session_state[show_key] = True
                        st.rerun()
                
                elif show_key in st.session_state and answered_key not in st.session_state:
                    # Timer de 10 secunde
                    timer_placeholder = st.empty()
                    for seconds in range(10, -1, -1):
                        timer_placeholder.markdown(f'<p class="timer-text">⏱️ {seconds} secunde</p>', unsafe_allow_html=True)
                        time.sleep(1)
                        if seconds == 0:
                            st.error("Timpul a expirat!")
                            st.session_state[answered_key] = "Gresit"
                            # Aici se salvează automat în GSheets prin conn.update()
                    
                    st.write(q['question'])
                    ans = st.radio("Alege răspunsul:", [q['a'], q['b'], q['c'], q['d']], key=f"rad_{q['id']}")
                    if st.button("Trimite Răspuns", key=f"submit_{q['id']}"):
                        st.session_state[answered_key] = ans
                        st.success(f"Răspuns salvat!")
                
                else:
                    st.info(f"Ai răspuns la această întrebare.")
                st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("🏆 Top Performeri")
    # Logica de clasament preluată din tab-ul Responses
    res_df = conn.read(worksheet="Responses")
    ranking = res_df.groupby('username').agg(
        Total=('question_id', 'count'),
        Corecte=('is_correct', 'sum')
    ).sort_values(by='Corecte', ascending=False)
    st.table(ranking)