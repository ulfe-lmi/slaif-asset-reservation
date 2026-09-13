# CONTEXT-BUDGET — measured routine coding governance

Generation 1. Exact UTF-8 bytes of the mandatory transitive coding read set
(excluding the active order and product code), measured on the installed files:

| Component (installed path) | Exact bytes | Byte ceiling | Token target |
|---|---:|---:|---:|
| `AGENTS.md` | 1058 | 2048 | 400 |
| `oap/coding-instructions/AGENTS.md` | 6403 | 12000 | 2200 |
| `ARCHITECTURE-for-agents.md` | 12929 | 20000 | 3800 |
| `OAP-COMMUNICATION-coding-agent.md` | 4105 | 10000 | 1800 |
| `oap/coding-instructions/SECURITY-CORE.md` | 1410 | — | — |
| `oap/coding-instructions/TESTING-CORE.md` | 1823 | — | — |
| **Total (excluding order/code)** | **27728** | **50000** | **10000** |

Optional (order-scoped, not routine): root SECURITY.md sections, TESTING.md full file,
docs/decisions ADRs, subtree contracts named by the order.

Tokens: **UNMEASURED** — no qualified tokenizer for the configured (still unconfigured)
model was run; character estimates are not presented as exact counts. Byte ceilings are
hard measured limits; overflow fails check_governance and tests (BA-15). Overflow
handling: redistill or restructure the projection, or record a justified budget
revision — never silently truncate law.

Full strategic law, full architecture, full plan, source books, the historical
register and future drafts are deliberately outside the routine transitive set.
