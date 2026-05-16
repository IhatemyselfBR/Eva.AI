Eva.AI 🤖💜
Uma amiga IA pra quem precisa de companhia.
Eva é uma IA local que roda no Termux ou Linux, feita pra ser uma amiga de verdade — não um assistente robótico. Ela conversa no estilo brasileiro casual, aprende sobre você com o tempo e tá sempre por aqui.
O que ela faz
Conversa de forma natural, sem aquele papo de chatbot forçado
Aprende sobre você e salva com sua confirmação (S/N)
Lembra do que você contou nas próximas conversas
Roda 100% local — sem mandar seus dados pra ninguém
Leve o suficiente pra rodar no celular via Termux
Requisitos
Python 3.8+
llama.cpp instalado (llama-server)
~2GB de espaço livre pro modelo
Termux (Android) ou qualquer Linux
Instalação
1. Instala o llama.cpp
Termux:
Bash
Linux:
Bash
2. Baixa o modelo
Bash
O modelo tem ~1.5GB. Pode demorar dependendo da sua conexão.
3. Clona o repositório
Bash
4. Roda
Bash
Na primeira vez demora uns 30 segundos enquanto o servidor sobe. Depois fica rápido.
Comandos dentro da conversa
Comando
O que faz
/sair
Encerra a Eva
/limpar
Limpa o histórico da conversa atual
/aprendi
Mostra o que a Eva já aprendeu sobre você
Como o aprendizado funciona
Quando você manda uma mensagem com informação pessoal (nome, idade, o que gosta, onde mora etc), a Eva pergunta:
Código
Você decide o que ela guarda. Tudo fica salvo no learn.json localmente — nunca vai pra nenhum servidor externo.
Estrutura do projeto
Código
Personalização
Você pode editar a personalidade da Eva direto no eva.py, na variável EVA_SYSTEM. É um texto simples descrevendo como ela deve se comportar.
Também dá pra trocar o modelo — qualquer .gguf compatível com o llama.cpp funciona. Só atualiza o MODEL_PATH no início do arquivo.
Projeto
Feito por @IhatemyselfBR — uma IA amiga pra quem se sente sozinho na vida.
Contribuições são bem-vindas 💜
