.PHONY: install dev build test fe-% be-%
install: ; cd frontend && pnpm install
dev:                 ## run backend stack + frontend
	cd backend && docker compose up -d
	cd frontend && pnpm dev
fe-%: ; cd frontend && pnpm $*
be-up: ; cd backend && docker compose up -d
be-test: ; cd backend && pytest -q
