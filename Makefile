.PHONY: route-report route-apply route-aliases

route-report:
        python scripts/route_doctor.py --report

route-apply:
        python scripts/route_doctor.py --apply --threshold=85

route-aliases:
        python scripts/generate_route_aliases.py > ALIAS_ROUTES.py && echo "ALIAS_ROUTES.py generated."

# Performance and Security Testing
perf: ## Run performance tests
        PERF_TTFB_MS=${PERF_TTFB_MS:-800} PERF_RESP_MAX_KB=${PERF_RESP_MAX_KB:-250} python -m pytest tests/perf -v

security: ## Run security tests  
        python -m pytest tests/security -v

# Database Operations
backup-db: ## Create database backup (engine-agnostic)
        python scripts/db_backup.py

# Release Management
release-gate: ## Run comprehensive release gate checks
        python scripts/release_gate.py

# UI Testing
sweep: ## Run comprehensive UI sweep testing
        python scripts/ui_sweep.py