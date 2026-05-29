# Borgis — Chatbot de IA para Energia Solar

Borgis é um assistente virtual especializado em energia solar fotovoltaica, construído com Django e uma pipeline de RAG (Retrieval-Augmented Generation). Ele responde perguntas dos usuários em tempo real, buscando informações em uma base de conhecimento própria e gerando respostas com o modelo GPT-4o mini da OpenAI.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Tech Stack](#tech-stack)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Como Usar](#como-usar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Pipeline RAG](#pipeline-rag)
- [Controle de Acesso](#controle-de-acesso)
- [Endpoints](#endpoints)

---

## Visão Geral

O Borgis transforma um guia técnico de energia solar (PDF) em uma base de conhecimento vetorial consultável. Quando um usuário faz uma pergunta, o sistema recupera os trechos mais relevantes do documento e os envia ao LLM junto com a pergunta, produzindo respostas precisas e contextualizadas. As respostas chegam ao usuário em streaming token a token, criando uma experiência fluida e interativa.

---

## Funcionalidades

- **Chat com IA em streaming** — respostas transmitidas em tempo real via Server-Sent Events (SSE)
- **RAG com FAISS** — recuperação semântica dos trechos mais relevantes antes de gerar a resposta
- **Base de conhecimento em PDF** — o guia de energia solar é processado e indexado automaticamente
- **Reindexação pelo painel** — administradores e gerentes podem reconstruir o vectorstore pelo navegador
- **Multi-usuário** — cadastro, login/logout e controle de permissões por papel (Role-Based Access Control)
- **Interface responsiva** — frontend com Tailwind CSS, indicador de digitação e histórico de conversa na sessão

---

## Arquitetura

```
Usuário (navegador)
    │
    │  HTTP / SSE
    ▼
Django (views.py)
    │
    ├── stream_response()  ──►  consultar_ia_stream()
    │                               │
    │                    ┌──────────┴──────────┐
    │                    ▼                     ▼
    │             VectorStoreManager     OpenAIProvider
    │             (FAISS + embeddings)   (gpt-4o-mini)
    │                    │                     │
    │             top-4 docs relevantes        │
    │                    └──────────┬──────────┘
    │                               ▼
    │                        AIQueryService
    │                        (monta prompt + faz stream)
    │
    ▼
EventSource (JavaScript) → renderiza tokens na tela
```

---

## Tech Stack

| Camada | Tecnologia |
|---|---|
| Framework web | Django 5.2.1 |
| Banco de dados | PostgreSQL via Supabase |
| LLM | OpenAI `gpt-4o-mini` |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector store | FAISS (`faiss-cpu`) |
| Processamento de PDF | PyPDF |
| Orquestração LLM | LangChain + LangChain-OpenAI |
| Frontend | Tailwind CSS 4 + Vanilla JS (EventSource) |
| Autenticação | Django Auth + django-role-permissions |
| Configuração | python-decouple / python-dotenv |

---

## Pré-requisitos

- Python 3.10+
- Conta na [OpenAI](https://platform.openai.com/) com acesso à API
- Projeto no [Supabase](https://supabase.com/) (PostgreSQL)
- `pip` e `venv` (ou gerenciador equivalente)

---

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/viniAG34/Borgis-bot-IA-para-energia-solar.git
cd "Borgis-bot-IA-para-energia-solar"

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas credenciais (veja a seção abaixo)

# 5. Aplique as migrações
python manage.py migrate

# 6. Crie o usuário administrador inicial
python manage.py criar_admin

# 7. Construa o vectorstore (indexa o PDF)
# Acesse o painel de treinamento após subir o servidor (veja "Como Usar")

# 8. Suba o servidor de desenvolvimento
python manage.py runserver
```

Acesse em: [http://localhost:8000](http://localhost:8000)

---

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha os valores:

```env
# Django
SECRET_KEY=sua-chave-secreta-django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL (Supabase)
DB_NAME=postgres
DB_USER=postgres.<project-id>
DB_PASSWORD=sua-senha
DB_HOST=aws-0-sa-east-1.pooler.supabase.com
DB_PORT=6543

# Supabase API
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_KEY=sua-anon-key
SUPABASE_SERVICE_KEY=sua-service-role-key

# OpenAI
OPENAI_API_KEY=sk-...

# Usuário admin inicial (criado via manage.py criar_admin)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=senha-segura
ADMIN_EMAIL=admin@seudominio.com
```

> **Nunca commite o arquivo `.env` com credenciais reais.** Ele já está no `.gitignore`.

---

## Como Usar

### Usuário comum

1. Acesse `/usuarios/cadastro` e crie uma conta
2. Faça login em `/usuarios/login`
3. Navegue até `/oraculo/chat`
4. Digite sua dúvida sobre energia solar e pressione Enter
5. A resposta é gerada e exibida em tempo real

### Administrador / Gerente

1. Faça login com a conta de admin (criada via `criar_admin`)
2. Para reindexar o conteúdo do PDF, acesse `/oraculo/treinar_ia`
3. Clique em **Reconstruir Vectorstore** — o sistema reprocessa o PDF e recria o índice FAISS
4. Gerencie permissões de usuários em `/usuarios/permissoes`

---

## Estrutura do Projeto

```
.
├── core/                   # Configuração Django (settings, urls, roles)
│   ├── settings.py
│   ├── urls.py
│   └── roles.py            # Define o papel "Gerente" com permissão treinar_ia
│
├── oraculo/                # App principal — chat e RAG
│   ├── utils.py            # Pipeline RAG completa (DocumentProcessor, VectorStoreManager, AIQueryService)
│   ├── views.py            # Views: chat, stream SSE, treinar_ia
│   ├── models.py           # Modelos: Treinamentos, DataTreinamento, Pergunta
│   ├── urls.py
│   └── templates/
│       ├── chat.html       # Interface do chat com streaming
│       └── treinar_ia.html # Painel de reindexação
│
├── usuarios/               # App de autenticação e permissões
│   ├── views.py            # Cadastro, login, gerenciamento de permissões
│   ├── urls.py
│   └── templates/
│       ├── login.html
│       ├── cadastro.html
│       └── permissoes.html
│
├── templates/
│   └── base.html           # Template base com navbar e Tailwind CSS
│
├── guia_energia_solar.pdf  # Base de conhecimento (documento fonte)
├── vectorstore/            # Índice FAISS gerado (não versionado)
├── manage.py
├── requirements.txt
└── .env.example
```

---

## Pipeline RAG

O fluxo completo de geração de resposta passa por quatro etapas:

**1. Processamento do documento (`DocumentProcessor`)**
- Carrega o PDF `guia_energia_solar.pdf` com PyPDF
- Divide o texto em chunks de 800 caracteres com sobreposição de 100 caracteres usando `RecursiveCharacterTextSplitter`

**2. Indexação vetorial (`VectorStoreManager`)**
- Gera embeddings para cada chunk com `text-embedding-3-small` (OpenAI)
- Armazena o índice FAISS localmente em `vectorstore/`
- Reutiliza o índice em disco a cada reinicialização (sem custo extra de API)

**3. Consulta (`AIQueryService`)**
- Converte a pergunta do usuário em embedding
- Recupera os 4 chunks mais semanticamente próximos do índice FAISS
- Monta um `ChatPromptTemplate` com: papel do assistente + contexto recuperado + pergunta

**4. Geração com streaming**
- Envia o prompt ao `gpt-4o-mini` (temperatura 0.3 para respostas precisas)
- Transmite cada token via `StreamingHttpResponse` usando o protocolo SSE (`text/event-stream`)
- O frontend consome os eventos com a API `EventSource` e renderiza os tokens em tempo real

---

## Controle de Acesso

| Recurso | Permissão necessária |
|---|---|
| `/oraculo/chat` | Usuário autenticado |
| `/oraculo/treinar_ia` | Superusuário ou papel `Gerente` |
| `/usuarios/permissoes` | Superusuário |
| `/admin/` | Superusuário |

Papéis são gerenciados via `django-role-permissions`. O papel **Gerente** concede acesso à reindexação sem precisar ser superusuário.

---

## Endpoints

| Método | URL | Descrição |
|---|---|---|
| `GET` | `/` | Redireciona para `/oraculo/chat` |
| `GET` | `/oraculo/chat` | Interface do chat |
| `GET` | `/oraculo/stream_response` | Stream SSE com a resposta da IA |
| `GET/POST` | `/oraculo/treinar_ia` | Painel de reindexação (admin/gerente) |
| `GET/POST` | `/usuarios/login` | Login |
| `GET/POST` | `/usuarios/cadastro` | Cadastro de novo usuário |
| `POST` | `/usuarios/logout` | Logout |
| `GET/POST` | `/usuarios/permissoes` | Gerenciamento de papéis (admin) |
| `GET/POST` | `/admin/` | Django Admin |

---

## Licença

Este projeto foi desenvolvido para uso interno. Consulte o proprietário para informações sobre licenciamento e redistribuição.
