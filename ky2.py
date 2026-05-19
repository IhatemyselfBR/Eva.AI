#!/usr/bin/env python3

import json
import urllib.request
import urllib.error
import getpass
import os

SERVER_URL = input("Link do Cloudflare: ").strip()

if SERVER_URL.endswith("/"):
    SERVER_URL = SERVER_URL[:-1]

def limpar():
    os.system("clear")

class Cor:
    ROSA     = "\033[95m"
    AZUL     = "\033[94m"
    VERDE    = "\033[92m"
    AMARELO  = "\033[93m"
    CINZA    = "\033[90m"
    VERMELHO = "\033[91m"
    BRANCO   = "\033[97m"
    RESET    = "\033[0m"
    BOLD     = "\033[1m"

def cabecalho():
    print(f"{Cor.ROSA}{Cor.BOLD}")
    print("  ███████╗██╗   ██╗ █████╗ ")
    print("  ██╔════╝██║   ██║██╔══██╗")
    print("  █████╗  ██║   ██║███████║")
    print("  ██╔══╝  ╚██╗ ██╔╝██╔══██║")
    print("  ███████╗ ╚████╔╝ ██║  ██║")
    print("  ╚══════╝  ╚═══╝  ╚═╝  ╚═╝")
    print(f"{Cor.RESET}{Cor.CINZA}  cliente remoto da Eva{Cor.RESET}")
    print(f"{Cor.CINZA}  {'─'*35}{Cor.RESET}\n")

def status(msg):
    print(f"{Cor.CINZA}  {msg}{Cor.RESET}")

def eva_fala(msg):
    print(f"\n{Cor.ROSA}{Cor.BOLD}Eva:{Cor.RESET} {Cor.BRANCO}{msg}{Cor.RESET}\n")

def voce_fala():
    return input(f"{Cor.AZUL}{Cor.BOLD}Você:{Cor.RESET} ").strip()

def mostrar_cmds(tipo="user"):

    cmds = [
        "/limpar",
        "/sair"
    ]

    if tipo == "admin":
        cmds.append("/admin")

    if tipo == "superadmin":
        cmds.append("/admin")
        cmds.append("/superadmin")

    linha = " · ".join(cmds)

    print(f"{Cor.CINZA}  {linha}{Cor.RESET}\n")

def login():

    limpar()

    cabecalho()

    print(f"{Cor.AMARELO}Conectando:{Cor.RESET} {SERVER_URL}\n")

    username = input(
        f"{Cor.AZUL}{Cor.BOLD}User:{Cor.RESET} "
    ).strip().lower()

    senha = getpass.getpass(
        f"{Cor.AZUL}{Cor.BOLD}Senha:{Cor.RESET} "
    )

    return username, senha

username, senha = login()

def enviar(payload):

    req = urllib.request.Request(
        f"{SERVER_URL}/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(
            resp.read().decode("utf-8")
        )

try:

    auth = enviar({
        "username": username,
        "senha": senha,
        "mensagem": "__login__"
    })

except Exception as e:

    print(f"\nErro: {e}\n")
    raise SystemExit

if "erro" in auth:

    print(f"\n{Cor.VERMELHO}{auth['erro']}{Cor.RESET}\n")
    raise SystemExit

tipo = auth.get("tipo", "user")

limpar()
cabecalho()

print(
    f"{Cor.VERDE}✓ Conectado como {username}{Cor.RESET}\n"
)

mostrar_cmds(tipo)

while True:

    try:

        entrada = voce_fala()

        if not entrada:
            continue

        if entrada.lower() == "/limpar":

            limpar()
            cabecalho()

            print(
                f"{Cor.VERDE}✓ Conectado como {username}{Cor.RESET}\n"
            )

            mostrar_cmds(tipo)

            continue

        if entrada.lower() in [
            "/sair",
            "sair",
            "exit"
        ]:

            print(
                f"\n{Cor.CINZA}Até depois.{Cor.RESET}\n"
            )

            break

        status("Eva tá pensando...")

        dados = enviar({
            "username": username,
            "senha": senha,
            "mensagem": entrada
        })

        print(" " * 60, end="\r")

        if "erro" in dados:

            print(
                f"\n{Cor.VERMELHO}{dados['erro']}{Cor.RESET}\n"
            )

            continue

        resposta = dados.get(
            "resposta",
            "Sem resposta."
        )

        eva_fala(resposta)

    except KeyboardInterrupt:

        print(
            f"\n{Cor.CINZA}Saindo...{Cor.RESET}\n"
        )

        break

    except Exception as e:

        print(
            f"\n{Cor.VERMELHO}Erro:{Cor.RESET} {e}\n"
        )
