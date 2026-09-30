# Taxonomy

Gemini reads this file on every run and files insights/tools under these paths.
Only list items in the form "- `path` — definition" are parsed. Add, rename, or split freely;
then remap existing records in `data/*.jsonl` (see CLAUDE.md).

## Insight topics

- `system-design/caching` — cache placement, invalidation, eviction, stampedes
- `system-design/databases` — data modeling, indexing, replication, sharding, SQL vs NoSQL, CQRS
- `system-design/distributed-systems` — consistency models, consensus, partitioning theory, clocks
- `system-design/scalability` — scaling reads/writes, load balancing, horizontal scaling, rate limiting, CDNs
- `system-design/api-design` — request/response APIs: REST/gRPC/GraphQL, versioning, pagination, auth
- `system-design/real-time` — WebSockets, server-sent events, long polling, pub/sub to clients
- `system-design/async-processing` — message queues, worker pools, background jobs, workflow engines
- `system-design/reliability` — retries and backoff, idempotency, circuit breakers, failover, self-healing
- `software-engineering/practices` — testing, code review, debugging, architecture patterns
- `ai-ml/engineering` — building with LLMs, RAG, evals, agents
- `career/interviews` — interview prep, resumes, job search
- `game-dev/roblox` — Roblox development: Studio, Luau scripting, Open Cloud APIs, asset pipelines
- `game-dev/general` — game design, engines, 3D assets, and workflows that aren't platform-specific

## Tool categories

- `dev-tools/runtimes-and-languages` — language runtimes, compilers, package managers
- `dev-tools/databases` — databases and data stores
- `dev-tools/infra` — hosting, deployment, observability, CI/CD
- `dev-tools/productivity` — editors, terminals, CLIs, workflow tools
- `dev-tools/ai` — AI coding assistants, model APIs, AI frameworks
- `dev-tools/game-dev` — game engines, 3D/asset tools, and game platform APIs
- `products/other` — anything that isn't a developer tool
