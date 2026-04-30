import streamlit as st
import requests
import matplotlib.pyplot as plt

# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    page_title="JourneyIt AI Travel Assistant",
    page_icon="✈",
    layout="wide"
)

# -----------------------------
# STYLING & THEME
# -----------------------------

page_bg = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
    --amber: #F5A623;
    --amber-dark: #D4851A;
    --navy: #1A1F4B;
    --navy-light: #2D3561;
    --cream: #FDF6EC;
    --cream-dark: #F5EAD5;
    --coral: #E8604C;
    --white: #FFFFFF;
    --text-muted: #6B7280;
    --text-body: #374151;
}

html { scroll-behavior: smooth; }

[data-testid="stAppViewContainer"] {
    background: var(--white);
    color: var(--text-body);
}

[data-testid="stHeader"] {
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(0,0,0,0.06);
}

[data-testid="stToolbar"] {
    right: 2rem;
}

/* Main container styling */
.main {
    padding: 20px 40px;
}

/* Card styling */
.card {
    background: var(--white);
    border: 1.5px solid rgba(0,0,0,0.07);
    border-radius: 20px;
    padding: 36px 28px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: transform .25s, box-shadow .25s, border-color .25s;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 16px 48px rgba(0,0,0,0.09);
    border-color: var(--amber);
}

/* Button styling */
button {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    border-radius: 10px;
    transition: all .2s;
}

[data-testid="baseButton-primary"] {
    background: var(--amber) !important;
    color: var(--white) !important;
}

[data-testid="baseButton-primary"]:hover {
    background: var(--amber-dark) !important;
    transform: translateY(-2px);
}

/* Tab styling */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 2px solid rgba(0,0,0,0.1);
}

[data-testid="stTabs"] [role="tab"] {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    color: var(--text-body);
    border-bottom: 3px solid transparent;
    padding: 12px 24px;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--amber);
    border-bottom-color: var(--amber);
}

/* Heading styling */
h1 {
    font-family: 'Playfair Display', serif;
    font-weight: 900;
    color: var(--navy);
}

h2 {
    font-family: 'Playfair Display', serif;
    font-weight: 700;
    color: var(--navy);
    margin-top: 24px;
}

h3 {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    color: var(--navy);
}

/* Info/Success/Warning messages */
[data-testid="stAlert"] {
    border-radius: 12px;
    border-left: 4px solid;
}

/* Input styling */
[data-testid="stNumberInput"] input {
    border-radius: 8px;
    border: 1.5px solid rgba(0,0,0,0.1);
    padding: 10px 14px;
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stSelectbox"] > div > div {
    border-radius: 8px;
    border: 1.5px solid rgba(0,0,0,0.1);
}

/* Metric styling */
[data-testid="metric-container"] {
    background: var(--cream);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(245, 166, 35, 0.2);
}

