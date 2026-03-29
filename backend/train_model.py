"""
Health Risk Prediction Model Training Script
Trains an SVM model for health risk prediction using health metrics.
"""

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
import os

# Set random seed for reproducibility
np.random.seed(42)

def generate_synthetic_data(n_samples=5000):
    """
    Generate synthetic training data based on realistic health scenarios.
    Returns: (X, y) where X is features and y is risk level (0=Low, 1=Medium, 2=High, 3=Critical)
    """
    print("Generating synthetic training data...")
    
    features = []
    labels = []
    
    for i in range(n_samples):
        # Age (normalized 0-1)
        age = np.random.randint(18, 85)
        age_normalized = min(age / 100.0, 1.0)
        
        # Symptom severity (0-1)
        symptom_severity = np.random.beta(2, 5)  # Skewed towards lower severity
        
        # Diagnosis severity (0-1)
        diagnosis_severity = np.random.beta(2, 5)
        
        # Treatment status severity (0-1)
        treatment_options = [0.1, 0.4, 0.8, 1.0]  # Recovered, Stable, Under Observation, Critical
        treatment_severity = np.random.choice(treatment_options, p=[0.4, 0.3, 0.2, 0.1])
        
        # Medicine complexity (0-1)
        medicine_complexity = np.random.beta(2, 4)
        
        # BP normalized (0-1)
        systolic = np.random.normal(120, 20)
        diastolic = np.random.normal(80, 15)
        if systolic > 140 or diastolic > 90:
            bp_normalized = min(1.0, 0.5 + (systolic - 140) / 100)
        elif systolic < 90 or diastolic < 60:
            bp_normalized = 0.8
        else:
            bp_normalized = 0.3
        
        # BMI normalized (0-1)
        bmi = np.random.normal(25, 5)
        if bmi < 18.5:
            bmi_normalized = 0.6
        elif bmi > 30:
            bmi_normalized = 1.0
        elif bmi > 25:
            bmi_normalized = 0.7
        else:
            bmi_normalized = 0.3
        
        # Cholesterol normalized (0-1)
        cholesterol = np.random.normal(200, 40)
        if cholesterol > 240:
            cholesterol_normalized = 1.0
        elif cholesterol > 200:
            cholesterol_normalized = 0.7
        else:
            cholesterol_normalized = 0.3
        
        # Glucose normalized (0-1)
        glucose = np.random.normal(100, 25)
        if glucose > 125:
            glucose_normalized = 1.0
        elif glucose > 100:
            glucose_normalized = 0.7
        else:
            glucose_normalized = 0.3
        
        # Smoking: 0 = Non-Smoker, 1 = Smoker (binary)
        smoking_risk = np.random.choice([0, 1], p=[0.7, 0.3])
        
        # Alcohol: 0 = Habit Absent, 1 = Habit Present (binary)
        alcohol_risk = np.random.choice([0, 1], p=[0.6, 0.4])
        
        # Physical Activity: 0-5 scale (0 = No activity, 5 = 5+ hours/week)
        # For model: normalize to 0-1, but higher activity = lower risk (inverted)
        activity_value = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.2, 0.15, 0.15, 0.2, 0.15, 0.15])
        activity_risk = 1.0 - (activity_value / 5.0)  # Invert: 0 (no activity) = 1.0, 5 (active) = 0.0
        
        # Family History: 0 = No family history, 1 = Family history present (binary)
        family_history_risk = np.random.choice([0, 1], p=[0.7, 0.3])
        
        # Create feature vector
        feature_vector = [
            age_normalized,
            symptom_severity,
            diagnosis_severity,
            treatment_severity,
            medicine_complexity,
            bp_normalized,
            bmi_normalized,
            cholesterol_normalized,
            glucose_normalized,
            smoking_risk,
            alcohol_risk,
            activity_risk,
            family_history_risk
        ]
        
        # Calculate risk score (weighted combination)
        base_risk = (symptom_severity * 0.2 + diagnosis_severity * 0.2 + 
                    treatment_severity * 0.2 + medicine_complexity * 0.1)
        
        # Health metrics risk calculation
        # smoking_risk, alcohol_risk, family_history_risk are now 0 or 1 (binary)
        # activity_risk is inverted (0 = no activity = high risk 1.0, 5 = active = low risk 0.0)
        health_risk = (bp_normalized * 0.1 + bmi_normalized * 0.1 + 
                      cholesterol_normalized * 0.05 + glucose_normalized * 0.05 +
                      float(smoking_risk) * 0.05 + float(alcohol_risk) * 0.03 + 
                      activity_risk * 0.03 + float(family_history_risk) * 0.02)
        
        risk_score = min(base_risk + health_risk, 1.0)
        
        # Assign label based on risk score
        if risk_score >= 0.8 or treatment_severity >= 0.9:
            label = 3  # Critical
        elif risk_score >= 0.6:
            label = 2  # High
        elif risk_score >= 0.4:
            label = 1  # Medium
        else:
            label = 0  # Low
        
        # Add some noise: critical symptoms/diagnosis override
        if symptom_severity >= 0.9 or diagnosis_severity >= 0.9:
            if label < 2:
                label = 2  # At least High
        
        features.append(feature_vector)
        labels.append(label)
    
    return np.array(features), np.array(labels)


