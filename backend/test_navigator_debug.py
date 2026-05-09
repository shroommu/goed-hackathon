#!/usr/bin/env python3
"""Debug script to test navigator endpoint locally"""
import sys
import traceback
from app import create_app
from flask import json

app = create_app()

with app.app_context():
    try:
        from app.routes_navigator import search_resources, get_llm_client, generate_llm_response
        
        # Test basic search
        print("Testing search_resources...")
        context = {}
        message = "I need help with funding"
        candidates = search_resources(context, message)
        print(f"Found {len(candidates)} candidates")
        
        # Test LLM client
        print("\nTesting LLM client...")
        llm_client = get_llm_client()
        if llm_client:
            print("LLM client initialized successfully")
            print(f"API Key configured: {bool(app.config.get('OPENROUTER_API_KEY'))}")
            
            # Try to generate response
            print("\nTesting LLM response generation...")
            response = generate_llm_response(message, context, candidates[:5], llm_client)
            print("Success!")
            print(json.dumps(response, indent=2))
        else:
            print("LLM client is None - API key missing")
            
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)
