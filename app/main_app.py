import streamlit as st
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title='Grand Azure — Adaptive Hotel Pricing',
    page_icon='🏨', layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lato:wght@300;400;700&display=swap');
html,body,[class*="css"]{ font-family:'Lato',sans-serif; }
.stApp{ background:linear-gradient(135deg,#0d1117 0%,#0f1b2d 50%,#0d1117 100%); color:#e0e0e0; }
.stButton>button{
  background:linear-gradient(135deg,#FFD700,#FFA500)!important;
  color:#000!important;font-weight:700!important;border:none!important;
  border-radius:8px!important;transition:all .3s!important;
}
.stButton>button:hover{ transform:translateY(-2px)!important;
  box-shadow:0 8px 20px rgba(255,215,0,.3)!important; }
.stSidebar{ background:linear-gradient(180deg,#0f1b2d,#1a2744)!important;
  border-right:1px solid rgba(255,215,0,.15)!important; }
.stSidebar .stMarkdown,.stSidebar label,.stSidebar p{ color:#e0e0e0!important; }
.stMetric{ background:rgba(255,215,0,.05)!important;
  border:1px solid rgba(255,215,0,.2)!important;border-radius:10px!important;padding:1rem!important; }
hr{ border-color:rgba(255,215,0,.2)!important; }
.stSuccess{ background:rgba(76,175,80,.15)!important;border:1px solid #4CAF50!important; }
.stInfo{ background:rgba(0,188,212,.15)!important;border:1px solid #00BCD4!important; }
</style>""", unsafe_allow_html=True)


@st.cache_resource(show_spinner='🔄 Initialising AI pricing models…')
def _init_models():
    from core.model_training import load_or_train_models
    return load_or_train_models()


def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        from app.login_page import show_login_page
        show_login_page()
        return

    role     = st.session_state.get('role', 'customer')
    username = st.session_state.get('username', 'Guest')

    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:1rem 0 .5rem">
          <div style="font-size:2.5rem">🏨</div>
          <div style="font-family:'Playfair Display',serif;font-size:1.4rem;
                      color:#FFD700;font-weight:700">Grand Azure</div>
        </div>""", unsafe_allow_html=True)

        role_icon = '🛎️' if role == 'customer' else '📊'
        st.markdown(
            f'<div style="text-align:center;color:#aaa;font-size:.85rem;margin-bottom:.5rem">'
            f'{role_icon} Logged in as <b style="color:#FFD700">{username}</b></div>',
            unsafe_allow_html=True
        )
        if st.button('🚪 Logout', use_container_width=True):
            for key in ['logged_in','role','username']:
                st.session_state.pop(key, None)
            st.rerun()
        st.markdown('---')

    pm, om = _init_models()

    if role == 'manager':
        from app.manager_dashboard import show_manager_dashboard
        show_manager_dashboard(pm, om)
    else:
        from app.customer_interface import show_customer_interface
        show_customer_interface(pm, om)


if __name__ == '__main__':
    main()
