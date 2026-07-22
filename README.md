# DemandSense AI

AI-Powered Decision Intelligence Platform for Demand Forecasting and Supply Chain Optimization

## Tagline
Predict. Explain. Optimize. Decide.

## Project Vision
Traditional demand forecasting software predicts demand.
DemandSense AI should help businesses make intelligent business decisions.

The platform should:
• Forecast future demand
• Explain why demand changes
• Detect operational risks
• Recommend inventory actions
• Recommend procurement decisions
• Detect anomalies
• Optimize warehouse operations
• Simulate business scenarios
• Generate executive reports
• Answer business questions using AI

The objective is not
"What will demand be?"

The objective is
"What is the best business decision?"

## Table of Contents
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Development Approach](#development-approach)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Project Structure
```
supplypilot-ai/
├── README.md
├── docker-compose.yml
├── Makefile
├── docs/
├── src/
│   ├── backend/          # FastAPI backend
│   ├── frontend/         # React frontend
│   ├── data-engineering/ # Data ingestion pipelines
│   ├── ml-models/        # Machine learning models
│   └── infra/            # Infrastructure as code
├── tests/
└── requirements/
```

## Technology Stack
### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **Message Queue**: Apache Kafka / Celery
- **Authentication**: JWT, OAuth2, RBAC
- **API Documentation**: OpenAPI/Swagger
- **Testing**: PyTest, Hypothesis
- **Logging**: Structlog, ELK stack
- **Monitoring**: Prometheus, Grafana

### Frontend
- **Library**: React 18+
- **Language**: TypeScript
- **Styling**: Tailwind CSS, shadcn/ui
- **State Management**: TanStack Query (React Query)
- **Forms**: React Hook Form
- **Charts**: Recharts
- **Animations**: Framer Motion
- **Icons**: Lucide Icons
- **State Management**: Zustand / Redux Toolkit
- **Routing**: React Router v6

### Data Engineering
- **ETL**: Apache Airflow / Prefect
- **Stream Processing**: Apache Kafka Streams / Apache Flink
- **Data Warehouse**: Snowflake / Amazon Redshift / PostgreSQL
- **Data Catalog**: Apache Atlas / AWS Glue
- **Data Quality**: Great Expectations
- **Orchestration**: Kubernetes

### Machine Learning
- **Frameworks**: PyTorch, TensorFlow, Scikit-learn
- **Models**: Prophet, XGBoost, LightGBM, CatBoost, LSTM, GRU
- **Model Serving**: TorchServe, TensorFlow Serving, BentoML
- **Experiment Tracking**: MLflow, Weights & Biases
- **Explainability**: SHAP, LIME
- **Feature Store**: Feast
- **Model Monitoring**: Evidently AI, WhyLabs

### DevOps & Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes (EKS/AKS/GKE)
- **CI/CD**: GitHub Actions
- **Infrastructure as Code**: Terraform
- **Service Mesh**: Istio / Linkerd
- **API Gateway**: Kong / AWS API Gateway
- **Observability**: OpenTelemetry, Jaeger, Prometheus, Grafana
- **Security**: HashiCorp Vault, AWS KMS

## Getting Started
### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and npm/yarn/pnpm
- Python 3.11+ and poetry/pip
- PostgreSQL
- Redis
- Kafka (optional for development)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd supplypilot-ai
   ```

2. Install backend dependencies:
   ```bash
   cd src/backend
   poetry install
   # or pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd ../frontend
   npm install
   # or yarn install
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   cd ../backend
   alembic upgrade head
   ```

6. Start the development stack:
   ```bash
   cd ..
   docker-compose up -d
   ```

7. Start the backend development server:
   ```bash
   cd src/backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

8. Start the frontend development server:
   ```bash
   cd ../frontend
   npm run dev
   # or yarn dev
   ```

## Development Approach
We follow an iterative development approach:
1. Analyze requirements
2. Design architecture
3. Design database
4. Design APIs
5. Design UI
6. Implement backend
7. Implement frontend
8. Integrate AI
9. Test
10. Refactor
11. Document

## Architecture
See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system architecture.

## API Documentation
API documentation is available at `/docs` when the backend is running.

## Deployment
See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment instructions.

## Contributing
Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.