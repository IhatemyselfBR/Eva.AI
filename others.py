import re, defs, use, locates, random, os

# Palavras que indicam saudação
SAUDACOES = ['oi', 'olá', 'ola', 'eae', 'eaí', 'oie', 'hey', 'hi', 'hello', 'opa', 'salve', 'fala']
DESPEDIDAS = ['tchau', 'bye', 'até', 'ate', 'adeus', 'falou', 'flw', 'fui']
COMO_VAI = ['tudo bem', 'tudo bom', 'como vai', 'como você tá', 'tô bem', 'to bem', 'tô mal', 'to mal', 'tô ótimo', 'tô cansado']

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
    f = frase.lower().strip()
    f_limpo = re.sub(r'[?!.,]', '', f).strip()

    # Saudações
    for s in SAUDACOES:
        if f_limpo == s or f_limpo.startswith(s + ' '):
            return 'saudacao'

    # Despedidas
    for d in DESPEDIDAS:
        if d in f_limpo:
            return 'despedida'

    # Como vai / estado emocional
    for c in COMO_VAI:
        if c in f_limpo:
            return 'como_vai'

    # Frase muito curta (menos de 3 palavras) sem conteúdo útil
    palavras = f_limpo.split()
    if len(palavras) <= 2 and not any(p in f_limpo for p in ['o que', 'como', 'onde', 'quem']):
        return 'incompreensao'

    return None

def identificar_intencao(frase):
    f = frase.lower()
    if re.search(r'\bonde\b|\bfica\b|\bencontrar\b|\blocalização\b|\blocalizar\b|\bencontro\b|\bachar\b|\bcomprar\b', f):
        return 'localizacao'
    if re.search(r'\bcomo\b|\bpasso a passo\b|\busar\b|\bservir\b|\bpra que serve\b|\bfunção\b|\buso\b|\butilizar\b', f):
        return 'instrucao'
    if re.search(r'\bquem\b|\bcriador\b|\borigem\b|\bhistória\b', f):
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
    print(f"\033[90m[Debug] Intenção: {intencao} | Alvo: {alvo}\033[0m")
    if intencao == 'instrucao':
        return use.buscar(alvo)
    if intencao == 'localizacao':
        return locates.buscar(alvo)
    return defs.buscar(alvo, intencao)
