# 10 — Deploy on Oracle Cloud "Always Free" (≈ $0/month)

Oracle's Always Free tier includes a permanently-free **Ampere A1 (ARM)** VM — up to
4 cores / 24 GB RAM. That's plenty for the full stack (Postgres + Redis + API + web +
Caddy). All images build natively on ARM, so nothing in the app changes.

> Use the **Ampere (ARM)** shape, not the tiny AMD "Micro" (1 GB RAM is too small to
> build/run everything).

You'll also want a domain (even a free one) so Caddy can issue HTTPS.

---

## 1. Create the free account

1. Sign up at https://www.oracle.com/cloud/free/ → "Start for free".
2. A credit card is required for identity verification; **Always Free resources are
   never charged**. (To be safe, you can stay on the Free plan and not upgrade.)
3. **Pick your home region carefully** — it's permanent, and Ampere capacity varies by
   region. Choose one geographically near you.

## 2. Create the Ampere VM

Console → **Compute → Instances → Create instance**:

- **Image:** Canonical **Ubuntu 22.04** (or 24.04).
- **Shape:** Change shape → **Ampere → VM.Standard.A1.Flex**. Set e.g. **2 OCPU / 12 GB**
  (all within the free 4 OCPU / 24 GB).
- **SSH keys:** upload your public key (or let it generate one and download the private key).
- **Networking:** keep "Assign a public IPv4 address" checked.
- Create. Note the **public IP**.

> **"Out of host capacity"?** Common with Ampere. Try: fewer OCPUs (1 OCPU / 6 GB),
> a different Availability Domain, or retry later (capacity frees up). It's worth the
> persistence — the VM is free forever.

## 3. Open ports in Oracle's cloud firewall (the usual gotcha)

Oracle blocks inbound traffic at the network level by default.

Console → your instance → **Virtual Cloud Network → Security Lists → default** →
**Add Ingress Rules**:

| Source CIDR | Protocol | Dest. port |
|-------------|----------|------------|
| 0.0.0.0/0   | TCP      | 80         |
| 0.0.0.0/0   | TCP      | 443        |

(Port 22 is already open.)

## 4. Point a domain at the VM

Add a DNS **A record**: `app.yourdomain.com → YOUR_PUBLIC_IP`.

No domain? Get a free subdomain at https://www.duckdns.org and point it at the IP —
Caddy issues HTTPS for it just the same.

## 5. Set up the server

SSH in (Oracle Ubuntu's default user is `ubuntu`):

```bash
ssh ubuntu@YOUR_PUBLIC_IP

# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu      # then log out/in so `docker` works without sudo

# Open 80/443 in the instance's local firewall (Oracle Ubuntu ships iptables rules)
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo apt-get update && sudo apt-get install -y iptables-persistent git
sudo netfilter-persistent save
```

## 6. Deploy the app

```bash
git clone https://github.com/<your-username>/investing-app.git
cd investing-app
cp .env.example .env
nano .env
```

Fill in `.env`:

```ini
DOMAIN=app.yourdomain.com
APP_BASE_URL=https://app.yourdomain.com
JWT_SECRET=<openssl rand -hex 32>
POSTGRES_PASSWORD=<a strong password>
REGISTRATION_ENABLED=true          # lock down after you register (step 8)
FINNHUB_API_KEY=<your key>          # live market data
# Optional: ANTHROPIC_API_KEY=... + AI_DECISION_MODE=empowered
```

Launch (first build on ARM takes a few minutes):

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Caddy auto-issues a Let's Encrypt cert. Open **https://app.yourdomain.com** and register.

```bash
curl -s https://app.yourdomain.com/api/v1/health
docker compose -f docker-compose.prod.yml logs -f caddy   # watch cert issuance
```

## 7. (Optional) demo data

```bash
docker compose -f docker-compose.prod.yml exec api python -m app.db.seed_demo
```

## 8. Lock down registration

After your account exists:

```bash
nano .env     # REGISTRATION_ENABLED=false
docker compose -f docker-compose.prod.yml up -d api
```

---

## Operating it

Same as the generic VPS guide — see [09-deploy-vps.md](09-deploy-vps.md) "Operating it"
and "Security checklist" (updates, logs, DB backups, restart-on-reboot). The stack uses
`restart: unless-stopped`, so it survives reboots automatically.

**Keep it free:** only use Always-Free-eligible resources (the Ampere VM + its boot
volume are free). Don't add paid load balancers, extra block volumes beyond the free
200 GB, etc. Oracle's billing page shows $0 as long as you stay within Always Free.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Site unreachable | Both firewalls must allow 80/443: Oracle **Security List** *and* the VM's **iptables** (step 3 + step 5). |
| Caddy cert fails | DNS A record must resolve to the VM IP and ports 80/443 must be reachable before Caddy can validate. |
| Build killed / OOM | You're on the 1 GB AMD micro shape — recreate as **Ampere** with ≥6 GB. |
| `docker: permission denied` | Log out/in after `usermod -aG docker`, or prefix with `sudo`. |
