-- ========================================
-- JourneyIt Database Schema
-- PostgreSQL DDL (compatible with MySQL with minor changes)
-- ========================================

-- Create ENUM types (PostgreSQL specific - skip for MySQL)
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended');
CREATE TYPE budget_type AS ENUM ('budget', 'economy', 'business', 'luxury');
CREATE TYPE address_type AS ENUM ('home', 'work', 'other');
CREATE TYPE booking_status AS ENUM ('confirmed', 'cancelled', 'completed', 'pending');
CREATE TYPE payment_status AS ENUM ('pending', 'confirmed', 'paid', 'refunded', 'failed');
CREATE TYPE hotel_type AS ENUM ('hotel', 'resort', 'apartment', 'villa', 'house');
CREATE TYPE trip_type AS ENUM ('leisure', 'business', 'adventure', 'family');
CREATE TYPE payment_method_type AS ENUM ('card', 'upi', 'netbanking', 'wallet');
CREATE TYPE card_type AS ENUM ('credit', 'debit');
CREATE TYPE card_brand AS ENUM ('visa', 'mastercard', 'amex', 'rupay', 'diners');
CREATE TYPE seat_pref AS ENUM ('window', 'middle', 'aisle');
CREATE TYPE meal_pref AS ENUM ('vegetarian', 'vegan', 'non-vegetarian', 'none');
CREATE TYPE checkin_status AS ENUM ('pending', 'checked_in', 'boarded', 'no_show');
CREATE TYPE review_type AS ENUM ('flight', 'hotel');

-- ========================================
-- 1. USERS TABLE
-- ========================================
CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  phone VARCHAR(20) UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  profile_picture TEXT,
  date_of_birth DATE,
  nationality VARCHAR(100),
  passport_number VARCHAR(50),
  email_verified BOOLEAN DEFAULT FALSE,
  phone_verified BOOLEAN DEFAULT FALSE,
  kyc_verified BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ========================================
