#!/usr/bin/env python3
"""
Backend API Testing for TPRM Job Search Automation System
Tests all backend endpoints and functionality
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
        return None

BACKEND_URL = get_backend_url()
if not BACKEND_URL:
    print("ERROR: Could not get REACT_APP_BACKEND_URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BACKEND_URL}/api"

print(f"Testing backend at: {API_BASE}")
print("=" * 60)

def test_health_check():
    """Test 1: Basic API Health Check - GET /api/"""
    print("\n🔍 TEST 1: API Health Check")
    print("-" * 30)
    
    try:
        response = requests.get(f"{API_BASE}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if "message" in data and "status" in data:
                print("✅ PASS: Health check endpoint working")
                return True
            else:
                print("❌ FAIL: Invalid response format")
                return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Request failed - {e}")
        return False

def test_job_search():
    """Test 2: Job Search Functionality - POST /api/search-jobs"""
    print("\n🔍 TEST 2: Job Search Functionality")
    print("-" * 30)
    
    # Test data for Third Party Risk Assessment jobs
    test_payload = {
        "query": "Third Party Risk Assessment",
        "location": "Bangalore India OR remote",
        "days_filter": 1
    }
    
    try:
        print(f"Sending request: {json.dumps(test_payload, indent=2)}")
        response = requests.post(
            f"{API_BASE}/search-jobs", 
            json=test_payload,
            timeout=30  # Longer timeout for search operations
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Jobs found: {data.get('total_count', 0)}")
            print(f"Search query: {data.get('search_query', 'N/A')}")
            
            # Check response structure
            required_fields = ['jobs', 'total_count', 'search_query', 'search_date']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ FAIL: Missing fields: {missing_fields}")
                return False
            
            # Check if jobs have proper structure
            if data['jobs']:
                sample_job = data['jobs'][0]
                job_fields = ['id', 'job_title', 'company_name', 'job_link', 'location', 'keywords', 'technical_skills']
                missing_job_fields = [field for field in job_fields if field not in sample_job]
                
                if missing_job_fields:
                    print(f"❌ FAIL: Job missing fields: {missing_job_fields}")
                    return False
                
                print(f"Sample job: {sample_job['job_title']} at {sample_job['company_name']}")
                print(f"Keywords: {sample_job['keywords'][:3]}...")
                print(f"Skills: {sample_job['technical_skills'][:3]}...")
            
            print("✅ PASS: Job search functionality working")
            return True
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Request failed - {e}")
        return False

def test_email_functionality():
    """Test 3: Email Test - POST /api/send-test-email"""
    print("\n🔍 TEST 3: Email Functionality")
    print("-" * 30)
    
    try:
        response = requests.post(f"{API_BASE}/send-test-email", timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if "message" in data and "successfully" in data["message"].lower():
                print("✅ PASS: Email functionality working")
                return True
            else:
                print("❌ FAIL: Unexpected response message")
                return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Request failed - {e}")
        return False

def test_manual_search_trigger():
    """Test 4: Manual Search Trigger - POST /api/trigger-manual-search"""
    print("\n🔍 TEST 4: Manual Search Trigger (Full Automation Flow)")
    print("-" * 30)
    
    try:
        print("Triggering manual search (this may take 30+ seconds)...")
        response = requests.post(f"{API_BASE}/trigger-manual-search", timeout=60)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if "message" in data and "completed" in data["message"].lower():
                print("✅ PASS: Manual search trigger working")
                return True
            else:
                print("❌ FAIL: Unexpected response message")
                return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Request failed - {e}")
        return False

def test_job_results_storage():
    """Test 5: Job Results Storage - GET /api/job-results"""
    print("\n🔍 TEST 5: Job Results Storage (MongoDB)")
    print("-" * 30)
    
    try:
        response = requests.get(f"{API_BASE}/job-results", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Stored results count: {len(data)}")
            
            if isinstance(data, list):
                if data:
                    sample_result = data[0]
                    required_fields = ['jobs', 'total_count', 'search_query', 'search_date']
                    missing_fields = [field for field in required_fields if field not in sample_result]
                    
                    if missing_fields:
                        print(f"❌ FAIL: Missing fields in stored result: {missing_fields}")
                        return False
                    
                    print(f"Latest search: {sample_result['search_query']}")
                    print(f"Jobs found: {sample_result['total_count']}")
                    print(f"Search date: {sample_result['search_date']}")
                else:
                    print("ℹ️  INFO: No stored results found (database empty)")
                
                print("✅ PASS: Job results storage working")
                return True
            else:
                print("❌ FAIL: Expected list response")
                return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Request failed - {e}")
        return False

def test_24_hour_filtering():
    """Test 6: 24-hour Job Filtering Logic"""
    print("\n🔍 TEST 6: 24-hour Job Filtering")
    print("-" * 30)
    
    # Test with different days_filter values
    test_cases = [
        {"days_filter": 1, "description": "24 hours (1 day)"},
        {"days_filter": 7, "description": "7 days (should still work)"}
    ]
    
    for test_case in test_cases:
        try:
            payload = {
                "query": "Third Party Risk Assessment",
                "location": "Bangalore India OR remote",
                "days_filter": test_case["days_filter"]
            }
            
            print(f"Testing {test_case['description']} filter...")
            response = requests.post(f"{API_BASE}/search-jobs", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Jobs found with {test_case['description']}: {data.get('total_count', 0)}")
            else:
                print(f"  ❌ FAIL: Status {response.status_code} for {test_case['description']}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ FAIL: Request failed for {test_case['description']} - {e}")
            return False
    
    print("✅ PASS: 24-hour filtering functionality working")
    return True

def run_all_tests():
    """Run all backend tests"""
    print("🚀 STARTING TPRM JOB SEARCH BACKEND TESTS")
    print("=" * 60)
    print(f"Backend URL: {API_BASE}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("API Health Check", test_health_check),
        ("Job Search Functionality", test_job_search),
        ("Email Functionality", test_email_functionality),
        ("Manual Search Trigger", test_manual_search_trigger),
        ("Job Results Storage", test_job_results_storage),
        ("24-hour Filtering", test_24_hour_filtering)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ FAIL: {test_name} - Unexpected error: {e}")
            results[test_name] = False
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)