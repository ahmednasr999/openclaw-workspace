import { EgressProvenancePolicy } from "./policy.js";

const BLOCK_REASON =
  "Blocked outbound navigation: the exact URL was neither supplied by the user in this run nor returned as a structured web_search result.";

function normalizedRunId(value) {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function resolveRunIdentity(event, ctx) {
  const eventRunId = normalizedRunId(event?.runId);
  const contextRunId = normalizedRunId(ctx?.runId);
  const conflict = Boolean(eventRunId && contextRunId && eventRunId !== contextRunId);
  return {
    eventRunId,
    contextRunId,
    conflict,
    runId: conflict ? null : eventRunId || contextRunId,
  };
}

export function resolveConsistentRunId(event, ctx) {
  return resolveRunIdentity(event, ctx).runId;
}

function resolvePolicyRunId(policy, event, ctx) {
  const identity = resolveRunIdentity(event, ctx);
  if (identity.conflict) {
    policy.endRun(identity.eventRunId);
    policy.endRun(identity.contextRunId);
  }
  return identity.runId;
}

export function createMemoryHeistGuard(policy = new EgressProvenancePolicy()) {
  return {
    id: "memory-heist-guard",
    name: "Memory Heist Egress Guard",
    description: "Blocks native web navigation to URLs without user or web-search provenance.",
    register(api) {
      api.on("message_received", (event, ctx) => {
        const runId = resolvePolicyRunId(policy, event, ctx);
        if (runId) policy.beginRun(runId, event?.content);
      });

      api.on("before_tool_call", (event, ctx) => {
        const runId = resolvePolicyRunId(policy, event, ctx);
        const decision = policy.authorize(event?.toolName, event?.params, runId ?? undefined);
        if (decision.allowed) return;
        return { block: true, blockReason: BLOCK_REASON };
      });

      api.on("after_tool_call", (event, ctx) => {
        const runId = resolvePolicyRunId(policy, event, ctx);
        if (event?.toolName !== "web_search" || event?.error) return;
        if (runId) policy.recordSearchResults(runId, event?.result);
      });

      api.on("agent_end", (event, ctx) => {
        const runId = resolvePolicyRunId(policy, event, ctx);
        if (runId) policy.endRun(runId);
      });

      api.logger.info?.("memory-heist-guard v1.0.2: strict search-result provenance guard active");
    },
  };
}

export default createMemoryHeistGuard();
