import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8081"
USER_LOGIN = "admin"
USER_PASS = "admin123" 

# Liste des thèmes à importer
TOPICS = [
    {"name": "Artificial Intelligence", "query": "cat:cs.AI"},
    {"name": "Astrophysics", "query": "cat:astro-ph"},
    {"name": "Quantum Physics", "query": "cat:quant-ph"},
    {"name": "Biology", "query": "cat:q-bio.QM"},
    {"name": "Finance", "query": "cat:q-fin.ST"}
]

def get_token():
    try:
        r = requests.post(f"{BACKEND_URL}/api/auth/login", json={
            "username": USER_LOGIN,
            "password": USER_PASS
        })
        if r.status_code == 200:
            return r.json().get("token")
    except:
        pass
    return None

def get_or_create_domain(token, domain_name):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BACKEND_URL}/api/domains", headers=headers)
    domains = r.json() if r.status_code == 200 else []
    
    for d in domains:
        if d['name'].lower() == domain_name.lower():
            return d
            
    # Sinon on le crée
    r = requests.post(f"{BACKEND_URL}/api/domains", json={"name": domain_name, "description": f"Articles about {domain_name}"}, headers=headers)
    return r.json() if r.status_code in [200, 201] else None

def fetch_arxiv_papers(query, max_results=5):
    # We use start=50 to get different papers than the ones potentially already in DB
    url = f"http://export.arxiv.org/api/query?search_query={query}&start=50&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    try:
        response = requests.get(url)
        root = ET.fromstring(response.content)
        papers = []
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            abstract = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            pdf_link = entry.find("atom:link[@title='pdf']", ns)
            pdf_url = pdf_link.attrib['href'] if pdf_link is not None else "https://arxiv.org"
            doi_elem = entry.find('atom:id', ns)
            doi = doi_elem.text.split('/')[-1] if doi_elem is not None else str(time.time())
            
            papers.append({
                "title": title,
                "abstractText": abstract,
                "pdfUrl": pdf_url,
                "doi": doi,
                "journal": "arXiv Research",
                "publicationDate": datetime.now().strftime("%Y-%m-%d")
            })
        return papers
    except:
        return []

def populate():
    token = get_token()
    if not token:
        print("Erreur d'authentification.")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    total_added = 0

    for topic in TOPICS:
        domain = get_or_create_domain(token, topic['name'])
        if not domain: continue
        
        print(f"\n--- Domaine : {topic['name']} ---")
        papers = fetch_arxiv_papers(topic['query'])
        
        for paper in papers:
            paper["domain"] = domain
            print(f"Ajout : {paper['title'][:50]}...")
            try:
                res = requests.post(f"{BACKEND_URL}/api/publications", json=paper, headers=headers)
                if res.status_code in [200, 201]:
                    pub_data = res.json()
                    # Si le backend renvoie un DTO imbrique, ajuster ici
                    pub_id = pub_data.get("publication", {}).get("id") if "publication" in pub_data else pub_data.get("id")
                    
                    # Confirmation auto avec metadonnées bidon (l'IA passera par dessus au prochain crawl ou reload)
                    requests.put(f"{BACKEND_URL}/api/publications/{pub_id}/confirm", json={
                        "aiCategories": topic['name'],
                        "aiKeywords": "Imported",
                        "aiConfidence": 1.0
                    }, headers=headers)
                    total_added += 1
                    print("   OK")
                else:
                    print(f"   Skip (erreur {res.status_code})")
                    if res.status_code == 500:
                        print(f"      Response: {res.text[:200]}...")
            except Exception as e:
                print(f"   Erreur: {e}")
            time.sleep(0.5)

    print(f"\nTermine ! {total_added} articles diversifies ont ete ajoutes.")

if __name__ == "__main__":
    populate()
