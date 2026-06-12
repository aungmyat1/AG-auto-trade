# GitHub Manual Setup — Owner Runbook

These steps must be done by the repo owner in the GitHub web UI. Agent sessions cannot do
them: the OAuth token lacks the `workflow` scope (CI files) and admin rights (protection
rules). Do them **in this order** — branch protection requires a CI check that must exist
and have run at least once first.

---

## Step 1 — Merge PR #1 (Trading Engineering OS)

1. Open <https://github.com/aungmyat1/AG-auto-trade/pull/1>.
2. Review the diff. Press **Ready for review** (it is a draft), then **Merge pull request**
   → **Confirm**. "Squash and merge" is fine if you prefer one commit.
3. Result: CLAUDE.md, skills, hooks, and slash commands are on `main`. Every future
   Claude Code web session now auto-installs deps via the SessionStart hook.

## Step 2 — Add the CI workflow (GitHub UI, ~2 min)

The token used by agent sessions cannot push workflow files, so create it in the browser:

1. Repo home → **Add file ▾** → **Create new file**.
2. Name the file exactly:

   ```
   .github/workflows/ci.yml
   ```

3. Paste:

   ```yaml
   name: CI

   on:
     push:
       branches: [main, "feat/*", "research/*", "claude/*"]
     pull_request:
       branches: [main]

   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: "3.11"
             cache: pip
         - name: Install
           run: pip install -e ".[dev]"
         - name: Lint
           run: ruff check ag/ tests/ scripts/ .claude/hooks/
         - name: Test
           run: pytest tests/ -v --tb=short
   ```

   (This is the workflow removed in commit `0045736`, plus a `ruff` lint step — the repo
   is lint-clean as of PR #1 — and `claude/*` so agent session branches get CI too.)

4. **Commit changes** → "Commit directly to the `main` branch" → **Commit**.
5. No secrets are needed — tests are pure-Python, no broker/API keys involved.

## Step 3 — Verify the first green run

1. Go to the **Actions** tab. A `CI` run triggers from the Step-2 commit.
2. Wait for the green check on the `test` job. If it fails, stop and investigate before
   Step 4 — you must not "require" a check that has never passed.

## Step 4 — Enable branch protection on `main`

Settings → **Branches** → **Add branch protection rule** (classic; a Ruleset achieves the
same if you prefer Settings → Rules → Rulesets → New branch ruleset):

| Setting | Value | Why |
|---|---|---|
| Branch name pattern | `main` | |
| ✅ Require a pull request before merging | ON, **required approvals: 0** | You are a solo owner — GitHub will not let you approve your own PR, so 1+ would deadlock you. The PR flow itself is the audit trail. |
| ✅ Require status checks to pass before merging | ON → search and select **`test`** | The CI job from Step 2. Tick "Require branches to be up to date" too. |
| ✅ Block force pushes | ON | Mirrors the agent-side `bash_guard` hook at the server. |
| ✅ Do not allow deletions | ON | |
| Require conversation resolution | Optional, recommended | Review comments must be resolved before merge. |

Click **Create**. From now on, nothing reaches `main` except a PR with green CI — the
"goalposts in git" discipline now has server-side teeth.

## Step 5 (recommended, 1 min) — Secret scanning & push protection

Settings → **Advanced Security** (or "Code security and analysis"):

- Enable **Secret scanning** and **Push protection**.

This is the server-side twin of the local `bash_guard.py` secret scan: GitHub will reject
pushes containing recognizable credentials even if a local hook is bypassed.

## Verification checklist

- [ ] PR #1 merged; `CLAUDE.md` visible at repo root on `main`
- [ ] Actions tab shows a green `CI` run on `main`
- [ ] Direct push to `main` is rejected (try `git push origin main` with a trivial commit —
      it should fail with a protection error)
- [ ] A test PR shows the `test` check as **Required**
- [ ] Settings → Advanced Security shows secret scanning + push protection ON
- [ ] Update `docs/PROJECT_STATE.md`: mark the "Branch protection OFF" and "No CI" rows in
      Known Gaps as closed (any agent session can do this on request)

## Ongoing PR flow after this setup

1. Agent develops on a `claude/*` (or `feat/*`) branch and opens a draft PR.
2. CI runs automatically; the local pre-push hook has already enforced green tests.
3. You review → Ready for review → merge. `main` stays protected and green.
