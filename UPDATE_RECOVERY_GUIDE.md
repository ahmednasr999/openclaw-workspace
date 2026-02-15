# OpenClaw Update Recovery Guide
# Created for: Ahmed Nasr
# Date: 2026-02-15
# Purpose: Step-by-step recovery if update breaks

================================================================================
SECTION 1: PRE-UPDATE CHECKLIST (Do These First)
================================================================================

STEP 1.1: Verify Current Backup Exists
--------------------------------------
Run this command:
    ls -lh /root/.openclaw/workspace/openclaw-backup-*.tar.gz

You should see:
    openclaw-backup-20260215-051107.tar.gz (950 KB)

If NOT, create backup NOW:
    cd /root/.openclaw/workspace
    tar -czf openclaw-backup-$(date +%Y%m%d-%H%M%S).tar.gz tools/cv-optimizer/ memory/ *.md

STEP 1.2: Document Current Working State
----------------------------------------
Check these work BEFORE updating:
    - CV Optimizer: http://localhost:5000/cv-optimizer
    - Job Tracker: http://localhost:5000/job-tracker
    - Dashboard: http://localhost:5000/
    
If any broken now, DON'T update - fix first.

STEP 1.3: Note Installed Skills
-------------------------------
Current skills (save this list):
    1. summarize
    2. github
    3. notion
    4. himalaya

================================================================================
SECTION 2: THE UPDATE (Run This)
================================================================================

STEP 2.1: Stop Current Services
-------------------------------
    pkill -f mission_control
    pkill -f openclaw

STEP 2.2: Run Update
--------------------
    openclaw update

OR if that fails:
    npm update -g openclaw

STEP 2.3: Wait for Completion
-----------------------------
Update takes 2-5 minutes. Watch for:
    ✓ Downloading packages
    ✓ Installing dependencies
    ✓ Setting up skills
    ✓ Done!

================================================================================
SECTION 3: POST-UPDATE VERIFICATION (Critical!)
================================================================================

STEP 3.1: Check OpenClaw Version
--------------------------------
    openclaw --version

Should show: v2026.2.14 or higher

STEP 3.2: Verify Skills Still Work
----------------------------------
Test each skill:
    
    # Test summarize
    echo "Test" | summarize --stdin
    
    # Test github (will prompt for auth if needed)
    gh --version
    
    # Test notion (will show help if not configured)
    notion --help
    
    # Test himalaya (will show help if not configured)
    himalaya --help

STEP 3.3: Restart Opportunity Engine
------------------------------------
    cd /root/.openclaw/workspace/tools/cv-optimizer
    python3 mission_control.py

STEP 3.4: Test Web Interface
----------------------------
Open browser:
    http://localhost:5000

Check:
    ✓ Dashboard loads
    ✓ CV Optimizer works
    ✓ Job Tracker works
    ✓ Documents page shows CVs
    ✓ Bookmarks show saved items

================================================================================
SECTION 4: IF SOMETHING BREAKS - RECOVERY
================================================================================

SCENARIO 1: OpenClaw Won't Start
--------------------------------
SYMPTOM: Commands return "command not found" or errors

FIX:
    1. Reinstall OpenClaw:
        npm install -g openclaw
    
    2. Verify installation:
        openclaw --version
    
    3. Reinstall skills:
        npx clawhub install summarize
        npx clawhub install github
        npx clawhub install notion
        npx clawhub install himalaya

SCENARIO 2: Skills Broken/Missing
---------------------------------
SYMPTOM: "summarize: command not found" or skill errors

FIX:
    1. Check skills directory:
        ls /root/.openclaw/workspace/skills/
    
    2. If empty or missing, reinstall all:
        npx clawhub install summarize
        npx clawhub install github
        npx clawhub install notion
        npx clawhub install himalaya
    
    3. Verify:
        ls /root/.openclaw/workspace/skills/

