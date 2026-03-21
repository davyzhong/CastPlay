# QA Pre-Release Checklist: Playlist Scheduling

**Purpose**: Validate requirements quality before release - testing if requirements are complete, clear, and testable
**Created**: 2026-03-16
**Feature**: [spec.md](../spec.md)
**Depth**: Lightweight (~18 items)
**Audience**: QA (pre-release validation)

---

## Requirement Completeness

- [ ] CHK001 - Are all 5 user stories mapped to testable functional requirements? [Completeness, Spec §User Scenarios]
- [ ] CHK002 - Are error handling requirements defined for invalid time ranges (end < start)? [Completeness, Spec §FR-001]
- [ ] CHK003 - Are requirements specified for the "no active schedule" fallback behavior? [Gap, Spec §Edge Cases]
- [ ] CHK004 - Are data validation requirements documented for the days_of_week bitmask (1-127)? [Completeness, Spec §FR-002]

## Requirement Clarity

- [ ] CHK005 - Is "within 5 seconds" in SC-002 defined as server-side evaluation or device-side switch? [Clarity, Spec §SC-002]
- [ ] CHK006 - Is "first assigned playlist" for fallback explicitly defined (by creation order, by ID, by assignment order)? [Ambiguity, Spec §Edge Cases]
- [ ] CHK007 - Are the priority and conflict resolution rules unambiguously defined when multiple schedules match? [Clarity, Spec §US5-AC3]

## Requirement Consistency

- [ ] CHK008 - Do time range requirements align between FR-001 (single calendar day) and Edge Cases (overnight not supported)? [Consistency, Spec §FR-001 vs §Edge Cases]
- [ ] CHK009 - Are conflict warning requirements consistent between FR-010 (warn) and US5-AC2 (allow save after confirmation)? [Consistency, Spec §FR-010 vs §US5]

## Acceptance Criteria Quality

- [ ] CHK010 - Can SC-001 "under 30 seconds" be objectively measured with a defined task flow? [Measurability, Spec §SC-001]
- [ ] CHK011 - Can SC-005 "90% satisfaction" be measured with a defined survey methodology? [Measurability, Spec §SC-005]
- [ ] CHK012 - Are all acceptance scenarios in Given-When-Then format complete with preconditions? [Acceptance Criteria, Spec §User Scenarios]

## Scenario Coverage

- [ ] CHK013 - Are requirements defined for device reconnection after extended offline period (days)? [Coverage, Gap]
- [ ] CHK014 - Are requirements specified for schedule evaluation during server restart? [Coverage, Gap]
- [ ] CHK015 - Are concurrent schedule modification requirements documented (multiple users editing same device)? [Coverage, Gap]

## Edge Case Coverage

- [ ] CHK016 - Are requirements defined for playlist deletion while schedule is active? [Edge Case, Spec §Edge Cases - partial]
- [ ] CHK017 - Is the behavior specified for daylight saving time transitions documented as testable requirements? [Edge Case, Spec §Edge Cases]

## Dependencies & Assumptions

- [ ] CHK018 - Is the assumption "existing APScheduler can be extended" validated with capacity requirements? [Assumption, Spec §Assumptions]

---

## Summary

| Category | Items | Critical |
|----------|-------|----------|
| Requirement Completeness | CHK001-004 | CHK002, CHK003 |
| Requirement Clarity | CHK005-007 | CHK006 |
| Requirement Consistency | CHK008-009 | - |
| Acceptance Criteria Quality | CHK010-012 | CHK011 |
| Scenario Coverage | CHK013-015 | CHK014 |
| Edge Case Coverage | CHK016-017 | CHK016 |
| Dependencies & Assumptions | CHK018 | CHK018 |

**Total Items**: 18

## Notes

- Items marked as [Gap] indicate potentially missing requirements that should be verified before release
- Items marked as [Ambiguity] require clarification to enable testable acceptance criteria
- This checklist validates REQUIREMENTS QUALITY - not implementation correctness
