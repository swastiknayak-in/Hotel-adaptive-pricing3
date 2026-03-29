import pandas as pd
from core.feature_engineering import engineer_features

ROOM_BASE_PRICES = {'Standard':3500,'Deluxe':5200,'Suite':8200,'Family':7000}
ROOM_CAPACITIES  = {'Standard':2,'Deluxe':3,'Suite':4,'Family':5}
ROOM_AMENITIES   = {
    'Standard':['WiFi','Breakfast','AC'],
    'Deluxe'  :['WiFi','Breakfast','Balcony','Mini Bar'],
    'Suite'   :['WiFi','Breakfast','Balcony','Jacuzzi','Butler'],
    'Family'  :['WiFi','Breakfast','Living Area','Kitchen','Kids Zone']
}

def build_feature_row(room_type, lead_time, month, stay_length,
                       guests, adults, children, babies,
                       hotel='City Hotel', week_number=25,
                       prev_cancel=0, prev_not_cancel=0) -> pd.DataFrame:
    wn = max(0, stay_length - min(stay_length, 2))
    we = stay_length - wn
    row = pd.DataFrame([{
        'hotel':hotel,'lead_time':lead_time,'arrival_month':month,
        'arrival_week_number':week_number,'stays_in_week_nights':wn,
        'stays_in_weekend_nights':we,'adults':adults,'children':children,
        'babies':babies,'room_type':room_type,
        'previous_cancellations':prev_cancel,
        'previous_bookings_not_canceled':prev_not_cancel
    }])
    return engineer_features(row)

def apply_discounts(price:float, lead_time:int, stay_length:int,
                    is_repeat:bool=False) -> dict:
    discounts, total = [], 0.0
    if lead_time > 60:
        discounts.append(('Advance Booking >60 days', .10)); total += .10
    if stay_length >= 5:
        discounts.append(('Long Stay ≥5 nights', .08));      total += .08
    if is_repeat:
        discounts.append(('Loyal Guest', .05));               total += .05
    disc_price = price * (1 - total)
    coupon     = 500 if disc_price > 5000 else 0
    final      = max(disc_price - coupon, price * .80)
    return {'original_price':round(price,2),'discounts':discounts,
            'discount_pct':total,'discounted_price':round(disc_price,2),
            'coupon_applied':coupon,'final_price':round(final,2)}

def forecast_revenue(price:float, rooms:int, occ:float) -> float:
    return round(price * rooms * occ, 2)
