import json
import os
import time
import random
import wikipedia
import re
from datetime import datetime

# =========================
# CONFIG
# =========================

MEM_FILE = "learning.json"
wikipedia.set_lang("pt")

# =========================
# BASE DE PARTIDA
# =========================

SEMENTES = [
    "ansiedade", "depressão", "felicidade", "motivação",
    "autoestima", "amor", "amizade", "dinheiro",
    "trabalho", "estudo", "tecnologia", "filosofia",
    "matemática", "internet", "saúde", "decisão"
]

# =========================
# UTIL
# =========================

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def limpar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)
    return texto

def tokens(texto):
    return [t for t in limpar(texto).split() if len(t) > 3]

# =========================
# MEMÓRIA (ROBUSTA)
# =========================

def carregar():
    if not os.path.exists(MEM_FILE):
        return {}

    try:
        with open(MEM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # garante consistência
        for k in list(data.keys()):
            if "texto" not in data[k]:
                del data[k]
            else:
                if "tokens" not in data[k]:
                    data[k]["tokens"] = tokens(data[k]["texto"])

        return data

    except:
        return {}

def salvar(mem):
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=4, ensure_ascii=False)

# =========================
# APRENDER
# =========================

def aprender(mem, termo):
    try:
        resumo = wikipedia.summary(termo, sentences=2)

        if not resumo or len(resumo) < 20:
            return

        mem[termo] = {
            "texto": resumo,
            "tokens": tokens(resumo),
            "hora": str(datetime.now())
        }

        log(f"Aprendido: {termo}")

    except Exception as e:
        log(f"Erro: {e}")

# =========================
# RELAÇÃO ENTRE CONCEITOS
# =========================

def similaridade(a_tokens, b_tokens):
    a = set(a_tokens)
    b = set(b_tokens)

    if not a or not b:
        return 0

    inter = len(a & b)
    uni = len(a | b)

    return inter / uni

def associar(mem, termo):
    if termo not in mem:
        return []

    base = mem[termo]["tokens"]

    relacoes = []

    for k, v in mem.items():
        if k == termo:
            continue

        score = similaridade(base, v["tokens"])

        if score > 0:
            relacoes.append((k, score))

    relacoes.sort(key=lambda x: x[1], reverse=True)

    return relacoes[:3]

# =========================
# LOOP PRINCIPAL
# =========================

def treinar():
    mem = carregar()

    fila = list(SEMENTES)
    random.shuffle(fila)

    log("Auto aprendizado iniciado.")

    while True:

        if not fila:
            fila = list(SEMENTES)
            random.shuffle(fila)

        termo = fila.pop()

        if termo in mem:
            continue

        log(f"Pesquisando: {termo}")

        aprender(mem, termo)
        salvar(mem)

        # teste de "consciência associativa"
        if mem:
            alvo = random.choice(list(mem.keys()))
            rel = associar(mem, alvo)

            log(f"Associações de '{alvo}': {rel}")

        time.sleep(2)

# =========================
# START
# =========================

treinar()
