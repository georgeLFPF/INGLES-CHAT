# Fala Fácil: tutor de pronúncia de inglês

Agente de IA que ajuda brasileiros a pronunciar palavras em inglês. O usuário digita uma palavra (em português ou inglês) e recebe a palavra em inglês, a transcrição fonética (IPA), a pronúncia "aportuguesada", uma dica sobre o som mais difícil e uma frase de exemplo.

> Projeto final do curso de agentes de IA, com **RAG**, **memória de curto prazo** e **MCP**.

---

## Exemplo

**Entrada:** `cachorro`

```
Inglês:      dog
IPA:         /dɔɡ/
Pronúncia:   "dóg"
Dica:        o "o" é aberto, parecido com o "ó" de "pó"
Exemplo:     The dog is sleeping. → "dâ dóg iz slípin"
```

---

## Problema e justificativa

Quem aprende inglês no Brasil costuma errar a pronúncia por causa de sons que não existem no português (*th*, *-ed*, *ough*, vogais curtas e longas) e da grafia irregular do inglês. Dicionários trazem o IPA, mas ele é pouco acessível para usuários comuns.

O tutor converte o IPA em uma pronúncia que um brasileiro consegue ler e explica **por que** a palavra soa daquele jeito.

---

## Como os requisitos são atendidos

| Componente | Onde está | Por que existe |
|---|---|---|
| **RAG** | `rag.py` + `data/` | As dicas vêm de uma base de regras de pronúncia para brasileiros. O modelo se apoia em material confiável em vez de depender só do que memorizou. |
| **Agente de análise** | `analisador.py` | Antes do agente de pronúncia, um agente de análise (com o mesmo modelo) corrige erros de digitação, extrai a palavra de frases como "como fala cachorro?" e já entrega o par inglês/português pronto. O agente fica só com a pronúncia. |
| **Memória de curto prazo** | `memory.py` | Guarda as últimas mensagens e as palavras da sessão, para perguntas de acompanhamento como "e a rima dela?" funcionarem. |
| **MCP** | `mcp_server.py` | O IPA, as sílabas e as rimas são dados determinísticos, então vêm de tools em vez de serem "adivinhados" pelo modelo. O servidor também guarda o histórico do aluno em SQLite. |
| **Interface** | `app.py` (Streamlit) | Tela simples para usuários comuns, sem terminal. |

---

## Arquitetura

```
Usuário digita uma palavra
        │
        ▼
   app.py (Streamlit)
        │
        ▼
   analisador.py  (agente de análise: corrige, organiza e traduz a palavra)
        │
        ▼
   agent.py ──► memory.py   (histórico da sessão)
        │   └─► rag.py      (busca regra de pronúncia → ChromaDB)
        │         └─► embeddings.py  (vetores com Xenova/Hugging Face, ONNX local)
        │
        ▼
   Modelo (Ollama) ──► decide chamar tools
        │
        ▼
   mcp_server.py
     ├─ ipa_da_palavra
     ├─ contar_silabas
     ├─ rimas_da_palavra
     ├─ salvar_palavra
     └─ listar_palavras   (SQLite: progresso.db)
```

---

## Modelos utilizados

O projeto usa dois modelos: um do Ollama, compartilhado pelos dois agentes, e um de embeddings:

| Função | Modelo | Onde roda | Variável no `.env` |
|---|---|---|---|
| **Agentes**: análise da entrada e chat de tradução e pronúncia | `llama3.1` (8B) | Ollama | `OLLAMA_MODEL` |
| **Embeddings** do RAG | `Xenova/paraphrase-multilingual-MiniLM-L12-v2` | Local (ONNX), baixado do Hugging Face | `HF_EMBED_MODEL` |

### Por que cada modelo

**`llama3.1` (análise e chat).** Um único modelo atende os dois agentes, então só ele fica carregado na memória do Ollama, em vez de dois modelos disputando RAM/VRAM e sendo trocados a cada pergunta. Os agentes continuam separados, cada um com seu prompt:
- **Análise:** corrige erros de digitação, tira a palavra de frases como "como fala cachorro?" e traduz para o inglês. Usa saída estruturada (JSON com esquema fixo), o que deixa o resultado previsível.
- **Chat:** conversa com o aluno, decide quais tools do MCP chamar (IPA, sílabas, rimas, histórico) e escreve a dica e a frase de exemplo. Exige suporte a *tool calling*, que o `llama3.1` tem.

