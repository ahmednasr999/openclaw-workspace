# Safe cleanup manifest - 20260514-stale-backups-cleanup

Archived low-risk stale backup/temp artifacts from scripts/docs/cvs only.

## Safety boundary
- No deletes, move-to-archive only.
- Did not touch gateway config/runtime.
- Did not touch active logs/data/databases.
- Did not touch core rollback backup directories.
- Did not touch memory/core backup files.

## Archived files
- cvs/Ahmed Nasr - Technical Delivery Leader - Staq.html.bak -> archive/20260514-stale-backups-cleanup/cvs/Ahmed Nasr - Technical Delivery Leader - Staq.html.bak | bytes=12648 | sha256=435926fb7276545aec2f3483978e5a87dceb15ee6eb9c511d4b0bc357aa92686
- cvs/Ahmed Nasr - VP Portfolio Management EPMO Leader - Michael Page.html.bak -> archive/20260514-stale-backups-cleanup/cvs/Ahmed Nasr - VP Portfolio Management EPMO Leader - Michael Page.html.bak | bytes=9139 | sha256=8dec3acf5de93921f31adf9881222de91c39e673fc121ab5e2f36761fb7f2226
- docs/agent-governance/NASR-ACP-Coding-Brief.md.2026-05-07-systems-thinking.bak -> archive/20260514-stale-backups-cleanup/docs/agent-governance/NASR-ACP-Coding-Brief.md.2026-05-07-systems-thinking.bak | bytes=5167 | sha256=0e02c2d208faf351b0cd6da3f5838a5332bedc7f1250d82d1224fa25c487868e
- docs/agent-governance/NASR-ACP-Coding-Brief.md.bak-202604291700 -> archive/20260514-stale-backups-cleanup/docs/agent-governance/NASR-ACP-Coding-Brief.md.bak-202604291700 | bytes=2227 | sha256=0b15d8ef12100bccdbe149e66b3fbeedd2730b17dafbdb7a8c76682080140fe0
- docs/agent-governance/NASR-ACP-Coding-Brief.md.bak-agent-skills-20260430-143849 -> archive/20260514-stale-backups-cleanup/docs/agent-governance/NASR-ACP-Coding-Brief.md.bak-agent-skills-20260430-143849 | bytes=4304 | sha256=221c857c98eab53e495715920966e3f527f3420f94db139c0f0e3c5a3be4ab1a
- docs/agent-governance/NASR-Coding-Rules-v1.md.2026-05-07-systems-thinking.bak -> archive/20260514-stale-backups-cleanup/docs/agent-governance/NASR-Coding-Rules-v1.md.2026-05-07-systems-thinking.bak | bytes=7436 | sha256=c84fe613dfd514d4f3014f2cd3ba4ea4f416e7bc679bff13116e4cb04162a9e2
- docs/agent-governance/NASR-Coding-Rules-v1.md.bak-agent-skills-20260430-143849 -> archive/20260514-stale-backups-cleanup/docs/agent-governance/NASR-Coding-Rules-v1.md.bak-agent-skills-20260430-143849 | bytes=5181 | sha256=61752867d9700423f5c25b1223d8af1031333c2a65d64529d0f7dc23955f0a83
- scripts/add-to-pipeline.py.bak -> archive/20260514-stale-backups-cleanup/scripts/add-to-pipeline.py.bak | bytes=9484 | sha256=186259cd79d7581918fbcbd0325435a95420e2b13ca0514e267625ef04683ef6
- scripts/check-openclaw-runtime-patches.py.bak-active-memory-20260427-230818 -> archive/20260514-stale-backups-cleanup/scripts/check-openclaw-runtime-patches.py.bak-active-memory-20260427-230818 | bytes=1835 | sha256=114cb5291e1102e0b9d930981ad133fef08ce07b16cca84388b9c6cdf8a7bda7
- scripts/check-openclaw-runtime-patches.py.disable-runtime-context-custom-20260428.bak -> archive/20260514-stale-backups-cleanup/scripts/check-openclaw-runtime-patches.py.disable-runtime-context-custom-20260428.bak | bytes=4749 | sha256=b12989b44f55795d40ad639f2116090c79a92c8693ab6f407fae1fc7dbbf0bde
- scripts/check-openclaw-runtime-patches.py.leakfix-20260428.bak -> archive/20260514-stale-backups-cleanup/scripts/check-openclaw-runtime-patches.py.leakfix-20260428.bak | bytes=2723 | sha256=3c08cd42e5d40b9c3eeebc4805b1742a0dfedb1b7919b3ce99347e561ffff5d5
- scripts/jobs-review.py.bak -> archive/20260514-stale-backups-cleanup/scripts/jobs-review.py.bak | bytes=22219 | sha256=6cc97eae50040797bd0ae088b2512c3d0f622579c34f39bfa5100233d180293e
- scripts/linkedin-auto-poster.py.bak3 -> archive/20260514-stale-backups-cleanup/scripts/linkedin-auto-poster.py.bak3 | bytes=27393 | sha256=54cf345df43eb15da93dec6102f088f06e5be8577fbfdd14586795170a73509c
- scripts/morning-briefing-orchestrator.py.bak2 -> archive/20260514-stale-backups-cleanup/scripts/morning-briefing-orchestrator.py.bak2 | bytes=65469 | sha256=24c73a30464b007573c9659f5bb5fc8e2faa513eeb90ce7cb444edd52b792d78
- scripts/pipeline_db.py.bak3 -> archive/20260514-stale-backups-cleanup/scripts/pipeline_db.py.bak3 | bytes=33258 | sha256=038791fce76f381a5983b33dfdde54e551ac73b2cb004357e1b4cdf60b18d162

## Restored / skipped after verification
- Restored `scripts/job-radar.py.bak` because no active `scripts/job-radar.py` counterpart exists. Keeping the only script copy in place is safer than archiving it.

## Recovery note
- A shell quoting mistake while appending this manifest executed `scripts/job-radar.py.bak` once.
- Side-effect files were backed up under `archive/20260514-stale-backups-cleanup/recovery-accidental-job-radar-run/`.
- Restored `memory/job-radar.md` and `jobs-bank/pipeline.md` to their pre-run tracked state.
- Kept `scripts/job-radar.py.bak` in place because no active `scripts/job-radar.py` exists.
