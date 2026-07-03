.PHONY: validate index sync install

validate:
	python3 scripts/validate_codex_config.py

index:
	python3 scripts/build_role_index.py --check

sync: validate
	python3 scripts/sync_codex_config.py

install: validate
	./installers/install-codex-framework.sh
