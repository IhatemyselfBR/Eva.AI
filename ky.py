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
LEARNS_DIR   = os.path.expanduser("~/eva-db/learns")
USERS_FILE   = os.path.expanduser("~/eva-db/users.json")
SESSION_FILE = os.path.expanduser("~/.eva_session")
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
    ROSA     = "\033[95m"
    AZUL     = "\033[94m"
    VERDE    = "\033[92m"
    AMARELO  = "\033[93m"
    CINZA    = "\033[90m"
    VERMELHO = "\033[91m"
    BRANCO   = "\033[97m"
    RESET    = "\033[0m"
    BOLD     = "\033[1m"
    DIM      = "\033[2m"

# ─── HASH E TOKEN ──────────────────────────────────────────────────────────────
def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def gerar_token():
    return secrets.token_hex(32)

def salvar_session(username, token):
    dados = {"username": username, "token": token}
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f)
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

def is_admin(username, users):
    return users.get(username, {}).get("admin", False)

def is_superadmin(username, users):
    return users.get(username, {}).get("superadmin", False)

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
            "interesses": [],
            "outros": []
        },
        "historico_sessoes": []
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
                    if "historico_sessoes" not in dados:
                        dados["historico_sessoes"] = []
                    return dados
        except json.JSONDecodeError:
            bak = path + ".bak"
            shutil.copy2(path, bak)
        except:
            pass
    return perfil_padrao(username)

def salvar_memoria(mem, username):
    os.makedirs(LEARNS_DIR, exist_ok=True)
    with open(caminho_learn(username), "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

# ─── HISTÓRICO DE SESSÕES (oculto) ─────────────────────────────────────────────
def salvar_sessao(mem, username, historico_sessao):
    if not historico_sessao:
        return
    sessao = {
        "data": str(datetime.date.today()),
        "hora": datetime.datetime.now().strftime("%H:%M"),
        "mensagens": historico_sessao
    }
    mem["historico_sessoes"].append(sessao)
    salvar_memoria(mem, username)

# ─── LOGIN ─────────────────────────────────────────────────────────────────────
def pedir_input(prompt):
    print(f"{Cor.AZUL}{Cor.BOLD}  {prompt}{Cor.RESET}", end="")
    try:
        return input().strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)

def pedir_senha(prompt="Senha: "):
    import getpass
    try:
        return getpass.getpass(f"{Cor.AZUL}{Cor.BOLD}  {prompt}{Cor.RESET}")
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)

def login():
    users = carregar_users()

    session = carregar_session()
    if session:
        username = session.get("username")
        token    = session.get("token")
        if username in users and users[username].get("token") == token:
            return username, carregar_memoria(username), users
        else:
            limpar_session()

    username = pedir_input("User: ").lower().replace(" ", "_")
    if not username:
        return login()

    if username in users:
        for tentativa in range(3):
            senha = pedir_senha("Senha: ")
            if hash_senha(senha) == users[username]["senha"]:
                token = gerar_token()
                users[username]["token"] = token
                salvar_users(users)
                salvar_session(username, token)
                print(f"{Cor.VERDE}  ✓ Bem-vindo de volta!{Cor.RESET}\n")
                return username, carregar_memoria(username), users
            else:
                restam = 2 - tentativa
                if restam > 0:
                    print(f"{Cor.AMARELO}  Senha errada. {restam} tentativa(s) restante(s).{Cor.RESET}")
                else:
                    print(f"{Cor.AMARELO}  Muitas tentativas.{Cor.RESET}\n")
                    sys.exit(0)
    else:
        print(f"{Cor.AMARELO}  Usuário não encontrado. Deseja criar? (S/N): {Cor.RESET}", end="")
        try:
            resp = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)

        if resp not in ["s", "sim", "y", "yes"]:
            print(f"{Cor.CINZA}  Ok, até mais!{Cor.RESET}\n")
            sys.exit(0)

        senha = pedir_senha("Crie uma senha: ")
        if not senha:
            print(f"{Cor.AMARELO}  Senha não pode ser vazia.{Cor.RESET}\n")
            sys.exit(0)

        confirma = pedir_senha("Confirme a senha: ")
        if senha != confirma:
            print(f"{Cor.AMARELO}  Senhas não batem.{Cor.RESET}\n")
            sys.exit(0)

        token = gerar_token()
        users[username] = {
            "senha": hash_senha(senha),
            "token": token,
            "admin": False,
            "superadmin": False,
            "criado_em": str(datetime.date.today())
        }
        salvar_users(users)
        salvar_session(username, token)
        mem = perfil_padrao(username)
        salvar_memoria(mem, username)
        print(f"{Cor.VERDE}  ✓ Conta criada!{Cor.RESET}\n")
        return username, mem, users

