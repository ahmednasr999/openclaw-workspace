#!/usr/bin/env python3
import os, json, time, glob, datetime
from collections import defaultdict

BASE = '/root/.openclaw/workspace/logs'
os.makedirs(BASE, exist_ok=True)
TRANSPORT_LOG = os.path.join(BASE, 'transport-layer.jsonl')
AGENT_LOG = os.path.join(BASE, 'agent-exec-layer.jsonl')
DELAY_LOG = os.path.join(BASE, 'delivery-diagnostics.jsonl')
HEARTBEAT_LOG = os.path.join(BASE, 'heartbeat-telemetry.jsonl')
SESS_GLOB = '/root/.openclaw/agents/main/sessions/*.jsonl'

state_offsets = {}
session_ids = {}
pending = {}  # user_msg_id -> {ts, session_id, warned10, warned30, text}
last_model = 'unknown'
last_hb = 0

def now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

def append(path, obj):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')

def parse_ts(ts):
    return datetime.datetime.fromisoformat(ts.replace('Z',''))

def gateway_alive():
    return os.system('pgrep -x openclaw-gateway >/dev/null 2>&1') == 0

def queue_depth():
    # Best-effort: count pending inbound waiting for reply
    return len([p for p in pending.values() if not p.get('replied')])

def handle_event(path, ev):
    global last_model
    if ev.get('type') == 'session':
        sid = ev.get('id')
        if sid:
            session_ids[path] = sid
        return

    if ev.get('type') != 'message':
        return

    msg = ev.get('message', {})
    role = msg.get('role')
    ts = ev.get('timestamp') or now_iso()
    sid = session_ids.get(path)
    session_key = f'agent:main:main:{sid}' if sid else 'agent:main:main:unknown'

    if role == 'user':
        msg_id = ev.get('id')
        content = ''
        for c in msg.get('content', []):
            if c.get('type') == 'text':
                content += c.get('text', '')

        rec = {
            'timestamp': ts,
            'layer': 'transport',
            'direction': 'inbound',
            'provider': 'telegram',
            'update_id': None,
            'chat_id': 'telegram:866838380',
            'user_id': '866838380',
            'message_id': msg_id,
            'routing_decision': 'accepted_to_session',
            'accept_reject_reason': 'matched_active_direct_chat',
            'policy_filter_result': 'pass',
            'sessionKey_used': session_key
        }
        append(TRANSPORT_LOG, rec)
        pending[msg_id] = {
            'ts': ts,
            'session_id': sid,
            'warned10': False,
            'warned30': False,
            'replied': False,
            'message_id': msg_id,
            'text': content[:120]
        }
        return

    if role == 'assistant':
        parent = ev.get('parentId')
        model = msg.get('model') or msg.get('provider') or 'unknown'
        last_model = model
        rec = {
            'timestamp': ts,
            'layer': 'transport',
            'direction': 'outbound',
            'provider': 'telegram',
            'message_id': ev.get('id'),
            'in_reply_to': parent,
            'delivery': 'attempted',
            'sessionKey_used': session_key,
            'model': model
        }
        append(TRANSPORT_LOG, rec)

        exec_rec = {
            'timestamp': ts,
            'layer': 'agent_execution',
            'session_id': sid,
            'message_id': ev.get('id'),
            'parent_id': parent,
            'model': model,
            'stopReason': msg.get('stopReason'),
            'usage': msg.get('usage', {})
        }
        append(AGENT_LOG, exec_rec)

        if parent in pending:
            pending[parent]['replied'] = True
            # Keep it for audit but no further alerts


def scan_files():
    files = sorted(glob.glob(SESS_GLOB))
    for p in files:
        if p not in state_offsets:
            state_offsets[p] = 0
        try:
            size = os.path.getsize(p)
            if state_offsets[p] > size:
                state_offsets[p] = 0
            with open(p, 'r', encoding='utf-8') as f:
                f.seek(state_offsets[p])
                for line in f:
                    line=line.strip()
                    if not line:
                        continue
                    try:
                        ev=json.loads(line)
                    except Exception:
                        continue
                    handle_event(p, ev)
                state_offsets[p] = f.tell()
        except FileNotFoundError:
            continue


def check_delays():
    now = datetime.datetime.utcnow()
    for mid, item in list(pending.items()):
        if item.get('replied'):
            continue
        age = (now - parse_ts(item['ts'])).total_seconds()
        if age >= 10 and not item['warned10']:
            item['warned10'] = True
            append(DELAY_LOG, {
                'timestamp': now_iso(),
                'event': 'Delayed reply warning',
                'wait_seconds': int(age),
                'model_used': last_model,
                'queue_size': queue_depth(),
                'tool_activity': 'unknown',
                'runId': None,
                'session_id': item.get('session_id'),
                'inbound_message_id': mid
            })
        if age >= 30 and not item['warned30']:
            item['warned30'] = True
            append(DELAY_LOG, {
                'timestamp': now_iso(),
                'event': 'Message gap diagnostic',
                'wait_seconds': int(age),
                'session_id': item.get('session_id'),
                'inbound_message_id': mid,
                'note': 'No outbound reply observed within 30s after inbound acceptance'
            })


def heartbeat():
    global last_hb
    now = time.time()
    if now - last_hb < 60:
        return
    last_hb = now
    append(HEARTBEAT_LOG, {
        'timestamp': now_iso(),
        'gateway_alive': gateway_alive(),
        'active_sessions_observed': len(session_ids),
        'model_health': {'last_model_seen': last_model},
        'queue_depth': queue_depth()
    })


def main():
    while True:
        scan_files()
        check_delays()
        heartbeat()
        time.sleep(1.0)

if __name__ == '__main__':
    main()