-- 2. USER PREFERENCES TABLE
-- ========================================
CREATE TABLE user_preferences (
  preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE,
  preferred_airlines JSONB,
  preferred_hotels JSONB,
  budget_preference budget_type DEFAULT 'economy',
  seat_preference seat_pref DEFAULT 'window',
  meal_preference meal_pref DEFAULT 'non-vegetarian',
  theme_preference VARCHAR(50) DEFAULT 'light',
  currency_code VARCHAR(3) DEFAULT 'INR',
  timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
  notification_email BOOLEAN DEFAULT TRUE,
  notification_sms BOOLEAN DEFAULT FALSE,
  notification_push BOOLEAN DEFAULT TRUE,
  price_alert_threshold DECIMAL(5,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- ========================================
-- 3. ADDRESSES TABLE
-- ========================================
CREATE TABLE addresses (
  address_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  address_type address_type NOT NULL,
  street_address VARCHAR(255) NOT NULL,
  city VARCHAR(100) NOT NULL,
  state VARCHAR(100),
  country VARCHAR(100) NOT NULL,
  postal_code VARCHAR(20),
  is_primary BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_addresses_user_id ON addresses(user_id);
CREATE INDEX idx_addresses_is_primary ON addresses(is_primary);

-- ========================================
-- 4. FLIGHTS TABLE
-- ========================================
CREATE TABLE flights (
  flight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  airline_code VARCHAR(2) NOT NULL,
  airline_name VARCHAR(100) NOT NULL,
  flight_number VARCHAR(10) NOT NULL,
  aircraft_type VARCHAR(50),
  departure_airport VARCHAR(3) NOT NULL,
  arrival_airport VARCHAR(3) NOT NULL,
  departure_date DATE NOT NULL,
  departure_time TIME NOT NULL,
  arrival_time TIME NOT NULL,
  duration_minutes INT,
  stops INT DEFAULT 0,
  base_fare DECIMAL(10,2) NOT NULL,
  taxes_fees DECIMAL(10,2) DEFAULT 0,
  total_fare DECIMAL(10,2) NOT NULL,
  seats_available INT,
  seat_capacity INT,
  class VARCHAR(20),
  baggage_allowance INT,
  meal_included BOOLEAN DEFAULT FALSE,
  source VARCHAR(50),
  external_flight_id VARCHAR(100),
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_flights_departure_airport ON flights(departure_airport);
CREATE INDEX idx_flights_arrival_airport ON flights(arrival_airport);
CREATE INDEX idx_flights_departure_date ON flights(departure_date);
CREATE INDEX idx_flights_airline ON flights(airline_code);

-- ========================================
-- 5. HOTELS TABLE
-- ========================================
CREATE TABLE hotels (
  hotel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hotel_name VARCHAR(255) NOT NULL,
  city VARCHAR(100) NOT NULL,
  state VARCHAR(100),
  country VARCHAR(100) NOT NULL,
  address VARCHAR(255),
  latitude DECIMAL(10,8),
  longitude DECIMAL(10,8),
  star_rating DECIMAL(3,2),
  review_count INT DEFAULT 0,
  review_score DECIMAL(3,2),
  hotel_type hotel_type,
  check_in_date DATE NOT NULL,
  check_out_date DATE NOT NULL,
  rooms_available INT,
  room_type VARCHAR(100),
  price_per_night DECIMAL(10,2) NOT NULL,
  total_price DECIMAL(10,2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'INR',
  amenities JSONB,
  photos JSONB,
  description TEXT,
  cancellation_policy VARCHAR(50),
  source VARCHAR(50),
  external_hotel_id VARCHAR(100),
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hotels_city ON hotels(city);
CREATE INDEX idx_hotels_check_in_date ON hotels(check_in_date);
CREATE INDEX idx_hotels_star_rating ON hotels(star_rating);

-- ========================================
-- 6. FLIGHT BOOKINGS TABLE
-- ========================================
CREATE TABLE flight_bookings (
  booking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  flight_id UUID NOT NULL,
  booking_reference VARCHAR(10) UNIQUE NOT NULL,
  passenger_name VARCHAR(255) NOT NULL,
  passport_number VARCHAR(50),
  passenger_email VARCHAR(255) NOT NULL,
  passenger_phone VARCHAR(20) NOT NULL,
  seat_number VARCHAR(10),
  class VARCHAR(20),
  meal_choice VARCHAR(50),
  baggage_weight INT,
  total_amount DECIMAL(10,2) NOT NULL,
  payment_status payment_status DEFAULT 'pending',
  booking_status booking_status DEFAULT 'confirmed',
  check_in_status checkin_status DEFAULT 'pending',
  check_in_time TIMESTAMP,
  special_requests TEXT,
  emergency_contact VARCHAR(100),
  emergency_phone VARCHAR(20),
  cancellation_reason TEXT,
  cancelled_at TIMESTAMP,
  refund_amount DECIMAL(10,2),
  booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
);

CREATE INDEX idx_flight_bookings_user_id ON flight_bookings(user_id);
CREATE INDEX idx_flight_bookings_status ON flight_bookings(booking_status);
CREATE INDEX idx_flight_bookings_reference ON flight_bookings(booking_reference);

-- ========================================
-- 7. HOTEL BOOKINGS TABLE
-- ========================================
CREATE TABLE hotel_bookings (
  booking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  hotel_id UUID NOT NULL,
  booking_reference VARCHAR(10) UNIQUE NOT NULL,
  guest_name VARCHAR(255) NOT NULL,
  guest_email VARCHAR(255) NOT NULL,
  guest_phone VARCHAR(20) NOT NULL,
  room_type VARCHAR(100) NOT NULL,
  check_in_date DATE NOT NULL,
  check_out_date DATE NOT NULL,
  number_of_nights INT,
  number_of_guests INT NOT NULL,
  price_per_night DECIMAL(10,2),
  total_amount DECIMAL(10,2) NOT NULL,
  payment_status payment_status DEFAULT 'pending',
  booking_status booking_status DEFAULT 'confirmed',
  check_in_status checkin_status DEFAULT 'pending',
  check_in_time TIMESTAMP,
  special_requests TEXT,
  additional_guests JSONB,
  cancellation_reason TEXT,
  cancelled_at TIMESTAMP,
  refund_amount DECIMAL(10,2),
  booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
);

CREATE INDEX idx_hotel_bookings_user_id ON hotel_bookings(user_id);
CREATE INDEX idx_hotel_bookings_status ON hotel_bookings(booking_status);
CREATE INDEX idx_hotel_bookings_reference ON hotel_bookings(booking_reference);

-- ========================================
-- 8. ITINERARIES TABLE
-- ========================================
CREATE TABLE itineraries (
  itinerary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  destination VARCHAR(100) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  trip_type trip_type,
  budget DECIMAL(10,2),
  visibility VARCHAR(50) DEFAULT 'private',
  flight_booking_id UUID,
  hotel_booking_id UUID,
  status booking_status DEFAULT 'planning',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (flight_booking_id) REFERENCES flight_bookings(booking_id),
  FOREIGN KEY (hotel_booking_id) REFERENCES hotel_bookings(booking_id)
);

CREATE INDEX idx_itineraries_user_id ON itineraries(user_id);
CREATE INDEX idx_itineraries_status ON itineraries(status);

-- ========================================
-- 9. PAYMENTS TABLE
-- ========================================
CREATE TABLE payments (
  payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  booking_id UUID,
  booking_type VARCHAR(50) NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'INR',
  payment_method payment_method_type NOT NULL,
  card_type card_type,
  card_last_four VARCHAR(4),
  transaction_id VARCHAR(100) UNIQUE,
  gateway VARCHAR(50),
  payment_status payment_status DEFAULT 'pending',
  failure_reason TEXT,
  paid_at TIMESTAMP,
  refund_amount DECIMAL(10,2),
  refund_status payment_status,
  refunded_at TIMESTAMP,
  receipt_url VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(payment_status);
CREATE INDEX idx_payments_created_at ON payments(created_at);

-- ========================================
-- 10. REVIEWS TABLE
-- ========================================
CREATE TABLE reviews (
  review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  booking_id UUID,
  review_type review_type NOT NULL,
  flight_id UUID,
  hotel_id UUID,
  rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
  title VARCHAR(255),
  review_text TEXT NOT NULL,
  categories JSONB,
  helpful_count INT DEFAULT 0,
  unhelpful_count INT DEFAULT 0,
  verified_purchase BOOLEAN DEFAULT FALSE,
  is_published BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (booking_id) REFERENCES flight_bookings(booking_id),
  FOREIGN KEY (flight_id) REFERENCES flights(flight_id),
  FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
);

CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);

-- ========================================
-- 11. FAVORITES TABLE
-- ========================================
CREATE TABLE favorites (
  favorite_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  favorite_type review_type NOT NULL,
  flight_id UUID,
  hotel_id UUID,
  note VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (flight_id) REFERENCES flights(flight_id),
  FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
);

CREATE INDEX idx_favorites_user_id ON favorites(user_id);

-- ========================================
-- 12. PAYMENT METHODS TABLE
-- ========================================
CREATE TABLE payment_methods (
  method_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  method_type payment_method_type NOT NULL,
  card_name VARCHAR(100),
  card_last_four VARCHAR(4),
  card_brand card_brand,
  expiry_month INT,
  expiry_year INT,
  upi_id VARCHAR(100),
  is_default BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_payment_methods_user_id ON payment_methods(user_id);
CREATE INDEX idx_payment_methods_default ON payment_methods(is_default);

-- ========================================
-- ADDITIONAL INDEXES FOR PERFORMANCE
-- ========================================

-- Composite indexes for common queries
CREATE INDEX idx_flights_route_date ON flights(departure_airport, arrival_airport, departure_date);
CREATE INDEX idx_hotels_location_dates ON hotels(city, check_in_date, check_out_date);
CREATE INDEX idx_bookings_user_status ON flight_bookings(user_id, booking_status);
CREATE INDEX idx_hotel_bookings_user_status ON hotel_bookings(user_id, booking_status);
CREATE INDEX idx_payments_user_created ON payments(user_id, created_at);

-- ========================================
-- DATABASE VIEWS (Optional)
-- ========================================

-- View for user's booking summary
CREATE VIEW user_booking_summary AS
SELECT
  u.user_id,
  u.email,
  COUNT(DISTINCT fb.booking_id) as flight_bookings,
  COUNT(DISTINCT hb.booking_id) as hotel_bookings,
  SUM(CASE WHEN fb.booking_status = 'completed' THEN 1 ELSE 0 END) as completed_flights,
  SUM(CASE WHEN hb.booking_status = 'completed' THEN 1 ELSE 0 END) as completed_hotels
FROM users u
LEFT JOIN flight_bookings fb ON u.user_id = fb.user_id
LEFT JOIN hotel_bookings hb ON u.user_id = hb.user_id
GROUP BY u.user_id, u.email;

-- View for available flights
CREATE VIEW available_flights AS
SELECT
  f.*,
  (f.seat_capacity - COALESCE(booked_seats, 0)) as available_seats
FROM flights f
LEFT JOIN (
  SELECT flight_id, COUNT(*) as booked_seats
  FROM flight_bookings
  WHERE booking_status != 'cancelled'
  GROUP BY flight_id
) b ON f.flight_id = b.flight_id
WHERE f.is_available = TRUE;

-- View for available hotels
CREATE VIEW available_hotels AS
SELECT
  h.*,
  (h.rooms_available - COALESCE(booked_rooms, 0)) as actual_available_rooms
FROM hotels h
LEFT JOIN (
  SELECT hotel_id, COUNT(*) as booked_rooms
  FROM hotel_bookings
  WHERE booking_status != 'cancelled'
  AND check_out_date > CURRENT_DATE
  GROUP BY hotel_id
) b ON h.hotel_id = b.hotel_id
WHERE h.is_available = TRUE;

-- ========================================
-- INITIAL DATA (Optional Sample Data)
-- ========================================

-- Sample user data
INSERT INTO users (email, password_hash, first_name, last_name, email_verified)
VALUES
  ('salman@journeyit.com', '$2b$12$...', 'Salman', 'Khan', TRUE),
  ('test@journeyit.com', '$2b$12$...', 'Test', 'User', FALSE);

-- Sample flight data
INSERT INTO flights (airline_code, airline_name, flight_number, departure_airport, arrival_airport, departure_date, departure_time, arrival_time, duration_minutes, total_fare, seat_capacity, class)
VALUES
  ('AI', 'Air India', 'AI123', 'DEL', 'BOM', CURRENT_DATE + INTERVAL '7 days', '09:00:00', '11:30:00', 150, 4500.00, 180, 'economy'),
  ('6E', 'IndiGo', '6E456', 'BLR', 'DEL', CURRENT_DATE + INTERVAL '7 days', '10:00:00', '12:45:00', 165, 3500.00, 200, 'economy');

-- ========================================
-- END OF SCHEMA
-- ========================================
