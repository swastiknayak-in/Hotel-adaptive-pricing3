import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.pricing_engine import ROOM_BASE_PRICES, build_feature_row, forecast_revenue
from core.demand_engine  import compute_demand_score, apply_dynamic_pricing

# ─────────────────────────────────────────────────────────────────────────────
#  DATA LOADING — bulletproof, never crashes
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = {
    'customer_name' : 'Guest',
    'room_type'     : 'Standard',
    'stay_length'   : 2,
    'guests'        : 2,
    'predicted_price': 5000,
    'final_price'   : 5000,
    'booking_date'  : '2024-01-01',
    'arrival_month' : 6,
    'lead_time'     : 30,
}

def _demo_bookings(n: int = 300) -> pd.DataFrame:
    np.random.seed(42)
    months = np.random.randint(1, 13, n)
    rooms  = np.random.choice(list(ROOM_BASE_PRICES), n, p=[.35,.30,.15,.20])
    prices = np.clip(
        np.array([ROOM_BASE_PRICES[r] for r in rooms], float) + np.random.normal(0, 500, n),
        1000, 15000
    )
    dates = pd.date_range('2024-01-01', periods=n, freq='D')
    stay  = np.random.randint(1, 10, n)
    fp    = (prices * np.random.uniform(.85, 1.0, n)).round(0)
    return pd.DataFrame({
        'customer_name' : [f'Demo_Guest_{i}' for i in range(n)],
        'room_type'     : rooms,
        'stay_length'   : stay,
        'guests'        : np.random.randint(1, 6, n),
        'predicted_price': prices.round(0),
        'final_price'   : fp,
        'revenue'       : fp * stay,
        'booking_date'  : dates.strftime('%Y-%m-%d'),
        'arrival_month' : months,
        'lead_time'     : np.random.randint(0, 200, n),
        'source'        : 'demo',
    })

def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'arrival_month' not in df.columns:
        try:
            df['arrival_month'] = (
                pd.to_datetime(df['booking_date'], errors='coerce')
                  .dt.month.fillna(6).astype(int)
            )
        except Exception:
            df['arrival_month'] = 6
    for col, default in REQUIRED_COLUMNS.items():
        if col not in df.columns:
            df[col] = default
    for col in ['arrival_month','lead_time','stay_length','guests']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(REQUIRED_COLUMNS[col]).astype(int)
    for col in ['final_price','predicted_price']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(5000).astype(float)
    if 'revenue' not in df.columns:
        df['revenue'] = df['final_price'] * df['stay_length']
    df['source'] = 'real'
    return df

def load_bookings():
    """Returns (real_df, combined_df). real_df has only actual customer bookings."""
    path    = 'storage/bookings.csv'
    real_df = pd.DataFrame()

    if os.path.exists(path):
        try:
            raw = pd.read_csv(path)
            # filter out old demo rows that may have been saved accidentally
            if not raw.empty:
                raw = raw[~raw.get('customer_name', pd.Series(dtype=str))
                              .astype(str).str.startswith('Demo_Guest_', na=False)]
            if not raw.empty:
                real_df = _ensure_columns(raw)
        except Exception:
            real_df = pd.DataFrame()

    demo = _demo_bookings()
    combined = pd.concat([real_df, demo], ignore_index=True) if not real_df.empty else demo
    combined['revenue'] = combined['final_price'] * combined['stay_length']
    return real_df, combined


# ─────────────────────────────────────────────────────────────────────────────
#  KPI CARD
# ─────────────────────────────────────────────────────────────────────────────

