import requests
from bs4 import BeautifulSoup
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}

termo = "navalha"
q = f"o que é {termo}"

print("--- Teste Wikipedia ---")
try:
    wiki = f"https://pt.wikipedia.org/w/api.php?action=opensearch&search={q.replace(' ', '+')}&limit=3&format=json"
    s = requests.get(wiki, headers=headers, timeout=3).json()
    print(f"Títulos encontrados: {s[1]}")
    
    for titulo in s[1]:
        t = titulo.replace(' ', '_')
        res = requests.get(f"https://pt.wikipedia.org/api/rest_v1/page/summary/{t}", headers=headers, timeout=3).json()
        extrato = res.get('extract', '')
        print(f"\nTítulo: {titulo}")
        print(f"Extrato: {extrato[:300]}")
        print(f"Tem 'pode referir-se': {'pode referir-se' in extrato.lower()}")
except Exception as e:
    print(f"Erro: {e}")
