# Release 0.9 — Team Intelligence, Search, and Watchlist

## Added

- Authenticated Team Intelligence API and UI for all NFL teams.
- Team detail pages with strategy edges, matchup context, factors, and Assistant prompts.
- Global search across teams and games in the application top bar.
- Persistent per-user watchlists for teams and games.
- Watchlist controls on team and Game Intelligence pages.
- Dedicated Watchlist workspace.

## API

- `GET /api/v1/teams`
- `GET /api/v1/teams/{abbreviation}`
- `GET /api/v1/search?q=...`
- `GET /api/v1/watchlist`
- `POST /api/v1/watchlist`
- `DELETE /api/v1/watchlist/{item_id}`

The application startup creates the new `watchlist_items` table automatically.
