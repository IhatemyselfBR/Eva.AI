import json
import copy
import random

# ===== CARREGAR MEMÓRIA =====
with open("learning.json", "r", encoding="utf-8") as f:
    memoria_real = json.load(f)

# ===== CÓPIA TEMPORÁRIA =====
memoria_teste = copy.deepcopy(memoria_real)

print("===================================")
print("        EVA - TEST MODE")
print("===================================")
print("Nada será salvo.\n")

while True:
    user = input("Você: ").lower().strip()

    if user in ["sair", "exit"]:
        print("Encerrando teste...")
        break

    resposta = None

    # ===== RESPOSTA EXATA =====
    if user in memoria_teste:

        dados = memoria_teste[user]

        # Caso seja lista de respostas
        if isinstance(dados, list):
            dados = random.choice(dados)

        # Caso seja dict
        if isinstance(dados, dict):
            resposta = dados.get("texto")

        # Caso seja string
        elif isinstance(dados, str):
            resposta = dados

    # ===== BUSCA POR PALAVRAS =====
    if not resposta:

        melhores = []

        for chave, dados in memoria_teste.items():

            if isinstance(dados, dict):

                tags = dados.get("tags", [])

                for palavra in user.split():

                    if palavra in tags:
                        melhores.append(dados)

        if melhores:
            escolhido = random.choice(melhores)
            resposta = escolhido.get("texto")

    # ===== FALLBACK =====
    if not resposta:
        resposta = "Ainda não sei responder isso."

    print("Eva:", resposta)
