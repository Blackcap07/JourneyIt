# 🚀 Database Quick Reference Guide

## 📋 Table Summary

| Table | Purpose | Records | Key Fields |
|-------|---------|---------|-----------|
| **users** | User accounts | 1M+ | user_id, email, password |
| **user_preferences** | User settings | 1M+ | budget, seat, meal, theme |
| **addresses** | User addresses | 5M+ | type, street, city, country |
| **flights** | Flight inventory | 100K+ | airline, airports, times, fare |
| **hotels** | Hotel inventory | 50K+ | name, city, dates, price |
| **flight_bookings** | Flight reservations | 10M+ | user, flight, reference, amount |
| **hotel_bookings** | Hotel reservations | 10M+ | user, hotel, dates, amount |
| **itineraries** | Trip plans | 5M+ | user, destination, dates |
| **payments** | Transactions | 10M+ | amount, method, status, gateway |
| **reviews** | User ratings | 20M+ | rating, title, text, verified |
| **favorites** | Wishlists | 30M+ | user, type, flight/hotel |
| **payment_methods** | Saved cards | 3M+ | type, brand, last_four |

---

## 🔑 Primary Keys & Foreign Keys

### Foreign Key Relationships

```
users (1) ──→ (M) user_preferences
users (1) ──→ (M) addresses
users (1) ──→ (M) flight_bookings
users (1) ──→ (M) hotel_bookings
users (1) ──→ (M) itineraries
users (1) ──→ (M) payments
users (1) ──→ (M) reviews
users (1) ──→ (M) favorites
users (1) ──→ (M) payment_methods

flights (1) ──→ (M) flight_bookings
hotels (1) ──→ (M) hotel_bookings

flight_bookings (1) ──→ (M) payments
hotel_bookings (1) ──→ (M) payments
```

---

## 🏗️ Common Queries

### 1. Get User Bookings

```python
# Python/SQLAlchemy
user = db.query(User).filter(User.user_id == user_id).first()
flights = db.query(FlightBooking).filter(FlightBooking.user_id == user_id).all()
hotels = db.query(HotelBooking).filter(HotelBooking.user_id == user_id).all()

# Raw SQL
SELECT * FROM flight_bookings WHERE user_id = '...' AND booking_status = 'confirmed';
SELECT * FROM hotel_bookings WHERE user_id = '...' AND booking_status = 'confirmed';
```

### 2. Search Available Flights

```python
# Python/SQLAlchemy
from datetime import datetime, date

flights = db.query(Flight).filter(
    Flight.departure_airport == "DEL",
    Flight.arrival_airport == "BOM",
    Flight.departure_date == date(2024, 12, 20),
    Flight.is_available == True
).order_by(Flight.total_fare).all()

# Raw SQL
SELECT * FROM flights 
WHERE departure_airport = 'DEL' 
  AND arrival_airport = 'BOM' 
  AND departure_date = '2024-12-20'
  AND is_available = TRUE
ORDER BY total_fare ASC;
```

### 3. Get Popular Hotels

```python
# Python/SQLAlchemy
hotels = db.query(Hotel).filter(
    Hotel.city == "Mumbai",
    Hotel.is_available == True
).order_by(Hotel.review_score.desc()).limit(10).all()

# Raw SQL
SELECT * FROM hotels 
WHERE city = 'Mumbai' 
  AND is_available = TRUE
ORDER BY review_score DESC
LIMIT 10;
```

### 4. User Spending Summary

```python
# Python/SQLAlchemy
from sqlalchemy import func

spending = db.query(
    func.sum(Payment.amount).label('total'),
    func.count(Payment.payment_id).label('count'),
    Payment.booking_type
).filter(
    Payment.user_id == user_id,
    Payment.payment_status == 'paid'
).group_by(Payment.booking_type).all()

# Raw SQL
SELECT 
    SUM(amount) as total,
    COUNT(*) as count,
    booking_type
FROM payments
WHERE user_id = '...' AND payment_status = 'paid'
GROUP BY booking_type;
```

### 5. Get User Reviews

```python
# Python/SQLAlchemy
reviews = db.query(Review).filter(
    Review.user_id == user_id,
    Review.is_published == True
).order_by(Review.created_at.desc()).all()

# Raw SQL
SELECT * FROM reviews 
WHERE user_id = '...' AND is_published = TRUE
ORDER BY created_at DESC;
```

---

## 📊 Data Insertion Examples

### 1. Create User Account

```python
from models import User
import bcrypt
from datetime import datetime

new_user = User(
    email="user@example.com",
    password_hash=bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
    first_name="John",
    last_name="Doe",
    phone="+91-9876543210",
    email_verified=False,
    kyc_verified=False,
    is_active=True
)

db.add(new_user)
db.commit()
```

