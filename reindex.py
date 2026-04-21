import requests
import time

BACKEND_URL = "http://localhost:8081"
USER_LOGIN = "admin"
USER_PASS = "admin123"

def get_token():
    try:
        r = requests.post(f"{BACKEND_URL}/api/auth/login", json={"username": USER_LOGIN, "password": USER_PASS})
        return r.json().get("token")
    except: return None

def reindex():
    token = get_token()
    if not token: return print("Auth failed")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Recuperer toutes les publications
    print("Recuperation des publications...")
    r = requests.get(f"{BACKEND_URL}/api/publications", headers=headers)
    if r.status_code != 200: return print(f"Failed to fetch: {r.status_code}")
    
    pubs = r.json()
    print(f"Trouve {len(pubs)} articles. Debut de la re-indexation...")
    
    # 2. Les envoyer un par un au service de classification (Python)
    for p in pubs:
        print(f"Traitement de : {p['title'][:50]} (ID: {p['id']})")
        
        try:
            # A. Appeler le service Python directement
            ai_data = {
                "publication_id": p['id'],
                "title": p['title'],
                "abstract_text": p.get('abstractText', ''),
                "domain": p.get('domain', {}).get('name', 'General'),
                "pdf_url": p.get('pdfUrl', '')
            }
            res = requests.post("http://localhost:8000/classify", json=ai_data)
            
            if res.status_code == 200:
                result = res.json()
                print(f"   AI OK (Cluster: {result.get('cluster_label')})")
                
                # B. Pousser les donnees vers Java pour peupler ai_categories, ai_keywords, etc.
                confirm_payload = {
                    "aiCategories": ", ".join([c["category"] for c in result.get("categories", [])]),
                    "aiKeywords": ", ".join(result.get("keywords", [])),
                    "aiConfidence": result.get("confidence", 1.0)
                }
                
                conf_res = requests.put(f"{BACKEND_URL}/api/publications/{p['id']}/confirm", 
                                        json=confirm_payload, headers=headers)
                
                if conf_res.status_code in [200, 204]:
                    print("   Sync Java OK")
                else:
                    print(f"   Sync Java FAIL ({conf_res.status_code})")
            else:
                print(f"   AI FAIL {res.status_code}")
        except Exception as e:
            print(f"   Erreur: {e}")
        time.sleep(0.2)

    print("\nFini ! Tous les articles sont maintenant indexes et enrichis par l'IA.")

if __name__ == "__main__":
    reindex()