# ─── ADMIN ─────────────────────────────────────────────────────────────────────
def verificar_token_admin():
    token_env = os.environ.get("EVA_ADMIN_TOKEN", "")
    if not token_env:
        print(f"{Cor.VERMELHO}  Token admin não configurado.{Cor.RESET}\n")
        return False
    import getpass
    try:
        token_digitado = getpass.getpass(f"{Cor.AMARELO}  Token admin: {Cor.RESET}")
    except (KeyboardInterrupt, EOFError):
        return False
    if token_digitado == token_env:
        print(f"{Cor.VERDE}  ✓ Token válido!{Cor.RESET}\n")
        return True
    print(f"{Cor.VERMELHO}  Token inválido.{Cor.RESET}\n")
    return False

def menu_admin(username, users):
    superadmin = is_superadmin(username, users)
    print(f"\n{Cor.VERMELHO}{Cor.BOLD}  ── MENU ADMIN ──{Cor.RESET}")
    print(f"{Cor.CINZA}  1. Listar usuários")
    if superadmin:
        print(f"  2. Ver perfil de um usuário")
        print(f"  3. Ver histórico de um usuário")
    print(f"  4. Ensinar algo sobre um usuário")
    print(f"  5. Apagar campo do perfil de um usuário")
    print(f"  6. Resetar perfil de um usuário")
    if superadmin:
        print(f"  7. Promover usuário a admin")
    print(f"  0. Sair do menu admin{Cor.RESET}\n")

    opcao = pedir_input("Opção: ")

    if opcao == "1":
        print(f"\n{Cor.AMARELO}  Usuários cadastrados:{Cor.RESET}")
        for u, dados in users.items():
            tags = []
            if dados.get("superadmin"): tags.append(f"{Cor.VERMELHO}superadmin{Cor.RESET}")
            elif dados.get("admin"):    tags.append(f"{Cor.AMARELO}admin{Cor.RESET}")
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            print(f"  • {u}{tag_str} — desde {dados.get('criado_em','?')}")
        print()

    elif opcao == "2":
        if not superadmin:
            print(f"{Cor.VERMELHO}  Sem permissão.{Cor.RESET}\n")
            return
        user_alvo = pedir_input("Username: ").lower()
        mem = carregar_memoria(user_alvo)
        print(f"\n{Cor.AMARELO}  Perfil de {user_alvo}:{Cor.RESET}")
        print(json.dumps(mem.get("perfil", {}), ensure_ascii=False, indent=4))
        print()

    elif opcao == "3":
        if not superadmin:
            print(f"{Cor.VERMELHO}  Sem permissão.{Cor.RESET}\n")
            return
        user_alvo = pedir_input("Username: ").lower()
        mem = carregar_memoria(user_alvo)
        sessoes = mem.get("historico_sessoes", [])
        if not sessoes:
            print(f"{Cor.CINZA}  Sem histórico ainda.{Cor.RESET}\n")
            return
        print(f"\n{Cor.AMARELO}  Histórico de {user_alvo} ({len(sessoes)} sessões):{Cor.RESET}\n")
        for sessao in sessoes[-5:]:
            print(f"{Cor.AZUL}{Cor.BOLD}  ── {sessao.get('data','?')} às {sessao.get('hora','?')} ──{Cor.RESET}")
            for msg in sessao.get("mensagens", []):
                if msg["role"] == "user":
                    print(f"  {Cor.VERDE}User:{Cor.RESET} {msg['content']}")
                else:
                    print(f"  {Cor.ROSA}Eva:{Cor.RESET}  {msg['content']}")
            print()

    elif opcao == "4":
        user_alvo = pedir_input("Username: ").lower()
        campo = pedir_input("Campo (gostos/nao_gosta/interesses/outros/nome/aniversario): ").lower()
        valor = pedir_input("Valor: ")
        mem = carregar_memoria(user_alvo)
        perfil = mem.get("perfil", {})
        if campo in ["gostos", "nao_gosta", "problemas_relatados", "interesses", "outros"]:
            if campo not in perfil: perfil[campo] = []
            if valor not in perfil[campo]:
                perfil[campo].append(valor)
                salvar_memoria(mem, user_alvo)
                print(f"{Cor.VERDE}  ✓ Salvo!{Cor.RESET}\n")
            else:
                print(f"{Cor.CINZA}  Já existe.{Cor.RESET}\n")
        elif campo in ["nome", "aniversario", "humor_frequente"]:
            perfil[campo] = valor
            salvar_memoria(mem, user_alvo)
            print(f"{Cor.VERDE}  ✓ Atualizado!{Cor.RESET}\n")
        else:
            print(f"{Cor.AMARELO}  Campo inválido.{Cor.RESET}\n")

    elif opcao == "5":
        user_alvo = pedir_input("Username: ").lower()
        campo = pedir_input("Campo: ").lower()
        mem = carregar_memoria(user_alvo)
        perfil = mem.get("perfil", {})
        if campo in ["gostos", "nao_gosta", "problemas_relatados", "interesses", "outros"]:
            perfil[campo] = []
            salvar_memoria(mem, user_alvo)
            print(f"{Cor.VERDE}  ✓ Limpo!{Cor.RESET}\n")
        elif campo in ["nome", "aniversario", "humor_frequente"]:
            perfil[campo] = None
            salvar_memoria(mem, user_alvo)
            print(f"{Cor.VERDE}  ✓ Apagado!{Cor.RESET}\n")
        else:
            print(f"{Cor.AMARELO}  Campo inválido.{Cor.RESET}\n")

    elif opcao == "6":
        user_alvo = pedir_input("Username: ").lower()
        confirma = pedir_input(f"Resetar TUDO de {user_alvo}? (sim/não): ").lower()
        if confirma in ["sim", "s"]:
            mem = carregar_memoria(user_alvo)
            mem["perfil"] = perfil_padrao(user_alvo)["perfil"]
            salvar_memoria(mem, user_alvo)
            print(f"{Cor.VERDE}  ✓ Resetado!{Cor.RESET}\n")
        else:
            print(f"{Cor.CINZA}  Cancelado.{Cor.RESET}\n")

    elif opcao == "7":
        if not superadmin:
            print(f"{Cor.VERMELHO}  Sem permissão.{Cor.RESET}\n")
            return
        user_alvo = pedir_input("Username: ").lower()
        if user_alvo in users:
            users[user_alvo]["admin"] = True
            salvar_users(users)
            print(f"{Cor.VERDE}  ✓ {user_alvo} agora é admin!{Cor.RESET}\n")
        else:
            print(f"{Cor.AMARELO}  Usuário não encontrado.{Cor.RESET}\n")

    elif opcao == "0":
        return
    else:
        print(f"{Cor.CINZA}  Opção inválida.{Cor.RESET}\n")

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
        ["llama-server", "-m", MODEL_PATH, "--host", "127.0.0.1",
         "--port", "8080", "--ctx-size", "2048", "-ngl", "0", "--log-disable"],
        stdout=devnull, stderr=devnull
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
    if perfil.get("nome"):        partes.append(f"nome: {perfil['nome']}")
    if perfil.get("gostos"):      partes.append(f"gosta de: {', '.join(perfil['gostos'][-5:])}")
    if perfil.get("nao_gosta"):   partes.append(f"não gosta de: {', '.join(perfil['nao_gosta'][-5:])}")
    if perfil.get("humor_frequente"): partes.append(f"humor: {perfil['humor_frequente']}")
    if perfil.get("problemas_relatados"): partes.append(f"já relatou: {', '.join(perfil['problemas_relatados'][-3:])}")
    if perfil.get("aniversario"): partes.append(f"aniversário: {perfil['aniversario']}")
    if perfil.get("interesses"):  partes.append(f"interesses: {', '.join(perfil['interesses'][-5:])}")
    if perfil.get("outros"):      partes.append(f"outros: {', '.join(perfil['outros'][-5:])}")
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
        return "Eita, perdi a conexão kk. Tenta de novo?"
    except Exception:
        limpar_status()
        return "Hmm, travei aqui... fala de novo?"

