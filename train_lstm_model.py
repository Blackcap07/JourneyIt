"""
LSTM Time Series Model for Flight Price Prediction
Predicts 7-day flight price trends using temporal patterns
"""

import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    from sklearn.preprocessing import MinMaxScaler
    TENSORFLOW_AVAILABLE = True
except ImportError:
    print("⚠️  TensorFlow not installed. Install with: pip install tensorflow")
    TENSORFLOW_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────
# SYNTHETIC TRAINING DATA GENERATION
# ─────────────────────────────────────────────────────────────────

def generate_synthetic_timeseries_data(
    num_routes: int = 50,
    days_per_route: int = 60,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic historical flight price data with realistic patterns

    Each route has 60 days of historical prices with:
    - Trend (prices trending up/down)
    - Seasonality (weekend vs weekday patterns)
    - Noise (random volatility)
    - Days-left effect (prices change as departure approaches)
    """
    np.random.seed(seed)

    data = []
    routes = [
        ("DEL", "BOM"), ("DEL", "GOI"), ("DEL", "BLR"),
        ("BOM", "BLR"), ("BOM", "HYD"), ("BOM", "MAA"),
        ("BLR", "GOI"), ("BLR", "HYD"), ("HYD", "GOI"),
        ("MAA", "BLR"), ("COL", "DEL"), ("PNQ", "BOM")
    ]

    for route_idx in range(min(num_routes, len(routes) * 5)):
        route = routes[route_idx % len(routes)]
        base_price = np.random.uniform(2000, 8000)  # Base price for route

        # Generate trend component
        trend = np.random.uniform(-0.5, 0.5)  # Price moves up/down over days

        # Generate seasonality
        seasonality_strength = np.random.uniform(0.1, 0.3)

        for day in range(days_per_route):
            # 1. Trend component (gradual change)
            trend_component = trend * day

            # 2. Seasonality component (weekly pattern)
            day_of_week = day % 7
            seasonality_component = seasonality_strength * np.sin(2 * np.pi * day_of_week / 7) * base_price

            # 3. Noise (random fluctuations)
            noise = np.random.normal(0, base_price * 0.05)  # 5% volatility

            # 4. Days-left effect (prices typically increase closer to departure)
            days_left = 30 - (day % 30)  # Cycle between 30 and 0
            days_left_effect = (30 - days_left) * 10  # Price increases as departure nears

            # Combine all components
            price = base_price + trend_component + seasonality_component + noise + days_left_effect
            price = max(1000, price)  # Minimum price

            data.append({
                'date': datetime.now() - timedelta(days=days_per_route - day),
                'from_iata': route[0],
                'to_iata': route[1],
                'days_left': days_left,
                'price': int(price)
            })

    df = pd.DataFrame(data)
    df = df.sort_values(['from_iata', 'to_iata', 'date']).reset_index(drop=True)

    print(f"[OK] Generated {len(df)} historical price records across {num_routes} routes")
    print(f"   Price range: Rs.{df['price'].min()} - Rs.{df['price'].max()}")

    return df


# ─────────────────────────────────────────────────────────────────
# TIME SERIES DATA PREPARATION
# ─────────────────────────────────────────────────────────────────

def create_sequences(data: np.ndarray, seq_length: int = 7) -> tuple:
    """
    Convert time series data into sequences for LSTM

    Input:  [3500, 3480, 3450, 3420, 3400, 3350, 3320, 3280, 3250, 3200]

    Output sequences (seq_length=7):
    X = [
        [3500, 3480, 3450, 3420, 3400, 3350, 3320],  → y = [3280]
        [3480, 3450, 3420, 3400, 3350, 3320, 3280],  → y = [3250]
        [3450, 3420, 3400, 3350, 3320, 3280, 3250],  → y = [3200]
    ]
    """
    X, y = [], []

    for i in range(len(data) - seq_length):
        X.append(data[i:i + seq_length])
        y.append(data[i + seq_length])

    return np.array(X), np.array(y)


def prepare_lstm_data(
    df: pd.DataFrame,
    seq_length: int = 7,
    test_size: float = 0.2
) -> dict:
    """
    Prepare data for LSTM training

    Groups by route, normalizes prices, creates sequences
    """
    routes_data = {}

    for route in df[['from_iata', 'to_iata']].drop_duplicates().values:
        from_iata, to_iata = route
        route_key = f"{from_iata}-{to_iata}"

        # Filter route data
        route_df = df[
            (df['from_iata'] == from_iata) &
            (df['to_iata'] == to_iata)
        ].sort_values('date')

        if len(route_df) < seq_length + 1:
            continue

        # Extract prices
        prices = route_df['price'].values.astype(float)

        # Normalize using MinMaxScaler (0 to 1)
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_prices = scaler.fit_transform(prices.reshape(-1, 1)).flatten()

        # Create sequences
        X, y = create_sequences(scaled_prices, seq_length)

        # Train/test split
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        routes_data[route_key] = {
            'scaler': scaler,
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'prices': prices,
            'scaled_prices': scaled_prices
        }

    print(f"[OK] Prepared {len(routes_data)} routes for LSTM training")

    return routes_data


# ─────────────────────────────────────────────────────────────────
# LSTM MODEL
# ─────────────────────────────────────────────────────────────────

def build_lstm_model(seq_length: int = 7) -> keras.Model:
    """
    Build LSTM neural network for time series prediction

    Architecture:
    Input (7 days) → LSTM (50 units) → Dropout → Dense → Output (next day price)
    """
    model = Sequential([
        # LSTM layer: learns temporal patterns
        LSTM(
            units=50,
            activation='relu',
            input_shape=(seq_length, 1),
            return_sequences=True  # Return full sequence
        ),
        Dropout(0.2),  # Prevent overfitting

        # Second LSTM layer for deeper learning
        LSTM(units=50, activation='relu'),
        Dropout(0.2),

        # Dense layers for final prediction
        Dense(units=25, activation='relu'),
        Dropout(0.1),

        # Output layer (single price prediction)
        Dense(units=1)
    ])

    # Compile model
    model.compile(
        optimizer='adam',
        loss='mse',  # Mean Squared Error
        metrics=['mae']  # Mean Absolute Error
    )

    return model


def train_lstm_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    epochs: int = 50,
    batch_size: int = 16
) -> keras.Model:
    """
    Train LSTM model
    """
    model = build_lstm_model(seq_length=X_train.shape[1])

    # Reshape for LSTM: (samples, seq_length, 1)
    X_train_reshaped = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
    X_test_reshaped = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

    # Early stopping to prevent overfitting
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True
    )

    # Train
    history = model.fit(
        X_train_reshaped,
        y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_test_reshaped, y_test),
        callbacks=[early_stop],
        verbose=1
    )

    return model, history


# ─────────────────────────────────────────────────────────────────
# INFERENCE FUNCTION (for backend integration)
# ─────────────────────────────────────────────────────────────────

def predict_7day_prices(
    model: keras.Model,
    last_sequence: np.ndarray,
    scaler,
    days_ahead: int = 7
) -> list:
    """
    Predict next 7 days of prices using LSTM

    Takes last 7 days of prices as input, predicts day 8, 9, ..., 14
    """
    predictions = []
    current_sequence = last_sequence.copy()

    for _ in range(days_ahead):
        # Reshape for model input
        input_seq = current_sequence.reshape(1, -1, 1)

        # Predict next price (normalized 0-1)
        next_pred_normalized = model.predict(input_seq, verbose=0)[0][0]

        # Store prediction
        predictions.append(next_pred_normalized)

        # Slide window: remove oldest, add newest
        current_sequence = np.append(current_sequence[1:], next_pred_normalized)

    # Inverse transform: convert from (0-1) back to actual prices
    predictions_normalized = np.array(predictions).reshape(-1, 1)
    predictions_actual = scaler.inverse_transform(predictions_normalized).flatten()

    return predictions_actual.astype(int).tolist()


# ─────────────────────────────────────────────────────────────────
# MAIN TRAINING PIPELINE
# ─────────────────────────────────────────────────────────────────

def train_and_save_lstm_models(output_dir: str = "../ml_models"):
    """
    Complete pipeline: generate data → train LSTM → save models
    """
    if not TENSORFLOW_AVAILABLE:
        print("❌ TensorFlow required. Install: pip install tensorflow")
        return

    import os
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "="*60)
    print("[*] LSTM MODEL TRAINING PIPELINE")
    print("="*60)

    # Step 1: Generate synthetic historical data
    print("\n[*] Step 1: Generating synthetic time series data...")
    df = generate_synthetic_timeseries_data(num_routes=30, days_per_route=60)

    # Step 2: Prepare data for LSTM
    print("\n[*] Step 2: Preparing sequences for LSTM...")
    routes_data = prepare_lstm_data(df, seq_length=7, test_size=0.2)

    # Step 3: Train models for each route
    print("\n[*] Step 3: Training LSTM models...")
    trained_models = {}
    route_metrics = {}

    for route_key, data in routes_data.items():
        print(f"\n   Training {route_key}...", end=" ")

        # Train model
        model, history = train_lstm_model(
            data['X_train'],
            data['y_train'],
            data['X_test'],
            data['y_test'],
            epochs=50,
            batch_size=16
        )

        trained_models[route_key] = model

        # Calculate metrics on test set
        X_test_reshaped = data['X_test'].reshape((data['X_test'].shape[0], data['X_test'].shape[1], 1))
        test_loss = model.evaluate(X_test_reshaped, data['y_test'], verbose=0)[0]

        route_metrics[route_key] = {
            'test_loss': float(test_loss),
            'train_samples': len(data['X_train']),
            'test_samples': len(data['X_test'])
        }

        print(f"OK (Loss: {test_loss:.4f})")

    # Step 4: Save models
    print("\n[*] Step 4: Saving models...")

    # Save individual route models
    for route_key, model in trained_models.items():
        model_path = f"{output_dir}/lstm_model_{route_key}.h5"
        model.save(model_path)
        print(f"   [OK] Saved: {model_path}")

    # Save routes data (scalers, preprocessed data)
    routes_data_for_save = {}
    for route_key, data in routes_data.items():
        routes_data_for_save[route_key] = {
            'scaler_min': float(data['scaler'].data_min_[0]),
            'scaler_max': float(data['scaler'].data_max_[0]),
            'scaler_range': float(data['scaler'].feature_range[1] - data['scaler'].feature_range[0]),
            'prices_mean': float(data['prices'].mean()),
            'prices_std': float(data['prices'].std()),
            'metrics': route_metrics.get(route_key, {})
        }

    routes_metadata_path = f"{output_dir}/lstm_routes_metadata.json"
    with open(routes_metadata_path, 'w') as f:
        json.dump(routes_data_for_save, f, indent=2)
    print(f"   [OK] Saved: {routes_metadata_path}")

    # Step 5: Summary
    print("\n" + "="*60)
    print("[SUMMARY] TRAINING COMPLETE")
    print("="*60)
    print(f"[OK] Routes trained: {len(trained_models)}")
    print(f"[OK] Models saved: {len(trained_models)} LSTM models")
    print(f"[OK] Metadata saved: routes configuration")
    print(f"\n[STATS] Average Test Loss: {np.mean([m['test_loss'] for m in route_metrics.values()]):.4f}")
    print("="*60 + "\n")

    return trained_models, routes_data


# ─────────────────────────────────────────────────────────────────
# EXAMPLE USAGE
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Train and save models
    models, data = train_and_save_lstm_models()

    # Example: Predict 7-day prices for a route
    if models:
        route_key = list(models.keys())[0]
        print(f"\n[EXAMPLE] Prediction for {route_key}:")

        model = models[route_key]
        route_data = data[route_key]

        # Get last 7 days of actual prices
        last_7_days_scaled = route_data['scaled_prices'][-7:]

        # Predict next 7 days
        predictions = predict_7day_prices(
            model,
            last_7_days_scaled,
            route_data['scaler'],
            days_ahead=7
        )

        print(f"\n   Last 7 days (actual):    {route_data['prices'][-7:].astype(int).tolist()}")
        print(f"   Next 7 days (predicted): {predictions}")
        print(f"\n   Trend: ", end="")
        if predictions[-1] > predictions[0]:
            print(f"INCREASING (+{predictions[-1] - predictions[0]})")
        else:
            print(f"DECREASING ({predictions[-1] - predictions[0]})")
