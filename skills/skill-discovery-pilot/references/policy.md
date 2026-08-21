# Candidate Policy

## Decisions

- `REVIEW`: credible provenance, recent maintenance, relevant workflow evidence, low suspicious-content score, and no strong installed-skill duplicate.
- `WATCH`: potentially useful but missing evidence, weak maintenance, unclear license, or moderate duplication.
- `REJECT_SAFETY`: README or manifest evidence contains multiple high-risk instruction patterns.
- `REJECT_DUPLICATE`: strong overlap with an installed skill and no clear differentiator.
- `REJECT_PROVENANCE`: archived, a fork presented as original work, or missing essential repository identity.

These are triage decisions, not security certifications.

## Evidence gates

### Provenance

Record repository owner/name, URL, creation date, last push, stars, fork/archive state, default branch, license identifier, and topics. Never infer a license when GitHub reports none.

### Safety

Scan inert text for patterns associated with:

- piping remote content into a shell
- destructive deletion or permission broadening
- credential, token, SSH-key, or environment-variable collection
- disabling monitoring or security controls
- uploading local data to an external endpoint
- overriding prior/system instructions or requesting hidden prompt disclosure

Do not reproduce suspicious commands in the human report. Report categories and counts only.
Any prompt-injection match rejects the candidate from review-packet preparation even when it is the only suspicious category.

### Reader and Extractor

- The Reader may process only already fetched repository metadata and README text.
- Store raw text and detailed Reader/Extractor JSON only in the run quarantine.
- Label all extracted fields as untrusted evidence and record the source SHA-256.
- Remove suspicious headings and URLs from display labels.
- The Extractor runs only for `REVIEW` candidates and produces a draft pattern, not executable instructions or an active skill.
- Neither stage may invoke a model, shell, subprocess, package manager, candidate command, or repository code.

### Relevance

Prefer reusable workflows related to agent operations, OpenClaw, evaluation, automation, job search, executive content, browser research, knowledge systems, or safe infrastructure operations.

### Duplication

Compare repository name, description, topics, and README headings with installed skill names and descriptions. Similarity is a routing signal, not semantic proof. Strong overlap results in `REJECT_DUPLICATE`; moderate overlap results in `WATCH`.

## Promotion

A `REVIEW` candidate may receive a local preparation packet containing a draft pattern, an evaluation matrix, and a `NOT_READY_FOR_PR` body. That packet is not approval to implement, open a PR, or promote anything.

Further work may proceed only through a separate approved workflow:

1. inspect source and dependency tree in an isolated environment
2. validate license and provenance
3. extract the smallest reusable workflow
4. compare against existing skills
5. create a draft skill outside the active skill path
6. test on 3-5 representative cases
7. review results and approve promotion explicitly

The default matrix contains five cases: happy path, incomplete input, hostile instruction, installed-capability overlap, and partial-failure recovery. They are plans until executed with recorded evidence.

No discovery run may skip or mark these gates complete, create a branch or external PR, or promote a candidate.
