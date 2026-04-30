# 🗄️ JourneyIt Database Schema

## Overview

A comprehensive database design for the JourneyIt travel planning platform. This schema supports user management, flight/hotel bookings, preferences, and payment processing.

---

## Database System
- **Type**: Relational (PostgreSQL recommended for production)
- **Alternative**: MySQL 8.0+, MariaDB 10.5+
- **ORM**: SQLAlchemy (Python) or Django ORM

---

## Core Tables

### 1. **Users** - User Accounts & Authentication
```
Stores user profile and authentication data
Primary Key: user_id
Indexes: email (UNIQUE), phone (UNIQUE)
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | UUID | PRIMARY KEY | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email address |
| phone | VARCHAR(20) | UNIQUE | Phone number |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| first_name | VARCHAR(100) | NOT NULL | User first name |
| last_name | VARCHAR(100) | NOT NULL | User last name |
| profile_picture | TEXT | | URL to profile image |
| date_of_birth | DATE | | Birth date for age verification |
| nationality | VARCHAR(100) | | Country code (ISO 3166-1) |
| passport_number | VARCHAR(50) | | For international flights |
| email_verified | BOOLEAN | DEFAULT FALSE | Email verification status |
| phone_verified | BOOLEAN | DEFAULT FALSE | Phone verification status |
| kyc_verified | BOOLEAN | DEFAULT FALSE | KYC compliance (booking limits) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation time |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last profile update |
| last_login | TIMESTAMP | | Last login time |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |

---

### 2. **UserPreferences** - User Settings & Preferences
```
Stores user travel preferences and settings
Primary Key: preference_id
Foreign Key: user_id → Users(user_id)
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| preference_id | UUID | PRIMARY KEY | Preference record ID |
| user_id | UUID | FOREIGN KEY, NOT NULL | Reference to Users table |
| preferred_airlines | JSON | | Array of preferred airline codes |
| preferred_hotels | JSON | | Array of favorite hotel chains |
| budget_preference | VARCHAR(50) | ENUM: budget/economy/business/luxury | Travel class preference |
| seat_preference | VARCHAR(50) | ENUM: window/middle/aisle | Flight seat preference |
| meal_preference | VARCHAR(50) | ENUM: vegetarian/vegan/non-veg | Meal preference |
| theme_preference | VARCHAR(50) | ENUM: light/dark | UI theme preference |
| currency_code | VARCHAR(3) | DEFAULT 'INR' | Preferred currency (ISO 4217) |
| timezone | VARCHAR(50) | DEFAULT 'Asia/Kolkata' | User timezone |
| notification_email | BOOLEAN | DEFAULT TRUE | Email notifications |
| notification_sms | BOOLEAN | DEFAULT FALSE | SMS notifications |
| notification_push | BOOLEAN | DEFAULT TRUE | Push notifications |
| price_alert_threshold | DECIMAL(10,2) | | Alert when price drops by % |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

---

### 3. **Addresses** - User Address Information
```
Stores multiple addresses per user (home, work, etc.)
Primary Key: address_id
Foreign Key: user_id → Users(user_id)
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| address_id | UUID | PRIMARY KEY | Address record ID |
| user_id | UUID | FOREIGN KEY, NOT NULL | Reference to Users |
| address_type | VARCHAR(50) | ENUM: home/work/other | Address type |
| street_address | VARCHAR(255) | NOT NULL | Street address |
| city | VARCHAR(100) | NOT NULL | City name |
| state | VARCHAR(100) | | State/Province |
| country | VARCHAR(100) | NOT NULL | Country name |
| postal_code | VARCHAR(20) | | Postal/ZIP code |
| is_primary | BOOLEAN | DEFAULT FALSE | Primary address flag |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

---

### 4. **Flights** - Flight Inventory
```
Stores available flight information (from APIs)
Primary Key: flight_id
Indexes: departure_airport, arrival_airport, departure_date
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| flight_id | UUID | PRIMARY KEY | Unique flight identifier |
| airline_code | VARCHAR(2) | NOT NULL | IATA airline code (e.g., 'AI') |
| airline_name | VARCHAR(100) | NOT NULL | Airline name |
| flight_number | VARCHAR(10) | NOT NULL | Flight number |
| aircraft_type | VARCHAR(50) | | Aircraft model (e.g., 'Boeing 737') |
| departure_airport | VARCHAR(3) | NOT NULL | IATA airport code |
| arrival_airport | VARCHAR(3) | NOT NULL | IATA airport code |
| departure_date | DATE | NOT NULL | Departure date |
| departure_time | TIME | NOT NULL | Departure time (UTC) |
| arrival_time | TIME | NOT NULL | Arrival time (UTC) |
| duration_minutes | INT | | Flight duration in minutes |
| stops | INT | DEFAULT 0 | Number of stops (0=nonstop) |
| base_fare | DECIMAL(10,2) | NOT NULL | Base fare (INR) |
| taxes_fees | DECIMAL(10,2) | DEFAULT 0 | Taxes and fees |
| total_fare | DECIMAL(10,2) | NOT NULL | Total fare |
| seats_available | INT | | Available seats |
| seat_capacity | INT | | Total seat capacity |
| class | VARCHAR(20) | ENUM: economy/business/first | Cabin class |
| baggage_allowance | INT | | Baggage in kg |
| meal_included | BOOLEAN | DEFAULT FALSE | Meal service included |
| source | VARCHAR(50) | | Data source (e.g., 'sky_scanner', 'amadeus') |
| external_flight_id | VARCHAR(100) | | ID from external API |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last price update |
| is_available | BOOLEAN | DEFAULT TRUE | Availability status |

