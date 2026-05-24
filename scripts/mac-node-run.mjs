#!/usr/bin/env node
import crypto from "node:crypto";
import { t as callGatewayTool } from "/usr/lib/node_modules/openclaw/dist/gateway-BQ6GcHQN.js";
import { t as formatExecCommand } from "/usr/lib/node_modules/openclaw/dist/system-run-command-oKbHuJTE.js";

const nodeId =
  process.env.OPENCLAW_NODE ||
  "f43e25edb0df8786349f43738612bed403b7df5f225eb3617232d5b630ba1207";
const argv = process.argv.slice(2);
const rawCommand = formatExecCommand(argv);

if (argv.length === 0) {
  console.error("usage: mac-node-run.mjs <executable> [args...]");
  process.exit(2);
}

const result = await callGatewayTool(
  "node.invoke",
  { timeoutMs: Number(process.env.OPENCLAW_INVOKE_TIMEOUT_MS || 120000) },
  {
    nodeId,
    command: "system.run",
    timeoutMs: Number(process.env.OPENCLAW_INVOKE_TIMEOUT_MS || 120000),
    params: {
      command: argv,
      rawCommand,
      cwd: "/Users/ahmednasr",
      timeoutMs: Number(process.env.OPENCLAW_RUN_TIMEOUT_MS || 90000),
      agentId: "main",
      sessionKey: "agent:main:telegram:direct:866838380",
      runId: crypto.randomUUID(),
      suppressNotifyOnExit: true,
    },
    idempotencyKey: crypto.randomUUID(),
  }
);

console.log(JSON.stringify(result, null, 2));
