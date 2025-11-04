"""
Test script to verify all CRUD operations work correctly
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5500"

def test_health():
    """Test health endpoint"""
    print("1. Testing Health Check...")
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_get_services():
    """Test GET services"""
    print("\n2. Testing GET /api/services...")
    response = requests.get(f"{BASE_URL}/api/services")
    print(f"   Status: {response.status_code}")
    services = response.json()
    print(f"   Found {len(services)} services")
    for s in services:
        print(f"   - {s['name']} ({s['code']}) - {s['price']}")
    return response.status_code == 200

def test_create_booking():
    """Test CREATE booking"""
    print("\n3. Testing POST /api/bookings...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    booking_data = {
        "service": "consultation",
        "date": tomorrow,
        "time": "10:00 AM",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": "1234567890",
        "notes": "Test booking"
    }
    response = requests.post(
        f"{BASE_URL}/api/bookings",
        json=booking_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    if response.status_code == 201:
        booking_id = response.json().get("booking_id")
        return booking_id
    return None

def test_get_booking(booking_id):
    """Test GET single booking"""
    print(f"\n4. Testing GET /api/bookings/{booking_id}...")
    response = requests.get(f"{BASE_URL}/api/bookings/{booking_id}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        booking = response.json()
        print(f"   Booking: {booking['first_name']} {booking['last_name']} - {booking['booking_date']} at {booking['booking_time']}")
    return response.status_code == 200

def test_get_all_bookings():
    """Test GET all bookings"""
    print("\n5. Testing GET /api/bookings...")
    response = requests.get(f"{BASE_URL}/api/bookings")
    print(f"   Status: {response.status_code}")
    bookings = response.json()
    print(f"   Found {len(bookings)} bookings")
    return response.status_code == 200

def test_update_booking(booking_id):
    """Test UPDATE booking"""
    print(f"\n6. Testing PUT /api/bookings/{booking_id}...")
    update_data = {
        "first_name": "Updated",
        "time": "2:00 PM"
    }
    response = requests.put(
        f"{BASE_URL}/api/bookings/{booking_id}",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_delete_booking(booking_id):
    """Test DELETE booking"""
    print(f"\n7. Testing DELETE /api/bookings/{booking_id}...")
    response = requests.delete(f"{BASE_URL}/api/bookings/{booking_id}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_get_slots():
    """Test GET time slots"""
    print("\n8. Testing GET /api/slots...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    response = requests.get(f"{BASE_URL}/api/slots?date={tomorrow}")
    print(f"   Status: {response.status_code}")
    slots = response.json()
    available = sum(1 for s in slots if s['available'])
    print(f"   Found {len(slots)} slots, {available} available")
    return response.status_code == 200

if __name__ == "__main__":
    print("=" * 60)
    print("RESERVABOOK CRUD OPERATIONS TEST")
    print("=" * 60)
    print("\nMake sure the backend server is running on http://127.0.0.1:5500")
    print("\nStarting tests...\n")
    
    try:
        # Run all tests
        test_health()
        test_get_services()
        booking_id = test_create_booking()
        if booking_id:
            test_get_booking(booking_id)
            test_get_all_bookings()
            test_update_booking(booking_id)
            test_get_slots()
            test_delete_booking(booking_id)
        
        print("\n" + "=" * 60)
        print("✅ ALL CRUD OPERATIONS TESTED SUCCESSFULLY!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server.")
        print("   Make sure the backend is running on http://127.0.0.1:5500")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