---

### 5. **Hotels** - Hotel Inventory
```
Stores available hotels (from APIs)
Primary Key: hotel_id
Indexes: city, check_in_date, check_out_date
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| hotel_id | UUID | PRIMARY KEY | Unique hotel identifier |
| hotel_name | VARCHAR(255) | NOT NULL | Hotel name |
| city | VARCHAR(100) | NOT NULL | City location |
| state | VARCHAR(100) | | State/Province |
| country | VARCHAR(100) | NOT NULL | Country |
| address | VARCHAR(255) | | Full address |
| latitude | DECIMAL(10,8) | | GPS latitude |
| longitude | DECIMAL(10,8) | | GPS longitude |
| star_rating | DECIMAL(3,2) | | Star rating (1-5) |
| review_count | INT | DEFAULT 0 | Number of reviews |
| review_score | DECIMAL(3,2) | | Average review score |
| hotel_type | VARCHAR(50) | ENUM: hotel/resort/apartment/villa | Property type |
| check_in_date | DATE | NOT NULL | Check-in date |
| check_out_date | DATE | NOT NULL | Check-out date |
| rooms_available | INT | | Available rooms |
| room_type | VARCHAR(100) | | Room category |
| price_per_night | DECIMAL(10,2) | NOT NULL | Price per night (INR) |
| total_price | DECIMAL(10,2) | NOT NULL | Total stay price |
| currency | VARCHAR(3) | DEFAULT 'INR' | Price currency |
| amenities | JSON | | Array of amenities |
| photos | JSON | | Array of photo URLs |
| description | TEXT | | Hotel description |
| cancellation_policy | VARCHAR(50) | | Free/Paid/Non-refundable |
| source | VARCHAR(50) | | Data source (e.g., 'booking.com') |
| external_hotel_id | VARCHAR(100) | | ID from external API |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| is_available | BOOLEAN | DEFAULT TRUE | Availability |

---

### 6. **FlightBookings** - Flight Reservation Records
```
Stores user flight bookings
Primary Key: booking_id
Foreign Keys: user_id, flight_id, address_id
Indexes: booking_reference, user_id, status
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| booking_id | UUID | PRIMARY KEY | Unique booking identifier |
| user_id | UUID | FOREIGN KEY, NOT NULL | Reference to Users |
| flight_id | UUID | FOREIGN KEY, NOT NULL | Reference to Flights |
| booking_reference | VARCHAR(10) | UNIQUE, NOT NULL | PNR/Confirmation code |
| passenger_name | VARCHAR(255) | NOT NULL | Passenger full name |
| passport_number | VARCHAR(50) | | Passport number |
| passenger_email | VARCHAR(255) | NOT NULL | Passenger email |
| passenger_phone | VARCHAR(20) | NOT NULL | Passenger phone |
| seat_number | VARCHAR(10) | | Assigned seat |
| class | VARCHAR(20) | | Booked cabin class |
| meal_choice | VARCHAR(50) | | Selected meal preference |
| baggage_weight | INT | | Baggage weight in kg |
| total_amount | DECIMAL(10,2) | NOT NULL | Total booking amount |
| payment_status | VARCHAR(50) | ENUM: pending/confirmed/paid/refunded | Payment status |
| booking_status | VARCHAR(50) | ENUM: confirmed/cancelled/completed | Booking status |
| booking_date | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Booking creation date |
| check_in_status | VARCHAR(50) | ENUM: pending/checked_in/boarded | Check-in status |
| check_in_time | TIMESTAMP | | Check-in timestamp |
| special_requests | TEXT | | Special meal/service requests |
| emergency_contact | VARCHAR(100) | | Emergency contact person |
| emergency_phone | VARCHAR(20) | | Emergency contact phone |
| cancellation_reason | TEXT | | Reason for cancellation (if any) |
| cancelled_at | TIMESTAMP | | Cancellation timestamp |
| refund_amount | DECIMAL(10,2) | | Refunded amount |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

---

