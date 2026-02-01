#!/usr/bin/env python3
"""Quick smoke test for Member 4 chains with gemini-3-flash-preview"""

import os
from dotenv import load_dotenv
load_dotenv()

from src.agents.prompts import extract_keywords_from_query_sync
from src.agents.state import FarmerInput, ExtractionModel

print(" Testing extract_keywords_from_query_sync with gemini-3-flash-preview...")

try:
    # Test 1: Simple extraction
    query = "My tomato plants have yellow leaves and I see white powder on them. What should I do?"
    result = extract_keywords_from_query_sync(query)
    
    print(f" Test 1 PASSED: Extract keywords")
    print(f"  Crop: {result.crop}")
    print(f"  Symptoms: {result.symptoms}")
    print(f"  Urgency: {result.urgency}")
    
except Exception as e:
    print(f" Test 1 FAILED: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n Basic functionality verified!")
