import json, os, others, weight, random, re

try:
    import readline
    hist_path = os.path.expanduser("~/.eva_history")
    if os.path.exists(hist_path): readline.read_history_file(hist_path)
except: pass


class EvaCore:

    def __init__(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        self.mem_path = 'learning.json'
        self.human_path = 'learninghumans.json'
        self.words_path = 'words.txt'
        self.memoria = self.carregar(self.mem_path)
        self.memoria_humana = self.carregar(self.human_path)
        self.last_key = None
        self.modo_ensino = False
        self.historico = []
        print(f"\033[90mMemória técnica: {len(self.memoria)} termos")
        print(f"Memória humana: {len(self.memoria_humana)} entradas\033[0m")

    # ==========================
    # I/O
    # ==========================

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

    # ==========================
    # WORDS.TXT
    # ==========================

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

    def aprender_padrao(self, tag, frase):
        if not os.path.exists(self.words_path): return
        with open(self.words_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        if frase in conteudo: return
        tag_str = f"[{tag}]"
        if tag_str in conteudo:
            conteudo = conteudo.replace(tag_str, f"{tag_str}\n{frase}")
            with open(self.words_path, 'w', encoding='utf-8') as f:
                f.write(conteudo)

    # ==========================
    # TAGS
    # ==========================

    def limpar(self, txt):
        return re.sub(r'[^\w\s]', '', txt.lower())

    def gerar_tags(self, texto):
        return [p for p in self.limpar(texto).split() if len(p) > 3]

    # ==========================
    # BUSCAS
    # ==========================

    def buscar_semantico(self, pergunta):
        tags_pergunta = set(self.gerar_tags(pergunta))
        melhor_texto = None
        melhor_score = 0
        melhor_peso = 0
        for chave, dado in self.memoria.items():
            if not isinstance(dado, dict): continue
            if dado.get('peso', 0) <= 0: continue
            tags_mem = set(dado.get('tags', []))
            score = len(tags_pergunta & tags_mem)
            peso = dado.get('peso', 1)
            if score > melhor_score or (score == melhor_score and peso > melhor_peso):
                melhor_score = score
                melhor_peso = peso
                melhor_texto = dado.get('texto')
        return melhor_texto if melhor_score >= 2 else None

    def buscar_humano(self, pergunta):
        tags_pergunta = set(self.gerar_tags(pergunta))
        melhor = None
        melhor_score = 0
        for chave, dado in self.memoria_humana.items():
            tags_titulo = set(self.gerar_tags(dado.get('pergunta', '')))
            score = len(tags_pergunta & tags_titulo)
            if score > melhor_score and score >= 2:
                melhor_score = score
                melhor = dado
        return melhor

    # ==========================
    # FORMATAR
    # ==========================

    def formatar(self, texto, fonte='memoria'):
        if not texto: return None
        palavras = texto.split()
        if len(palavras) > 50:
            texto = ' '.join(palavras[:50]) + '...'
        prefixos = {
            'memoria': ["Sobre isso: ", "Deixa eu te falar: ", "Tenho isso aqui: ", "", "", ""],
            'humano':  ["Vi alguém falar: ", "Uma pessoa comentou: ", "Encontrei isso: ", "", ""],
            'novo':    ["Pesquisei aqui: ", "Achei isso: ", "Olha o que encontrei: ", "", ""]
        }
        return random.choice(prefixos.get(fonte, [""])) + texto

    # ==========================
    # LOOP PRINCIPAL
    # ==========================

    def escutar(self):
        print("\033[96m" + "="*40 + "\n  EVA - SISTEMAS DE INTELIGÊNCIA ATIVOS\n" + "="*40 + "\033[0m")

        while True:
            try:
                user = input("\033[92mVocê:\033[0m ").strip()
                if not user: continue
                u_low = user.lower()

                self.historico.append(user)
                if len(self.historico) > 5:
                    self.historico.pop(0)

                # ==========================
                # MODO ENSINO
                # ==========================

                if self.modo_ensino:
                    if u_low == 'cancelar':
                        self.modo_ensino = False
                        print("Eva: Tá, deixa pra lá então.")
                    elif self.last_key:
                        tags = self.gerar_tags(f"{self.last_key} {user}")
                        self.memoria[self.last_key] = {
                            "texto": user, "peso": 10, "tags": tags
                        }
                        self.salvar()
                        self.modo_ensino = False
                        print(f"Eva: {random.choice(['Anotei! Valeu por me ensinar.', 'Entendido! Vou lembrar disso.', 'Boa, aprendi mais uma!', 'Guardei aqui, obrigada!'])}")
                    else:
                        self.modo_ensino = False
                        print("Eva: Deu ruim aqui, tenta de novo.")
                    continue

                # ==========================
                # COMANDOS
                # ==========================

                if u_low == '$ensinar':
                    if not self.last_key:
                        print("Eva: Me pergunta algo primeiro.")
                    else:
                        self.modo_ensino = True
                        print(f"Eva: Me conta então, o que é '{self.last_key}'?")
                    continue

                if u_low == '$r' and self.last_key:
                    if self.last_key in self.memoria:
                        del self.memoria[self.last_key]
                        self.salvar()
                        print(f"\033[91mSystem: '{self.last_key}' removido da memória.\033[0m")
                    else:
                        print(f"\033[91mSystem: Não encontrei '{self.last_key}' na memória.\033[0m")
                    continue

                if u_low == '$ng' and self.last_key:
                    suc, msg, critico = weight.ajustar_peso(self.memoria, self.last_key, -2)
                    self.salvar()
                    print(f"\033[91mSystem: {msg}\033[0m")
                    if critico:
                        res = others.roteador(self.last_key)
                        if res:
                            tags = self.gerar_tags(f"{self.last_key} {res}")
                            self.memoria[self.last_key] = {"texto": res, "peso": 1, "tags": tags}
                            self.salvar()
                            print(f"Eva: {self.formatar(res, 'novo')}")
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

                # ==========================
                # DETECÇÃO SOCIAL
                # ==========================

                tipo_social = others.detectar_social(u_low)

                if tipo_social == 'saudacao':
                    resp = self.obter_social('SAUDACOES') or 'Oi!'
                    print(f"Eva: {resp}")
                    self.aprender_padrao('SAUDACOES', resp)
                    continue

                if tipo_social == 'despedida':
                    print(f"Eva: {self.obter_social('DESPEDIDAS') or 'Tchau!'}")
                    continue

                if tipo_social == 'como_vai':
                    print(f"Eva: {self.obter_social('COMO_VAI') or 'Tô de boa! E você?'}")
                    continue

                if tipo_social == 'giria':
                    print(f"Eva: {self.obter_social('RESPOSTAS_GIRIAS') or 'Kkk!'}")
                    self.aprender_padrao('GIRIAS', u_low)
                    continue

                if tipo_social == 'incompreensao':
                    print(f"Eva: {self.obter_social('INCOMPREENSAO') or 'Não entendi, pode repetir?'}")
                    continue

                # ==========================
                # PROCESSAMENTO
                # ==========================

                alvo = others.extrair_alvo(user)
                if not alvo: alvo = user
                intencao = others.identificar_intencao(user)
                chave = f"{alvo}__{intencao}" if intencao != 'definicao' else alvo

                if u_low not in ['$g', '$p', '$ng', '$r']:
                    self.last_key = chave

                # 1. Memória exata
                if weight.validar_memoria(self.memoria, self.last_key):
                    m = self.memoria[self.last_key]
                    print(f"Eva: {self.formatar(m['texto'], 'memoria')}")

                # 2. Semântica por tags
                else:
                    semantico = self.buscar_semantico(user)
                    if semantico:
                        print(f"Eva: {self.formatar(semantico, 'memoria')}")

                    # 3. Memória humana
                    else:
                        humano = self.buscar_humano(user)
                        if humano:
                            print(f"Eva: {self.formatar(humano['resposta'], 'humano')}")

                        # 4. Web
                        else:
                            print(f"\033[90mEva: {random.choice(['Deixa eu pesquisar...', 'Um segundo...', 'Hmm, vou ver...', 'Procurando...'])}\033[0m")
                            res = others.roteador(user)
                            if res:
                                tags = self.gerar_tags(f"{alvo} {res}")
                                self.memoria[self.last_key] = {
                                    "texto": res, "peso": 1, "tags": tags
                                }
                                self.salvar()
                                print(f"Eva: {self.formatar(res, 'novo')}")
                            else:
                                print(f"Eva: {self.obter_social('ERRO_BUSCA') or 'Não achei nada sobre isso.'}")

            except KeyboardInterrupt: break
            except Exception as e: print(f"Erro: {e}")


if __name__ == "__main__":
    EvaCore().escutar()
