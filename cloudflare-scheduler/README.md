# Gold Price Board External Scheduler

Cloudflare Cron is the primary hourly trigger. It calls the existing GitHub
`workflow_dispatch` endpoint; it never reads or writes the formal history file.

- Cron: every hour at minute 23 (UTC and local minute are identical).
- GitHub workflow: `.github/workflows/refresh.yml`.
- Required Worker secrets: `GITHUB_TOKEN`, `TRIGGER_KEY`.
- `GITHUB_TOKEN` only needs Actions write permission for this public repository.
- `POST /trigger` is an authenticated deployment verification endpoint.
- `GET /health` exposes no credentials and performs no write.

The local launchd job runs later at minute 47 with `--fallback`. It only writes
when the latest remote snapshot is at least 75 minutes old.
