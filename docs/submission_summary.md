# SIH26191 Submission Summary

## Problem
Disaster authorities need more than a map: they must identify which habitations are most at risk, understand why, decide who moves first, identify safe destinations, verify carrying capacity and avoid double-booking limited shelters.

## Solution
A human-in-the-loop multi-hazard decision-support platform combining GIS exposure, transparent hazard profiles, population exposure, vulnerability, evacuation difficulty, shelter carrying capacity, routing and relocation allocation.

## Demonstration scope
The presentation dataset covers Puri, Guwahati and Chennai as representative Indian high-risk contexts. The geographies are real; bundled operational values and hazard footprints are synthetic DEMO scenarios. This is not presented as a definitive national risk ranking.

## Key differentiators
- Flood, Cyclone, Landslide, Earthquake, Drought and Combined profiles
- transparent hazard-indicator contributions and completeness
- frozen explainable final risk equation and visible risk drivers
- experimental coordination zones kept separate from decision logic
- limiting-resource shelter capacity
- capacity-safe multi-shelter split
- system-wide allocation preventing double booking
- optional safety-gated global network-flow optimizer
- road-aware routing with offline fallback
- PDF action-plan export
- custom CSV validation/template workflow
- NDMA SACHET-compatible alert infrastructure
- optional cached USGS earthquake context
- LIVE/CACHED/DEMO provenance handling
- offline-first demo and automated preflight gate

## Judge-safe technical claim
The multi-hazard profile weights are transparent prototype assumptions. They demonstrate the platform architecture and explainability, while authoritative deployments can replace them with source-specific calibrated mappings without changing the risk/capacity/relocation interfaces.

## One-line pitch
**The system turns multi-hazard GIS and population data into explainable red-zone priorities and capacity-aware relocation recommendations for disaster-management authorities.**
