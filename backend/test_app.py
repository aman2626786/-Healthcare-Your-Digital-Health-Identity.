"""
Test script for Swasthya SAMPARK application
Tests for common bugs and errors
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, predict_health_risk, health_risk_model
from app import get_db_connection, init_db

def test_imports():
    """Test if all imports work"""
    print("\n=== Testing Imports ===")
    try:
        from flask import Flask
        import sqlite3
        import numpy as np
        import pickle
        print("[OK] All imports successful")
        return True
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        return False

def test_database():
    """Test database connection and schema"""
    print("\n=== Testing Database ===")
    try:
        init_db()
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if all tables exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        required_tables = ['users', 'doctors', 'hospitals', 'records', 'emergencies']
        
        missing = [t for t in required_tables if t not in tables]
        if missing:
            print(f"[ERROR] Missing tables: {missing}")
            return False
        
        # Check if columns exist
        cur.execute("PRAGMA table_info(records)")
        record_columns = [row[1] for row in cur.fetchall()]
        required_columns = ['risk_level', 'risk_score']
        missing_cols = [c for c in required_columns if c not in record_columns]
        if missing_cols:
            print(f"[WARNING] Missing columns in records: {missing_cols}")
        
        conn.close()
        print("[OK] Database connection and schema OK")
        return True
    except Exception as e:
        print(f"[ERROR] Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_loading():
    """Test model loading"""
    print("\n=== Testing Model Loading ===")
    if health_risk_model is None:
        print("[WARNING] Model not loaded - using rule-based fallback")
        return True  # Not a critical error
    else:
        print("[OK] Model loaded successfully")
        return True

def test_prediction_function():
    """Test prediction function"""
    print("\n=== Testing Prediction Function ===")
    try:
        # Test with critical case
        test_data = {'age': 65}
        result = predict_health_risk(
            test_data, 
            'chest pain severe difficulty breathing', 
            'heart attack', 
            'Critical', 
            'aspirin, nitroglycerin'
        )
        print(f"[OK] Prediction test 1 (Critical): {result}")
        assert result[0] in ['Critical', 'High'], "Should detect high risk"
        assert result[2] == True, "Should trigger emergency"
        
        # Test with low risk case
        result2 = predict_health_risk(
            {'age': 30},
            'mild headache',
            'routine checkup',
            'Stable',
            'paracetamol'
        )
        print(f"[OK] Prediction test 2 (Low): {result2}")
        
        # Test with None user_data
        result3 = predict_health_risk(None, 'fever', 'infection', 'Stable', 'antibiotic')
        print(f"[OK] Prediction test 3 (None data): {result3}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Prediction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_routes():
    """Test key routes"""
    print("\n=== Testing Routes ===")
    client = app.test_client()
    
    routes_to_test = [
        ('/', 'GET', 200),
        ('/hospital/login', 'GET', 200),
        ('/doctor/login', 'GET', 200),
        ('/user/login', 'GET', 200),
        ('/emergency', 'GET', 200),
    ]
    
    passed = 0
    failed = 0
    
    for route, method, expected_status in routes_to_test:
        try:
            if method == 'GET':
                response = client.get(route)
            else:
                response = client.post(route)
            
            if response.status_code == expected_status:
                print(f"[OK] {route} - Status: {response.status_code}")
                passed += 1
            else:
                print(f"[WARNING] {route} - Expected {expected_status}, got {response.status_code}")
                failed += 1
        except Exception as e:
            print(f"[ERROR] {route} - Exception: {e}")
            failed += 1
    
    print(f"\nRoutes: {passed} passed, {failed} failed")
    return failed == 0

def test_utilities():
    """Test utility functions"""
    print("\n=== Testing Utility Functions ===")
    try:
        from app import generate_health_id, generate_health_qr
        
        # Test health ID generation
        health_id = generate_health_id()
        assert health_id.startswith('H-'), "Health ID should start with H-"
        assert len(health_id) > 5, "Health ID should have reasonable length"
        print(f"[OK] Health ID generation: {health_id}")
        
        # Test QR generation
        qr_path = generate_health_qr(health_id)
        assert 'qr/' in qr_path, "QR path should contain qr/"
        print(f"[OK] QR generation: {qr_path}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Utility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("SWASTHYA SAMPARK - Application Test Suite")
    print("=" * 50)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database()))
    results.append(("Model Loading", test_model_loading()))
    results.append(("Prediction Function", test_prediction_function()))
    results.append(("Routes", test_routes()))
    results.append(("Utilities", test_utilities()))
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

