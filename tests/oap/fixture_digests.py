"""Build-time injected identity constants (materialization generation 1).

These values are computed from the actual input package and the actual pre-conversion
repository bytes at staging time. They are constants ON PURPOSE: a test that recomputed
its expected digest from the thing under test would prove nothing.
"""

GEN = "1"
DATE = "2026-09-13"
BASE = "1fcc2c91d793556a91711365abef562604b62f84"
REPO_ID = "ulfe-lmi/slaif-asset-reservation"

# SHA-256 of the archived input package snapshots (docs/bootstrap/1/inputs/)
INPUT_DIGESTS = {
    "bootstrap-generator-prompt.md": (
        "09b72445b5d0ce26cd12b531148151f1293f51d5abee555dde3fe01c6280cb8d"
    ),
    "oap.md": "d4daeb2a4a8963691e0a15ebf8f4e46bdfe36c792c9685e5117396ff17f60989",
    "REPOSITORY-OBSERVATIONS.json": (
        "0a79f1660291b0bc31ebc3619aa4ac2c92f4c9840e107d376864d15595200370"
    ),
    "INSTRUCTIONS.md": "197bc6cdedcef13f3de9293d7dc8a328b77fc8723ec7ae76b23ed56f1e9f34ca",
    "PLAN.md": "d5677519a1546906eca644cb5be34a93f038a73fa20d6ba241cfdd0add6b9ef6",
    "ARCHITECTURE.md": "9e7c60e4ef6cee99d5baf20ee5ef6afcff38b10aa2eaa74a5a27084ff515a0c4",
    "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
    "SOURCE-MAP.md": "5b2e5e435ddc7392629410d1321ab5e362cce0bec822589b2dd7c0bd1f5b00e7",
    "PACKAGE-CHECKS.md": "9f713bf85dd4cedc7f5d740ed126773a58220af3b1685944ca68cc267f0c7fda",
    "README.md": "28b8bf41d940810067eacf3812e15b6a67a23fbeba1d60e874fb68b319f94666",
}

# SHA-256 of the original pre-conversion repository bytes (archived under previous/)
PREVIOUS_DIGESTS = {
    "AGENTS.md": "99822d8eea31e01bfb58dbea2dcfc3d8ec5c91e86d831c34ca1cc4fb65299ff1",
    "docs/architecture.md": "bcc8e46886eef1dc902c3bf142346603c3dd4ab47ee07a2c43b4e056b9d1f7dc",
    "docs/oap-workflow.md": "eb8863e8ceddee6b829ac0e3b77bbe2cd3974175260ab24174d97a964d86705c",
    "SECURITY.md": "fdf25060d1f5676bfdb6904908aa41bbfc6ade8b722ac64559fd915626c7ee88",
    "README.md": "e63ef8510d9199d35f46083643fefd080de4e79dfb520e23f13d4f1a69ec0dfc",
    "CONTRIBUTING.md": "74e31b8e2d8695b186310888129f6f5ac3e93250c18f5127f845b42f37cff7ae",
    "docs/README.md": "562ae9c58570601b6febac2839eeffa0abfff63e974a358789f0ec759b4d360c",
    "docs/roadmap.md": "75a327fb3bfe62b977de28da32ee2d06bd263a8716ca78e8c57739a4b5d49db7",
    "docs/project-handoff.md": ("d1672201a7c6e18ab8b54005b9a81e570b9f9a74413c5210f8327bede822894c"),
    ".github/PULL_REQUEST_TEMPLATE.md": (
        "93484d6bb52bd24be8ee486a8120cee59425d721df5e182765e94ace14de88e2"
    ),
    ".github/ISSUE_TEMPLATE/codex_work_order.yml": (
        "23c86666a0c38acda857555fad4cf0ac08ab1e19aeda408167272ce37ed8778c"
    ),
    ".gitignore": "0e1d31f7d5a86477ed5456286f5413454871173eaa5bd223c2cf7e0d0c7cdec5",
    ".dockerignore": "bdc82b5545f7de133be59d5d16d723611f5ae4378b286c42b965991469236f0b",
    ".github/workflows/ci.yml": (
        "aa02a7f083d248e16d45e046657d1d6c002c041943bf7e63a5b4dfd4949419f0"
    ),
}

# Git blob identities recorded in SOURCE-MAP.md (verified at materialization)
BLOB_IDS = {
    "docs_arch": "246870a7771452ce3878c228b9ad7ffd8e71eda0",
    "assets": "7c9ed1e4a072173960ebb9bdd886ce4c1fafe3a1",
    "agents": "3f43feeb0a3581d46af4efaa0150f8a1a705e46c",
    "main": BASE,
}

# SHA-256 of the candidate root ARCHITECTURE.md (package bytes installed verbatim)
ARCH_SHA = "9e7c60e4ef6cee99d5baf20ee5ef6afcff38b10aa2eaa74a5a27084ff515a0c4"
