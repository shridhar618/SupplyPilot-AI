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
├── docs/
├── services/                 # Microservices
│   ├── api-gateway/
│   ├── collaboration-workflow/
│   ├── data-ingestion/
│   ├── demand-forecasting/
│   ├── inventory-optimization/
│   ├── product-catalog/
│   ├── promotion-pricing/
│   ├── supply-chain-resilience/
│   ├── user-management/
│   ├── data-warehouse/
│   ├── explainable-ai/
│   └── monitoring-alerting/
├── shared/                   # Shared code (database models, utilities)
├── frontend/                 # React frontend
└── tests/                    # Unit and integration tests
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
- **Styling**: Tailwind CSS
- **State Management**: React Query (TanStack Query)
- **Forms**: React Hook Form
- **Charts**: Recharts
- **Animations**: Framer Motion
- **Icons**: Lucide Icons
- **Routing**: React Router v6

### Data Engineering
- **ETL**: Custom pipelines (can be extended with Airflow/Prefect)
- **Stream Processing**: Apache Kafka (integrated)
- **Data Warehouse**: PostgreSQL (can be extended to Snowflake/Redshift)
- **Data Catalog': Simple implementation (can be extended)
- **Data Quality': Basic validation (can be extended with Great Expectations)
- **Orchestration': Docker Compose (can be extended to Kubernetes)

### Machine Learning
- **Frameworks**: PyTorch, TensorFlow, Scikit-learn
- **Models**: Prophet, XGBoost, LSTM, ARIMA
- **Model Serving': REST APIs (can be extended with BentoML/TensorFlow Serving)
- **Experiment Tracking': MLflow (can be extended)
- **Explainability': SHAP (integrated in collaboration service)
- **Feature Store': Simple implementation (can be extended with Feast)
- **Model Monitoring': Basic metrics (can be extended with Evidently AI)

### DevOps & Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose (development), Kubernetes (production)
- **CI/CD': GitHub Actions (can be added)
- **Infrastructure as Code': Terraform (can be added)
- **Service Mesh': None (can be added with Istio/Linkerd)
- **API Gateway': Custom FastAPI gateway (can be extended with Kong/AWS API Gateway)
- **Observability': Basic logging and metrics (can be extended with OpenTelemetry, Jaeger, Prometheus, Grafana)
- **Security': JWT-based authentication (can be extended with HashiCorp Vault, AWS KMS)

## Getting Started
### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and npm/yarn/pnpm
- Python 3.11+ and poetry/pip (optional, as we use Docker)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd supplypilot-ai
   ```

2. (Optional) Install backend dependencies for development:
   ```bash
   # For each service, you can install dependencies individually
   # Example for demand-forecasting service:
   cd services/demand-forecasting
   pip install -r requirements.txt
   cd ..
   ```
   But note: we use Docker for running services, so this step is optional for development.

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   # or yarn install
   cd ..
   ```

4. Set up environment variables (optional, as we use docker-compose with defaults):
   ```bash
   # The docker-compose.yml already sets default values for development
   # To override, create a .env file in the root directory
   cp .env.example .env   # if you have an example file
   # Edit .env with your configuration
   ```

5. Start the development stack:
   ```bash
   docker-compose up -d
   ```

6. Access the services:
   - API Gateway: http://localhost:8000
   - Documentation (Swagger UI): http://localhost:8000/docs
   - Frontend: http://localhost:3000 (if you start the frontend dev server)
   - Other services on their respective ports (see docker-compose.yml)

7. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   # or yarn dev
   cd ..
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
Each service has its own documentation:
- API Gateway: http://localhost:8000/docs
- Demand Forecasting: http://localhost:8002/docs
- Data Ingestion: http://localhost:8001/docs
- etc.

## Deployment
See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment instructions.

## Contributing
Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.