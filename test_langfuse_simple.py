#!/usr/bin/env python3
"""
Simple test to verify Langfuse integration is working.
"""

import asyncio
import json
import httpx
from pathlib import Path

# Minimal test data
TEST_DATA = {
    "encounterId": "langfuse_simple_test",
    "encounterTranscript": [
        {"doctor": "How are you feeling?"},
        {"patient": "I have chest pain."},
        {"doctor": "When did it start?"},
        {"patient": "Yesterday evening."}
    ],
    "sections": [
        {
            "id": 1,
            "templateId": 1,
            "name": "Subjective",
            "prompt": "Extract patient symptoms.",
            "order": 1
        }
    ],
    "doctorId": "test_doctor",
    "doctor_preferences": {},
    "language": "en",
    "clinicId": "test_clinic"
}

async def test_simple():
    print("🧪 Simple Langfuse Test")
    print("=" * 40)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            print("📤 Sending request...")
            response = await client.post(
                "http://localhost:8000/generate-notes",
                json=TEST_DATA,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Job ID: {result['job_id']}")
                print(f"📋 Message: {result['message']}")
                
                # Wait for processing
                print("\n⏳ Waiting 30 seconds...")
                await asyncio.sleep(30)
                
                # Check status
                status_response = await client.get(
                    f"http://localhost:8000/extract/jobs/{result['job_id']}/status"
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"\n📊 Status: {status_data.get('status')}")
                    print(f"🆔 Trace ID: {status_data.get('trace_id', 'Not found')}")
                    print(f"🔗 Langfuse URL: {status_data.get('langfuse_trace_url', 'Not found')}")
                    print(f"🔧 Langfuse Enabled: {status_data.get('langfuse_enabled', False)}")
                
            else:
                print(f"❌ Failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Cleanup
    test_dir = Path(f"generated_notes/{TEST_DATA['encounterId']}")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
        print("\n🧹 Cleaned up test files")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_simple()) 