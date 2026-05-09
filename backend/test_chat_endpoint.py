#!/usr/bin/env python3
"""
Simple test script for the BE-014 chat endpoint.
Tests both with and without LLM (deterministic fallback).
"""

import json
import requests

BASE_URL = "http://localhost:5000/api"


def test_chat_basic():
    """Test basic chat without context."""
    print("\n=== Test 1: Basic chat without context ===")
    response = requests.post(
        f"{BASE_URL}/navigator/chat/message",
        json={"message": "I'm looking for funding for my AI startup"},
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_chat_with_context():
    """Test chat with existing context."""
    print("\n=== Test 2: Chat with context ===")
    response = requests.post(
        f"{BASE_URL}/navigator/chat/message",
        json={
            "message": "We're in San Francisco and just raised pre-seed",
            "context": {"industry": "AI", "objectives": ["funding"]},
        },
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_invalid_request():
    """Test error handling for invalid request."""
    print("\n=== Test 3: Invalid request (missing message) ===")
    response = requests.post(f"{BASE_URL}/navigator/chat/message", json={})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 400


def test_health():
    """Test health endpoint to verify API is running."""
    print("\n=== Test 0: Health check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


if __name__ == "__main__":
    print("Testing BE-014 Chat Endpoint")
    print("=" * 60)

    try:
        # Test health first
        if not test_health():
            print("\n❌ Health check failed. Is the API running?")
            exit(1)

        # Run tests
        tests = [
            ("Basic chat", test_chat_basic),
            ("Chat with context", test_chat_with_context),
            ("Invalid request", test_invalid_request),
        ]

        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                print(f"❌ Test '{name}' failed with exception: {e}")
                results.append((name, False))

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary:")
        for name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {status}: {name}")

        passed_count = sum(1 for _, p in results if p)
        total_count = len(results)
        print(f"\nTotal: {passed_count}/{total_count} tests passed")

    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API. Make sure the Flask app is running:")
        print("   cd backend && source .venv/bin/activate && flask run")
