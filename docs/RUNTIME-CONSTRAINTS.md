# Runtime constraints — development control plane only

Use an operator-approved Linux/WSL POSIX environment with shared local filesystem for both roles and
private FIFOs. Proposed paths are defaults, not observed destinations. Bootstrap/coding/strategy
roots must be canonical, distinct and non-nested. Existing .git worktree file is supported. Do not
use a network-mounted home for Codex SQLite/FIFO/locks without qualification; do not import settings
from unrelated SLAIF projects or prior host failures.

No production secrets, valuable unrelated files, broad host mounts, private SSH/cloud/browser auth,
real data or live lab access are required. Docker access means potential host control: qualify the
daemon/context as local owned test environment. Avoid broad cleanup commands and remote contexts.
Only synthetic disposable DBs/data are test inputs. Existing rehearsal/operational tests must run in
an isolated copy until their deployment-file ownership paths are qualified. Never delete unknown
volumes or overwrite existing deploy/env.production/password files.

Both development roles use Codex, separate private CODEX_HOME directories and model/provider configs.
Historical coding preference is chatgpt-5.5-high; active exact model ID/provider is UNCONFIGURED
until discovered/approved. Strategic and independent-audit model identity also UNCONFIGURED. No
silent fallback, price/context claim or hardcoded guessed CLI switch. Inspect installed help/version
and safe instruction discovery; live inference qualification is separately authorized and cost-bound.

Default activation false; no autostart/cron/daemon, no --yolo/sandbox bypass by default. High autonomy
requires explicit outer runtime approval and documented blast radius, not merely a CLI flag. Setup
shells are allowed before auth; bootstrap does not authenticate/copy auth or make model calls. Private
permissions0700 dirs/0600 configs/FIFOs; logs are redacted and local, not Git. Explicit quit stops
owned wrapper; never kill unrelated process/tmux/server to recover.

The private remote is existing ulfe-lmi/slaif-asset-reservation; no creating/publishing another repo,
changing visibility or secrets/rulesets. Operational GitHub access and strategic merge capability
are separately authorized. Check merge workflow/app/webhook effects; unverified external effects
block delegated merge activation. Human adjudication origin cannot be an agent-shared account.
