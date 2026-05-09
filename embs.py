import json
import os
import re

# =========================
# CONFIG
# =========================

ARQUIVO = "learning.json"

# =========================
# MAPA SEMÂNTICO
# =========================

MAPA = {

    "gato": [
        "felino",
        "gatinho",
        "cat",
        "bichano"
    ],

    "cachorro": [
        "dog",
        "doguinho",
        "cao",
        "cão",
        "canino"
    ],

    "python": [
        "programacao",
        "programação",
        "linguagem",
        "codigo",
        "código"
    ],

    "martelo": [
        "ferramenta",
        "construcao",
        "construção",
        "obra"
    ],

    "ia": [
        "inteligencia artificial",
        "ai",
        "machine learning",
        "rede neural"
    ]
}

# =========================
# LOAD
# =========================

if not os.path.exists(ARQUIVO):
    print("learning.json não encontrado.")
    exit()

with open(ARQUIVO, 'r', encoding='utf-8') as f:
    memoria = json.load(f)

# =========================
# FUNÇÕES
# =========================

def limpar(txt):

    txt = txt.lower()

    txt = re.sub(r'[^\w\s]', '', txt)

    return txt


def gerar_tags(texto):

    texto = limpar(texto)

    tags = []

    palavras = texto.split()

    # palavras normais
    for p in palavras:

        if len(p) > 3:
            tags.append(p)

    # mapa semântico
    for base, sinonimos in MAPA.items():

        if base in texto:
            tags.append(base)

        for s in sinonimos:

            if s in texto:
                tags.append(base)

    # remove repetidos
    tags = list(set(tags))

    return tags

# =========================
# PROCESSAR MEMÓRIA
# =========================

total = 0

for chave in memoria:

    dado = memoria[chave]

    if not isinstance(dado, dict):
        continue

    pergunta = chave.replace("__", " ")

    resposta = dado.get("texto", "")

    texto_total = f"{pergunta} {resposta}"

    tags = gerar_tags(texto_total)

    memoria[chave]["tags"] = tags

    print(f"\n[{chave}]")
    print(tags)

    total += 1

# =========================
# SAVE
# =========================

with open(ARQUIVO, 'w', encoding='utf-8') as f:

    json.dump(
        memoria,
        f,
        indent=4,
        ensure_ascii=False
    )

print(f"\n{total} pseudo-embeddings gerados.")
