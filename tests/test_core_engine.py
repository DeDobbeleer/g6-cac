"""End-to-end tests for the template → API payload generation pipeline.

Covers the full ResolutionEngine flow (chain resolution, merge, interpolation,
payload filtering) on both synthetic chains and the real demo-configs tree.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

from cac_configmgr.core.engine import ResolutionEngine, filter_internal_ids
from cac_configmgr.core.resolver import (
    CircularDependencyError,
    TemplateNotFoundError,
)
from cac_configmgr.providers.conventions.director import DirectorAPIConvention
from cac_configmgr.utils import load_instance

DEMO_TEMPLATES_DIR = Path(__file__).parent.parent / "demo-configs" / "templates"
DEMO_INSTANCES_DIR = Path(__file__).parent.parent / "demo-configs" / "instances"

INTERNAL_KEYS = {"id", "action", "first", "last", "after", "before", "position"}


def _walk_dicts(obj: Any) -> Iterator[dict]:
    """Yield every dict found recursively in obj."""
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk_dicts(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_dicts(item)


def _write_template(directory: Path, name: str, extends: str | None, spec: str) -> None:
    """Write a minimal single-file ConfigTemplate into directory."""
    directory.mkdir(parents=True, exist_ok=True)
    extends_line = f"  extends: {extends}\n" if extends else ""
    (directory / "resources.yaml").write_text(
        f"""apiVersion: cac-configmgr.io/v1
kind: ConfigTemplate
metadata:
  name: {name}
{extends_line}spec:
{spec}"""
    )


@pytest.fixture
def synthetic_chain(tmp_path: Path) -> tuple[Path, Any]:
    """Build a 3-level chain: golden (root) → mid → instance."""
    _write_template(
        tmp_path / "level1/golden",
        "golden",
        None,
        """  vars:
    mount: /opt/immune/storage
    retention_default: 90
  repos:
  - name: repo-a
    hiddenrepopath:
    - _id: primary
      path: '{{mount}}'
      retention: '{{retention_default}}'
""",
    )
    _write_template(
        tmp_path / "level2/mid",
        "mid",
        "level1/golden",
        """  repos:
  - name: repo-a
    hiddenrepopath:
    - _id: primary
      retention: 30
    - _id: warm
      path: /mnt/warm
      retention: 365
