import json
import os
import wikipedia
import re
from datetime import datetime

# =========================
# CONFIG
# =========================

TOPICS_FILE = "topics.txt"
MEM_FILE = "learning.json"

wikipedia.set_lang("pt")

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
# MEMÓRIA
# =========================

def carregar_memoria():
    if not os.path.exists(MEM_FILE):
        return {}

    try:
        with open(MEM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # normaliza estrutura quebrada
        for k in list(data.keys()):
            if "texto" not in data[k]:
                del data[k]
                continue

            if "tokens" not in data[k]:
                data[k]["tokens"] = tokens(data[k]["texto"])

        return data

    except:
        return {}

def salvar_memoria(mem):
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=4, ensure_ascii=False)

# =========================
# TOPICS
# =========================

def carregar_topics():
    if not os.path.exists(TOPICS_FILE):
        log("topics.txt não encontrado.")
        return []

    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        return [t.strip() for t in f.readlines() if t.strip()]

# =========================
# APRENDER
# =========================

def aprender(mem, termo):
    try:
        log(f"Pesquisando: {termo}")

        resumo = wikipedia.summary(termo, sentences=2)

        if not resumo or len(resumo) < 20:
            log(f"Ignorado: {termo}")
            return

        mem[termo] = {
            "texto": resumo,
            "tokens": tokens(resumo),
            "hora": str(datetime.now()),
            "peso": 1
        }

        log(f"Aprendido: {termo}")

    except Exception as e:
        log(f"Erro em '{termo}': {e}")

# =========================
# EXECUÇÃO ÚNICA
# =========================

def executar():
    mem = carregar_memoria()
    topics = carregar_topics()

    if not topics:
        log("Sem tópicos.")
        return

    log("Iniciando aprendizado único...")

    for termo in topics:
        if termo not in mem:
            aprender(mem, termo)
            salvar_memoria(mem)

    log("Finalizado. Nada mais para fazer.")

# =========================
# START
# =========================

executar()
