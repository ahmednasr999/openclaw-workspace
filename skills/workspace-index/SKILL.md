# Workspace Index Skill

Maintains a navigable index of the workspace so agents can find files without exploring the file tree.

## When to Use
- Before any task that requires finding files
- When spawning sub-agents (include relevant index sections in the brief)
- After creating/moving/deleting significant files (run the updater)

## Index Location
`WORKSPACE_INDEX.md` in workspace root.

## Updating the Index
Run the generator script to rebuild:
```bash
bash skills/workspace-index/generate-index.sh
```

## Index Structure
The index is organized by function, not by directory:
1. **Core Config** - Files injected every session
2. **Memory** - Daily notes, lessons, knowledge
3. **Job Search** - Pipeline, applications, CVs, dossiers
4. **LinkedIn/Content** - Posts, drafts, calendar, engagement
5. **Scripts** - Grouped by function (cron, CV, LinkedIn, infra, etc.)
6. **Skills** - All installed skills with status
7. **Coordination** - Dashboard, pipeline, calendar, outreach
8. **Infrastructure** - Mission Control, cron, hooks, logs

## Rules
- After creating new files in key directories, run the updater
- Sub-agents should receive only their relevant index section, not the whole thing
- The index is a MAP, not documentation. Keep entries to one line each.
