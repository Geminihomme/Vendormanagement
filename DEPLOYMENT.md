# Deployment Guide — Vendor Management Platform

This guide walks you through deploying your app so others can use it.
Written for a non-technical founder. Every step is explained.

---

## What You'll End Up With

After following this guide, you'll have:
- Your app live on the internet at a real URL
- A database storing your vendor data safely
- HTTPS (the padlock icon) protecting all data in transit
- Your team able to log in and use it from anywhere

---

## Option A: Deploy on Railway (Recommended)

Railway is the easiest option. It reads your Docker setup and handles everything.

### Step 1: Create a Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with your GitHub account
3. You'll get $5 of free credit to start

### Step 2: Push Your Code to GitHub

Your code is already on GitHub! Railway will read it from there.

### Step 3: Create a New Project on Railway

1. Click **"New Project"** in the Railway dashboard
2. Choose **"Deploy from GitHub Repo"**
3. Select your `Vendormanagement` repository
4. Railway will detect your `docker-compose.yml` automatically

### Step 4: Add a PostgreSQL Database

1. In your Railway project, click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway creates a managed database for you (with backups!)
3. Click on the database → **"Variables"** tab → copy the `DATABASE_URL`

### Step 5: Configure Environment Variables

Click on your **backend** service → **"Variables"** tab → add these:

| Variable | Value | How to Get It |
|----------|-------|---------------|
| `DATABASE_URL` | `postgresql://...` | Copy from Railway's PostgreSQL service |
| `JWT_SECRET_KEY` | Long random string | Run `openssl rand -hex 32` in your terminal |
| `CORS_ORIGINS` | `https://your-frontend-url.railway.app` | Railway gives you this URL after deploy |
| `ENVIRONMENT` | `production` | Type exactly this |

Click on your **frontend** service → **"Variables"** tab → add:

| Variable | Value |
|----------|-------|
| `REACT_APP_API_URL` | `https://your-backend-url.railway.app` |

### Step 6: Deploy

Railway deploys automatically when you push code. Click **"Deploy"** to trigger manually.

### Step 7: Add a Custom Domain (Optional)

1. Click on your frontend service → **"Settings"** → **"Custom Domain"**
2. Enter your domain (e.g., `app.yourcompany.com`)
3. Railway gives you a DNS record to add at your domain registrar
4. Railway handles HTTPS automatically

---

## Option B: Deploy on DigitalOcean App Platform

### Step 1: Create a DigitalOcean Account

