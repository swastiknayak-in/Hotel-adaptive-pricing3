import streamlit as st

# ── Credential store ─────────────────────────────────────────────────────────
USERS = {
    'user1'    : ('password1', 'customer'),
    'user2'    : ('password2', 'customer'),
    'manager1' : ('password1', 'manager'),
    'manager2' : ('password2', 'manager'),
}

def show_login_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lato:wght@300;400&display=swap');
    .cred-box{background:rgba(255,215,0,.07);border:1px solid rgba(255,215,0,.2);
              border-radius:10px;padding:.9rem 1.2rem;margin-top:.8rem}
    .cred-title{color:#FFD700;font-size:.8rem;letter-spacing:2px;
                text-transform:uppercase;font-weight:700;margin-bottom:.5rem}
    .cred-item{font-family:monospace;font-size:.82rem;color:#ccc;
               background:rgba(255,255,255,.06);border-radius:6px;
               padding:3px 10px;margin:3px 0;display:block}
    .cred-label{color:#aaa;font-size:.75rem;margin-bottom:.3rem;margin-top:.1rem}
    </style>""", unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("""
        <div style="text-align:center;padding:2rem 0 1rem">
          <div style="font-size:4rem">🏨</div>
          <div style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;
                      background:linear-gradient(135deg,#FFD700,#FFA500);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                      background-clip:text">Grand Azure</div>
          <div style="font-family:'Lato',sans-serif;color:#888;letter-spacing:4px;
                      font-size:.85rem;margin-top:.3rem;text-transform:uppercase">
            Adaptive Pricing &amp; Revenue Management</div>
          <hr style="border:1px solid rgba(255,215,0,.3);margin:1.5rem 0">
        </div>""", unsafe_allow_html=True)

        st.markdown('### 🔐 Sign In')
        username = st.text_input('👤 Username', placeholder='e.g. user1 or manager1')
        password = st.text_input('🔑 Password', type='password', placeholder='Enter password')

        if st.button('✨ Enter Portal', use_container_width=True, type='primary'):
            if username in USERS and USERS[username][0] == password:
                st.session_state['role']      = USERS[username][1]
                st.session_state['logged_in'] = True
                st.session_state['username']  = username
                st.rerun()
            else:
                st.error('❌ Invalid username or password. Use the demo credentials below.')

        # ── Demo credentials panel ──────────────────────────────
        st.markdown("""
        <div class="cred-box">
          <div class="cred-title">📋 Demo Login Credentials</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:.4rem">
            <div>
              <div class="cred-label">🛎️ Guest Login</div>
              <span class="cred-item">user1 / password1</span>
              <span class="cred-item">user2 / password2</span>
            </div>
            <div>
              <div class="cred-label">📊 Manager Login</div>
              <span class="cred-item">manager1 / password1</span>
              <span class="cred-item">manager2 / password2</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
