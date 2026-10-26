# 🗣️ Tutor de Pronúncia de Inglês

Agente de IA que ajuda brasileiros a pronunciar palavras em inglês. O usuário digita uma palavra (em português ou inglês) e recebe a palavra em inglês, a transcrição fonética (IPA), a pronúncia "aportuguesada", uma dica sobre o som mais difícil e uma frase de exemplo.

> Projeto final do curso de agentes de IA, com **RAG**, **memória de curto prazo** e **MCP**.

---

## 📌 Exemplo

**Entrada:** `cachorro`

```
Inglês:      dog
IPA:         /dɔɡ/
Pronúncia:   "dóg"
Dica:        o "o" é aberto, parecido com o "ó" de "pó"
Exemplo:     The dog is sleeping. → "dâ dóg iz slípin"
```

---

## 🎯 Problema e justificativa

Quem aprende inglês no Brasil costuma errar a pronúncia por causa de sons que não existem no português (*th*, *-ed*, *ough*, vogais curtas e longas) e da grafia irregular do inglês. Dicionários trazem o IPA, mas ele é pouco acessível para usuários comuns.

O tutor converte o IPA em uma pronúncia que um brasileiro consegue ler e explica **por que** a palavra soa daquele jeito.

---

## 🧩 Como os requisitos são atendidos

| Componente | Onde está | Por que existe |
|---|---|---|
| **RAG** | `rag.py` + `data/` | As dicas vêm de uma base de regras de pronúncia para brasileiros. O modelo se apoia em material confiável em vez de depender só do que memorizou. |
| **Modelo de análise** | `analisador.py` | Antes do agente, um modelo separado corrige erros de digitação, extrai a palavra de frases como "como fala cachorro?" e já entrega o par inglês/português pronto. O agente fica só com a pronúncia. |
| **Memória de curto prazo** | `memory.py` | Guarda as últimas mensagens e as palavras da sessão, para perguntas de acompanhamento como "e a rima dela?" funcionarem. |
| **MCP** | `mcp_server.py` | O IPA, as sílabas e as rimas são dados determinísticos, então vêm de tools em vez de serem "adivinhados" pelo modelo. O servidor também guarda o histórico do aluno em SQLite. |
| **Interface** | `app.py` (Streamlit) | Tela simples para usuários comuns, sem terminal. |

---

## 🏗️ Arquitetura

```
Usuário digita uma palavra
        │
        ▼
   app.py (Streamlit)
        │
        ▼
   analisador.py  (modelo de análise: corrige, organiza e traduz a palavra)
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

## 🤖 Modelos utilizados

O projeto usa três modelos, cada um com uma função diferente:

| Função | Modelo | Onde roda | Variável no `.env` |
|---|---|---|---|
| **Análise** da entrada | `llama3.2` (3B) | Ollama | `OLLAMA_ANALYSIS_MODEL` |
| **Chat**: agente de tradução e pronúncia | `llama3.1` (8B) | Ollama | `OLLAMA_MODEL` |
| **Embeddings** do RAG | `Xenova/paraphrase-multilingual-MiniLM-L12-v2` | Local (ONNX), baixado do Hugging Face | `HF_EMBED_MODEL` |

### Por que cada modelo

**`llama3.2` (análise).** A primeira etapa é simples: corrigir erros de digitação, tirar a palavra de frases como "como fala cachorro?" e traduzir para o inglês. Um modelo pequeno (3B) faz isso bem e responde rápido, então o aluno não espera duas vezes o tempo de um modelo grande. A resposta usa saída estruturada (JSON com esquema fixo), o que deixa o resultado previsível mesmo com um modelo menor.

**`llama3.1` (chat).** É o agente que conversa com o aluno, decide quais tools do MCP chamar (IPA, sílabas, rimas, histórico) e escreve a dica e a frase de exemplo. Essa etapa exige suporte a *tool calling*, que o `llama3.1` tem, e um modelo maior (8B), que segue instruções e escreve explicações em português com mais qualidade.

**`Xenova/paraphrase-multilingual-MiniLM-L12-v2` (embeddings).**
- **Multilíngue:** as regras de pronúncia estão em português, e 
├── rag.py              # indexação e busca das regras de pronúncia
├── embeddings.py       # embeddings locais com modelo Xenova (Hugging Face)
├── memory.py           # memória de curto prazo
├── mcp_server.py       # servidor MCP com as tools
├── data/
│   └── regras_pronuncia.txt
├── manage.py           # start/stop via Docker SDK e modo local sem Docker
├── Dockerfile          # imagem da aplicação
├── docker-compose.yml  # alternativa ao manage.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Requisitos

- Python 3.10 ou superior
- Git
- **Com Docker:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e aberto
- **Sem Docker:** [Ollama](https://ollama.com) instalado (local) ou conta no Ollama Cloud

---

## 🐳 Como executar com Docker (recomendado)

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

No `.env` você escolhe o modelo de chat do Ollama (`OLLAMA_MODEL`), o de análise (`OLLAMA_ANALYSIS_MODEL`) e o de embeddings do Hugging Face (`HF_EMBED_MODEL`). Para usar o Ollama Cloud, remova o `#` da linha `OLLAMA_API_KEY`.

