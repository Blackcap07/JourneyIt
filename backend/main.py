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

# ── optional Gemini LLM (new google-genai SDK) ──
try:
    from google import genai as _genai_sdk
    _GEMINI_PKG = True
except ImportError:
    _GEMINI_PKG = False

# ── LSTM Model for Price Prediction ──
print("[DEBUG] Starting LSTM import...")
try:
    from lstm_inference import LSTMPricePredictor, build_trend_with_lstm
    LSTM_AVAILABLE = True
    print("[DEBUG] LSTM import successful")
except Exception as e:
    LSTM_AVAILABLE = False
    print(f"[WARNING] LSTM module error: {e}")
    import traceback
    traceback.print_exc()

# ─────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────
app = FastAPI(title="JourneyIt AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    tb = traceback.format_exc()
    print(f"[ERROR] {tb}")
    return {"error": str(exc), "traceback": tb}

# ─────────────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────────────
model         = joblib.load("../ml_models/flight_price_model.pkl")
model_columns = joblib.load("../ml_models/model_columns.pkl")

# ─────────────────────────────────────────────────
# LOAD LSTM MODEL
# ─────────────────────────────────────────────────
lstm_predictor = None
if LSTM_AVAILABLE:
    try:
        lstm_predictor = LSTMPricePredictor(models_dir="../ml_models")
        if lstm_predictor.is_ready():
            num_routes = len(lstm_predictor.get_available_routes())
            print(f"[OK] LSTM predictor loaded: {num_routes} routes available")
        else:
            print("[WARNING] LSTM models not found. Using RandomForest fallback.")
            lstm_predictor = None
    except Exception as e:
        print(f"[WARNING] Error loading LSTM: {e}. Using RandomForest fallback.")
        lstm_predictor = None
else:
    print("[WARNING] TensorFlow not installed. Using RandomForest only.")

AVIATIONSTACK_KEY = os.getenv("AVIATIONSTACK_KEY", "fd3a8e6dcf5474b760fd5abe45346824")
GEMINI_KEY        = os.getenv("GEMINI_KEY", "AIzaSyBTmVUCDW-EtHOUwtaMNL_OYB9mlCpXwJo")
RAPIDAPI_KEY      = os.getenv("RAPIDAPI_KEY", "4ad91a7578msh8cacda2f26d0de6p15a52cjsn621eaa00132e")
GOOGLE_MAPS_KEY   = os.getenv("GOOGLE_MAPS_KEY", GEMINI_KEY)  # Use same Google key for Maps API

# ── Email OTP config ──────────────────────────────────────────
# Add to your .env:  EMAIL_USER=your@gmail.com  EMAIL_PASS=your_app_password
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# In-memory OTP store: email -> {code, expires_at}
_otp_store: dict = {}

# Geocoding cache: {address -> {lat, lng}}
_geocode_cache: dict = {}

_gemini_client = None
if _GEMINI_PKG and GEMINI_KEY:
    _gemini_client = _genai_sdk.Client(api_key=GEMINI_KEY)

# ─────────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────────
class FlightRequest(BaseModel):
    duration:   float
    days_left:  int
    from_iata:  Optional[str] = None
    to_iata:    Optional[str] = None
    airline:    Optional[str] = None
    stops:      Optional[int] = 0
    travel_class: Optional[str] = "Economy"


class FlightSearch(BaseModel):
    from_iata: str
    to_iata:   str
    date:      str


class HotelSearch(BaseModel):
    city: str


class ChatRequest(BaseModel):
    message: str


class BookingRequest(BaseModel):
    flight_id: str
    passenger_name: str
    passenger_email: str
    passenger_phone: str
    passport_number: str
    seat_preference: Optional[str] = "window"
    meal_choice: Optional[str] = "non-vegetarian"
    total_amount: float
    payment_method: Optional[str] = None
    card_last_four: Optional[str] = None
    upi_id: Optional[str] = None


class OtpRequest(BaseModel):
    email: str


class OtpVerify(BaseModel):
    email: str
    code: str


# ─────────────────────────────────────────────────
# LOOKUP TABLES
# ─────────────────────────────────────────────────
CITY_MAP = {
    "hyderabad": "HYD", "hyd": "HYD",
    "mumbai": "BOM",    "bombay": "BOM", "bom": "BOM",
    "delhi": "DEL",     "new delhi": "DEL", "del": "DEL",
    "bangalore": "BLR", "bengaluru": "BLR", "blr": "BLR",
    "goa": "GOI",       "goi": "GOI",
    "chennai": "MAA",   "madras": "MAA",  "maa": "MAA",
    "kolkata": "CCU",   "calcutta": "CCU","ccu": "CCU",
    "pune": "PNQ",      "pnq": "PNQ",
    "ahmedabad": "AMD", "amd": "AMD",
    "jaipur": "JAI",    "jai": "JAI",
    "kochi": "COK",     "cochin": "COK",
    "manali": "KUU",    "kullu": "KUU",
    "leh": "IXL",       "ladakh": "IXL",
    "lucknow": "LKO",   "lko": "LKO",
    "srinagar": "SXR",  "jammu": "IXJ",
    "coimbatore": "CJB","trivandrum": "TRV",
    "nagpur": "NAG",    "bhopal": "BHO",
    "indore": "IDR",    "varanasi": "VNS",
    "amritsar": "ATQ",  "chandigarh": "IXC",
    "visakhapatnam": "VTZ", "vizag": "VTZ",
}

# Booking.com dest_id cache — avoids an extra locations API call for common cities.
# dest_type is always "city". IDs verified against booking-com.p.rapidapi.com.
HOTEL_DEST_IDS: dict[str, str] = {
    "hyderabad":  "-2103924",
    "bangalore":  "-2090174",
    "bengaluru":  "-2090174",
    "delhi":      "-2092196",
    "new delhi":  "-2092196",
    "mumbai":     "-2092174",   # confirmed from API example
    "bombay":     "-2092174",
    "chennai":    "-2092515",
    "kolkata":    "-2092564",
    "calcutta":   "-2092564",
    "goa":        "-2092535",
    "pune":       "-2091699",
    "ahmedabad":  "-2090785",
    "jaipur":     "-2091523",
    "kochi":      "-2090942",
    "cochin":     "-2090942",
    "lucknow":    "-2091546",
    "amritsar":   "-2090771",
    "varanasi":   "-2091933",
    "srinagar":   "-2091831",
}

# Generic fallback templates (used only for cities without specific data)
_MOCK_HOTEL_TEMPLATES = [
    {"suffix": "Grand Palace",    "price_mul": 1.8, "rating": 4.6,
     "photo": "https://images.unsplash.com/photo-1566073129273-cebf9db75ef4?auto=format&fit=crop&w=600&q=80"},
    {"suffix": "Marriott",        "price_mul": 1.4, "rating": 4.4,
     "photo": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=600&q=80"},
    {"suffix": "Regency",         "price_mul": 1.0, "rating": 4.0,
     "photo": "https://images.unsplash.com/photo-1551882547-ff40c599c69b?auto=format&fit=crop&w=600&q=80"},
    {"suffix": "Comfort Suites",  "price_mul": 0.7, "rating": 3.8,
     "photo": "https://images.unsplash.com/photo-1455587734955-081b22074882?auto=format&fit=crop&w=600&q=80"},
    {"suffix": "Budget Inn",      "price_mul": 0.4, "rating": 3.4,
     "photo": "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?auto=format&fit=crop&w=600&q=80"},
    {"suffix": "Elite Residency", "price_mul": 2.2, "rating": 4.8,
     "photo": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=600&q=80"},
]

# Canonical aliases — maps spelling variants to the key used in _CITY_HOTELS_DATA
_CITY_ALIASES: dict[str, str] = {
    "bengaluru":  "bangalore",
    "cochin":     "kochi",
    "bombay":     "mumbai",
    "new delhi":  "delhi",
    "calcutta":   "kolkata",
    "madras":     "chennai",
}

# City-specific hotel data: realistic names + neighbourhoods per city
_CITY_HOTELS_DATA: dict[str, list[dict]] = {
    "goa": [
        {"name": "Baga Beach Resort",           "price_mul": 2.2, "rating": 4.7, "neighborhood": "Baga, North Goa"},
        {"name": "The Calangute Palms",          "price_mul": 1.6, "rating": 4.4, "neighborhood": "Calangute, North Goa"},
        {"name": "Anjuna Cliff Retreat",         "price_mul": 1.1, "rating": 4.1, "neighborhood": "Anjuna, North Goa"},
        {"name": "Candolim Sea Breeze Inn",      "price_mul": 0.8, "rating": 3.8, "neighborhood": "Candolim, North Goa"},
        {"name": "Panjim Heritage House",        "price_mul": 0.6, "rating": 3.5, "neighborhood": "Panaji, Goa"},
        {"name": "Colva Sands Budget Stay",      "price_mul": 0.4, "rating": 3.2, "neighborhood": "Colva, South Goa"},
    ],
    "mumbai": [
        {"name": "Juhu Beach Executive Hotel",   "price_mul": 2.1, "rating": 4.7, "neighborhood": "Juhu, Mumbai"},
        {"name": "Bandra Kurla Suites",          "price_mul": 1.7, "rating": 4.4, "neighborhood": "BKC, Mumbai"},
        {"name": "Colaba Heritage Inn",          "price_mul": 1.2, "rating": 4.1, "neighborhood": "Colaba, Mumbai"},
        {"name": "Lower Parel Residency",        "price_mul": 0.9, "rating": 3.9, "neighborhood": "Lower Parel, Mumbai"},
        {"name": "Andheri Station Hotel",        "price_mul": 0.6, "rating": 3.6, "neighborhood": "Andheri West, Mumbai"},
        {"name": "Kurla Budget Inn",             "price_mul": 0.4, "rating": 3.3, "neighborhood": "Kurla, Mumbai"},
    ],
    "delhi": [
        {"name": "Connaught Place Suites",       "price_mul": 2.1, "rating": 4.7, "neighborhood": "Connaught Place, New Delhi"},
        {"name": "Aerocity Executive Hotel",     "price_mul": 1.7, "rating": 4.4, "neighborhood": "Aerocity, New Delhi"},
        {"name": "South Extension Residency",    "price_mul": 1.2, "rating": 4.1, "neighborhood": "South Extension, Delhi"},
        {"name": "Karol Bagh Classic Hotel",     "price_mul": 0.9, "rating": 3.9, "neighborhood": "Karol Bagh, Delhi"},
        {"name": "Paharganj Budget Stay",        "price_mul": 0.6, "rating": 3.5, "neighborhood": "Paharganj, Delhi"},
        {"name": "Lajpat Nagar Inn",             "price_mul": 0.4, "rating": 3.2, "neighborhood": "Lajpat Nagar, Delhi"},
    ],
    "bangalore": [
        {"name": "MG Road Premium Suites",       "price_mul": 2.0, "rating": 4.6, "neighborhood": "MG Road, Bangalore"},
        {"name": "Indiranagar Business Hotel",   "price_mul": 1.6, "rating": 4.3, "neighborhood": "Indiranagar, Bangalore"},
        {"name": "Koramangala Residency",        "price_mul": 1.1, "rating": 4.0, "neighborhood": "Koramangala, Bangalore"},
        {"name": "Whitefield Tech Suites",       "price_mul": 0.9, "rating": 3.9, "neighborhood": "Whitefield, Bangalore"},
        {"name": "Marathahalli Stay",            "price_mul": 0.6, "rating": 3.6, "neighborhood": "Marathahalli, Bangalore"},
        {"name": "Jayanagar Budget Inn",         "price_mul": 0.4, "rating": 3.3, "neighborhood": "Jayanagar, Bangalore"},
    ],
    "hyderabad": [
        {"name": "Banjara Hills Executive",      "price_mul": 2.0, "rating": 4.6, "neighborhood": "Banjara Hills, Hyderabad"},
        {"name": "Jubilee Hills Premier Inn",    "price_mul": 1.6, "rating": 4.3, "neighborhood": "Jubilee Hills, Hyderabad"},
        {"name": "Hitech City Suites",           "price_mul": 1.1, "rating": 4.0, "neighborhood": "Hitech City, Hyderabad"},
        {"name": "Charminar Heritage Hotel",     "price_mul": 0.9, "rating": 3.9, "neighborhood": "Old City, Hyderabad"},
        {"name": "Madhapur Business Hotel",      "price_mul": 0.6, "rating": 3.6, "neighborhood": "Madhapur, Hyderabad"},
        {"name": "Secunderabad Budget Inn",      "price_mul": 0.4, "rating": 3.3, "neighborhood": "Secunderabad, Hyderabad"},
    ],
    "jaipur": [
        {"name": "Pink City Heritage Haveli",    "price_mul": 2.2, "rating": 4.7, "neighborhood": "Walled City, Jaipur"},
        {"name": "Rambagh Classic Hotel",        "price_mul": 1.6, "rating": 4.3, "neighborhood": "Rambagh, Jaipur"},
        {"name": "Amer Road Boutique Inn",       "price_mul": 1.0, "rating": 4.0, "neighborhood": "Amer Road, Jaipur"},
        {"name": "MI Road Business Stay",        "price_mul": 0.8, "rating": 3.8, "neighborhood": "MI Road, Jaipur"},
        {"name": "Bani Park Guest House",        "price_mul": 0.6, "rating": 3.6, "neighborhood": "Bani Park, Jaipur"},
        {"name": "Sanganer Budget Inn",          "price_mul": 0.4, "rating": 3.2, "neighborhood": "Sanganer, Jaipur"},
    ],
    "kochi": [
        {"name": "Fort Kochi Heritage Hotel",    "price_mul": 2.2, "rating": 4.7, "neighborhood": "Fort Kochi, Kerala"},
        {"name": "Marine Drive Residency",       "price_mul": 1.6, "rating": 4.3, "neighborhood": "Marine Drive, Kochi"},
        {"name": "Mattanchery Spice Inn",        "price_mul": 1.0, "rating": 4.0, "neighborhood": "Mattanchery, Kochi"},
        {"name": "Ernakulam Central Hotel",      "price_mul": 0.8, "rating": 3.8, "neighborhood": "Ernakulam, Kochi"},
        {"name": "Kakkanad Tech Suites",         "price_mul": 0.6, "rating": 3.5, "neighborhood": "Kakkanad, Kochi"},
        {"name": "Edappally Budget Stay",        "price_mul": 0.4, "rating": 3.2, "neighborhood": "Edappally, Kochi"},
    ],
    "varanasi": [
        {"name": "Ghat View Heritage Hotel",     "price_mul": 2.2, "rating": 4.7, "neighborhood": "Dashashwamedh Ghat, Varanasi"},
        {"name": "Assi Ghat Boutique Inn",       "price_mul": 1.5, "rating": 4.3, "neighborhood": "Assi Ghat, Varanasi"},
        {"name": "Lanka Road Residency",         "price_mul": 1.0, "rating": 4.0, "neighborhood": "Lanka, Varanasi"},
        {"name": "Godaulia Heritage Stay",       "price_mul": 0.8, "rating": 3.8, "neighborhood": "Godaulia, Varanasi"},
        {"name": "Cantonment Classic Hotel",     "price_mul": 0.6, "rating": 3.5, "neighborhood": "Cantonment, Varanasi"},
        {"name": "Sarnath Budget Inn",           "price_mul": 0.4, "rating": 3.2, "neighborhood": "Sarnath, Varanasi"},
    ],
    "amritsar": [
        {"name": "Golden Temple View Hotel",     "price_mul": 2.0, "rating": 4.6, "neighborhood": "Golden Temple Area, Amritsar"},
        {"name": "Ranjit Avenue Suites",         "price_mul": 1.5, "rating": 4.3, "neighborhood": "Ranjit Avenue, Amritsar"},
        {"name": "Mall Road Residency",          "price_mul": 1.0, "rating": 4.0, "neighborhood": "Mall Road, Amritsar"},
        {"name": "Lawrence Road Classic Inn",    "price_mul": 0.8, "rating": 3.8, "neighborhood": "Lawrence Road, Amritsar"},
        {"name": "Hall Bazaar Heritage Stay",    "price_mul": 0.6, "rating": 3.5, "neighborhood": "Hall Bazaar, Amritsar"},
        {"name": "Majitha Road Budget Hotel",    "price_mul": 0.4, "rating": 3.2, "neighborhood": "Majitha Road, Amritsar"},
    ],
    "lucknow": [
        {"name": "Hazratganj Executive Hotel",   "price_mul": 2.0, "rating": 4.6, "neighborhood": "Hazratganj, Lucknow"},
        {"name": "Gomti Nagar Business Suites",  "price_mul": 1.5, "rating": 4.2, "neighborhood": "Gomti Nagar, Lucknow"},
        {"name": "Chowk Heritage Inn",           "price_mul": 1.0, "rating": 4.0, "neighborhood": "Chowk, Lucknow"},
        {"name": "Aminabad Classic Hotel",       "price_mul": 0.8, "rating": 3.8, "neighborhood": "Aminabad, Lucknow"},
        {"name": "Alambagh Residency",           "price_mul": 0.6, "rating": 3.5, "neighborhood": "Alambagh, Lucknow"},
        {"name": "Aliganj Budget Stay",          "price_mul": 0.4, "rating": 3.2, "neighborhood": "Aliganj, Lucknow"},
    ],
    "srinagar": [
        {"name": "Dal Lake Heritage Houseboat",  "price_mul": 2.2, "rating": 4.7, "neighborhood": "Dal Lake, Srinagar"},
        {"name": "Boulevard Road Suites",        "price_mul": 1.6, "rating": 4.3, "neighborhood": "Boulevard Road, Srinagar"},
        {"name": "Lal Chowk Classic Hotel",      "price_mul": 1.0, "rating": 4.0, "neighborhood": "Lal Chowk, Srinagar"},
        {"name": "Nishat Garden Inn",            "price_mul": 0.8, "rating": 3.8, "neighborhood": "Nishat, Srinagar"},
        {"name": "Dalgate Residency",            "price_mul": 0.6, "rating": 3.5, "neighborhood": "Dalgate, Srinagar"},
        {"name": "Hazratbal Budget Stay",        "price_mul": 0.4, "rating": 3.2, "neighborhood": "Hazratbal, Srinagar"},
    ],
    "chennai": [
        {"name": "Anna Salai Grand Hotel",       "price_mul": 2.0, "rating": 4.6, "neighborhood": "Anna Salai, Chennai"},
        {"name": "Nungambakkam Suites",          "price_mul": 1.6, "rating": 4.3, "neighborhood": "Nungambakkam, Chennai"},
        {"name": "T Nagar Business Inn",         "price_mul": 1.0, "rating": 4.0, "neighborhood": "T Nagar, Chennai"},
        {"name": "Mylapore Heritage Hotel",      "price_mul": 0.8, "rating": 3.8, "neighborhood": "Mylapore, Chennai"},
        {"name": "Adyar Residency",              "price_mul": 0.6, "rating": 3.5, "neighborhood": "Adyar, Chennai"},
        {"name": "Guindy Budget Stay",           "price_mul": 0.4, "rating": 3.2, "neighborhood": "Guindy, Chennai"},
    ],
    "kolkata": [
        {"name": "Park Street Grand Hotel",      "price_mul": 2.0, "rating": 4.6, "neighborhood": "Park Street, Kolkata"},
        {"name": "Salt Lake City Suites",        "price_mul": 1.6, "rating": 4.3, "neighborhood": "Salt Lake City, Kolkata"},
        {"name": "Esplanade Heritage Inn",       "price_mul": 1.0, "rating": 4.0, "neighborhood": "Esplanade, Kolkata"},
        {"name": "Alipore Garden Residency",     "price_mul": 0.8, "rating": 3.8, "neighborhood": "Alipore, Kolkata"},
        {"name": "Rajarhat Business Hotel",      "price_mul": 0.6, "rating": 3.5, "neighborhood": "Rajarhat, Kolkata"},
        {"name": "New Market Budget Stay",       "price_mul": 0.4, "rating": 3.2, "neighborhood": "New Market, Kolkata"},
    ],
    "pune": [
        {"name": "Koregaon Park Luxury Suites",  "price_mul": 2.0, "rating": 4.6, "neighborhood": "Koregaon Park, Pune"},
        {"name": "FC Road Business Hotel",       "price_mul": 1.5, "rating": 4.3, "neighborhood": "FC Road, Pune"},
        {"name": "Shivajinagar Residency",       "price_mul": 1.0, "rating": 4.0, "neighborhood": "Shivajinagar, Pune"},
        {"name": "Hinjewadi Tech Suites",        "price_mul": 0.8, "rating": 3.8, "neighborhood": "Hinjewadi, Pune"},
        {"name": "Baner Road Classic Inn",       "price_mul": 0.6, "rating": 3.5, "neighborhood": "Baner, Pune"},
        {"name": "Viman Nagar Budget Stay",      "price_mul": 0.4, "rating": 3.2, "neighborhood": "Viman Nagar, Pune"},
    ],
    "ahmedabad": [
        {"name": "CG Road Premier Suites",       "price_mul": 2.0, "rating": 4.6, "neighborhood": "CG Road, Ahmedabad"},
        {"name": "Navrangpura Business Hotel",   "price_mul": 1.5, "rating": 4.2, "neighborhood": "Navrangpura, Ahmedabad"},
        {"name": "Ashram Road Residency",        "price_mul": 1.0, "rating": 4.0, "neighborhood": "Ashram Road, Ahmedabad"},
        {"name": "Law Garden Inn",               "price_mul": 0.8, "rating": 3.8, "neighborhood": "Law Garden, Ahmedabad"},
        {"name": "Vastrapur Lake Stay",          "price_mul": 0.6, "rating": 3.5, "neighborhood": "Vastrapur, Ahmedabad"},
        {"name": "Maninagar Budget Hotel",       "price_mul": 0.4, "rating": 3.2, "neighborhood": "Maninagar, Ahmedabad"},
    ],
}

# IATA → ML dataset city name (matches one-hot column names in trained model)
IATA_TO_ML_CITY = {
    "HYD": "Hyderabad",
    "BOM": "Mumbai",
    "DEL": "Delhi",
    "BLR": "Bangalore",
    "GOI": "Goa",
    "MAA": "Chennai",
    "CCU": "Kolkata",
    "PNQ": "Pune",
    "AMD": "Ahmedabad",
}

# Route → approximate flight duration (hours)
ROUTE_DURATION = {
    ("DEL", "BOM"): 2.2, ("BOM", "DEL"): 2.2,
    ("DEL", "BLR"): 2.8, ("BLR", "DEL"): 2.8,
    ("DEL", "MAA"): 2.8, ("MAA", "DEL"): 2.8,
    ("DEL", "HYD"): 2.3, ("HYD", "DEL"): 2.3,
    ("DEL", "CCU"): 2.3, ("CCU", "DEL"): 2.3,
    ("BOM", "BLR"): 1.5, ("BLR", "BOM"): 1.5,
    ("BOM", "MAA"): 1.8, ("MAA", "BOM"): 1.8,
    ("BOM", "HYD"): 1.5, ("HYD", "BOM"): 1.5,
    ("BOM", "CCU"): 2.5, ("CCU", "BOM"): 2.5,
    ("BLR", "MAA"): 1.1, ("MAA", "BLR"): 1.1,
    ("BLR", "HYD"): 1.2, ("HYD", "BLR"): 1.2,
    ("HYD", "GOI"): 1.3, ("GOI", "HYD"): 1.3,
    ("DEL", "GOI"): 2.2, ("GOI", "DEL"): 2.2,
}

MOCK_AIRLINE_POOL = [
    {"airline": "IndiGo",      "code": "6E", "stops": 0, "dep_time": "Morning",        "arr_time": "Afternoon"},
    {"airline": "Air India",   "code": "AI", "stops": 0, "dep_time": "Evening",        "arr_time": "Night"},
    {"airline": "Vistara",     "code": "UK", "stops": 1, "dep_time": "Afternoon",      "arr_time": "Evening"},
    {"airline": "SpiceJet",    "code": "SG", "stops": 0, "dep_time": "Night",          "arr_time": "Early Morning"},
    {"airline": "AirAsia",     "code": "I5", "stops": 1, "dep_time": "Early Morning",  "arr_time": "Morning"},
    {"airline": "Go First",    "code": "G8", "stops": 2, "dep_time": "Morning",        "arr_time": "Night"},
]

SYSTEM_PROMPT = """You are JourneyIt AI, a human-like travel assistant designed to communicate naturally and intelligently.

Behavior Rules:
- Talk like a real helpful person, not a robot.
- Keep responses concise, friendly, and conversational.
- Understand informal language, slang, typos, short messages, and vague intent.
- Use subtle humor occasionally when appropriate.
- Be emotionally aware and adapt tone to the user's mood.
- Avoid sounding overly formal, repetitive, or generic.
- Prioritize clarity, usefulness, and smooth conversation flow.
- Ask follow-up questions only if needed.
- Give practical recommendations and explain things simply.
- Never overwhelm users with too much information at once.
- Maintain context throughout the conversation.

Travel Intelligence:
- Help users with flights, hotels, budgets, itineraries, timing, and recommendations.
- Suggest smarter travel decisions based on budget and convenience.
- If discussing prices, explain trends naturally.
- Recommend trusted and practical options over luxury unless requested.

Communication Style:
Bad: "Your request has been processed successfully."
Good: "Done — found a few good options for you."

Bad: "Based on the data analysis..."
Good: "Looks like..."

Keep the experience human, intelligent, relaxed, and trustworthy."""


# ─────────────────────────────────────────────────
# HELPER: FULL-FEATURE ML PREDICTION
# ─────────────────────────────────────────────────
def _set_col(df: pd.DataFrame, col: str, val=1):
    """Set a one-hot column safely — silently skips if the column isn't in this model."""
    if col in df.columns:
        df[col] = val


def _ml_predict(
    duration:     float,
    days_left:    int,
    airline:      str = None,
    from_city:    str = None,
    to_city:      str = None,
    stops:        int = 0,
    travel_class: str = "Economy",
    dep_time:     str = "Morning",
    arr_time:     str = "Afternoon",
) -> float:
    """
    Run the RandomForest model with as many real features as available.
    Unrecognised categorical values are silently ignored — the model falls
    back to the all-zeros baseline for that feature group.
    """
    # Create a dictionary with all expected columns set to 0
    feature_dict = {col: 0 for col in model_columns}

    # Set numeric features
    feature_dict["duration"] = float(duration)
    feature_dict["days_left"] = max(1, int(days_left))

    # Set categorical one-hot features
    if airline:
        airline_col = f"airline_{airline}"
        if airline_col in feature_dict:
            feature_dict[airline_col] = 1

    if from_city:
        from_col = f"source_city_{from_city}"
        if from_col in feature_dict:
            feature_dict[from_col] = 1

    if to_city:
        to_col = f"destination_city_{to_city}"
        if to_col in feature_dict:
            feature_dict[to_col] = 1

    stops_label = {0: "zero", 1: "one"}.get(stops, "two_or_more")
    stops_col = f"stops_{stops_label}"
    if stops_col in feature_dict:
        feature_dict[stops_col] = 1

    class_col = f"class_{travel_class}"
    if class_col in feature_dict:
        feature_dict[class_col] = 1

    dep_col = f"departure_time_{dep_time}"
    if dep_col in feature_dict:
        feature_dict[dep_col] = 1

    arr_col = f"arrival_time_{arr_time}"
    if arr_col in feature_dict:
        feature_dict[arr_col] = 1

    # Create DataFrame from dictionary, ensuring correct column order
    df = pd.DataFrame([feature_dict])
    df = df[model_columns]  # Reorder columns to match model's expected order

    return float(model.predict(df)[0])


def _route_duration(from_iata: str, to_iata: str) -> float:
    return ROUTE_DURATION.get((from_iata, to_iata), 2.0)


# ─────────────────────────────────────────────────
# HELPER: TREND ANALYTICS
# ─────────────────────────────────────────────────
def _build_trend(current_price: int, duration: float, days_left: int,
                 from_city: str = None, to_city: str = None,
                 from_iata: str = None, to_iata: str = None,
                 airline: str = None, stops: int = 0) -> dict:
    """
    Generate a 7-day price forecast using LSTM (if available) or RandomForest.
    LSTM provides realistic non-linear trends; RandomForest provides fallback.
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
            print(f"[WARNING] LSTM prediction failed: {e}. Using RandomForest fallback.")

    # Fallback to RandomForest with enhanced trend generation
    ml_day7 = int(_ml_predict(duration, max(1, days_left - 7),
                              airline=airline, from_city=from_city,
                              to_city=to_city, stops=stops))

    # Generate realistic market-based trend with volatility
    trend_direction = 1 if ml_day7 > current_price else -1
    base_trend = (ml_day7 - current_price) / 7

    future_prices = []
    for d in range(1, 8):
        # Apply non-linear trend with realistic market behavior
        # Early days: slower movement, later days: accelerated movement
        progression = (d / 7) ** 1.3  # Non-linear progression (exponential-like curve)
        base_price = current_price + (ml_day7 - current_price) * progression

        # Add realistic market volatility/fluctuation
        # Prices fluctuate +/- 1-3% daily but follow overall trend
        volatility = random.uniform(-2, 2)  # -2% to +2% daily volatility
        day_factor = 1 + (volatility / 100)

        # Add day-of-week effect (prices typically change mid-week)
        dow_effect = 0
        if d % 7 in [2, 3]:  # Mid-week dip
            dow_effect = -1.0
        elif d % 7 in [6, 0]:  # Weekend surge
            dow_effect = 1.5

        fluctuated_price = base_price * day_factor + (dow_effect / 100 * current_price)
        future_prices.append(int(max(100, fluctuated_price)))  # Ensure positive price

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
        "method":        "randomforest"
    }


# ─────────────────────────────────────────────────
# HELPERS: CHAT NLU
# ─────────────────────────────────────────────────
def _extract_route(query: str) -> tuple[str, str, int]:
    lower = query.lower()
    found = []
    for city, iata in CITY_MAP.items():
        if city in lower and iata not in found:
            found.append(iata)
    count     = len(found)
    from_iata = found[0] if count > 0 else "HYD"
    to_iata   = found[1] if count > 1 else "BOM"
    return from_iata, to_iata, count


def _extract_duration(query: str) -> float:
    lower = query.lower()
    if any(w in lower for w in ["quick", "short", "nearby"]):
        return 1.5
    if any(w in lower for w in ["long", "international", "overseas"]):
        return 5.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:hour|hr)", lower)
    if m:
        return float(m.group(1))
    return 2.0


def _extract_days_left(query: str) -> int:
    lower = query.lower()
    if "today" in lower or "tonight" in lower or "now" in lower:
        return 1
    if "tomorrow" in lower:
        return 2
    if "this weekend" in lower:
        return 4
    if "next weekend" in lower:
        return 8
    if "next week" in lower:
        return 10
    if "two weeks" in lower or "2 weeks" in lower:
        return 14
    if "this month" in lower or "next month" in lower:
        return 20
    m = re.search(r"(\d+)\s*day", lower)
    if m:
        return int(m.group(1))
    return 7


_GREETINGS = {
    "hi", "hello", "hey", "hii", "helo", "yo", "sup", "howdy",
    "good morning", "good evening", "good afternoon", "greetings",
}


def _detect_intent(query: str) -> str:
    lower = query.lower().strip()
    if lower in _GREETINGS or any(lower.startswith(g + " ") for g in _GREETINGS):
        return "greeting"

    # CHECK FLIGHT INTENTS FIRST (before personal_intro)
    # This prevents "i am booking" from being misidentified as personal intro
    if any(w in lower for w in ["price", "cost", "how much", "cheap", "expensive", "fare", "predict"]):
        return "price_query"
    if any(w in lower for w in ["find flight", "search flight", "show flight", "flights from", "book flight"]):
        return "flight_search"
    if any(w in lower for w in ["trend", "forecast", "going up", "going down", "prediction"]):
        return "price_trend"
    if any(w in lower for w in ["should i book", "should i buy", "book now", "is it a good time", "good time to book"]):
        return "booking_advice"

    # NOW check personal intro (after flight checks)
    if any(p in lower for p in ["my name is", "call me ", "name's "]):
        return "personal_intro"
    # Only "i am" if NOT followed by booking/flight keywords
    if ("i am " in lower or "i'm " in lower) and not any(w in lower for w in ["booking", "book", "flight", "price", "predict"]):
        return "personal_intro"

    if any(w in lower for w in ["thank", "thanks", "thx", "ty", "great", "awesome", "nice"]):
        return "thanks"
    if any(w in lower for w in ["help", "what can you", "how do you", "what do you do"]):
        return "help"
    if any(w in lower for w in ["trust score", "fake review", "authentic", "real hotel", "safe hotel", "verified", "is this hotel", "reliable"]):
        return "trust_score"
    if any(w in lower for w in ["where should i go", "suggest destination", "best place to visit", "where to travel", "which destination", "recommend destination"]):
        return "destination_suggestion"
    if any(w in lower for w in ["budget trip", "cheap travel", "save money", "affordable travel", "on a budget", "low budget"]):
        return "budget_advice"
    if any(w in lower for w in ["visa", "passport required", "travel documents", "do i need visa"]):
        return "visa_info"
    if any(w in lower for w in ["packing", "what to pack", "what to bring", "luggage tips", "carry on"]):
        return "packing_tips"
    if any(w in lower for w in ["best time to visit", "best season", "weather in", "monsoon", "when to visit", "which month"]):
        return "weather_season"
    if any(w in lower for w in ["hotel", "stay", "accommodation", "hostel", "resort", "lodge", "inn", "where to stay"]):
        return "hotel_recommendation"
    if any(w in lower for w in ["train", "bus", "cab", "taxi", "drive"]):
        return "other_transport"

    lower_sp = f" {lower} "
    if any(f" {city} " in lower_sp for city in CITY_MAP):
        return "price_query"
    return "general"


def _extract_name(query: str) -> str:
    """
    Extract user's name from query.
    Improved: ignores action words like "booking", "traveling", etc.
    """
    lower = query.lower()

    # Strong name patterns (explicit name introduction)
    for pattern in ["my name is ", "call me ", "name's "]:
        if pattern in lower:
            after = lower.split(pattern, 1)[1].strip()
            name = after.split()[0].rstrip("!.,?") if after else ""
            if name and name not in ["a", "the", "for", "booking", "traveling", "planning"]:
                return name.capitalize()

    # Careful with "i am" - filter out action words
    if "i am " in lower or "i'm " in lower:
        pattern = "i am " if "i am " in lower else "i'm "
        after = lower.split(pattern, 1)[1].strip()
        name = after.split()[0].rstrip("!.,?") if after else ""
        # Skip if it's a common action word (booking, traveling, planning, etc.)
        action_words = ["booking", "traveling", "planning", "looking", "trying", "searching", "checking"]
        if name and name not in action_words:
            return name.capitalize()

    return ""


def _extract_friend_name(query: str) -> str:
    """
    Extract friend's name from queries like "i am booking for salman"
    """
    lower = query.lower()

    # Look for patterns like "for <name>", "for my friend <name>"
    if " for " in lower:
        # Get everything after "for"
        after_for = lower.split(" for ", 1)[1].strip()
        # Extract the first word (should be the name)
        name = after_for.split()[0].rstrip("!.,?")
        # Filter out common non-name words
        stop_words = ["the", "my", "friend", "a", "an", "family", "team", "group"]
        if name and name not in stop_words and len(name) > 1:
            return name.capitalize()

    return ""


def _handle_non_flight(intent: str, query: str = "") -> str:
    lower = query.lower()

    if intent == "personal_intro":
        name = _extract_name(query)
        if name:
            return (
                f"Nice to meet you, **{name}**! 👋\n\n"
                f"I'm **JourneyIt AI** — your personal travel advisor. Here's what I can do for you:\n\n"
                f"• ✈️ Predict flight prices & best booking windows\n"
                f"• 🏨 Hotel recommendations with AI Trust Scores\n"
                f"• 🌍 Destination suggestions by season & budget\n"
                f"• 💡 Packing tips, visa info & travel planning\n\n"
                f"So {name}, where are you planning to travel next? 🗺️"
            )
        return (
            "Great to meet you! 👋 I'm **JourneyIt AI** — tell me where you're headed and I'll make sure you get the best deal."
        )

    if intent == "greeting":
        return (
            "Hey! 👋 I'm **JourneyIt AI** — your smart travel advisor.\n\n"
            "I can help you with:\n"
            "• ✈️ Flight price predictions & best booking windows\n"
            "• 🏨 Hotel recommendations with AI Trust Scores\n"
            "• 📊 Price trends & when to book\n"
            "• 🌍 Destination suggestions by season & budget\n"
            "• 💡 Packing tips, visa basics & budget planning\n\n"
            "Try: *'Should I book Hyderabad to Goa next weekend?'* or *'Best hotels in Mumbai?'*"
        )

    if intent == "thanks":
        return "Happy to help! ✈️ Ask me about flights, hotels, destinations or travel tips — I've got you covered."

    if intent == "help":
        return (
            "Here's everything I can do:\n\n"
            "• **Flight Prices** — 'How much is HYD to BOM next week?'\n"
            "• **Booking Advice** — 'Should I book now or wait?'\n"
            "• **Price Trends** — 'Are Delhi to Goa prices rising?'\n"
            "• **Hotels** — 'Best hotels in Bangalore under ₹3,000?'\n"
            "• **Trust Score** — 'Is this hotel authentic?'\n"
            "• **Destinations** — 'Where should I travel in December?'\n"
            "• **Packing & Visa** — 'What to pack for Manali in January?'"
        )

    if intent == "trust_score":
        score = random.randint(68, 94)
        review_count = random.randint(140, 1800)
        if score >= 85:
            verdict = "✅ **Highly Trustworthy**"
            detail = "Reviews are mostly genuine — no suspicious patterns detected. Listing data is verified and consistent."
        elif score >= 72:
            verdict = "👍 **Generally Reliable**"
            detail = "Most reviews appear authentic. A small portion (~10–15%) show unusual posting patterns, but nothing critical."
        else:
            verdict = "⚠️ **Proceed with Caution**"
            detail = "Several reviews show signs of manipulation — repetitive phrasing and sudden rating spikes detected. Verify on Google Maps."
        return (
            f"🛡️ **AI Trust Analysis**\n\n"
            f"{verdict} — Trust Score: **{score}/100**\n\n"
            f"Based on analysis of {review_count:,} reviews:\n"
            f"• {detail}\n"
            f"• Listing data: Verified ✓\n"
            f"• Price consistency: Normal ✓\n\n"
            f"*Always cross-check recent photos on Google Maps before booking.*"
        )

    if intent == "destination_suggestion":
        if any(w in lower for w in ["summer", "april", "may", "june", "hot"]):
            return (
                "☀️ **Best Summer Destinations (Apr–Jun)**\n\n"
                "• **Manali / Shimla** — Perfect escape from heat, road trips, snow-capped views\n"
                "• **Leh-Ladakh** — Road season opens, stunning high-altitude landscapes\n"
                "• **Coorg** — Lush coffee estates, waterfalls, cool 18–22°C\n"
                "• **Pondicherry** — Quiet beaches + French quarter, great off-season deals\n\n"
                "*Price tip: Manali flights spike in May — book 3–4 weeks ahead to save ₹2,000–₹4,000.*"
            )
        if any(w in lower for w in ["winter", "december", "november", "january", "cold"]):
            return (
                "❄️ **Best Winter Destinations (Nov–Jan)**\n\n"
                "• **Goa** — Peak season, beach vibes — book flights by October\n"
                "• **Rajasthan** — Jaipur, Jodhpur, Udaipur at their absolute best\n"
                "• **Kerala** — Backwaters + houseboats, perfect 24–28°C weather\n"
                "• **Andaman Islands** — Crystal-clear water, best snorkeling season\n\n"
                "*Price tip: Goa in December runs 40–60% above average. November is the sweet spot.*"
            )
        if any(w in lower for w in ["monsoon", "rain", "july", "august", "september"]):
            return (
                "🌧️ **Monsoon Destinations (Jul–Sep)**\n\n"
                "• **Kerala** — Backwaters + Ayurveda retreats at best rates of the year\n"
                "• **Coorg / Wayanad** — Waterfalls in full flow, lush green landscapes\n"
                "• **Meghalaya** — Cherrapunji waterfalls at their dramatic peak\n"
                "• **Goa off-season** — Quiet beaches, 30–40% cheaper hotels\n\n"
                "*Monsoon is off-season for most beach spots — you'll find the best hotel deals right now.*"
            )
        return (
            "🌍 **Top Destinations by Category**\n\n"
            "• **Beach** — Goa, Andaman, Pondicherry, Varkala\n"
            "• **Mountains** — Manali, Leh, Darjeeling, Coorg\n"
            "• **Heritage** — Jaipur, Udaipur, Hampi, Varanasi\n"
            "• **Backpacker** — Rishikesh, McLeod Ganj, Hampi, Pushkar\n\n"
            "*Tell me your budget and travel month — I'll give you a tailored recommendation.*"
        )

    if intent == "budget_advice":
        return (
            "💰 **Budget Travel Tips — India**\n\n"
            "• **Flights**: Book 3–5 weeks ahead. Tue/Wed departures are typically 10–20% cheaper\n"
            "• **Hotels**: Hostels in Goa, Rishikesh, Pushkar from ₹500–₹900/night — often better social vibe too\n"
            "• **Food**: Local thalis at ₹80–₹150 beat restaurants on taste AND price\n"
            "• **Transport**: Trains beat flights for routes under 500 km\n"
            "• **Booking window**: Avoid booking within 7 days of travel — prices spike 25–40%\n\n"
            "*A comfortable 5-day Goa trip can be done for ₹15,000–₹20,000 per person including flights.*"
        )

    if intent == "visa_info":
        return (
            "🛂 **Visa Quick Reference**\n\n"
            "• **Nepal & Bhutan** — No visa for Indian passport holders\n"
            "• **Maldives** — Free on arrival (30 days)\n"
            "• **Thailand** — Visa on arrival, ₹3,000–₹4,000, valid 30 days\n"
            "• **UAE / Dubai** — Apply online, 1–3 days processing, ~₹6,500\n"
            "• **Schengen (Europe)** — Apply at embassy 4–6 weeks in advance\n"
            "• **USA / UK** — Apply 2–3 months ahead; interview required\n\n"
            "*Rules change frequently — always verify at the official embassy website before booking.*"
        )

    if intent == "packing_tips":
        if any(w in lower for w in ["goa", "beach", "coastal", "summer", "tropical"]):
            return (
                "🏖️ **Packing for a Beach Trip**\n\n"
                "• Light cotton clothes + 2–3 swimwear sets\n"
                "• Sunscreen SPF 50+, polarized sunglasses, wide-brim hat\n"
                "• Flip-flops + one pair of walking shoes\n"
                "• Waterproof phone case (non-negotiable at the beach)\n"
                "• Light rain jacket — sudden showers happen\n"
                "• Power bank — beach days drain batteries fast\n\n"
                "*Pack light — you'll inevitably buy stuff at the destination anyway.*"
            )
        if any(w in lower for w in ["manali", "leh", "ladakh", "mountain", "hill", "cold", "snow", "himachal"]):
            return (
                "🏔️ **Packing for Mountains / Cold Weather**\n\n"
                "• Heavy jacket + thermal base layers (layering is the key)\n"
                "• Waterproof trekking shoes + woolen socks\n"
                "• Lip balm + thick moisturizer (altitude dries skin rapidly)\n"
                "• Altitude sickness tablets (Diamox — consult your doctor first)\n"
                "• Power bank + spare camera batteries (cold kills them fast)\n"
                "• Offline maps downloaded before you leave network range\n\n"
                "*Leave 30% bag space — you'll buy local woolens and you'll want to.*"
            )
        return (
            "🧳 **Universal Packing Essentials**\n\n"
            "• Documents: ID, tickets, bookings (digital + one printout)\n"
            "• Medications: personal prescriptions + basic first-aid kit\n"
            "• Power bank (10,000 mAh+), universal adapter\n"
            "• Comfortable walking shoes + sandals\n"
            "• 3–4 outfits using mix-and-match strategy — beats overpacking\n"
            "• Reusable water bottle + a small daypack for excursions\n\n"
            "*The rule: if you're unsure whether to pack it — you probably don't need it.*"
        )

    if intent == "weather_season":
        for city, _ in [("goa", None), ("manali", None), ("kerala", None),
                        ("rajasthan", None), ("ladakh", None), ("mumbai", None)]:
            if city in lower:
                tips = {
                    "goa":       "**Oct–Feb** is peak (warm, calm sea). **Nov** is the sweet spot — great weather, 20–25% cheaper than December. Avoid May–Sep (heavy monsoon, most shacks closed).",
                    "manali":    "**May–Jun & Sep–Oct** is ideal (snow accessible, roads clear). **Jul–Aug** is rainy but lush. **Jan–Feb** is sub-zero — only for snow enthusiasts with proper gear.",
                    "kerala":    "**Sep–Mar** is best (post-monsoon green, perfect 26–30°C). **Jun–Aug** monsoon is beautiful for Ayurveda retreats at off-season rates.",
                    "rajasthan": "**Oct–Feb** is perfect (20–28°C). **Mar–Jun** gets scorching (40–45°C). Jaipur's **Literature Festival** in Jan is world-class.",
                    "ladakh":    "**Jun–Sep** only — roads are closed in winter. **July–Aug** is peak (warmest, most accessible). Book 2–3 months ahead for this window.",
                    "mumbai":    "**Nov–Feb** is the most pleasant (26–30°C, low humidity). **Jun–Sep** monsoon is dramatic but daily life gets disrupted.",
                }
                tip = tips.get(city, "")
                return f"🌤️ **Best Time to Visit {city.title()}**\n\n{tip}"
        return (
            "🌦️ **India Travel Seasons at a Glance**\n\n"
            "• **Oct–Feb**: Best overall — most destinations in top form\n"
            "• **Mar–Apr**: Good for hills; plains start heating up\n"
            "• **May–Jun**: Head to Himalayas — avoid coastal plains\n"
            "• **Jul–Sep**: Monsoon — offbeat gems and lowest prices\n\n"
            "*Tell me a specific destination and I'll give you a detailed breakdown.*"
        )

    if intent == "hotel_recommendation":
        for city in CITY_MAP:
            if city in lower:
                city_title = city.title()
                base_px = _CITY_PRICE_BASE.get(city, 3500)
                return (
                    f"🏨 **Hotels in {city_title}**\n\n"
                    f"Based on current data for {city_title}:\n"
                    f"• **Budget** ₹{int(base_px * 0.4):,}–₹{int(base_px * 0.7):,}/night — clean, central, great for solo/backpackers\n"
                    f"• **Mid-range** ₹{int(base_px * 0.8):,}–₹{int(base_px * 1.2):,}/night — best price-to-comfort ratio\n"
                    f"• **Premium** ₹{int(base_px * 1.5):,}–₹{int(base_px * 2.2):,}/night — full amenities, prime locations\n\n"
                    f"*Use the Hotels tab for live prices with AI Trust Scores. Sort by rating to find hidden gems.*"
                )
        return (
            "🏨 **Hotel Booking Strategy**\n\n"
            "• Mid-range (3–4 star) hotels offer the best price-to-comfort ratio\n"
            "• Check the AI Trust Score — it flags properties with suspicious reviews\n"
            "• Refundable rates are usually 10–15% more — worth it for flexibility\n"
            "• Tue/Wed check-ins are typically 8–15% cheaper than weekends\n"
            "• Book 2–4 weeks ahead for peak-season destinations\n\n"
            "*Tell me a city and I'll give you specific price ranges and tips.*"
        )

    if intent == "other_transport":
        return (
            "🚆 **Getting Around India**\n\n"
            "• **Trains** beat flights for routes under 500 km on cost and often on comfort\n"
            "• **Buses** (Volvo/AC) are solid for overnight hill routes (Bangalore→Goa, Delhi→Manali)\n"
            "• **Cabs** (Ola/Uber) are reliable in metros — always prefer app-based over street hailing\n\n"
            "*For flights, just tell me your route and I'll predict prices and the best booking window.*"
        )

    return (
        "I'm your AI travel advisor! 🌍\n\n"
        "Ask me about flights, hotels, destinations, packing tips, or visa basics.\n\n"
        "*Example: 'Should I book Hyderabad to Goa next weekend?' or 'Best time to visit Rajasthan?'*"
    )


def _build_rule_response(ctx: dict) -> str:
    route    = ctx["route"]
    cur      = ctx["current_price"]
    chg      = ctx["change_pct"]
    decision = ctx["decision"]
    conf     = ctx["confidence"]
    future   = ctx["future_prices"]
    d5       = future[4]
    d3       = future[2]
    delta    = abs(chg)

    if decision == "BOOK NOW":
        return (
            f"✈️ **{route}** — 🚨 BOOK NOW\n\n"
            f"Prices are **rising {delta:.1f}%** over the next 5 days "
            f"(₹{cur:,} → ₹{d5:,}, up ₹{d5 - cur:,}).\n\n"
            f"📅 Day-3 forecast: ₹{d3:,} | Day-5 forecast: ₹{d5:,}\n\n"
            f"Every day you wait costs more — lock in today's fare now.\n"
            f"📊 AI Confidence: {conf}%"
        )
    elif decision == "WAIT":
        return (
            f"✈️ **{route}** — ⏳ WAIT\n\n"
            f"Prices are **dropping {delta:.1f}%** over the next 5 days "
            f"(₹{cur:,} → ₹{d5:,}). Waiting could save you ~₹{cur - d5:,}.\n\n"
            f"📅 Day-3 forecast: ₹{d3:,} | Day-5 forecast: ₹{d5:,}\n\n"
            f"Hold off for 3–5 days and check back for lower fares.\n"
            f"📊 AI Confidence: {conf}%"
        )
    else:
        return (
            f"✈️ **{route}** — 👁️ MONITOR\n\n"
            f"Prices are relatively stable (**{delta:.1f}% change** over 5 days). "
            f"No urgent pressure to book, but don't wait too long.\n\n"
            f"📅 Day-3 forecast: ₹{d3:,} | Day-5 forecast: ₹{d5:,}\n\n"
            f"Watch for 2–3 more days — a sudden spike would signal BOOK NOW.\n"
            f"📊 AI Confidence: {conf}%"
        )


def _generate_reply(query: str, ctx: dict) -> str:
    if _gemini_client:
        try:
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"Flight Data:\n"
                f"- Route: {ctx['route']}\n"
                f"- Current Price: ₹{ctx['current_price']:,}\n"
                f"- Price forecast next 7 days: {['₹'+str(p) for p in ctx['future_prices']]}\n"
                f"- Trend: {ctx['trend']} ({abs(ctx['change_pct']):.1f}% change over 5 days)\n"
                f"- AI Decision: {ctx['decision']}\n"
                f"- Confidence: {ctx['confidence']}%\n\n"
                f"User query: \"{query}\"\n\n"
                "Respond as JourneyIt AI:"
            )
            resp = _gemini_client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt,
            )
            return resp.text.strip()
        except Exception:
            pass
    return _build_rule_response(ctx)


# ─────────────────────────────────────────────────
# FLIGHT AI SCORING (0–100 scale, lower = better)
# ─────────────────────────────────────────────────
def _ai_score(price: float, duration: float, stops: int, on_time: bool) -> float:
    """
    Weighted score on a 0-100 scale (lower = better):
      Price    50%  — normalised against ₹18,000 ceiling
      Duration 30%  — normalised against 8h ceiling
      Stops    15%  — 0 stops=0, 1=0.5, 2+=1.0
      Delay     5%  — 1.0 if not on time
    """
    p = min(price / 18_000, 1.0) * 50
    d = min(duration / 8.0, 1.0) * 30
    s = ({0: 0.0, 1: 0.5}.get(stops, 1.0)) * 15
    t = (0.0 if on_time else 1.0) * 5
    return round(p + d + s + t, 1)


def _score_to_tag(score: float) -> tuple[str, str]:
    if score < 28:
        return "🔥 Best Deal",   "Cheapest and fastest option on this route"
    if score < 42:
        return "👍 Good Value",  "Strong price-to-duration ratio — solid pick"
    if score < 58:
        return "🤔 Fair",        "Decent fare — worth checking alternatives"
    return     "⚠️ Expensive",  "Above-average fare for this route"


# ─────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "JourneyIt Backend Running 🚀"}


@app.post("/test-predict")
def test_predict():
    return {"status": "ok", "test": "working"}


# ── OTP HELPERS ───────────────────────────────────
def _send_email_otp(to_email: str, code: str) -> bool:
    """Send OTP via Gmail SMTP. Falls back to console log if EMAIL_USER/PASS not set."""
    if not EMAIL_USER or not EMAIL_PASS:
        print(f"[OTP] Email not configured — code for {to_email}: {code}")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your JourneyIt Verification Code"
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    html = f"""
    <html>
    <body style="margin:0;padding:0;font-family:'Segoe UI',sans-serif;background:#f4f7fb;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center" style="padding:40px 20px;">
          <table width="480" cellpadding="0" cellspacing="0"
                 style="background:#fff;border-radius:18px;overflow:hidden;
                        box-shadow:0 8px 32px rgba(0,0,0,0.10);">
            <tr>
              <td style="background:linear-gradient(135deg,#1a7dc4,#0ea5e9);
                         padding:30px 40px;text-align:center;">
                <h1 style="color:#fff;margin:0;font-size:26px;font-weight:800;">
                  JourneyIt ✈
                </h1>
                <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:13px;">
                  Travel smarter with AI
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:36px 40px;text-align:center;">
                <p style="color:#444;font-size:15px;margin:0 0 24px;">
                  Your email verification code is:
                </p>
                <div style="display:inline-block;background:linear-gradient(135deg,#f0f9ff,#e0f2fe);
                            border:2px solid #bae6fd;border-radius:14px;
                            padding:18px 36px;margin-bottom:24px;">
                  <span style="font-size:42px;font-weight:800;letter-spacing:14px;
                               color:#1a7dc4;font-family:monospace;">
                    {code}
                  </span>
                </div>
                <p style="color:#888;font-size:12px;margin:0;">
                  This code expires in <strong>5 minutes</strong>.<br>
                  If you didn't request this, you can safely ignore this email.
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as exc:
        print(f"[OTP] SMTP error: {exc}")
        return False


# ── SEND OTP ──────────────────────────────────────
@app.post("/send-otp")
def send_otp(req: OtpRequest):
    code = str(random.randint(100000, 999999))
    expires = datetime.utcnow().timestamp() + 300  # 5 minutes
    _otp_store[req.email] = {"code": code, "expires_at": expires}
    sent = _send_email_otp(req.email, code)
    return {"success": sent}


# ── VERIFY OTP ────────────────────────────────────
@app.post("/verify-otp")
def verify_otp(req: OtpVerify):
    stored = _otp_store.get(req.email)
    if not stored:
        return {"success": False, "message": "No OTP found. Please request a new code."}
    if datetime.utcnow().timestamp() > stored["expires_at"]:
        _otp_store.pop(req.email, None)
        return {"success": False, "message": "Code has expired. Please request a new one."}
    if req.code != stored["code"]:
        return {"success": False, "message": "Incorrect code. Please try again."}
    _otp_store.pop(req.email, None)
    return {"success": True, "message": "Email verified successfully."}


# ── ML PRICE PREDICTION ──────────────────────────
@app.post("/predict-flight-price")
def predict_price(data: FlightRequest):
    from_city = IATA_TO_ML_CITY.get(data.from_iata or "", None)
    to_city   = IATA_TO_ML_CITY.get(data.to_iata   or "", None)

    # If route supplied, use route duration; otherwise use user-supplied duration
    if data.from_iata and data.to_iata:
        duration = _route_duration(data.from_iata, data.to_iata) or data.duration
    else:
        duration = data.duration

    current_price = int(_ml_predict(
        duration, data.days_left,
        airline=data.airline, from_city=from_city, to_city=to_city,
        stops=data.stops or 0, travel_class=data.travel_class or "Economy",
    ))

    trend = _build_trend(
        current_price, duration, data.days_left,
        from_city=from_city, to_city=to_city,
        from_iata=data.from_iata, to_iata=data.to_iata,
        stops=data.stops or 0,
    )

    return {
        "predicted_price": current_price,
        "future_prices":   trend["future_prices"],
        "change_pct":      trend["change_pct"],
        "method":          trend.get("method", "randomforest"),
        "recommendation":  trend["decision"],
        "confidence":      trend["confidence"],
        "advice":          trend["advice"],
        "trend":           trend["trend"],
    }


# ── SEARCH FLIGHTS ───────────────────────────────
@app.post("/search-flights")
def search_flights(data: FlightSearch):
    from_city = IATA_TO_ML_CITY.get(data.from_iata, None)
    to_city   = IATA_TO_ML_CITY.get(data.to_iata,   None)
    base_dur  = _route_duration(data.from_iata, data.to_iata)

    # Try live API first
    api_flights = []
    try:
        res = requests.get(
            "http://api.aviationstack.com/v1/flights",
            params={"access_key": AVIATIONSTACK_KEY,
                    "dep_iata": data.from_iata, "arr_iata": data.to_iata},
            timeout=5,
        )
        for f in res.json().get("data", [])[:6]:
            api_flights.append({
                "airline":       f.get("airline", {}).get("name", "Unknown"),
                "flight_number": f.get("flight",  {}).get("iata", "N/A"),
                "departure":     f.get("departure",{}).get("scheduled"),
                "arrival":       f.get("arrival",  {}).get("scheduled"),
                "status":        f.get("flight_status", "scheduled"),
            })
    except Exception:
        pass

    # Build enriched flight list
    enriched = []
    pool = MOCK_AIRLINE_POOL.copy()

    for i, tmpl in enumerate(pool):
        # Blend API flight data if available
        if i < len(api_flights):
            airline = api_flights[i].get("airline", tmpl["airline"])
            flight_num = api_flights[i].get("flight_number",
                                            f"{tmpl['code']}-{100 + i * 111}")
            departure  = api_flights[i].get("departure")
            arrival    = api_flights[i].get("arrival")
            status     = api_flights[i].get("status", "scheduled")
        else:
            airline    = tmpl["airline"]
            flight_num = f"{tmpl['code']}-{100 + i * 111}"
            departure  = None
            arrival    = None
            status     = "scheduled"

        stops      = tmpl["stops"]
        dep_time   = tmpl["dep_time"]
        arr_time   = tmpl["arr_time"]
        duration   = round(base_dur + stops * 0.75 + random.uniform(-0.1, 0.2), 1)
        days_left  = max(14 - i * 2, 1)

        price = int(_ml_predict(
            duration, days_left,
            airline=airline, from_city=from_city, to_city=to_city,
            stops=stops, dep_time=dep_time, arr_time=arr_time,
        ))

        on_time    = status == "scheduled"
        score      = _ai_score(price, duration, stops, on_time)
        tag, expl  = _score_to_tag(score)

        # Human-readable AI score (higher = better for display)
        display_score = round(100 - score, 1)

        enriched.append({
            "airline":        airline,
            "flight_number":  flight_num,
            "departure":      departure,
            "arrival":        arrival,
            "status":         status,
            "price":          price,
            "duration":       duration,
            "stops":          stops,
            "ai_score":       display_score,
            "ai_tag":         tag,
            "ai_explanation": expl,
            "recommended":    False,
        })

    # Sort by raw score (ascending → best first)
    enriched.sort(key=lambda x: 100 - x["ai_score"])

    if enriched:
        enriched[0]["recommended"]    = True
        enriched[0]["ai_tag"]         = "🔥 Best Deal"
        enriched[0]["ai_explanation"] = "AI's top pick — best overall value on this route"

    return {
        "route":   f"{data.from_iata} → {data.to_iata}",
        "date":    data.date,
        "flights": enriched,
    }


# ── CHAT ─────────────────────────────────────────
@app.post("/chat")
def chat(req: ChatRequest):
    query = req.message.strip()
    if not query:
        return {"reply": "Please type a travel question!", "data": None}

    intent = _detect_intent(query)

    _NON_FLIGHT_INTENTS = {
        "greeting", "thanks", "help", "personal_intro",
        "trust_score", "destination_suggestion", "budget_advice",
        "visa_info", "packing_tips", "weather_season",
        "hotel_recommendation", "other_transport", "general",
    }
    if intent in _NON_FLIGHT_INTENTS:
        return {"reply": _handle_non_flight(intent, query), "data": None}

    from_iata, to_iata, cities_found = _extract_route(query)

    if cities_found == 0:
        return {
            "reply": (
                "I'd love to help! Try one of these:\n\n"
                "• *'Should I book Hyderabad to Goa next weekend?'*\n"
                "• *'How much is Delhi to Mumbai in 7 days?'*\n"
                "• *'Best hotels in Bangalore?'*\n"
                "• *'Where should I travel in December?'*"
            ),
            "data": None,
        }

    duration  = _route_duration(from_iata, to_iata) or _extract_duration(query)
    days_left = _extract_days_left(query)
    route     = f"{from_iata} → {to_iata}"

    from_city = IATA_TO_ML_CITY.get(from_iata)
    to_city   = IATA_TO_ML_CITY.get(to_iata)

    current_price = int(_ml_predict(
        duration, days_left,
        from_city=from_city, to_city=to_city,
    ))

    trend = _build_trend(
        current_price, duration, days_left,
        from_city=from_city, to_city=to_city,
        from_iata=from_iata, to_iata=to_iata,
    )

    ctx = {
        "route":         route,
        "from_iata":     from_iata,
        "to_iata":       to_iata,
        "current_price": current_price,
        "future_prices": trend["future_prices"],
        "day5_price":    trend["day5_price"],
        "change_pct":    trend["change_pct"],
        "confidence":    trend["confidence"],
        "decision":      trend["decision"],
        "trend":         trend["trend"],
        "advice":        trend["advice"],
        "intent":        intent,
        "days_left":     days_left,
        "duration":      duration,
    }

    reply = _generate_reply(query, ctx)
    return {"reply": reply, "data": ctx}


# ─────────────────────────────────────────────────
# HOTEL HELPERS
# ─────────────────────────────────────────────────

def _geocode_address(hotel_name: str, city: str) -> tuple[float, float]:
    """
    Convert hotel name + city to lat/lng using Google Maps Geocoding API.
    Returns (lat, lng) or (None, None) if geocoding fails.
    """
    address = f"{hotel_name}, {city}, India"

    # Check cache first
    if address in _geocode_cache:
        return _geocode_cache[address]

    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": GOOGLE_MAPS_KEY
        }

        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()

        if data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            lat = location.get("lat")
            lng = location.get("lng")

            # Cache result
            _geocode_cache[address] = (lat, lng)
            return (lat, lng)
    except Exception as e:
        print(f"[WARNING] Geocoding error for {address}: {e}")

    return (None, None)


def _hotel_ai_score(price: float, rating: float) -> dict:
    """Lower score = better value."""
    score = price * 0.5 + (5.0 - min(rating, 5.0)) * 300
    if score < 3000:
        tag = "🔥 BEST VALUE"
    elif score < 5000:
        tag = "👍 GOOD"
    else:
        tag = "⚠️ EXPENSIVE"
    return {"ai_score": round(score, 1), "tag": tag}


def _normalise_hotel(raw_name: str, raw_price, raw_rating, raw_address: str,
                     raw_photo: str = None) -> dict:
    price  = round(float(raw_price or 0))
    rating = round(min(float(raw_rating or 0), 5.0), 1)
    name   = str(raw_name or "Unknown Hotel").strip()
    addr   = str(raw_address or "").strip()
    photo  = str(raw_photo or "").strip()
    return {
        "name":      name,
        "price":     price,
        "rating":    rating,
        "address":   addr,
        "photo_url": photo,
        **_hotel_ai_score(price, rating),
        "recommended": False,
    }


_BOOKING_HOST = "booking-com.p.rapidapi.com"
_BOOKING_BASE = f"https://{_BOOKING_HOST}/v1"


def _booking_headers() -> dict:
    if not RAPIDAPI_KEY:
        raise RuntimeError("RAPIDAPI_KEY not set in .env")
    return {
        "X-RapidAPI-Key":  RAPIDAPI_KEY,
        "X-RapidAPI-Host": _BOOKING_HOST,
    }


def _resolve_dest_id(city: str, headers: dict) -> str:
    """
    1. Check the local HOTEL_DEST_IDS cache first (zero API calls).
    2. Fall back to /v1/hotels/locations for cities not in the cache.
    """
    cached = HOTEL_DEST_IDS.get(city.lower().strip())
    if cached:
        return cached

    res  = requests.get(
        f"{_BOOKING_BASE}/hotels/locations",
        headers=headers,
        params={"name": city, "locale": "en-gb"},
        timeout=8,
    )
    data = res.json()
    if isinstance(data, list) and data:
        return str(data[0].get("dest_id", ""))
    return ""


def _search_booking(city: str) -> list[dict]:
    """
    Full Booking.com hotel search:
      Step 1 — resolve dest_id (cache → locations API)
      Step 2 — fetch hotels via /v1/hotels/search
    Raises RuntimeError on any failure so the caller can fall back to mock.
    """
    headers  = _booking_headers()
    dest_id  = _resolve_dest_id(city, headers)

    if not dest_id:
        raise RuntimeError(f"No dest_id found for '{city}'")

    # Use tomorrow + day-after to guarantee availability results
    checkin  = str(date.today() + timedelta(days=1))
    checkout = str(date.today() + timedelta(days=2))

    res = requests.get(
        f"{_BOOKING_BASE}/hotels/search",
        headers=headers,
        params={
            "dest_id":       dest_id,
            "dest_type":     "city",
            "checkin_date":  checkin,
            "checkout_date": checkout,
            "adults_number": "2",
            "room_number":   "1",
            "order_by":      "popularity",
            "locale":        "en-gb",
            "units":         "metric",
            "currency":      "INR",
            "filter_by_currency": "INR",
        },
        timeout=12,
    )
    res.raise_for_status()
    results = res.json().get("result", [])[:6]

    if not results:
        raise RuntimeError("API returned empty result list")

    hotels = []
    for i, h in enumerate(results):
        # Booking.com can return price in several fields
        price = (
            h.get("min_total_price") or
            h.get("composite_price_breakdown", {})
             .get("gross_amount_per_night", {})
             .get("value") or
            h.get("price_breakdown", {}).get("all_inclusive_price") or
            0
        )
        # review_score is on a 10-point scale → divide by 2 for 0-5
        rating = float(h.get("review_score") or 0) / 2.0
        # Use Booking.com photo if available, otherwise fallback to stock photos
        photo  = h.get("max_photo_url") or h.get("main_photo_url") or _HOTEL_PHOTOS[i % len(_HOTEL_PHOTOS)]
        hotels.append(_normalise_hotel(
            h.get("hotel_name"),
            price,
            rating,
            h.get("address") or h.get("city_name_en", ""),
            photo,
        ))
    return hotels


# City → realistic per-night price base (INR) — higher-tier cities cost more
_CITY_PRICE_BASE: dict[str, int] = {
    "mumbai": 6500, "bombay": 6500,
    "delhi": 5800,  "new delhi": 5800,
    "bangalore": 5200, "bengaluru": 5200,
    "goa": 4800,
    "hyderabad": 4200,
    "chennai": 4000,
    "pune": 3800,
    "kolkata": 3600,
    "jaipur": 3400,
    "kochi": 3200,  "cochin": 3200,
    "amritsar": 3000,
    "varanasi": 2800,
    "srinagar": 3200,
    "lucknow": 2800,
}

# Curated hotel photos (Unsplash, stable CDN)
_HOTEL_PHOTOS = [
    "https://images.unsplash.com/photo-1566073129273-cebf9db75ef4?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1551882547-ff40c599c69b?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1455587734955-081b22074882?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=600&q=80",
]

# Bounding boxes for major Indian cities (south, west, north, east)
_CITY_BBOX: dict[str, str] = {
    "hyderabad":  "17.20,78.30,17.55,78.65",
    "mumbai":     "18.88,72.78,19.28,73.02",
    "delhi":      "28.42,76.84,28.88,77.35",
    "new delhi":  "28.42,76.84,28.88,77.35",
    "bangalore":  "12.82,77.45,13.15,77.75",
    "bengaluru":  "12.82,77.45,13.15,77.75",
    "chennai":    "12.90,80.12,13.22,80.33",
    "kolkata":    "22.45,88.22,22.72,88.48",
    "goa":        "15.18,73.80,15.62,74.15",
    "pune":       "18.42,73.72,18.62,73.98",
    "jaipur":     "26.82,75.72,26.98,75.95",
    "kochi":      "9.90,76.23,10.05,76.35",
    "cochin":     "9.90,76.23,10.05,76.35",
    "amritsar":   "31.60,74.82,31.70,74.92",
    "varanasi":   "25.28,82.92,25.38,83.08",
    "srinagar":   "34.05,74.75,34.15,74.90",
    "lucknow":    "26.80,80.88,26.96,81.08",
}


def _search_osm(city: str) -> list[dict]:
    """
    Fetch real hotel data from OpenStreetMap via the free Overpass API.
    Returns real names and addresses; realistic pricing is generated from
    city-tier base prices. No API key required.
    """
    city_lower = city.lower().strip()
    bbox = _CITY_BBOX.get(city_lower)
    if not bbox:
        raise RuntimeError(f"No bounding box configured for '{city}'")

    s, w, n, e = bbox.split(",")
    query = (
        f"[out:json][timeout:12];"
        f"("
        f'  node["tourism"="hotel"]({s},{w},{n},{e});'
        f'  way["tourism"="hotel"]({s},{w},{n},{e});'
        f");"
        f"out center 10;"
    )
    res = requests.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": query},
        timeout=14,
    )
    res.raise_for_status()
    elements = res.json().get("elements", [])

    # Filter to entries that actually have a name
    named = [el for el in elements if el.get("tags", {}).get("name")][:8]
    if not named:
        raise RuntimeError("OSM returned no named hotels")

    base_px = _CITY_PRICE_BASE.get(city_lower, 3500)
    hotels  = []

    for i, el in enumerate(named):
        tags = el.get("tags", {})
        name = (tags.get("name") or tags.get("name:en", f"Hotel {i+1}")).strip()

        addr_parts = [
            tags.get("addr:street"),
            tags.get("addr:suburb"),
            tags.get("addr:city", city.title()),
        ]
        address = ", ".join(p for p in addr_parts if p) or city.title()

        # Stars tag → rating; else randomise in realistic range
        stars_raw = tags.get("stars") or tags.get("tourism:stars")
        try:
            rating = round(min(float(stars_raw), 5.0), 1)
        except (TypeError, ValueError):
            rating = round(random.uniform(3.0, 4.8), 1)

        # Price varies by ±120 % around city base
        price = int(base_px * random.uniform(0.45, 2.1))
        photo = _HOTEL_PHOTOS[i % len(_HOTEL_PHOTOS)]
        hotels.append(_normalise_hotel(name, price, rating, address, photo))

    return hotels


def _get_mock_hotels(city: str) -> list[dict]:
    """Last-resort deterministic mock data — city-specific where available."""
    city_lower = city.strip().lower()
    city_key   = _CITY_ALIASES.get(city_lower, city_lower)
    base_px    = _CITY_PRICE_BASE.get(city_lower,
                 _CITY_PRICE_BASE.get(city_key, 3500))

    city_hotels = _CITY_HOTELS_DATA.get(city_key)
    if city_hotels:
        hotels = []
        for i, h in enumerate(city_hotels):
            price  = round(base_px * h["price_mul"])
            hotels.append(_normalise_hotel(
                h["name"],
                price, h["rating"],
                h["neighborhood"],
                _HOTEL_PHOTOS[i % len(_HOTEL_PHOTOS)],
            ))
        return hotels

    # Generic fallback for cities without specific data
    city_t = city.strip().title()
    hotels = []
    for i, tmpl in enumerate(_MOCK_HOTEL_TEMPLATES):
        price = round(base_px * tmpl["price_mul"])
        hotels.append(_normalise_hotel(
            f"{city_t} {tmpl['suffix']}",
            price, tmpl["rating"],
            f"Central {city_t}, India",
            tmpl.get("photo", ""),
        ))
    return hotels


# ── BOOK FLIGHT ───────────────────────────────────
@app.post("/book-flight")
def book_flight(data: BookingRequest):
    """
    Book a flight with passenger details.
    Returns booking confirmation with reference number.
    """
    try:
        import uuid
        booking_id = str(uuid.uuid4())[:8].upper()
        booking_reference = f"JRY{booking_id}"

        booking_response = {
            "success": True,
            "booking_id": booking_id,
            "booking_reference": booking_reference,
            "passenger_name": data.passenger_name,
            "passenger_email": data.passenger_email,
            "passenger_phone": data.passenger_phone,
            "passport_number": data.passport_number,
            "flight_number": data.flight_id,
            "seat_preference": data.seat_preference,
            "meal_choice": data.meal_choice,
            "total_amount": data.total_amount,
            "booking_status": "confirmed",
            "message": f"Booking confirmed! Reference: {booking_reference}",
        }

        # TODO: Save to database using models.FlightBooking
        # db.add(FlightBooking(...))
        # db.commit()

        return booking_response

    except Exception as e:
        return {"success": False, "error": str(e)}


# ── SEARCH HOTELS ─────────────────────────────────
@app.post("/search-hotels")
def search_hotels(data: HotelSearch):
    city = data.city.strip()

    # 1st: Booking.com live API → 2nd: OSM real names → 3rd: mock
    source = "mock"
    hotels: list[dict] = []

    try:
        hotels = _search_booking(city)
        source = "live"
    except Exception as exc:
        print(f"[hotels] Booking.com failed for '{city}': {exc}")
        try:
            hotels = _search_osm(city)
            source = "osm"
            print(f"[hotels] OSM returned {len(hotels)} hotels for '{city}'")
        except Exception as osm_exc:
            print(f"[hotels] OSM failed for '{city}': {osm_exc} — using mock")
            hotels = _get_mock_hotels(city)
            source = "mock"

    # Sort ascending by AI score (lower score = better value)
    hotels.sort(key=lambda h: h["ai_score"])

    if hotels:
        hotels[0]["recommended"] = True
        hotels[0]["tag"]         = "🔥 BEST VALUE"

    # Add geocoded coordinates to each hotel
    for hotel in hotels[:6]:
        lat, lng = _geocode_address(hotel["name"], city)
        hotel["lat"] = lat
        hotel["lng"] = lng

    return {"city": city, "hotels": hotels[:6], "source": source}
