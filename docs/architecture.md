# SportsIntel AI Architecture

## Principles

1. External providers never feed product features directly.
2. All data passes through ingestion adapters into a canonical sports data lake.
3. LMS is a first-class strategy domain.
4. AI explains grounded analytics; it does not invent probabilities.
5. No backward compatibility is required before the first production release.

## Initial bounded contexts

- Sports Catalog
- NFL Schedule and Game Data
- Player and Injury Data
- Market and Odds Data
- LMS Pools and Entries
- LMS Recommendation Engine
- Provider Ingestion and Audit
- AI Explanation
