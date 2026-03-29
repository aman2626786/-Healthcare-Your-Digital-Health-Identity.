"""
Test script to verify the health risk prediction model works correctly.
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app import predict_health_risk, health_risk_model, model_scaler

def test_prediction():
    """Test the prediction function with sample data."""
    print("=" * 60)
    print("Testing Health Risk Prediction Model")
    print("=" * 60)
    
    if health_risk_model is None:
        print("[ERROR] Model not loaded!")
        return False
    
    print(f"[OK] Model loaded successfully")
    print(f"[OK] Scaler available: {model_scaler is not None}\n")
    
    # Test Case 1: Low Risk Patient
    print("Test Case 1: Low Risk Patient")
    print("-" * 60)
    user_data = {'age': 30, 'name': 'Test User'}
    symptoms = "Mild headache"
    diagnosis = "Routine checkup"
    treatment_status = "Stable"
    medicines = "Paracetamol"
    health_metrics = {
        'age': 30,
        'systolic_bp': 120,
        'diastolic_bp': 80,
        'bmi': 22.0,
        'cholesterol': 180,
        'glucose': 95,
        'smoking': 'Never',
        'alcohol': 'Never',
        'physical_activity': 'Active',
        'family_history': 'None'
    }
    
    risk_level, risk_score, should_emergency = predict_health_risk(
        user_data, symptoms, diagnosis, treatment_status, medicines, health_metrics
    )
    print(f"  Risk Level: {risk_level}")
    print(f"  Risk Score: {risk_score:.4f}")
    print(f"  Emergency Trigger: {should_emergency}")
    print()
    
    # Test Case 2: High Risk Patient
    print("Test Case 2: High Risk Patient")
    print("-" * 60)
    health_metrics_high = {
        'age': 65,
        'systolic_bp': 160,
        'diastolic_bp': 100,
        'bmi': 32.0,
        'cholesterol': 280,
        'glucose': 150,
        'smoking': 'Current',
        'alcohol': 'Regular',
        'physical_activity': 'Sedentary',
        'family_history': 'Heart Disease'
    }
    
    risk_level, risk_score, should_emergency = predict_health_risk(
        user_data, "Chest pain, difficulty breathing", "Hypertension, Diabetes", 
        "Under Observation", "Metformin, Aspirin, Lisinopril", health_metrics_high
    )
    print(f"  Risk Level: {risk_level}")
    print(f"  Risk Score: {risk_score:.4f}")
    print(f"  Emergency Trigger: {should_emergency}")
    print()
    
    # Test Case 3: Critical Patient
    print("Test Case 3: Critical Patient")
    print("-" * 60)
    risk_level, risk_score, should_emergency = predict_health_risk(
        user_data, "Severe chest pain, unconscious", "Heart attack", 
        "Critical", "Emergency medications", health_metrics_high
    )
    print(f"  Risk Level: {risk_level}")
    print(f"  Risk Score: {risk_score:.4f}")
    print(f"  Emergency Trigger: {should_emergency}")
    print()
    
    # Test Case 4: Medium Risk Patient
    print("Test Case 4: Medium Risk Patient")
    print("-" * 60)
    health_metrics_medium = {
        'age': 45,
        'systolic_bp': 135,
        'diastolic_bp': 88,
        'bmi': 27.0,
        'cholesterol': 220,
        'glucose': 110,
        'smoking': 'Former',
        'alcohol': 'Occasional',
        'physical_activity': 'Moderate',
        'family_history': 'Diabetes'
    }
    
    risk_level, risk_score, should_emergency = predict_health_risk(
        user_data, "Persistent cough, fatigue", "Upper respiratory infection", 
        "Under Observation", "Antibiotics, Cough syrup", health_metrics_medium
    )
    print(f"  Risk Level: {risk_level}")
    print(f"  Risk Score: {risk_score:.4f}")
    print(f"  Emergency Trigger: {should_emergency}")
    print()
    
    print("=" * 60)
    print("[SUCCESS] All test cases completed!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        test_prediction()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

