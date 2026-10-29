# Evolving Support Team — portal

Next.js (JavaScript) ops console for the self-evolving support team.

```bash
# 1. backend (repo root)
uv run python -m eat.os_app        # serves http://localhost:7777

# 2. portal
cd ui
cp .env.example .env.local         # optional: EAT_API_URL, OS_SECURITY_KEY
npm install
npm run dev                        # http://localhost:3000
```

All browser calls go to `/api/*`, which a route handler proxies (SSE included) to
`${EAT_API_URL}/ui/*`, adding `Authorization: Bearer $OS_SECURITY_KEY` server-side.
