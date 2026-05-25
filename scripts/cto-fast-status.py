#!/usr/bin/env python3
from __future__ import annotations
import json, sqlite3, subprocess, time
from pathlib import Path

def run(args, timeout=2):
    try:
        return subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    except Exception as e:
        return type('R', (), {'returncode': 99, 'stdout': '', 'stderr': str(e)})()

now=int(time.time()*1000)
print('FAST STATUS')
r=run(['systemctl','--user','show','openclaw-gateway','--property=ActiveState,SubState,MainPID,ActiveEnterTimestamp'],3)
print('gateway=' + ('unknown' if r.returncode else r.stdout.strip().replace('\n','; ')))
try:
    con=sqlite3.connect('/root/.openclaw/tasks/runs.sqlite', timeout=1); cur=con.cursor()
    rows=cur.execute("select status, count(*) from task_runs group by status order by status").fetchall()
    active=cur.execute("select task_id,task_kind,owner_key,created_at,error from task_runs where status in ('running','queued') order by created_at desc limit 8").fetchall()
    slow=cur.execute("select task_id,task_kind,owner_key,status,created_at from task_runs where status='running' and ?-created_at>300000 order by created_at limit 8",(now,)).fetchall()
    ctx=cur.execute("select status,notify_policy,delivery_status,count(*) from task_runs where task_kind='context_engine_turn_maintenance' group by status,notify_policy,delivery_status").fetchall()
    print('tasks_by_status=' + ', '.join(f'{a}:{b}' for a,b in rows))
    print('active_tasks=' + (json.dumps(active,ensure_ascii=False) if active else 'none'))
    print('slow_tasks_5m=' + (json.dumps(slow,ensure_ascii=False) if slow else 'none'))
    print('context_maintenance=' + (json.dumps(ctx,ensure_ascii=False) if ctx else 'none'))
except Exception as e: print('tasks_error=' + str(e))
try:
    jobs_raw=json.loads(Path('/root/.openclaw/cron/jobs.json').read_text()).get('jobs',{})
    jobs={j.get('id'): j for j in jobs_raw} if isinstance(jobs_raw, list) else jobs_raw
    state=json.loads(Path('/root/.openclaw/cron/jobs-state.json').read_text()).get('jobs',{})
    errs=[]
    for jid, st in state.items():
        s=st.get('state',{}) if isinstance(st,dict) else {}
        if s.get('lastRunStatus')=='error' or s.get('lastStatus')=='error' or s.get('consecutiveErrors',0):
            errs.append({'id':jid,'name':jobs.get(jid,{}).get('name'), 'errors':s.get('consecutiveErrors'), 'summary':s.get('lastDiagnosticSummary') or s.get('lastError')})
    print('cron_errors=' + (json.dumps(errs[:10],ensure_ascii=False) if errs else 'none'))
except Exception as e: print('cron_error=' + str(e))
try:
    paired=json.loads(Path('/root/.openclaw/nodes/paired.json').read_text())
    nodes=[{'name':v.get('displayName'),'version':v.get('version'),'lastConnectedAtMs':v.get('lastConnectedAtMs'),'commands':v.get('commands')} for v in paired.values()]
    print('nodes=' + json.dumps(nodes,ensure_ascii=False))
except Exception as e: print('nodes_error=' + str(e))
print('model_usage=use /status for exact live model quota')
