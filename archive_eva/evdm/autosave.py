import os
import getpass

# Senha vem da variável de ambiente, nunca hardcoded
SENHA = os.environ.get("EVA_SAVE_PASS", "")

if not SENHA:
    print("Erro: variável EVA_SAVE_PASS não configurada.")
    print("Roda: export EVA_SAVE_PASS='sua_senha'")
    exit()

senha = getpass.getpass("Senha: ")

if senha != SENHA:
    print("Senha incorreta.")
    exit()

# ─── Sobe o código (repo público) ──────────────────────────────────────────────
print("\nSalvando código...")
os.chdir("/data/data/com.termux/files/home/eva")
os.system("git add .")
os.system('git commit -m "AutoSave EVA"')
os.system("git push origin main")

# ─── Sobe o banco de dados (repo privado) ──────────────────────────────────────
print("\nSalvando banco de dados...")
os.chdir("/data/data/com.termux/files/home/eva-db")
os.system("git add .")
os.system('git commit -m "AutoSave DB"')
os.system("git push origin main")

print("\nTudo salvo!")
