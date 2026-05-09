import requests
import json
import os
import time
import random
from datetime import datetime

output_path = 'learninghumans.json'

subreddits = [
    "brasil",
    "desabafos",
    "relacionamentos",
    "financaspessoais",
    "psicologia",
    "saudementalBR",
    "TrabalhosBR"
]

def carregar():
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def salvar(dados):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def log(msg):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {msg}")

def buscar_posts(subreddit):
    headers = {
        'User-Agent': 'EVA-Bot/1.0 (educational project)'
    }
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=25&t=month"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        log(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            return data['data']['children']  # CORRIGIDO
        return []
    except Exception as e:
        log(f"   Erro: {e}")
        return []

def buscar_comentarios(subreddit, post_id):
    headers = {
        'User-Agent': 'EVA-Bot/1.0 (educational project)'
    }
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit=10"
    comentarios = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if len(data) > 1:
                for comment in data[1]['data']['children']:
                    body = comment['data'].get('body', '')
                    score = comment['data'].get('score', 0)
                    if body and score > 5 and len(body) > 30 and len(body) < 500:
                        if body not in ['[deleted]', '[removed]']:
                            comentarios.append({
                                "texto": body,
                                "score": score
                            })
    except:
        pass
    return comentarios

def coletar():
    dados = carregar()
    total = 0

    log(f"🧠 Iniciando coleta humana — {len(dados)} entradas já salvas")
    log("Ctrl+C para parar\n")

    while True:
        for subreddit in subreddits:
            log(f"📡 Coletando r/{subreddit}...")
            posts = buscar_posts(subreddit)

            if not posts:
                log(f"❌ r/{subreddit} — sem posts")
                continue

            for post in posts:
                try:
                    post_data = post['data']  # CORRIGIDO
                    post_id = post_data['id']
                    titulo = post_data['title']
                    texto_post = post_data.get('selftext', '')

                    if len(titulo) < 10:
                        continue

                    chave = f"reddit_{post_id}"
                    if chave in dados:
                        continue

                    comentarios = buscar_comentarios(subreddit, post_id)

                    if comentarios:
                        melhor = sorted(comentarios, key=lambda x: x['score'], reverse=True)[0]
                        dados[chave] = {
                            "pergunta": titulo,
                            "contexto": texto_post[:300] if texto_post else "",
                            "resposta": melhor['texto'],
                            "score": melhor['score'],
                            "subreddit": subreddit
                        }
                        salvar(dados)
                        total += 1
                        log(f"✅ [{total}] '{titulo[:50]}'")

                    time.sleep(random.uniform(2, 3))

                except Exception as e:
                    log(f"❌ Erro: {e}")
                    continue

            log(f"✅ r/{subreddit} concluído")
            time.sleep(5)

        log("🔄 Rodada completa, reiniciando...")
        time.sleep(30)

if __name__ == "__main__":
    try:
        coletar()
    except KeyboardInterrupt:
        print(f"\n\n⏹  Coleta pausada. {output_path} salvo!")
