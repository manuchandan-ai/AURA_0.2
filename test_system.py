import requests

API = "http://127.0.0.1:8000"

print("1. Testing Root Endpoint...")
r1 = requests.get(f"{API}/")
assert r1.status_code == 200, "Root offline"
print("   Status: ONLINE")

print("2. Testing General Chat & LLM Router...")
r2 = requests.post(f"{API}/chat", json={"message": "Ping AURA verification test"}).json()
assert "response" in r2, "Chat response failed"
print("   Engine:", r2["response"].splitlines()[-1])

print("3. Testing Morning Briefing Engine...")
r3 = requests.get(f"{API}/briefing").json()
assert "headline" in r3, "Briefing failed"
print("   Directive:", r3.get("focus_directive"))

print("4. Testing Memory Retrieval...")
r4 = requests.get(f"{API}/memories").json()
assert "memories" in r4, "Memory fetch failed"
print("   Total Memories Retained:", len(r4["memories"]))

print("\nALL SYSTEM CHECKS PASSED SUCCESSFULLY!")
