# Health Risk Prediction Model

## Overview
This directory contains the trained SVM (Support Vector Machine) model for health risk prediction. The model predicts patient risk levels based on health metrics and medical records.

## Model Details

- **Algorithm**: SVM (Support Vector Machine) with RBF kernel
- **Features**: 13 health metrics
- **Classes**: 4 risk levels (Low, Medium, High, Critical)
- **Accuracy**: ~96% on test set
- **Format**: Pickle file containing model, scaler, and metadata

## Features Used

1. **age_normalized** - Patient age normalized to 0-1
2. **symptom_severity** - Encoded severity of symptoms (0-1)
3. **diagnosis_severity** - Encoded severity of diagnosis (0-1)
4. **treatment_severity** - Encoded treatment status (0-1)
5. **medicine_complexity** - Number of medicines normalized (0-1)
6. **bp_normalized** - Blood pressure risk score (0-1)
7. **bmi_normalized** - BMI risk score (0-1)
8. **cholesterol_normalized** - Cholesterol risk score (0-1)
9. **glucose_normalized** - Glucose risk score (0-1)
10. **smoking_risk** - Smoking status risk (0-1)
11. **alcohol_risk** - Alcohol consumption risk (0-1)
12. **activity_risk** - Physical activity risk (inverted, 0-1)
13. **family_history_risk** - Family history risk (0-1)

## Files

- `svm_health_risk_model.pkl` - Trained model with scaler and metadata
- `README.md` - This file

## Training the Model

To retrain the model with new data or different parameters:

```bash
python train_model.py
```

The training script will:
1. Generate synthetic training data (5000 samples)
2. Split data into train/test sets (80/20)
3. Scale features using StandardScaler
4. Train SVM model with RBF kernel
5. Evaluate model performance
6. Save model to `pkl/svm_health_risk_model.pkl`

## Model Usage

The model is automatically loaded when the Flask app starts. It's used in the `predict_health_risk()` function in `app.py`.

### Example Usage

```python
from app import predict_health_risk

health_metrics = {
    'age': 45,
    'systolic_bp': 140,
    'diastolic_bp': 90,
    'bmi': 25.5,
    'cholesterol': 220,
    'glucose': 110,
    'smoking': 'Former',
    'alcohol': 'Occasional',
    'physical_activity': 'Moderate',
    'family_history': 'Diabetes'
}

risk_level, risk_score, should_emergency = predict_health_risk(
    user_data, symptoms, diagnosis, treatment_status, medicines, health_metrics
)
```

## Risk Levels

- **Low** (0): Risk score < 0.4, no emergency
- **Medium** (1): Risk score 0.4-0.6, no emergency
- **High** (2): Risk score 0.6-0.8, emergency triggered
- **Critical** (3): Risk score >= 0.8, emergency triggered

## Model Performance

- **Training Accuracy**: 98.82%
- **Test Accuracy**: 95.90%
- **Precision/Recall**:
  - Low: 0.97/0.96
  - Medium: 0.96/0.96
  - High: 0.61/0.82
  - Critical: 1.00/0.97

## Notes

- The model uses feature scaling for optimal performance
- If the model fails to load, the system falls back to rule-based risk assessment
- The model is trained on synthetic data; for production, retrain with real patient data
- Model predictions are combined with rule-based overrides for critical cases

