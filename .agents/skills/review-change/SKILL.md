---
name: review-change
description: Review a change in this repository before it is committed or merged - your own work, a branch, or a pull request. Use when asked to review, check, or sign off on changes, or before reporting a task as done.
---

# Review a change

Review against this repository's own rules in `AGENTS.md`; this skill is the checklist.
Report findings as: file:line, what is wrong, a concrete failure scenario, and the fix.
Do not report style preferences the linters do not enforce.

## 1. Gather the change

- Local work: `git status` and `git diff` (staged and unstaged).
- A branch: `git log --oneline <base>..HEAD` and `git diff <base>...HEAD`.

## 2. Verify, do not trust

Run `python scripts/verify.py`. A change is not done while it fails or prints "NOT COMPLETE"
for a check the change touches. Quote failures exactly.

## 3. Correctness

- Does every behavior change come with a test in `tests/` that fails without it? Tests use synthetic numpy frames, never a camera or a downloaded model.
- Optional dependencies (ONNX model, scipy, MediaPipe, pyaudio) missing: the code degrades and logs, it does not crash.
- The CLI loop (`src/moza/cli.py`) and the server loop (`background_vision_worker`) change together.
- Rules: conditions only use keys present in the server's `context` dict (see the `add-rule` skill).

## 4. Repository invariants

- **Personal data**: no frames, recordings, face crops, `data/` or `models/` written to the repo, logs or webhooks; face anonymization is not bypassed.
- **Network exposure**: the server keeps binding `127.0.0.1` by default and `ALLOWED_ORIGINS` limited to the desktop app; any widening is opt-in and documented.
- **Interfaces**: new detectors, sources, channels and sinks subclass `src/moza/core/interfaces.py`.
- **Port 8100**: hard-coded in several desktop files; changed everywhere or nowhere (`grep -rn 8100 apps/desktop/src`).
- **Client SDK**: `clients/python/moza_client` stays free of CV dependencies (it is used by takient `robot_host`).
- **Secrets**: no `.env`, API keys or webhook URLs with tokens in the diff, logs or error messages.

## 5. Commits

- Format `<type>(<scope>): <subject>` with the types and scopes in `AGENTS.md`.
- Atomic: refactor, then fix/feat, then test; at most 5 staged files per commit (lockfiles and docs excluded); config not mixed with source.
- Each commit builds and passes tests on its own.
- No mention of AI tools in commit messages.

## 6. Verdict

End with one line: `ready`, `ready after fixes listed above`, or `not ready: <reason>`.
