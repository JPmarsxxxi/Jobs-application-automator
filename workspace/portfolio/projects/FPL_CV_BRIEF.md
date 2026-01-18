# FPL Player Performance Prediction

**Time-series ML regression to predict Fantasy Premier League player points with focus on data leakage detection and hyperparameter optimization.**

## Tech Stack
Python • Scikit-learn • XGBoost • Pandas • NumPy • Matplotlib • FPL API

## Problem
Predict player total_points using historical performance data from Fantasy Premier League API.

## Solution Pipeline

```
FPL API → Feature Engineering → 3 Models → Hyperparameter Tuning → Data Leakage Fix
   ↓            ↓                    ↓              ↓                      ↓
2000+ rows  Time-series       LR/RF/XGBoost    Grid search         Clean features
            Rolling stats                     Optimal params        Realistic R²
```

## Models Compared

| Model | Initial R² | Clean R² | Key Insight |
|-------|-----------|----------|-------------|
| Linear Regression | 0.96 | 0.35 | Baseline, interpretable |
| Random Forest | 0.98 | 0.38 | Best clean performance |
| XGBoost | 0.99 | 0.32 | Overfits without tuning |

**Critical Finding:** Initial R² > 0.95 revealed data leakage. Clean models achieve realistic R² ≈ 0.35.

## Key Features

### 1. Data Collection
```python
# FPL API integration
response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
players_df = pd.DataFrame(response.json()['elements'])

# Historical performance
for player in players:
    history = requests.get(f'/api/element-summary/{player_id}/').json()
```

### 2. Time-Series Feature Engineering
```python
# Rolling statistics (7-day, 14-day windows)
df['rolling_7_avg'] = df.groupby('player')['total_points'].rolling(7).mean()
df['rolling_14_std'] = df.groupby('player')['total_points'].rolling(14).std()

# Lag features (prevent leakage)
df['lag_1_points'] = df.groupby('player')['total_points'].shift(1)
df['lag_3_points'] = df.groupby('player')['total_points'].shift(3)
```

### 3. Hyperparameter Optimization
```python
# Grid search for Random Forest
n_estimators_range = [50, 100, 200, 300]
max_depth_range = [5, 10, 15, 20, None]

for n in n_estimators_range:
    rf = RandomForestRegressor(n_estimators=n)
    val_rmse = cross_val_score(rf, X_val, y_val, scoring='neg_rmse')
    # Track best params
```

**Results:**
- Random Forest: n_estimators=200, max_depth=15
- XGBoost: learning_rate=0.1, max_depth=5

### 4. Data Leakage Detection & Fix

**Problem Identified:**
```
Initial features included:
- bonus (direct component of total_points formula)
- bps, ict_index (FPL-calculated metrics)
→ R² = 0.98 (unrealistically high)
```

**Solution:**
```python
# Remove leaky features
leaky_features = ['bonus', 'bps', 'influence', 'creativity', 'threat', 'ict_index']
clean_features = [f for f in features if f not in leaky_features]

# Retrain with clean features
→ R² = 0.35 (realistic for sports prediction)
```

## Performance Metrics

**Before Leakage Fix:**
- Test RMSE: 0.52 points
- Test R²: 0.98
- Status: ⚠️ Unrealistic (data leakage)

**After Leakage Fix:**
- Test RMSE: 1.85 points
- Test R²: 0.35
- Status: ✅ Realistic (production-ready)

## Skills Demonstrated

**Machine Learning:**
- Regression (Linear, Random Forest, XGBoost)
- Hyperparameter tuning (grid search)
- Cross-validation strategies
- Overfitting detection & mitigation

**Data Science:**
- Time-series feature engineering
- Rolling statistics and lag features
- Data leakage identification
- Train/val/test splitting (temporal ordering)

**Critical Thinking:**
- Questioned suspiciously high R² (0.98)
- Diagnosed root cause (target leakage)
- Fixed by removing leaky features
- Validated realistic performance

**Domain Knowledge:**
- FPL scoring system understanding
- Football statistics interpretation
- API integration and data collection

## Code Sample
```python
def detect_data_leakage(features, target):
    """Identify features with unrealistic predictive power"""
    
    # Train simple model
    lr = LinearRegression()
    lr.fit(X_train[features], y_train)
    r2 = lr.score(X_test[features], y_test)
    
    # Check individual feature correlations
    correlations = X_train[features].corrwith(y_train)
    
    # Flag suspicious features
    leaky = correlations[correlations.abs() > 0.9]
    
    if r2 > 0.95:
        print(f"⚠️ Warning: R² = {r2:.3f} suggests leakage")
        print(f"Suspicious features: {leaky.index.tolist()}")
    
    return leaky.index.tolist()
```

## Key Learnings

1. **High R² ≠ Good Model**
   - R² > 0.95 in real-world tasks often indicates problems
   - Always validate against domain expectations

2. **Feature Engineering > Model Choice**
   - Clean features with simple model > Leaky features with complex model
   - Time-series requires careful temporal alignment

3. **Production vs Research**
   - Research: Maximize metrics
   - Production: Ensure features available at prediction time

4. **Hyperparameter Impact**
   - Random Forest: 12% RMSE improvement with tuning
   - XGBoost: 8% RMSE improvement
   - Diminishing returns beyond certain complexity

## Visualizations Created
- Model comparison bar charts (RMSE, MAE, R²)
- Prediction vs actual scatter plots
- Residual distribution analysis
- Feature importance rankings
- Hyperparameter tuning curves

---

**Status:** Complete • **Type:** Academic coursework + portfolio project • **Environment:** Python/Jupyter
