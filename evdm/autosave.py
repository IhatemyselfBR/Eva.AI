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

print("Salvando no GitHub...")

PASTA = "/data/data/com.termux/files/home/eva"
os.chdir(PASTA)

os.system("git add .")
os.system('git commit -m "AutoSave EVA"')
os.system("git push origin main")

print("Backup enviado.")
