# 📊 Database Integration Guide for JourneyIt

## Quick Start

### Option 1: Using PostgreSQL (Recommended)

```bash
# Install dependencies
pip install sqlalchemy psycopg2-binary alembic python-dotenv

# Install PostgreSQL
# macOS: brew install postgresql
# Windows: https://www.postgresql.org/download/windows/
# Linux: sudo apt-get install postgresql postgresql-contrib
```

### Option 2: Using MySQL

```bash
# Install dependencies
pip install sqlalchemy mysql-connector-python alembic python-dotenv

# Install MySQL
# macOS: brew install mysql
# Windows: https://dev.mysql.com/downloads/mysql/
# Linux: sudo apt-get install mysql-server
```

---

## Step 1: Environment Configuration

Create `.env` file in the `backend/` directory:

```env
# Database Configuration
DB_DRIVER=postgresql  # or mysql
DB_USER=journeyit_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432  # PostgreSQL: 5432, MySQL: 3306
DB_NAME=journeyit_db

# Database URL (Auto-generated)
DATABASE_URL=postgresql://journeyit_user:your_password@localhost:5432/journeyit_db

# Other configs
ENVIRONMENT=development  # development, staging, production
```

---

## Step 2: Database Setup

### PostgreSQL Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create user
CREATE USER journeyit_user WITH PASSWORD 'your_secure_password';

# Create database
CREATE DATABASE journeyit_db OWNER journeyit_user;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE journeyit_db TO journeyit_user;

# Exit psql
\q
```

### MySQL Setup

```bash
# Connect to MySQL
mysql -u root -p

# Create user
CREATE USER 'journeyit_user'@'localhost' IDENTIFIED BY 'your_secure_password';

# Create database
CREATE DATABASE journeyit_db;

# Grant privileges
GRANT ALL PRIVILEGES ON journeyit_db.* TO 'journeyit_user'@'localhost';
FLUSH PRIVILEGES;

# Exit MySQL
EXIT;
```

---

## Step 3: Run Schema SQL

### Using PostgreSQL

```bash
# Connect and run schema
psql -U journeyit_user -d journeyit_db -f db_schema.sql
```

### Using MySQL

```bash
# Connect and run schema
mysql -u journeyit_user -p journeyit_db < db_schema.sql
```

---

## Step 4: Update Backend Code

### Create `database.py` in `backend/`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv
from models import Base

load_dotenv()

# Database Configuration
DB_DRIVER = os.getenv("DB_DRIVER", "postgresql")
DB_USER = os.getenv("DB_USER", "journeyit_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "journeyit_db")

# Build database URL
if DB_DRIVER == "postgresql":
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
elif DB_DRIVER == "mysql":
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    # SQLite for testing
    DATABASE_URL = "sqlite:///./test.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set True for SQL logging
    pool_pre_ping=True,  # Test connection before using
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Dependency injection for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Update `main.py` to use database

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Flight, Hotel
import bcrypt
import os
from datetime import datetime, timedelta

app = FastAPI()

# ========================================
# Authentication Endpoints
# ========================================

@app.post("/register")
def register(email: str, password: str, first_name: str, last_name: str, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # Create user
    new_user = User(
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"user_id": str(new_user.user_id), "email": new_user.email}

@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    """Login user"""
    
    user = db.query(User).filter(User.email == email).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Generate JWT token (implement as needed)
    return {"user_id": str(user.user_id), "token": "..."}

# ========================================
# Flight Endpoints
# ========================================

@app.get("/flights/search")
def search_flights(
    from_airport: str,
    to_airport: str,
    date: str,
    db: Session = Depends(get_db)
):
    """Search available flights"""
    
    flights = db.query(Flight).filter(
        Flight.departure_airport == from_airport,
        Flight.arrival_airport == to_airport,
        Flight.departure_date == date,
        Flight.is_available == True
    ).all()
    
    return [
        {
            "flight_id": str(f.flight_id),
            "airline": f.airline_name,
            "departure": f.departure_time,
            "arrival": f.arrival_time,
            "fare": f.total_fare,
            "seats": f.seats_available
        }
        for f in flights
    ]

@app.post("/bookings/flight")
def book_flight(
    user_id: str,
    flight_id: str,
    passenger_name: str,
    db: Session = Depends(get_db)
):
    """Book a flight"""
    
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify flight exists and available
    flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
    if not flight or not flight.is_available:
        raise HTTPException(status_code=404, detail="Flight not available")
    
    # Create booking record
    from models import FlightBooking
    booking = FlightBooking(
        user_id=user_id,
        flight_id=flight_id,
        booking_reference=generate_booking_ref(),  # Implement this
        passenger_name=passenger_name,
        passenger_email=user.email,
        passenger_phone=user.phone,
        total_amount=flight.total_fare,
        booking_status="confirmed"
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    return {
        "booking_id": str(booking.booking_id),
        "booking_reference": booking.booking_reference,
        "status": "confirmed"
    }
```