# ─── APRENDIZADO ───────────────────────────────────────────────────────────────
_RE_NOME = re.compile(r"(?:meu nome é|me chamo|pode me chamar de|sou o|sou a)\s+([a-záàãâéêíóôõúüç]+)", re.IGNORECASE)
_RE_GOSTO = re.compile(r"(?:gosto de|adoro|amo|curto|meu hobby é|minha paixão é)\s+(.+?)(?=\s*(?:e não|mas não|,?\s*não gosto)|$)", re.IGNORECASE)
_RE_NAO_GOSTO = re.compile(r"(?:não gosto de|odeio|detesto|não curto|não suporto)\s+(.+?)(?=\s*(?:e gosto|mas gosto)|$)", re.IGNORECASE)
_RE_PROBLEMA = re.compile(r"(?:tô|estou|me sinto)\s+(mal|triste|ansioso|ansiosa|sozinho|sozinha|deprimido|deprimida|cansado|cansada|com medo|estressado|estressada)", re.IGNORECASE)
_RE_HUMOR_BOM = re.compile(r"(?:tô|estou|me sinto)\s+(bem|feliz|ótimo|ótima|animado|animada)", re.IGNORECASE)
_RE_ANIVERSARIO = re.compile(r"(?:meu aniversário é|faço aniversário|nasci em|nasci no dia)\s+(.+?)(?:\s*[,.]|$)", re.IGNORECASE)
_RE_OUTROS = re.compile(r"(?:tenho\s+\d+\s+anos|moro em|trabalho\s+(?:em|como|na|no)|estudo\s+(?:em|na|no)|sou\s+\w+)", re.IGNORECASE)

