import json, os, time, re, random
import search
import requests
from datetime import datetime

mem_path = 'learning.json'

# ==========================
# SEMENTES POR CATEGORIA
# ==========================

sementes = {
    "cotidiano": [
        "ansiedade", "depressão", "felicidade", "motivação", "autoestima",
        "amizade", "amor", "relacionamento", "família", "conflito",
        "dinheiro", "dívida", "emprego", "salário", "aluguel",
        "sono", "estresse", "alimentação", "saúde", "rotina"
    ],
    "tecnologia": [
        "celular", "aplicativo", "internet", "programação", "inteligência artificial",
        "machine learning", "banco de dados", "cibersegurança", "automação", "linux",
        "python", "javascript", "api", "nuvem", "blockchain"
    ],
    "ciencia": [
        "fotossíntese", "gravitação", "átomo", "célula", "dna",
        "evolução", "física quântica", "relatividade", "neurociência", "genética",
        "astronomia", "ecologia", "química orgânica", "biologia molecular", "astrofísica"
    ],
    "cultura": [
        "filosofia", "história", "geografia", "economia", "política",
        "arte", "música", "cinema", "literatura", "esporte",
        "psicologia", "sociologia", "antropologia", "linguística", "arqueologia"
    ],
    "saude": [
        "exercício", "dieta", "hidratação", "meditação", "yoga",
        "pressão alta", "diabetes", "colesterol", "obesidade", "insônia",
        "imunidade", "vitamina", "postura", "alongamento", "primeiros socorros"
    ],
    "carreira": [
        "empreendedorismo", "produtividade", "foco", "liderança", "networking",
        "currículo", "entrevista", "freelancer", "burnout", "feedback",
        "negociação", "comunicação", "trabalho em equipe", "gestão", "planejamento"
    ],
    "financas": [
        "investimento", "poupança", "juros", "inflação", "orçamento",
        "cartão de crédito", "renda extra", "aposentadoria", "imposto", "bolsa de valores",
        "criptomoeda", "tesouro direto", "fundo de investimento", "seguro", "previdência"
    ]
}

# ==========================
# FILTROS ANTI-LIXO
# ==========================

STOPWORDS = {
    'de', 'da', 'do', 'em', 'no', 'na', 'os', 'as', 'um', 'uma',
    'para', 'com', 'por', 'que', 'se', 'ao', 'dos', 'das', 'nos', 'nas',
    'pelo', 'pela', 'este', 'esta', 'esse', 'essa', 'seu', 'sua'
}

def filtro_termo(t):
    if ':' in t: return False
    if len(t) < 3 or len(t) > 40: return False
    if t.replace(' ', '').isdigit(): return False
    if re.match(r'^\d', t): return False
    if re.match(r'^[0-9\-\/]+$', t): return False
    if len(t.split()) > 4: return False
    if t.lower() in STOPWORDS: return False
    # Filtra siglas e abreviações puras
    if re.match(r'^[a-z]{1,2}$', t.lower()): return False
    return True

# ==========================
# I/O
# ==========================

def carregar():
    if os.path.exists(mem_path):
        with open(mem_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
            except: return {}
    return {}

def salvar(memoria):
    with open(mem_path, 'w', encoding='utf-8') as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)

def log(msg):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {msg}")

# ==========================
# WIKIPEDIA
# ==========================

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

def extrair_relacionados(termo):
    termos = []
    try:
        url = f"https://pt.wikipedia.org/w/api.php?action=query&titles={termo.replace(' ', '_')}&prop=links&pllimit=30&format=json"
        data = requests.get(url, headers=headers, timeout=5).json()
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            for link in page.get('links', []):
                t = link.get('title', '').lower()
                if filtro_termo(t):
                    termos.append(t)
    except: pass
    return termos

def extrair_sinonimos(termo):
    """Busca redirecionamentos da Wikipedia — são sinônimos e variações do termo"""
    sinonimos = []
    try:
        url = f"https://pt.wikipedia.org/w/api.php?action=query&titles={termo.replace(' ', '_')}&prop=redirects&rdlimit=10&format=json"
        data = requests.get(url, headers=headers, timeout=5).json()
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            for r in page.get('redirects', []):
                t = r.get('title', '').lower()
                if filtro_termo(t):
                    sinonimos.append(t)
    except: pass
    return sinonimos

