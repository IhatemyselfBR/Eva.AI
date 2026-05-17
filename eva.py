#!/usr/bin/env python3
# EVA - Sua amiga IA
# Usa llama-server (HTTP) no Termux/Linux

import json
import os
import re
import sys
import shutil
import hashlib
import secrets
import datetime
import random
import time
import subprocess
import urllib.request
import urllib.error

# ─── CONFIGS ───────────────────────────────────────────────────────────────────
MODEL_PATH   = os.path.expanduser("~/eva/models/gemma-2-2b-it-Q4_K_M.gguf")
LEARNS_DIR   = os.path.expanduser("~/eva/learns")
USERS_FILE   = os.path.expanduser("~/eva/users.json")
SESSION_FILE = os.path.expanduser("~/.eva_session")  # escondido na home
SERVER_URL   = "http://127.0.0.1:8080"
MAX_HISTORY  = 10

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
    "Que bom te ver de novo, {nome} 😊 Como tá?",
    "Ei {nome}! Sumido(a)! Tô aqui 😄",
    "{nome}! Apareceu! Como tá o dia?",
    "Oi {nome} 👋 tava com saudade já!",
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

# ─── HASH E TOKEN ──────────────────────────────────────────────────────────────
def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def gerar_token():
    return secrets.token_hex(32)

def salvar_session(username, token):
    dados = {"username": username, "token": token}
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f)
    # Permissão só pro dono do arquivo
    os.chmod(SESSION_FILE, 0o600)

def carregar_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

def limpar_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# ─── USUÁRIOS ──────────────────────────────────────────────────────────────────
def carregar_users():
    os.makedirs(LEARNS_DIR, exist_ok=True)
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def salvar_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ─── MEMÓRIA ───────────────────────────────────────────────────────────────────
def perfil_padrao(username):
    return {
        "username": username,
        "primeira_vez": True,
        "total_conversas": 0,
        "ultima_conversa": None,
        "perfil": {
            "nome": username,
            "gostos": [],
            "nao_gosta": [],
            "humor_frequente": None,
            "problemas_relatados": [],
            "aniversario": None,
            "outros": []
        }
    }

def caminho_learn(username):
    return os.path.join(LEARNS_DIR, f"{username}.json")

def carregar_memoria(username):
    path = caminho_learn(username)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, dict):
                    return dados
        except json.JSONDecodeError:
            bak = path + ".bak"
            shutil.copy2(path, bak)
            print(f"{Cor.AMARELO}  JSON corrompido, backup salvo.{Cor.RESET}")
        except:
            pass
    return perfil_padrao(username)

def salvar_memoria(mem, username):
    os.makedirs(LEARNS_DIR, exist_ok=True)
    with open(caminho_learn(username), "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

# ─── LOGIN ─────────────────────────────────────────────────────────────────────
def pedir_input(prompt):
    print(f"{Cor.AZUL}{Cor.BOLD}  {prompt}{Cor.RESET}", end="")
    try:
        return input().strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)

def pedir_senha(prompt="Senha: "):
    """Pede senha sem eco no terminal"""
    import getpass
    try:
        return getpass.getpass(f"{Cor.AZUL}{Cor.BOLD}  {prompt}{Cor.RESET}")
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)