</style>
"""

st.markdown(page_bg, unsafe_allow_html=True)

# -----------------------------
# HEADER & TITLE
# -----------------------------

col_logo, col_space = st.columns([1, 4])

with col_logo:
    st.markdown(
        """
        <h1 style='color:#1A1F4B;font-size:32px;margin:0;'>
        Journey<span style='color:#F5A623'>It</span> ✈
        </h1>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    """
    <p style='text-align:center;color:#1A1F4B;font-size:24px;font-weight:700;margin:20px 0 4px;'>
    AI Travel Assistant for Budget Travelers
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align:center;color:#6B7280;font-size:15px;margin:0 0 32px;'>
    Predict flight prices, plan budgets, and discover destinations with AI
    </p>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# NAVIGATION TABS
# -----------------------------

tab1, tab2, tab3 = st.tabs([
    "✈ Flight Price Advisor",
    "💰 Budget Trip Planner",
    "🌍 Destination Recommender"
])

# =============================
# FLIGHT PRICE ADVISOR
# =============================

with tab1:

    st.markdown(
        "<h2 style='font-size:28px;margin-bottom:24px;'>✈ Predict Future Flight Prices</h2>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        duration = st.number_input(
            "Flight Duration (hours)",
            1.0,
            20.0,
            2.0,
            key="flight_duration"
        )

    with col2:
        days_left = st.number_input(
            "Days Before Departure",
            1,
            60,
            10,
            key="flight_days_left"
        )

    if st.button("Predict Flight Price", key="predict_btn"):

        data = {
            "duration": duration,
            "days_left": days_left
        }

        # FIX 1: Catch specific exceptions and show the actual error message
        try:
            response = requests.post(
                "http://127.0.0.1:8000/predict-flight-price",
                json=data,
                timeout=10  # FIX 2: Added timeout to prevent hanging
            )
            response.raise_for_status()  # FIX 3: Raises HTTPError for bad status codes (4xx, 5xx)

            result = response.json()
            predicted_price = result['predicted_price']

            st.success(f"Predicted Price: ₹{round(predicted_price, 2)}")
            st.info(f"Recommendation: {result['recommendation']}")

            # -----------------------------
            # 📈 PRICE TREND GRAPH
            # -----------------------------

            st.subheader("📈 Price Trend Analysis")

            days_range = list(range(1, 31))
            prices = []

            for d in days_range:
                temp_data = {
                    "duration": duration,
                    "days_left": d
                }

                # FIX 4: Added timeout and raise_for_status inside the loop too
                temp_response = requests.post(
                    "http://127.0.0.1:8000/predict-flight-price",
                    json=temp_data,
                    timeout=10
                )
                temp_response.raise_for_status()
                temp_result = temp_response.json()
                prices.append(temp_result['predicted_price'])

            fig, ax = plt.subplots()
            ax.plot(days_range, prices, color="royalblue", linewidth=2)

            ax.set_xlabel("Days Before Departure")
            ax.set_ylabel("Price (₹)")
            ax.set_title("Flight Price Trend")

            st.pyplot(fig)
            plt.close(fig)  # FIX 5: Close figure after rendering to prevent memory leaks

            # -----------------------------
            # 💡 SMART INSIGHT
            # -----------------------------

            # FIX 6: Compare last vs first price correctly (prices[-1] = 1 day left, prices[0] = 30 days left)
            # Lower days_left = closer to departure; prices typically rise. Corrected logic:
            if prices[0] > prices[-1]:
                st.warning("Prices are higher when booked late 📈 — Book early!")
            else:
                st.success("Prices may drop closer to departure 📉 — You can wait.")

        except requests.exceptions.ConnectionError:
            st.error("❌ Backend not running. Please start the FastAPI server at http://127.0.0.1:8000")
        except requests.exceptions.Timeout:
            st.error("⏱ Request timed out. The backend took too long to respond.")
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Server returned an error: {e}")
        except KeyError as e:
            st.error(f"❌ Unexpected API response format. Missing key: {e}")
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {e}")

# =============================
# BUDGET TRIP PLANNER
# =============================

with tab2:

    st.markdown(
        "<h2 style='font-size:28px;margin-bottom:24px;'>💰 Plan a Trip Within Your Budget</h2>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        budget1 = st.number_input(
            "Total Budget (₹)",
            5000,
            200000,
            20000,
            key="budget_input"
        )

    with col2:
        days1 = st.number_input(
            "Trip Duration (days)",
            1,
            10,
            3,
            key="days_input"
        )

    travel_type1 = st.selectbox(
        "Travel Type",
        ["Beach", "Mountains", "City", "Adventure"],
        key="budget_travel_type"
    )

    if st.button("Generate Trip Plan", key="plan_btn"):

        flight_cost = budget1 * 0.4
        hotel_cost = budget1 * 0.4
        activity_cost = budget1 * 0.2

        st.subheader("💰 Budget Allocation")

        col1, col2, col3 = st.columns(3)

        col1.metric("Flights", f"₹{int(flight_cost)}")
        col2.metric("Hotels", f"₹{int(hotel_cost)}")
        col3.metric("Activities", f"₹{int(activity_cost)}")

        st.subheader("📍 Suggested Destination")

        if travel_type1 == "Beach":
            destination = "Goa"
        elif travel_type1 == "Mountains":
            destination = "Manali"
        elif travel_type1 == "City":
            destination = "Delhi"
        else:
            destination = "Rishikesh"

        st.success(destination)

        st.subheader("🗺 Suggested Itinerary")

        # FIX 7: Itinerary now shows travel-type-specific activities instead of identical generic text
        itinerary_map = {
            "Beach": [
                "Arrive and check in, relax at the beach",
                "Water sports and seafood lunch, sunset cruise",
                "Local market visit and beach bonfire night",
                "Snorkeling trip and departure",
            ],
            "Mountains": [
                "Arrive and acclimatize, local monastery visit",
                "Trek to nearby viewpoint, bonfire in the evening",
                "River crossing adventure and local cuisine",
                "Sunrise point visit and departure",
            ],
            "City": [
                "Arrive, check in, and explore the old city",
                "Museums, heritage sites, and street food tour",
                "Shopping districts and rooftop dinner",
                "Day trip to a nearby attraction and departure",
            ],
            "Adventure": [
                "Arrive and gear up, briefing session",
                "River rafting or bungee jumping",
                "Camping under the stars, bonfire",
                "Early morning hike and departure",
            ],
        }

        activities = itinerary_map.get(travel_type1, [])

        for i in range(1, int(days1) + 1):
            # Cycle through activities if trip is longer than the list
            activity = activities[(i - 1) % len(activities)] if activities else "Explore local attractions and food"
            st.write(f"**Day {i}:** {activity}")

# =============================
# DESTINATION RECOMMENDER
# =============================

with tab3:

    st.markdown(
        "<h2 style='font-size:28px;margin-bottom:24px;'>🌍 AI Destination Recommender</h2>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        budget2 = st.number_input(
            "Budget (₹)",
            5000,
            200000,
            20000,
            key="dest_budget"
        )

    with col2:
        days2 = st.number_input(
            "Trip Duration",
            1,
            10,
            3,
            key="dest_days"
        )

    travel_type2 = st.selectbox(
        "Travel Type",
        ["Beach", "Mountains", "City", "Adventure"],
        key="destination_travel_type"
    )

    if st.button("Recommend Destinations", key="recommend_btn"):

        if travel_type2 == "Beach":
            if budget2 < 15000:
                destinations = ["Gokarna", "Puri"]
            else:
                destinations = ["Goa", "Pondicherry", "Andaman"]

        elif travel_type2 == "Mountains":
            if budget2 < 15000:
                destinations = ["Mussoorie", "Nainital"]
            else:
                destinations = ["Manali", "Shimla", "Leh"]

        elif travel_type2 == "City":
            destinations = ["Delhi", "Mumbai", "Bangalore"]

        else:
            if budget2 < 15000:
                destinations = ["Rishikesh"]
            else:
                destinations = ["Spiti Valley", "Ladakh"]

        st.subheader("Top Destinations")

        for place in destinations:
            st.success(place)

# =============================
# FEATURES SECTION
# =============================

st.divider()

st.markdown(
    "<h2 style='font-size:32px;text-align:center;margin-top:40px;margin-bottom:32px;'>Why Choose JourneyIt?</h2>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown(
        """
        <div style='background:#FEF3DC;padding:24px;border-radius:16px;text-align:center;'>
        <div style='font-size:32px;margin-bottom:12px;'>✈️</div>
        <h3 style='color:#1A1F4B;font-size:18px;margin-bottom:8px;'>Flight Prediction</h3>
        <p style='color:#6B7280;font-size:14px;margin:0;'>Predict flight prices using machine learning.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div style='background:#E8EBF7;padding:24px;border-radius:16px;text-align:center;'>
        <div style='font-size:32px;margin-bottom:12px;'>💰</div>
        <h3 style='color:#1A1F4B;font-size:18px;margin-bottom:8px;'>Budget Planner</h3>
        <p style='color:#6B7280;font-size:14px;margin:0;'>Plan trips within your travel budget.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div style='background:#FCE8E5;padding:24px;border-radius:16px;text-align:center;'>
        <div style='font-size:32px;margin-bottom:12px;'>🌍</div>
        <h3 style='color:#1A1F4B;font-size:18px;margin-bottom:8px;'>Destination AI</h3>
        <p style='color:#6B7280;font-size:14px;margin:0;'>Find the best destinations for your travel style.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

st.markdown(
    "<footer style='text-align:center;color:#6B7280;font-size:14px;padding:40px 0;'>© 2025 JourneyIt. Built for budget travelers.</footer>",
    unsafe_allow_html=True
)