def extrair_categorias(termo):
    """Busca categorias da Wikipedia — geram termos relacionados por área"""
    cats = []
    try:
        url = f"https://pt.wikipedia.org/w/api.php?action=query&titles={termo.replace(' ', '_')}&prop=categories&cllimit=10&format=json"
        data = requests.get(url, headers=headers, timeout=5).json()
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            for cat in page.get('categories', []):
                titulo = cat.get('title', '').replace('Categoria:', '').lower()
                # Extrai palavras úteis da categoria
                palavras = [p for p in titulo.split() if filtro_termo(p)]
                cats.extend(palavras[:3])
    except: pass
    return cats

def gerar_tags_simples(texto):
    texto = re.sub(r'[^\w\s]', '', texto.lower())
    return [p for p in texto.split() if len(p) > 3 and p not in STOPWORDS]

# ==========================
# LOOP PRINCIPAL
# ==========================

def treinar():
    memoria = carregar()

    # Monta fila inicial com todas as sementes embaralhadas
    fila = []
    for categoria, termos in sementes.items():
        fila.extend(termos)
    random.shuffle(fila)

    vistos = set(memoria.keys())
    aprendidos = 0
    erros_seguidos = 0
    requisicoes = 0
    rodada = 1

    log(f"🧠 Auto-treino v2 iniciado — {len(memoria)} termos já na memória")
    log(f"📋 {len(fila)} termos na fila inicial")
    log("Ctrl+C para parar com segurança\n")

    while True:
        # Fila vazia — nova rodada com sementes + variações
        if not fila:
            rodada += 1
            log(f"🔄 Rodada {rodada} — reiniciando com sementes...")
            fila = []
            for categoria, termos in sementes.items():
                fila.extend(termos)
            # Adiciona sinônimos dos termos já aprendidos pra diversificar
            amostra = random.sample(list(memoria.keys()), min(20, len(memoria)))
            for termo in amostra:
                sins = extrair_sinonimos(termo)
                fila.extend(sins[:3])
            random.shuffle(fila)
            vistos.clear()

        termo = fila.pop(0)

        if termo in vistos:
            continue
        vistos.add(termo)

        # Já sabe — aproveita pra descobrir relacionados e sinônimos
        if termo in memoria and memoria[termo].get('peso', 0) > 0:
            relacionados = extrair_relacionados(termo)
            sinonimos = extrair_sinonimos(termo)
            novos = [t for t in relacionados + sinonimos if t not in vistos][:6]
            fila.extend(novos)
            log(f"⏭  '{termo}' — já sei | +{len(novos)} na fila ({len(fila)} total)")
            time.sleep(0.8)
            continue

        # Busca o termo
        log(f"🔍 [{aprendidos}] Buscando '{termo}'...")
        res = search.executar_busca(termo, 'definicao')
        requisicoes += 1

        if res:
            # Gera tags
            tags = gerar_tags_simples(f"{termo} {res}")

            memoria[termo] = {
                "texto": res,
                "peso": 1,
                "tags": tags
            }
            salvar(memoria)
            aprendidos += 1
            erros_seguidos = 0
            log(f"✅ '{termo}' aprendido! (total: {aprendidos} | tags: {len(tags)})")

            # Descobre relacionados, sinônimos e categorias
            relacionados = extrair_relacionados(termo)
            sinonimos = extrair_sinonimos(termo)
            cats = extrair_categorias(termo)
            novos = [t for t in relacionados + sinonimos + cats if t not in vistos][:8]
            fila.extend(novos)
            log(f"   📎 +{len(novos)} termos na fila ({len(fila)} total)")

        else:
            erros_seguidos += 1
            log(f"❌ '{termo}' — não encontrei ({erros_seguidos} seguidos)")

            if erros_seguidos >= 5:
                log("⚠️  Muitos erros — pausando 10s...")
                time.sleep(10)
                erros_seguidos = 0

        # Pausa a cada 50 requisições
        if requisicoes % 50 == 0:
            log(f"☕ {requisicoes} requisições — pausa de 5s...")
            time.sleep(5)
        else:
            time.sleep(random.uniform(1.5, 2.5))

if __name__ == "__main__":
    try:
        treinar()
    except KeyboardInterrupt:
        print("\n\n⏹  Treino pausado com segurança. Conhecimento salvo!")
