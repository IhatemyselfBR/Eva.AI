import requests
import json
import os
from datetime import datetime

API_KEY = "AIzaSyC9ZQhXYtPfKdDOhN0vY325TBgrGo2kZko"

MEM_PATH = "learning.json"


def carregar():
    if os.path.exists(MEM_PATH):
        with open(MEM_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}


def salvar(mem):
    with open(MEM_PATH, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=4, ensure_ascii=False)


def perguntar(pergunta):

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": pergunta
                    }
                ]
            }
        ]
    }

    try:
        r = requests.post(url, json=payload, timeout=20)

        data = r.json()

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print("Erro:", e)
        return None


def aprender(chave, pergunta):

    memoria = carregar()

    if chave in memoria:
        return memoria[chave]["texto"]

    resposta = perguntar(pergunta)

    if resposta:

        memoria[chave] = {
            "texto": resposta,
            "peso": 2,
            "fonte": "gemini",
            "data": str(datetime.now())
        }

        salvar(memoria)

    return resposta


while True:

    user = input("Você: ")

    if user.lower() == "sair":
        break

    r = aprender(user.lower(), user)

    print("Eva:", r)
