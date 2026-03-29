# Makefile for Swasthya Sampark
# Provides convenient commands for development and deployment

.PHONY: help install dev run test clean docker-build docker-run docker-up docker-down deploy

help:
	@echo "Swasthya Sampark - Available Commands:"
	@echo ""
	@echo "  make install     - Install Python dependencies"
	@echo "  make dev         - Setup development environment"
	@echo "  make run         - Run the application"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Clean cache and temporary files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docker-up    - Start with docker-compose"
	@echo "  make docker-down - Stop docker-compose"
	@echo "  make deploy      - Deploy to production (requires configuration)"

install:
	pip install -r requirements.txt

dev: install
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file from env.example"; \
		echo "Please edit .env with your configuration"; \
	fi
	@mkdir -p backend/uploads frontend/static/qr
	@touch backend/uploads/.gitkeep frontend/static/qr/.gitkeep
	@echo "Development environment ready!"

run:
	python run.py

test:
	@echo "Running tests..."
	cd backend && python -m pytest test_*.py -v || python test_app.py

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "Cleaned cache and temporary files"

docker-build:
	docker build -t swasthya-sampark .

docker-run:
	docker run -d \
		--name swasthya-sampark \
		-p 5000:5000 \
		-e SECRET_KEY=$$(python -c 'import secrets; print(secrets.token_hex(32))') \
		-v $$(pwd)/backend/health_system.db:/app/backend/health_system.db \
		-v $$(pwd)/backend/uploads:/app/backend/uploads \
		-v $$(pwd)/frontend/static/qr:/app/frontend/static/qr \
		swasthya-sampark

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

deploy:
	@echo "Deployment commands:"
	@echo "  For Heroku: git push heroku main"
	@echo "  For Docker: make docker-build && make docker-run"
	@echo "  For Gunicorn: gunicorn --config gunicorn_config.py wsgi:application"
	@echo "See DEPLOYMENT.md for detailed instructions"

