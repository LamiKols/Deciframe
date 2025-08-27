.PHONY: route-report route-apply route-aliases

route-report:
	python scripts/route_doctor.py --report

route-apply:
	python scripts/route_doctor.py --apply --threshold=85

route-aliases:
	python scripts/generate_route_aliases.py > ALIAS_ROUTES.py && echo "ALIAS_ROUTES.py generated."