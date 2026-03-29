"""
Test script for Emergency ML Model
Tests various scenarios and edge cases
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import predict_emergency_priority, emergency_model, emergency_scaler

def test_model_loading():
    """Test if model loads correctly"""
    print("=" * 60)
    print("Test 1: Model Loading")
    print("=" * 60)
    assert emergency_model is not None, "Model should be loaded"
    assert hasattr(emergency_model, 'predict'), "Model should have predict method"
    print(f"[OK] Model loaded: {type(emergency_model).__name__}")
    print(f"[OK] Model expects {emergency_model.n_features_in_} features")
    print(f"[OK] Model classes: {list(emergency_model.classes_)}")
    print()

def test_basic_predictions():
    """Test basic prediction scenarios"""
    print("=" * 60)
    print("Test 2: Basic Predictions")
    print("=" * 60)
    
    test_cases = [
        {
            'name': 'Critical EMS',
            'params': {
                'symptoms': 'chest pain severe heart attack',
                'age': 70,
                'state': 'Karnataka',
                'zone': 'Urban',
                'day': 'Monday',
                'time_slot': 'Morning',
                'emergency_type': 'EMS',
                'weather': 'Clear'
            }
        },
        {
            'name': 'Traffic Accident',
            'params': {
                'symptoms': 'accident on highway',
                'age': 45,
                'state': 'Maharashtra',
                'zone': 'Highway',
                'day': 'Friday',
                'time_slot': 'Evening',
                'emergency_type': 'Traffic',
                'weather': 'Rain'
            }
        },
        {
            'name': 'Fire Emergency',
            'params': {
                'symptoms': 'fire in building',
                'age': 50,
                'state': 'Delhi',
                'zone': 'Urban',
                'day': 'Sunday',
                'time_slot': 'Night',
                'emergency_type': 'Fire',
                'weather': 'Fog'
            }
        },
        {
            'name': 'Low Priority',
            'params': {
                'symptoms': 'mild headache',
                'age': 25,
                'state': 'Kerala',
                'zone': 'Rural',
                'day': 'Tuesday',
                'time_slot': 'Afternoon',
                'emergency_type': 'EMS',
                'weather': 'Clear'
            }
        }
    ]
    
    for test_case in test_cases:
        try:
            priority, severity, score = predict_emergency_priority(**test_case['params'])
            print(f"[OK] {test_case['name']}: Priority={priority}, Severity={severity}, Score={score:.3f}")
            assert priority in ['Low', 'Medium', 'High', 'Critical'], f"Invalid priority: {priority}"
            assert severity in ['Mild', 'Moderate', 'Severe', 'Critical'], f"Invalid severity: {severity}"
            assert 0 <= score <= 1, f"Score should be between 0 and 1: {score}"
        except Exception as e:
            print(f"[ERROR] {test_case['name']}: Error - {e}")
            raise
    
    print()

def test_edge_cases():
    """Test edge cases"""
    print("=" * 60)
    print("Test 3: Edge Cases")
    print("=" * 60)
    
    edge_cases = [
        {
            'name': 'Missing all optional fields',
            'params': {'symptoms': 'pain'}
        },
        {
            'name': 'Empty symptoms',
            'params': {'symptoms': '', 'age': 30}
        },
        {
            'name': 'None age',
            'params': {'symptoms': 'chest pain', 'age': None}
        },
        {
            'name': 'Invalid state',
            'params': {'symptoms': 'pain', 'state': 'InvalidState'}
        },
        {
            'name': 'All fields None',
            'params': {
                'symptoms': None,
                'age': None,
                'state': None,
                'zone': None,
                'day': None,
                'time_slot': None,
                'emergency_type': None,
                'weather': None
            }
        }
    ]
    
    for test_case in edge_cases:
        try:
            priority, severity, score = predict_emergency_priority(**test_case['params'])
            print(f"[OK] {test_case['name']}: Priority={priority}, Severity={severity}, Score={score:.3f}")
            assert priority in ['Low', 'Medium', 'High', 'Critical'], f"Invalid priority: {priority}"
            assert 0 <= score <= 1, f"Score should be between 0 and 1: {score}"
        except Exception as e:
            print(f"[ERROR] {test_case['name']}: Error - {e}")
            raise
    
    print()

def test_feature_extraction():
    """Test feature extraction"""
    print("=" * 60)
    print("Test 4: Feature Extraction")
    print("=" * 60)
    
    # Test that features are correctly extracted
    test_params = {
        'symptoms': 'severe chest pain',
        'age': 65,
        'state': 'Karnataka',
        'zone': 'Urban',
        'day': 'Monday',
        'time_slot': 'Morning',
        'emergency_type': 'EMS',
        'weather': 'Clear'
    }
    
    try:
        priority, severity, score = predict_emergency_priority(**test_params)
        print(f"[OK] Feature extraction works: Priority={priority}, Score={score:.3f}")
        assert score > 0, "Score should be positive"
    except Exception as e:
        print(f"[ERROR] Feature extraction failed: {e}")
        raise
    
    print()

def test_all_states():
    """Test with different states"""
    print("=" * 60)
    print("Test 5: All States")
    print("=" * 60)
    
    states = ['Karnataka', 'Delhi', 'Maharashtra', 'Tamil Nadu', 'Kerala']
    
    for state in states:
        try:
            priority, severity, score = predict_emergency_priority(
                symptoms='emergency',
                age=50,
                state=state,
                zone='Urban',
                day='Monday',
                time_slot='Morning',
                emergency_type='EMS',
                weather='Clear'
            )
            print(f"[OK] State {state}: Priority={priority}, Score={score:.3f}")
        except Exception as e:
            print(f"[ERROR] State {state}: Error - {e}")
            raise
    
    print()

if __name__ == '__main__':
    try:
        test_model_loading()
        test_basic_predictions()
        test_edge_cases()
        test_feature_extraction()
        test_all_states()
        
        print("=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n[FAILED] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

