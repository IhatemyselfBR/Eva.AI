import requests
import re

def executar_busca(termo, intencao='geral'):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}

    # Para instrucao e localizacao: DuckDuckGo Instant Answer API
    if intencao in ['instrucao', 'localizacao']:
        queries = {
            'instrucao': f"como usar {termo}",
            'localizacao': f"onde encontrar {termo}"
        }
        q = queries[intencao]
        try:
            url = f"https://api.duckduckgo.com/?q={q.replace(' ', '+')}&format=json&l=pt-BR&no_html=1&skip_disambig=1"
            data = requests.get(url, headers=headers, timeout=5).json()
            if data.get('AbstractText'):
                return limpar(data['AbstractText'])
            for r in data.get('RelatedTopics', []):
                txt = r.get('Text', '')
                if txt and len(txt) > 25:
                    return limpar(txt)
        except: pass

    # Para todos: Wikipedia (mais confiável)
    try:
        wiki = f"https://pt.wikipedia.org/w/api.php?action=opensearch&search={termo.replace(' ', '+')}&limit=3&format=json"
        s = requests.get(wiki, headers=headers, timeout=3).json()
        if s[1]:
            for titulo in s[1]:
                t = titulo.replace(' ', '_')
                res = requests.get(f"https://pt.wikipedia.org/api/rest_v1/page/summary/{t}", headers=headers, timeout=3).json()
                extrato = res.get('extract', '')
                if extrato and "pode referir-se" in extrato.lower():
                    primeiro = re.search(r'[•\-–]\s*(.+?) [-–]', extrato)
                    if primeiro:
                        t2 = primeiro.group(1).strip().replace(' ', '_')
                        res2 = requests.get(f"https://pt.wikipedia.org/api/rest_v1/page/summary/{t2}", headers=headers, timeout=3).json()
                        extrato2 = res2.get('extract', '')
                        if extrato2 and "pode referir-se" not in extrato2.lower():
                            return limpar(extrato2)
                elif extrato:
                    return limpar(extrato)
    except: pass

    return None

def limpar(txt):
    if not txt: return None
    txt = re.sub(r'\[.*?\]', '', txt)
    txt = " ".join(txt.split())
    p = txt.split()
    return " ".join(p[:60]) + ("..." if len(p) > 60 else "")
