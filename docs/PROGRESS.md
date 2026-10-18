# SDD ledger — plan: ../../implementation-plan.md
Execution: inline, approved by user “继续实施”.
Ruling: New empty project is isolated in outputs/zhixing; initialized feat/zhixing rather than a linked worktree without an existing source repository.
Pre-flight: Tasks 1→2 share Trade/Evidence; 2→3 share time filters/calculation; 3→4 share report schema; 4→5 share build output. No conflicts.
Task 1: complete — timezone, exact cutoff, unknown publication, backfilled reasons and safe URL validation passed.
Task 2: complete — CSV preview/atomic validation, duplicate IDs, finite decimals, FIFO fees and partial sells passed.
Task 3: complete — report schema, references, runtime mode, AI failure, per-decision information sets, checklist and exports passed.
Task 4: implementing — React/TypeScript build passed; browser checked sample, future toggle, rule report, save checklist and mark complete at narrow viewport.
Ruling: Group reviews use per-trade knowledge_by_decision, not a single later cutoff — prevents information from later decisions leaking into earlier ones. Regression watched fail then pass.
Ruling: Fuyao API docs became accessible via direct HTTP; implemented documented X-api-key historical endpoint. Historical publication time absent in schema, therefore available_at remains null and quality=missing. Never infer publication from date_ms or upstream timestamp. No live authorized provider call claimed.
Ruling: pnpm blocked esbuild lifecycle scripts; allow-listed only esbuild in pnpm-workspace.yaml; direct TypeScript and Vite builds succeeded.
Current evidence: 24 pytest tests passed, one upstream Starlette/httpx deprecation warning. Real API keys absent, only mock transports exercised runtime AI/provider branches.
Task 4: complete — responsive UI, CSV paste/preview/confirm, evidence drawer, rule report, checklist and cross-case context verified in browser.
Task 5: implementation complete — README, AI_USAGE, TESTING, DELIVERY, Dockerfile, lockfiles, CI and examples prepared. Docker unavailable, so Docker/CI execution not claimed.
Review: independent read-only reviewer found five P2 issues; reproduced and fixed malformed AI/provider containers, operation/prediction guards, batch capacity and seconds truncation. Secondary false positive for legitimate trade IDs also reproduced and fixed.
Verification: 42 pytest passed (one upstream deprecation warning); 2 Node time tests passed; TypeScript and Vite production build passed. git diff --check clean; no actual .env/database/node_modules tracked; credential pattern scan found no secrets.
Deployment: localhost.run HTTPS tunnel established at https://a94ffc96d47473.lhr.life; external /api/health returned status=ok and ai_configured=false. Long-term hosting not authorized; Render available but unconnected.
Ruling: Provide generic read-only HTTP Git source snapshot to satisfy source repository access without inventing a GitHub repository. Snapshot contains reviewed source commits only; source routes whitelist Git object paths. Offline ZIP/bundle remain available if temporary tunnel expires.
Public smoke found TLS proxy Origin mismatch (403); configured canonical PUBLIC_ORIGIN instead of weakening CSRF checks. Regression covers accepted canonical origin and rejected malicious origin. Public source clone already verified at c7e4c30; refreshing final source snapshot after this fix.
Public IAB navigation returned ERR_BLOCKED_BY_CLIENT; do not claim public browser visual verification. Use actual HTTPS main-chain tests plus successful Git clone; local browser QA remains valid.
Final public main-chain: HTTPS health/HTML, POST sample, time filter, rules report with knowledge map, checklist create/patch, export, Secure cookie and cross-session 404 all passed. Source HEAD=200/config=404. Domain rotated automatically; final verified current URL is in DELIVERY.md.
Final reviewer: original issues and trade-ID false positive resolved, no remaining finding from narrow recheck. Kept feature branch as standalone new repository (no base branch or merge target exists).
GitHub publication: authenticated jerrylongj1 and created private jerrylongj1/zhixing-investment-review. Initial push rejected because OAuth lacks workflow scope. Ruling: move optional CI YAML to docs/ci-example.yml and publish a clean initial snapshot without active workflows, preserving original full history in local feature branch/bundle. No extra workflow execution permissions requested.
