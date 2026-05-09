import re, defs, use, locates, random, os

SAUDACOES = [
    'oi', 'olá', 'ola', 'eae', 'eaí', 'oie', 'hey', 'hi', 'hello',
    'opa', 'salve', 'fala', 'oii', 'oiii', 'bom dia', 'boa tarde',
    'boa noite', 'fala aí', 'e aí', 'e ai', 'fala mano', 'fala cara'
]

DESPEDIDAS = [
    'tchau', 'bye', 'adeus', 'falou', 'flw', 'fui embora',
    'vou nessa', 'até mais', 'ate mais', 'até logo', 'ate logo',
    'até depois', 'ate depois', 'até a próxima', 'vazei', 'partiu'
]

COMO_VAI = [
    'tudo bem', 'tudo bom', 'como vai', 'como você tá', 'como voce ta',
    'tô bem', 'to bem', 'tô mal', 'to mal', 'tô ótimo', 'to otimo',
    'tô cansado', 'to cansado', 'tô triste', 'to triste', 'tô feliz',
    'to feliz', 'tô de boa', 'to de boa', 'tô na luta', 'tô quebrado',
    'tô estressado', 'tô pensativo', 'tô suave', 'tô ok', 'to ok',
    'tô mais ou menos', 'tô normal', 'tô vivo', 'tô na correria'
]

GIRIAS = [
    'suave', 'suavão', 'vix', 'vixi', 'kkk', 'kkkk', 'kkkkk', 'kkkkkk',
    'rsrs', 'haha', 'massa', 'top', 'show', 'pow', 'slc', 'oxe', 'eita',
    'caramba', 'bora', 'bah', 'puts', 'poxa', 'nossa', 'uai', 'beleza',
    'firmeza', 'de boa', 'tmj', 'que isso', 'misericórdia', 'pelo amor'
]

def obter_frase(words_path, tag):
    frases = []
    if os.path.exists(words_path):
        with open(words_path, 'r', encoding='utf-8') as f:
            cap = False
            for l in f:
                l = l.strip()
                if l == f"[{tag}]": cap = True; continue
                if l.startswith("[") and cap: break
                if cap and l: frases.append(l)
    return random.choice(frases) if frases else None

def detectar_social(frase):
    f = re.sub(r'[?!.,]', '', frase.lower()).strip()

    # Saudações — só no início da frase
    for s in SAUDACOES:
        if f == s or f.startswith(s + ' '):
            return 'saudacao'

    # Despedidas — frase inteira deve ser despedida
    for d in DESPEDIDAS:
        if f == d or f.startswith(d):
            return 'despedida'

    # Como vai
    for c in COMO_VAI:
        if f == c or c in f:
            return 'como_vai'

    # Gírias — frase inteira é a gíria
    for g in GIRIAS:
        if f == g or f.startswith(g):
            return 'giria'

    # CORREÇÃO: só vira incompreensão se tiver menos de 3 caracteres
    # Palavras normais de 1 termo como "cachorro", "gato" vão pra busca
    if len(f) < 3:
        return 'incompreensao'

    return None

def identificar_intencao(frase):
    f = frase.lower()
    if re.search(r'\bonde\b|\bfica\b|\bencontrar\b|\blocalização\b|\blocalizar\b|\bencontro\b|\bachar\b|\bcomprar\b', f):
        return 'localizacao'
    if re.search(r'\bcomo\b|\bpasso a passo\b|\busar\b|\bservir\b|\bpra que serve\b|\bfunção\b|\buso\b|\butilizar\b', f):
        return 'instrucao'
    if re.search(r'\bquem\b|\bcriador\b|\borigem\b|\bhistória\b|\bquem é\b|\bquem foi\b', f):
        return 'origem'
    return 'definicao'

def extrair_alvo(frase):
    alvo = re.sub(r'[?!.,]', '', frase.lower()).strip()
    termos_sujeira = [
        r'^o que (são|sao|é|e)\s+(o|a|os|as)\s+',
        r'^o que (são|sao|é|e)\s+',
        r'^como (usar|funciona|fazer|serve|uso|utilizar)\s+(o|a|os|as|um|uma)\s+',
        r'^como (usar|funciona|fazer|serve|uso|utilizar)\s+',
        r'^como (uso|utilizo|faço)\s+(o|a|os|as|um|uma)\s+',
        r'^como (uso|utilizo|faço)\s+',
        r'^pra que serve (o|a|os|as|um|uma)\s+',
        r'^pra que serve\s+',
        r'^onde (encontrar|encontro|fica|localizar|achar|comprar)\s+(o|a|os|as|um|uma)\s+',
        r'^onde (encontrar|encontro|fica|localizar|achar|comprar)\s+',
        r'^quem (é|foi|são)\s+(o|a|os|as)?\s*',
        r'^quem (é|foi|são)\s+',
        r'^(o|a|os|as|um|uma)\s+'
    ]
    for pat in termos_sujeira:
        alvo = re.sub(pat, '', alvo).strip()
    return alvo if alvo else frase.strip()

def roteador(frase):
    intencao = identificar_intencao(frase)
    alvo = extrair_alvo(frase)
    if not alvo or len(alvo) < 2:
        alvo = frase
    if intencao == 'instrucao':
        return use.buscar(alvo)
    if intencao == 'localizacao':
        return locates.buscar(alvo)
    return defs.buscar(alvo, intencao)
