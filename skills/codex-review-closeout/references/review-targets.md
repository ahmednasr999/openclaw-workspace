# Review Targets

Pick the smallest truthful review target.

## Local edits

Use for uncommitted or staged workspace changes:
- inspect `git status --short`
- inspect `git diff` and, when staged changes exist, `git diff --staged`
- review only the repo that was actually edited

## Branch or PR work

Use for a branch, PR, or comment-resolution task:
- identify base branch from repo context, PR metadata, or explicit user request
- inspect changed files before review
- prefer branch-vs-base review over broad repository review

## Do not review

Skip or state unavailable when:
- no code/config/docs diff exists
- the task was pure read-only analysis
- there is no git repo and no meaningful diff artifact
- running review would require external write/deploy/approval not yet granted

## Source-of-truth order

1. Current working tree and `git status`.
2. Actual diff and changed files.
3. PR metadata or issue thread if relevant.
4. Tests/checks already run in this session.
