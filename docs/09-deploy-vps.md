# 09 — Deploy to a VPS (always-on, HTTPS)

Host the app on a small Linux VPS with Docker + automatic HTTPS via Caddy. Cost is
~$4–6/month. Only ports 80/443 (and SSH) are exposed; everything else stays internal.

What you'll need: a VPS (Hetzner / DigitalOcean / Vultr…), a domain you control, and
your API keys.

---

## 1. Create the server

- Provider: **Hetzner CX22** (~€4) or **DigitalOcean $6 droplet**. Ubuntu 24.04 LTS.
- SSH in: `ssh root@YOUR_SERVER_IP`

## 2. Point your domain at it

Add a DNS **A record**: `app.yourdomain.com → YOUR_SERVER_IP`. (Caddy needs this to
issue the TLS certificate.) No domain? A free subdomain from [DuckDNS](https://www.duckdns.org)
works too.

## 3. Install Docker + a firewall

```bash
curl -fsSL https://get.docker.com | sh
apt-get update && apt-get install -y ufw git
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw --force enable
```

## 4. Get the code

```bash
git clone https://github.com/<your-username>/investing-app.git
cd investing-app
```

(Private repo? Use a deploy key or `gh auth login`, or clone over SSH.)

## 5. Configure secrets

```bash
cp .env.example .env
nano .env
```

Set at minimum:

```ini
DOMAIN=app.yourdomain.com
APP_BASE_URL=https://app.yourdomain.com
JWT_SECRET=<paste: openssl rand -hex 32>
POSTGRES_PASSWORD=<a strong password>
REGISTRATION_ENABLED=true          # for now; lock down in step 7
FINNHUB_API_KEY=<your key>          # live market data
# Optional: ANTHROPIC_API_KEY=... + AI_DECISION_MODE=empowered  (Claude-powered)
# Optional: NTFY_TOPIC=... / TELEGRAM_BOT_TOKEN=... + TELEGRAM_CHAT_ID=...
```

`.env` is gitignored — it never goes back to GitHub.

## 6. Launch

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Caddy fetches a Let's Encrypt cert automatically (give it ~30s on first boot). Then
open **https://app.yourdomain.com** and register your account.

Check it's healthy:
```bash
curl -s https://app.yourdomain.com/api/v1/health
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f caddy   # watch cert issuance
```

## 7. Lock down registration (important for a public URL)

After you've created your account, stop strangers from signing up:

```bash
nano .env            # set REGISTRATION_ENABLED=false
docker compose -f docker-compose.prod.yml up -d api
```

Now `/auth/register` returns 403; only you can log in.

## 8. Optional demo data

```bash
docker compose -f docker-compose.prod.yml exec api python -m app.db.seed_demo
```

---

## Operating it

```bash
# Update to the latest code
git pull
docker compose -f docker-compose.prod.yml up -d --build

# Logs / status
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml ps

# Backup the database
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U investing investing > backup-$(date +%F).sql

# Stop / start
docker compose -f docker-compose.prod.yml down      # keeps data (named volumes)
docker compose -f docker-compose.prod.yml up -d
```

`restart: unless-stopped` means the stack comes back automatically after a reboot.

## Security checklist

- [x] Strong `JWT_SECRET` and `POSTGRES_PASSWORD` (not the defaults).
- [x] `REGISTRATION_ENABLED=false` after creating your account.
- [x] Firewall: only 22/80/443 open (`ufw status`).
- [ ] Optional: SSH key-only login, disable root password, set up `unattended-upgrades`.
- [ ] Rotate the Finnhub/Anthropic keys if they were ever shared.

## Cost notes

The VPS is the only fixed cost. Market data (Finnhub free tier) is free; Claude usage is
pay-per-use — see [08-runbook.md](08-runbook.md) §7 for controls (freshness gate, model
tiering, deterministic fallback). With `AI_DECISION_MODE=deterministic` there is **no**
LLM cost at all.

## Alternatives

- **Private only (no public URL):** install [Tailscale](https://tailscale.com) on the
  VPS (or your Mac) and skip Caddy/DNS — reach the app over the private Tailscale IP
  from your phone. Most secure for personal use.
- **Managed PaaS:** Railway/Render/Fly can run the images from GitHub, but you'll wire
  up managed Postgres/Redis and per-service config yourself.
