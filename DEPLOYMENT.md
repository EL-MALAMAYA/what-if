# Deployment Guide — Railway + Custom Domain

## 1. Connect GitHub to Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select the `what-if` repository. Railway auto-detects the `Procfile`.
4. Wait for the first build to complete (it will fail gracefully until env vars are set).

## 2. Set Environment Variables

1. In your Railway project, click the **service card** (the deployed app).
2. Go to the **Variables** tab.
3. Add the following two variables:

   | Variable            | Value                        |
   |---------------------|------------------------------|
   | `GMI_API_KEY`       | Your GMI Cloud API key       |
   | `GMI_ENDPOINT_URL`  | Your GMI Cloud endpoint URL  |

4. Click **Deploy** (or Railway will auto-redeploy on variable change).

## 3. Add a Custom Domain

1. In the same service, go to the **Settings** tab.
2. Scroll to **Networking** → **Custom Domain**.
3. Click **Add Domain** and enter: `what-if.live`
4. Railway will display a target hostname, something like:
   ```
   what-if-production-xxxx.up.railway.app
   ```
   Copy this value — you need it for the next step.

## 4. Configure DNS (CNAME Record)

Go to your domain registrar (Namecheap, Cloudflare, GoDaddy, etc.) and add:

| Type    | Host / Name | Value / Target                              | TTL  |
|---------|-------------|---------------------------------------------|------|
| `CNAME` | `@`         | `what-if-production-xxxx.up.railway.app`    | Auto |

> **Note:** Some registrars don't allow a CNAME on the root (`@`). In that case:
> - Use Cloudflare (supports CNAME flattening on root).
> - Or add `www` as the host and set up a redirect from `what-if.live` → `www.what-if.live`.

DNS propagation typically takes 5–30 minutes. Once complete, Railway auto-provisions an SSL certificate.

## 5. Verify

Open `https://what-if.live` in your browser. You should see the dashboard with the "Configuration Required" card if env vars aren't set, or the full simulation UI if they are.
