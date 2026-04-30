# Backend Integration Code Snippets

Copy and paste these code snippets into `backend/main.py`

---

## Step 1: Add Import (Top of main.py)

Find this section:
```python
import joblib
import requests
import os
import re
import random
import pandas as pd
```

Add this line after:
```python
# ── LSTM Model ──
try:
    from lstm_inference import LSTMPricePredictor, build_trend_with_lstm
    LSTM_AVAILABLE = True
except ImportError:
    LSTM_AVAILABLE = False
    print("⚠️  LSTM module not available. Using RandomForest fallback.")
```

---

## Step 2: Initialize LSTM at Startup (Around line 45)

Find this section:
```python
app = FastAPI(title="JourneyIt AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────────────────────
model         = joblib.load("../ml_models/flight_price_model.pkl")
model_columns = joblib.load("../ml_models/model_columns.pkl")
```

Add this after the model loading:
```python
# ─────────────────────────────────────────────────────────
# LOAD LSTM MODEL (New)
# ─────────────────────────────────────────────────────────
lstm_predictor = None
if LSTM_AVAILABLE:
    try:
        lstm_predictor = LSTMPricePredictor(models_dir="../ml_models")
        if lstm_predictor.is_ready():
            print(f"✅ LSTM predictor loaded: {len(lstm_predictor.get_available_routes())} routes available")
        else:
            print("⚠️  LSTM predictor initialized but models not found. Using RandomForest fallback.")
            lstm_predictor = None
    except Exception as e:
        print(f"⚠️  Error loading LSTM: {e}. Using RandomForest fallback.")
        lstm_predictor = None
else:
    print("⚠️  TensorFlow not available. Using RandomForest fallback only.")
```

---

## Step 3: Replace _build_trend Function

### Option A: Keep both, add routing logic

Find the `_build_trend()` function definition (around line 410). Keep it but modify to use LSTM:

**Replace this:**
```python
def _build_trend(current_price: int, duration: float, days_left: int,
                 from_city: str = None, to_city: str = None,
                 airline: str = None, stops: int = 0) -> dict:
```

**With this:**
```python
def _build_trend(current_price: int, duration: float, days_left: int,
                 from_city: str = None, to_city: str = None,
                 from_iata: str = None, to_iata: str = None,
                 airline: str = None, stops: int = 0) -> dict:
    """
    Build 7-day trend using LSTM (if available) or RandomForest
    """
    # Try LSTM first
    if lstm_predictor and lstm_predictor.is_ready():
        try:
            return build_trend_with_lstm(
                current_price,
                duration,
                days_left,
                from_iata=from_iata or "DEL",
                to_iata=to_iata or "BOM",
                lstm_predictor=lstm_predictor
            )
        except Exception as e:
            print(f"⚠️  LSTM prediction failed: {e}. Falling back to RandomForest.")
    
    # Fallback to original RandomForest method
    return _build_trend_randomforest(current_price, duration, days_left, 
                                     from_city, to_city, airline, stops)


def _build_trend_randomforest(current_price: int, duration: float, days_left: int,
                              from_city: str = None, to_city: str = None,
                              airline: str = None, stops: int = 0) -> dict:
    """
    Original RandomForest-based trend (renamed for clarity)
    """
    # Original code stays here unchanged
```

---

## Step 4: Update Chat Endpoint

Find the chat endpoint function (around line 1130):

**Find this call:**
```python
trend = _build_trend(
    current_price, duration, data.days_left,
    from_city=from_city, to_city=to_city, stops=data.stops or 0,
)
```

**Replace with:**
```python
trend = _build_trend(
    current_price, duration, data.days_left,
    from_city=from_city, to_city=to_city,
    from_iata=from_iata, to_iata=to_iata,  # Add these
    stops=data.stops or 0,
)
```

---

## Step 5: Update Flight Search Endpoint

Find `search_flights` function (around line 1020):