def login():
    users = carregar_users()

    # Verifica sessão salva no dispositivo
    session = carregar_session()
    if session:
        username = session.get("username")
        token    = session.get("token")
        if username in users and users[username].get("token") == token:
            mem = carregar_memoria(username)
            return username, mem
        else:
            # Token inválido, limpa
            limpar_session()

    # Pede username
    username = pedir_input("User: ").lower().replace(" ", "_")
    if not username:
        return login()

    if username in users:
        # Usuário existe — pede senha
        for tentativa in range(3):
            senha = pedir_senha("Senha: ")
            if hash_senha(senha) == users[username]["senha"]:
                # Senha correta — gera token e salva sessão
                token = gerar_token()
                users[username]["token"] = token
                salvar_users(users)
                salvar_session(username, token)
                print(f"{Cor.VERDE}  ✓ Bem-vindo de volta!{Cor.RESET}\n")
                return username, carregar_memoria(username)
            else:
                restam = 2 - tentativa
                if restam > 0:
                    print(f"{Cor.AMARELO}  Senha errada. {restam} tentativa(s) restante(s).{Cor.RESET}")
                else:
                    print(f"{Cor.AMARELO}  Muitas tentativas. Tenta de novo.{Cor.RESET}\n")
                    sys.exit(0)
    else:
        # Usuário não existe
        print(f"{Cor.AMARELO}  Usuário não encontrado. Deseja criar? (S/N): {Cor.RESET}", end="")
        try:
            resp = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)

        if resp not in ["s", "sim", "y", "yes"]:
            print(f"{Cor.CINZA}  Ok, até mais!{Cor.RESET}\n")
            sys.exit(0)

        # Cria conta
        senha = pedir_senha("Crie uma senha: ")
        if not senha:
            print(f"{Cor.AMARELO}  Senha não pode ser vazia.{Cor.RESET}\n")
            sys.exit(0)

        confirma = pedir_senha("Confirme a senha: ")
        if senha != confirma:
            print(f"{Cor.AMARELO}  Senhas não batem. Tenta de novo.{Cor.RESET}\n")
            sys.exit(0)

        token = gerar_token()
        users[username] = {
            "senha": hash_senha(senha),
            "token": token,
            "criado_em": str(datetime.date.today())
        }
        salvar_users(users)
        salvar_session(username, token)

        mem = perfil_padrao(username)
        salvar_memoria(mem, username)
        print(f"{Cor.VERDE}  ✓ Conta criada!{Cor.RESET}\n")
        return username, mem

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

    for _ in range(30):
        time.sleep(1)
        if servidor_online():
            limpar_status()
            return True
        if servidor_proc.poll() is not None:
            limpar_status()
            return False

    limpar_status()
    return False

def parar_servidor():
    global servidor_proc
    if servidor_proc:
        servidor_proc.terminate()
        servidor_proc = None

# ─── MODELO ────────────────────────────────────────────────────────────────────
def montar_contexto(perfil):
    partes = []
    if perfil.get("nome"):
        partes.append(f"nome: {perfil['nome']}")
    if perfil.get("gostos"):
        partes.append(f"gosta de: {', '.join(perfil['gostos'][-5:])}")
    if perfil.get("nao_gosta"):
        partes.append(f"não gosta de: {', '.join(perfil['nao_gosta'][-5:])}")
    if perfil.get("humor_frequente"):
        partes.append(f"humor frequente: {perfil['humor_frequente']}")
    if perfil.get("problemas_relatados"):
        partes.append(f"já relatou: {', '.join(perfil['problemas_relatados'][-3:])}")
    if perfil.get("aniversario"):
        partes.append(f"aniversário: {perfil['aniversario']}")
    if perfil.get("outros"):
        partes.append(f"outros: {', '.join(perfil['outros'][-5:])}")
    return " | ".join(partes)

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
        "repeat_penalty": 1.15,
        "repeat_last_n": 64,
        "mirostat": 2,
        "mirostat_tau": 5.0,
        "mirostat_eta": 0.1,
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
    except Exception:
        limpar_status()
        return "Hmm, travei aqui... fala de novo?"

