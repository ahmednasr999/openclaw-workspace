#!/bin/bash
# Workspace Index Generator
# Rebuilds WORKSPACE_INDEX.md from current file tree
# Run: bash skills/workspace-index/generate-index.sh

WS="/root/.openclaw/workspace"
OUT="$WS/WORKSPACE_INDEX.md"

cat > "$OUT" << 'HEADER'
# WORKSPACE_INDEX.md
# Auto-generated workspace map. Do not edit manually.
# Rebuild: bash skills/workspace-index/generate-index.sh

HEADER

echo "## Core Config (injected every session)" >> "$OUT"
for f in AGENTS.md SOUL.md TOOLS.md IDENTITY.md USER.md MEMORY.md HEARTBEAT.md STATE.yaml; do
    [ -f "$WS/$f" ] && echo "- \`$f\` - $(head -1 "$WS/$f" | sed 's/^#* //')" >> "$OUT"
done
echo "" >> "$OUT"

echo "## Memory" >> "$OUT"
echo "### Daily Notes (memory/YYYY-MM-DD*.md)" >> "$OUT"
count=$(ls "$WS"/memory/2026-*.md 2>/dev/null | wc -l)
latest=$(ls -t "$WS"/memory/2026-*.md 2>/dev/null | head -1 | xargs basename 2>/dev/null)
echo "- ${count} daily notes. Latest: \`${latest:-none}\`" >> "$OUT"
echo "### Reference" >> "$OUT"
for f in "$WS"/memory/*.md; do
    base=$(basename "$f")
    [[ "$base" == 2026-* ]] && continue
    echo "- \`memory/$base\`" >> "$OUT"
done
echo "" >> "$OUT"

echo "## Job Search" >> "$OUT"
echo "- \`jobs-bank/pipeline.md\` - Application pipeline tracker" >> "$OUT"
echo "- \`jobs-bank/search-policy.md\` - Search criteria and filters" >> "$OUT"
echo "- \`jobs-bank/skip-patterns.md\` - Auto-skip rules" >> "$OUT"
count=$(ls "$WS"/jobs-bank/applications/*.md 2>/dev/null | wc -l)
echo "- \`jobs-bank/applications/\` - ${count} application files" >> "$OUT"
count=$(ls "$WS"/jobs-bank/dossiers/*.md 2>/dev/null | wc -l)
echo "- \`jobs-bank/dossiers/\` - ${count} company dossiers" >> "$OUT"
echo "" >> "$OUT"

echo "## CVs" >> "$OUT"
echo "- \`memory/master-cv-data.md\` - **SOURCE OF TRUTH** for all CV content" >> "$OUT"
echo "- \`memory/ats-best-practices.md\` - ATS compliance rules" >> "$OUT"
for f in "$WS"/cvs/*.pdf "$WS"/cvs/*.html "$WS"/cvs/in-progress/*; do
    [ -f "$f" ] && echo "- \`${f#$WS/}\`" >> "$OUT"
done
echo "" >> "$OUT"

echo "## LinkedIn & Content" >> "$OUT"
echo "- \`coordination/content-calendar.json\` - Content scheduling" >> "$OUT"
for d in linkedin/drafts linkedin/posts linkedin/engagement; do
    count=$(ls "$WS/$d"/* 2>/dev/null | wc -l)
    echo "- \`$d/\` - ${count} files" >> "$OUT"
done
echo "" >> "$OUT"

echo "## Coordination" >> "$OUT"
for f in "$WS"/coordination/*.json; do
    [ -f "$f" ] && echo "- \`coordination/$(basename "$f")\`" >> "$OUT"
done
echo "" >> "$OUT"

echo "## Scripts (by function)" >> "$OUT"
echo "### CV & Job Search" >> "$OUT"
ls "$WS"/scripts/*cv* "$WS"/scripts/*ats* "$WS"/scripts/*dossier* "$WS"/scripts/*recruiter* "$WS"/scripts/*job* "$WS"/scripts/*handoff* 2>/dev/null | while read f; do
    echo "- \`scripts/$(basename "$f")\`" >> "$OUT"
done
echo "### LinkedIn & Content" >> "$OUT"
ls "$WS"/scripts/*linkedin* "$WS"/scripts/*content* "$WS"/scripts/*x-* 2>/dev/null | while read f; do
    echo "- \`scripts/$(basename "$f")\`" >> "$OUT"
done
echo "### Infrastructure & Monitoring" >> "$OUT"
ls "$WS"/scripts/*watchdog* "$WS"/scripts/*health* "$WS"/scripts/*gateway* "$WS"/scripts/*backup* "$WS"/scripts/*retention* "$WS"/scripts/*snapshot* "$WS"/scripts/*openclaw* "$WS"/scripts/*disk* 2>/dev/null | while read f; do
    echo "- \`scripts/$(basename "$f")\`" >> "$OUT"
done
echo "### Briefings & Intelligence" >> "$OUT"
ls "$WS"/scripts/*brief* "$WS"/scripts/*morning* "$WS"/scripts/*insight* "$WS"/scripts/*intel* "$WS"/scripts/*firehose* "$WS"/scripts/*radar* "$WS"/scripts/*competitive* 2>/dev/null | while read f; do
    echo "- \`scripts/$(basename "$f")\`" >> "$OUT"
done
echo "### Gmail & Notifications" >> "$OUT"
ls "$WS"/scripts/*gmail* "$WS"/scripts/*telegram* "$WS"/scripts/*notification* "$WS"/scripts/*notion* 2>/dev/null | while read f; do
    echo "- \`scripts/$(basename "$f")\`" >> "$OUT"
done
echo "" >> "$OUT"

echo "## Skills" >> "$OUT"
for d in "$WS"/skills/*/; do
    name=$(basename "$d")
    [[ "$name" == ".archived" || "$name" == "cron" ]] && continue
    echo "- \`skills/$name/\`" >> "$OUT"
done
echo "### Cron Skills" >> "$OUT"
for d in "$WS"/skills/cron/*/; do
    name=$(basename "$d")
    echo "- \`skills/cron/$name/\`" >> "$OUT"
done
echo "" >> "$OUT"

echo "## Infrastructure" >> "$OUT"
echo "- \`mission-control/\` - Mission Control dashboard app" >> "$OUT"
echo "- \`infrastructure/\` - systemd configs, credential templates" >> "$OUT"
echo "- \`logs/\` - Watchdog and system logs" >> "$OUT"
echo "" >> "$OUT"

# Timestamp
echo "---" >> "$OUT"
echo "_Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')_" >> "$OUT"

echo "Index generated: $OUT"
wc -l "$OUT"