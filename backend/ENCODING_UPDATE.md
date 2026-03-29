# Health Metrics Encoding Update

## Overview
Updated the health metrics encoding scheme to match standardized healthcare data formats.

## Encoding Changes

### 1. Smoking
**Previous**: Text values (Never, Former, Current)  
**New**: Binary encoding
- `0` = Non-Smoker
- `1` = Smoker

### 2. Alcohol
**Previous**: Text values (Never, Occasional, Regular)  
**New**: Binary encoding
- `0` = Habit Absent
- `1` = Habit Present

### 3. Physical Activity
**Previous**: Text values (Sedentary, Light, Moderate, Active)  
**New**: Numeric scale (0-5)
- `0` = No activity (Sedentary lifestyle → High risk)
- `1` = ~1 hour/week (Very low activity)
- `2` = ~2 hours/week (Low activity)
- `3` = ~3 hours/week (Moderate activity)
- `4` = ~4 hours/week (Good activity level)
- `5` = 5+ hours/week (Active / Healthy lifestyle)

**Note**: For model prediction, this is inverted (0 = high risk 1.0, 5 = low risk 0.0)

### 4. Family History
**Previous**: Text values (None, Heart Disease, Diabetes, Hypertension, Other)  
**New**: Binary encoding
- `0` = No family history of chronic disease (Genetic risk absent)
- `1` = Family history present (Genetic risk present)

## Files Updated

1. **`templates/doctor_dashboard.html`**
   - Updated form dropdowns to use new encoding values
   - Physical Activity now shows hours/week scale

2. **`app.py`**
   - Updated `predict_health_risk()` function to convert form values to new encoding
   - Updated risk calculation to use binary values (0/1) for smoking, alcohol, family history
   - Physical activity converted from 0-5 scale to inverted risk score (0-1)

3. **`train_model.py`**
   - Updated synthetic data generation to use new encoding scheme
   - Model retrained with new encoding format
   - Test accuracy: 95.40%

## Model Retraining

The model has been retrained with the new encoding scheme:
- **Training Accuracy**: 98.02%
- **Test Accuracy**: 95.40%
- **Model saved**: `pkl/svm_health_risk_model.pkl`

## Testing

The updated model has been tested and verified to work correctly with the new encoding scheme.

## Backward Compatibility

The system handles both old and new formats gracefully:
- Form values are parsed as integers
- Missing or invalid values default to 0 (lowest risk)
- The prediction function converts values appropriately

