# PIPPA Compras Públicas

## O que é este projeto
Aplicação web de inteligência em compras governamentais que cruza a **demanda pública** (licitações, contratos, atas do PNCP, DOU e diários municipais) com a **oferta produtiva das MPEs** (dados do Observatório SEBRAE) para gerar oportunidades e indicadores para 4 perfis de usuário.

## Arquitetura
- **Backend:** FastAPI (Python 3.12) + PostgreSQL + SQLAlchemy + APScheduler
- **Frontend:** React 18 + Vite + TypeScript + Tailwind CSS + Recharts
- **Deploy:** Frontend → GitHub Pages | Backend → Railway/Render/Cloud Run

## Perfis de Usuário
1. `gestor_publico` — Gestor de compras de órgão público
2. `sebrae_nacional` — Analista de políticas públicas do SEBRAE Nacional
3. `sebrae_uf` — Gerente de desenvolvimento territorial do SEBRAE estadual
4. `mpe` — Proprietário de micro ou pequena empresa

## Fontes de Dados (APIs oficiais)
- **PNCP** (`pncp.gov.br/api/consulta`) — licitações, contratos, atas, PCA (sem auth)
- **DOU Seção 3** (`in.gov.br`) — editais federais
- **Querido Diário** (`api.queridodiario.org.br`) — diários oficiais municipais (sem auth)
- **Dados Abertos Compras** (`dadosabertos.compras.gov.br`) — CATMAT/CATSER, preços
- **Observatório SEBRAE** (`apiv2-observatorio.sebrae.com.br/tesseract`) — MPEs por CNAE/município (token)

## Comandos

### Backend
```bash
cd backend
cp .env.example .env  # preencher OBSERVATORIO_TOKEN
docker compose up -d db
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Convenções
- Backend: Python 3.12+, type hints obrigatórios, async/await para I/O
- Frontend: TypeScript strict, componentes funcionais, Tailwind para estilos
- Routers do backend retornam JSON, um router por perfil
- Cada serviço de dashboard monta a resposta específica do perfil
- Classificação de oportunidades usa 5 sinais: oportunidade, competitivo, cautela, saturado, deserto
