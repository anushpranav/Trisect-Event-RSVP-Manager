#!/usr/bin/env python3
"""
Simple test script to verify the RSVP Manager application works correctly.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        from app import create_app
        from models import db, Organizer, Event, Guest
        from config import Config
        from qr_generator import generate_rsvp_qr
        from analytics import get_event_analytics, get_organizer_analytics
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    try:
        from config import Config
        config = Config()
        print("✅ Configuration loaded successfully")
        print(f"   Database URI: {config.SQLALCHEMY_DATABASE_URI[:20]}...")
        print(f"   Mail Server: {config.MAIL_SERVER}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_app_creation():
    """Test Flask app creation."""
    print("\nTesting Flask app creation...")
    try:
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

def test_models():
    """Test database models."""
    print("\nTesting database models...")
    try:
        from models import Organizer, Event, Guest
        
        # Test Organizer model
        organizer = Organizer(
            name="Test Organizer",
            email="test@example.com",
            passwordHash="test_hash"
        )
        print("✅ Organizer model works")
        
        # Test Event model
        event = Event(
            title="Test Event",
            description="Test Description",
            date=datetime.now() + timedelta(days=7),
            location="Test Location",
            organizerId=1
        )
        print("✅ Event model works")
        
        # Test Guest model
        guest = Guest(
            eventId=1,
            name="Test Guest",
            email="guest@example.com",
            uniqueAccessToken="test_token"
        )
        print("✅ Guest model works")
        
        return True
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

def test_qr_generation():
    """Test QR code generation."""
    print("\nTesting QR code generation...")
    try:
        from qr_generator import generate_rsvp_qr
        qr_code = generate_rsvp_qr("test_token")
        if qr_code:
            print("✅ QR code generation works")
            return True
        else:
            print("❌ QR code generation failed")
            return False
    except Exception as e:
        print(f"❌ QR generation error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 RSVP Manager - Application Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_app_creation,
        test_models,
        test_qr_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application should work correctly.")
        print("\nTo run the application:")
        print("1. Set up your .env file with database and email credentials")
        print("2. Run: python app.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 