def _kpi(label, value, sub=None, icon='📊', highlight=False):
    border = 'rgba(76,175,80,.5)' if highlight else 'rgba(255,215,0,.2)'
    subhtml = f'<div style="color:#4CAF50;font-size:.82rem;margin-top:.1rem">{sub}</div>' if sub else ''
    return f"""
    <div style="background:linear-gradient(135deg,#1a1f35,#252b45);
                border:1px solid {border};border-radius:12px;
                padding:1.2rem;text-align:center">
      <div style="font-size:1.8rem">{icon}</div>
      <div style="color:#aaa;font-size:.78rem;letter-spacing:2px;text-transform:uppercase">{label}</div>
      <div style="color:#FFD700;font-size:1.75rem;font-weight:700;margin:.3rem 0">{value}</div>
      {subhtml}
    </div>"""


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def show_manager_dashboard(pricing_model, occupancy_model):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lato:wght@300;400;700&display=swap');
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:1.5rem">
      <h1 style="font-family:'Playfair Display',serif;color:#FFD700;margin:0">
        📊 Revenue Command Center</h1>
      <p style="color:#aaa;letter-spacing:2px;font-size:.85rem;text-transform:uppercase;margin:0">
        Grand Azure — Manager Analytics Dashboard</p>
    </div>""", unsafe_allow_html=True)

    # ── Load data ─────────────────────────────────────────────────────────────
    real_df, df = load_bookings()
    has_real    = not real_df.empty

    # ── Refresh button ────────────────────────────────────────────────────────
    col_r, col_info = st.columns([1, 4])
    with col_r:
        if st.button('🔄 Refresh Data', use_container_width=True):
            st.rerun()
    with col_info:
        if has_real:
            st.success(f'✅ **{len(real_df)} real booking(s)** loaded from Guest Portal '
                       f'+ {len(df)-len(real_df)} demo records for chart context.')
        else:
            st.info('ℹ️ No real bookings yet. Showing demo data. '
                    'When guests book rooms, stats will update here automatically.')

    st.markdown('---')

    # ── KPI Row: Real bookings first, then combined ────────────────────────────
    if has_real:
        st.markdown('#### 🏆 Live Booking Stats (Real Guest Bookings)')
        r_rev   = real_df['revenue'].sum() if 'revenue' in real_df.columns else (real_df['final_price'] * real_df['stay_length']).sum()
        r_books = len(real_df)
        r_guests= real_df['guests'].sum()
        r_avg   = real_df['final_price'].mean()

        c1, c2, c3, c4 = st.columns(4)
        for col, args in zip([c1,c2,c3,c4],[
            ('Real Revenue',    f'₹{r_rev:,.0f}',     '✅ From real bookings', '💰', True),
            ('Real Bookings',   f'{r_books}',          '✅ Actual guests',       '📅', True),
            ('Total Guests',    f'{r_guests}',         '✅ People booked',       '👥', True),
            ('Avg. Room Rate',  f'₹{r_avg:,.0f}',      None,                    '🏷️', False),
        ]):
            with col:
                st.markdown(_kpi(*args), unsafe_allow_html=True)

        st.markdown('<div style="margin:.8rem 0"></div>', unsafe_allow_html=True)

    st.markdown('#### 📈 Combined Analytics (Real + Demo Data)')
    total_rev     = df['revenue'].sum()
    total_bookings= len(df)
    avg_price     = df['final_price'].mean()
    avg_stay      = df['stay_length'].mean()

    c1, c2, c3, c4 = st.columns(4)
    for col, args in zip([c1,c2,c3,c4],[
        ('Total Revenue',   f'₹{total_rev/1e6:.2f}M', None, '💰', False),
        ('Total Bookings',  f'{total_bookings:,}',     None, '📅', False),
        ('Avg. Room Rate',  f'₹{avg_price:,.0f}',      None, '🏷️', False),
        ('Avg. Stay',       f'{avg_stay:.1f} nights',  None, '🌙', False),
    ]):
        with col:
            st.markdown(_kpi(*args), unsafe_allow_html=True)

    st.markdown('---')

    # ── Charts ────────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('#### 📅 Booking Demand by Month')
        MONTH_NAMES = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                       7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
        monthly = df.groupby('arrival_month').size().reset_index(name='bookings')
        monthly['month'] = monthly['arrival_month'].map(MONTH_NAMES)
        fig = px.bar(monthly, x='month', y='bookings',
                     color='bookings', color_continuous_scale='YlOrRd',
                     template='plotly_dark')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          coloraxis_showscale=False, margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('#### 💰 Revenue by Room Type')
        room_rev = df.groupby('room_type')['revenue'].sum().reset_index()
        fig = px.pie(room_rev, names='room_type', values='revenue', hole=.4,
                     color_discrete_sequence=['#FFD700','#FF9800','#00BCD4','#4CAF50'],
                     template='plotly_dark')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown('#### 📈 Revenue Trend')
        df2 = df.copy()
        df2['booking_dt'] = pd.to_datetime(df2['booking_date'], errors='coerce')
        df2 = df2.dropna(subset=['booking_dt']).sort_values('booking_dt')
        df2['week'] = df2['booking_dt'].dt.to_period('W').astype(str)
        weekly = df2.groupby('week')['revenue'].sum().reset_index()
        fig = go.Figure(go.Scatter(
            x=weekly['week'], y=weekly['revenue'],
            fill='tozeroy', line=dict(color='#FFD700', width=2),
            fillcolor='rgba(255,215,0,.1)'
        ))
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(0,0,0,0)',
                          xaxis=dict(showticklabels=False),
                          margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown('#### ⏳ Lead Time Distribution')
        fig = px.histogram(df, x='lead_time', nbins=30,
                           color_discrete_sequence=['#00BCD4'], template='plotly_dark')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('#### 🏆 Room Popularity & Avg. Revenue')
    room_stats = (df.groupby('room_type')
                    .agg(bookings=('room_type','count'), avg_rev=('revenue','mean'))
                    .reset_index())
    fig = make_subplots(specs=[[{'secondary_y':True}]])
    fig.add_trace(go.Bar(x=room_stats['room_type'], y=room_stats['bookings'],
                          name='Bookings', marker_color='#FFD700'), secondary_y=False)
    fig.add_trace(go.Scatter(x=room_stats['room_type'], y=room_stats['avg_rev'],
                              name='Avg Revenue', line=dict(color='#00BCD4', width=3),
                              mode='lines+markers'), secondary_y=True)
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20,b=20,l=20,r=20))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('#### 👥 Guest Segmentation')
    df['segment'] = pd.cut(df['guests'], bins=[0,1,2,4,10],
                           labels=['Solo','Couple','Small Group','Family'])
    seg = df.groupby('segment', observed=True).size().reset_index(name='count')
    fig = px.bar(seg, x='segment', y='count', color='segment',
                 color_discrete_sequence=['#4CAF50','#FFD700','#FF9800','#00BCD4'],
                 template='plotly_dark')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      showlegend=False, margin=dict(t=20,b=20,l=20,r=20))
    st.plotly_chart(fig, use_container_width=True)

    # ── Recent real bookings table ────────────────────────────────────────────
    if has_real:
        st.markdown('---')
        st.markdown('#### 📋 Recent Guest Bookings (Live)')
        display_cols = ['customer_name','room_type','stay_length','guests',
                        'final_price','revenue','booking_date','arrival_month']
        show_cols = [c for c in display_cols if c in real_df.columns]
        show_df = real_df[show_cols].sort_values('booking_date', ascending=False).head(20)
        show_df.columns = [c.replace('_',' ').title() for c in show_df.columns]
        st.dataframe(show_df, use_container_width=True)

    # ── Pricing Simulator ─────────────────────────────────────────────────────
    st.markdown('---')
    st.markdown('## 🎛️ Pricing Simulator')

    s1, s2 = st.columns(2)
    with s1:
        sim_room  = st.selectbox('Room Type', list(ROOM_BASE_PRICES))
        sim_stay  = st.slider('Stay Duration (nights)', 1, 14, 3)
        sim_rooms = st.slider('Rooms Available', 1, 50, 10)
    with s2:
        sim_guests = st.number_input('Expected Guests/Room', 1, 5, 2)
        sim_lead   = st.slider('Lead Time (days)', 0, 365, 30)
        sim_month  = st.selectbox(
            'Arrival Month', list(range(1,13)),
            format_func=lambda m: datetime(2024,m,1).strftime('%B'),
            index=5, key='sim_month'
        )

    if st.button('🔮 Simulate Pricing', type='primary', use_container_width=True):
        try:
            row = build_feature_row(sim_room, sim_lead, sim_month, sim_stay,
                                     sim_guests, sim_guests, 0, 0)
            predicted = float(pricing_model.predict(row)[0])
            predicted = max(ROOM_BASE_PRICES[sim_room] * .7, predicted)
            occ       = float(np.clip(occupancy_model.predict(row)[0], .3, 1.0))
            demand    = compute_demand_score(sim_lead, sim_month, sim_room)
            pricing   = apply_dynamic_pricing(predicted, demand)
            revenue   = forecast_revenue(pricing['final_dynamic_price'], sim_rooms, occ)

            r1,r2,r3,r4 = st.columns(4)
            r1.metric('Recommended Price', f"₹{pricing['final_dynamic_price']:,.0f}")
            r2.metric('Price Floor',       f"₹{pricing['price_floor']:,.0f}")
            r3.metric('Price Ceiling',     f"₹{pricing['price_ceiling']:,.0f}")
            r4.metric('Expected Revenue',  f"₹{revenue:,.0f}")
            st.info(f"📊 **Demand Score:** {demand:.3f} | **Predicted Occupancy:** {occ:.1%}")

            fig = go.Figure(go.Indicator(
                mode='gauge+number', value=demand*100,
                title={'text':'Demand Score','font':{'color':'#FFD700'}},
                number={'suffix':'%','font':{'color':'#FFD700'}},
                gauge={'axis':{'range':[0,100]},'bar':{'color':'#FFD700'},
                       'steps':[{'range':[0,33],'color':'#1a3c4e'},
                                 {'range':[33,66],'color':'#1a4a2e'},
                                 {'range':[66,100],'color':'#4a2e1a'}]}
            ))
            fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                              height=280, margin=dict(t=30,b=10,l=40,r=40))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f'Simulation error: {e}')
