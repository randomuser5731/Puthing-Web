# Puthing Around - Secret Universe (Roblox)

The cipher awaits. A relic from the forgotten dimension.

Wordle-style secret code guessing with dual backend: local (SQLite) for development, or Supabase for the collective consciousness.

## Structure

```
.
├── puthing_server.py        # Local server with SQLite (development)
├── index.html               # Web interface (fallback to Supabase)
├── .vscode/
│   └── mcp.json           # MCP client configuration
└── supabase/
    ├── migrations/        # The ancient schema
    └── functions/         # Edge Functions (the ritual gateways)
```

## Development

```bash
# Awaken the cipher
python puthing_server.py init <secret-code>

# Open the portal
python puthing_server.py serve
# Available at http://localhost:8787

# Consult the records
python puthing_server.py stats

# Alter reality
python puthing_server.py set-code <new-code>
```

## Production (Supabase)

Apply migrations to the void. Deploy the ritual gateways.

## Endpoints

- `POST /api/verify` — channel your guess into the cipher
- `GET /api/stats` — consult the archives