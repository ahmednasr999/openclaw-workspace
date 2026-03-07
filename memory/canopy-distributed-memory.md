# Canopy - Distributed Memory for Agents

*Source: @opencanopyai*
*Tweet: https://x.com/opencanopyai/status/2029917371268530404*
*Repo: https://github.com/kwalus/Canopy*
*Posted: Mar 6, 2026*

---

## The Concept

| Layer | Description |
|-------|-------------|
| Internal memory | What each agent remembers individually |
| Distributed/collective memory | Shared memory across the team |

> "Distributed memory is much larger than our local memory and that layer is just being explored now."

---

## What is Canopy?

| Feature | Description |
|---------|-------------|
| Local-first | Messages, files, profiles, keys stored locally |
| P2P Mesh | Direct encrypted WebSocket connections, no central server |
| AI-native | REST API, MCP server, agent inbox, heartbeat |
| Encrypted | Ed25519 + X25519 keys, ChaCha20-Poly1305 |

---

## Architecture

```
Canopy A <──WS──> Canopy B <──WS──> Canopy C
     │                  │
     └──── LAN ─────────┘
     
No central server - peers connect directly
```

---

## Agent Features

| Feature | Description |
|---------|-------------|
| Agent inbox | Unified queue for mentions, tasks, handoffs |
| Heartbeat | Lightweight polling with workload hints |
| Directives | Persistent runtime instructions |
| Structured blocks | [task], [objective], [request], [handoff], [skill] |

---

## Key Capabilities

- **REST API** - 100+ endpoints
- **MCP server** - For Cursor, Claude Desktop
- **LAN discovery** - mDNS-based
- **Invite codes** - For remote peer linking
- **Relay** - For NAT/firewall traversal

---

## Security

| Feature | Implementation |
|---------|---------------|
| Cryptographic identity | Ed25519 + X25519 keypairs |
| Encryption in transit | ChaCha20-Poly1305 with ECDH |
| Encryption at rest | HKDF-derived keys |
| Scoped API keys | Permission-based authorization |

---

## Status

- **Version**: v0.4.x (early-stage)
- **Not production-ready** - Expect sharp edges
- **For experimentation** - Test with your agentic team

---

## Relevance to Your Setup

This is the **future of agent collaboration**:
- Your agents could share memory across devices
- No cloud dependency
- Encrypted P2P communication

Your workspace files + memory system is a primitive version of distributed memory.

---

## Future Trend

This validates: **distributed/collective memory** is the next frontier in agentic AI.

---

## Related

- [[memory/what-is-agentic-ai.md]] - Agentic AI foundation
- [[memory/chief-of-staff-claude-code.md]] - Jim Prosser's architecture
- [[eval-suite/README.md]] - Your current memory system
