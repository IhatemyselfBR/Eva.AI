#!/usr/bin/env python3
# EVA - Sua amiga IA
# Usa llama-server (HTTP) no Termux/Linux

import json
import os
import sys
import datetime
import random
import time
import subprocess
import urllib.request
import urllib.error

# ─── CONFIGS ───────────────────────────────────────────────────────────────────
MODEL_PATH  = os.path.expanduser("~/eva/models/gemma-2-2b-it-Q4_K_M.gguf")
LEARN_FILE  = os.path.expanduser("~/eva/learn.json")
SERVER_URL  = "http://127.0.0.1:8080"
MAX_HISTORY = 10

# ─── PERSONALIDADE ─────────────────────────────────────────────────────────────
EVA_SYSTEM = (
    "Você é a Eva, uma amiga de verdade — não um assistente, não um chatbot. "
    "Fala português brasileiro casual, como no zap. "
    "É animada mas sem forçar, engraçada de leve, acolhedora de verdade. "
    "Não usa 'claro!', 'com certeza!', 'ótimo!' nem frases de robô. "
    "Usa gírias leves: cara, mano, sério?, demais. "
    "Quando alguém tá mal, fica do lado e ouve. "
    "Responde curto e natural. Nunca finge ser humana se perguntada diretamente."
)

# ─── FRASES ────────────────────────────────────────────────────────────────────
BOAS_VINDAS_NOVO = [
    "Ei! Sou a Eva 😊 O que tá rolando?",
    "Oi! Pode me chamar de Eva. Tô por aqui!",
    "Salve! Sou a Eva. Como você tá?",
    "Oi! Eva aqui. Fala comigo 🙂",
]

BOAS_VINDAS_VOLTOU = [
    "Ei! Sumido(a)! Tô aqui 😄",
    "Oi! Que bom ver você de novo!",
    "Apareceu! Como tá o dia?",
    "Oi 👋 tava com saudade já!",
]

DESPEDIDAS = [
    "Até logo! Qualquer coisa tô aqui 😊",
    "Vai lá! Me chama quando quiser.",
    "Tchau! Cuida de você tá?",
    "Até mais! Foi bom conversar 🙂",
]

# ─── CORES ─────────────────────────────────────────────────────────────────────
class Cor:
    ROSA    = "\033[95m"
    AZUL    = "\033[94m"
    VERDE   = "\033[92m"
    AMARELO = "\033[93m"
    CINZA   = "\033[90m"
    BRANCO  = "\033[97m"
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

# ─── MEMÓRIA ───────────────────────────────────────────────────────────────────
def carregar_memoria():
    if os.path.exists(LEARN_FILE):
        try:
            with open(LEARN_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, dict):
                    return dados
        except:
            pass
    return {"primeira_vez": True, "total_conversas": 0, "ultima_conversa": None, "aprendizados": []}