**Add this near the beginning:**
```python
@app.post("/search-flights")
def search_flights(data: FlightSearch):
    from_city = IATA_TO_ML_CITY.get(data.from_iata, None)
    to_city   = IATA_TO_ML_CITY.get(data.to_iata,   None)
    base_dur  = _route_duration(data.from_iata, data.to_iata)

    # ... existing code ...
    
    # When building enriched flights list, use LSTM for trend:
    for i, tmpl in enumerate(pool):
        # ... existing code ...
        
        # Original line:
        # trend = _build_trend(...)
        
        # Replace with:
        trend_info = _build_trend(
            price, duration, days_left,
            from_city=from_city, to_city=to_city,
            from_iata=data.from_iata, to_iata=data.to_iata,
            airline=airline, stops=stops
        )
        
        # ... rest of code ...
```

---

## Step 6: Update Prediction Endpoint

Find `predict_price` function (around line 986):

**Modify the trend building:**
```python
@app.post("/predict-flight-price")
def predict_price(data: FlightRequest):
    from_city = IATA_TO_ML_CITY.get(data.from_iata or "", None)
    to_city   = IATA_TO_ML_CITY.get(data.to_iata   or "", None)

    if data.from_iata and data.to_iata:
        duration = _route_duration(data.from_iata, data.to_iata) or data.duration
    else:
        duration = data.duration

    current_price = int(_ml_predict(
        duration, data.days_left,
        airline=data.airline, from_city=from_city, to_city=to_city,
        stops=data.stops or 0, travel_class=data.travel_class or "Economy",
    ))

    # Use LSTM for trend
    trend = _build_trend(
        current_price, duration, data.days_left,
        from_city=from_city, to_city=to_city,
        from_iata=data.from_iata,  # Add this
        to_iata=data.to_iata,      # Add this
        stops=data.stops or 0,
    )

    return {
        "predicted_price": current_price,
        "future_prices":   trend["future_prices"],
        "change_pct":      trend["change_pct"],
        "recommendation":  trend["decision"],
        "confidence":      trend["confidence"],
        "advice":          trend["advice"],
        "trend":           trend["trend"],
        "method":          trend.get("method", "randomforest")  # Show which was used
    }
```

---

## Complete Code Block (Copy Directly)

If you want to copy the entire modified section, here's the complete integration:

