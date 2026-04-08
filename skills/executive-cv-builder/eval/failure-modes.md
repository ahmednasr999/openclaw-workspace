# Common Failure Modes (learned from 56 CV generations)

| Failure | Cause | Prevention |
|---------|-------|------------|
| CV built on wrong model | Session was on MiniMax/Haiku, not Opus | Step 0 model gate is BLOCKING |
| Wasted CV for unqualified role | Scored from title only, full JD revealed disqualifier | Step 0 full JD gate is BLOCKING |
| Tiny PDF (< 10KB) | Missing CSS/styling in HTML template | Post-gen quality gate checks file size |
| Bloated PDF (> 100KB) | Playwright embedded fonts/images | Use WeasyPrint, not Playwright |
| Em dashes in output | Model default punctuation | Post-gen automated check, hard rule in Step 4 |
| Header shows "Ahmed Nasr CV" | Model added label | Post-gen header check, Step 4 header gate |