""",
    )
    from cac_configmgr.models.template import Instance

    instance = Instance(
        **{
            "apiVersion": "cac-configmgr.io/v1",
            "kind": "Instance",
            "metadata": {"name": "inst", "extends": "level2/mid"},
            "spec": {},
        }
    )
    return tmp_path, instance


class TestChainResolution:
    """Inheritance chain building via TemplateResolver."""

    def test_chain_order_root_to_leaf(self, synthetic_chain):
        templates_dir, instance = synthetic_chain
        resolved = ResolutionEngine(templates_dir).resolve(instance)

        names = [t.metadata.name for t in resolved.source_chain.templates]
        assert names == ["golden", "mid", "inst"]

    def test_circular_dependency_detected(self, tmp_path: Path):
        _write_template(tmp_path / "x/a", "a", "x/b", "  vars: {}\n")
        _write_template(tmp_path / "x/b", "b", "x/a", "  vars: {}\n")

        from cac_configmgr.models.template import Instance

        instance = Instance(
            **{
                "apiVersion": "cac-configmgr.io/v1",
                "kind": "Instance",
                "metadata": {"name": "a", "extends": "x/b"},
                "spec": {},
            }
        )
        with pytest.raises(CircularDependencyError):
            ResolutionEngine(tmp_path).resolve(instance)

    def test_template_not_found(self, tmp_path: Path):
        from cac_configmgr.models.template import Instance

        instance = Instance(
            **{
                "apiVersion": "cac-configmgr.io/v1",
                "kind": "Instance",
                "metadata": {
                    "name": "orphan",
                    "extends": "does/not-exist",
                },
                "spec": {},
            }
        )
        with pytest.raises(TemplateNotFoundError):
            ResolutionEngine(tmp_path).resolve(instance)


class TestMergeAndInterpolation:
    """Resource merge and variable interpolation through the engine."""

    def test_field_level_merge_inherits_parent_values(self, synthetic_chain):
        templates_dir, instance = synthetic_chain
        resolved = ResolutionEngine(templates_dir).resolve(instance)

        repo = resolved.get_resource("repos", "repo-a")
        assert repo is not None
        tiers = {t["_id"]: t for t in repo["hiddenrepopath"]}
        # primary: retention overridden by mid, path inherited from golden
        assert tiers["primary"]["retention"] == 30
        assert tiers["primary"]["path"] == "/opt/immune/storage"
        # warm: appended by mid
        assert tiers["warm"]["path"] == "/mnt/warm"
        assert tiers["warm"]["retention"] == 365

    def test_interpolation_preserves_types(self, synthetic_chain):
        templates_dir, instance = synthetic_chain
        resolved = ResolutionEngine(templates_dir).resolve(instance)

        repo = resolved.get_resource("repos", "repo-a")
        retention = repo["hiddenrepopath"][0]["retention"]
        assert retention == 30
        assert isinstance(retention, int)


class TestApiPayload:
    """to_api_payload() output contract."""

    def test_no_internal_keys_anywhere(self, synthetic_chain):
        templates_dir, instance = synthetic_chain
        payload = ResolutionEngine(templates_dir).resolve(instance).to_api_payload()

        for d in _walk_dicts(payload):
            for key in d:
                assert not key.startswith("_"), f"internal key leaked: {key}"
                assert key not in INTERNAL_KEYS, f"ordering key leaked: {key}"

    def test_only_non_empty_resource_types(self, synthetic_chain):
        templates_dir, instance = synthetic_chain
        payload = ResolutionEngine(templates_dir).resolve(instance).to_api_payload()

        assert set(payload) == {"repos"}

    def test_filter_internal_ids_converts_none_to_string(self):
        # Documented LogPoint API quirk: None must be sent as string "None"
        assert filter_internal_ids({"a": None}) == {"a": "None"}

    def test_filter_internal_ids_nested(self):
        obj = {"_id": "x", "items": [{"_action": "delete", "keep": 1, "first": True}]}
        assert filter_internal_ids(obj) == {"items": [{"keep": 1}]}


@pytest.mark.skipif(not DEMO_TEMPLATES_DIR.exists(), reason="demo-configs not present")
class TestDemoConfigsEndToEnd:
    """Full pipeline against the real demo-configs tree."""

    def _resolve(self, instance_path: Path):
        instance = load_instance(instance_path)
        return ResolutionEngine(DEMO_TEMPLATES_DIR).resolve(instance)

    def test_bank_a_prod_chain(self):
        resolved = self._resolve(DEMO_INSTANCES_DIR / "banks/bank-a/prod/instance.yaml")
        names = [t.metadata.name for t in resolved.source_chain.templates]
        assert names == [
            "golden-base",
            "golden-pci-dss",
            "acme-base",
            "acme-banking-addon",
            "acme-banking-premium",
            "bank-a-prod",
        ]

    def test_bank_a_prod_repo_secu_merge(self):
        resolved = self._resolve(DEMO_INSTANCES_DIR / "banks/bank-a/prod/instance.yaml")
        repo = resolved.get_resource("repos", "repo-secu")
        assert repo is not None

        tiers = {t["_id"]: t for t in repo["hiddenrepopath"]}
        # primary: retention overridden by acme-base, path inherited from golden-base
        assert tiers["primary"]["retention"] == 90
        assert tiers["primary"]["path"] == "/opt/immune/storage"
        # nfs-tier: added by the instance itself
        assert tiers["nfs-tier"]["retention"] == 3650
        assert tiers["nfs-tier"]["path"] == "/opt/immune/storage-nfs"

    def test_bank_a_prod_variables_merged(self):
        resolved = self._resolve(DEMO_INSTANCES_DIR / "banks/bank-a/prod/instance.yaml")
        assert resolved.variables["client_code"] == "BANKA"
        assert resolved.variables["mount_point"] == "/opt/immune/storage"

    @pytest.mark.parametrize(
        "instance_yaml",
        sorted(DEMO_INSTANCES_DIR.glob("*/*/*/instance.yaml")),
        ids=lambda p: p.parent.relative_to(DEMO_INSTANCES_DIR).as_posix(),
    )
    def test_all_instances_resolve_to_clean_payload(self, instance_yaml: Path):
        payload = self._resolve(instance_yaml).to_api_payload()

        assert payload, f"{instance_yaml}: empty payload"

        # No internal/ordering keys leak into the API payload
        for d in _walk_dicts(payload):
            for key in d:
                assert not key.startswith("_"), f"internal key leaked: {key}"
                assert key not in INTERNAL_KEYS, f"ordering key leaked: {key}"

        # Every repo tier must have a usable path and a typed int retention.
        # Guards against the "path": "None" artifact seen in legacy dumps.
        for repo in payload.get("repos", []):
            for tier in repo["hiddenrepopath"]:
                path = tier.get("path")
                assert isinstance(path, str) and path != "None" and path.startswith("/"), (
                    f"{instance_yaml}: repo {repo['name']} has invalid tier path {path!r}"
                )
                assert isinstance(tier.get("retention"), int), (
                    f"{instance_yaml}: repo {repo['name']} retention not an int"
                )

    @pytest.mark.parametrize(
        "instance_yaml",
        sorted(DEMO_INSTANCES_DIR.glob("*/*/*/instance.yaml")),
        ids=lambda p: p.parent.relative_to(DEMO_INSTANCES_DIR).as_posix(),
    )
    def test_payload_resources_have_api_name_fields(self, instance_yaml: Path):
        payload = self._resolve(instance_yaml).to_api_payload()
        convention = DirectorAPIConvention()

        for resource_type, resources in payload.items():
            name_field = convention.get_name_field(resource_type)
            for resource in resources:
                assert resource.get(name_field), (
                    f"{instance_yaml}: {resource_type} resource missing '{name_field}': {resource}"
                )
