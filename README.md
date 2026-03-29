# 🏨 Grand Azure — Hotel Adaptive Pricing & Revenue Management

A full-stack AI-powered hotel pricing and revenue management system built with **Python**, **Scikit-learn**, **Streamlit**, and **Plotly**.

---

## ✨ Features

### 🛎️ Customer Portal
- View all room types with **AI-predicted dynamic prices**
- Smart room recommendations based on guests, stay length & travel type
- Automatic discounts — advance booking, long stay, loyal guest
- ₹500 coupon for bookings over ₹5,000
- Bookings saved to CSV with all fields

### 📊 Manager Dashboard
- **KPI cards** — total revenue, bookings, avg rate, avg stay
- Booking demand by month (bar chart)
- Revenue by room type (donut chart)
- Revenue trend over time (area chart)
- Lead time distribution (histogram)
- Room popularity vs avg revenue (dual-axis)
- Guest segmentation by group size
- **Interactive pricing simulator** with demand gauge

---

## 🤖 Machine Learning Models

| Model | Algorithm | Target | RMSE |
|-------|-----------|--------|------|
| Pricing | RandomForestRegressor (120 trees, depth=12) | `adr` (avg daily rate) | ~₹267 |
| Occupancy | GradientBoostingRegressor (100 trees) | `occupancy_rate` | ~0.08 |

### Auto-Training Architecture
Models are **not stored in Git** (18MB — too large). They train automatically on first run:

```python
if not os.path.exists("models/pricing_model.pkl"):
    train_models()   # ~30 seconds on Streamlit Cloud
```

---

## 📁 Project Structure

```
hotel/
├── data/
│   └── hotel_bookings.csv        # 5,000 synthetic training records
├── models/
│   └── (auto-generated .pkl)     # Excluded from Git via .gitignore
├── core/
│   ├── feature_engineering.py    # Derived features + column lists
│   ├── model_training.py         # Train & save both ML models
│   ├── pricing_engine.py         # Room catalog, discounts, forecasting
│   └── demand_engine.py          # Demand score + dynamic pricing formula
├── app/
│   ├── main_app.py               # ← Streamlit entry point
│   ├── login_page.py             # Role selector (Customer / Manager)
│   ├── customer_interface.py     # Room cards + booking flow
│   └── manager_dashboard.py      # Analytics + pricing simulator
├── storage/
│   └── bookings.csv              # Written at runtime (not in Git)
├── assets/
│   └── room_images/              # SVG room illustrations
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🛠️ Local Setup

```bash
git clone https://github.com/YOUR_USERNAME/hotel-adaptive-pricing
cd hotel-adaptive-pricing
pip install -r requirements.txt
streamlit run app/main_app.py
```

Models train automatically on first launch (~30 seconds).

---

## ☁️ Deploy on Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select your repository
5. Set **Main file path**: `app/main_app.py`
6. Click **Deploy** ✅

> Models re-train on first Streamlit Cloud boot (~30 sec). All subsequent loads use the cached models.

---

## 💰 Dynamic Pricing Formula

```
demand_score  = (0.4 × lead_time_factor) + (0.3 × month_factor) + (0.3 × room_demand_factor)
dynamic_price = predicted_price × (1 + demand_score)
final_price   = clamp(dynamic_price,  predicted × 0.85,  predicted × 1.40)
```

## 🏷️ Discount Rules

| Condition | Discount |
|-----------|----------|
| Lead time > 60 days | 10% off |
| Stay ≥ 5 nights | 8% off |
| Returning guest | 5% off |
| Total > ₹5,000 | ₹500 coupon |
| Minimum floor | 80% of predicted |

---

## 📦 Tech Stack

```
streamlit    — web UI
pandas       — data processing
numpy        — numerical operations
scikit-learn — ML models (RandomForest + GradientBoosting)
plotly       — interactive charts
joblib       — model serialisation
```
