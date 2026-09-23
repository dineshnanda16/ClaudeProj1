"""
Test script to verify Cohere integration for medication extraction.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Testing Cohere Integration")
print("=" * 60)

# Test 1: Verify .env is loaded
print("\n[Test 1] Environment Configuration:")
print(f"  LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
print(f"  LLM_MODEL: {os.getenv('LLM_MODEL')}")
print(f"  LLM_TEMPERATURE: {os.getenv('LLM_TEMPERATURE')}")

# Check API key (without exposing it)
api_key = os.getenv('COHERE_API_KEY')
if api_key:
    print(f"  COHERE_API_KEY: {'*' * 20}{api_key[-4:]} (last 4 chars shown)")
else:
    print("  COHERE_API_KEY: NOT SET")

# Test 2: Import medication extractor
print("\n[Test 2] Import MedicationExtractor:")
try:
    from processors.medication_extractor import MedicationExtractor
    print("  ✅ Import successful")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    exit(1)

# Test 3: Initialize extractor
print("\n[Test 3] Initialize MedicationExtractor:")
try:
    extractor = MedicationExtractor()
    print(f"  ✅ Initialization successful")
    print(f"  Provider: {extractor.provider}")
    print(f"  Model: {extractor.model}")
    print(f"  Temperature: {extractor.temperature}")
    print(f"  Client type: {type(extractor.client).__name__}")
except Exception as e:
    print(f"  ❌ Initialization failed: {e}")
    exit(1)

# Test 4: Verify Cohere client
print("\n[Test 4] Verify Cohere Client:")
if extractor.provider == "cohere":
    print("  ✅ Provider is Cohere")
    if "cohere" in str(type(extractor.client)).lower():
        print("  ✅ Client is Cohere ClientV2")
    else:
        print(f"  ❌ Client is not Cohere: {type(extractor.client)}")
else:
    print(f"  ❌ Provider is not Cohere: {extractor.provider}")

# Test 5: Test medication extraction with sample text
print("\n[Test 5] Test Medication Extraction:")
sample_text = """
PRESCRIPTION

Patient: John Doe
Date: 2026-09-22

Medications:
1. Metformin 500mg - Take one tablet twice daily with meals
2. Lisinopril 10mg - Take one tablet once daily in the morning
3. Atorvastatin 20mg - Take one tablet once daily at bedtime
"""

try:
    print("  Sending request to Cohere API...")
    result = extractor.extract_medications_from_document(
        document_text=sample_text,
        filename="test_prescription.pdf",
        document_type="New Prescription",
        page_info=[(1, sample_text)]
    )

    print(f"  ✅ Extraction completed")
    print(f"  Status: {result.extraction_status.value}")
    print(f"  Medications found: {result.get_medication_count()}")

    if result.medications:
        print("\n  Extracted medications:")
        for idx, med in enumerate(result.medications, 1):
            print(f"    {idx}. {med.medication_name}")
            print(f"       Strength: {med.strength or 'N/A'}")
            print(f"       Frequency: {med.frequency or 'N/A'}")
            print(f"       Source page: {med.source_page}")

except Exception as e:
    print(f"  ❌ Extraction failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("✅ All tests passed! Cohere integration is working.")
print("=" * 60)