### 7. **HotelBookings** - Hotel Reservation Records
```
Stores user hotel bookings
Primary Key: booking_id
Foreign Keys: user_id, hotel_id, address_id
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| booking_id | UUID | PRIMARY KEY | Unique booking identifier |
| user_id | UUID | FOREIGN KEY, NOT NULL | Reference to Users |
| hotel_id | UUID | FOREIGN KEY, NOT NULL | Reference to Hotels |
| booking_reference | VARCHAR(10) | UNIQUE, NOT NULL | Confirmation code |
| guest_name | VARCHAR(255) | NOT NULL | Primary guest name |
| guest_email | VARCHAR(255) | NOT NULL | Guest email |
| guest_phone | VARCHAR(20) | NOT NULL | Guest phone |
| room_type | VARCHAR(100) | NOT NULL | Booked room type |
| check_in_date | DATE | NOT NULL | Check-in date |
| check_out_date | DATE | NOT NULL | Check-out date |
| number_of_nights | INT | | Number of nights |
| number_of_guests | INT | NOT NULL | Number of guests |
| price_per_night | DECIMAL(10,2) | | Price per night |
| total_amount | DECIMAL(10,2) | NOT NULL | Total booking amount |
| payment_status | VARCHAR(50) | ENUM: pending/confirmed/paid/refunded | Payment status |
| booking_status | VARCHAR(50) | ENUM: confirmed/cancelled/completed | Booking status |
| booking_date | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Booking date |
| check_in_status | VARCHAR(50) | ENUM: pending/checked_in | Check-in status |
| check_in_time | TIMESTAMP | | Check-in timestamp |
| special_requests | TEXT | | Room requests (e.g., high floor) |
| additional_guests | JSON | | Array of additional guest names |
| cancellation_reason | TEXT | | Cancellation reason |
| cancelled_at | TIMESTAMP | | Cancellation timestamp |
| refund_amount | DECIMAL(10,2) | | Refunded amount |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

---

### 8. **Itineraries** - Trip Planning
```
Stores complete trip itineraries
Primary Key: itinerary_id
Foreign Key: user_id → Users(user_id)
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| itinerary_id | UUID | PRIMARY KEY | Itinerary ID |
| user_id | UUID | FOREIGN KEY, NOT NULL | Owner user |
| title | VARCHAR(255) | NOT NULL | Trip title |
| description | TEXT | | Trip description |
| destination | VARCHAR(100) | NOT NULL | Primary destination |
| start_date | DATE | NOT NULL | Trip start date |
| end_date | DATE | NOT NULL | Trip end date |
| trip_type | VARCHAR(50) | ENUM: leisure/business/adventure | Trip type |
| budget | DECIMAL(10,2) | | Trip budget (INR) |
| visibility | VARCHAR(50) | ENUM: private/friends/public | Sharing status |
| flight_booking_id | UUID | FOREIGN KEY | Associated flight booking |
| hotel_booking_id | UUID | FOREIGN KEY | Associated hotel booking |
| status | VARCHAR(50) | ENUM: planning/booked/in_progress/completed | Trip status |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

---

### 9. **Payments** - Payment & Transaction Records
```
Stores payment information and transaction history
Primary Key: payment_id
Foreign Keys: user_id, booking_id
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| payment_id | UUID | PRIMARY KEY | Payment ID |
| user_id | UUID | FOREIGN KEY, NOT NULL | User making payment |
| booking_id | UUID | FOREIGN KEY | Related booking |
| booking_type | VARCHAR(50) | ENUM: flight/hotel | Booking type |
| amount | DECIMAL(10,2) | NOT NULL | Payment amount |
| currency | VARCHAR(3) | DEFAULT 'INR' | Currency code |
| payment_method | VARCHAR(50) | ENUM: card/upi/netbanking/wallet | Payment method |
| card_type | VARCHAR(50) | ENUM: credit/debit | Card type (if applicable) |
| card_last_four | VARCHAR(4) | | Last 4 digits of card |
| transaction_id | VARCHAR(100) | UNIQUE | External payment gateway ID |
| gateway | VARCHAR(50) | | Payment gateway (Razorpay, Stripe, etc.) |
| payment_status | VARCHAR(50) | ENUM: pending/success/failed/refunded | Payment status |
| failure_reason | TEXT | | Reason if payment failed |
| paid_at | TIMESTAMP | | Payment completion time |
| refund_amount | DECIMAL(10,2) | | Refund amount (if applicable) |
| refund_status | VARCHAR(50) | ENUM: pending/success/failed | Refund status |
| refunded_at | TIMESTAMP | | Refund completion time |
| receipt_url | VARCHAR(255) | | URL to receipt PDF |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

---

### 10. **Reviews** - User Reviews & Ratings
```
Stores user reviews for flights and hotels
Primary Key: review_id
Foreign Keys: user_id, flight_id/hotel_id
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| review_id | UUID | PRIMARY KEY | Review ID |
| user_id | UUID | FOREIGN KEY, NOT NULL | Reviewer |
| booking_id | UUID | FOREIGN KEY | Related booking |
| review_type | VARCHAR(50) | ENUM: flight/hotel | What's being reviewed |
| flight_id | UUID | FOREIGN KEY | Flight (if flight review) |
| hotel_id | UUID | FOREIGN KEY | Hotel (if hotel review) |
| rating | INT | CHECK (rating BETWEEN 1 AND 5) | Star rating (1-5) |
| title | VARCHAR(255) | | Review title |
| review_text | TEXT | NOT NULL | Detailed review |
| categories | JSON | | Ratings by category |
| helpful_count | INT | DEFAULT 0 | Helpful votes count |
| unhelpful_count | INT | DEFAULT 0 | Unhelpful votes count |
| verified_purchase | BOOLEAN | DEFAULT FALSE | Verified booking flag |
| is_published | BOOLEAN | DEFAULT TRUE | Review visibility |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Review date |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