# ─── APRENDIZADO ───────────────────────────────────────────────────────────────
_RE_NOME = re.compile(
    r"(?:meu nome é|me chamo|pode me chamar de|sou o|sou a)\s+([a-záàãâéêíóôõúüç]+)",
    re.IGNORECASE
)
_RE_GOSTO = re.compile(
    r"(?:gosto de|adoro|amo|curto|meu hobby é|meu hobbie é|minha paixão é)\s+(.+?)(?=\s*(?:e não|mas não|,?\s*não gosto)|$)",
    re.IGNORECASE
)
_RE_NAO_GOSTO = re.compile(
    r"(?:não gosto de|odeio|detesto|não curto|não suporto)\s+(.+?)(?=\s*(?:e gosto|mas gosto)|$)",
    re.IGNORECASE
)
_RE_PROBLEMA = re.compile(
    r"(?:tô|estou|me sinto)\s+(mal|triste|ansioso|ansiosa|sozinho|sozinha|deprimido|deprimida|cansado|cansada|com medo|estressado|estressada)",
    re.IGNORECASE
)
_RE_HUMOR_BOM = re.compile(
    r"(?:tô|estou|me sinto)\s+(bem|feliz|ótimo|ótima|animado|animada)",
    re.IGNORECASE
)
_RE_ANIVERSARIO = re.compile(
    r"(?:meu aniversário é|faço aniversário|nasci em|nasci no dia)\s+(.+?)(?:\s*[,.]|$)",
    re.IGNORECASE
)
_RE_OUTROS = re.compile(
    r"(?:tenho\s+\d+\s+anos|moro em|trabalho\s+(?:em|como|na|no)|estudo\s+(?:em|na|no)|sou\s+\w+)",
    re.IGNORECASE
)

def classificar_e_salvar(msg, perfil):
    atualizado = False

    m = _RE_NOME.search(msg)
    if m:
        perfil["nome"] = m.group(1).capitalize()
        atualizado = True

    m = _RE_GOSTO.search(msg)
    if m:
        raw = m.group(1).strip().rstrip(".,!")
        for item in re.split(r",\s*|\s+e\s+", raw):
            item = item.strip().rstrip(".,!")
            if item and item.lower() not in [g.lower() for g in perfil["gostos"]]:
                perfil["gostos"].append(item)
        atualizado = True

    m = _RE_NAO_GOSTO.search(msg)
    if m:
        raw = m.group(1).strip().rstrip(".,!")
        for item in re.split(r",\s*|\s+e\s+", raw):
            item = item.strip().rstrip(".,!")
            if item and item.lower() not in [g.lower() for g in perfil["nao_gosta"]]:
                perfil["nao_gosta"].append(item)
        atualizado = True

    m = _RE_PROBLEMA.search(msg)
    if m:
        estado = m.group(1).lower()
        if estado not in perfil["problemas_relatados"]:
            perfil["problemas_relatados"].append(estado)
        perfil["humor_frequente"] = estado
        atualizado = True

    m = _RE_HUMOR_BOM.search(msg)
    if m:
        perfil["humor_frequente"] = m.group(1).lower()
        atualizado = True

    m = _RE_ANIVERSARIO.search(msg)
    if m:
        perfil["aniversario"] = m.group(1).strip()
        atualizado = True

    if not atualizado:
        m = _RE_OUTROS.search(msg)
        if m and len(msg) < 150:
            if msg not in perfil["outros"]:
                perfil["outros"].append(msg)
            atualizado = True

    return atualizado

def detectar_aprendizado(msg):
    return bool(
        _RE_NOME.search(msg) or _RE_GOSTO.search(msg) or
        _RE_NAO_GOSTO.search(msg) or _RE_PROBLEMA.search(msg) or
        _RE_HUMOR_BOM.search(msg) or _RE_ANIVERSARIO.search(msg) or
        _RE_OUTROS.search(msg)
    )

def perguntar_aprender(msg, memoria, username):
    print(f"\n{Cor.AMARELO}  💡 Eva quer aprender:{Cor.RESET}")
    print(f"  \"{msg}\"")
    r = voce_fala("  Salva isso? (S/N): ").lower()
    if r in ["s", "sim", "y", "yes"]:
        if classificar_e_salvar(msg, memoria["perfil"]):
            salvar_memoria(memoria, username)
            print(f"{Cor.VERDE}  ✓ Anotado!{Cor.RESET}\n")
        else:
            print(f"{Cor.CINZA}  Não consegui classificar, tudo bem.{Cor.RESET}\n")

