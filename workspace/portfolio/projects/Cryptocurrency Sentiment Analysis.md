# Crypto Sentiment Analysis: Bitcoin Price Prediction

**Research project testing whether social media sentiment predicts Bitcoin price movements using multi-source data and dual NLP approaches.**

## Research Question
Can social media sentiment predict hourly Bitcoin price movements?

**Answer:** No. Sentiment is reactive (follows price), not predictive (leads price).

## Tech Stack
Python • PyTorch • Transformers • Scikit-learn • CryptoBERT • PRAW • Telethon • YouTube API • Pandas

## What It Does

Collects data from 5 sources, analyzes sentiment with 2 different encoders, trains 3 ML models, and compares results.

```
Reddit + Telegram + YouTube + News → Sentiment Analysis → Price Prediction
          ↓                              ↓                      ↓
    500-1000 posts              Custom vs CryptoBERT      52.9% accuracy
                                                         (baseline: 50.9%)
```

## Key Results

| Metric | Custom Encoder | CryptoBERT | Baseline |
|--------|----------------|------------|----------|
| **Test Accuracy** | 52.4% | 52.9% | 50.9% |
| **Improvement** | +1.5% | +2.0% | - |
| **Conclusion** | Barely better than random guessing | ← |

## Technical Implementation

### 1. Multi-Source Data Collection
```python
class PriceDataCollector:
    """Collect hourly Bitcoin prices from CryptoCompare API"""
    def get_historical_prices(self, symbol='BTC', limit=2000):
        # Fetches OHLCV data with timestamps
        # Aligns with sentiment data for feature engineering
```

**Collected:**
- 2000+ hours of Bitcoin prices
- 500-1000 Reddit posts/comments
- Telegram channel messages
- YouTube video comments
- Google News headlines

### 2. Dual Sentiment Analysis

**Custom Encoder:**
- Simple LSTM network
- Trained on Twitter sentiment + crypto examples
- 64.8% classification accuracy
- Fast inference

**CryptoBERT:**
- Pre-trained transformer (ElKulako/cryptobert)
- Domain-specific (cryptocurrency text)
- Classifies: Bullish/Bearish/Neutral
- Sophisticated but only 0.5% better

### 3. Machine Learning Pipeline
```python
# Trained 3 models with both sentiment encoders
models = {
    'Logistic Regression': 52.9%,  # Best performer
    'Random Forest': 52.3%,
    'Gradient Boosting': 52.3%
}
# All barely beat baseline (50.9% = random)
```

**Features engineered:**
- Sentiment scores (positive, negative, neutral)
- Temporal (hour, day of week)
- Technical indicators (price change, volume)
- Aggregated statistics (mean, std, max)

## Key Findings

**1. Sentiment Doesn't Predict Hourly Prices**
- Only 1.5-2% improvement over random guessing
- Market moves → People react → Sentiment forms
- Not: Sentiment → Market moves

**2. Model Sophistication Doesn't Help**
- CryptoBERT (complex, pre-trained) vs Custom (simple)
- Difference: 0.5% accuracy
- Problem is data, not encoding quality

**3. Feature Importance Analysis**
```
Most Predictive Features:
1. Previous price change (65%)
2. Time of day (15%)
3. Volume indicators (12%)
4. Sentiment scores (8%)  ← Least important!
```

## Academic Value

**Why negative results matter:**
- Prevents wasted effort on ineffective strategies
- Demonstrates scientific rigor (test hypotheses properly)
- Clear methodology for reproducibility
- Valuable for literature: "What doesn't work"

**Potential impact:**
- Saves traders from relying on hourly sentiment
- Suggests sentiment may work at longer timeframes (daily/weekly)
- Shows simple models can match expensive pre-trained alternatives

## Skills Demonstrated

**Data Engineering:**
- Multi-API integration (Reddit, Telegram, YouTube, News, Crypto prices)
- Parallel data collection with error handling
- Data alignment and synchronization
- JSON persistence and loading

**NLP & Deep Learning:**
- Custom LSTM sentiment classifier
- Transfer learning with pre-trained transformers (CryptoBERT)
- Tokenization and text preprocessing
- Model comparison and evaluation

**Machine Learning:**
- Feature engineering (sentiment, temporal, technical)
- Multiple algorithms (Logistic Regression, Random Forest, Gradient Boosting)
- Train/test split with temporal ordering
- Comprehensive evaluation (accuracy, precision, recall, F1, confusion matrices)

**Data Science:**
- Hypothesis testing and validation
- Statistical analysis and interpretation
- Visualization (performance charts, confusion matrices, feature importance)
- Critical thinking about model limitations

## Code Sample

```python
# Example: Encoding sentiment with both approaches
def compare_encoders(text_data):
    """Compare Custom vs CryptoBERT sentiment encoding"""
    
    # Custom encoder (simple, fast)
    custom_scores = custom_model.predict(text_data)
    
    # CryptoBERT (sophisticated, slower)
    tokenizer = AutoTokenizer.from_pretrained("ElKulako/cryptobert")
    model = AutoModelForSequenceClassification.from_pretrained("ElKulako/cryptobert")
    
    inputs = tokenizer(text_data, return_tensors="pt", padding=True)
    outputs = model(**inputs)
    cryptobert_scores = F.softmax(outputs.logits, dim=1)
    
    # Result: CryptoBERT only 0.5% better despite complexity
    return custom_scores, cryptobert_scores
```

## Practical Implications

**For Traders:**
❌ Don't use hourly social media sentiment for trading
✅ Consider sentiment as lagging indicator
✅ Test at longer timeframes (daily/weekly)

**For Researchers:**
✅ Negative results are valuable
✅ Simple baselines can outperform complex models
✅ Data quality > Model sophistication

**For ML Engineers:**
✅ Always compare against baselines
✅ Domain-specific models not always worth the cost
✅ Proper evaluation prevents overfitting

## Future Enhancements

- Test daily/weekly timeframes
- Add Twitter/X real-time stream
- Include on-chain metrics (whale movements)
- Event-driven analysis (news, regulations)
- Multi-cryptocurrency comparison
- Market regime classification (bull/bear)

## Performance Metrics

- **Data Collection:** 2000+ hours of aligned data
- **Models Trained:** 6 (3 algorithms × 2 encoders)
- **Processing Time:** ~15 minutes total (Colab GPU)
- **Final Accuracy:** 52.9% (vs 50.9% baseline)
- **Conclusion:** Sentiment lacks predictive power at hourly timeframes

---

**GitHub:** [Repository Link] • **Notebook:** Jupyter/Colab ready • **Status:** Complete research project

**Note:** Educational research only. Not financial advice.
