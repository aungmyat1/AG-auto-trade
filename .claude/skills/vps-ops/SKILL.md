---
name: vps-ops
description: VPS / infrastructure operations for the WORKER agent host — Ubuntu, systemd, Docker, logs, backups, monitoring. Use for deploy, restart, disk, service-health, or log-investigation tasks.
---

# VPS Operations (WORKER host)

The VPS is the only machine allowed to trade: it owns the IB keys. Cloud/research agents
never hold broker keys. Keep that boundary intact in every operation.

## Standing rules

- **Never print or echo secret env values** (`IB_*`, `TELEGRAM_BOT_TOKEN`, anything in
  `.env`). Confirm presence with `test -n "$VAR" && echo set`, never `echo $VAR`.
- **Snapshot before stopping.** Before stopping/restarting any trading service, snapshot
  its trade journal/log and check `.kill_switch_state.json` (halt state must be captured,
  not destroyed) — a running demo/dry-run may be a gate metric.
- **Destructive ops need the owner.** `docker compose down -v`, dropping data dirs,
  `pkill -f python` on a box with a live dry-run — confirm first.

## Service management

```bash
systemctl status <svc>                 # ag services use the ag-* prefix
journalctl -u <svc> -n 200 --no-pager  # recent logs
sudo systemctl restart <svc>           # after snapshot + reason logged
docker compose ps && docker compose logs --tail 200 <svc>
```

## Health triage order

1. Disk: `df -h` (full disk silently kills journals first)
2. Memory/CPU: `free -m`, `top -bn1 | head -20`
3. Service state: `systemctl --failed`, `docker ps -a` (look for restart loops)
4. App logs: journalctl/compose logs around the first error timestamp, not the last
5. Network: broker/data connectivity (IB gateway port, Databento reachability)
6. Clock: `timedatectl` — NTP drift breaks session windows and bar alignment

## Backups

- Trade journals + `VALIDATION_STATUS.md` + `.kill_switch_state.json` are the crown-jewel
  state. Back up before upgrades: `tar -czf ~/backups/ag-$(date +%F).tar.gz <data dirs>`.
- Verify a backup by listing its contents, not by its exit code.

## After any incident

Write `docs/audits/INCIDENT_<date>.md`: timeline, root cause, what the monitoring missed,
and update `docs/PROJECT_STATE.md` if the stage/health changed. Alert via
`ag.monitoring.alert_system_event()` when Telegram env is configured.
