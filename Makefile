# Makefile for NoteGen AI APIs - Medical SOAP Generation Microservice
# Production-ready development automation

.PHONY: install dev test lint format clean docker-up docker-down help docker-build docker-run
.DEFAULT_GOAL := help

# Project Configuration
PROJECT_NAME := notegen-ai-apis
PYTHON_VERSION := 3.11
## Development Commands
install:
	poetry install --with dev
	poetry run pre-commit install
dev: 
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

## Testing examples Commands
run-example:
	curl -X POST http://127.0.0.1:8000/generate-notes -H "Content-Type: application/json" -d @generated_notes/examples/example.json
run-example1:
	curl -X POST http://127.0.0.1:8000/generate-notes -H "Content-Type: application/json" -d @generated_notes/examples/example1.json
run-example2:
	curl -X POST http://127.0.0.1:8000/generate-notes -H "Content-Type: application/json" -d @generated_notes/examples/example2.json


run-example-prod:
	curl -X POST http://notegen-ai-api-staging-alb-2046352778.ca-central-1.elb.amazonaws.com/generate-notes -H "Content-Type: application/json" -d @generated_notes/examples/example.json
run-example1-prod:
	curl -X POST http://notegen-ai-api-staging-alb-2046352778.ca-central-1.elb.amazonaws.com/generate-notes -H "Content-Type: application/json" -d @generated_notes/examples/example1.json
run-example2-prod:
	curl -X POST http://notegen-ai-api-staging-alb-2046352778.ca-central-1.elb.amazonaws.com/generate-notes -H "Content-Type: application/json" -d @generated_notes/examples/example2.json

# Docker commands
docker-build:
	docker build -t notegen-ai-api .

docker-run:
	docker run -p 8000:8000 --env-file .env notegen-ai-api