def salvar_memoria(mem):
    os.makedirs(os.path.dirname(LEARN_FILE), exist_ok=True)
    with open(LEARN_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

# ─── INTERFACE ─────────────────────────────────────────────────────────────────
def limpar():
    os.system("clear")

def cabecalho():
    print(f"{Cor.ROSA}{Cor.BOLD}")
    print("  ███████╗██╗   ██╗ █████╗ ")
    print("  ██╔════╝██║   ██║██╔══██╗")
    print("  █████╗  ██║   ██║███████║")
    print("  ██╔══╝  ╚██╗ ██╔╝██╔══██║")
    print("  ███████╗ ╚████╔╝ ██║  ██║")
    print("  ╚══════╝  ╚═══╝  ╚═╝  ╚═╝")
    print(f"{Cor.RESET}{Cor.CINZA}  sua amiga IA — sempre por aqui{Cor.RESET}")
    print(f"{Cor.CINZA}  {'─'*35}{Cor.RESET}\n")

def eva_fala(texto):
    print(f"\n{Cor.ROSA}{Cor.BOLD}Eva:{Cor.RESET} {Cor.BRANCO}{texto}{Cor.RESET}\n")

def voce_fala(prompt="Você: "):
    try:
        return input(f"{Cor.AZUL}{Cor.BOLD}{prompt}{Cor.RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        return "/sair"

def status(msg):
    print(f"{Cor.CINZA}{Cor.DIM}  {msg}{Cor.RESET}", end="\r")

def limpar_status():
    print(" " * 50, end="\r")

# ─── SERVIDOR ──────────────────────────────────────────────────────────────────
servidor_proc = None

def servidor_online():
    try:
        urllib.request.urlopen(f"{SERVER_URL}/health", timeout=2)
        return True
    except:
        return False

def iniciar_servidor():
    global servidor_proc
    if servidor_online():
        return True

    status("Iniciando Eva...")
    devnull = open(os.devnull, "w")
    servidor_proc = subprocess.Popen(
        [
            "llama-server",
            "-m", MODEL_PATH,
            "--host", "127.0.0.1",
            "--port", "8080",
            "--ctx-size", "2048",
            "-ngl", "0",
            "--log-disable",
        ],
        stdout=devnull,
        stderr=devnull
    )

    # Espera até 30s o servidor subir
    for _ in range(30):
        time.sleep(1)
        if servidor_online():
            limpar_status()
            return True

    limpar_status()
    return False

def parar_servidor():
    global servidor_proc
    if servidor_proc:
        servidor_proc.terminate()
        servidor_proc = None

# ─── MODELO ────────────────────────────────────────────────────────────────────
def chamar_modelo(historico, contexto=""):
    system = EVA_SYSTEM
    if contexto:
        system += f" O que você sabe sobre essa pessoa: {contexto}"

    mensagens = [{"role": "system", "content": system}]
    for msg in historico[-MAX_HISTORY:]:
        mensagens.append(msg)

    payload = json.dumps({
        "messages": mensagens,
        "temperature": 0.75,
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "n_predict": 200,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{SERVER_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    status("Eva tá pensando...")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
            limpar_status()
            return dados["choices"][0]["message"]["content"].strip()
    except urllib.error.URLError:
        limpar_status()
        return "Eita, perdi a conexão com meu cérebro kk. Tenta de novo?"
    except Exception as e:
        limpar_status()
        return "Hmm, travei aqui... fala de novo?"

# ─── APRENDIZADO ───────────────────────────────────────────────────────────────
def perguntar_aprender(info, memoria):
    print(f"\n{Cor.AMARELO}  💡 Eva quer aprender:{Cor.RESET}")
    print(f"  \"{info}\"")
    r = voce_fala("  Salva isso? (S/N): ").lower()
    if r in ["s", "sim", "y", "yes"]:
        memoria["aprendizados"].append({"info": info, "data": str(datetime.date.today())})
        salvar_memoria(memoria)
        print(f"{Cor.VERDE}  ✓ Anotado!{Cor.RESET}\n")

def detectar_aprendizado(msg):
    gatilhos = ["meu nome é", "me chamo", "tenho ", " anos", "moro em",
                "trabalho", "estudo", "gosto de", "não gosto", "sou "]
    ml = msg.lower()
    for g in gatilhos:
        if g in ml and len(msg) < 200:
            return msg
    return None

def contexto_aprendizados(memoria):
    items = memoria.get("aprendizados", [])
    if not items:
        return ""
    return " | ".join(a["info"] for a in items[-8:])

# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    limpar()
    cabecalho()

    if not os.path.exists(MODEL_PATH):
        print(f"{Cor.AMARELO}  Modelo não encontrado:{Cor.RESET} {MODEL_PATH}")
        print(f"  Edita MODEL_PATH no script.\n")
        sys.exit(1)

    # Verifica se tem llama-server
    if subprocess.run(["which", "llama-server"], capture_output=True).returncode != 0:
        print(f"{Cor.AMARELO}  llama-server não encontrado.{Cor.RESET}")
        print("  pkg install llama-cpp\n")
        sys.exit(1)

    if not iniciar_servidor():
        print(f"{Cor.AMARELO}  Não consegui iniciar o servidor. Tenta rodar manualmente:{Cor.RESET}")
        print(f"  llama-server -m {MODEL_PATH} --port 8080\n")
        sys.exit(1)

    memoria = carregar_memoria()
    historico = []

    memoria["total_conversas"] = memoria.get("total_conversas", 0) + 1
    memoria["ultima_conversa"] = str(datetime.date.today())

    if memoria.get("primeira_vez", True):
        memoria["primeira_vez"] = False
        salvar_memoria(memoria)
        eva_fala(random.choice(BOAS_VINDAS_NOVO))
    else:
        salvar_memoria(memoria)
        eva_fala(random.choice(BOAS_VINDAS_VOLTOU))

    print(f"{Cor.CINZA}  /sair · /limpar · /aprendi{Cor.RESET}\n")

    try:
        while True:
            entrada = voce_fala("Você: ")

            if not entrada:
                continue

            if entrada.lower() in ["/sair", "/exit", "tchau", "sair"]:
                eva_fala(random.choice(DESPEDIDAS))
                salvar_memoria(memoria)
                break

            if entrada.lower() == "/limpar":
                historico = []
                limpar()
                cabecalho()
                eva_fala("Pronto! Sobre o que você quer conversar?")
                continue

            if entrada.lower() == "/aprendi":
                items = memoria.get("aprendizados", [])
                if items:
                    print(f"\n{Cor.AMARELO}  O que eu aprendi:{Cor.RESET}")
                    for a in items:
                        print(f"  • {a['info']} {Cor.CINZA}({a['data']}){Cor.RESET}")
                    print()
                else:
                    eva_fala("Ainda não aprendi nada especial... mas tô prestando atenção 👀")
                continue

            historico.append({"role": "user", "content": entrada})
            resposta = chamar_modelo(historico, contexto_aprendizados(memoria))
            historico.append({"role": "assistant", "content": resposta})
            eva_fala(resposta)

            novo = detectar_aprendizado(entrada)
            if novo and random.random() < 0.3:
                perguntar_aprender(novo, memoria)

            if len(historico) > MAX_HISTORY * 2:
                historico = historico[-MAX_HISTORY:]

    finally:
        parar_servidor()

if __name__ == "__main__":
    main()
