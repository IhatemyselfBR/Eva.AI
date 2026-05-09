import json
import os
import random
import re

import others
import weight

try:
    import readline

    hist_path = os.path.expanduser("~/.eva_history")

    if os.path.exists(hist_path):
        readline.read_history_file(hist_path)

except:
    pass


class EvaCore:

    def __init__(self):

        os.system(
            'clear'
            if os.name == 'posix'
            else 'cls'
        )

        self.mem_path = 'learning.json'

        self.words_path = 'words.txt'

        self.memoria = self.carregar()

        self.last_key = None

        self.modo_ensino = False

    # =========================
    # LOAD
    # =========================

    def carregar(self):

        if os.path.exists(self.mem_path):

            with open(
                self.mem_path,
                'r',
                encoding='utf-8'
            ) as f:

                try:

                    data = json.load(f)

                    return (
                        data
                        if isinstance(data, dict)
                        else {}
                    )

                except:

                    return {}

        return {}

    # =========================
    # SAVE
    # =========================

    def salvar(self):

        with open(
            self.mem_path,
            'w',
            encoding='utf-8'
        ) as f:

            json.dump(
                self.memoria,
                f,
                indent=4,
                ensure_ascii=False
            )

        try:

            import readline

            readline.write_history_file(
                os.path.expanduser(
                    "~/.eva_history"
                )
            )

        except:
            pass

    # =========================
    # SOCIAL
    # =========================

    def obter_social(self, tag):

        frases = []

        if os.path.exists(self.words_path):

            with open(
                self.words_path,
                'r',
                encoding='utf-8'
            ) as f:

                cap = False

                for l in f:

                    l = l.strip()

                    if l == f"[{tag}]":

                        cap = True

                        continue

                    if l.startswith("[") and cap:
                        break

                    if cap and l:
                        frases.append(l)

        return (
            random.choice(frases)
            if frases
            else None
        )

    # =========================
    # LIMPEZA
    # =========================

    def limpar(self, txt):

        txt = txt.lower()

        txt = re.sub(
            r'[^\w\s]',
            '',
            txt
        )

        return txt

    # =========================
    # TAGS
    # =========================

    def gerar_tags(self, texto):

        texto = self.limpar(texto)

        return texto.split()

    # =========================
    # BUSCA SEMÂNTICA
    # =========================

    def buscar_semelhante(self, pergunta):

        tags_pergunta = self.gerar_tags(
            pergunta
        )

        melhor_texto = None

        maior_pontuacao = 0

        for chave, dado in self.memoria.items():

            if not isinstance(dado, dict):
                continue

            tags_memoria = dado.get(
                "tags",
                []
            )

            pontuacao = len(

                set(tags_pergunta)

                &

                set(tags_memoria)
            )

            if pontuacao > maior_pontuacao:

                maior_pontuacao = pontuacao

                melhor_texto = dado.get(
                    "texto"
                )

        if maior_pontuacao >= 1:

            return melhor_texto

        return None

    # =========================
    # LOOP PRINCIPAL
    # =========================

    def escutar(self):

        print(
            "\033[96m"
            + "="*40
            + "\n  EVA - SISTEMAS DE INTELIGÊNCIA ATIVOS\n"
            + "="*40
            + "\033[0m"
        )

        while True:

            try:

                user = input(
                    "\033[92mVocê:\033[0m "
                ).strip()

                if not user:
                    continue

                u_low = user.lower()

                # =========================
                # MODO ENSINO
                # =========================

                if self.modo_ensino:

                    if u_low == 'cancelar':

                        self.modo_ensino = False

                        print(
                            "Eva: Aula cancelada."
                        )

                    elif self.last_key:

                        texto_total = (
                            f"{self.last_key} {user}"
                        )

                        tags = self.gerar_tags(
                            texto_total
                        )

                        self.memoria[
                            self.last_key
                        ] = {

                            "texto": user,

                            "peso": 10,

                            "tags": tags
                        }

                        self.salvar()

                        self.modo_ensino = False

                        print(
                            "Eva: Entendido!"
                        )

                    else:

                        self.modo_ensino = False

                        print(
                            "Eva: Erro interno."
                        )

                    continue

                # =========================
                # COMANDOS
                # =========================

                if u_low == '$ensinar':

                    if not self.last_key:

                        print(
                            "Eva: Pergunte algo primeiro."
                        )

                    else:

                        self.modo_ensino = True

                        print(
                            f"Eva: O que é '{self.last_key}'?"
                        )

                    continue

                if u_low == '$ng' and self.last_key:

                    suc, msg, critico = (
                        weight.ajustar_peso(
                            self.memoria,
                            self.last_key,
                            -2
                        )
                    )

                    self.salvar()

                    print(
                        f"\033[91mSystem: {msg}\033[0m"
                    )

                    if critico:

                        res = others.roteador(
                            self.last_key
                        )

                        if res:

                            tags = self.gerar_tags(
                                f"{self.last_key} {res}"
                            )

                            self.memoria[
                                self.last_key
                            ] = {

                                "texto": res,

                                "peso": 1,

                                "tags": tags
                            }

                            self.salvar()

                            print(
                                f"\033[94mEva (Novo):\033[0m {res}"
                            )

                    continue

                if u_low == '$p' and self.last_key:

                    suc, msg, _ = (
                        weight.ajustar_peso(
                            self.memoria,
                            self.last_key,
                            6
                        )
                    )

                    self.salvar()

                    print(
                        f"\033[92mSystem: {msg}\033[0m"
                    )

                    continue

                if u_low == '$g' and self.last_key:

                    suc, msg, _ = (
                        weight.ajustar_peso(
                            self.memoria,
                            self.last_key,
                            2
                        )
                    )

                    self.salvar()

                    print(
                        f"\033[93mSystem: {msg}\033[0m"
                    )

                    continue

                # =========================
                # PROCESSAMENTO
                # =========================

                alvo = others.extrair_alvo(user)

                if not alvo:
                    alvo = user

                intencao = (
                    others.identificar_intencao(
                        user
                    )
                )

                chave = (

                    f"{alvo}__{intencao}"

                    if intencao != 'definicao'

                    else alvo
                )

                if u_low not in [
                    '$g',
                    '$p',
                    '$ng'
                ]:

                    self.last_key = chave

                # =========================
                # MEMÓRIA DIRETA
                # =========================

                if weight.validar_memoria(
                    self.memoria,
                    self.last_key
                ):

                    m = self.memoria[
                        self.last_key
                    ]

                    print(
                        f"\033[94mEva (Memória [R:{m['peso']}]):\033[0m {m['texto']}"
                    )

                else:

                    print(
                        f"\033[90mEva: Analisando '{alvo}' (Tipo: {intencao})...\033[0m"
                    )

                    # =========================
                    # BUSCA SEMÂNTICA
                    # =========================

                    semelhante = (
                        self.buscar_semelhante(
                            user
                        )
                    )

                    if semelhante:

                        print(
                            f"\033[95mEva (Semântica):\033[0m {semelhante}"
                        )

                        continue

                    # =========================
                    # BUSCA EXTERNA
                    # =========================

                    res = others.roteador(user)

                    if res:

                        tags = self.gerar_tags(
                            f"{user} {res}"
                        )

                        self.memoria[
                            self.last_key
                        ] = {

                            "texto": res,

                            "peso": 1,

                            "tags": tags
                        }

                        self.salvar()

                        print(
                            f"\033[94mEva (Novo):\033[0m {res}"
                        )

                    else:

                        social = self.obter_social(
                            "ERRO_BUSCA"
                        )

                        print(
                            f"\033[94mEva:\033[0m {social or 'Ainda não conheço isso.'}"
                        )

            except KeyboardInterrupt:

                break

            except Exception as e:

                print(
                    f"Erro no Sistema: {e}"
                )


if __name__ == "__main__":

    EvaCore().escutar()
