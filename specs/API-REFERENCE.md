# LogPoint Director API Reference

**Project:** CaC-ConfigMgr  
**Last Updated:** 2026-02-27  
**Status:** Active reference for API implementation

---

## Overview

This document centralizes all LogPoint Director API documentation links for resources managed by CaC-ConfigMgr.

**Base URL:** `https://{api-server-host-name}/configapi/{pool_UUID}/{logpoint_identifier}`

**Authentication:** Bearer token via `Authorization` header

**Async Pattern:** All POST/PUT/DELETE operations return a `request_id` for polling via `/monitorapi/{pool_UUID}/{logpoint_identifier}/orders/{request_id}`

---

## Core Resources

### 1. Repositories (Repos)

**Status:** P0 - Implemented ✅

**API Endpoints:**
| Operation | Method | URL |
|-----------|--------|-----|
| Create | POST | `/configapi/{pool_UUID}/{logpoint_identifier}/Repo` |
| Get | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/Repo/{id}` |
| List | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/Repo` |
| Edit | PUT | `/configapi/{pool_UUID}/{logpoint_identifier}/Repo/{id}` |
| Delete | DELETE | `/configapi/{pool_UUID}/{logpoint_identifier}/Repo/{id}` |

**Request/Response Format:**
```json
// Create Request
{
    "data": {
        "name": "repo-secu",
        "path": "/opt/immune/storage",
        "retention": 365
    }
}

// List Response
[
    {
        "id": "590961d2d8aaa45aa5501cdd",
        "name": "repo-secu",
        "path": "/opt/immune/storage",
        "retention": 365,
        "active": true
    }
]
```

**Key Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | ✅ | Repository name |
| `path` | String | ✅ | Storage path |
| `retention` | Integer | ✅ | Retention days |
| `id` | String | - | System-generated ID |
| `active` | Boolean | - | Status flag |

---

### 2. Routing Policies

**Status:** P0 - Implemented ✅

**Documentation:** https://docs.logpoint.com/director/director-apis/director-console-api-documentation/routingpolicies

**API Endpoints:**
| Operation | Method | URL |
|-----------|--------|-----|
| Create | POST | `/configapi/{pool_UUID}/{logpoint_identifier}/RoutingPolicy` |
| Get | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/RoutingPolicy/{id}` |
| List | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/RoutingPolicy` |
| Edit | PUT | `/configapi/{pool_UUID}/{logpoint_identifier}/RoutingPolicy/{id}` |
| Delete | DELETE | `/configapi/{pool_UUID}/{logpoint_identifier}/RoutingPolicy/{id}` |

**Request/Response Format:**
```json
// Create Request
{
    "data": {
        "policy_name": "rp-windows",
        "catch_all": "repo-system",
        "routing_criteria": [
            {
                "type": "KeyPresentValueMatches",
                "key": "EventType",
                "value": "Verbose",
                "repo": "repo-system-verbose",
                "drop": "store"
            }
        ]
    }
}

// List Response
[
    {
        "id": "590961d2d8aaa45aa5501cdd",
        "policy_name": "rp-windows",
        "catch_all": "repo-system",
        "routing_criteria": [...],
        "active": true
    }
]
```

**Key Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `policy_name` | String | ✅ | Policy name |
| `catch_all` | String | ✅ | Default repository |
| `routing_criteria` | Array | ✅ | Routing rules |
| `id` | String | - | System-generated ID |
| `active` | Boolean | - | Status flag |

**Routing Criterion Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | String | ✅ | Match type: KeyPresent, KeyPresentValueMatches |
| `key` | String | ✅ | Field to match |
| `value` | String | ❌ | Value to match (if applicable) |
| `repo` | String | ❌ | Destination repo (if not dropping) |
| `drop` | String | ✅ | Action: store, discard_raw, discard |

---

### 3. Processing Policies

**Status:** P0 - Implemented ✅

**Documentation:** https://docs.logpoint.com/director/director-apis/director-console-api-documentation/processingpolicy

**API Endpoints:**
| Operation | Method | URL |
|-----------|--------|-----|
| Create | POST | `/configapi/{pool_UUID}/{logpoint_identifier}/ProcessingPolicy` |
| Get | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/ProcessingPolicy/{id}` |
| List | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/ProcessingPolicy` |
| Edit | PUT | `/configapi/{pool_UUID}/{logpoint_identifier}/ProcessingPolicy/{id}` |
| Delete | DELETE | `/configapi/{pool_UUID}/{logpoint_identifier}/ProcessingPolicy/{id}` |