def mostrar_perfil(memoria):
    perfil = memoria.get("perfil", {})
    tem = any(perfil.get(k) for k in ["gostos","nao_gosta","humor_frequente","problemas_relatados","aniversario","outros"])
    if not tem:
        eva_fala("Ainda não aprendi nada especial... mas tô prestando atenção 👀")
        return
    print(f"\n{Cor.AMARELO}  O que eu sei sobre você:{Cor.RESET}")
    if perfil.get("nome"):        print(f"  Nome:        {perfil['nome']}")
    if perfil.get("gostos"):      print(f"  Gosta de:    {', '.join(perfil['gostos'])}")
    if perfil.get("nao_gosta"):   print(f"  Não gosta:   {', '.join(perfil['nao_gosta'])}")
    if perfil.get("humor_frequente"): print(f"  Humor:       {perfil['humor_frequente']}")
    if perfil.get("problemas_relatados"): print(f"  Já relatou:  {', '.join(perfil['problemas_relatados'])}")
    if perfil.get("aniversario"): print(f"  Aniversário: {perfil['aniversario']}")
    if perfil.get("outros"):      print(f"  Outros:      {', '.join(perfil['outros'])}")
    print()

# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    limpar()
    cabecalho()

    if not os.path.exists(MODEL_PATH):
        print(f"{Cor.AMARELO}  Modelo não encontrado:{Cor.RESET} {MODEL_PATH}")
        sys.exit(1)

    if subprocess.run(["which", "llama-server"], capture_output=True).returncode != 0:
        print(f"{Cor.AMARELO}  llama-server não encontrado.{Cor.RESET}")
        print("  pkg install llama-cpp\n")
        sys.exit(1)

    if not iniciar_servidor():
        print(f"{Cor.AMARELO}  Não consegui iniciar o servidor.{Cor.RESET}")
        sys.exit(1)

    username, memoria = login()
    historico = []

    memoria["total_conversas"] = memoria.get("total_conversas", 0) + 1
    memoria["ultima_conversa"] = str(datetime.date.today())

    if memoria.get("primeira_vez", True):
        memoria["primeira_vez"] = False
        salvar_memoria(memoria, username)
        eva_fala(random.choice(BOAS_VINDAS_NOVO))
    else:
        salvar_memoria(memoria, username)
        nome = memoria.get("perfil", {}).get("nome", username)
        eva_fala(random.choice(BOAS_VINDAS_VOLTOU).format(nome=nome))

    print(f"{Cor.CINZA}  /sair · /limpar · /aprendi · /esquecer · /sair-conta{Cor.RESET}\n")

    try:
        while True:
            entrada = voce_fala("Você: ")

            if not entrada:
                continue

            if entrada.lower() in ["/sair", "/exit", "tchau", "sair"]:
                eva_fala(random.choice(DESPEDIDAS))
                salvar_memoria(memoria, username)
                break

            if entrada.lower() == "/sair-conta":
                limpar_session()
                eva_fala("Sessão encerrada! Na próxima vai pedir senha de novo 🔒")
                salvar_memoria(memoria, username)
                break

            if entrada.lower() == "/limpar":
                historico = []
                limpar()
                cabecalho()
                eva_fala("Pronto! Sobre o que você quer conversar?")
                continue

            if entrada.lower() == "/aprendi":
                mostrar_perfil(memoria)
                continue

            if entrada.lower() == "/esquecer":
                memoria["perfil"] = perfil_padrao(username)["perfil"]
                salvar_memoria(memoria, username)
                eva_fala("Esqueci tudo sobre você. Vamos começar do zero 🙂")
                continue

            historico.append({"role": "user", "content": entrada})
            contexto = montar_contexto(memoria.get("perfil", {}))
            resposta = chamar_modelo(historico, contexto)
            historico.append({"role": "assistant", "content": resposta})
            eva_fala(resposta)

            if detectar_aprendizado(entrada):
                perguntar_aprender(entrada, memoria, username)

            if len(historico) > MAX_HISTORY * 2:
                historico = historico[-MAX_HISTORY:]

    finally:
        parar_servidor()

if __name__ == "__main__":
    main()
