#!/usr/bin/env python3

import json
import os
import re
import sys
import hashlib
import secrets
import datetime
import random
import time
import subprocess
import urllib.request
import urllib.error
import threading
import getpass

from flask import Flask, request, jsonify

MODEL_PATH = os.path.expanduser("~/eva/models/gemma-2-2b-it-Q4_K_M.gguf")
LEARNS_DIR = os.path.expanduser("~/eva-db/learns")
USERS_FILE = os.path.expanduser("~/eva-db/users.json")
SESSION_FILE = os.path.expanduser("~/.eva_session")

SERVER_URL = "http://127.0.0.1:8080"

MAX_HISTORY = 10

app = Flask(__name__)

EVA_SYSTEM = (
    "Você é a Eva, uma amiga virtual natural e casual. "
    "Fala português brasileiro informal como conversa real. "
    "Responde curto, humana e acolhedora."
)

class Cor:
    ROSA     = "\033[95m"
    AZUL     = "\033[94m"
    VERDE    = "\033[92m"
    AMARELO  = "\033[93m"
    CINZA    = "\033[90m"
    RESET    = "\033[0m"
    BOLD     = "\033[1m"

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
    print(f"{Cor.RESET}")

def eva_fala(msg):
    print(f"\n{Cor.ROSA}{Cor.BOLD}Eva:{Cor.RESET} {msg}\n")

def voce_fala(txt="Você: "):
    return input(f"{Cor.AZUL}{Cor.BOLD}{txt}{Cor.RESET}").strip()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def gerar_token():
    return secrets.token_hex(32)

def carregar_users():

    os.makedirs(LEARNS_DIR, exist_ok=True)

    if os.path.exists(USERS_FILE):

        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}

def salvar_users(users):

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def caminho_learn(username):
    return os.path.join(LEARNS_DIR, f"{username}.json")

def perfil_padrao(username):

    return {
        "username": username,
        "perfil": {
            "nome": username,
            "gostos": [],
            "nao_gosta": [],
            "interesses": []
        },
        "_temp_chat": []
    }

def carregar_memoria(username):

    path = caminho_learn(username)

    if os.path.exists(path):

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    return perfil_padrao(username)

def salvar_memoria(mem, username):

    with open(caminho_learn(username), "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

def servidor_online():

    try:
        urllib.request.urlopen(f"{SERVER_URL}/health", timeout=2)
        return True
    except:
        return False

servidor_proc = None

def iniciar_servidor():

    global servidor_proc

    if servidor_online():
        return True

    servidor_proc = subprocess.Popen([
        "llama-server",
        "-m", MODEL_PATH,
        "--host", "0.0.0.0",
        "--port", "8080",
        "--ctx-size", "2048",
        "-ngl", "0",
        "--log-disable"
    ])

    for _ in range(30):

        time.sleep(1)

        if servidor_online():
            return True

    return False

def montar_contexto(perfil):

    partes = []

    if perfil.get("nome"):
        partes.append(f"nome: {perfil['nome']}")

    if perfil.get("gostos"):
        partes.append(
            f"gosta de: {', '.join(perfil['gostos'])}"
        )

    if perfil.get("nao_gosta"):
        partes.append(
            f"não gosta de: {', '.join(perfil['nao_gosta'])}"
        )

    if perfil.get("interesses"):
        partes.append(
            f"interesses: {', '.join(perfil['interesses'])}"
        )

    return " | ".join(partes)

def chamar_modelo(historico, contexto=""):

    mensagens = [
        {
            "role": "system",
            "content": EVA_SYSTEM + " " + contexto
        }
    ]

    mensagens.extend(historico[-MAX_HISTORY:])

    payload = json.dumps({
        "messages": mensagens,
        "temperature": 0.7,
        "top_p": 0.9,
        "n_predict": 200,
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{SERVER_URL}/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(req, timeout=120) as resp:

            dados = json.loads(
                resp.read().decode("utf-8")
            )

            return dados["choices"][0]["message"]["content"]

    except:
        return "Deu ruim aqui 😭"

_RE_GOSTO = re.compile(
    r"(?:gosto de|adoro|amo)\s+(.+)",
    re.IGNORECASE
)

def aprender(msg, perfil):

    m = _RE_GOSTO.search(msg)

    if m:

        gosto = m.group(1).strip()

        if gosto not in perfil["gostos"]:
            perfil["gostos"].append(gosto)

@app.route("/chat", methods=["POST"])
def api_chat():

    dados = request.json

    username = dados.get("username", "").lower()
    senha = dados.get("senha", "")
    mensagem = dados.get("mensagem", "")

    users = carregar_users()

    if username not in users:

        return jsonify({
            "erro": "Usuário não existe"
        }), 401

    if hash_senha(senha) != users[username]["senha"]:

        return jsonify({
            "erro": "Senha inválida"
        }), 401

    if mensagem == "__login__":

        tipo = "user"

        if users[username].get("superadmin"):
            tipo = "superadmin"

        elif users[username].get("admin"):
            tipo = "admin"

        return jsonify({
            "ok": True,
            "tipo": tipo
        })

    memoria = carregar_memoria(username)

    historico = memoria.get("_temp_chat", [])

    historico.append({
        "role": "user",
        "content": mensagem
    })

    contexto = montar_contexto(
        memoria.get("perfil", {})
    )

    resposta = chamar_modelo(
        historico,
        contexto
    )

    historico.append({
        "role": "assistant",
        "content": resposta
    })

    memoria["_temp_chat"] = historico[-MAX_HISTORY:]

    aprender(mensagem, memoria["perfil"])

    salvar_memoria(memoria, username)

    return jsonify({
        "resposta": resposta
    })

def login():

    users = carregar_users()

    username = voce_fala("User: ").lower()

    if username in users:

        senha = getpass.getpass("Senha: ")

        if hash_senha(senha) != users[username]["senha"]:

            print("Senha errada.")
            sys.exit(0)

        return username, carregar_memoria(username), users

    senha = getpass.getpass("Crie uma senha: ")

    users[username] = {
        "senha": hash_senha(senha),
        "admin": False,
        "superadmin": False,
        "token": gerar_token()
    }

    salvar_users(users)

    memoria = perfil_padrao(username)

    salvar_memoria(memoria, username)

    return username, memoria, users

def main():

    limpar()

    cabecalho()

    print("Iniciando servidor...\n")

    if not iniciar_servidor():

        print("Erro ao iniciar llama-server")
        return

    print("Servidor iniciado.\n")

    username, memoria, users = login()

    historico = memoria.get("_temp_chat", [])

    eva_fala(f"Oi {username} 😊")

    while True:

        entrada = voce_fala()

        if not entrada:
            continue

        if entrada.lower() in [
            "/sair",
            "sair",
            "exit"
        ]:

            eva_fala("Até depois 🙂")
            break

        historico.append({
            "role": "user",
            "content": entrada
        })

        contexto = montar_contexto(
            memoria["perfil"]
        )

        resposta = chamar_modelo(
            historico,
            contexto
        )

        historico.append({
            "role": "assistant",
            "content": resposta
        })

        memoria["_temp_chat"] = historico[-MAX_HISTORY:]

        aprender(
            entrada,
            memoria["perfil"]
        )

        salvar_memoria(memoria, username)

        eva_fala(resposta)

threading.Thread(
    target=lambda: app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    ),
    daemon=True
).start()

if __name__ == "__main__":
    main()
