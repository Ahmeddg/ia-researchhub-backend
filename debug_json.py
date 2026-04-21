import requests

BACKEND_URL = "http://localhost:8081"
USER_LOGIN = "admin"
USER_PASS = "admin123"

def get_token():
    try:
        r = requests.post(f"{BACKEND_URL}/api/auth/login", json={"username": USER_LOGIN, "password": USER_PASS})
        return r.json().get("token")
    except: return None

def debug_json():
    token = get_token()
    if not token: return print("Auth failed")
    
    headers = {"Authorization": f"Bearer {token}"}
    print("Fetching personalized recommendations...")
    r = requests.get(f"{BACKEND_URL}/api/publications/personalized", headers=headers)
    
    content = r.text
    print(f"Total length: {len(content)} characters")
    
    # On regarde autour de la position 39588
    pos = 39588
    start = max(0, pos - 100)
    end = min(len(content), pos + 100)
    
    print("\n--- CONTENT AROUND ERROR POSITION ---")
    print(content[start:pos])
    print(">>> ERROR HERE <<<")
    print(content[pos:end])
    print("--------------------------------------")
    
    try:
        import json
        json.loads(content)
        print("\nJSON is actually valid according to Python!")
    except Exception as e:
        print(f"\nJSON Error: {e}")

if __name__ == "__main__":
    debug_json()