def train_model():
    """Train the SVM model and save it."""
    print("=" * 60)
    print("Health Risk Prediction Model Training")
    print("=" * 60)
    
    # Generate training data
    X, y = generate_synthetic_data(n_samples=5000)
    
    print(f"\nGenerated {len(X)} training samples")
    print(f"Feature shape: {X.shape}")
    print(f"Label distribution:")
    unique, counts = np.unique(y, return_counts=True)
    for label, count in zip(unique, counts):
        label_name = ['Low', 'Medium', 'High', 'Critical'][label]
        print(f"  {label_name}: {count} ({count/len(y)*100:.1f}%)")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Scale features
    print("\nScaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train SVM model
    print("\nTraining SVM model...")
    # Using RBF kernel with balanced class weights
    model = SVC(
        kernel='rbf',
        C=1.0,
        gamma='scale',
        probability=True,  # Enable predict_proba
        class_weight='balanced',  # Handle class imbalance
        random_state=42
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    print("\nEvaluating model...")
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    train_accuracy = accuracy_score(y_train, y_train_pred)
    test_accuracy = accuracy_score(y_test, y_test_pred)
    
    print(f"\nTraining Accuracy: {train_accuracy:.4f}")
    print(f"Test Accuracy: {test_accuracy:.4f}")
    
    print("\nClassification Report (Test Set):")
    print(classification_report(y_test, y_test_pred, 
                                target_names=['Low', 'Medium', 'High', 'Critical']))
    
    print("\nConfusion Matrix (Test Set):")
    print(confusion_matrix(y_test, y_test_pred))
    
    # Save model and scaler
    model_dir = os.path.join(os.path.dirname(__file__), 'pkl')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'svm_health_risk_model.pkl')
    scaler_path = os.path.join(model_dir, 'scaler.pkl')
    
    # Create a combined model object that includes both model and scaler
    model_package = {
        'model': model,
        'scaler': scaler,
        'feature_names': [
            'age_normalized',
            'symptom_severity',
            'diagnosis_severity',
            'treatment_severity',
            'medicine_complexity',
            'bp_normalized',
            'bmi_normalized',
            'cholesterol_normalized',
            'glucose_normalized',
            'smoking_risk',
            'alcohol_risk',
            'activity_risk',
            'family_history_risk'
        ]
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_package, f)
    
    print(f"\n[SUCCESS] Model saved to: {model_path}")
    print(f"[SUCCESS] Scaler saved to: {scaler_path}")
    print("\nModel training completed successfully!")
    
    return model, scaler, test_accuracy


if __name__ == '__main__':
    try:
        model, scaler, accuracy = train_model()
        print(f"\n{'='*60}")
        print("Training Summary:")
        print(f"  Model Type: SVM (RBF Kernel)")
        print(f"  Test Accuracy: {accuracy:.4f}")
        print(f"  Features: 13")
        print(f"  Classes: 4 (Low, Medium, High, Critical)")
        print(f"{'='*60}")
    except Exception as e:
        print(f"\n[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()

