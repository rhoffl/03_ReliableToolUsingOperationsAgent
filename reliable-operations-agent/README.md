# Reliable Tool-Using Operations Agent

A portfolio-ready incident-response application that investigates simulated incidents through controlled, typed tools. It preserves execution history, proposes evidence-backed remediation, requires explicit approval before mutations, executes idempotently, and verifies recovery.

## Run locally

Requirements: Docker Desktop or Docker Engine with Compose.

```bash
cp .env.example .env
docker compose up --build
```

- Dashboard: http://localhost:3003
- API documentation: http://localhost:8003/docs
- Health check: http://localhost:8003/health

Run tests: `docker compose run --rm api pytest -q`

Reset local data: `docker compose down -v`

## Demonstration

1. Launch `bad deployment`, select it, and choose **Investigate incident**.
2. Inspect four read-only tool calls, the grounded hypothesis, and proposed rollback.
3. Approve or reject the exact action.
4. If approved, inspect its idempotency key, recovery verification, and report.
5. Launch `prompt injection` to prove that instructions embedded in logs remain inert.

## Safety architecture

- Explicit allowlisted state transitions.
- Typed API and tool inputs.
- Scoped, allowlisted tools with bounded calls.
- Human approval bound to the exact action hash.
- An action ledger that prevents duplicate execution.
- Untrusted logs and runbooks treated only as evidence.
- Append-only history of tools, approvals, actions, and verification.
- Cost and tool-call budgets.

## Important limitation

The included reasoning engine is deterministic so the application runs without cloud credentials and tests remain repeatable. A production LLM adapter may replace hypothesis drafting, but it must return the same structured fields and cannot bypass state, policy, or approval controls.

## Production extensions

Add OIDC, approver RBAC, encrypted secrets, signed audit exports, migrations, a durable worker, OpenTelemetry export, model-provider adapters, and real log/metric/deployment connectors. Keep all production credentials read-only by default.