**Request/Response Format:**
```json
// Create Request
{
    "data": {
        "policy_name": "pp-windows",
        "routing_policy": "586cc3edd8aaa406f6fdc8e3",
        "norm_policy": "_logpoint",
        "enrich_policy": "57591a2cd8aaa41bfef54888"
    }
}

// With None values (no NP/EP)
{
    "data": {
        "policy_name": "pp-default",
        "routing_policy": "586cc3edd8aaa406f6fdc8e3",
        "norm_policy": "None",
        "enrich_policy": "None"
    }
}

// List Response
[
    {
        "id": "59099afa854ff52b6819a739",
        "policy_name": "pp-windows",
        "routing_policy": "590961d2d8aaa45aa5501ce2",
        "norm_policy": "_logpoint",
        "enrich_policy": "57591a2cd8aaa41bfef54888",
        "active": true
    }
]
```

**Key Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `policy_name` | String | ✅ | Policy name |
| `routing_policy` | String | ✅ | Routing Policy ID |
| `norm_policy` | String | ✅ | Normalization Policy name OR "None" |
| `enrich_policy` | String | ✅ | Enrichment Policy ID OR "None" |
| `id` | String | - | System-generated ID |
| `active` | Boolean | - | Status flag |

**Important:** Reference fields accept "None" (string) for optional policies.

---

### 4. Normalization Policies

**Status:** P1 - Implemented ✅

**Documentation:** https://docs.logpoint.com/director/director-apis/director-console-api-documentation/normalizationpolicy

**API Endpoints:**
| Operation | Method | URL |
|-----------|--------|-----|
| Create | POST | `/configapi/{pool_UUID}/{logpoint_identifier}/NormalizationPolicy` |
| Get | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/NormalizationPolicy/{id}` |
| List | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/NormalizationPolicy` |
| Edit | PUT | `/configapi/{pool_UUID}/{logpoint_identifier}/NormalizationPolicy/{id}` |
| Delete | DELETE | `/configapi/{pool_UUID}/{logpoint_identifier}/NormalizationPolicy/{id}` |

**Related APIs:**
| Operation | Method | URL |
|-----------|--------|-----|
| List Packages | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/NormalizationPackage` |
| List Compiled | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/NormalizationPackage/ListCompiledNormalizers` |

**Request/Response Format:**
```json
// Create Request
{
    "data": {
        "name": "np-windows",
        "normalization_packages": "567cf5487b011d9e45bda3f0,567cf5487b011d9e45bda3f3",
        "compiled_normalizer": "JSONCompiledNormalizer,WindowsXMLCompiledNormalizer"
    }
}

// List Response
[
    {
        "id": "590ff8e943fe06bbb6ddff7b",
        "name": "_LogPointAlerts",
        "normalization_packages": ["590ff8c1d8aaa47064d4f6fd"],
        "compiled_normalizer": "WindowsCompiledNormalizer",
        "active": true
    }
]
```

**Key Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | ✅ | Policy name |
| `normalization_packages` | String/Array | ❌ | Comma-separated IDs OR array |
| `compiled_normalizer` | String | ❌ | Comma-separated normalizer names |
| `id` | String | - | System-generated ID |
| `active` | Boolean | - | Status flag |

---

### 5. Enrichment Policies

**Status:** P1 - Implemented ✅

**Documentation:** https://docs.logpoint.com/director/director-apis/director-console-api-documentation/enrichmentpolicy

**API Endpoints:**
| Operation | Method | URL |
|-----------|--------|-----|
| Create | POST | `/configapi/{pool_UUID}/{logpoint_identifier}/EnrichmentPolicy` |
| Get | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/EnrichmentPolicy/{id}` |
| List | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/EnrichmentPolicy` |
| Edit | PUT | `/configapi/{pool_UUID}/{logpoint_identifier}/EnrichmentPolicy/{id}` |
| Delete | DELETE | `/configapi/{pool_UUID}/{logpoint_identifier}/EnrichmentPolicy/{id}` |

**Related APIs:**
| Operation | Method | URL |
|-----------|--------|-----|
| List Sources | GET | `/configapi/{pool_UUID}/{logpoint_identifier}/EnrichmentSource` |

