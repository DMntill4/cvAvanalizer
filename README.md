# Analizador de Currículums con IA - Docker Base Monorepo

Repositorio base con entorno de desarrollo en Docker para aplicaciones de Inteligencia Artificial, procesamiento de lenguaje natural y modelos estructurados con LangChain y Streamlit.

---

## 1. Estructura General del Repositorio

```
.
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── init/
│   └── .gitkeep
└── app/
    ├── main.py
    └── intermedio/
        └── cv_analyzer/
            ├── README.md
            ├── app.py
            ├── models/
            │   ├── __init__.py
            │   └── cv_model.py
            ├── prompts/
            │   ├── __init__.py
            │   └── cv_prompts.py
            ├── services/
            │   ├── __init__.py
            │   ├── pdf_processor.py
            │   └── cv_evaluator.py
            ├── ui/
            │   ├── __init__.py
            │   └── streamlit_ui.py
            └── tests/
                ├── __init__.py
                └── test_cv_analyzer.py
```

---

## 2. Inicio Rápido

### Ejecución Local del Analizador de CV
```bash
pip install -r requirements.txt
cd app/intermedio/cv_analyzer
streamlit run app.py
```

### Ejecución con Docker Compose
```bash
cp .env.example .env
docker compose up -d --build
docker compose exec -w /app/app/intermedio/cv_analyzer app python -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

Consulta [`app/intermedio/cv_analyzer/README.md`](app/intermedio/cv_analyzer/README.md) para ver la especificación técnica completa, umbrales y criterios de evaluación.