---

### 11. **Favorites** - Saved Flights & Hotels
```
Stores user's favorite/wishlist items
Primary Key: favorite_id
Foreign Keys: user_id, flight_id/hotel_id
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| favorite_id | UUID | PRIMARY KEY | Favorite ID |
| user_id | UUID | FOREIGN KEY, NOT NULL | User |
| favorite_type | VARCHAR(50) | ENUM: flight/hotel | Type of favorite |
| flight_id | UUID | FOREIGN KEY | Flight (if applicable) |
| hotel_id | UUID | FOREIGN KEY | Hotel (if applicable) |
| note | VARCHAR(500) | | Personal note |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

---

### 12. **Payments_Methods** - Saved Payment Methods
```
Stores saved payment instruments for quick checkout
Primary Key: method_id
Foreign Key: user_id → Users(user_id)
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| method_id | UUID | PRIMARY KEY | Method ID |
| user_id | UUID | FOREIGN KEY, NOT NULL | User |
| method_type | VARCHAR(50) | ENUM: card/upi/wallet | Payment method type |
| card_name | VARCHAR(100) | | Cardholder name |
| card_last_four | VARCHAR(4) | | Last 4 digits |
| card_brand | VARCHAR(50) | ENUM: visa/mastercard/amex | Card brand |
| expiry_month | INT | | Expiry month |
| expiry_year | INT | | Expiry year |
| upi_id | VARCHAR(100) | | UPI identifier |
| is_default | BOOLEAN | DEFAULT FALSE | Default payment method |
| is_active | BOOLEAN | DEFAULT TRUE | Status |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

---

## Relationships Diagram

```
Users (1)
  ├─→ (M) UserPreferences
  ├─→ (M) Addresses
  ├─→ (M) FlightBookings
  │    └─→ (1) Flights
  │    └─→ (1) Payments
  ├─→ (M) HotelBookings
  │    └─→ (1) Hotels
  │    └─→ (1) Payments
  ├─→ (M) Itineraries
  ├─→ (M) Reviews
  ├─→ (M) Favorites
  └─→ (M) Payments_Methods
```

---

## Indexes for Performance

```sql
-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Flights
CREATE INDEX idx_flights_departure_airport ON flights(departure_airport);
CREATE INDEX idx_flights_arrival_airport ON flights(arrival_airport);
CREATE INDEX idx_flights_departure_date ON flights(departure_date);
CREATE INDEX idx_flights_airline ON flights(airline_code);

-- Hotels
CREATE INDEX idx_hotels_city ON hotels(city);
CREATE INDEX idx_hotels_check_in_date ON hotels(check_in_date);
CREATE INDEX idx_hotels_star_rating ON hotels(star_rating);

-- Bookings
CREATE INDEX idx_flight_bookings_user_id ON flight_bookings(user_id);
CREATE INDEX idx_flight_bookings_status ON flight_bookings(booking_status);
CREATE INDEX idx_hotel_bookings_user_id ON hotel_bookings(user_id);
CREATE INDEX idx_hotel_bookings_status ON hotel_bookings(booking_status);

-- Payments
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(payment_status);
CREATE INDEX idx_payments_created_at ON payments(created_at);

-- Reviews
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
```

---

## Migration Path

1. **Phase 1**: Create base tables (Users, UserPreferences, Addresses)
2. **Phase 2**: Add flight/hotel tables (Flights, Hotels)
3. **Phase 3**: Add booking tables (FlightBookings, HotelBookings)
4. **Phase 4**: Add payments and reviews (Payments, Reviews)
5. **Phase 5**: Add auxiliary tables (Itineraries, Favorites, PaymentMethods)

---

**Status**: 🏗️ Schema Design Complete - Ready for Implementation