**Request/Response Format:**
```json
// Create Request
{
    "data": {
        "name": "testPolicy",
        "description": "Enrichment Policy description",
        "specifications": [
            {
                "source": "test_odbc",
                "criteria": [
                    {
                        "type": "KeyPresents",
                        "key": "id",
                        "value": ""
                    }
                ],
                "rules": [
                    {
                        "category": "simple",
                        "source_key": "id",
                        "operation": "Equals",
                        "event_key": "id",
                        "type": "string",
                        "prefix": false
                    }
                ]
            }
        ]
    }
}

// List Response
[
    {
        "id": "574fb123d8aaa4625bfe2d23",
        "name": "testPolicy",
        "specifications": [
            {
                "source": "test_odbc",
                "criteria": [...],
                "rules": [...]
            }
        ],
        "description": "Enrichment Policy description"
    }
]
```

**Key Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | ✅ | Policy name |
| `description` | String | ❌ | Description |
| `specifications` | Array | ✅ | List of specifications |
| `id` | String | - | System-generated ID |

**Specification Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | String | ✅ | Enrichment source name |
| `criteria` | Array | ✅ | Matching criteria |
| `rules` | Array | ❌ | Enrichment rules |

**Criterion Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | String | ✅ | KeyPresents or KeyPresentsValueMatches |
| `key` | String | ✅ | Key to match |
| `value` | String | ❌ | Value to match |

**Rule Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | String | ✅ | simple or type_based |
| `source_key` | String | ✅ | Source field |
| `event_key` | String | ✅ | Event field |
| `operation` | String | ✅ | Equals |
| `type` | String | ❌ | ip, string, or num |
| `prefix` | Boolean | ❌ | true or false |

---

## API Response Patterns

### Success Response (All Operations)
```json
{
    "status": "Success",
    "message": "/monitorapi/{pool_UUID}/{logpoint_identifier}/orders/{request_id}"
}
```

### Async Operation Status
Poll: `GET /monitorapi/{pool_UUID}/{logpoint_identifier}/orders/{request_id}`

---

## Field Name Conventions

### API vs CaC-ConfigMgr Mapping

| Resource | API Field | Our YAML Field | Alias |
|----------|-----------|----------------|-------|
| RoutingPolicy | `policy_name` | `policy_name` | - |
| ProcessingPolicy | `policy_name` | `policy_name` | - |
| NormalizationPolicy | `name` | `name` | - |
| EnrichmentPolicy | `name` | `name` | - |
| References | `routing_policy` | `routing_policy` | `routingPolicy` |
| References | `norm_policy` | `normalization_policy` | `normalizationPolicy` |
| References | `enrich_policy` | `enrichment_policy` | `enrichmentPolicy` |

### Important Notes
- API uses snake_case for all fields
- Our YAML supports camelCase aliases for readability
- Reference fields accept "None" (string) for optional policies
- `normalization_packages` can be comma-separated string OR array
- `compiled_normalizer` is always comma-separated string

---

## Future Resources (Planned)

### 6. Devices / Log Sources
**Status:** P2 - Planned ⏳
**Expected Endpoint:** `/Device`
**Note:** Device configuration for log collection

### 7. Alert Rules
**Status:** P2 - Planned ⏳
**Expected Endpoint:** `/AlertRule`
**Note:** Search Head configuration

### 8. Dashboards
**Status:** P2 - Planned ⏳
**Expected Endpoint:** `/Dashboard`
**Note:** Search Head visualization

### 9. Log Collection Policies
**Status:** P2 - Planned ⏳
**Documentation:** https://docs.logpoint.com/docs/data-integration-guide/en/latest/Configuration/Log%20Collection%20Policies.html
**Note:** Collector/Fetcher configuration

### 10. Users and Permissions
**Status:** P3 - Planned ⏳
**Expected Endpoint:** `/User`, `/UserGroup`
**Note:** Authentication and authorization

### 11. System Settings
**Status:** P3 - Planned ⏳
**Expected Endpoint:** `/SystemSetting`
**Note:** SNMP, backup, etc.

---

## Validation Checklist

When implementing new resources, verify:
- [ ] API endpoint URL confirmed from official docs
- [ ] All mandatory fields documented with types
- [ ] Field names match API exactly (case-sensitive)
- [ ] Reference fields format (ID vs Name vs "None")
- [ ] Optional fields accept "None" string if applicable
- [ ] Async operation pattern implemented
- [ ] Example payload tested against actual API
- [ ] Related list APIs identified (for references)

---

## Related Documentation

- [LogPoint Director Console API Documentation](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/)
- [Data Integration Guide](https://docs.logpoint.com/docs/data-integration-guide/en/latest/)

---

## Update History

| Date | Change | Author |
|------|--------|--------|
| 2026-02-27 | Initial creation with complete API endpoints and field documentation | CaC Team |
