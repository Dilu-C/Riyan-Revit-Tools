---
trigger: always_on
description: Guardrail prohibiting automated git push commands in the background to prevent hung tasks and credential deadlocks.
---

# Git & Remote Push Execution Guardrails

## 1. Never Run Automated `git push` via Terminal
- Under no circumstances should the agent execute `git push` via terminal commands or background tasks.
- Terminal-based `git push` on Windows frequently triggers blocking GUI/browser authentication prompts or hangs indefinitely as a background task.

## 2. Respect User's GitHub Desktop Workflow
- Prepare all local files, repositories, commits, and structures locally as requested.
- Once local changes are committed or staged, inform the user that their changes are ready for them to push with 1 click via **GitHub Desktop** (`Push origin`).
- Never attempt to force, automate, or background-push to remote repositories.
