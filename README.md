# JourneyIt ✈️

## AI-Powered Travel Intelligence Platform

JourneyIt is a full-stack AI-powered travel platform designed to help users make smarter travel decisions using Machine Learning, real-time APIs, and intelligent recommendation systems.

The platform predicts flight prices, analyzes fare trends, recommends the best booking time, provides hotel discovery, and offers conversational AI-based travel assistance — all within a modern travel experience.

---

# 🌍 What JourneyIt Does

JourneyIt combines:
- ✈️ Flight Price Prediction
- 📈 Fare Trend Forecasting
- 🏨 Smart Hotel Discovery
- 🤖 Conversational AI Assistance
- 🧠 Intelligent Booking Recommendations
- 🔐 Secure Authentication System

The goal of the project is to reduce uncertainty in travel booking decisions using AI and data-driven recommendations.

---

# 🚀 Core Features

## ✈️ Smart Flight Search
Users can:
- Search flights between cities
- View AI-recommended flights
- Compare prices and durations
- Get booking recommendations

### AI Recommendation Types
- 🔥 BOOK NOW
- 👀 MONITOR
- ⏳ WAIT

The system analyzes future price trends before suggesting the best action.

---

## 📈 Flight Price Prediction

JourneyIt predicts future flight prices using Machine Learning models.

### Features:
- 7-day future fare forecasting
- Trend analysis
- Confidence scoring
- Historical pattern learning

Example:
```text
Today Price: ₹4,500
Predicted in 5 Days: ₹4,050

Recommendation:
WAIT — Save approximately ₹450
```

---

# 🧠 Machine Learning Architecture

JourneyIt uses a **Hybrid ML Architecture**.

## Primary Model — LSTM
Used for:
- Time-series forecasting
- Learning fare movement patterns
- Detecting price trends

### Advantages
- High prediction accuracy
- Learns temporal patterns
- Better trend forecasting

### Performance
- Accuracy: ~92%

---

## Fallback Model — RandomForest

Used when:
- LSTM model unavailable
- Historical sequence insufficient
- Faster predictions required

### Advantages
- Fast inference
- Reliable fallback
- Lower computational cost

### Performance
- Accuracy: ~75–80%

---

# 🔄 Hybrid Prediction Flow

```text
User Flight Request
        ↓
Check LSTM Availability
        ↓
 ┌───────────────┬────────────────┐
 │               │                │
LSTM         RandomForest      Mock
Primary      Fallback          Emergency
Prediction   Prediction        Response
```

This architecture ensures predictions are always available even if one system fails.

---

# 🏨 Smart Hotel Discovery

JourneyIt includes an intelligent hotel search engine with a multi-level fallback system.

### Features
- Hotel recommendations
- AI trust scoring
- Hotel value analysis
- Real-time + fallback data sources

### Hotel Data Sources
1. Booking.com API
2. OpenStreetMap API
3. Mock fallback data

---

# 🤖 Conversational AI Assistant

JourneyIt includes an AI-powered travel chatbot capable of handling multiple travel-related queries.

### Supported Intents
- Flight booking advice
- Budget travel suggestions
- Destination recommendations
- Hotel recommendations
- Weather & seasonal advice
- Packing tips
- Visa information

### Example Queries
```text
Should I book Hyderabad to Mumbai flights now?

Suggest a budget trip for summer.

Find good hotels in Goa.
```

---

# 🔐 Authentication System

JourneyIt uses:
- Firebase Authentication
- OTP Email Verification
- Secure Login & Signup Flow

### Authentication Features
- Email verification
- OTP validation
- Protected routes
- User session management

---

# 📊 Data Visualization

The frontend provides interactive visualizations for:
- Price trend charts
- Fare movement graphs
- AI confidence indicators
- Recommendation panels

---

# 🏗️ Complete System Architecture

```text
                        USER
                          ↓
                React Frontend UI
                          ↓
                Axios API Requests
                          ↓
                  FastAPI Backend
                          ↓
        ┌─────────────────────────────────┐
        │                                 │
   ML Prediction Engine              Chat Engine
   (LSTM + RandomForest)             (AI Intents)
        │                                 │
        └─────────────────────────────────┘
                          ↓
                External API Layer
        ┌────────────┬────────────┬────────────┐
        │            │            │
 AviationStack   Booking.com   Gemini API
        │            │            │
        └────────────┴────────────┘
                          ↓
                     Firebase
```

---

# 🛠️ Tech Stack

# Frontend
- React
- React Router
- Axios
- Recharts
- Firebase Authentication

# Backend
- FastAPI
- Python
- Uvicorn
- REST APIs
- Pydantic

# Machine Learning
- TensorFlow / Keras
- Scikit-learn
- RandomForest
- LSTM Networks
- Pandas
- NumPy

# APIs & Services
- AviationStack API
- Booking.com API
- Google Gemini API
- Google Maps API
- Firebase

---

# 📂 Project Structure

```bash
JourneyIt/
│
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── context/
│   └── services/
│
├── backend/
│   ├── main.py
│   ├── models/
│   ├── datasets/
│   ├── utils/
│   └── train.py
│
├── ml_models/
│   ├── lstm_models/
│   ├── flight_price_model.pkl
│   └── model_columns.pkl
│
├── docs/
├── README.md
└── requirements.txt
```

---

# ⚙️ Installation & Setup

## 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/journeyit.git
cd journeyit
```

---

## 2️⃣ Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### Run Backend

```bash
uvicorn main:app --reload
```

Backend runs on:
```text
http://127.0.0.1:8000
```

---

## 3️⃣ Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs on:
```text
http://localhost:3000
```

---

# 🔑 Environment Variables

Create a `.env` file inside backend:

```env
AVIATIONSTACK_KEY=your_key
GEMINI_KEY=your_key
GOOGLE_MAPS_KEY=your_key
RAPIDAPI_KEY=your_key
EMAIL_USER=your_email
EMAIL_PASS=your_password
```

---

# 📡 Main API Endpoints

| Endpoint | Description |
|---|---|
| `/predict-flight-price` | Predict future flight prices |
| `/search-flights` | Search flights |
| `/search-hotels` | Hotel search |
| `/chat` | Conversational AI |
| `/send-otp` | Send OTP |
| `/verify-otp` | Verify OTP |

---

# 🔥 Key Highlights

- AI-powered travel intelligence
- Production-style architecture
- Hybrid ML prediction system
- Real-time + fallback infrastructure
- Conversational AI integration
- Scalable backend design
- Smart recommendation engine

---

# 📈 Future Improvements

- Payment gateway integration
- PostgreSQL + Redis
- Booking history
- Price alerts & notifications
- Mobile application
- Multi-language support
- Real-time booking system

---

# 👨‍💻 Author

## Salman Arif

Final Year Engineering Project  
AI-Powered Travel Intelligence Platform

---

# 📜 License

This project is for educational and research purposes.
