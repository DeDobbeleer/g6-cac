# Audit Plan Template

**Active Audit**: See [audits/2026-02-27-phase1-complete.md](audits/2026-02-27-phase1-complete.md) for the completed Phase 1 audit.

**Audit History**: See [audits/README.md](audits/README.md) for all past audits.

---

## Purpose

This file serves as a template for future audits. When starting a new audit:
1. Copy this file to `audits/YYYY-MM-DD-audit-scope.md`
2. Update the audit scope and checklist
3. Execute all verification steps
4. Record results

## Pre-Audit Checklist

Before starting audit:
- [ ] Define audit scope (which specs, which code areas)
- [ ] Date the audit file
- [ ] Update status to "In Progress"

## Standard Verification Steps

### Step 1: Specification Verification
- [ ] Check spec matches implementation
- [ ] Verify examples work
- [ ] Check field names and aliases

### Step 2: Project Status Verification
- [ ] Verify completed items are done
- [ ] Verify "not started" items are indeed not started
- [ ] Update dates and commit references

### Step 3: ADR Verification
- [ ] All architectural decisions documented
- [ ] ADRs reflect current implementation

### Step 4: Documentation Verification
- [ ] README.md up to date
- [ ] AGENTS.md up to date
- [ ] All markdown files accurate

### Step 5: Code ↔ Specs Synchronization
- [ ] Pydantic models match specs
- [ ] Aliases correct
- [ ] Tests cover specifications

### Step 6: Final Report
- [ ] Document inconsistencies found
- [ ] List corrective actions
- [ ] Mark audit complete

## Post-Audit Actions

After completing audit:
1. Move completed audit to `audits/` directory
2. Update `audits/README.md` index
3. Create git commit
4. Merge to main if audit passes
