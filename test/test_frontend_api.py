import urllib.request
import json

def run_tests():
    print("--- 1. Testing GET /api/health ---")
    res = urllib.request.urlopen("http://localhost:8080/api/health")
    data = json.loads(res.read().decode())
    print("Health Status:", data.get("status"))
    assert data.get("status") == "ready"

    print("--- 2. Testing GET /api/keys ---")
    res = urllib.request.urlopen("http://localhost:8080/api/keys")
    data = json.loads(res.read().decode())
    print("Total providers in keys:", len(data.get("providers", {})))
    assert len(data.get("providers", {})) > 0

    print("--- 3. Testing POST /api/keys/test with provider='groq' (no key passed) ---")
    req = urllib.request.Request(
        "http://localhost:8080/api/keys/test",
        data=json.dumps({"provider": "groq"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode())
    print("Groq Test Result:", data.get("valid"), "-", data.get("message")[:60])
    assert "valid" in data

    print("--- 4. Testing GET /api/metrics ---")
    res = urllib.request.urlopen("http://localhost:8080/api/metrics")
    data = json.loads(res.read().decode())
    print("Metrics total calls:", data.get("summary", {}).get("total_calls"))
    assert "summary" in data

    print("--- 5. Testing Static Delivery /css/main.css ---")
    res = urllib.request.urlopen("http://localhost:8080/css/main.css")
    css = res.read().decode()
    print("css/main.css fetched successfully. Length:", len(css))
    assert "variables.css" in css

    print("--- 6. Testing Static Delivery /js/app.js ---")
    res = urllib.request.urlopen("http://localhost:8080/js/app.js")
    js = res.read().decode()
    print("js/app.js fetched successfully. Length:", len(js))
    assert "initNavbar" in js

    print("--- 7. Testing SPA / Root /index.html ---")
    res = urllib.request.urlopen("http://localhost:8080/")
    html = res.read().decode()
    print("index.html fetched successfully. Length:", len(html))
    assert "css/main.css" in html
    assert "js/app.js" in html

    print("=== ALL 7 FRONTEND & API TESTS PASSED! ===")

if __name__ == "__main__":
    run_tests()
