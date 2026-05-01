# Tailscale hardening plan - 2026-05-01

## Current state

- `tailscaled` is active and enabled.
- VPS tailnet IPv4 observed previously: `100.99.230.14`.
- Tailscale helps reduce public admin surface, but it does not fix local kernel privilege-escalation CVEs.

## Goal

Keep only genuinely public services exposed publicly. Move administrative access behind Tailscale where safe.

## Safe staged plan

1. Confirm out-of-band console access from the VPS provider.
2. Confirm Ahmed's Mac/iPad can reach the VPS over Tailscale.
3. Confirm SSH works over the tailnet IP before changing public firewall rules.
4. Snapshot current firewall and sshd config.
5. Restrict SSH to tailnet only, preferably by firewall first, not sshd config first.
6. Keep public 80/443 only if they are intentionally serving public endpoints.
7. Keep OpenClaw gateway bound to loopback/private access, not public internet.
8. Verify access from both tailnet and provider console after each step.

## Approval gate

Do not change SSH/firewall rules without explicit approval in the same maintenance window. Main risk is locking Ahmed out of the VPS.

## Verification after changes

- `tailscale status` shows Ahmed device online.
- `ssh root@100.99.230.14` or equivalent succeeds from trusted device.
- Public scan no longer shows SSH if SSH is intended tailnet-only.
- `openclaw status` remains healthy after firewall changes.
