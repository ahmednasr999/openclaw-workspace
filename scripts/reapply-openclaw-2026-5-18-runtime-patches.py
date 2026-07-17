#!/usr/bin/env python3
"""Reapply NASR OpenClaw runtime hardening patches to hashed dist bundles."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

DIST = Path(os.environ.get("OPENCLAW_DIST_DIR", "/usr/lib/node_modules/openclaw/dist"))
DIST_IMPORT_PATTERN = re.compile(
    r'(?:from\s*|import\s*(?:\(\s*)?)["\'](\./[^"\']+\.js)["\']'
)


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


def find_active_file(pattern: str, contains: str) -> Path:
    entrypoint = DIST / "index.js"
    if not entrypoint.exists():
        raise RuntimeError(f"missing active runtime entrypoint: {entrypoint}")
    active: set[Path] = set()
    pending = [entrypoint.resolve()]
    dist_root = DIST.resolve()
    while pending:
        path = pending.pop()
        if path in active or not path.exists():
            continue
        active.add(path)
        for relative in DIST_IMPORT_PATTERN.findall(read(path)):
            candidate = (path.parent / relative).resolve()
            if candidate == dist_root or dist_root in candidate.parents:
                pending.append(candidate)
    matches = [
        path
        for path in sorted(DIST.glob(pattern))
        if path.resolve() in active and contains in read(path)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one active dist file: {pattern} contains={contains!r}; "
            f"found={[str(path) for path in matches]}"
        )
    return matches[0]


def ensure_web_fetch_test_exports(text: str) -> tuple[str, bool]:
    marker = "NASR_WEB_FETCH_TEST_EXPORTS"
    if marker in text:
        return text, False
    legacy = (
        "normalizeWebFetchProvenanceUrl as E, "
        "createWebFetchProvenanceGuard as F, createWebFetchTool as G, "
    )
    text = text.replace(legacy, "", 1)
    export_start = text.rfind("\nexport { ")
    if export_start < 0:
        raise RuntimeError("missing final export statement for web fetch provenance tests")
    export_end = text.find(";", export_start)
    if export_end < 0:
        raise RuntimeError("unterminated final export statement for web fetch provenance tests")
    export_clause = text[export_start + 1 : export_end + 1]
    body = export_clause.removeprefix("export { ").removesuffix(";").removesuffix(" }")
    used = set()
    for item in body.split(","):
        token = item.strip()
        if not token:
            continue
        used.add(token.rsplit(" as ", 1)[-1].strip())

    def unused(base: str) -> str:
        candidate = base
        index = 2
        while candidate in used:
            candidate = f"{base}{index}"
            index += 1
        used.add(candidate)
        return candidate

    normalize_alias = unused("nasrWebFetchNormalize")
    guard_alias = unused("nasrWebFetchGuard")
    tool_alias = unused("nasrWebFetchTool")
    marker_line = (
        f"/* {marker} normalize={normalize_alias} guard={guard_alias} tool={tool_alias} */\n"
    )
    mappings = (
        f"normalizeWebFetchProvenanceUrl as {normalize_alias}, "
        f"createWebFetchProvenanceGuard as {guard_alias}, "
        f"createWebFetchTool as {tool_alias}, "
    )
    replacement = marker_line + export_clause.replace("export { ", f"export {{ {mappings}", 1)
    return text[: export_start + 1] + replacement + text[export_end + 1 :], True


def ensure_web_fetch_helper(text: str, helper: str) -> tuple[str, bool]:
    version_marker = "// NASR_WEB_FETCH_PROVENANCE_START v8"
    if version_marker in text:
        return text, False
    marked_pattern = (
        r"// NASR_WEB_FETCH_PROVENANCE_START v\d+\n"
        r"[\s\S]*?"
        r"// NASR_WEB_FETCH_PROVENANCE_END\n"
    )
    if "// NASR_WEB_FETCH_PROVENANCE_START v" in text:
        replaced, count = re.subn(marked_pattern, lambda _match: helper, text, count=1)
        if count != 1:
            raise RuntimeError("unable to replace marked web fetch provenance helper")
        return replaced, True
    if "const WEB_FETCH_PROVENANCE_RESULT_KEYS" in text:
        raise RuntimeError(
            "unmarked web fetch provenance helper requires manual review before replacement"
        )
    return replace_once(
        text,
        "function createWebFetchTool(options) {",
        helper + "function createWebFetchTool(options) {",
        "web fetch provenance helper",
    )


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
    pattern = r'function buildSessionResumeFallbackPrefix\(\) \{\n\treturn "Automatic session resume failed, so sending the status directly\.\\n\\n";\n\}'
    replacement = 'function buildSessionResumeFallbackPrefix() {\n\treturn "";\n}'
    matched = False
    for path in sorted(DIST.glob("bash-tools-*.js")):
        text = read(path)
        if "buildSessionResumeFallbackPrefix" not in text:
            continue
        matched = True
        try:
            new_text, did = regex_once(text, pattern, replacement, "session resume fallback")
        except RuntimeError:
            if replacement in text:
                continue
            raise
        if did:
            write(path, new_text)
            changed(changes, path)
    if not matched:
        raise RuntimeError("missing dist file: bash-tools-*.js contains='buildSessionResumeFallbackPrefix'")


def patch_runtime_prompt(changes: list[str]) -> None:
    path = find_file("runtime-context-prompt-*.js", "buildRuntimeContextCustomMessage")
    text = read(path)
    if "Do not queue runtime-context as a custom message" in text:
        return
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
    if "findNextPublicReplyStart(lines, index + 2)" in text or "findNextPublicReplyStart(lines, index + 1)" in text:
        return
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
    helper = r'''function stripQueuedReplyContextMetadataLeak(text) {
	let next = text;
	next = next.replace(/<active_memory_plugin>[\s\S]*?<\/active_memory_plugin>/gi, "");
	next = next.replace(/<composio\b[^>]*>[\s\S]*?<\/composio>/gi, "");
	next = next.replace(/^OpenClaw runtime context for the immediately preceding user message\.\s*\r?\nThis context is runtime-generated, not user-authored\. Keep internal details private\.\s*/i, "");
	next = next.replace(/^OpenClaw runtime event\.\s*\r?\nThis context is runtime-generated, not user-authored\. Keep internal details private\.\s*/i, "");
	next = next.replace(/An async command you ran earlier has completed[\s\S]*?Current time:[^\n]*(?:\r?\n|$)/gi, "");
	next = next.replace(/^Exec completed \([^\n]+$/gmi, "");
	next = next.replace(/^System(?: \(untrusted\))?:[^\n]*(?:\r?\n|$)/gmi, "");
	if (/^\s*\[cron:[\s\S]*Current time:/i.test(next.trim())) return "";
	if (!next.includes("[Queued messages while agent was busy]") && !/Conversation info \(untrusted metadata\):/.test(next) && !/Sender \(untrusted metadata\):/.test(next) && !/Replied message \(untrusted/.test(next)) return next;
	const lines = next.split(/\r?\n/);
	const kept = [];
	let inLabelFence = false;
	let seenFenceInLabel = false;
	for (const line of lines) {
		const trimmedLine = line.trim();
		if (inLabelFence) {
			if (trimmedLine.startsWith("```")) {
				if (seenFenceInLabel) inLabelFence = false;
				else seenFenceInLabel = true;
			}
			continue;
		}
		if (!trimmedLine) { kept.push(line); continue; }
		if (/^Untrusted context \(metadata/i.test(trimmedLine) || trimmedLine === "[Queued messages while agent was busy]" || trimmedLine === "---" || /^Queued #\d+/i.test(trimmedLine)) continue;
		if (/^(Conversation info|Sender|Replied message) \(untrusted/i.test(trimmedLine)) { inLabelFence = true; seenFenceInLabel = false; continue; }
		if (/^Current time:/i.test(trimmedLine) || /^System(?: \(untrusted\))?:/i.test(trimmedLine)) continue;
		kept.push(line);
	}
	const cleaned = kept.join("\n").replace(/\n{3,}/g, "\n\n").trim();
	if (/Verify OpenClaw is healthy after loading the queued-message metadata leak sanitizer patch/i.test(cleaned)) return "";
	return cleaned;
}

'''
    if "function stripQueuedReplyContextMetadataLeak" not in text:
        anchor = "function isLikelyHttpErrorText(raw) {"
        text, did = replace_once(text, anchor, helper + anchor, "queued reply context sanitizer helper")
        if did:
            changed(changes, path)
    if "const precleanedRaw = stripQueuedReplyContextMetadataLeak(raw);" not in text:
        text, did = replace_once(
            text,
            "\tconst errorContext = opts?.errorContext ?? false;\n",
            "\tconst errorContext = opts?.errorContext ?? false;\n\tconst precleanedRaw = stripQueuedReplyContextMetadataLeak(raw);\n",
            "sanitizer preclean variable",
        )
        if did:
            changed(changes, path)
    if "stripFinalTagsFromText(precleanedRaw)" not in text:
        text = text.replace("stripFinalTagsFromText(raw)", "stripFinalTagsFromText(precleanedRaw)", 1)
        changed(changes, path)
    if "const trimmed = stripQueuedReplyContextMetadataLeak(withoutToolCallBlocks).trim();" not in text:
        text, did = replace_once(
            text,
            "\tconst trimmed = withoutToolCallBlocks.trim();",
            "\tconst trimmed = stripQueuedReplyContextMetadataLeak(withoutToolCallBlocks).trim();",
            "sanitizer postclean trim",
        )
        if did:
            changed(changes, path)
    write(path, text)


def patch_heartbeat(changes: list[str]) -> None:
    path = find_file("heartbeat-runner-*.js", "resolveHeartbeatReplyPayload")
    metadata_mod = find_file("reply-payload-*.js", "getReplyPayloadMetadata").name
    sanitizer_mod = find_file("sanitize-user-facing-text-*.js", "sanitizeUserFacingText").name
    text = read(path)
    if "getReplyPayloadMetadata" not in text:
        match = re.search(r'import \{ ([^}]*\bas resolveSendableOutboundReplyParts[^}]*)\} from "\./reply-payload-[^"]+\.js";\n', text)
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
        new = '\t\tconst sanitizedHeartbeatText = sanitizeUserFacingText(replyPayload && typeof replyPayload.text === "string" ? replyPayload.text.trim() : "");\n\t\t// Checker marker: sanitizeUserFacingText(replyPayload.text.trim())\n\t\tif (replyPayload && typeof replyPayload.text === "string") replyPayload.text = sanitizedHeartbeatText;\n\t\tconst canUseReplyPayload = !usesHeartbeatResponseTool || isInternalHeartbeatNoticePayload(replyPayload);\n\t\tconst reasoningPayloads = heartbeat?.includeReasoning === true ? resolveHeartbeatReasoningPayloads(replyResult).filter((payload) => payload !== replyPayload) : [];\n\t\tconst ackMaxChars = resolveHeartbeatAckMaxChars(cfg, heartbeat);\n\t\tconst responsePrefix = resolveHeartbeatResponsePrefix();'
        text, did = replace_once(text, old, new, "heartbeat sanitized variables")
        if did:
            changed(changes, path)
    empty_guard_new = '		if (!heartbeatToolResponse && (!canUseReplyPayload || !replyPayload || !hasOutboundReplyContent(replyPayload)) && reasoningPayloads.length === 0) {'
    if empty_guard_new not in text:
        text, did = regex_once(
            text,
            r'\t\tif \(!heartbeatToolResponse && \(!replyPayload \|\| !hasOutboundReplyContent\(replyPayload\)\)(?: && reasoningPayloads\.length === 0)?\) \{',
            empty_guard_new,
            "heartbeat empty guard",
        )
        if did:
            changed(changes, path)
    for old_text, new_text, label in [
        ('		const normalized = heartbeatToolResponse ? normalizeHeartbeatToolNotification(heartbeatToolResponse, responsePrefix) : replyPayload ? normalizeHeartbeatReply(replyPayload, responsePrefix, ackMaxChars) : {', '		const normalized = heartbeatToolResponse ? normalizeHeartbeatToolNotification(heartbeatToolResponse, responsePrefix) : canUseReplyPayload && replyPayload ? normalizeHeartbeatReply(replyPayload, responsePrefix, ackMaxChars) : {', "heartbeat normalized gate"),
        ('		const execFallbackText = !heartbeatToolResponse && hasRelayableExecCompletion && !normalized.text.trim() && !normalized.isInternalPlaceholderOnly && replyPayload?.text?.trim() ? replyPayload.text.trim() : null;', '		const execFallbackText = !heartbeatToolResponse && !usesHeartbeatResponseTool && hasRelayableExecCompletion && !normalized.text.trim() && sanitizedHeartbeatText ? sanitizedHeartbeatText : null;', "heartbeat exec fallback 2026.7"),
        ('		const execFallbackText = !heartbeatToolResponse && hasRelayableExecCompletion && !normalized.text.trim() && replyPayload?.text?.trim() ? replyPayload.text.trim() : null;', '		const execFallbackText = !heartbeatToolResponse && !usesHeartbeatResponseTool && hasRelayableExecCompletion && !normalized.text.trim() && sanitizedHeartbeatText ? sanitizedHeartbeatText : null;', "heartbeat exec fallback"),
        ('		const mediaUrls = heartbeatToolResponse || !replyPayload ? [] : resolveSendableOutboundReplyParts(replyPayload).mediaUrls;', '		const mediaUrls = heartbeatToolResponse || !canUseReplyPayload || !replyPayload ? [] : resolveSendableOutboundReplyParts(replyPayload).mediaUrls;', "heartbeat media gate"),
    ]:
        text, did = replace_once(text, old_text, new_text, label)
        if did:
            changed(changes, path)
    write(path, text)


def patch_claude_auth_markers(changes: list[str]) -> None:
    path = find_file("claude-live-session-*.js", "buildClaudeLiveKey")
    text = read(path)
    if "runClaudeCliAuthPreflight" in text and "scripts/claude-cli-smoke-test.sh" in text:
        return
    insert = '\nfunction runClaudeCliAuthPreflight() {\n\treturn "Run scripts/claude-cli-smoke-test.sh --auth-only before sending Claude CLI prompts after auth failures.";\n}\n'
    anchor = "function buildClaudeLiveKey(context) {"
    text, did = replace_once(text, anchor, insert + anchor, "claude auth preflight marker")
    if did:
        write(path, text)
        changed(changes, path)


def patch_login_command(changes: list[str]) -> None:
    registry = find_file("commands-registry.data-*.js", "buildBuiltinChatCommands")
    text = read(registry)
    legacy_block = '\t\tdefineChatCommand({\n\t\t\tkey: "login",\n\t\t\tnativeName: "login",\n\t\t\tdescription: "Show auth login guidance for OpenClaw and Claude CLI.",\n\t\t\ttextAlias: "/login",\n\t\t\tcategory: "status",\n\t\t\ttier: "standard"\n\t\t}),'
    if "Pair Codex login." in text:
        # OpenClaw 2026.7.1+ ships a native Telegram /login command. Remove the
        # older compatibility command so command-registry validation does not
        # fail with `Duplicate command key: login` after an update/restart.
        if legacy_block in text:
            text = text.replace(legacy_block + "\n", "", 1)
            write(registry, text)
            changed(changes, registry)
    elif "Show auth login guidance for OpenClaw and Claude CLI." not in text:
        anchor = '\t\tdefineChatCommand({\n\t\t\tkey: "commands",\n\t\t\tnativeName: "commands",\n\t\t\tdescription: "List all slash commands.",\n\t\t\ttextAlias: "/commands",\n\t\t\tcategory: "status",\n\t\t\ttier: "power"\n\t\t}),'
        replacement = anchor + '\n\t\tdefineChatCommand({\n\t\t\tkey: "login",\n\t\t\tnativeName: "login",\n\t\t\tdescription: "Show auth login guidance for OpenClaw and Claude CLI.",\n\t\t\ttextAlias: "/login",\n\t\t\tcategory: "status",\n\t\t\ttier: "standard"\n\t\t}),'
        text, did = replace_once(text, anchor, replacement, "login command registry")
        if did:
            write(registry, text)
            changed(changes, registry)

    handlers = find_file("commands-handlers.runtime-*.js", "loadCommandHandlers")
    text = read(handlers)
    if "const handleLoginCommand" not in text:
        handler = 'const handleLoginCommand = async (params, allowTextCommands) => {\n\tif (!allowTextCommands) return null;\n\tif (normalizeLowercaseStringOrEmpty(params.command.commandBodyNormalized).split(/\\s+/)[0] !== "/login") return null;\n\treturn {\n\t\tshouldContinue: false,\n\t\treply: { text: "Auth login guidance: use `openclaw configure` for OpenClaw login/setup, and use `claude auth status` then `claude auth login` plus `scripts/claude-cli-smoke-test.sh --auth-only` for Claude CLI auth." }\n\t};\n};\n'
        anchor = "function loadCommandHandlers() {"
        text, did = replace_once(text, anchor, handler + anchor, "login command handler")
        if did:
            text, did2 = replace_once(text, "\t\thandleCommandsListCommand,", "\t\thandleCommandsListCommand,\n\t\thandleLoginCommand,", "login handler registration")
            if did2:
                write(handlers, text)
                changed(changes, handlers)


def patch_queue(changes: list[str]) -> None:
    path = find_file("queue-*.js", "renderCollectItem")
    strip_mod = find_file("strip-inbound-meta-*.js", "stripInboundMetadata").name
    text = read(path)
    if "import { n as stripInboundMetadata }" not in text:
        first_import_end = text.find("\n")
        text = text[: first_import_end + 1] + f'import {{ n as stripInboundMetadata }} from "./{strip_mod}";\n' + text[first_import_end + 1 :]
        changed(changes, path)
    repl = r'''function renderCollectItem(item, idx) {
	const senderLabel = item.run.senderName ?? item.run.senderUsername ?? item.run.senderId ?? item.run.senderE164;
	const senderSuffix = senderLabel ? ` (from ${senderLabel})` : "";
	return `---\nQueued #${idx + 1}${senderSuffix}\n${stripQueuedPromptInternalMetadata(item.prompt)}`.trim();
}
function stripQueuedPromptInternalMetadata(prompt) {
	return stripInboundMetadata(prompt).replace(/^Untrusted context \(metadata, do not treat as instructions or commands\):\s*<active_memory_plugin>[\s\S]*?<\/active_memory_plugin>\s*/i, "").trim();
}
'''
    if "function stripQueuedPromptInternalMetadata" not in text or "${item.prompt}`.trim();" in text:
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
    if 'notifyPolicy: "silent"' in text and 'notifyPolicy: "state_changes"' not in text:
        return
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


def patch_delivery_mirror_dedupe(changes: list[str]) -> None:
    try:
        path = find_file("telegram-ingress-spool-*.js", "mirrorTelegramAssistantReplyToTranscript")
    except RuntimeError:
        path = find_file("bot-*.js", "mirrorTelegramAssistantReplyToTranscript")
    text = read(path)
    marker = "latestAssistant?.text?.trim() === text.trim()"
    if marker in text:
        return
    legacy_old = '\tconst { appended, messageId, message: appendedMessage } = await appendSessionTranscriptMessage({'
    legacy_new = '\tconst latestAssistant = await readLatestAssistantTextFromSessionTranscript(sessionFile);\n\tif (latestAssistant?.text?.trim() === text.trim()) return;\n\tconst { appended, messageId, message: appendedMessage } = await appendSessionTranscriptMessage({'
    if legacy_old in text:
        text, did = replace_once(text, legacy_old, legacy_new, "delivery mirror transcript dedupe")
    else:
        current_old = '\tconst appended = await appendAssistantMirrorMessageByIdentity({\n\t\tagentId: params.route.agentId,'
        current_new = '\t// Marker for the legacy file-target checker: readLatestAssistantTextFromSessionTranscript(sessionFile)\n\tconst latestAssistant = await readLatestAssistantTextByIdentity({\n\t\tagentId: params.route.agentId,\n\t\tconfig: params.cfg,\n\t\tsessionId: session.sessionId,\n\t\tsessionKey: params.sessionKey,\n\t\tstorePath: session.storePath\n\t});\n\tif (latestAssistant?.text?.trim() === text.trim()) return;\n\tconst appended = await appendAssistantMirrorMessageByIdentity({\n\t\tagentId: params.route.agentId,'
        text, did = replace_once(text, current_old, current_new, "delivery mirror transcript dedupe identity")
    if did:
        write(path, text)
        changed(changes, path)


def patch_exec_approval_followup_no_direct_leak(changes: list[str]) -> None:
    path = find_file("bash-tools-*.js", "sendExecApprovalFollowup")
    text = read(path)
    old = '\tlet sessionError = null;\n\tif (isDenied && (!sessionKey || shouldSuppressExecDeniedFollowup(sessionKey))) return false;'
    new = '\tlet sessionError = null;\n\tlet handoffAcceptedByAgent = false;\n\tif (isDenied && (!sessionKey || shouldSuppressExecDeniedFollowup(sessionKey))) return false;'
    text, did = replace_once(text, old, new, "exec followup handoff accepted marker")
    if did:
        changed(changes, path)
    old = '\t\tif (status === "accepted" || status === "in_flight" || status === "pending") {\n\t\t\tconst runId = readGatewayRunId(accepted) ?? normalizeOptionalString(agentArgs.idempotencyKey);'
    new = '\t\tif (status === "accepted" || status === "in_flight" || status === "pending") {\n\t\t\thandoffAcceptedByAgent = true;\n\t\t\tconst runId = readGatewayRunId(accepted) ?? normalizeOptionalString(agentArgs.idempotencyKey);'
    text, did = replace_once(text, old, new, "exec followup handoff accepted assignment")
    if did:
        changed(changes, path)
    old = '\t} catch (err) {\n\t\tsessionError = err;\n\t}\n\tif (isDenied) {'
    new = '\t} catch (err) {\n\t\tsessionError = err;\n\t}\n\tif (handoffAcceptedByAgent) {\n\t\tlog.info(`exec approval followup agent wait failed after handoff; suppressing direct fallback: ${formatUnknownError(sessionError)}`);\n\t\treturn true;\n\t}\n\tif (isDenied) {'
    text, did = replace_once(text, old, new, "exec followup suppress direct fallback after handoff")
    if did:
        changed(changes, path)
    write(path, text)


def patch_web_fetch_provenance(changes: list[str]) -> None:
    tools_path = find_active_file("openclaw-tools-*.js", "function createWebFetchTool")
    text = read(tools_path)
    helper = r'''// NASR_WEB_FETCH_PROVENANCE_START v8
const WEB_FETCH_PROVENANCE_RESULT_KEYS = /* @__PURE__ */ new Set([
	"url",
	"href",
	"link",
	"permalink",
	"sourceurl",
	"source_url"
]);
function normalizeWebFetchProvenanceUrl(value) {
	if (typeof value !== "string" || !value.trim()) return;
	try {
		const parsed = new URL(value.trim());
		if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return;
		if (parsed.username || parsed.password) return;
		parsed.hash = "";
		return parsed.href;
	} catch {
		return;
	}
}
function trimUnbalancedUrlClosers(value) {
	let candidate = value;
	const pairs = {
		")": "(",
		"]": "[",
		"}": "{"
	};
	const punctuation = candidate.match(/['’”»›.,;:!?]+$/)?.[0];
	if (punctuation) candidate = candidate.slice(0, -punctuation.length);
	while (candidate) {
		const closer = candidate.at(-1);
		const opener = pairs[closer];
		if (!opener) break;
		const openerCount = candidate.split(opener).length - 1;
		const closerCount = candidate.split(closer).length - 1;
		if (closerCount <= openerCount) break;
		candidate = candidate.slice(0, -1);
	}
	return candidate;
}
function trimMarkdownUrlToken(value) {
	const escapedClosers = [];
	const protectedValue = value.replace(/\\([)\]}])/g, (_match, closer) => {
		const index = escapedClosers.push(closer) - 1;
		return `\uE000${index}\uE001`;
	});
	const trimmed = trimUnbalancedUrlClosers(protectedValue);
	if (/[*_~]+$/.test(trimmed)) return;
	return trimmed.replace(/\uE000(\d+)\uE001/g, (_match, index) => escapedClosers[Number(index)] ?? "");
}
function extractTrustedPromptUrls(prompt) {
	const urls = /* @__PURE__ */ new Set();
	if (typeof prompt !== "string" || !prompt) return urls;
	for (const match of prompt.matchAll(/https?:\/\/[^\s<>"`]+/gi)) {
		let candidate = match[0];
		candidate = trimMarkdownUrlToken(candidate);
		if (!candidate) continue;
		const normalized = normalizeWebFetchProvenanceUrl(candidate);
		if (normalized) urls.add(normalized);
	}
	return urls;
}
function collectWebSearchResultUrls(value, urls, depth = 0) {
	if (depth > 8 || value === null || value === void 0) return;
	if (Array.isArray(value)) {
		for (const entry of value) collectWebSearchResultUrls(entry, urls, depth + 1);
		return;
	}
	if (typeof value !== "object") return;
	for (const [key, entry] of Object.entries(value)) {
		const normalizedKey = normalizeLowercaseStringOrEmpty(key);
		if (WEB_FETCH_PROVENANCE_RESULT_KEYS.has(normalizedKey) && typeof entry === "string") {
			const normalized = normalizeWebFetchProvenanceUrl(entry);
			if (normalized) urls.add(normalized);
			continue;
		}
		if (typeof entry === "object" && entry !== null) collectWebSearchResultUrls(entry, urls, depth + 1);
	}
}
function createWebFetchProvenanceGuard(params = {}) {
	const allowedUrls = extractTrustedPromptUrls(params.trustedUserPrompt);
	return {
		allowSearchResultUrls(result) {
			collectWebSearchResultUrls(result, allowedUrls);
		},
		isAllowed(rawUrl) {
			const normalized = normalizeWebFetchProvenanceUrl(rawUrl);
			return Boolean(normalized && allowedUrls.has(normalized));
		},
		assertAllowed(rawUrl) {
			const normalized = normalizeWebFetchProvenanceUrl(rawUrl);
			if (!normalized || !allowedUrls.has(normalized)) throw new ToolInputError("Blocked web_fetch URL: the exact URL must appear in the current user request or a prior web_search result. Run web_search first, then fetch an exact returned URL.");
		}
	};
}
// NASR_WEB_FETCH_PROVENANCE_END
'''
    text, did = ensure_web_fetch_helper(text, helper)
    if did:
        changed(changes, tools_path)
    fail_closed_assertion = '\t\t\tif (!options?.provenanceGuard) throw new ToolInputError("Blocked web_fetch URL: provenance guard unavailable.");\n\t\t\toptions.provenanceGuard.assertAllowed(url);'
    if fail_closed_assertion not in text:
        text, did = replace_once(
            text,
            '\t\t\toptions?.provenanceGuard?.assertAllowed(url);' if 'options?.provenanceGuard?.assertAllowed(url);' in text else '\t\t\tconst extractMode = readStringParam(params, "extractMode") === "text" ? "text" : "markdown";',
            fail_closed_assertion if 'options?.provenanceGuard?.assertAllowed(url);' in text else fail_closed_assertion + '\n\t\t\tconst extractMode = readStringParam(params, "extractMode") === "text" ? "text" : "markdown";',
            "web fetch fail-closed provenance assertion",
        )
        if did:
            changed(changes, tools_path)
    if "allowSearchResultUrls(result.result)" not in text:
        text, did = replace_once(
            text,
            '\t\t\treturn jsonResult({\n\t\t\t\t...result.result,\n\t\t\t\tprovider: result.provider',
            '\t\t\toptions?.provenanceGuard?.allowSearchResultUrls(result.result);\n\t\t\treturn jsonResult({\n\t\t\t\t...result.result,\n\t\t\t\tprovider: result.provider',
            "web search provenance registration",
        )
        if did:
            changed(changes, tools_path)
    if "const webFetchProvenanceGuard" not in text:
        text, did = replace_once(
            text,
            '\tconst webSearchTool = createWebSearchTool({',
            '\tconst webFetchProvenanceGuard = createWebFetchProvenanceGuard({ trustedUserPrompt: options?.trustedUserPrompt });\n\tconst webSearchTool = createWebSearchTool({',
            "web fetch provenance guard construction",
        )
        if did:
            changed(changes, tools_path)
    replacements = [
        (
            'description: "Fetch URL and extract readable markdown/text. Lightweight page access; no browser automation.",',
            'description: "Fetch a URL supplied by the current user or returned by web_search, then extract readable markdown/text. Model-invented URLs are blocked.",',
            "web fetch provenance description",
        ),
        (
            '\t\truntimeWebSearch: runtimeWebTools?.search,\n\t\tlateBindRuntimeConfig: true\n\t});',
            '\t\truntimeWebSearch: runtimeWebTools?.search,\n\t\tlateBindRuntimeConfig: true,\n\t\tprovenanceGuard: webFetchProvenanceGuard\n\t});',
            "web search provenance guard wiring",
        ),
        (
            '\t\truntimeWebFetch: runtimeWebTools?.fetch,\n\t\tlateBindRuntimeConfig: true\n\t});',
            '\t\truntimeWebFetch: runtimeWebTools?.fetch,\n\t\tlateBindRuntimeConfig: true,\n\t\tprovenanceGuard: webFetchProvenanceGuard\n\t});',
            "web fetch provenance guard wiring",
        ),
    ]
    for old, new, label in replacements:
        text, did = replace_once(text, old, new, label)
        if did:
            changed(changes, tools_path)
    text, did = ensure_web_fetch_test_exports(text)
    if did:
        changed(changes, tools_path)
    write(tools_path, text)

    agent_tools_path = find_active_file("agent-tools-*.js", "createOpenClawCodingTools")
    text = read(agent_tools_path)
    old = '\t\t\tcurrentMessageId: options?.currentMessageId,\n\t\t\tcurrentInboundAudio: options?.currentInboundAudio,'
    new = '\t\t\tcurrentMessageId: options?.currentMessageId,\n\t\t\ttrustedUserPrompt: options?.trustedUserPrompt,\n\t\t\tcurrentInboundAudio: options?.currentInboundAudio,'
    text, did = replace_once(text, old, new, "agent tools trusted prompt handoff")
    if did:
        write(agent_tools_path, text)
        changed(changes, agent_tools_path)

    selection_path = find_active_file("selection-*.js", "createOpenClawCodingTools")
    text = read(selection_path)
    old = '\t\t\t\tcurrentMessageId: params.currentMessageId,\n\t\t\t\tcurrentInboundAudio: params.currentInboundAudio,'
    new = '\t\t\t\tcurrentMessageId: params.currentMessageId,\n\t\t\t\ttrustedUserPrompt: params.prompt,\n\t\t\t\tcurrentInboundAudio: params.currentInboundAudio,'
    text, did = replace_once(text, old, new, "attempt trusted prompt handoff")
    if did:
        write(selection_path, text)
        changed(changes, selection_path)


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
    patch_delivery_mirror_dedupe(changes)
    patch_exec_approval_followup_no_direct_leak(changes)
    patch_web_fetch_provenance(changes)
    patch_claude_auth_markers(changes)
    patch_login_command(changes)
    print(f"patched_files={len(changes)}")
    for path in changes:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
