# Makefile for NoteGen AI APIs - Medical SOAP Generation Microservice
# Production-ready development automation

.PHONY: install dev test lint format clean docker-up docker-down help
.DEFAULT_GOAL := help

# Project Configuration
PROJECT_NAME := notegen-ai-apis
PYTHON_VERSION := 3.11
DOCKER_COMPOSE_FILE := docker-compose.yml

## Development Commands
install:
	poetry install --with dev
	poetry run pre-commit install

dev: 
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

## Testing examples Commands
run-example:
	curl -X POST http://127.0.0.1:8000/process-encounter -H "Content-Type: application/json" -d @generated_notes/examples/example.json

run-example2:
	curl -X POST http://127.0.0.1:8000/process-encounter -H "Content-Type: application/json" -d @generated_notes/examples/example2.json