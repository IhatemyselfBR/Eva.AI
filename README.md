# 📱 Como instalar a Eva no seu celular

> Tutorial passo a passo pra instalar a Eva no Termux (Android)

---

## O que você vai precisar

- Celular Android
- Pelo menos 4GB de espaço livre
- Conexão com internet pra baixar os arquivos (depois roda offline)

---

## Passo 1 — Instala o Termux

O Termux é um terminal pra Android. É por ele que a Eva roda.

1. Acessa: **https://f-droid.org/packages/com.termux/**
2. Baixa e instala o Termux pelo F-Droid
3. Abre o Termux depois de instalar

> ⚠️ Não instala pelo Play Store, a versão de lá é antiga e quebrada.

---

## Passo 2 — Configura o Termux

Cola esses comandos um por um no Termux. Depois de cada um aperta **Enter** e espera terminar.

```
termux-change-repo
```
Vai abrir um menu. Usa as setas pra selecionar **South America** e confirma.

```
pkg update -y
```

```
pkg install python git wget llama-cpp -y
```

Esse último demora um pouco, normal.

---

## Passo 3 — Baixa a Eva

```
git clone https://github.com/IhatemyselfBR/Eva.AI.git ~/eva
```

---

## Passo 4 — Baixa o modelo de IA

Esse é o cérebro da Eva. Tem ~1.5GB então pode demorar dependendo da sua internet.

```
mkdir -p ~/eva/models
```

```
wget -O ~/eva/models/gemma-2-2b-it-Q4_K_M.gguf "https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf"
```

Espera terminar. Vai aparecer uma barrinha de progresso.

---

## Passo 5 — Roda a Eva

```
python ~/eva/eva.py
```

Na primeira vez demora uns 30 segundos enquanto ela inicializa. Depois fica rápido.

---

## Passo 6 — Cria sua conta

Quando aparecer **User:** digita um nome de usuário (sem espaço, sem acento).

Exemplo:
```
User: pedro
```

Ela vai perguntar se quer criar. Digita **S** e cria uma senha.

Pronto! A Eva vai te cumprimentar e vocês podem começar a conversar 😊

---

## Comandos dentro da conversa

| Comando | O que faz |
|---|---|
| `/sair` | Encerra a conversa |
| `/limpar` | Limpa o histórico da sessão atual |
| `/aprendi` | Mostra o que a Eva aprendeu sobre você |
| `/esquecer` | Apaga tudo que ela sabe sobre você |
| `/sair-conta` | Sai da conta (próxima vez pede senha) |

---

## Dicas

- Na segunda vez que abrir, ela já lembra quem você é e entra direto sem pedir senha
- Quanto mais você conversar, mais ela aprende sobre você
- Se ela pedir pra salvar algo que você falou, digita **S** pra confirmar ou **N** pra ignorar

---

## Tá dando erro?

**"Modelo não encontrado"**
→ O download do Passo 4 não terminou. Roda de novo.

**"llama-server não encontrado"**
→ Roda: `pkg install llama-cpp -y`

**"pkg: command not found"**
→ Reinstala o Termux pelo F-Droid (não pelo Play Store)

---

Qualquer dúvida manda mensagem 💜

contato discord: ihatemyselfbr
