# LogPoint Director API Reference

**Project:** CaC-ConfigMgr  
**Last Updated:** 2026-02-27  
**Status:** Active reference for API implementation

---

## Overview

This document centralizes all LogPoint Director API documentation links for resources managed by CaC-ConfigMgr.

Base URL: `https://{api-server-host-name}/configapi/{pool_UUID}/{logpoint_identifier}`

---

## Core Resources

### 1. Repositories (Repos)
**API Endpoint:** `/Repo`

**Status:** P0 - Implemented ✅

**Documentation Links:**
- Create: POST `/Repo`
- Get: GET `/Repo/{id}`
- List: GET `/Repo`
- Edit: PUT `/Repo/{id}`
- Delete: DELETE `/Repo/{id}`

**Note:** Part of LogPoint core storage configuration.

---

### 2. Routing Policies
**API Endpoint:** `/RoutingPolicy`

**Status:** P0 - Implemented ✅

**Documentation Links:**
- [RoutingPolicies - Create/Edit/Get/List/Delete](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/routingpolicies)

**Key Fields:**
- `policy_name`: String (Policy name)
- `catch_all`: String (Default repo)
- `routing_criteria`: JSON Array
- `id`: String (Policy ID)

---

### 3. Processing Policies
**API Endpoint:** `/ProcessingPolicy`

**Status:** P0 - Implemented ✅

**Documentation Links:**
- [ProcessingPolicy - Create](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/processingpolicy)
- [ProcessingPolicy - Edit/Get/List/Delete](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/processingpolicy)

**Key Fields:**
```json
{
    "policy_name": "policyName",
    "routing_policy": "586cc3edd8aaa406f6fdc8e3",
    "norm_policy": "_logpoint",
    "enrich_policy": "57591a2cd8aaa41bfef54888"
}
```

**References:**
- Links to Routing Policy (by ID)
- Links to Normalization Policy (by name or "None")
- Links to Enrichment Policy (by ID or "None")

---

### 4. Normalization Policies
**API Endpoint:** `/NormalizationPolicy`

**Status:** P1 - Implemented ✅

**Documentation Links:**
- [NormalizationPolicy - Create](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/normalizationpolicy)
- [NormalizationPolicy - Edit/Get/List/Delete](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/normalizationpolicy)

**Key Fields:**
```json
{
    "name": "_test1",
    "normalization_packages": ["590ff8c1d8aaa47064d4f6fd"],
    "compiled_normalizer": "JSONCompiledNormalizer,WindowsXMLCompiledNormalizer"
}
```

**Related APIs:**
- NormalizationPackage - List: GET `/NormalizationPackage`
- NormalizationPackage - ListCompiledNormalizers: GET `/NormalizationPackage/ListCompiledNormalizers`

---

### 5. Enrichment Policies
**API Endpoint:** `/EnrichmentPolicy`

**Status:** P1 - Implemented ✅

**Documentation Links:**
- [EnrichmentPolicy - Create](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/enrichmentpolicy)
- [EnrichmentPolicy - Edit/Get/List/Delete](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/enrichmentpolicy)

**Key Fields:**
```json
{
    "name": "testPolicy",
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
```

**Related APIs:**
- EnrichmentSource - List: GET `/EnrichmentSource`

---

## Future Resources (Planned)

### 6. Devices / Log Sources
**API Endpoint:** `/Device` (TBD)

**Status:** P2 - Planned ⏳

**Note:** Device configuration for log collection.

---

### 7. Alert Rules
**API Endpoint:** `/AlertRule` (TBD)

**Status:** P2 - Planned ⏳

**Note:** Search Head configuration.

---

### 8. Dashboards
**API Endpoint:** `/Dashboard` (TBD)

**Status:** P2 - Planned ⏳

**Note:** Search Head visualization.

---

### 9. Log Collection Policies
**API Endpoint:** `/LogCollectionPolicy` (TBD)

**Status:** P2 - Planned ⏳

**Documentation Links:**
- [Log Collection Policies - UI Guide](https://docs.logpoint.com/docs/data-integration-guide/en/latest/Configuration/Log%20Collection%20Policies.html)

**Note:** Collector/Fetcher configuration per device.

---

## API Response Format

### Success Response
```json
{
    "status": "Success",
    "message": "/monitorapi/{pool_UUID}/{logpoint_identifier}/orders/{request_id}"
}
```

### Async Operation Pattern
All POST/PUT/DELETE operations return an async order ID. Poll the monitor endpoint for status.

---

## Field Name Conventions

### Current Project Alignment

| Resource | Field Name | API Format | Our Format | Status |
|----------|------------|------------|------------|--------|
| RoutingPolicy | name | `policy_name` | `policy_name` | ✅ Aligned |
| ProcessingPolicy | name | `policy_name` | `policy_name` | ✅ Aligned |
| NormalizationPolicy | name | `name` | `name` | ✅ Aligned |
| EnrichmentPolicy | name | `name` | `name` | ✅ Aligned |

### Important Notes
- API uses snake_case (`routing_policy`, `norm_policy`)
- Our YAML uses camelCase aliases (`routingPolicy`, `normalizationPolicy`)
- Reference fields often accept "None" as string for optional policies

---

## Related Documentation

- [LogPoint Director Console API Documentation](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/)
- [Data Integration Guide](https://docs.logpoint.com/docs/data-integration-guide/en/latest/)

---

## Validation Checklist

When implementing new resources, verify:
- [ ] API endpoint URL confirmed
- [ ] All mandatory fields documented
- [ ] Field names match API (not UI)
- [ ] Reference fields format (ID vs Name)
- [ ] Optional fields accept "None" string
- [ ] Async operation pattern implemented
- [ ] Example payload tested against API

---

## Update History

| Date | Change | Author |
|------|--------|--------|
| 2026-02-27 | Initial creation with NP, EP, PP, RP, Repo links | CaC Team |
