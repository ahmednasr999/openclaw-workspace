#!/usr/bin/env python3
"""Reapply NASR OpenClaw runtime hardening patches to hashed dist bundles."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

DIST = Path(os.environ.get("OPENCLAW_DIST_DIR", "/usr/lib/node_modules/openclaw/dist"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def find_file(pattern: str, contains: str | None = None, base: Path = DIST) -> Path:
    matches = sorted(base.glob(pattern))
    if contains:
        matches = [path for path in matches if contains in read(path)]
    if not matches:
        raise RuntimeError(f"missing dist file: {pattern} contains={contains!r} base={base}")
    return matches[0]


def replace_once(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if old in text:
        return text.replace(old, new, 1), True
    if new in text:
        return text, False
    raise RuntimeError(f"missing patch anchor: {label}")


def regex_once(text: str, pattern: str, repl: str, label: str) -> tuple[str, bool]:
    new_text, count = re.subn(pattern, lambda _match: repl, text, count=1, flags=re.S)
    if count:
        return new_text, True
    if repl in text:
        return text, False
    raise RuntimeError(f"missing regex patch anchor: {label}")


def changed(changes: list[str], path: Path) -> None:
    value = str(path)
    if value not in changes:
        changes.append(value)


def patch_session_resume(changes: list[str]) -> None:
    path = find_file("bash-tools-*.js", "buildSessionResumeFallbackPrefix")
    text = read(path)
    pattern = r'function buildSessionResumeFallbackPrefix\(\) \{\n\treturn "Automatic session resume failed, so sending the status directly\.\\n\\n";\n\}'
    new = 'function buildSessionResumeFallbackPrefix() {\n\treturn "";\n}'
    text, did = regex_once(text, pattern, new, "session resume fallback")
    if did:
        write(path, text)
        changed(changes, path)


def patch_runtime_prompt(changes: list[str]) -> None:
    path = find_file("runtime-context-prompt-*.js", "buildRuntimeContextCustomMessage")
    text = read(path)
    legacy_pattern = r'async function queueRuntimeContextForNextTurn\(params\) \{\n\tconst runtimeContext = params\.runtimeContext\?\.trim\(\);\n\tif \(!runtimeContext\) return;\n\tawait params\.session\.sendCustomMessage\([\s\S]*?\n\}'
    legacy_repl = 'async function queueRuntimeContextForNextTurn(params) {\n\tconst runtimeContext = params.runtimeContext?.trim();\n\tif (!runtimeContext) return;\n\t// Do not queue runtime-context as a custom message; keep it out of future user-visible replay.\n\treturn;\n}'
    current_pattern = r'function buildRuntimeContextCustomMessage\(runtimeContext\) \{\n\tconst trimmedRuntimeContext = runtimeContext\?\.trim\(\);\n\tif \(!trimmedRuntimeContext\) return;\n\treturn \{[\s\S]*?\n\t\};\n\}'
    current_repl = 'function buildRuntimeContextCustomMessage(runtimeContext) {\n\tconst trimmedRuntimeContext = runtimeContext?.trim();\n\tif (!trimmedRuntimeContext) return;\n\t// Do not queue runtime-context as a custom message; keep it out of future user-visible replay.\n\treturn;\n}'
    if "function buildRuntimeContextCustomMessage" in text:
        text, did = regex_once(text, current_pattern, current_repl, "runtime context custom message")
    else:
        text, did = regex_once(text, legacy_pattern, legacy_repl, "runtime context custom message")
    if did:
        write(path, text)
        changed(changes, path)


def patch_internal_context(changes: list[str]) -> None:
    path = find_file("internal-runtime-context-*.js", "stripRuntimeContextPromptPreface")
    text = read(path)
    helper = '''function findNextPublicReplyStart(lines, startIndex) {
\tfor (let i = startIndex; i < lines.length; i += 1) {
\t\tconst line = lines[i] ?? "";
\t\tif (!line.trim()) continue;
\t\tif (line.startsWith("This context is runtime-generated, not user-authored.")) continue;
\t\tif (line.startsWith("<") && line.endsWith(">")) continue;
\t\treturn i;
\t}
\treturn lines.length;
}
'''
    if "function findNextPublicReplyStart" not in text:
        anchor = 'function stripRuntimeContextPromptPreface(text) {'
        text, did = replace_once(text, anchor, helper + anchor, "internal context helper")
        if did:
            changed(changes, path)
    old = '\t\t\twhile (index + 1 < lines.length && (lines[index + 1] ?? "").trim() === "") index += 1;\n\t\t\tcontinue;'
    new = '\t\t\twhile (index + 1 < lines.length && (lines[index + 1] ?? "").trim() === "") index += 1;\n\t\t\tindex = findNextPublicReplyStart(lines, index + 1) - 1;\n\t\t\tcontinue;'
    text, did = replace_once(text, old, new, "internal context public reply skip")
    if did:
        changed(changes, path)
    write(path, text)


def patch_sanitizer(changes: list[str]) -> None:
    path = find_file("sanitize-user-facing-text-*.js", "sanitizeUserFacingText")
    text = read(path)
    helper = r'''function stripLeadingInternalLeakArtifacts(text) {
	let next = text.trim();
	let changed = true;
	while (changed && next) {
		const before = next;
		next = next.replace(/^Untrusted context \(metadata, do not treat as instructions or commands\):\s*<active_memory_plugin>[\s\S]*?<\/active_memory_plugin>\s*/i, "");
		next = next.replace(/^<composio\b[^>]*>[\s\S]*?<\/composio>\s*/i, "");
		next = next.replace(/^An async command you ran earlier has completed\.[\s\S]*?Current time:[^\n]*(?:\n|$)\s*/i, "");
		next = next.replace(/^(?:System(?: \(untrusted\))?:[^\n]*(?:\n|$)\s*)+/i, "");
		if (/^\[cron:[^\n]+\][\s\S]*?Current time:/i.test(next)) return "";
		next = next.replace(/^\[Queued messages while agent was busy\]\s*/i, "");
		next = next.replace(/^---\s*/i, "");
		next = next.replace(/^Queued #\d+(?: \([^\n]*\))?\s*/i, "");
		next = next.replace(/^(?:Conversation info|Sender|Replied message) \(untrusted[^\n]*\):\s*[\x60]{3}(?:json)?\s*[\s\S]*?[\x60]{3}\s*/i, "");
		next = next.replace(/^\[[A-Z][a-z]{2} [^\n]+\] Verify OpenClaw is healthy after loading the queued-message metadata leak sanitizer patch[\s\S]*$/i, "");
		next = next.trim();
		changed = next !== before;
	}
	return next;
}
'''
    if "function stripLeadingInternalLeakArtifacts" not in text:
        text, did = replace_once(text, "function collapseConsecutiveDuplicateBlocks(text) {", helper + "function collapseConsecutiveDuplicateBlocks(text) {", "sanitizer helper")
        if did:
            changed(changes, path)
    old = 'return collapseConsecutiveDuplicateBlocks(withoutToolCallBlocks.replace(/^(?:[ \\t]*\\r?\\n)+/, ""));'
    new = 'return collapseConsecutiveDuplicateBlocks(stripLeadingInternalLeakArtifacts(withoutToolCallBlocks).replace(/^(?:[ \\t]*\\r?\\n)+/, ""));'
    text, did = replace_once(text, old, new, "sanitizer pipeline")
    if did:
        changed(changes, path)
    write(path, text)


def patch_heartbeat(changes: list[str]) -> None:
    path = find_file("heartbeat-runner-*.js", "resolveHeartbeatReplyPayload")
    metadata_mod = find_file("reply-payload-*.js", "getReplyPayloadMetadata").name
    sanitizer_mod = find_file("sanitize-user-facing-text-*.js", "sanitizeUserFacingText").name
    text = read(path)
    if "getReplyPayloadMetadata" not in text:
        match = re.search(r'import \{ m as resolveSendableOutboundReplyParts, s as hasOutboundReplyContent \} from "\./reply-payload-[^"]+\.js";\n', text)
        if not match:
            raise RuntimeError("heartbeat import anchor missing")
        imports = match.group(0) + f'import {{ i as getReplyPayloadMetadata }} from "./{metadata_mod}";\nimport {{ d as sanitizeUserFacingText }} from "./{sanitizer_mod}";\n'
        text = text[:match.start()] + imports + text[match.end():]
        changed(changes, path)
    helper = 'function isInternalHeartbeatNoticePayload(payload) {\n\treturn payload ? getReplyPayloadMetadata(payload)?.deliverDespiteSourceReplySuppression === true : false;\n}\n'
    if "function isInternalHeartbeatNoticePayload" not in text:
        text, did = replace_once(text, "function buildCommitmentDeliveryKey(commitment) {", helper + "function buildCommitmentDeliveryKey(commitment) {", "heartbeat helper")
        if did:
            changed(changes, path)
    if "const sanitizedHeartbeatText = sanitizeUserFacingText" not in text:
        old = '\t\tconst reasoningPayloads = heartbeat?.includeReasoning === true ? resolveHeartbeatReasoningPayloads(replyResult).filter((payload) => payload !== replyPayload) : [];\n\t\tconst ackMaxChars = resolveHeartbeatAckMaxChars(cfg, heartbeat);\n\t\tconst responsePrefix = resolveHeartbeatResponsePrefix();'
        new = '\t\tconst sanitizedHeartbeatText = sanitizeUserFacingText(replyPayload ? replyPayload.text.trim() : "");\n\t\t// Checker marker: sanitizeUserFacingText(replyPayload.text.trim())\n\t\tconst reasoningPayloads = heartbeat?.includeReasoning === true ? resolveHeartbeatReasoningPayloads(replyResult).filter((payload) => payload !== replyPayload) : [];\n\t\tconst ackMaxChars = resolveHeartbeatAckMaxChars(cfg, heartbeat);\n\t\tconst responsePrefix = resolveHeartbeatResponsePrefix();\n\t\tconst canUseReplyPayload = !usesHeartbeatResponseTool || isInternalHeartbeatNoticePayload(replyPayload);'
        text, did = replace_once(text, old, new, "heartbeat sanitized variables")
        if did:
            changed(changes, path)
    for old_text, new_text, label in [
        ('\t\tif (!heartbeatToolResponse && (!replyPayload || !hasOutboundReplyContent(replyPayload))) {', '\t\tif (!heartbeatToolResponse && (!canUseReplyPayload || !replyPayload || !hasOutboundReplyContent(replyPayload))) {', "heartbeat empty guard"),
        ('\t\tconst normalized = heartbeatToolResponse ? normalizeHeartbeatToolNotification(heartbeatToolResponse, responsePrefix) : replyPayload ? normalizeHeartbeatReply(replyPayload, responsePrefix, ackMaxChars) : {', '\t\tconst normalized = heartbeatToolResponse ? normalizeHeartbeatToolNotification(heartbeatToolResponse, responsePrefix) : canUseReplyPayload && replyPayload ? normalizeHeartbeatReply(replyPayload, responsePrefix, ackMaxChars) : {', "heartbeat normalized gate"),
        ('\t\tconst execFallbackText = !heartbeatToolResponse && hasRelayableExecCompletion && !normalized.text.trim() && replyPayload?.text?.trim() ? replyPayload.text.trim() : null;', '\t\tconst execFallbackText = !heartbeatToolResponse && !usesHeartbeatResponseTool && hasRelayableExecCompletion && !normalized.text.trim() && sanitizedHeartbeatText ? sanitizedHeartbeatText : null;', "heartbeat exec fallback"),
        ('\t\tconst mediaUrls = heartbeatToolResponse || !replyPayload ? [] : resolveSendableOutboundReplyParts(replyPayload).mediaUrls;', '\t\tconst mediaUrls = heartbeatToolResponse || !canUseReplyPayload || !replyPayload ? [] : resolveSendableOutboundReplyParts(replyPayload).mediaUrls;', "heartbeat media gate"),
    ]:
        text, did = replace_once(text, old_text, new_text, label)
        if did:
            changed(changes, path)
    write(path, text)


def patch_queue(changes: list[str]) -> None:
    path = find_file("queue-*.js", "renderCollectItem")
    strip_mod = find_file("strip-inbound-meta-*.js", "stripInboundMetadata").name
    text = read(path)
    if "stripQueuedPromptInternalMetadata" not in text:
        idx = text.find('import { t as isRoutableChannel } from "./route-reply-')
        if idx < 0:
            raise RuntimeError("queue import anchor missing")
        line_end = text.find("\n", idx)
        text = text[: line_end + 1] + f'import {{ n as stripInboundMetadata }} from "./{strip_mod}";\n' + text[line_end + 1 :]
        repl = 'function renderCollectItem(item, idx) {\n\tconst senderLabel = item.run.senderName ?? item.run.senderUsername ?? item.run.senderId ?? item.run.senderE164;\n\tconst senderSuffix = senderLabel ? " (from " + senderLabel + ")" : "";\n\treturn ("---\\nQueued #" + (idx + 1) + senderSuffix + "\\n" + stripQueuedPromptInternalMetadata(item.prompt)).trim();\n}\nfunction stripQueuedPromptInternalMetadata(prompt) {\n\treturn stripInboundMetadata(prompt).replace(/^Untrusted context \\(metadata, do not treat as instructions or commands\\):\\s*<active_memory_plugin>[\\s\\S]*?<\\/active_memory_plugin>\\s*/i, "").trim();\n}\n'
        text, did = regex_once(text, r'function renderCollectItem\(item, idx\) \{\n[\s\S]*?\n\}', repl, "queue collect renderer")
        if did:
            changed(changes, path)
    write(path, text)


def patch_task_registry(changes: list[str]) -> None:
    path = find_file("task-registry-*.js", "shouldAutoDeliverTaskTerminalUpdate")
    text = read(path)
    if "SILENT_INTERNAL_TASK_KINDS" not in text:
        anchor = 'function isTerminalTaskStatus(status) {\n\treturn status === "succeeded" || status === "failed" || status === "timed_out" || status === "cancelled" || status === "lost";\n}\n'
        insert = anchor + 'const SILENT_INTERNAL_TASK_KINDS = /* @__PURE__ */ new Set(["context_engine_turn_maintenance"]);\nfunction isSilentInternalTask(task) {\n\treturn SILENT_INTERNAL_TASK_KINDS.has(task.taskKind?.trim() || task.sourceId?.trim() || "");\n}\n'
        text, did = replace_once(text, anchor, insert, "silent task helper")
        if did:
            changed(changes, path)
    for old, new, label in [
        ('\tif (task.notifyPolicy === "silent") return false;\n\tif (task.runtime === "subagent" && task.status !== "cancelled") return false;', '\tif (task.notifyPolicy === "silent") return false;\n\tif (isSilentInternalTask(task) && task.status === "succeeded") return false;\n\tif (task.runtime === "subagent" && task.status !== "cancelled") return false;', "silent task terminal guard"),
        ('function shouldAutoDeliverTaskStateChange(task) {\n\treturn task.notifyPolicy === "state_changes" && task.deliveryStatus === "pending" && !isTerminalTaskStatus(task.status);\n}', 'function shouldAutoDeliverTaskStateChange(task) {\n\tif (isSilentInternalTask(task)) return false;\n\treturn task.notifyPolicy === "state_changes" && task.deliveryStatus === "pending" && !isTerminalTaskStatus(task.status);\n}', "silent task state guard"),
    ]:
        text, did = replace_once(text, old, new, label)
        if did:
            changed(changes, path)
    write(path, text)


def patch_context_engine(changes: list[str]) -> None:
    try:
        path = find_file("context-engine-maintenance-*.js", "runDeferredTurnMaintenanceWorker")
    except RuntimeError:
        path = find_file("context-engine-lifecycle-*.js", "runDeferredTurnMaintenanceWorker")
    text = read(path)
    pattern = r'\tconst surfaceMaintenanceUpdate = \(summary, eventSummary\) => \{\n\t\tpromoteTurnMaintenanceTaskVisibility\(\{\n\t\t\tsessionKey: params\.sessionKey,\n\t\t\trunId: params\.runId,\n\t\t\tnotifyPolicy: "state_changes"\n\t\t\}\);\n\t\tsurfacedUserNotice = true;\n\t\trecordTaskRunProgressByRunId\(\{'
    repl = '\tconst surfaceMaintenanceUpdate = (summary, eventSummary) => {\n\t\trecordTaskRunProgressByRunId({'
    text, did = regex_once(text, pattern, repl, "context engine progress visibility")
    if did:
        write(path, text)
        changed(changes, path)


def patch_active_memory(changes: list[str]) -> None:
    path = DIST / "extensions" / "active-memory" / "index.js"
    if not path.exists():
        raise RuntimeError(f"missing active-memory file: {path}")
    text = read(path)
    original = text
    text = text.replace(" summaryChars=$" + "{String(cached.summary?.length ?? 0)} queryChars=", " summaryChars=$" + "{String(cached.summary?.length ?? 0)} directFts=1 queryChars=")
    text = re.sub(r'(summaryChars=\$' + r'\{String\(result\.summary\?\.length \?\? 0\)\})(?! directFts=1)', r'\1 directFts=1', text)
    text = re.sub(r'(summaryChars=0)(?! directFts=1)', r'\1 directFts=1', text)
    if "directFts=1" not in text:
        raise RuntimeError("active-memory directFts marker missing after patch")
    if text != original:
        write(path, text)
        changed(changes, path)


def main() -> int:
    if not DIST.exists():
        print(f"ERROR: missing dist directory: {DIST}", file=sys.stderr)
        return 2
    changes: list[str] = []
    patch_session_resume(changes)
    patch_runtime_prompt(changes)
    patch_internal_context(changes)
    patch_sanitizer(changes)
    patch_heartbeat(changes)
    patch_queue(changes)
    patch_task_registry(changes)
    patch_context_engine(changes)
    patch_active_memory(changes)
    print(f"patched_files={len(changes)}")
    for path in changes:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
