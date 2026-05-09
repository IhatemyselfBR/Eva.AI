import json, os, time, re, random
import search
import requests
from datetime import datetime

mem_path = 'learning.json'

sementes = [
    "ansiedade", "depressão", "felicidade", "motivação", "autoestima",
    "amizade", "amor", "relacionamento", "família", "conflito",
    "dinheiro", "dívida", "emprego", "desemprego", "salário",
    "aluguel", "alimentação", "saúde", "sono", "estresse",
    "celular", "aplicativo", "redes sociais", "whatsapp", "instagram",
    "segurança digital", "senha", "vírus", "backup", "wifi",
    "estudo", "faculdade", "concurso", "currículo", "entrevista",
    "freelancer", "empreendedorismo", "produtividade", "foco", "rotina",
    "exercício", "dieta", "hidratação", "medicamento", "dor de cabeça",
    "insônia", "imunidade", "vitamina", "consulta médica", "primeiros socorros",
    "organização", "planejamento", "decisão", "criatividade", "comunicação",
    "negociação", "liderança", "trabalho em equipe", "conflito", "solução",
    "martelo", "computador", "brasil", "python", "célula",
    "fotossíntese", "gravitação", "internet", "átomo", "filosofia",
    "matemática", "física", "química", "biologia", "história",
    "geografia", "economia", "política", "arte", "música",
    "cinema", "literatura", "esporte", "medicina", "tecnologia",
    "astronomia", "ecologia", "psicologia", "sociologia", "robô"
]

extras_por_categoria = {
    "emocoes": [
        "raiva", "medo", "tristeza", "alegria", "ciúme", "solidão",
        "gratidão", "empatia", "resiliência", "inteligência emocional"
    ],
    "carreira": [
        "networking", "portfólio", "promoção", "demissão", "home office",
        "reunião", "prazo", "metas", "feedback", "burnout"
    ],
    "saude": [
        "pressão alta", "diabetes", "colesterol", "obesidade", "gripe",
        "febre", "dor nas costas", "postura", "alongamento", "meditação"
    ],
    "financas": [
        "investimento", "poupança", "cartão de crédito", "juros", "inflação",
        "orçamento", "gastos", "renda extra", "aposentadoria", "imposto"
    ],
    "tecnologia": [
        "inteligência artificial", "machine learning", "blockchain", "nuvem",
        "programação", "banco de dados", "api", "cibersegurança", "automação", "linux"
    ],
    "relacionamentos": [
        "comunicação não violenta", "limites saudáveis", "trauma", "terapia",
        "abuso", "dependência emocional", "autoconhecimento", "perdão", "confiança", "respeito"
    ]
}

def carregar():
    if os.path.exists(mem_path):
        with open(mem_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
            except:
                return {}
    return {}

def salvar(memoria):
    with open(mem_path, 'w', encoding='utf-8') as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)

def extrair_termos_relacionados(termo):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    termos = []
    try:
        url = f"https://pt.wikipedia.org/w/api.php?action=query&titles={termo.replace(' ', '_')}&prop=links&pllimit=20&format=json"
        data = requests.get(url, headers=headers, timeout=5).json()
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            for link in page.get('links', []):
                t = link.get('title', '')
                if ':' in t: continue
                if len(t) < 3 or len(t) > 40: continue
                if t.replace(' ', '').isdigit(): continue
                if re.match(r'^\d', t): continue
                if re.match(r'^[0-9\-\/]+$', t): continue
                if len(t.split()) > 4: continue
                termos.append(t.lower())
    except:
        pass
    return termos

def log(msg):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {msg}")

def treinar_infinito():
    memoria = carregar()

    fila = list(sementes)
    for categoria, termos in extras_por_categoria.items():
        fila.extend(termos)
    random.shuffle(fila)

    vistos = set(memoria.keys())
    aprendidos = 0
    erros_seguidos = 0
    requisicoes = 0

    log(f"🧠 Auto-treino iniciado — {len(memoria)} termos já na memória")
    log(f"📋 {len(fila)} termos na fila inicial")
    log("Ctrl+C para parar com segurança\n")

    while True:
        if not fila:
            log("🔄 Fila vazia, reiniciando...")
            fila = list(sementes)
            for categoria, termos in extras_por_categoria.items():
                fila.extend(termos)
            random.shuffle(fila)
            vistos.clear()

        termo = fila.pop(0)

        if termo in vistos:
            continue
        vistos.add(termo)

        if termo in memoria and memoria[termo].get('peso', 0) > 0:
            relacionados = extrair_termos_relacionados(termo)
            novos = [t for t in relacionados if t not in vistos][:5]
            fila.extend(novos)
            log(f"⏭  '{termo}' — já sei | fila: {len(fila)}")
            time.sleep(1)
            continue

        log(f"🔍 Buscando '{termo}'...")
        res = search.executar_busca(termo, 'definicao')
        requisicoes += 1

        if res:
            memoria[termo] = {"texto": res, "peso": 1}
            salvar(memoria)
            aprendidos += 1
            erros_seguidos = 0
            log(f"✅ '{termo}' aprendido! (total: {aprendidos})")
            relacionados = extrair_termos_relacionados(termo)
            novos = [t for t in relacionados if t not in vistos][:5]
            fila.extend(novos)
            log(f"   📎 +{len(novos)} termos na fila ({len(fila)} total)")
        else:
            erros_seguidos += 1
            log(f"❌ '{termo}' — não encontrei ({erros_seguidos} erros seguidos)")
            if erros_seguidos >= 5:
                log("⚠️  Muitos erros — pausando 10s...")
                time.sleep(10)
                erros_seguidos = 0

        if requisicoes % 50 == 0:
            log(f"☕ {requisicoes} requisições — pausa de 5s...")
            time.sleep(5)
        else:
            time.sleep(random.uniform(1, 2))

if __name__ == "__main__":
    try:
        treinar_infinito()
    except KeyboardInterrupt:
        print("\n\n⏹  Treino pausado com segurança. Conhecimento salvo!")
