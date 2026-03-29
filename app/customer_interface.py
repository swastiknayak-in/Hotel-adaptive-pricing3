import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.pricing_engine import (ROOM_BASE_PRICES, ROOM_CAPACITIES, ROOM_AMENITIES,
                                   build_feature_row, apply_discounts)
from core.demand_engine  import compute_demand_score, apply_dynamic_pricing, recommend_room

ROOM_EMOJIS = {'Standard':'🛏️','Deluxe':'🌟','Suite':'👑','Family':'👨‍👩‍👧‍👦'}
ROOM_DESC   = {
    'Standard':'Comfortable and cozy. Perfect for solo travelers or couples.',
    'Deluxe'  :'Private balcony with beautiful city/sunset views.',
    'Suite'   :'Jacuzzi, butler service, and panoramic night skyline.',
    'Family'  :'Bunk beds, garden view, dedicated living area & sofa.',
}
ROOM_IMAGES = {
    'Standard':'assets/room_images/standard.svg',
    'Deluxe'  :'assets/room_images/deluxe.svg',
    'Suite'   :'assets/room_images/suite.svg',
    'Family'  :'assets/room_images/family.svg',
}
MONTH_NAMES = ['January','February','March','April','May','June',
               'July','August','September','October','November','December']


def show_customer_interface(pricing_model, occupancy_model):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lato:wght@300;400;700&display=swap');
    .room-card{background:linear-gradient(135deg,rgba(255,255,255,.05),rgba(255,255,255,.02));
               border:1px solid rgba(255,215,0,.2);border-radius:16px;padding:1.5rem;margin:.5rem 0}
    .room-title{font-family:'Playfair Display',serif;font-size:1.4rem;color:#FFD700}
    .price-tag{font-size:1.8rem;font-weight:700;color:#4CAF50}
    .chip{display:inline-block;background:rgba(255,215,0,.15);color:#FFD700;
          border-radius:20px;padding:2px 12px;font-size:.75rem;margin:2px}
    .disc-card{background:linear-gradient(135deg,rgba(76,175,80,.12),rgba(76,175,80,.05));
               border:1px solid rgba(76,175,80,.35);border-radius:12px;
               padding:1rem 1.2rem;margin:.6rem 0}
    .disc-row{display:flex;justify-content:space-between;align-items:center;
              padding:3px 0;font-size:.88rem}
    .disc-strike{text-decoration:line-through;color:#888}
    .disc-final{font-size:1.2rem;font-weight:700;color:#4CAF50}
    .disc-badge{background:rgba(255,152,0,.2);color:#FF9800;border-radius:20px;
                padding:2px 10px;font-size:.75rem;font-weight:700}
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:1rem">
      <h1 style="font-family:'Playfair Display',serif;color:#FFD700;margin:0">🏨 Grand Azure Hotel</h1>
      <p style="color:#aaa;letter-spacing:2px;font-size:.85rem;text-transform:uppercase;margin:0">
        Adaptive Pricing — Best Rates Guaranteed</p>
    </div>""", unsafe_allow_html=True)

    # ── Sidebar: all inputs as dropdowns/sliders/checkboxes ──────────────────
    with st.sidebar:
        st.markdown('## 🗓️ Your Stay Details')
        st.markdown('---')

        name = st.text_input('👤 Guest Name', value=st.session_state.get('username','Guest').capitalize())

        st.markdown('**👥 Number of Guests**')
        adults   = st.selectbox('🧑 Adults',   options=list(range(1, 5)), index=1)
        children = st.selectbox('👧 Children', options=list(range(0, 4)), index=0)
        babies   = st.selectbox('🍼 Babies',   options=list(range(0, 3)), index=0)
        guests   = adults + children + babies

        st.markdown(f'<div style="color:#FFD700;font-size:.85rem;margin:.3rem 0">'
                    f'👥 Total guests: <b>{guests}</b></div>', unsafe_allow_html=True)
        st.markdown('---')

        st.markdown('**🌙 Stay Duration**')
        stay = st.slider('Nights', min_value=1, max_value=30, value=3,
                         help='How many nights will you stay?')
        st.markdown(f'<div style="color:#aaa;font-size:.8rem">'
                    f'🗓️ {stay} night{"s" if stay>1 else ""}</div>', unsafe_allow_html=True)
        st.markdown('---')

        st.markdown('**📅 Arrival Details**')
        month_name = st.selectbox('📆 Arrival Month', MONTH_NAMES, index=5)
        month      = MONTH_NAMES.index(month_name) + 1
        lead       = st.slider('⏰ Days until Check-in', min_value=0, max_value=365, value=30,
                               help='How far in advance are you booking?')
        st.markdown('---')

        st.markdown('**🎒 Travel Preferences**')
        traveler  = st.selectbox('✈️ Traveler Type',
                                  ['🏖️ Leisure', '💼 Business', '👨‍👩‍👧 Family'],
                                  index=0)
        traveler_key = traveler.split(' ')[1].lower()  # leisure/business/family
        is_rep    = st.checkbox('⭐ Returning Guest  (get 5% loyalty discount)')
        st.markdown('---')

        # Live recommendation
        rec = recommend_room(guests, stay, traveler_key)
        st.markdown(f"""
        <div style="background:rgba(255,215,0,.1);border:1px solid rgba(255,215,0,.3);
                    border-radius:10px;padding:.8rem;text-align:center">
          <div style="color:#FFD700;font-size:.8rem;letter-spacing:1px;text-transform:uppercase">
            💡 AI Recommendation</div>
          <div style="color:white;font-size:1rem;font-weight:700;margin-top:.3rem">{rec}</div>
        </div>""", unsafe_allow_html=True)

    # ── Pre-compute prices for ALL rooms based on sidebar inputs ─────────────
    room_prices = {}
    for room, base in ROOM_BASE_PRICES.items():
        try:
            row      = build_feature_row(room, lead, month, stay,
                                          guests, adults, children, babies)
            pred     = max(base * .7, float(pricing_model.predict(row)[0]))
            demand   = compute_demand_score(lead, month, room)
            dyn_info = apply_dynamic_pricing(pred, demand)
            disc_info= apply_discounts(dyn_info['final_dynamic_price'], lead, stay, is_rep)
            room_prices[room] = {
                'base'       : base,
                'predicted'  : pred,
                'dynamic'    : dyn_info['final_dynamic_price'],
                'final'      : disc_info['final_price'],
                'disc_info'  : disc_info,
                'demand'     : demand,
            }
        except Exception:
            room_prices[room] = {
                'base': base, 'predicted': base, 'dynamic': base,
                'final': base, 'demand': 0,
                'disc_info': {'discounts':[], 'final_price':base,
                              'coupon_applied':0, 'original_price':base,
                              'discount_pct':0, 'discounted_price':base},
            }

    # ── Global price summary banner ──────────────────────────────────────────
    rec_room  = rec.replace(' Room','').replace(' Suite','')
    # find closest match
    matched = next((r for r in ROOM_BASE_PRICES if rec_room.lower() in r.lower()), 'Standard')
    rp      = room_prices[matched]
    saving  = rp['base'] - rp['final']
    pct_off = (saving / rp['base'] * 100) if saving > 0 else 0

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(255,215,0,.1),rgba(255,165,0,.05));
                border:1px solid rgba(255,215,0,.3);border-radius:14px;
                padding:1rem 1.5rem;margin-bottom:1.2rem;
                display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem">
      <div>
        <div style="color:#FFD700;font-size:.8rem;letter-spacing:2px;text-transform:uppercase">
          ✨ Best Rate for Your Selection</div>
        <div style="color:white;font-size:1.5rem;font-weight:700;margin-top:.2rem">
          {stay} nights · {guests} guest{'s' if guests>1 else ''} · {month_name}</div>
      </div>
      <div style="text-align:right">
        <div style="color:#aaa;font-size:.85rem">Recommended: <b style="color:#FFD700">{matched} Room</b></div>
        <div style="color:#4CAF50;font-size:1.6rem;font-weight:700">₹{rp['final']:,.0f}<span style="font-size:.9rem;color:#aaa">/night</span></div>
        {"<div style='color:#FF9800;font-size:.82rem'>🏷️ Save ₹"+f"{saving:,.0f} ({pct_off:.0f}% off)</div>" if pct_off > 0 else ""}
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Room cards ───────────────────────────────────────────────────────────
    st.markdown('### 🛏️ Available Rooms')
    cols = st.columns(2)

    for idx, (room, base) in enumerate(ROOM_BASE_PRICES.items()):
        rp        = room_prices[room]
        disc_info = rp['disc_info']
        price     = rp['final']
        orig      = rp['base']

        with cols[idx % 2]:
            # Room image
            img = ROOM_IMAGES.get(room, '')
            if img and os.path.exists(img):
                st.image(img, use_container_width=True)

            # Room info card
            amenities_html = ''.join(f'<span class="chip">{a}</span>'
                                     for a in ROOM_AMENITIES[room])
            st.markdown(f"""
            <div class="room-card">
              <div style="font-size:2rem">{ROOM_EMOJIS[room]}</div>
              <div class="room-title">{room} Room</div>
              <div style="color:#aaa;font-size:.85rem;margin:.3rem 0">{ROOM_DESC[room]}</div>
              <div style="margin:.2rem 0">👥 Capacity: <b>{ROOM_CAPACITIES[room]} guests</b></div>
              <div style="margin:.5rem 0">{amenities_html}</div>
              <div class="price-tag">₹{price:,.0f}<span style="font-size:.9rem;color:#aaa">/night</span></div>
              <div style="color:#aaa;font-size:.75rem">Base Rate: ₹{orig:,}</div>
            </div>""", unsafe_allow_html=True)

            # ── Discount card ────────────────────────────────────
            total_disc  = disc_info.get('discount_pct', 0)
            orig_price  = disc_info.get('original_price', orig)
            disc_price  = disc_info.get('discounted_price', price)
            coupon      = disc_info.get('coupon_applied', 0)
            discounts   = disc_info.get('discounts', [])

            if total_disc > 0 or coupon > 0:
                rows_html = ''
                for d_name, d_pct in discounts:
                    rows_html += f"""
                    <div class="disc-row">
                      <span>✅ {d_name}</span>
                      <span style="color:#4CAF50">-{int(d_pct*100)}%</span>
                    </div>"""
                if coupon:
                    rows_html += f"""
                    <div class="disc-row">
                      <span>🎟️ Loyalty Coupon</span>
                      <span style="color:#4CAF50">-₹{coupon:,}</span>
                    </div>"""
                saving_total = (orig_price - price) * stay
                st.markdown(f"""
                <div class="disc-card">
                  <div style="color:#4CAF50;font-size:.8rem;letter-spacing:1px;
                              text-transform:uppercase;font-weight:700;margin-bottom:.5rem">
                    🏷️ Your Discount Breakdown</div>
                  <div class="disc-row">
                    <span>Original price</span>
                    <span class="disc-strike">₹{orig_price:,.0f}/night</span>
                  </div>
                  {rows_html}
                  <hr style="border:1px solid rgba(76,175,80,.2);margin:.4rem 0">
                  <div class="disc-row">
                    <span style="font-weight:700">You pay</span>
                    <span class="disc-final">₹{price:,.0f}/night</span>
                  </div>
                  <div style="margin-top:.4rem">
                    <span class="disc-badge">
                      Save ₹{orig_price-price:,.0f}/night · ₹{saving_total:,.0f} total for {stay} nights
                    </span>
                  </div>
                </div>""", unsafe_allow_html=True)

            # ── Book button ──────────────────────────────────────
            total_cost = price * stay
            if st.button(f'📅 Book {room}  —  ₹{total_cost:,.0f} total',
                         key=f'book_{room}', use_container_width=True):
                _save_booking(name, room, stay, guests, orig, price, month, lead)
                st.success(f'✅ **{room} Room booked for {stay} nights!**  '
                           f'Total: **₹{total_cost:,.0f}**')
                st.balloons()


def _save_booking(name, room, stay, guests, predicted, final, month, lead):
    """Save booking to CSV with ALL columns dashboard needs."""
    os.makedirs('storage', exist_ok=True)
    row = pd.DataFrame([{
        'customer_name'  : name,
        'room_type'      : room,
        'stay_length'    : int(stay),
        'guests'         : int(guests),
        'predicted_price': float(predicted),
        'final_price'    : float(final),
        'revenue'        : float(final * stay),      # pre-compute for dashboard
        'booking_date'   : datetime.now().strftime('%Y-%m-%d %H:%M'),
        'arrival_month'  : int(month),
        'lead_time'      : int(lead),
    }])
    path = 'storage/bookings.csv'
    if os.path.exists(path):
        existing = pd.read_csv(path)
        row = pd.concat([existing, row], ignore_index=True)
    row.to_csv(path, index=False)
