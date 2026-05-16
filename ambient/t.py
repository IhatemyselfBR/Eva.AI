import json
import random
import re
import math
from collections import Counter

ARQUIVO = "learn.json"

# =========================================
# CARREGAR MEMÓRIA
# =========================================

try:
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        memoria = json.load(f)
except:
    memoria = []

# =========================================
# STOPWORDS
# =========================================

STOPWORDS = {
    "a", "o", "e", "de", "da", "do",
    "que", "pra", "para", "um", "uma",
    "em", "na", "no", "com", "eu",
    "tu", "você", "vc"
}

# =========================================
# SINÔNIMOS
# =========================================

SINONIMOS = {

    "oi": ["eae", "opa", "ola", "salve"],
    "triste": ["mal", "deprimido", "pra baixo"],
    "feliz": ["alegre", "animado"],
    "cansado": ["exausto", "morto", "sono"],
    "ansiedade": ["ansioso", "nervoso"],
    "tchau": ["flw", "adeus", "ate logo"]

}

# =========================================
# LIMPEZA
# =========================================

def limpar(texto):

    texto = texto.lower()

    texto = re.sub(r"[^\w\s]", "", texto)

    palavras = texto.split()

    resultado = []

    for p in palavras:

        if p not in STOPWORDS:
            resultado.append(p)

    return resultado

# =========================================
# EXPANDIR SINÔNIMOS
# =========================================

def expandir_palavras(lista):

    expandida = []

    for palavra in lista:

        expandida.append(palavra)

        for chave, sinonimos in SINONIMOS.items():

            if palavra == chave or palavra in sinonimos:

                expandida.append(chave)

                expandida.extend(sinonimos)

    return expandida

# =========================================
# VOCABULÁRIO
# =========================================

def construir_vocabulario():

    palavras = set()

    for item in memoria:

        entrada = item.get("entrada", "")

        lista = limpar(entrada)

        lista = expandir_palavras(lista)

        for p in lista:
            palavras.add(p)

    return sorted(list(palavras))

VOCAB = construir_vocabulario()

# =========================================
# VETORIZAÇÃO
# =========================================

def vetorizar(texto):

    palavras = limpar(texto)

    palavras = expandir_palavras(palavras)

    contagem = Counter(palavras)

    vetor = []

    for palavra in VOCAB:

        vetor.append(contagem.get(palavra, 0))

    return vetor

# =========================================
# SIMILARIDADE
# =========================================

def similaridade(v1, v2):

    produto = sum(a*b for a, b in zip(v1, v2))

    norma1 = math.sqrt(sum(a*a for a in v1))
    norma2 = math.sqrt(sum(b*b for b in v2))

    if norma1 == 0 or norma2 == 0:
        return 0

    return produto / (norma1 * norma2)

# =========================================
# BUSCAR RESPOSTA
# =========================================

def buscar_resposta(user):

    vetor_user = vetorizar(user)

    candidatos = []

    for item in memoria:

        entrada = item["entrada"]

        respostas = item["respostas"]

        peso = item.get("peso", 1)

        vetor_entrada = vetorizar(entrada)

        score = similaridade(vetor_user, vetor_entrada)

        score *= peso

        if score > 0.15:

            resposta = random.choice(respostas)

            candidatos.append((score, resposta, entrada))

    if candidatos:

        candidatos.sort(reverse=True)

        melhor = candidatos[0]

        return melhor[1], melhor[2], round(melhor[0], 3)

    return "Não sei responder isso ainda.", None, 0

# =========================================
# APRENDER
# =========================================

def aprender(entrada, resposta):

    global memoria
    global VOCAB

    entrada = entrada.lower()

    for item in memoria:

        if item["entrada"] == entrada:

            if resposta not in item["respostas"]:

                item["respostas"].append(resposta)

                item["peso"] += 1

                salvar()

                print("Nova resposta adicionada.")

            return

    novo = {

        "entrada": entrada,

        "respostas": [resposta],

        "tags": limpar(entrada),

        "tipo": "geral",

        "peso": 1
    }

    memoria.append(novo)

    salvar()

    VOCAB = construir_vocabulario()

# =========================================
# SALVAR
# =========================================

def salvar():

    with open(ARQUIVO, "w", encoding="utf-8") as f:

        json.dump(memoria, f, ensure_ascii=False, indent=4)

# =========================================
# LOOP
# =========================================

print("="*40)
print("      EVA BRAIN v7")
print("="*40)

while True:

    user = input("\nVocê: ").strip()

    if user.lower() in ["sair", "exit"]:
        break

    resposta, origem, score = buscar_resposta(user)

    print(f"Eva: {resposta}")

    if origem:
        print(f"[similaridade: {score}] [base: {origem}]")

    # -----------------------------
    # SE NÃO SOUBER
    # -----------------------------

    if resposta == "Não sei responder isso ainda.":

        ensinar = input("Ensinar nova resposta? (s/n): ").lower()

        if ensinar == "s":

            nova = input("Nova resposta: ").strip()

            aprender(user, nova)

            print("Eva: Aprendi.")

    # -----------------------------
    # SE JÁ SOUBER
    # -----------------------------

    else:

        expandir = input(
            "Adicionar nova resposta para essa frase? (s/n): "
        ).lower()

        if expandir == "s":

            nova = input("Nova resposta: ").strip()

            aprender(user, nova)

            print("Eva: Memória expandida.")