Em máquinas mais fracas, dá para trocar por `llama3.2` (3B) no `OLLAMA_MODEL`, ao custo de explicações um pouco piores.

**`Xenova/paraphrase-multilingual-MiniLM-L12-v2` (embeddings).**
- **Multilíngue:** as regras de pronúncia estão em português, e 
├── rag.py              # indexação e busca das regras de pronúncia
├── embeddings.py       # embeddings locais com modelo Xenova (Hugging Face)
├── memory.py           # memória de curto prazo
├── mcp_server.py       # servidor MCP com as tools
├── data/
│   └── regras_pronuncia.txt
├── manage.py           # start/stop dos containers via Docker SDK
├── Dockerfile          # imagem da aplicação
├── docker-compose.yml  # alternativa ao manage.py
├── requirements.txt
└── README.md
```

---

## Requisitos

- Python 3.10 ou superior
- Git
- **Com Docker:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e aberto
- **Sem Docker:** [Ollama](https://ollama.com) instalado (local) ou conta no Ollama Cloud

---

## Como executar com Docker (recomendado)

O script `manage.py` usa o Docker SDK para Python para subir tudo: o Ollama, os modelos e a aplicação. Não é preciso instalar o Ollama na máquina.

### 1. Clonar o repositório e instalar as dependências

```bash
git clone https://github.com/<seu-usuario>/tutor-pronuncia.git
cd tutor-pronuncia

python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configurar o `.env`

```bash
# Linux / macOS
cp .env.example .env

# Windows
copy .env.example .env
```

No `.env` você escolhe o modelo do Ollama usado pelos dois agentes (`OLLAMA_MODEL`) e o de embeddings do Hugging Face (`HF_EMBED_MODEL`). Para usar o Ollama Cloud, remova o `#` da linha `OLLAMA_API_KEY`, coloque sua chave e escolha um modelo do Cloud (ex.: `gpt-oss:20b`). Com a chave, o Ollama local não é iniciado.

### 3. Subir os containers

Com o Docker Desktop aberto:

```bash
python manage.py start
```

O comando baixa a imagem do Ollama, cria a rede e os volumes, sobe o container do Ollama, baixa os modelos (só demora na primeira vez), constrói a imagem e sobe a aplicação. Ao final, acesse `http://localhost:8501`.

Nas execuções seguintes, a imagem do Ollama e os modelos que já existem localmente não são baixados de novo, o build da aplicação roda em paralelo com a subida do Ollama, e o container da aplicação é mantido se nada mudou. Para buscar versões novas da imagem do Ollama e dos modelos, use `python manage.py start --atualizar`.

### 4. Parar os containers

```bash
python manage.py stop
```

Os modelos baixados e o histórico de palavras ficam salvos nos volumes e são reaproveitados na próxima vez.

### Pouca memória (erro ao enviar mensagem no chat)

Se o chat responder com erro e o log do Ollama (`docker logs tutor-ollama`) mostrar `insufficient memory` ou `unable to allocate CPU_REPACK buffer`, o modelo não coube na RAM. O `llama3.1` (8B) precisa de uns 5 GB livres. Nesse caso:

