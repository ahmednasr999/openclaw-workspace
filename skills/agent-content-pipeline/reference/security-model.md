# Security Model

The security model separates drafting (AI) from approval/posting (human):

- ✅ Agent drafts content
- ✅ Agent revises based on feedback
- ❌ Agent cannot approve (human approves via `content review`)
- ❌ Agent cannot post

Posting is handled manually via CLI — never by the agent directly.

## Platform Auth Table

| Platform | Auth Storage | Encrypted? | Password Required? |
|----------|--------------|------------|-------------------|
| LinkedIn | Browser profile | ✅ Yes | ✅ Yes |
| X/Twitter | Firefox tokens | ✅ Yes | ✅ Yes |

Both platforms require password to post. Tokens are extracted from Firefox and encrypted locally.
