import pandas as pd

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['stay_length'] = df['stays_in_week_nights'] + df['stays_in_weekend_nights']
    df['number_of_guests'] = df['adults'] + df['children'] + df['babies']
    df['cancellation_risk'] = df['previous_cancellations'] / (df['previous_bookings_not_canceled'] + 1)
    return df

NUMERIC_FEATURES = [
    'lead_time','arrival_month','arrival_week_number',
    'stays_in_week_nights','stays_in_weekend_nights',
    'previous_cancellations','previous_bookings_not_canceled',
    'adults','children','babies',
    'stay_length','number_of_guests','cancellation_risk'
]
CATEGORICAL_FEATURES = ['hotel','room_type']
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
