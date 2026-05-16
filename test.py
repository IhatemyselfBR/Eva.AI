import json
import random
import re

# ========================================
# EVA - BRAIN TEST
# ========================================

print("========================================")
print("        EVA - BRAIN TEST")
print("========================================\n")

# ===== CARREGAR MEMÓRIA =====

with open("learning.json", "r", encoding="utf-8") as f:
    memoria = json.load(f)

# ===== MEMÓRIA DE CONTEXTO =====

historico = []

# ===== PALAVRAS INÚTEIS =====

stopwords = {
    "o", "a", "os", "as", "de", "da", "do",
    "e", "é", "que", "um", "uma", "pra",
    "para", "com", "em", "no", "na",
    "tudo", "isso", "essa", "esse"
}

# ===== LIMPEZA =====

def limpar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)
    palavras = texto.split()

    return [
        p for p in palavras
        if p not in stopwords and len(p) > 1
    ]

# ===== BUSCA INTELIGENTE =====

def buscar_resposta(user):

    palavras = limpar(user)

    melhores = []

    for chave, dados in memoria.items():

        if not isinstance(dados, dict):
            continue

        texto = dados.get("texto", "")
        tags = dados.get("tags", [])
        peso = dados.get("peso", 1)

        score = 0

        # ===== SCORE POR TAG =====

        for palavra in palavras:

            if palavra in tags:
                score += 3

            if palavra in texto.lower():
                score += 2

        # ===== CONTEXTO =====

        for antiga in historico[-3:]:

            for palavra in limpar(antiga):

                if palavra in tags:
                    score += 1

        # ===== BONUS PESO =====

        score += peso * 0.2

        if score > 0:
            melhores.append((score, texto))

    # ===== ESCOLHER MELHOR =====

    if melhores:

        melhores.sort(reverse=True)

        top = melhores[:5]

        resposta = random.choice(top)[1]

        return resposta

    return "Ainda não sei responder isso."

# ===== LOOP =====

while True:

    user = input("Você: ").strip()

    if user.lower() in ["sair", "exit"]:
        print("\nEncerrando...")
        break

    resposta = buscar_resposta(user)

    print("Eva:", resposta)

    historico.append(user)

    # Limita histórico
    if len(historico) > 10:
        historico.pop(0)
