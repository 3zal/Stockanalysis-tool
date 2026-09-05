# Deploying investr-info-api (the FastAPI) — Railway

This service is the Investr Score + search + full-analysis backend for investr.info. Since
5 Sept 2026 it runs on **Railway** (region Singapore) as a Docker container built from
[`backend/Dockerfile`](backend/Dockerfile). Health check (`/health`) and restart policy are
dashboard settings — Railway deprecated its `railway.json` config-as-code in Aug 2026. It used to be a Render web service (`render.yaml`,
now deprecated and kept only as a record).

The **full runbook** — DNS, both services, env vars, verification, the web upload, the App Store
build — is `DEPLOYMENT.md` in the `investr-pulse` repo. The short version for this service:

1. Railway → the `investr` project → **+ New → GitHub Repo → `3zal/Stockanalysis-tool`**,
   branch `main`.
2. Service **Settings → Root Directory** = `backend`. The Dockerfile is picked up automatically.
3. **Variables**:
   | Var | Value |
   |-----|-------|
   | `CORS_ORIGINS` | `https://investr.info,https://www.investr.info,capacitor://localhost,https://localhost` |
   | `TWELVEDATA_KEY` | the TwelveData API key (read at `services/stock_service.py:669`; the code still carries a hard-coded fallback — rotate that key and delete the fallback when you get a minute) |
4. **Settings → Networking → Custom Domain** = `api.investr.info`; add the CNAME Railway shows
   in Hostinger's DNS zone. Until DNS propagates, use the generated `*.up.railway.app` domain.
5. Verify: `https://api.investr.info/health` → `{"status":"ok","build":"yearly-v2"}`, then
   `https://api.investr.info/api/stocks/RELIANCE` returns a full analysis with a `score`
   (that call is the one that proves Yahoo/NSE are reachable from Railway's Singapore IPs).

Redeploys: every push to `main` deploys (Railway's default). There is no Manual Deploy step
any more — the thing that bit the Render setup.
