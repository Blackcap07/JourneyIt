# JourneyIt - Complete Architecture & Functionality Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [High-Level Architecture Diagrams](#high-level-architecture-diagrams)
3. [Complete System Architecture](#complete-system-architecture)
4. [Detailed Component Breakdown](#detailed-component-breakdown)
5. [Feature Matrix & Functionality Status](#feature-matrix)
6. [API Reference](#api-reference)
7. [Data Flow & Processing](#data-flow-processing)
8. [Database Schema & Data Models](#database-schema)
9. [Security & Authentication](#security-authentication)
10. [Deployment Architecture](#deployment-architecture)

---

## Project Overview

**JourneyIt** is a comprehensive AI-powered travel intelligence platform designed to optimize travel planning through:

### Core Capabilities
1. **ML-Powered Flight Price Prediction** - Forecast prices 7 days ahead with confidence scoring
2. **Intelligent Hotel Discovery** - Search 20+ Indian cities with AI trust scoring
3. **Conversational Travel AI** - Chat interface with 20+ travel-related intents
4. **Smart Budget Planning** - Allocate travel budget across flights, hotels, activities
5. **Destination Intelligence** - Seasonal recommendations with weather & visa info
6. **Trust Scoring System** - Detect fake reviews and authentic accommodations
7. **Real-time Flight Tracking** - Live flight data via AviationStack
8. **Multi-source Hotel Data** - Booking.com, OpenStreetMap, and curated databases

### Technology Stack Summary
```
Frontend:     React 19 + Firebase Auth
Backend:      FastAPI + Python 3.11
ML Engine:    scikit-learn RandomForest
Databases:    Firebase (auth), In-memory (OTP)
External:     Booking.com, AviationStack, Google Gemini, OpenStreetMap
```

---

## High-Level Architecture Diagrams

### System Architecture Overview
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                              │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Flights     │  │  Hotels      │  │  Chatbot     │  │  Booking     │   │
│  │  Page        │  │  Page        │  │  Interface   │  │  & Payment   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │  Budget      │  │  Destination │  │  Auth Modal  │                      │
│  │  Planner     │  │  Recommender │  │  (Firebase)  │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↑
                        AXIOS HTTP Client Layer
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY & ROUTING                               │
│                                                                              │
│  FastAPI Router (localhost:8000)                                           │
│  ├── /predict-flight-price        [ML Inference]                          │
│  ├── /search-flights              [Flight Discovery]                      │
│  ├── /search-hotels               [Hotel Search]                          │
│  ├── /chat                        [AI Chat]                               │
│  ├── /send-otp                    [Email Auth]                            │
│  └── /verify-otp                  [Email Auth Verify]                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↑
        ┌───────────────────────────┼───────────────────────────┐
        ↓                           ↓                           ↓
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  BUSINESS LOGIC  │      │   ML INFERENCE   │      │  CHAT ENGINE     │
│  LAYER           │      │   LAYER          │      │  (NLU)           │
│                  │      │                  │      │                  │
│ • Price Trends  │      │ • Flight Price   │      │ • Intent         │
│ • Hotel Scoring │      │   Model          │      │   Detection      │
│ • Route Mapping │      │ (RandomForest)   │      │ • Response       │
│ • City Lookups  │      │                  │      │   Generation     │
└──────────────────┘      └──────────────────┘      └──────────────────┘
        ↓                           ↓                           ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL API INTEGRATION LAYER                         │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ AviationStack   │  │ Booking.com API │  │ Google Gemini   │            │
│  │ (Real Flights)  │  │ (Hotel Search)  │  │ (AI Responses)  │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ OpenStreetMap   │  │ Gmail SMTP      │  │ Firebase Auth   │            │
│  │ (Real Hotels)   │  │ (OTP Email)     │  │ (User Identity) │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
        ↓                           ↓                           ↓
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  LIVE DATA       │      │  FALLBACK DATA   │      │  LOCAL DATA      │
│  (Real-time)     │      │  (OSM Hotels)    │      │  (Cached)        │
│                  │      │                  │      │                  │
│ • Flight Info    │      │ • Real Addresses │      │ • City Mappings  │
│ • Pricing        │      │ • Hotel Names    │      │ • Route Duration │
│ • Availability   │      │ • Reviews        │      │ • Airlines       │
└──────────────────┘      └──────────────────┘      └──────────────────┘
        ↓                           ↓                           ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MODELS & DATA LAYER                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ML Model: RandomForest (flight_price_model.pkl)                    │   │
│  │ - 100 estimators, trained on historical flight data               │   │
│  │ - Features: duration, days_left, airline, city, stops, class      │   │
│  │ - Accuracy: ~90%+ R² score on test data                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Data Stores:                                                        │   │
│  │ • /dataset/Flights.csv (training data)                             │   │
│  │ • In-memory OTP store (5-min expiry)                               │   │
│  │ • City price bases & aliases (20+ cities)                          │   │
│  │ • Hotel templates & neighborhood data                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Complete Request/Response Flow
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     USER INITIATES FLIGHT SEARCH                            │
│                    "Should I book HYD to BOM?"                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. FRONTEND PROCESSING                                                     │
│     • User types message in Chatbot component                              │
│     • Message sent to POST /chat endpoint with axios                       │
│     • Request: { message: "Should I book HYD to BOM?" }                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. BACKEND INTENT DETECTION (NLU)                                          │
│     _detect_intent(query) → keyword matching against 20+ intent patterns    │
│     Result: "booking_advice"                                               │
│                                                                              │
│     _extract_route(query) → scan CITY_MAP for city names                   │
│     Result: from_iata="HYD", to_iata="BOM"                                │
│                                                                              │
│     _extract_days_left(query) → regex parsing or defaults                 │
│     Result: days_left=7 (default)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. ML FEATURE PREPARATION                                                  │
│     • Route → Duration lookup: HYD→BOM = 1.5 hours                         │
│     • City codes → ML city names: HYD→"Hyderabad", BOM→"Mumbai"           │
│     • Create feature vector with one-hot encoding                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. ML INFERENCE (RandomForest Model)                                       │
│     • Load: flight_price_model.pkl, model_columns.pkl                     │
│     • Predict current price: ₹3,500 (for 7 days left, 1.5h flight)        │
│     • Predict day-7 price: ₹3,100 (using days_left-7)                     │
│     • Linear interpolation for 7-day trend                                 │
│     Result: [₹3500, ₹3428, ₹3356, ₹3285, ₹3213, ₹3141, ₹3100]           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. TREND ANALYSIS & DECISION MAKING                                        │
│     • Day-5 price: ₹3213 vs Current: ₹3500 = -8.2% drop                   │
│     • Decision threshold:                                                   │
│       - if change > 10%: "BOOK NOW"                                        │
│       - if change < -5%: "WAIT" ← THIS CASE                               │
│       - else: "MONITOR"                                                     │
│     • Confidence calculation based on price variance                       │
│     Result: decision="WAIT", confidence=78%                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  6. RESPONSE GENERATION (Optional Gemini API)                               │
│     If GEMINI_KEY available:                                               │
│       • Send context + flight data to Google Gemini 2.5-Flash             │
│       • Gemini generates conversational, data-driven response              │
│     Else:                                                                    │
│       • Use rule-based template response with data                         │
│                                                                              │
│     Response:                                                               │
│     "HYD → BOM — ⏳ WAIT                                                    │
│      Prices dropping 8.2% over 5 days (₹3500 → ₹3213).                   │
│      Waiting could save ₹287. Day-3: ₹3356, Day-5: ₹3213.                │
│      Hold off 3-5 days for lower fares.                                    │
│      Confidence: 78%"                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  7. RESPONSE TRANSMISSION TO FRONTEND                                       │
│     Response JSON:                                                          │
│     {                                                                        │
│       "reply": "HYD → BOM — ⏳ WAIT...",                                   │
│       "data": {                                                             │
│         "route": "HYD → BOM",                                              │
│         "current_price": 3500,                                             │
│         "future_prices": [3428, 3356, 3285, 3213, 3141, 3100],           │
│         "change_pct": -8.2,                                               │
│         "decision": "WAIT",                                                │
│         "confidence": 78                                                    │
│       }                                                                      │
│     }                                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  8. FRONTEND DISPLAY                                                        │
│     • Display message in chat bubbles                                      │
│     • Show trend chart using recharts library                              │
│     • Highlight WAIT recommendation in UI                                  │
│     • Add savings indicator: "Save ₹287 by waiting"                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Hotel Search Flow with Fallback Chain
```
User Query: "Show hotels in Goa"
           ↓
    ┌──────────────────────────────────────────┐
    │ Step 1: DESTINATION NORMALIZATION        │
    │ • Lowercase city name                     │
    │ • Check aliases (bengaluru→bangalore)     │
    │ • Lookup city price base (goa=₹4800)     │
    └──────────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────────┐
    │ Step 2a: TRY BOOKING.COM (LIVE API)      │
    │ • Resolve destination ID via cache       │
    │ • If not cached: call locations API      │
    │ • Search hotels for checkin+1, checkout+2│
    │ • Extract: name, price, rating, photo    │
    └──────────────────────────────────────────┘
           ↓
    ┌─ SUCCESS? ──┬─ FAIL? ──────────────────┐
    │             │                           │
    ↓             ↓                           │
  DISPLAY    Step 2b: TRY OSM               │
  (Booking)  • Query Overpass API            │
             • Fetch hotels within bbox      │
             • Real hotel names + addresses  │
             • Generate pricing from base    │
             └─┬──────────────────────┬────┐
               │                      │    │
            SUCCESS?            FAIL? │    │
               ↓                      ↓    │
             DISPLAY            Step 2c:   │
             (OSM)              MOCK DATA  │
                                • Load     │
                                  city-    │
                                  specific │
                                  templates│
                                └─────────┬┘
                                     ↓
                                  DISPLAY
                                  (Mock)
```

---

## Complete System Architecture

### 1. BACKEND LAYER - Detailed Breakdown

#### 1.1 Flight Price Prediction Module

**Location**: `backend/main.py:987-1016`

**How It Works**:
```
User Input:
  duration: 2.5 hours
  days_left: 7 days
  from_iata: "HYD" (Hyderabad)
  to_iata: "BOM" (Mumbai)
  
           ↓
           
Feature Transformation:
  1. Map IATA codes to ML city names
     HYD → "Hyderabad"
     BOM → "Mumbai"
  
  2. Create pandas DataFrame with model_columns
     Columns: 600+ one-hot encoded features
  
  3. Set feature values:
     df["duration"] = 2.5
     df["days_left"] = 7
     df["airline_IndiGo"] = 1  (if airline="IndiGo")
     df["source_city_Hyderabad"] = 1
     df["destination_city_Mumbai"] = 1
     df["stops_zero"] = 1
     df["class_Economy"] = 1
     ...rest are 0
           ↓
           
ML Inference:
  1. Load RandomForest model from pickle
  2. Call model.predict(feature_vector)
  3. Get predicted price: ₹3,500
           ↓
           
Trend Forecasting:
  1. Predict price for day-7: ₹3,100
  2. Linear interpolation between current & day-7
  3. Generate 7-day forecast: [3500, 3428, 3356, 3285, 3213, 3141, 3100]
           ↓
           
Decision Logic:
  change_pct = ((3213 - 3500) / 3500) * 100 = -8.2%
  
  if change_pct > 10:     "BOOK NOW"  (prices rising, lock in now)
  elif change_pct < -5:   "WAIT"      (prices dropping, wait 3-5 days)
  else:                   "MONITOR"   (stable, no urgency)
           ↓
           
Response:
  {
    "predicted_price": 3500,
    "future_prices": [3428, 3356, 3285, 3213, 3141, 3100],
    "change_pct": -8.2,
    "recommendation": "WAIT",
    "confidence": 78,
    "advice": "Waiting ~5 days could save you ₹287"
  }
```

**Model Training** (`train.py`):
```
Dataset: Flights.csv
├─ Features: airline, source_city, departure_time, stops, 
│            arrival_time, destination_city, class, duration, days_left
├─ Target: price (regression)
├─ Rows: ~10,000 flight records
└─ Processing:
   1. Drop unnamed columns
   2. One-hot encode: airline, source_city, stops, class, times
   3. Split: 80% train, 20% test
   4. Train: RandomForest(n_estimators=100, random_state=42)
   5. Evaluate: R² score ~0.92
   6. Save: flight_price_model.pkl, model_columns.pkl
```

#### 1.2 Hotel Search Module

**Three-Tier Fallback Architecture**:

**Tier 1: Booking.com API** (Lines 1253-1315)
```python
def _search_booking(city: str):
    """
    Step 1: Resolve destination ID
      - Check cache (HOTEL_DEST_IDS dict)
      - If miss: call /v1/hotels/locations
      - Get dest_id for city (e.g., "-2103924" for Hyderabad)
    
    Step 2: Build search parameters
      - Check-in: today + 1 day
      - Check-out: today + 2 days
      - Adults: 2, Rooms: 1
      - Currency: INR, Locale: en-gb
    
    Step 3: Call /v1/hotels/search
      - Returns up to 100 results
      - Extract: name, price, rating, photo
    
    Step 4: Normalize data
      - Price: various fields → min_total_price
      - Rating: booking's 10-point → 5-point scale
      - Photo: max_photo_url or main_photo_url
    
    Returns: list[dict] with 6 hotel objects
    """
```

**Tier 2: OpenStreetMap/Overpass API** (Lines 1368-1427)
```python
def _search_osm(city: str):
    """
    Used when Booking.com fails
    
    Data Source: OpenStreetMap (free, no API key)
    Query: All hotels (tourism=hotel tag) within city bbox
    
    Bounding boxes configured for 16 cities:
    - Hyderabad: "17.20,78.30,17.55,78.65" (S,W,N,E)
    - Mumbai: "18.88,72.78,19.28,73.02"
    - Delhi: "28.42,76.84,28.88,77.35"
    ... etc
    
    Processing:
    1. Query Overpass API with bbox
    2. Extract hotel names, addresses, star ratings
    3. Generate prices from city base ± 120%
    4. Assign real photos from curated URL list
    
    Returns: list[dict] with 8 real hotel names
    """
```

**Tier 3: Mock Data** (Lines 1430-1461)
```python
Fallback when both APIs fail

City-specific templates (20+ cities):
  _CITY_HOTELS_DATA = {
    "goa": [
      {"name": "Baga Beach Resort", "price_mul": 2.2, "rating": 4.7},
      {"name": "The Calangute Palms", "price_mul": 1.6, "rating": 4.4},
      ... 6 hotels total per city
    ],
    "mumbai": [...],
    "delhi": [...],
    ...
  }

Generic fallback for unconfigured cities:
  _MOCK_HOTEL_TEMPLATES = [
    "Grand Palace" (premium),
    "Marriott" (upscale),
    "Regency" (mid-range),
    "Comfort Suites" (budget),
    "Budget Inn" (economy),
    "Elite Residency" (luxury),
  ]
```

**AI Hotel Scoring** (Lines 1189-1198):
```python
def _hotel_ai_score(price: float, rating: float):
    """
    Composite score for value optimization
    Lower score = better value
    
    Formula: price * 0.5 + (5.0 - rating) * 300
    
    Example 1:
      price: ₹2,000, rating: 4.7
      score = 2000*0.5 + (5-4.7)*300 = 1000 + 90 = 1090
      tag: 🔥 BEST VALUE
    
    Example 2:
      price: ₹8,000, rating: 3.2
      score = 8000*0.5 + (5-3.2)*300 = 4000 + 540 = 4540
      tag: ⚠️ EXPENSIVE
    
    Thresholds:
      score < 3000:  🔥 BEST VALUE
      score < 5000:  👍 GOOD
      score >= 5000: ⚠️ EXPENSIVE
    """
```

#### 1.3 Chat/Conversational AI Module

**Intent Detection System** (20+ Intents):

```
1. GREETING INTENTS
   Patterns: ["hi", "hello", "hey", "howdy", "greetings"]
   Response: Welcome message + feature list

2. FLIGHT INTENTS
   a) price_query
      Triggers: ["price", "cost", "how much", "fare"]
      Requires: route extraction + days_left
      Response: ML prediction + trend data
   
   b) flight_search
      Triggers: ["find flight", "search flight", "book flight"]
      Response: Flight results from AviationStack
   
   c) booking_advice
      Triggers: ["should i book", "is it good time", "book now"]
      Response: BOOK NOW / WAIT / MONITOR decision
   
   d) price_trend
      Triggers: ["trend", "forecast", "going up", "prediction"]
      Response: 7-day forecast chart + advice

3. TRAVEL ADVICE INTENTS
   a) destination_suggestion
      Triggers: ["where should i go", "recommend destination"]
      Sub-intents by season:
         - Summer: Manali, Shimla, Coorg, Pondicherry
         - Winter: Goa, Rajasthan, Kerala, Andaman
         - Monsoon: Kerala, Coorg, Meghalaya, Goa
   
   b) budget_advice
      Triggers: ["budget trip", "cheap travel", "save money"]
      Response: 5 tips for affordable travel in India
   
   c) visa_info
      Triggers: ["visa", "passport", "travel documents"]
      Response: Visa requirements for 6 major destinations
   
   d) packing_tips
      Triggers: ["packing", "what to pack", "luggage"]
      Sub-types:
         - Beach: swimwear, sunscreen, waterproof case
         - Mountains: jacket, thermals, altitude tablets
         - Generic: documents, meds, power bank, shoes
   
   e) weather_season
      Triggers: ["best time to visit", "weather", "which month"]
      Response: Season-specific recommendations for cities

4. HOTEL INTENTS
   hotel_recommendation
   Triggers: ["hotel", "accommodation", "where to stay"]
   Response: Price ranges by tier + booking tips

5. TRUST INTENTS
   trust_score
   Triggers: ["fake review", "authentic", "safe hotel"]
   Response: AI trust score (68-94) + verdict

6. PERSONAL INTENTS
   personal_intro
   Triggers: ["my name is", "i am", "i'm", "call me"]
   Action: Extract name → personalized greeting

7. UTILITY INTENTS
   help, thanks, general
```

**Response Generation Pipeline**:
```
Input: "Should I book Goa flights next week?"
           ↓
    Intent Detection
           ↓
    Route Extraction (Goa → GOI, default from → HYD)
           ↓
    Time Extraction ("next week" → 7 days)
           ↓
    ML Context Building
    • Predict price
    • Calculate trend
    • Generate decision
           ↓
    Gemini API Call (if available)
    • Send system prompt
    • Include flight data
    • Get conversational response
           ↓
    If Gemini fails:
    • Use rule-based template
    • Insert data values
           ↓
    Response to User
```

#### 1.4 Authentication Module

**OTP Flow** (Lines 961-982):
```
Step 1: User enters email
        ↓
        POST /send-otp
        
Step 2: Generate random 6-digit code
        ↓
        Store in memory: _otp_store[email] = {code, expires_at}
        
Step 3: Send via Gmail SMTP
        • HTML template with gradient header
        • "JourneyIt ✈ Travel smarter with AI"
        • Code displayed in large monospace font
        • Expires in 5 minutes warning
        
Step 4: User copies code
        ↓
        POST /verify-otp with {email, code}
        
Step 5: Validate
        • Check if email in store
        • Check if not expired (datetime.utcnow() < expires_at)
        • Check if code matches
        
Step 6: Response
        Success: "Email verified successfully"
        Failure: "Incorrect code" / "Expired" / "No OTP found"
```

**Firebase Integration** (React):
- Uses Firebase Authentication SDK
- Email/password + Social sign-in ready
- AuthContext provides global user state
- Protected routes via AuthGuard component

---

### 2. ML MODELS LAYER - Detailed

#### Training Process

```
Input Data: Flights.csv (~10K rows)
├─ Columns: 
│  • Categorical: airline, source_city, destination_city, 
│                 departure_time, arrival_time, stops, class
│  • Numerical: duration, days_left
│  • Target: price
│
├─ Data Cleaning
│  └─ Remove: Unnamed index column, duplicate flight_iata
│
├─ Feature Engineering
│  └─ One-hot encoding:
│     • airline: 6 carriers → 6 binary columns
│     • source_city: 9 cities → 9 binary columns
│     • destination_city: 9 cities → 9 binary columns
│     • departure_time: 5 times → 5 binary columns
│     • arrival_time: 5 times → 5 binary columns
│     • stops: 3 categories → 3 binary columns
│     • class: 3 classes → 3 binary columns
│     TOTAL: 2 numerical + 43 categorical = 45 features
│
├─ Train/Test Split
│  ├─ Size: 80% train (~8K), 20% test (~2K)
│  └─ Random seed: 42 (reproducibility)
│
├─ Model Training
│  └─ RandomForestRegressor:
│     • Estimators: 100 trees
│     • Random state: 42
│     • Max depth: unlimited (default)
│     • Min samples: 1 (default)
│     • Training time: ~5 seconds
│
├─ Evaluation
│  ├─ R² Score on test: ~0.92
│  ├─ Mean Absolute Error: ~₹400
│  └─ Root Mean Squared Error: ~₹600
│
└─ Serialization
   ├─ flight_price_model.pkl (model artifact)
   └─ model_columns.pkl (feature names for inference)
```

#### Inference Process

```
When backend needs prediction:
1. Load pickled artifacts (lazy loaded once at startup)
2. Create empty DataFrame with all model_columns
3. Fill in user-provided features
4. Call model.predict(df)
5. Return float value (e.g., 3500.25)
6. Round to integer for display (₹3,500)
```

---

### 3. FRONTEND LAYER - Detailed Component Architecture

#### Component Hierarchy

```
App (Main Router)
├── AuthGuard (Authentication wrapper)
│   ├── AuthModal (Login/Signup/OTP)
│   │   ├── OTPInput (6-digit code input)
│   │   ├── PasswordInput (visibility toggle)
│   │   ├── PasswordStrengthBar (strength indicator)
│   │   └── PasswordChecklist (validation hints)
│   │
│   └── Main Content (if authenticated)
│       ├── FlightsPage
│       │   ├── FlightSearch (form inputs)
│       │   ├── FlightCard (repeating)
│       │   │   └── AI Score badge (🔥/👍/🤔/⚠️)
│       │   ├── TrendChart (recharts line chart)
│       │   └── RecommendationPanel (BOOK/WAIT/MONITOR)
│       │
│       ├── HotelsPage
│       │   ├── HotelSearch (city + filters)
│       │   ├── HotelCard (repeating)
│       │   │   ├── HotelBadge (trust score)
│       │   │   ├── Price display
│       │   │   └── Rating + reviews count
│       │   ├── HotelMap (leaflet map)
│       │   └── Filter/Sort controls
│       │
│       ├── HotelDetail (modal)
│       │   ├── Photo Gallery (image carousel)
│       │   ├── HotelMap (location)
│       │   ├── ReviewCard (repeating)
│       │   ├── TrustScore (AI trust badge)
│       │   ├── BookingSummary
│       │   └── Booking controls
│       │
│       ├── Chatbot
│       │   ├── MessageList (chat history)
│       │   │   ├── User message bubble
│       │   │   └── AI response bubble
│       │   └── InputField (message composition)
│       │
│       ├── BudgetPlanner
│       │   ├── Budget input
│       │   ├── Duration input
│       │   ├── Trip type selector
│       │   └── Breakdown display (flights, hotels, activities)
│       │
│       ├── Destination (Recommender)
│       │   ├── Budget input
│       │   ├── Type selector
│       │   └── Recommendations list
│       │
│       ├── PaymentPage
│       │   ├── Order summary
│       │   ├── PaymentModal
│       │   │   ├── Card form (placeholder)
│       │   │   └── Confirmation
│       │   └── Receipt display
│       │
│       └── Navbar
│           ├── Logo
│           ├── Tab navigation
│           └── User menu
```

#### Key Components Explanation

**FlightsPage.jsx** (16.8 KB, 467 lines)
- Flight search form with route & date pickers
- Real-time API calls to backend
- Displays 6 flights with AI scores
- Trend chart showing 7-day price forecast
- Recommendation banner (BOOK NOW / WAIT / MONITOR)
- Dark theme with gradient styling

**HotelsPage.jsx** (13.7 KB, 389 lines)
- City-based hotel search
- Shows 6 hotels sorted by AI score
- Hotel cards with:
  - Image + price
  - Rating + review count
  - Trust score badge
  - "View Details" button
- Map view (Leaflet)
- Filter by price range

**HotelDetail.jsx** (21.1 KB, 601 lines)
- Modal overlay with full hotel profile
- Photo gallery (carousel)
- Hotel location map
- Amenities & services list
- Guest reviews (RecommendationCard components)
- Trust score analysis
- Booking calendar
- Price display + "Book Now" button

**Chatbot.jsx** (11.2 KB, 320 lines)
- Conversational interface
- Message history with scrolling
- User messages: right-aligned, blue background
- AI responses: left-aligned, dark background
- Auto-scroll to latest message
- Loading indicator while waiting for response
- Supports text + rich data display (trend charts)

**PaymentModal.jsx** (placeholder)
- Card form (not integrated with real processor)
- Order summary
- Confirmation button
- Receipt display

**AuthModal.jsx** (15.7 KB, 449 lines)
- Email input + OTP verification flow
- Password strength validation
- Real-time feedback on password requirements
- OTP countdown timer
- Success/error messages

---

## Feature Matrix & Functionality Status

### Fully Implemented Features ✅

| Feature | Component | Status | Notes |
|---------|-----------|--------|-------|
| **Flight Price Prediction** | Backend ML | ✅ Complete | RandomForest model, 7-day forecast |
| **Flight Search** | FlightsPage + Backend | ✅ Complete | AviationStack + mock data |
| **Hotel Search** | HotelsPage + Backend | ✅ Complete | 3-tier fallback (Booking→OSM→Mock) |
| **Hotel Details** | HotelDetail Modal | ✅ Complete | Photos, map, reviews, booking |
| **Chat/Conversational AI** | Chatbot + Backend | ✅ Complete | 20+ intents, Gemini integration |
| **Budget Planner** | BudgetPlanner | ✅ Complete | 40% flights, 40% hotels, 20% activities |
| **Destination Recommender** | Destination | ✅ Complete | By budget & type, seasonal variants |
| **OTP Authentication** | AuthModal + Backend | ✅ Complete | Email verification, 5-min expiry |
| **Firebase Auth** | AuthGuard + Context | ✅ Complete | Email/password sign-in |
| **Price Trend Chart** | TrendChart (recharts) | ✅ Complete | 7-day visualization |
| **AI Trust Scoring** | TrustScore component | ✅ Complete | Hotel authenticity detection |
| **City Mappings** | Backend | ✅ Complete | 20+ cities with aliases |
| **Airline Data** | Backend | ✅ Complete | 6 carriers, realistic attributes |

### Partially Implemented Features 🟡

| Feature | Component | Status | Notes |
|---------|-----------|--------|-------|
| **Payment Integration** | PaymentModal | 🟡 Placeholder | UI ready, no real processor |
| **Booking Flow** | Multiple | 🟡 Partial | Can display summary, no database |
| **User Profiles** | AuthContext | 🟡 Basic | Firebase user object only |
| **Booking History** | Not implemented | ❌ Missing | Need database |
| **Reviews/Ratings** | ReviewCard | 🟡 Mock data | No user submission |
| **Wishlists** | Not implemented | ❌ Missing | No storage |
| **Price Alerts** | Not implemented | ❌ Missing | Would need scheduler |

### Features Requiring Work 📋

| Feature | Why Not Done | Priority |
|---------|-------------|----------|
| **Real Payment Gateway** | Requires Stripe/Razorpay integration | High |
| **Persistent Database** | Would use PostgreSQL + ORM | High |
| **Booking Storage** | Depends on database | High |
| **User Wishlists** | Needs database | Medium |
| **Real Email Notifications** | Partially done (OTP only) | Medium |
| **Price Alert Subscriptions** | Would need cron jobs | Medium |
| **Mobile App** | Would require React Native | Low |
| **Multi-language Support** | i18n integration | Low |

---

## API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Flight Price Prediction

**POST** `/predict-flight-price`

Request:
```json
{
  "duration": 2.5,
  "days_left": 7,
  "from_iata": "HYD",
  "to_iata": "BOM",
  "airline": "IndiGo",
  "stops": 0,
  "travel_class": "Economy"
}
```

Response:
```json
{
  "predicted_price": 3500,
  "future_prices": [3428, 3356, 3285, 3213, 3141, 3100],
  "change_pct": -8.2,
  "recommendation": "WAIT",
  "confidence": 78,
  "advice": "Prices expected to drop 8.2% — waiting ~5 days could save you ₹287",
  "trend": "decreasing"
}
```

#### 2. Flight Search

**POST** `/search-flights`

Request:
```json
{
  "from_iata": "DEL",
  "to_iata": "GOI",
  "date": "2026-05-15"
}
```

Response:
```json
{
  "route": "DEL → GOI",
  "date": "2026-05-15",
  "flights": [
    {
      "airline": "IndiGo",
      "flight_number": "6E-100",
      "departure": "2026-05-15T06:00:00",
      "arrival": "2026-05-15T08:15:00",
      "status": "scheduled",
      "price": 2800,
      "duration": 2.2,
      "stops": 0,
      "ai_score": 87.3,
      "ai_tag": "🔥 Best Deal",
      "ai_explanation": "Cheapest and fastest option on this route",
      "recommended": true
    },
    {
      "airline": "Air India",
      "flight_number": "AI-500",
      "price": 3200,
      "duration": 2.2,
      "stops": 0,
      "ai_score": 82.1,
      "ai_tag": "👍 Good Value",
      "recommended": false
    }
    // ... 4 more flights
  ]
}
```

#### 3. Hotel Search

**POST** `/search-hotels`

Request:
```json
{
  "city": "goa"
}
```

Response:
```json
{
  "city": "goa",
  "source": "booking",
  "hotels": [
    {
      "name": "Baga Beach Resort",
      "price": 4200,
      "rating": 4.7,
      "address": "Baga, North Goa",
      "photo_url": "https://...",
      "ai_score": 1050.0,
      "tag": "🔥 BEST VALUE",
      "recommended": true
    },
    {
      "name": "The Calangute Palms",
      "price": 3500,
      "rating": 4.4,
      "address": "Calangute, North Goa",
      "ai_score": 1650.0,
      "tag": "👍 GOOD",
      "recommended": false
    }
    // ... 4 more hotels
  ]
}
```

#### 4. Chat

**POST** `/chat`

Request:
```json
{
  "message": "Should I book Delhi to Mumbai flights next week?"
}
```

Response:
```json
{
  "reply": "✈️ **DEL → BOM** — 👁️ MONITOR\n\nPrices are relatively stable (3.2% change over 5 days). No urgent pressure to book, but don't wait too long.\n\n📅 Day-3 forecast: ₹2,450 | Day-5 forecast: ₹2,380\n\nWatch for 2–3 more days — a sudden spike would signal BOOK NOW.\n📊 AI Confidence: 81%",
  "data": {
    "route": "DEL → BOM",
    "from_iata": "DEL",
    "to_iata": "BOM",
    "current_price": 2400,
    "future_prices": [2410, 2425, 2450, 2380, 2365, 2350],
    "change_pct": 3.2,
    "decision": "MONITOR",
    "confidence": 81,
    "trend": "increasing"
  }
}
```

#### 5. Send OTP

**POST** `/send-otp`

Request:
```json
{
  "email": "user@example.com"
}
```

Response:
```json
{
  "success": true
}
```

#### 6. Verify OTP

**POST** `/verify-otp`

Request:
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

Response Success:
```json
{
  "success": true,
  "message": "Email verified successfully."
}
```

Response Failure:
```json
{
  "success": false,
  "message": "Incorrect code. Please try again."
}
```

---

## Data Flow & Processing

### Complete Feature Transformation Pipeline

```
FLIGHT PRICE PREDICTION PIPELINE:

Raw Input
├─ duration: 2.5
├─ days_left: 7
├─ from_iata: "HYD"
├─ to_iata: "BOM"
├─ airline: "IndiGo"
├─ stops: 0
└─ travel_class: "Economy"

         ↓

Validation & Normalization
├─ duration: float(2.5) → 2.5
├─ days_left: max(1, int(7)) → 7
├─ from_iata: uppercase("HYD") → "HYD"
├─ to_iata: uppercase("BOM") → "BOM"
├─ airline: normalize("IndiGo") → "IndiGo"
├─ stops: {0,1,2+} → "zero"
└─ travel_class: {Economy, Business} → "Economy"

         ↓

ML Feature Encoding
Create pandas DataFrame: df[model_columns]

Numerical Features:
├─ df["duration"] = 2.5
└─ df["days_left"] = 7

Categorical One-Hot Features:
├─ df["airline_IndiGo"] = 1, all other airline cols = 0
├─ df["source_city_Hyderabad"] = 1, others = 0
├─ df["destination_city_Mumbai"] = 1, others = 0
├─ df["stops_zero"] = 1, df["stops_one"] = 0, etc.
├─ df["class_Economy"] = 1, df["class_Business"] = 0
├─ df["departure_time_Morning"] = 0, ... (depends on input)
└─ df["arrival_time_Afternoon"] = 0, ... (depends on input)

All unspecified columns = 0

         ↓

ML Inference
Load: flight_price_model.pkl (RandomForest with 100 trees)
Input: Feature vector (45 dimensions)
Output: price prediction (float)

Example: 3500.25

         ↓

Post-Processing
├─ Round: 3500.25 → 3500
└─ Format: ₹3,500
```

### Hotel AI Scoring Pipeline

```
Raw Hotel Data
├─ name: "Baga Beach Resort"
├─ price: 4200
├─ rating: 4.7
├─ address: "Baga, North Goa"
└─ photo: "https://..."

         ↓

Normalization
├─ price: int(4200)
├─ rating: min(float(4.7), 5.0) → 4.7
├─ name: str.strip()
└─ address: str.strip()

         ↓

AI Scoring
score = price * 0.5 + (5.0 - rating) * 300
score = 4200 * 0.5 + (5.0 - 4.7) * 300
score = 2100 + 90 = 2190

         ↓

Tag Assignment
if score < 3000:    tag = "🔥 BEST VALUE"
elif score < 5000:  tag = "👍 GOOD"
else:               tag = "⚠️ EXPENSIVE"

Result: tag = "🔥 BEST VALUE"

         ↓

Sorting & Display
Sort all hotels by ai_score (ascending)
Mark top hotel as "recommended"
Update ai_tag to "🔥 BEST VALUE"
Display with visual emphasis
```

---

## Database Schema & Data Models

### Current Data Structures

```
1. OTP STORE (In-Memory)
   _otp_store: Dict[str, Dict]
   {
     "user@example.com": {
       "code": "123456",
       "expires_at": 1714214400.0  # Unix timestamp
     }
   }

2. CITY PRICE BASE
   _CITY_PRICE_BASE: Dict[str, int]
   {
     "mumbai": 6500,
     "delhi": 5800,
     "bangalore": 5200,
     "goa": 4800,
     ...
   }

3. CITY HOTELS DATA
   _CITY_HOTELS_DATA: Dict[str, List[Dict]]
   {
     "goa": [
       {
         "name": "Baga Beach Resort",
         "price_mul": 2.2,
         "rating": 4.7,
         "neighborhood": "Baga, North Goa"
       },
       ...
     ],
     ...
   }

4. HOTEL DEST IDS (Booking.com Cache)
   HOTEL_DEST_IDS: Dict[str, str]
   {
     "goa": "-2092535",
     "mumbai": "-2092174",
     ...
   }

5. ROUTE DURATIONS
   ROUTE_DURATION: Dict[Tuple[str, str], float]
   {
     ("DEL", "BOM"): 2.2,
     ("BOM", "BLR"): 1.5,
     ...
   }

6. AIRLINE POOL
   MOCK_AIRLINE_POOL: List[Dict]
   [
     {
       "airline": "IndiGo",
       "code": "6E",
       "stops": 0,
       "dep_time": "Morning",
       "arr_time": "Afternoon"
     },
     ...
   ]
```

### Recommended Production Schema (PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  firebase_uid VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Bookings table
CREATE TABLE bookings (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  booking_type ENUM('flight', 'hotel'),
  source_city VARCHAR(10),
  destination_city VARCHAR(10),
  check_in_date DATE,
  check_out_date DATE,
  price DECIMAL(10, 2),
  status ENUM('pending', 'confirmed', 'cancelled'),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Hotel searches (for analytics)
CREATE TABLE hotel_searches (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  city VARCHAR(50),
  search_date TIMESTAMP DEFAULT NOW()
);

-- Flight searches (for analytics)
CREATE TABLE flight_searches (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  from_city VARCHAR(10),
  to_city VARCHAR(10),
  travel_date DATE,
  search_date TIMESTAMP DEFAULT NOW()
);

-- Price history (for trend analysis)
CREATE TABLE price_history (
  id UUID PRIMARY KEY,
  from_iata VARCHAR(10),
  to_iata VARCHAR(10),
  price DECIMAL(10, 2),
  days_left INT,
  recorded_at TIMESTAMP DEFAULT NOW(),
  INDEX (from_iata, to_iata, recorded_at)
);

-- Reviews table
CREATE TABLE reviews (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  hotel_name VARCHAR(255),
  rating INT CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Wishlists
CREATE TABLE wishlists (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  hotel_name VARCHAR(255),
  city VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, hotel_name)
);

-- Price alerts
CREATE TABLE price_alerts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  from_iata VARCHAR(10),
  to_iata VARCHAR(10),
  target_price DECIMAL(10, 2),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Security & Authentication

### Current Implementation

```
✅ OTP-based email verification
   • 6-digit random code
   • 5-minute expiry
   • HTML email template
   • SMTP SSL (port 465)

✅ Firebase Authentication
   • Email/password sign-in
   • Firebase SDK integration
   • JWT tokens (Firebase-managed)
   • User state in React Context

✅ CORS Enabled
   • Allows all origins (development)
   • All methods, all headers

❌ API Key Exposure (Security Risk)
   • Keys hardcoded in main.py as defaults
   • Should always load from .env
   • Currently: os.getenv(KEY, HARDCODED_DEFAULT)
```

### Recommended Production Security

```
1. Environment Secrets
   • Use AWS Secrets Manager / HashiCorp Vault
   • Load at runtime, never commit
   • Rotate quarterly

2. API Authentication
   • JWT with RS256 (asymmetric)
   • 15-minute access token + refresh token
   • Rate limiting (100 req/min per IP)

3. Database
   • PostgreSQL with SSL
   • Parameterized queries (SQLAlchemy ORM)
   • Row-level security for multi-tenant

4. API Security
   • HTTPS/TLS 1.3+
   • CORS to specific domains only
   • Request signing (HMAC)
   • Input validation & sanitization

5. Payment Security
   • PCI DSS compliance
   • Use Stripe/Razorpay (never store cards)
   • Tokenization for recurring payments

6. Audit Logging
   • Log all auth attempts
   • Log API calls with user_id
   • Alert on suspicious patterns
```

---

## Deployment Architecture

### Local Development Stack

```
┌─────────────────────────────────────────────────┐
│          DEVELOPMENT ENVIRONMENT                │
├─────────────────────────────────────────────────┤
│                                                 │
│  Frontend:                                      │
│  npm start → http://localhost:3000             │
│  • React dev server with hot reload            │
│  • Source maps for debugging                   │
│  • Direct API calls to localhost:8000          │
│                                                 │
│  Backend:                                       │
│  uvicorn main:app --reload                     │
│  • http://localhost:8000                       │
│  • Auto-reload on file changes                 │
│  • Interactive docs at /docs                   │
│                                                 │
│  ML Models:                                     │
│  • flight_price_model.pkl loaded at startup    │
│  • In-memory data structures                   │
│                                                 │
│  External Services:                            │
│  • Firebase (live authentication)              │
│  • Booking.com RapidAPI (live)                 │
│  • AviationStack (live)                        │
│  • Gmail SMTP (live)                           │
│  • Google Gemini (live)                        │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Production Deployment (Recommended)

```
┌──────────────────────────────────────────────────────────────┐
│                    PRODUCTION STACK                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  FRONTEND:                                                   │
│  • Vercel / Netlify                                         │
│  • CDN: Cloudflare                                          │
│  • HTTPS: Let's Encrypt                                     │
│  • Environment: .env.production                             │
│                                                              │
│  BACKEND:                                                    │
│  • Docker container (Gunicorn + Uvicorn)                    │
│  • Hosted on: AWS EC2 / DigitalOcean / Heroku              │
│  • Load Balancer: nginx reverse proxy                       │
│  • HTTPS: Let's Encrypt (auto-renewed)                      │
│  • Environment: AWS Secrets Manager                         │
│                                                              │
│  DATABASE:                                                   │
│  • PostgreSQL on AWS RDS or managed service                │
│  • Automated backups (daily)                                │
│  • Read replicas for scaling                                │
│  • Connection pooling: PgBouncer                            │
│                                                              │
│  CACHING:                                                    │
│  • Redis for OTP store + session cache                      │
│  • Hotel search results cache (24h TTL)                     │
│  • Query results cache (1h TTL)                             │
│                                                              │
│  MONITORING:                                                 │
│  • Application: New Relic / Datadog                         │
│  • Logs: ELK Stack / CloudWatch                             │
│  • Alerts: PagerDuty                                        │
│                                                              │
│  CI/CD:                                                      │
│  • GitHub Actions for automated deploys                     │
│  • Test suite on every PR                                   │
│  • Docker image build & push                                │
│  • Blue-green deployment                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Docker Deployment

**Backend Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY backend/ .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/docs')"

# Run with Gunicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", "main:app"]
```

**Frontend Dockerfile**:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY journeyit-frontend/package*.json .
RUN npm install
COPY journeyit-frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Current Implementation Status

### What's Working ✅

1. **Core ML Engine**
   - ✅ RandomForest model inference
   - ✅ 7-day price forecasting
   - ✅ Confidence scoring
   - ✅ BOOK NOW / WAIT / MONITOR recommendations

2. **Hotel Search**
   - ✅ 3-tier fallback system
   - ✅ AI trust scoring
   - ✅ 20+ city templates
   - ✅ Real-time Booking.com integration
   - ✅ OpenStreetMap fallback

3. **Chat Intelligence**
   - ✅ 20+ intent recognition
   - ✅ Context extraction (route, time)
   - ✅ Gemini API integration
   - ✅ Rule-based fallback responses
   - ✅ Multi-intent handling

4. **Authentication**
   - ✅ Email OTP verification
   - ✅ Firebase integration
   - ✅ User state persistence
   - ✅ Protected routes

5. **Frontend UI**
   - ✅ Dark theme with gradients
   - ✅ Interactive charts (recharts)
   - ✅ Modal dialogs
   - ✅ Map integration (Leaflet)
   - ✅ Responsive design

### What Needs Work 🔧

1. **Payment Integration** (0% done)
   - Payment gateway (Stripe/Razorpay)
   - Card tokenization
   - Order tracking

2. **Database** (0% done)
   - PostgreSQL setup
   - User profiles
   - Booking history
   - Reviews & ratings

3. **Async Processing** (0% done)
   - Background jobs (email, notifications)
   - Price monitoring scheduler
   - Cache warming

4. **Testing** (0% done)
   - Unit tests for ML
   - Component tests for React
   - Integration tests for APIs

---

## Summary Statistics

### Codebase Metrics

```
Backend:
- Files: 1 main file (backend/main.py)
- Lines of Code: 1,495
- Functions: 30+
- API endpoints: 6
- External APIs integrated: 6

Frontend:
- Components: 30+
- Lines of Code: ~15,000
- CSS files: 25+
- Pages: 8+
- Dependencies: 15

ML Models:
- Models: 1 RandomForest
- Features: 45 (2 numerical + 43 categorical)
- Accuracy: ~90-92% R²
- Inference time: <100ms

Data:
- Cities covered: 20+ Indian cities
- Hotels per city: 6-60
- Airlines: 6 major carriers
- Routes: 20+ pre-configured

External Integrations:
- Booking.com: hotel pricing
- AviationStack: real flights
- Google Gemini: AI responses
- OpenStreetMap: hotel data
- Firebase: authentication
- Gmail SMTP: email delivery
```

---

**Last Updated**: April 27, 2026
**Project Stage**: MVP (Minimum Viable Product)
**Team Size**: Solo Developer
**Estimated LOC**: 20,000+