1. Go to [digitalocean.com](https://www.digitalocean.com)
2. Sign up (you may get $200 free credit for 60 days)

### Step 2: Create a Managed Database

1. Go to **"Databases"** in the sidebar
2. Click **"Create Database Cluster"**
3. Choose **PostgreSQL 15**, pick the $15/month plan
4. Pick a region closest to your users (e.g., London for EMEA)
5. Note the connection string — you'll need it

### Step 3: Create an App

1. Go to **"Apps"** in the sidebar → **"Create App"**
2. Choose **"GitHub"** as the source
3. Select your repository
4. DigitalOcean will detect two services (backend and frontend)

### Step 4: Configure Each Service

**Backend service:**
- Set the Dockerfile path to `backend/Dockerfile`
- Add environment variables (same as Railway table above)
- Set the HTTP port to `8000`

**Frontend service:**
- Set the Dockerfile path to `frontend/Dockerfile`
- Add build argument: `REACT_APP_API_URL=https://your-backend-url`
- Set the HTTP port to `3000`

### Step 5: Deploy

Click **"Create Resources"**. DigitalOcean builds and deploys your app.

---

## Option C: Deploy on a VPS (Advanced)

This is for when you want full control. You rent a server and set everything up.

### Step 1: Rent a Server

1. Go to [DigitalOcean](https://www.digitalocean.com) or [Hetzner](https://www.hetzner.com)
2. Create a "Droplet" (DigitalOcean) or "Cloud Server" (Hetzner)
3. Choose **Ubuntu 22.04**, **2GB RAM**, **1 CPU** (~$6-12/month)
4. Add your SSH key for secure access

### Step 2: Install Docker on the Server

Connect to your server and run:

```bash
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt install docker-compose-plugin -y
```

### Step 3: Get Your Code on the Server

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/Vendormanagement.git
cd Vendormanagement
```

### Step 4: Configure Environment

```bash
# Copy the example config
cp .env.example .env

# Edit it with your real values
nano .env
```

Fill in:
- `DB_PASSWORD`: A strong password (20+ characters)
- `JWT_SECRET_KEY`: Run `openssl rand -hex 32` and paste the result
- `CORS_ORIGINS`: Your domain (e.g., `https://app.yourcompany.com`)
- `REACT_APP_API_URL`: Your backend URL (e.g., `https://api.yourcompany.com`)

### Step 5: Launch

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

This builds everything and starts it in the background.

### Step 6: Set Up HTTPS with Caddy (Reverse Proxy)

HTTPS is the padlock icon in the browser. It encrypts all data between
the user's browser and your server. Without it, passwords and financial
data could be intercepted.

Install Caddy (an easy reverse proxy that handles HTTPS automatically):

```bash
apt install -y caddy
```

Edit the Caddy config:

```bash
nano /etc/caddy/Caddyfile
```

Replace contents with:

```
app.yourcompany.com {
    reverse_proxy localhost:3000
}

api.yourcompany.com {
    reverse_proxy localhost:8000
}
```

Restart Caddy:

```bash
systemctl restart caddy
```

Caddy automatically gets HTTPS certificates from Let's Encrypt. Free and automatic.

### Step 7: Point Your Domain

At your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.):

1. Add an **A record** pointing `app.yourcompany.com` → your server's IP
2. Add an **A record** pointing `api.yourcompany.com` → your server's IP
3. Wait 5-30 minutes for DNS propagation

---

## Setting Up a Domain Name

### What Is a Domain?

A domain name is your app's address on the internet (like `yourcompany.com`).
Without it, users would need to type an IP address like `143.198.56.23` — not great.

### Where to Buy One

| Registrar | Cost | Notes |
|-----------|------|-------|
| [Cloudflare](https://www.cloudflare.com/products/registrar/) | ~$10/year | Cheapest, sells at cost, great DNS |
| [Namecheap](https://www.namecheap.com) | ~$10-15/year | User-friendly, good support |
| [Google Domains](https://domains.google) | ~$12/year | Simple, integrates with Google |
| [GoDaddy](https://www.godaddy.com) | ~$15/year | Most well-known, but upsells a lot |

### Recommended Setup

Buy one domain (e.g., `yourcompany.com`) and create two subdomains:

- `app.yourcompany.com` → Your frontend (what users see)
- `api.yourcompany.com` → Your backend (where data lives)

This is cleaner than putting everything on one domain and is how most
professional SaaS applications are structured.

### DNS Records to Add

At your domain registrar, add these DNS records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | `app` | Your server's IP address | 300 |
| A | `api` | Your server's IP address | 300 |

If using Railway or DigitalOcean, they'll give you a CNAME value instead:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | `app` | `your-app.railway.app` | 300 |
| CNAME | `api` | `your-api.railway.app` | 300 |

---

## After Deployment: Ongoing Maintenance

Deploying is like opening a store. But a store needs ongoing care:

### 1. Backups (Protecting Your Data)

**What:** Regular copies of your database, in case something goes wrong.
**Think of it as:** Photocopying all your paper files and storing them in a safe.

- **Railway/DigitalOcean managed databases:** Automatic daily backups included.
- **VPS:** Set up a cron job:
  ```bash
  # Add to crontab (runs daily at 2 AM)
  0 2 * * * docker exec vendormanagement-db-1 pg_dump -U vendorapp vendormanagement > /backups/db_$(date +\%Y\%m\%d).sql
  ```

### 2. Monitoring (Knowing When Things Break)

**What:** Getting notified if your app goes down.
**Think of it as:** A security camera for your store.

- **Free option:** [UptimeRobot](https://uptimerobot.com) — pings your `/health` endpoint every 5 minutes and emails you if it's down.
- Set it to check: `https://api.yourcompany.com/health`

### 3. Updates (Deploying New Features)

**What:** When you add features or fix bugs, you need to update the live app.
**Think of it as:** Printing a new edition of your book.

- **Railway/DigitalOcean:** Push to GitHub → automatically deploys.
- **VPS:** SSH in and run:
  ```bash
  cd Vendormanagement
  git pull
  docker compose -f docker-compose.prod.yml up -d --build
  ```

### 4. Security Updates

**What:** Keep your server software up to date.
**Think of it as:** Changing the locks on your store periodically.

- **Railway/DigitalOcean:** They handle this for you.
- **VPS:** Run monthly:
  ```bash
  apt update && apt upgrade -y
  ```

### 5. Log Monitoring (Understanding Problems)

**What:** Checking your app's diary to understand errors.
**Think of it as:** Reading the store's incident reports.

```bash
# View backend logs
docker compose -f docker-compose.prod.yml logs backend --tail 100

# View database logs
docker compose -f docker-compose.prod.yml logs db --tail 100

# Follow logs in real time (like a live feed)
docker compose -f docker-compose.prod.yml logs -f backend
```

### 6. Scaling (Handling More Users)

When your team grows beyond ~20 concurrent users:

- **Backend:** Increase workers in `backend/Dockerfile` (change `--workers 2` to `--workers 4`)
- **Database:** Upgrade to a larger plan on your hosting provider
- **Server (VPS):** Upgrade to more RAM/CPU

---

## Quick Reference: Environment Variables Checklist

Before deploying, make sure ALL of these are set:

| Variable | Where | Example | Required? |
|----------|-------|---------|-----------|
| `DB_PASSWORD` | docker-compose | `xK9#mP2$vL5nQ8w` | YES |
| `JWT_SECRET_KEY` | Backend | `a1b2c3d4...` (64 chars) | YES |
| `CORS_ORIGINS` | Backend | `https://app.yourcompany.com` | YES |
| `ENVIRONMENT` | Backend | `production` | YES |
| `REACT_APP_API_URL` | Frontend (build) | `https://api.yourcompany.com` | YES |

---

## Troubleshooting

### "I can't reach the app"
1. Check if containers are running: `docker compose -f docker-compose.prod.yml ps`
2. Check logs: `docker compose -f docker-compose.prod.yml logs`
3. Make sure your domain DNS records are pointing to the right IP

### "CORS error in the browser"
- The `CORS_ORIGINS` environment variable doesn't match your frontend URL
- Make sure it includes `https://` and has no trailing slash

### "Login doesn't work"
- `JWT_SECRET_KEY` might not be set — check backend environment variables
- Clear browser localStorage and try again

### "Database connection refused"
- The database might not be ready yet — wait 30 seconds and try again
- Check the `DATABASE_URL` is correct in backend environment variables