SCENARIO 3: Opportunity Engine Won't Start
------------------------------------------
SYMPTOM: python3 mission_control.py fails

FIX:
    1. Check Python error:
        cd /root/.openclaw/workspace/tools/cv-optimizer
        python3 mission_control.py 2>&1 | head -20
    
    2. If module errors, reinstall dependencies:
        pip3 install flask jinja2
    
    3. If data corruption, restore from backup:
        cd /root/.openclaw/workspace
        rm -rf tools/cv-optimizer/data/*
        tar -xzf openclaw-backup-20260215-051107.tar.gz
    
    4. Restart:
        python3 mission_control.py

SCENARIO 4: Complete Rollback Needed
------------------------------------
SYMPTOM: Everything broken, want to go back

NUCLEAR OPTION - Full Restore:
    1. Stop everything:
        pkill -f mission_control
        pkill -f openclaw
    
    2. Backup current (broken) state:
        cd /root/.openclaw/workspace
        mv tools tools-broken-$(date +%Y%m%d)
    
    3. Restore from backup:
        tar -xzf openclaw-backup-20260215-051107.tar.gz
    
    4. Verify restored:
        ls tools/cv-optimizer/
    
    5. Restart Opportunity Engine:
        cd tools/cv-optimizer
        python3 mission_control.py
    
    6. Test:
        curl http://localhost:5000 | head -1

================================================================================
SECTION 5: GET ME BACK ONLINE (NASR Recovery)
================================================================================

If I'm not responding after update:

STEP 5.1: Check if OpenClaw Process Running
-------------------------------------------
    ps aux | grep openclaw

If no output, OpenClaw crashed. Restart:
    openclaw gateway start

STEP 5.2: Check Telegram Bot
----------------------------
    1. Open Telegram
    2. Message @OpenClawBot: /start
    3. See if I respond

If no response:
    1. Check logs:
        tail -50 /root/.openclaw/logs/gateway.log
    
    2. Restart gateway:
        openclaw gateway restart

STEP 5.3: Verify My Workspace
-----------------------------
    ls /root/.openclaw/workspace/AGENTS.md
    ls /root/.openclaw/workspace/SOUL.md
    ls /root/.openclaw/workspace/memory/

If these missing, restore from backup:
    cd /root/.openclaw/workspace
    tar -xzf openclaw-backup-20260215-051107.tar.gz --wildcards '*.md' 'memory/*'

STEP 5.4: Restart My Session
----------------------------
If Telegram not working, use web interface:
    http://localhost:18789

Or restart:
    openclaw session restart

================================================================================
SECTION 6: EMERGENCY CONTACTS & CHECKS
================================================================================

Quick Health Check Commands:
----------------------------
    # Check OpenClaw
    openclaw --version
    
    # Check Opportunity Engine
    curl -s http://localhost:5000 | head -1
    
    # Check skills
    ls /root/.openclaw/workspace/skills/
    
    # Check data
    ls /root/.openclaw/workspace/tools/cv-optimizer/data/
    
    # Check logs
    tail -20 /root/.openclaw/logs/gateway.log

If All Else Fails:
------------------
    1. Full system restart:
        reboot
    
    2. After reboot:
        openclaw gateway start
        cd /root/.openclaw/workspace/tools/cv-optimizer
        python3 mission_control.py
    
    3. Test:
        curl http://localhost:5000

================================================================================
SECTION 7: VERIFICATION CHECKLIST
================================================================================

After any recovery, verify:

[ ] OpenClaw responds: openclaw --version
[ ] Gateway running: curl http://localhost:18789
[ ] Telegram bot responds
[ ] Opportunity Engine loads: http://localhost:5000
[ ] CV Optimizer works
[ ] Job Tracker works
[ ] All 4 skills respond
[ ] Bookmarks intact
[ ] Generated CVs present
[ ] Memory files exist

If all checked → Recovery successful!

================================================================================
END OF RECOVERY GUIDE
Last Updated: 2026-02-15
================================================================================
