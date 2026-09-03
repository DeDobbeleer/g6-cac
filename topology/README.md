# Topology / Fleet code archive

This directory contains code that was **archived on 2026-09-03** when the
Fleet/Topology concept was removed from the active code path of
`cac_configmgr`.

Topology will return later via a separate PR-FAQ (SIM topology, planned for
Q4). Until then, the active code path only supports hierarchical template
resolution (repos, routingPolicies, etc.) without any fleet/topology coupling.

## Contents

- `fleet.py` — the full Fleet model family (`Tag`, `Node`/`AIO`/`DataNode`/
  `SearchHead`, `DirectorConfig`, `Nodes`, `FleetSpec`, `Fleet`), previously
  at `src/cac_configmgr/models/fleet.py`.
- `test_models_fleet.py` — the fleet model unit tests, previously at
  `tests/test_models_fleet.py`.
- `demo-fleets/` — the demo `fleet.yaml` files that used to live next to each
  demo instance under `demo-configs/instances/`.

## What was removed from the active code

- The **Fleet model** (`src/cac_configmgr/models/fleet.py`) and its exports
  in `src/cac_configmgr/models/__init__.py`.
- **`TopologyInstance` / `fleetRef`**: renamed to `Instance`
  (`kind: Instance`), and the required `fleetRef` metadata field was dropped
  from `InstanceMetadata`.
- The **`plan` CLI command** (it was fleet-coupled: per-node payloads). It
  will return together with the topology PR-FAQ. A topology-free `resolve`
  command was added instead.
- **fleet.yaml loading** (`load_fleet` / `save_fleet` in
  `src/cac_configmgr/utils/yaml_utils.py`) and the `--fleet` / `--topology`
  options of the `validate` command.

## Restoring

When the topology PR-FAQ lands, move `fleet.py` back to
`src/cac_configmgr/models/fleet.py`, restore the exports, and reintroduce the
`fleetRef` link between instances and fleets.
