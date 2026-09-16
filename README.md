# PIPPA Compras Públicas

**Plataforma de Inteligência em Compras Governamentais para MPEs**

Aplicação web que cruza a demanda de compras públicas (licitações, contratos, atas de registro de preço) com a oferta produtiva das micro e pequenas empresas brasileiras, gerando oportunidades e indicadores para diferentes perfis de usuário.

## Perfis de Usuário

| Perfil | Para quem | O que oferece |
|--------|-----------|---------------|
| **Gestor Público** | Secretários, diretores de compras | Indicadores de conformidade MPE, benchmark de preços, planejamento PCA |
| **SEBRAE Nacional** | Diretores e analistas da sede | Panorama nacional, tendências, desertos de fornecimento, dados para advocacy |
| **SEBRAE UF** | Gerentes regionais | Radar de oportunidades no estado, cruzamento oferta × demanda, alertas CNAE |
| **MPE** | Proprietários de pequenos negócios | Oportunidades de venda ao governo em linguagem simples, mobile-first |

## Fontes de Dados

- [PNCP](https://pncp.gov.br) — Portal Nacional de Contratações Públicas (federal, estadual, municipal)
- [DOU Seção 3](https://www.in.gov.br) — Diário Oficial da União (editais federais)
- [Querido Diário](https://queridodiario.ok.org.br) — Diários oficiais municipais (955 municípios)
- [Dados Abertos Compras](https://dadosabertos.compras.gov.br) — Catálogos CATMAT/CATSER, pesquisa de preços
- [Observatório SEBRAE](https://observatorio.sebrae.com.br) — MPEs por CNAE e município

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS + Recharts |
| Backend | FastAPI + SQLAlchemy + PostgreSQL + APScheduler |
| Deploy | GitHub Pages (frontend) + Railway/Render (backend) |

## Setup Local

### Backend

```bash
cd backend
cp .env.example .env    # preencher OBSERVATORIO_TOKEN
docker compose up -d db # PostgreSQL local
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload  # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

## Estrutura

```
pippa-compras-publicas/
├── backend/
│   ├── app/
│   │   ├── clients/       # Clientes de API (PNCP, Querido Diário, Observatório, DOU, Dados Abertos)
│   │   ├── models/        # Modelos ORM (contratação, item, contrato, cruzamento, alerta)
│   │   ├── routers/       # Endpoints por perfil (gestor_publico, sebrae_nacional, sebrae_uf, mpe)
│   │   ├── services/      # Lógica de negócio (classificador, cruzamento demanda × oferta)
│   │   └── collectors/    # Pipeline de coleta diária
│   └── docker-compose.yml
├── frontend/
│   └── src/
│       ├── components/    # Componentes React por perfil + shared
│       ├── pages/         # Páginas (Home, GestorPublico, SebraeNacional, SebraeUF, MPE)
│       └── api/           # Cliente HTTP + hooks React Query
└── .github/workflows/     # CI + deploy GitHub Pages
```

## Motor de Inteligência

O diferencial do PIPPA Compras é o cruzamento **Demanda Pública × Oferta MPE**:

1. Cada contratação é classificada em 8 dimensões (esfera, modalidade, momento, exclusividade MPE, CATMAT, valor, localização, urgência)
2. O CATMAT/CATSER é mapeado para o CNAE equivalente
3. O Observatório SEBRAE retorna a quantidade de MPEs daquele CNAE na região
4. Um sinal de oportunidade é gerado:
   - 🟢 **Oportunidade** — poucas MPEs competindo, cota exclusiva disponível
   - 🟡 **Competitivo** — mercado equilibrado
   - 🟠 **Atenção** — mercado saturado
   - 🔴 **Saturado** — muitos fornecedores estabelecidos
   - ⚪ **Deserto** — demanda existe, mas faltam MPEs no setor/região
