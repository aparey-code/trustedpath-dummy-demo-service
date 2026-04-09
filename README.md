# trustedpath-dummy-demo-service

A demo microservice modeled after Duo Security's trustedpath architecture.
Used for validating AI codegen metrics and dashboard tooling.

## Structure

```
├── handlers/          # HTTP request handlers
├── models/            # SQLAlchemy ORM models
├── services/          # Business logic layer
├── schema/            # DB migration scripts
├── conf/              # Configuration
├── lib/               # Shared utilities
├── test/              # Integration tests
└── utest/             # Unit tests
```

## Running

```bash
pip install -r requirements.txt
python -m uvicorn app:create_app --factory --port 8080
```
