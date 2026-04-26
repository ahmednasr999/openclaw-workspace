# Task Receipts and Proof

Last updated: 2026-04-21
Owner: NASR
Status: proposed spec
Purpose: define how OpenClaw should represent proof-sensitive side effects so completion is evidence-based instead of assumption-based.

## Problem

Today a task can succeed technically while the real-world outcome is still unverified.

Examples:
- a LinkedIn post creation call succeeds but read-back fails
- a message send call returns success but the target thread is not confirmed
- a gateway restart succeeds but the live process is not yet verified healthy
- an export file is written but not visually validated

The system needs a first-class proof model.

## Principle

For proof-sensitive work, `success` and `verified` are different states.

A tool-side success means the mutation likely happened.
A verified receipt means the mutation has evidence.

## Receipt object

```ts
export type TaskReceipt = {
  receiptId: string;
  receiptType: string;
  ownerKey?: string;
  sessionKey?: string;
  agentId?: string;
  runId?: string;
  taskId?: string;
  targetSystem: string;
  targetRef?: string;
  artifactPaths?: string[];
  verificationStatus: "verified" | "unverified" | "failed";
  verificationEvidence?: string[];
  createdAt: number;
  metadata?: Record<string, unknown>;
};
```

## Receipt types

Recommended initial values:
- `linkedin_post`
- `message_send`
- `gateway_restart`
- `gateway_config_change`
- `file_export`
- `issue_create`
- `issue_update`
- `cron_external_mutation`

## Verification statuses

### verified
Use when there is direct evidence.

Examples:
- post URL or share URN confirmed
- message id confirmed in expected target
- process restarted and new PID plus health probe confirmed
- export rendered and visually checked

### unverified
Use when the action likely succeeded but proof is incomplete.

Examples:
- post create call succeeded, read-back failed due permission limits
- file exists, but no render/inspection happened yet
- send returned success, but target verification was not possible

### failed
Use when verification definitively failed or the side effect itself failed.

Examples:
- publish API returned error
- restart returned but health probe failed
- render failed and no readable artifact exists

## Task linkage

Task records should not duplicate entire receipts.

They should only carry enough receipt summary to explain state:
- `proofRequired?: boolean`
- `proofStatus?: "missing" | "verified" | "failed"`
- `latestReceiptId?: string`
- `verificationRule?: string`

## User-facing language

### Allowed
- `Published successfully. Proof verified.`
- `Posted successfully. Proof not yet verified.`
- `Restart completed. Health probe verified.`

### Avoid
- `Done.` when proof is missing
- `Posted successfully` if the only evidence is a likely-but-unverified tool response and the wording would imply stronger certainty than exists

## First workflows to adopt

### LinkedIn posting
Verification evidence can include:
- share URN
- post URL
- readable confirmation from provider
- optional screenshot

### Gateway/config changes
Verification evidence can include:
- process PID changed
- health endpoint / RPC probe ok
- config validation passed

### External messaging
Verification evidence can include:
- provider message id
- thread id
- confirmed destination target

## Storage strategy

Recommended first version:
- append receipt JSONL log
- reference latest receipt id from task record

Why:
- low migration risk
- easy auditability
- good fit for incremental rollout

## Minimal operator behavior

The operator should be able to inspect:
- latest receipt for a task
- whether proof is missing
- what exact evidence was used

## Definition of done

This spec is successful when:
- proof-sensitive workflows stop pretending proof exists when it does not
- task outputs clearly distinguish success from verification
- receipts become a reusable primitive rather than a custom one-off pattern in every workflow