---

## Step 5: Database Migrations (Alembic)

Initialize Alembic for schema versioning:

```bash
# Initialize Alembic
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

---

## Step 6: Backup & Restoration

### PostgreSQL Backup

```bash
# Backup
pg_dump -U journeyit_user journeyit_db > backup.sql

# Restore
psql -U journeyit_user journeyit_db < backup.sql
```

### MySQL Backup

```bash
# Backup
mysqldump -u journeyit_user -p journeyit_db > backup.sql

# Restore
mysql -u journeyit_user -p journeyit_db < backup.sql
```

---

## Step 7: Performance Optimization

### Add Connection Pooling

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)
```

### Add Caching

```python
from functools import lru_cache
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

# Enable query result caching
from cachetools import TTLCache

flight_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minute cache

@app.get("/flights/search")
def search_flights(from_airport: str, to_airport: str, date: str, db: Session = Depends(get_db)):
    cache_key = f"{from_airport}-{to_airport}-{date}"
    
    if cache_key in flight_cache:
        return flight_cache[cache_key]
    
    results = db.query(Flight).filter(...).all()
    flight_cache[cache_key] = results
    return results
```

---

## File Structure After Integration

```
backend/
├── main.py                 # FastAPI app (update with DB endpoints)
├── models.py              # SQLAlchemy ORM models (NEW)
├── database.py            # Database configuration (NEW)
├── db_schema.sql          # Raw SQL schema (NEW)
├── requirements.txt       # Add sqlalchemy, psycopg2-binary
├── .env                   # Environment variables (NEW)
└── migrations/            # Alembic migrations folder (NEW)
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── 001_initial_schema.py
```

---

## Required Python Packages

Add to `requirements.txt`:

```
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9     # For PostgreSQL
# mysql-connector-python==8.0.33  # For MySQL (uncomment if using MySQL)
python-dotenv==1.0.0
bcrypt==4.1.1
pydantic==2.4.2
fastapi==0.104.1
uvicorn==0.24.0
```

---

## Testing Database Connection

```python
# test_db.py
from database import engine, get_db
from models import Base, User

def test_connection():
    """Test database connection"""
    try:
        # Test create tables
        Base.metadata.create_all(bind=engine)
        
        # Test query
        db = next(get_db())
        users = db.query(User).all()
        print(f"✅ Database connected! Found {len(users)} users")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_connection()
```

Run test:
```bash
python test_db.py
```

---

## Next Steps

1. ✅ Set up database (PostgreSQL/MySQL)
2. ✅ Run schema SQL file
3. ✅ Create `database.py` and update `main.py`
4. ✅ Test connection with test script
5. ✅ Add authentication endpoints
6. ✅ Implement booking endpoints
7. ✅ Add payment processing
8. ✅ Set up migrations with Alembic
9. ✅ Configure backups
10. ✅ Deploy to production

---

## Support

For PostgreSQL issues: https://www.postgresql.org/docs/
For MySQL issues: https://dev.mysql.com/doc/
For SQLAlchemy: https://docs.sqlalchemy.org/