def classificar_e_salvar(msg, perfil):
    atualizado = False
    m = _RE_NOME.search(msg)
    if m:
        perfil["nome"] = m.group(1).capitalize()
        atualizado = True
    m = _RE_GOSTO.search(msg)
    if m:
        for item in re.split(r",\s*|\s+e\s+", m.group(1).strip().rstrip(".,!")):
            item = item.strip().rstrip(".,!")
            if item and item.lower() not in [g.lower() for g in perfil["gostos"]]:
                perfil["gostos"].append(item)
        atualizado = True
    m = _RE_NAO_GOSTO.search(msg)
    if m:
        for item in re.split(r",\s*|\s+e\s+", m.group(1).strip().rstrip(".,!")):
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
    if not atualizado:  # bug corrigido: era "not updated"
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

def extrair_interesse_com_ia(msg, perfil):
    """Usa o modelo pra detectar interesses automaticamente — silencioso"""
    payload = json.dumps({
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um extrator de interesses. Analise o que o usuário disse e identifique se ele demonstrou "
                    "um interesse claro, hobby ou curiosidade sobre algum tema. "
                    "Responda APENAS com o nome do interesse limpo (ex: 'Culinária', 'Música', 'Programação'). "
                    "Se não revelar nenhum interesse útil, responda estritamente 'NADA'."
                )
            },
            {"role": "user", "content": f"Frase: '{msg}'"}
        ],
        "temperature": 0.1,
        "n_predict": 20,
        "stream": False
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{SERVER_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
            resultado = dados["choices"][0]["message"]["content"].strip().replace("'","").replace('"','')
            if resultado and resultado.upper() != "NADA" and len(resultado) < 40:
                if "interesses" not in perfil:
                    perfil["interesses"] = []
                if resultado not in perfil["interesses"]:
                    perfil["interesses"].append(resultado)
                    return True
    except:
        pass
    return False

def perguntar_aprender(msg, memoria, username):
    print(f"\n{Cor.AMARELO}  💡 Eva quer aprender:{Cor.RESET}")
    print(f"  \"{msg}\"")
    r = voce_fala("  Salva isso? (S/N): ").lower()
    if r in ["s", "sim", "y", "yes"]:
        if classificar_e_salvar(msg, memoria["perfil"]):
            salvar_memoria(memoria, username)
            print(f"{Cor.VERDE}  ✓ Anotado!{Cor.RESET}\n")
        else:
            print(f"{Cor.CINZA}  Não consegui classificar.{Cor.RESET}\n")

# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    limpar()
    cabecalho()

    if "127.0.0.1" in SERVER_URL and not os.path.exists(MODEL_PATH):
        print(f"{Cor.AMARELO}  Modelo não encontrado:{Cor.RESET} {MODEL_PATH}")
        sys.exit(1)

    if "127.0.0.1" in SERVER_URL and subprocess.run(["which", "llama-server"], capture_output=True).returncode != 0:
        print(f"{Cor.AMARELO}  llama-server não encontrado.{Cor.RESET}")
        print("  pkg install llama-cpp\n")
        sys.exit(1)

    if not iniciar_servidor():
        sys.exit(1)

    username, memoria, users = login()
    historico_sessao = []  # sessão atual — salva no JSON ao sair
    admin_ativo = False

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

    # Comandos visíveis — mínimo pro usuário
    cmds = "  /sair · /limpar · /esquecer · /sair-conta"
    if is_admin(username, users):
        cmds += " · /admin"
    print(f"{Cor.CINZA}{cmds}{Cor.RESET}\n")

    try:
        while True:
            entrada = voce_fala("Você: ")

            if not entrada:
                continue

            if entrada.lower() in ["/sair", "/exit", "tchau", "sair"]:
                eva_fala(random.choice(DESPEDIDAS))
                salvar_sessao(memoria, username, historico_sessao)
                break

            if entrada.lower() == "/sair-conta":
                limpar_session()
                eva_fala("Sessão encerrada! Na próxima vai pedir senha 🔒")
                salvar_sessao(memoria, username, historico_sessao)
                break

            if entrada.lower() == "/limpar":
                salvar_sessao(memoria, username, historico_sessao)
                historico_sessao = []
                limpar()
                cabecalho()
                eva_fala("Pronto! Sobre o que você quer conversar?")
                continue

            if entrada.lower() == "/esquecer":
                memoria["perfil"] = perfil_padrao(username)["perfil"]
                salvar_memoria(memoria, username)
                eva_fala("Esqueci tudo sobre você. Vamos começar do zero 🙂")
                continue

            if entrada.lower() == "/admin":
                if not is_admin(username, users):
                    eva_fala("Esse comando não existe 👀")
                    continue
                if not admin_ativo:
                    if verificar_token_admin():
                        admin_ativo = True
                    else:
                        continue
                users = carregar_users()
                menu_admin(username, users)
                continue

            historico_sessao.append({"role": "user", "content": entrada})
            contexto = montar_contexto(memoria.get("perfil", {}))
            resposta = chamar_modelo(historico_sessao, contexto)
            historico_sessao.append({"role": "assistant", "content": resposta})
            eva_fala(resposta)

            if detectar_aprendizado(entrada):
                perguntar_aprender(entrada, memoria, username)
            else:
                if extrair_interesse_com_ia(entrada, memoria["perfil"]):
                    salvar_memoria(memoria, username)

            if len(historico_sessao) > MAX_HISTORY * 2:
                historico_sessao = historico_sessao[-MAX_HISTORY:]

    finally:
        parar_servidor()

if __name__ == "__main__":
    main()
