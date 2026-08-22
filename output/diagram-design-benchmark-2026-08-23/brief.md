# Diagram benchmark brief

## Decision question

Can an executive understand, in under 20 seconds, why the hardened OpenClaw runtime accepts normal Telegram work while rejecting unsafe ingress and blind recovery?

## Required content

- Ahmed's Telegram DM is the permitted intake.
- The gateway is the privileged gate into an isolated agent runtime.
- The bearer identity was rotated and its `0600` state matched both processes.
- Recovery now requires evidence before reset.
- Public webhook ingress remains disabled.
- Blind force reset has been removed and must stop before execution.
- Security proof is the audit destination (`19/19`; zero failures in the final suite).

## Output constraints

- Audience: executive.
- Destination: 16:9 slide / browser artifact.
- Static, self-contained HTML with inline SVG.
- Maximum eight components and three trust zones.
- No runtime internals, individual test cases, ports, or deployment detail.

## Scoring rubric (100)

- Executive comprehension in 20 seconds: 30
- Route and boundary semantics: 25
- Visual hierarchy and polish: 20
- Accessibility and validation: 15
- Production effort and reuse: 10
