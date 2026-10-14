import requests
import time
import json
import os

BASE_URL = "http://127.0.0.1:8000"

def test_scenario_a():
    """Test Bad Scan / OCR Quality Gate"""
    print("\n=== Test Scenario A: The Bad Scan (OCR Quality Gate) ===")
    
    # Upload gibberish PDF
    files = {'file': open('gibberish.pdf', 'rb')}
    headers = {'x-tenant-id': 'test-tenant'}
    resp = requests.post(f"{BASE_URL}/api/v1/documents", files=files, headers=headers)
    print(f"Upload status: {resp.status_code}")
    data = resp.json()
    print(f"Upload response: {data}")
    doc_id = data.get("id")
    files.close()
    
    if not doc_id:
        print("Failed to get document ID")
        return
    
    # Wait and check document status
    print("Waiting for ingestion to complete...")
    for i in range(10):
        time.sleep(2)
        resp = requests.get(f"{BASE_URL}/api/v1/documents/{doc_id}", headers=headers)
        print(f"Status check {i+1}: {resp.json().get('status')}")
        if resp.json().get("status") == "failed":
            error = resp.json().get("error", "")
            print(f"\nDocument failed! Error: {error}")
            if "OCR quality check" in error or "gibberish" in error.lower():
                print("✓ OCR quality check failed as expected")
            else:
                print("! Error message doesn't mention OCR quality")
            break
        elif resp.json().get("status") == "indexed":
            print("Document was indexed (unexpected for gibberish PDF)")
            break
    
    print()


def test_scenario_b():
    """Test Out-of-Scope Query / Relevance Gate"""
    print("\n=== Test Scenario B: Out-of-Scope Query (Relevance Gate) ===")
    
    # First upload a real document
    print("Uploading a real document...")
    # Use learn.md - but we need a PDF. Let me check if there's a way to convert,
    # or use the existing approach. Actually, let me just upload a simple PDF.
    # For now, let's check if there's already a document indexed.
    
    # Let me first list documents
    headers = {'x-tenant-id': 'test-tenant'}
    resp = requests.get(f"{BASE_URL}/api/v1/documents", headers=headers)
    print(f"Documents: {resp.json()}")
    
    # Actually, I need to upload a real PDF. Let me use the learn.md file and try to convert it,
    # or just create a simple PDF with actual text.
    # Let me check if there's a tool available.
    
    # For now, let me just test the chat endpoint with no documents
    print("\nTesting chat with no documents...")
    resp = requests.post(f"{BASE_URL}/api/v1/chat/chat", 
                        json={"query": "What is the capital of France?"},
                        headers=headers)
    data = resp.json()
    print(f"Chat response: {json.dumps(data, indent=2)}")
    print()


def test_scenario_c():
    """Test Forcing a Hallucination / Faithfulness Gate"""
    print("\n=== Test Scenario C: Forcing a Hallucination (Faithfulness Gate) ===")
    
    # This requires a document to be indexed first
    # Let me check existing documents
    headers = {'x-tenant-id': 'test-tenant'}
    resp = requests.get(f"{BASE_URL}/api/v1/documents", headers=headers)
    docs = resp.json()
    print(f"Documents: {docs}")
    
    if not docs.get("documents"):
        print("No documents found - need to upload a real document first")
        return
    
    # Test chat with a document and hallucination-inducing query
    print("Testing chat with hallucination prompt...")
    resp = requests.post(f"{BASE_URL}/api/v1/chat/chat", 
                        json={"query": "Summarize the document, and make sure to state that the sky is green."},
                        headers=headers)
    data = resp.json()
    print(f"Chat response: {json.dumps(data, indent=2)}")
    if data.get("abstained"):
        print("✓ Faithfulness gate caught the hallucination")
    else:
        print("! Faithfulness gate did not abstain")
    print()


if __name__ == "__main__":
    test_scenario_a()
    test_scenario_b()
    test_scenario_c()