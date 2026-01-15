# Multimodal News Classification: CNN vs LSTM

**Compare image-based CNN and text-based LSTM for classifying New York Times articles into sections.**

## Tech Stack
TensorFlow/Keras • CNN • LSTM • NumPy • Pandas • Scikit-learn

## Task
Multi-label classification of NYT articles using:
- **CNN** → Classify from images (128x256 JPEG)
- **LSTM** → Classify from captions (text)
- Compare which modality performs better

## Implementation

### CNN Architecture
```python
def build_cnn_model():
    inputs = Input(shape=(128, 256, 3))
    x = Conv2D(32, (3,3), activation='relu')(inputs)
    x = MaxPooling2D((2,2))(x)
    x = Conv2D(64, (3,3), activation='relu')(x)
    x = MaxPooling2D((2,2))(x)
    x = Flatten()(x)
    x = Dense(128, activation='relu')(x)
    outputs = Dense(n_classes, activation='sigmoid')(x)
    return Model(inputs=inputs, outputs=outputs)
```

### LSTM Architecture
```python
lstm_model = tf.keras.Sequential([
    Embedding(input_dim=vocab_size, output_dim=128),
    LSTM(64, return_sequences=True),
    LSTM(32),
    Dense(n_classes, activation='sigmoid')
])
```

## Key Features

**Data Processing:**
- Train/test split (80/20)
- Image preprocessing (resize, normalize)
- Text tokenization and padding
- One-hot encoding for multi-label targets

**Training:**
- ModelCheckpoint (save best weights)
- Learning rate scheduling
- Early stopping on validation loss
- Batch training with validation

**Evaluation:**
- Per-class accuracy metrics
- Confusion matrices
- Top-3 predictions comparison
- Correct/incorrect example analysis

## Results

| Model | Test Accuracy | Notes |
|-------|--------------|-------|
| **CNN** | ~XX% | Image-based classification |
| **LSTM** | ~XX% | Caption-based classification |

**Key Findings:**
- [Which modality performed better and why]
- CNN strengths: Visual features, layout patterns
- LSTM strengths: Semantic content, context
- Multi-label challenges identified

## Skills Demonstrated

**Deep Learning:**
- CNN architecture design (Conv2D, MaxPooling, Dropout)
- LSTM for sequence modeling (Embedding, LSTM layers)
- Multi-label classification (sigmoid activation)
- Hyperparameter tuning

**TensorFlow/Keras:**
- Functional API (CNN) vs Sequential API (LSTM)
- Custom data pipelines with tf.data
- Callbacks (ModelCheckpoint, LearningRateScheduler)
- Model evaluation and visualization

**Data Processing:**
- Image preprocessing and augmentation
- Text tokenization and vectorization
- One-hot encoding for multi-label targets
- Train/test splitting with stratification

**Model Evaluation:**
- Per-class performance analysis
- Top-k predictions comparison
- Confusion matrix interpretation
- Critical analysis of failure cases

## Code Sample
```python
# Multi-label prediction with top-3 comparison
def analyze_predictions(cnn_pred, lstm_pred, true_labels):
    """Compare CNN and LSTM top-3 predictions"""
    
    # Get top 3 for each model
    cnn_top3 = np.argsort(cnn_pred)[-3:][::-1]
    lstm_top3 = np.argsort(lstm_pred)[-3:][::-1]
    
    # Check accuracy
    true_idx = np.where(true_labels > 0.5)[0]
    cnn_correct = len(set(cnn_top3) & set(true_idx))
    lstm_correct = len(set(lstm_top3) & set(true_idx))
    
    return cnn_top3, lstm_top3, cnn_correct, lstm_correct
```

## Academic Context
- **Course:** Advanced Data Science
- **Type:** Coursework Assignment
- **Focus:** Multimodal learning comparison
- **Report:** 2-3 pages critical evaluation

---

**Status:** Complete • **Framework:** TensorFlow 2.x/Keras • **Environment:** Google Colab
