import json, os, others, weight, random, re

try:
    import readline
    hist_path = os.path.expanduser("~/.eva_history")
    if os.path.exists(hist_path): readline.read_history_file(hist_path)
except: pass

class EvaCoreTeste:
    def __init__(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        self.mem_path = 'learning.json'
        self.human_path = 'learninghumans.json'
        self.words_path = 'words.txt'
        self.memoria = self.carregar(self.mem_path)
        self.memoria_humana = self.carregar(self.human_path)
        self.last_key = None
        self.modo_ensino = False
        print(f"Memória técnica: {len(self.memoria)} termos")
        print(f"Memória humana: {len(self.memoria_humana)} entradas")

    def carregar(self, path):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
                except: return {}
        return {}

    def salvar(self):
        with open(self.mem_path, 'w', encoding='utf-8') as f:
            json.dump(self.memoria, f, indent=4, ensure_ascii=False)
        try:
            import readline
            readline.write_history_file(os.path.expanduser("~/.eva_history"))
        except: pass

    def obter_social(self, tag):
        frases = []
        if os.path.exists(self.words_path):
            with open(self.words_path, 'r', encoding='utf-8') as f:
                cap = False
                for l in f:
                    l = l.strip()
                    if l == f"[{tag}]": cap = True; continue
                    if l.startswith("[") and cap: break
                    if cap and l: frases.append(l)
        return random.choice(frases) if frases else None

    def buscar_humano(self, user):
        """Busca na memória humana por similaridade de palavras"""
        user_words = set(re.sub(r'[?!.,]', '', user.lower()).split())
        melhor_score = 0
        melhor_resposta = None

        for chave, dado in self.memoria_humana.items():
            pergunta = dado.get('pergunta', '').lower()
            pergunta_words = set(re.sub(r'[?!.,]', '', pergunta).split())

            # Conta palavras em comum
            comum = len(user_words & pergunta_words)
            if comum > melhor_score and comum >= 2:
                melhor_score = comum
                melhor_resposta = dado

        return melhor_resposta

    def escutar(self):
        print("\033[96m" + "="*40 + "\n  EVA TESTE - MEMÓRIA HUMANA ATIVA\n" + "="*40 + "\033[0m")
        while True:
            try:
                user = input("\033[92mVocê:\033[0m ").strip()
                if not user: continue
                u_low = user.lower()

                # --- 1. MODO ENSINO ---
                if self.modo_ensino:
                    if u_low == 'cancelar':
                        self.modo_ensino = False
                        print("Eva: Aula cancelada.")
                    elif self.last_key:
                        self.memoria[self.last_key] = {"texto": user, "peso": 10}
                        self.salvar()
                        self.modo_ensino = False
                        print("Eva: Entendido!")
                    else:
                        self.modo_ensino = False
                        print("Eva: Erro interno no modo ensino. Tente novamente.")
                    continue

                # --- 2. COMANDOS DE SISTEMA ---
                if u_low == '$ensinar':
                    if not self.last_key:
                        print("Eva: Pergunte algo primeiro para eu saber o que ensinar.")
                    else:
                        self.modo_ensino = True
                        print(f"Eva: O que é '{self.last_key}'?")
                    continue

                if u_low == '$ng' and self.last_key:
                    suc, msg, critico = weight.ajustar_peso(self.memoria, self.last_key, -2)
                    self.salvar()
                    print(f"\033[91mSystem: {msg}\033[0m")
                    if critico:
                        res = others.roteador(self.last_key)
                        if res:
                            self.memoria[self.last_key] = {"texto": res, "peso": 1}
                            self.salvar()
                            print(f"\033[94mEva (Novo):\033[0m {res}")
                    continue

                if u_low == '$p' and self.last_key:
                    suc, msg, _ = weight.ajustar_peso(self.memoria, self.last_key, 6)
                    self.salvar()
                    print(f"\033[92mSystem: {msg}\033[0m")
                    continue

                if u_low == '$g' and self.last_key:
                    suc, msg, _ = weight.ajustar_peso(self.memoria, self.last_key, 2)
                    self.salvar()
                    print(f"\033[93mSystem: {msg}\033[0m")
                    continue


# --- 3. DETECÇÃO SOCIAL ---
tipo_social = others.detectar_social(user)
if tipo_social == 'saudacao':
    frase = others.obter_frase(self.words_path, 'SAUDACOES')
    print(f"\033[94mEva:\033[0m {frase or 'Oi!'}")
    continue
if tipo_social == 'despedida':
    frase = others.obter_frase(self.words_path, 'DESPEDIDAS')
    print(f"\033[94mEva:\033[0m {frase or 'Tchau!'}")
    continue
if tipo_social == 'como_vai':
    print(f"\033[94mEva:\033[0m Tô por aqui! Em que posso ajudar?")
    continue
if tipo_social == 'incompreensao':
    frase = others.obter_frase(self.words_path, 'INCOMPREENSAO')
    print(f"\033[94mEva:\033[0m {frase or 'Não entendi, pode repetir?'}")
    continue

                # --- 3. PROCESSAMENTO DE DIÁLOGO ---
                alvo = others.extrair_alvo(user)
                if not alvo: alvo = user
                intencao = others.identificar_intencao(user)
                chave = f"{alvo}__{intencao}" if intencao != 'definicao' else alvo

                if u_low not in ['$g', '$p', '$ng']:
                    self.last_key = chave

                # Primeiro tenta memória técnica
                if weight.validar_memoria(self.memoria, self.last_key):
                    m = self.memoria[self.last_key]
                    print(f"\033[94mEva (Memória [R:{m['peso']}]):\033[0m {m['texto']}")

                else:
                    # Tenta memória humana
                    humano = self.buscar_humano(user)
                    if humano:
                        print(f"\033[93mEva (Humano):\033[0m {humano['resposta']}")
                        print(f"\033[90m[contexto: r/{humano['subreddit']}]\033[0m")

                    else:
                        # Busca na web
                        print(f"\033[90mEva: Analisando '{alvo}' (Tipo: {intencao})...\033[0m")
                        res = others.roteador(user)
                        if res:
                            self.memoria[self.last_key] = {"texto": res, "peso": 1}
                            self.salvar()
                            print(f"\033[94mEva (Novo):\033[0m {res}")
                        else:
                            social = self.obter_social("ERRO_BUSCA")
                            print(f"\033[94mEva:\033[0m {social or 'Ainda não conheço isso.'}")

            except KeyboardInterrupt: break
            except Exception as e: print(f"Erro no Sistema: {e}")

if __name__ == "__main__":
    EvaCoreTeste().escutar()