### 2. Create Flight Booking

```python
from models import FlightBooking
import uuid

booking = FlightBooking(
    user_id="user-uuid",
    flight_id="flight-uuid",
    booking_reference="AI12345",
    passenger_name="John Doe",
    passenger_email="john@example.com",
    passenger_phone="+91-9876543210",
    seat_number="12A",
    total_amount=4500.00,
    payment_status="paid",
    booking_status="confirmed"
)

db.add(booking)
db.commit()
```

### 3. Record Payment

```python
from models import Payment

payment = Payment(
    user_id="user-uuid",
    flight_booking_id="booking-uuid",
    booking_type="flight",
    amount=4500.00,
    currency="INR",
    payment_method="card",
    card_type="credit",
    card_last_four="1234",
    transaction_id="TXN123456",
    gateway="razorpay",
    payment_status="paid",
    paid_at=datetime.utcnow()
)

db.add(payment)
db.commit()
```

---

## 🔍 Useful Indexes

```sql
-- Fast user lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);

-- Fast flight searches
CREATE INDEX idx_flights_route ON flights(departure_airport, arrival_airport);
CREATE INDEX idx_flights_date ON flights(departure_date);

-- Fast hotel searches
CREATE INDEX idx_hotels_location ON hotels(city, check_in_date);

-- Fast booking lookups
CREATE INDEX idx_bookings_user_status ON flight_bookings(user_id, booking_status);
CREATE INDEX idx_bookings_reference ON flight_bookings(booking_reference);

-- Fast payment lookups
CREATE INDEX idx_payments_user_date ON payments(user_id, created_at);
```

---

## ⚡ Performance Tips

### 1. Use Connection Pooling
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)
```

### 2. Enable Query Caching
```python
# Cache frequently accessed data
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_flight(flight_id):
    cache_key = f"flight:{flight_id}"
    
    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query database
    flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
    
    # Store in cache (1 hour)
    redis_client.setex(cache_key, 3600, json.dumps(flight))
    
    return flight
```

### 3. Batch Operations
```python
# Bad: Multiple inserts
for user in users:
    db.add(user)
    db.commit()

# Good: Batch insert
db.add_all(users)
db.commit()
```

### 4. Use Query Filtering
```python
# Bad: Load all then filter
flights = db.query(Flight).all()
available = [f for f in flights if f.seats_available > 0]

# Good: Filter in database
available = db.query(Flight).filter(Flight.seats_available > 0).all()
```

---

## 🔐 Security Best Practices

### 1. Password Hashing
```python
import bcrypt

# Hash password on registration
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Verify password on login
if bcrypt.checkpw(password.encode(), user.password_hash.encode()):
    # Login successful
    pass
```

### 2. SQL Injection Prevention
```python
# ✅ GOOD: Use ORM or parameterized queries
user = db.query(User).filter(User.email == email).first()

# ❌ BAD: String concatenation
user = db.query(User).filter(f"email = '{email}'").first()  # Vulnerable!
```

### 3. Sensitive Data
```python
# Don't store sensitive data in plaintext
# Use encryption for:
# - Credit card numbers
# - SSN/Passport numbers
# - Other PII

from cryptography.fernet import Fernet

cipher = Fernet(key)
encrypted_card = cipher.encrypt(card_number.encode()).decode()
```

---

## 🧪 Testing Database

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

@pytest.fixture
def test_db():
    """Create in-memory test database"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def test_user_creation(test_db):
    """Test user creation"""
    from models import User
    
    user = User(
        email="test@example.com",
        password_hash="hash",
        first_name="Test",
        last_name="User"
    )
    
    test_db.add(user)
    test_db.commit()
    
    retrieved = test_db.query(User).filter(User.email == "test@example.com").first()
    assert retrieved is not None
    assert retrieved.first_name == "Test"
```

---

## 📈 Monitoring Queries

```python
# Enable SQL logging
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# This will print all SQL queries to console
```

---

## 🚢 Backup Strategy

```bash
# Daily backup (PostgreSQL)
0 2 * * * pg_dump -U journeyit_user journeyit_db | gzip > /backups/journeyit_$(date +\%Y\%m\%d).sql.gz

# Weekly backup (MySQL)
0 3 * * 0 mysqldump -u journeyit_user -p journeyit_db | gzip > /backups/journeyit_$(date +\%Y\%m\%d).sql.gz

# Archive old backups
0 4 * * * find /backups -name "journeyit_*.sql.gz" -mtime +30 -delete
```

---

## 📚 Resources

- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **MySQL Docs**: https://dev.mysql.com/doc/
- **Database Design**: https://en.wikipedia.org/wiki/Database_design
- **SQL Performance**: https://use-the-index-luke.com/

---

**Last Updated**: December 2024  
**Status**: ✅ Production Ready
