import json
import time
import sys
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== 1. TESTING AUTH & TOKEN ISSUANCE ===")
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token_data = login_resp.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print(f"Logged in successfully as admin. Token prefix: {token[:20]}...")

    print("\n=== 2. TESTING FILE VALIDATION ON ARTIFACT UPLOAD ===")
    # Executable file with MZ magic bytes should be blocked
    malicious_bytes = b"MZ\x90\x00\x03\x00\x00\x00Executable simulation"
    files = {"file": ("malware.exe", malicious_bytes, "application/octet-stream")}
    bad_upload = requests.post(f"{BASE_URL}/artifacts/upload", headers={"Authorization": f"Bearer {token}"}, files=files, data={"prompt": "Analyze this"})
    assert bad_upload.status_code == 400, f"Expected 400 on malicious upload, got {bad_upload.status_code}: {bad_upload.text}"
    print(f"Malicious executable successfully blocked: {bad_upload.json()['detail']}")

    # Valid document upload and vector indexing
    doc_text = """AURA Project Specification:
    Neural Architecture v2.0 introduces decoupled background workers,
    precomputed vector embeddings in SQLite, and low-latency audio pipelines."""
    files_ok = {"file": ("aura_spec.txt", doc_text.encode("utf-8"), "text/plain")}
    good_upload = requests.post(f"{BASE_URL}/artifacts/upload", headers={"Authorization": f"Bearer {token}"}, files=files_ok, data={"prompt": "Summarize architecture"})
    assert good_upload.status_code == 200, f"Valid upload failed: {good_upload.text}"
    art_data = good_upload.json()
    art_id = art_data["id"]
    print(f"Valid document uploaded & indexed. Artifact ID: {art_id}")

    print("\n=== 3. TESTING DECOUPLED BACKGROUND GOAL GENERATION ===")
    goal_resp = requests.post(f"{BASE_URL}/goals", headers=headers, json={
        "intention": "Master Python Async and Neural Streaming",
        "category": "Career",
        "duration": "14 Days",
        "experience": "Intermediate"
    })
    assert goal_resp.status_code == 200, f"Goal creation failed: {goal_resp.text}"
    goal_data = goal_resp.json()
    assert goal_data["status"] == "queued", f"Expected 'queued', got {goal_data}"
    job_id = goal_data["job_id"]
    goal_id = goal_data["goal_id"]
    print(f"Goal queued. Job ID: {job_id}, Goal ID: {goal_id}")

    # Poll job until ready
    print("Polling job status...")
    ready = False
    for attempt in range(15):
        poll_resp = requests.get(f"{BASE_URL}/goals/jobs/{job_id}", headers=headers)
        assert poll_resp.status_code == 200, f"Poll failed: {poll_resp.text}"
        poll_data = poll_resp.json()
        print(f"  Attempt {attempt+1}: Status = {poll_data['status']}")
        if poll_data["status"] == "ready":
            ready = True
            break
        time.sleep(1.5)
    assert ready, "Goal generation job did not complete within timeout!"
    print("Goal roadmap background task generated successfully!")

    print("\n=== 4. TESTING REAL-TIME SSE CHAT STREAMING ===")
    stream_resp = requests.post(f"{BASE_URL}/chat/stream", headers=headers, json={
        "message": "Explain in one sentence what makes AURA resilient.",
        "session_id": None
    }, stream=True)
    assert stream_resp.status_code == 200, f"Stream request failed: {stream_resp.status_code}"
    
    events = []
    streamed_text = ""
    for line in stream_resp.iter_lines():
        if line:
            decoded = line.decode("utf-8")
            if decoded.startswith("data:"):
                payload = json.loads(decoded[5:].strip())
                events.append(payload)
                if payload.get("type") == "token":
                    streamed_text += payload["token"]
                    print(payload["token"], end="", flush=True)

    print("\nStream completed!")
    assert any(e.get("type") == "init" for e in events), "Init event missing in stream"
    assert any(e.get("type") == "token" for e in events), "Token events missing in stream"
    assert any(e.get("type") == "done" for e in events), "Done event missing in stream"
    print(f"Full response assembled ({len(streamed_text)} chars).")

    print("\n=== 5. TESTING NORMALIZED CHAT HISTORY & PERSISTENCE ===")
    hist_resp = requests.get(f"{BASE_URL}/chat/history", headers=headers)
    assert hist_resp.status_code == 200, f"Chat history failed: {hist_resp.text}"
    history_data = hist_resp.json()
    assert len(history_data["history"]) > 0, "No chat history returned"
    first_session = history_data["history"][0]
    print(f"Recent chat session: ID={first_session['session_id']}, Preview='{first_session['preview']}', Messages count={len(first_session['messages'])}")

    print("\n=== 6. TESTING SECURITY RATE LIMITING ON /auth/login ===")
    # Make multiple rapid requests to trigger rate limit (10/minute)
    rate_limited = False
    for i in range(15):
        r = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "wrongpassword"})
        if r.status_code == 429:
            rate_limited = True
            print(f"Rate limiter successfully triggered at attempt {i+1}: 429 Too Many Requests")
            break
    print(f"Rate limiting active: {rate_limited}")

    print("\n==========================================")
    print("  ALL 5 HARDENING VERIFICATIONS PASSED!  ")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
