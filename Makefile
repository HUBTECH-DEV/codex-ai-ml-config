.PHONY: validate schemas index test compile secrets ci install sync sync-status \
	sync-fetch sync-pull sync-commit sync-push

PYTHON ?= python3
HUBICG_BRANCH ?= beta

validate:
	$(PYTHON) scripts/validate_codex_config.py

schemas:
	$(PYTHON) scripts/validate_schemas.py

index:
	$(PYTHON) scripts/build_role_index.py --check

test:
	$(PYTHON) -m unittest discover -s tests -v

compile:
	$(PYTHON) -m compileall -q scripts tests

secrets:
	$(PYTHON) scripts/scan_secrets.py

ci: validate schemas index test compile secrets

install: validate
	./installers/install-codex-framework.sh

# Legacy-safe alias: `make sync` only reports local/cached status.
sync: sync-status

sync-status: validate
	$(PYTHON) scripts/sync_codex_config.py --branch $(HUBICG_BRANCH)

sync-fetch: validate
	$(PYTHON) scripts/sync_codex_config.py --branch $(HUBICG_BRANCH) --fetch

sync-pull: validate
	$(PYTHON) scripts/sync_codex_config.py --branch $(HUBICG_BRANCH) --pull

sync-commit: validate
	$(PYTHON) scripts/sync_codex_config.py --branch $(HUBICG_BRANCH) --commit

sync-push: validate
	$(PYTHON) scripts/sync_codex_config.py --branch $(HUBICG_BRANCH) --push