1. **Use o Ollama Cloud (recomendado em máquinas com até 8 GB de RAM).** No `.env`, coloque sua chave em `OLLAMA_API_KEY` (crie em https://ollama.com/settings/keys) e um modelo do Cloud com tool calling, como `OLLAMA_MODEL=gpt-oss:20b`. Com a chave, o `manage.py` não sobe o Ollama local e a aplicação conversa direto com `https://ollama.com`.
2. Ou troque o modelo local por um menor: `OLLAMA_MODEL=llama3.2` (3B, uns 3 GB) ou `llama3.2:1b` (mais leve, respostas piores).
3. Se o Docker roda no WSL, aumente a memória dele criando `C:\Users\<usuario>\.wslconfig`:

   ```ini
   [wsl2]
   memory=3GB
   swap=4GB
   ```

   Depois rode `wsl --shutdown` no Windows e suba os containers de novo.
4. Pare outros containers que não esteja usando, para liberar RAM.

### Alternativa: Docker Compose

```bash
docker compose up --build    # sobe tudo
docker compose down          # para tudo
```

---

## Como executar sem Docker

### 1. Clonar o repositório

```bash
git clone https://github.com/<seu-usuario>/tutor-pronuncia.git
cd tutor-pronuncia
```

### 2. Criar o ambiente virtual e instalar as dependências

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Baixar o modelo no Ollama

```bash
ollama pull llama3.1   # o mesmo modelo atende os dois agentes (use o que estiver em OLLAMA_MODEL)
```

O modelo de embeddings do RAG (`Xenova/paraphrase-multilingual-MiniLM-L12-v2`) é baixado automaticamente do Hugging Face na primeira execução e roda localmente, sem o Ollama.

### 4. Configurar o modelo

```bash
# Linux / macOS
cp .env.example .env

# Windows
copy .env.example .env
```

No `.env` você escolhe o modelo do Ollama usado pelos dois agentes (`OLLAMA_MODEL`) e o de embeddings do Hugging Face (`HF_EMBED_MODEL`). Para usar o Ollama Cloud, remova o `#` da linha `OLLAMA_API_KEY`, coloque sua chave e escolha um modelo do Cloud (ex.: `gpt-oss:20b`). Com a chave, o Ollama local não é iniciado.

### 5. Rodar a aplicação

```bash
streamlit run front-end/app.py
```

O navegador abre em `http://localhost:8501`. O servidor MCP é iniciado automaticamente pelo agente, então não é preciso rodá-lo à parte.

---

## Como usar

1. Digite uma palavra na caixa de texto (ex.: `cachorro` ou `thought`).
2. Clique em **Pronunciar**.
3. Veja o cartão com inglês, IPA, pronúncia, dica e exemplo.
4. Use o chat para dúvidas ("me dá rimas", "quantas sílabas tem?", "mostre as palavras que já vi").
5. A barra lateral mostra o histórico de palavras estudadas.

---

## Tools do servidor MCP

| Tool | O que faz |
|---|---|
| `ipa_da_palavra` | Retorna a transcrição IPA de uma palavra em inglês |
| `contar_silabas` | Número de sílabas e posição da sílaba tônica |
| `rimas_da_palavra` | Até 10 palavras que rimam |
| `salvar_palavra` | Grava o par português/inglês e o IPA no SQLite |
| `listar_palavras` | Lista as 50 palavras mais recentes do histórico |

O servidor também expõe um **resource** (`pronuncia://regras/th`) e um **prompt** (`tutor_pronuncia`).

### Testar o servidor MCP isoladamente

```bash
mcp dev mcp_server.py
```

Abre o MCP Inspector no navegador, onde cada tool pode ser chamada manualmente.

---

## Decisões técnicas

- **IPA via tool, não via modelo:** modelos de linguagem erram transcrições fonéticas. A biblioteca `eng-to-ipa` consulta o dicionário CMU e devolve um resultado verificável.
- **Palavra desconhecida:** a tool devolve um erro claro, e o agente avisa o usuário em vez de inventar uma pronúncia.
- **Persistência separada da memória:** o SQLite no servidor MCP guarda o progresso entre sessões. A memória do agente cobre apenas a conversa atual.
- **Validação de entrada:** as tools rejeitam texto vazio, muito longo ou com símbolos antes de consultar qualquer biblioteca.
- **Logs no stderr:** em servidores MCP via stdio, o stdout é reservado ao protocolo.

---

## Limitações

- A pronúncia aportuguesada é uma aproximação, pois alguns sons do inglês não existem no português.
- O dicionário cobre principalmente inglês americano.
- Palavras muito raras, nomes próprios ou gírias podem não ser encontrados.
- Sem áudio: a pronúncia é apenas em texto.

---


## Tecnologias

Python · MCP (`mcp`) · Ollama · Hugging Face (Xenova, ONNX Runtime) · ChromaDB · Streamlit · SQLite · `eng-to-ipa` · `pronouncing`

---