```python
# ═══════════════════════════════════════════════════════════════════
# TOP OF FILE - Add imports
# ═══════════════════════════════════════════════════════════════════

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import date, timedelta, datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import joblib
import requests
import os
import re
import random
import pandas as pd

# Load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── optional Gemini LLM ──
try:
    from google import genai as _genai_sdk
    _GEMINI_PKG = True
except ImportError:
    _GEMINI_PKG = False

# ── LSTM Model (NEW) ──
try:
    from lstm_inference import LSTMPricePredictor, build_trend_with_lstm
    LSTM_AVAILABLE = True
except ImportError:
    LSTM_AVAILABLE = False
    print("⚠️  lstm_inference module not found. Using RandomForest only.")


# ═══════════════════════════════════════════════════════════════════
# MODEL INITIALIZATION - Add LSTM loading after FastAPI setup
# ═══════════════════════════════════════════════════════════════════

app = FastAPI(title="JourneyIt AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────
# LOAD MODELS
# ─────────────────────────────────────────────────────────
model         = joblib.load("../ml_models/flight_price_model.pkl")
model_columns = joblib.load("../ml_models/model_columns.pkl")

# Load LSTM Model (NEW)
lstm_predictor = None
if LSTM_AVAILABLE:
    try:
        lstm_predictor = LSTMPricePredictor(models_dir="../ml_models")
        if lstm_predictor.is_ready():
            num_routes = len(lstm_predictor.get_available_routes())
            print(f"✅ LSTM predictor loaded: {num_routes} routes available")
        else:
            print("⚠️  LSTM models not found. Using RandomForest fallback.")
            lstm_predictor = None
    except Exception as e:
        print(f"⚠️  Error loading LSTM: {e}")
        lstm_predictor = None


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS - Modify _build_trend
# ═══════════════════════════════════════════════════════════════════

def _build_trend(current_price: int, duration: float, days_left: int,
                 from_city: str = None, to_city: str = None,
                 from_iata: str = None, to_iata: str = None,
                 airline: str = None, stops: int = 0) -> dict:
    """
    Build 7-day trend using LSTM (if available) or RandomForest
    
    Now accepts from_iata/to_iata for LSTM route matching
    """
    # Try LSTM first
    if lstm_predictor and lstm_predictor.is_ready():
        try:
            return build_trend_with_lstm(
                current_price,
                duration,
                days_left,
                from_iata=from_iata or "DEL",
                to_iata=to_iata or "BOM",
                lstm_predictor=lstm_predictor
            )
        except Exception as e:
            print(f"⚠️  LSTM failed ({e}), using RandomForest")
    
    # Fallback to RandomForest method
    ml_day7 = int(_ml_predict(duration, max(1, days_left - 7),
                              airline=airline, from_city=from_city,
                              to_city=to_city, stops=stops))

    future_prices = [
        int(current_price + (ml_day7 - current_price) * (d / 7))
        for d in range(1, 8)
    ]

    day5_price  = future_prices[4]
    change_pct  = round(((day5_price - current_price) / current_price) * 100, 1)
    future_avg  = sum(future_prices) / len(future_prices)
    variance    = sum((p - future_avg) ** 2 for p in future_prices) / len(future_prices)
    confidence  = int(max(55, min(92, 85 - variance / 100_000)))

    if change_pct > 10:
        decision = "BOOK NOW"
    elif change_pct < -5:
        decision = "WAIT"
    else:
        decision = "MONITOR"

    if decision == "BOOK NOW":
        advice = (f"Prices rising {change_pct:.1f}% over 5 days — "
                  f"book now to avoid paying ₹{day5_price - current_price:,} more")
    elif decision == "WAIT":
        save = current_price - day5_price
        advice = (f"Prices expected to drop {abs(change_pct):.1f}% — "
                  f"waiting ~5 days could save you ₹{save:,}")
    else:
        advice = (f"Prices stable ({change_pct:+.1f}% over 5 days) — "
                  f"monitor for 2–3 days before committing")

    return {
        "future_prices": future_prices,
        "day5_price":    day5_price,
        "change_pct":    change_pct,
        "confidence":    confidence,
        "decision":      decision,
        "advice":        advice,
        "trend":         "increasing" if change_pct > 0 else "decreasing",
        "method":        "randomforest"  # For tracking
    }
```

---

## Testing After Integration

### Test 1: Backend starts with LSTM

When you run `uvicorn main:app --reload`, you should see:

```
✅ LSTM predictor loaded: 50 routes available
```

Or fallback message:

```
⚠️  LSTM models not found. Using RandomForest fallback.
```

### Test 2: Make API call

```bash
curl -X POST http://localhost:8000/predict-flight-price \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 2.5,
    "days_left": 7,
    "from_iata": "DEL",
    "to_iata": "BOM"
  }'
```

**Should include**: `"method": "lstm"` in response

### Test 3: Chat endpoint

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Should I book DEL to BOM?"}'
```

**Should show**: Non-linear 7-day price forecast

---

## Troubleshooting Integration Issues

### "NameError: name 'build_trend_with_lstm' is not defined"
- Make sure you added the import at the top
- Check that `lstm_inference.py` is in the same directory as `main.py`

### "ModuleNotFoundError: No module named 'tensorflow'"
- Run: `pip install tensorflow`
- Restart backend

### "LSTM models not found" warning
- Run: `python train_lstm_model.py`
- Check models were created: `ls ml_models/lstm_model_*.h5`

### Predictions look wrong (all same value)
- Make sure LSTM models are properly trained
- Check for error messages in backend logs
- Verify tensor shapes in lstm_inference.py

---

## Roll Back (If Needed)

If you want to revert to RandomForest-only:

1. Remove the LSTM import
2. Remove LSTM initialization
3. Change `_build_trend` calls to not pass `from_iata`/`to_iata`
4. Remove the LSTM fallback logic

The RandomForest code will still work as before.

---

**Questions?** Check:
- `LSTM_QUICK_START.md` for quick reference
- `LSTM_INTEGRATION_GUIDE.md` for detailed guide
- `lstm_inference.py` for implementation details
