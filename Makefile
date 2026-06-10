run-demo:
	DEMO_MODE=true uvicorn api.main:app --reload --port 8000 &
	cd web-ui && npm run dev

run-api:
	DEMO_MODE=true uvicorn api.main:app --reload --port 8000

run-ui:
	cd web-ui && npm run dev

test:
	pytest tests/ -v

build:
	docker build -t canary-whisperer .