### 3. Subir os containers

Com o Docker Desktop aberto:

```bash
python manage.py start
```

O comando baixa a imagem do Ollama, cria a rede e os volumes, sobe o container do Ollama, baixa os modelos (só demora na primeira vez), constrói a imagem e sobe a aplicação. Ao final, acesse `http://localhost:8501`.

### 4. Parar os containers

```bash
python manage.py stop
```

Os modelos baixados e o histórico de palavras ficam salvos nos volumes e são reaproveitados na próxima vez.

### Alternativa: Docker Compose

```bash
docker compose up --build    # sobe tudo
docker compose down          # para tudo
```

---

## 🚀 Como executar sem Docker

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

### 3. Configurar o `.env`

```bash
# Linux / macOS
cp .env.example .env

# Windows
copy .env.example .env
```

No `.env` você escolhe o modelo de chat do Ollama (`OLLAMA_MODEL`), o de análise (`OLLAMA_ANALYSIS_MODEL`) e o de embeddings do Hugging Face (`HF_EMBED_MODEL`). Para usar o Ollama Cloud, remova o `#` da linha `OLLAMA_API_KEY`.

### 4. Rodar a aplicação

```bash
python manage.py local
```

O comando usa o Ollama instalado na máquina (e roda `ollama serve` sozinho se ele não estiver aberto), baixa os modelos de chat e de análise, confere a conexão e abre o Streamlit em `http://localhost:8501`. Para parar, use `Ctrl+C`. O histórico de palavras fica em `progresso.db` e o índice do RAG em `.chroma/`, na pasta do projeto.

O modelo de embeddings do RAG (`Xenova/paraphrase-multilingual-MiniLM-L12-v2`) é baixado automaticamente do Hugging Face na primeira execução e roda localmente, sem o Ollama. O servidor MCP é iniciado pelo agente, então não é preciso rodá-lo à parte.

### Alternativa: passo a passo manual

```bash
ollama pull llama3.1    # modelo de chat (OLLAMA_MODEL)
ollama pull llama3.2    # modelo de análise (OLLAMA_ANALYSIS_MODEL)
streamlit run front-end/app.py
```

---

## 🖥️ Como usar

1. Digite uma palavra na caixa de texto (ex.: `cachorro` ou `thought`).
2. Clique em **Pronunciar**.
3. Veja o cartão com inglês, IPA, pronúncia, dica e exemplo.
4. Use o chat para dúvidas ("me dá rimas", "quantas sílabas tem?", "mostre as palavras que já vi").
5. A barra lateral mostra o histórico de palavras estudadas.

---

## 🛠️ Tools do servidor MCP

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

## 🧠 Decisões técnicas

- **IPA via tool, não via modelo:** modelos de linguagem erram transcrições fonéticas. A biblioteca `eng-to-ipa` consulta o dicionário CMU e devolve um resultado verificável.
- **Palavra desconhecida:** a tool devolve um erro claro, e o agente avisa o usuário em vez de inventar uma pronúncia.
- **Persistência separada da memória:** o SQLite no servidor MCP guarda o progresso entre sessões. A memória do agente cobre apenas a conversa atual.
- **Validação de entrada:** as tools rejeitam texto vazio, muito longo ou com símbolos antes de consultar qualquer biblioteca.
- **Logs no stderr:** em servidores MCP via stdio, o stdout é reservado ao protocolo.

---

## ⚠️ Limitações

- A pronúncia aportuguesada é uma aproximação, pois alguns sons do inglês não existem no português.
- O dicionário cobre principalmente inglês americano.
- Palavras muito raras, nomes próprios ou gírias podem não ser encontrados.
- Sem áudio: a pronúncia é apenas em texto.

---


## 🧰 Tecnologias

Python · MCP (`mcp`) · Ollama · Hugging Face (Xenova, ONNX Runtime) · ChromaDB · Streamlit · SQLite · `eng-to-ipa` · `pronouncing`

---

