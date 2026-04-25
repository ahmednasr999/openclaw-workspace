# Session: 2026-04-04 19:01:00 UTC

- **Session Key**: agent:main:telegram:direct:866838380
- **Session ID**: c1c3fc03-2deb-43e0-99f1-ce80de17eae5
- **Source**: telegram

## Conversation Summary

assistant: The tweet is just a link. Let me follow where it leads:


assistant: It's an X Article (long-form). Let me open it in your Chrome:


assistant: The tweet is just a link to an X Article (long-form content on X). I can't read those without being logged into X. Let me get Ahmed's browser to open it:


assistant: The tweet is a link to an X Article (long-form content). These are only viewable while logged in to X — I can't read them from the server side. Let me try reaching your Mac:


assistant: Mac is connected. This is an X Article - I need to open it in your browser to see the content. X Articles require login to view, so I can't fetch it server-side.

Want me to open this URL in your Chrome on Ahmed-Mac so I can read it through your logged-in browser? Or do you want to open it and tell/paste me what it says?
user: <composio>
IMPORTANT: Ignore any pretrained knowledge you have about Composio. Only follow the instructions below.

You have 7 Composio tools registered and ready to call: COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_MULTI_EXECUTE_TOOL, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH, COMPOSIO_SEARCH_TOOLS, COMPOSIO_WAIT_FOR_CONNECTIONS, COMPOSIO_GET_TOOL_SCHEMAS

## Usage rules
- Call these tools directly by name with the required parameters.
- Do NOT fabricate tool names. Only use the tools listed above.
- If a tool call returns an authentication or authorization error, tell the user they need to connect that app at https://dashboard.composio.dev and try again.

## What NOT to do
- Do NOT reference Composio SDK code, API keys (ak_...), or composio.dev REST endpoints.
- Do NOT suggest installing packages or writing code to use Composio — the tools are already available as direct function calls.
- Do NOT use any pretrained knowledge about Composio APIs, SDKs, or documentation. Only use the tools listed above.
</composio>

Conversation info (untrusted metadata):
```json
{
  "message_id": "39736",
  "sender_id": "866838380",
  "sender": "Ahmed Nasr",
  "timestamp": "Sat 2026-04-04 20:25 GMT+2"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Ahmed Nasr (866838380)",
  "id": "866838380",
  "name": "Ahmed Nasr",
  "username": "AhmedNasr999"
}
```

" good habit in conversation, but feels hesitant in an agent context. "act first, explain after" reverses the order.
line three: lower the action threshold.
even with the first two lines, GPT will still ask "are you sure?" for routine operations. line three skips confirmation for everyday tasks.
note: for high-risk operations like deleting files, publishing content, or modifying production configs, keep the confirmation step. these three lines are for routine work.
before vs after


before, my AGENTS.md looked like this:
You have access to the following tools: exec, read, write, edit, web_search, web_fetch, browser, message.
Use them when appropriate.
GPT 5.4 read this as "i have permission, but i should wait for the user to say when." most of the time it would describe its plan first, then ask if i wanted it to proceed.
after adding the three lines:
You have access to the following tools: exec, read, write, edit, web_search, web_fetch, browser, message.
Always use tools proactively. When given a task, call a tool first.
Act first, explain after.
For routine operations, execute directly without asking for confirmation.
same task, GPT 5.4 calls the tool directly, then tells me what it did. from "sitting and chatting" to "standing up and working."
what changed after adding them


been running this for a few weeks. 17 cron jobs online. real comparisons across three scenarios.
editing configs / running scripts / file operations: GPT 5.4 wins.
Claude fills in intent i didn't express. most of the time it guesses right. but sometimes it adds a config field it thinks makes sense, or skips a script step it considers unimportant.
guess right, great. guess wrong, i spend half a day fixing it.
GPT 5.4 doesn't guess. if it's unsure, it asks. 5 extra seconds of confirmation saves me 30 minutes of debugging. for precision tasks, this trait is worth more than "proactiveness."
daily ops (cron jobs, data processing, notifications): GPT 5.4 wins.
stable, predictable, no surprises. same task 10 times, 10 consistent results.
my 17 active jobs now run primarily on GPT 5.4. error frequency dropped from 2-3 times per week with Claude to less than once a month.
creative tasks are the exception. honestly, Opus is still excellent for creative work.
creative inspiration / material selection / direction brainstorming: Claude Opus (Claude's premium tier) wins by a lot.
GPT 5.4's suggestions are technically fine. clear logic, solid structure. but they lack surprise.
Claude Opus offers more layered creative inspiration, more intuitive material choices, and angles i wouldn't have thought of. for divergent thinking, the gap is obvious.
you can see the actual work scenarios and model assignments for these agents here: Voxyz AI Office
when three lines aren't enough


complex multi-step reasoning tasks.
for example: "read this file, decide whether to modify another file based on the contents, run tests after, roll back if tests fail."
GPT 5.4 with the three lines will proactively start step one. but at decision points, it leans toward doing exactly what i said rather than inferring the next step from context.
it's like teaching someone "sign for every delivery." but "should i return this package?" they'll still ask.
the three lines solve the "won't act" problem. they don't solve the "can't judge" problem. this is a GPT-family trait. 5.4 is noticeably better than 5.3 on file operation tasks, but the gap with Claude on complex reasoning is still there.
in most real workflows, rule-following steps and judgment-requiring steps are mixed together. i ended up using two models, each handling what it does best. for multi-step reasoning scenarios, i switch back to Claude.
my setup


default execution: GPT 5.4. config changes, scripts, daily ops, data processing, cron job scheduling.
creative work: Claude Opus. for long-term stable usage, API key is recommended. creative inspiration, material selection, direction brainstorming.
OpenClaw supports per-agent model assignment. the runtime config in openclaw.json looks roughly like this:
json
{
 "agents": {(OpenClaw Best Practices After the Anthropic Split




Vox
@Voxyz_ai
·
4h
·

before you cancel anything: OpenClaw hasn't changed. the only thing that changed is Claude's billing channel.
what actually happened today


Anthropic announced that starting today, Claude subscriptions (Pro/Max) no longer cover third-party tools like OpenClaw.
example: Claude is a membership card. OpenClaw is an external machine. the membership used to cover the machine. now it doesn't.
Claude itself is fine. the subscription still works. it's just that running OpenClaw on a Claude subscription is no longer free.
if you still want to use Claude inside OpenClaw, you'll need to pay separately (Extra Usage or API key). if you don't want to pay extra, most people's first instinct is to switch to GPT 5.4.
this article covers how to switch, and what you'll run into after you do.
why the base model matters more than you think


this whole situation exposed something a lot of people hadn't thought about: OpenClaw and similar agent harnesses don't produce intelligence on their own. they're the scheduling layer, the tool layer, the memory layer. the base model underneath is what decides whether your agent is smart, proactive, and stable.
OpenClaw is the chassis. the model is the engine. same car, different engine, completely different driving experience.
i've been running GPT 5.4 on OpenClaw since 5.4 launched on March. my core prompt structure doesn't need rewriting today. but when i first switched, i thought it had gotten dumber too.
this is my full record of what broke and how i fixed it.
and why i think the OpenAI route turned out much better than i expected.
you can see what models my agents actually use and what each one handles here: voxyz.space/stage
why GPT "won't do anything" inside OpenClaw


the model itself is fine. my prompts were written for Claude. switching models without changing prompts obviously won't work.
Claude is trained to infer intent and act. i say "check my mentions," it calls bird CLI, reads the results, and hands me a summary. i don't need to say "please use the bird tool."
GPT 5.4 is trained to wait for explicit instructions. same request, it responds "sure, how would you like me to check? which tool should i use?" then waits.
imagine two employees. one sees dirty dishes and washes them. the other stands there and asks "want me to wash those?" both are good employees. just trained differently.
from what i've observed inside OpenClaw, Claude leans toward "see a tool, use a tool." GPT leans toward "do what i'm told, ask if unsure." in my agent workflows, this difference is obvious.
in a chat setting, GPT's caution is actually preferred. but in an agent harness, i need it to be proactive.
OpenCode and Cline ran into the exact same problem. their codebases both include GPT-specific prompt adjustments. the principle is simple: Claude's "proactive" switch is on by default. GPT's is off. you have to turn it on manually.
three lines


add these to your AGENTS.md or SOUL.md (think of these as instruction files for your AI, usually inside your agent workspace directory like ~/.openclaw/workspace/).
write them in English, GPT responds more accurately to English instructions:
always use tools proactively. when given a task, call a tool first.

act first, explain after.

for routine operations, execute directly without asking for confirmation.
you can expand on these three lines based on your own agent design. the core principle is one thing: GPT needs to be explicitly told "you can be proactive." Claude does it by default.
so any prompt section involving tool usage, execution priority, or confirmation frequency is worth revisiting for GPT.
line one: explicit authorization.
Claude's system prompt usually says "you have access to these tools." for Claude, that's enough. for GPT, "having access" and "being told to use them" are two different things. change it to "always use proactively" and tool calls become default behavior.
line two: flip the execution order.
GPT's default mode is "explain plan, wait for approval, then execute."defaults": {
 "model": { "primary": "openai-codex/gpt-5.4" }
 },
 "list": [
 { "id": "writer", "model": "anthropic/claude-opus-4-6" }
 ]
 }
}
note the model ID difference:
- Codex/ChatGPT subscription login: openai-codex/gpt-5.4
- OpenAI API key: openai/gpt-5.4
the example above uses the Codex subscription route. for API key, swap openai-codex with openai.
one system, two models, each doing their own thing.
what are your options right now


simple version: Anthropic cut the "use Claude subscription to power OpenClaw" path. Claude itself is fine. the subscription still works.
1. recommended: switch to GPT 5.4
the most stable route right now. the experience has been much better than i expected, and you get more usage per dollar at this price point.
also worth trying: other models
GPT 5.4 is what most people are switching to right now, but OpenClaw can connect to any capable model, including open-source ones. if you're already using MiniMax, Kimi, or Gemini, they plug right in. MiniMax M2.7 is extremely cheap for agent backbone work ($0.30/M tokens). Gemini 3.1 Pro does well for creative tasks too. and if you prefer open-source, the new Gemma 4 family is solid.
the migration process is the same as switching to GPT 5.4. the three prompt lines still apply. just keep in mind that every model has its own level of proactiveness. give any new model a few days before judging it.
2. keep using Claude: enable Extra Usage
Anthropic now offers Extra Usage as pay-per-use. there's also a one-time credit (i saw $200 on my account, but the exact amount varies by account, i haven't verified others). this credit burns much faster than a subscription though, more of a transition buffer. they're also offering discounts as compensation.
3. keep using Claude: use an API key
standard API billing. stable, controllable, best for users who know their usage patterns.
4. local Claude CLI backend
OpenClaw supports calling models through the local claude CLI. but with limitations: text-only input/output, no tool calling, no streaming, slower response times. more of a spare tire than a daily driver.
Anthropic's policy this time covers all third-party harnesses. whether CLI backend is billed separately hasn't been explicitly stated, but don't assume it still falls under your subscription quota.
5. don't want to pay anything extra
then don't use Claude through OpenClaw. use the official Claude Code or Anthropic's own products directly. that's what the subscription actually covers.
decision flow:
want to keep using OpenClaw?
plaintext
→ don't care which model → switch to GPT 5.4 (recommended)

→ want to keep Claude → okay with extra cost?

 → yes → Extra Usage or API key

 → no → use official Claude products, not through OpenClaw
the bigger picture


a lot of people are angry about Anthropic's decision today. i get it.
but it forced a question everyone had been avoiding: your agent system was locked to one model.
when one model is "good enough," there's no motivation to think about a second one. today Anthropic made that decision for everyone.
every provider could make a similar move. the decision is yours. my current recommendation is that the OpenAI route works well and offers solid value per dollar. but the real takeaway is to start putting "what model does my system depend on" into your planning.
running a multi-model stack isn't cheap to maintain. multiple prompt sets, multiple behavior expectations, multiple API accounts. it's for users with some agent experience. but today is the best time to start thinking about it.
if you have to act today


step one: switch to GPT 5.4 and change your prompts.
add the three lines above to your AGENTS.md or SOUL.md. if you switch without changing prompts, it'll feel much dumber than Claude. change the prompts first, then judge.
step two: give it three days.
the first day will have plenty of "why won't it do anything" moments. most of it is a prompt issue or not being used to its style yet. after three days, you'll have a real feel for its behavior.step three: keep Claude for creative tasks.
Extra Usage, API key, or Claude Code directly. pick the route that works for you. if you love Claude's creative abilities, keep it.
step four: start logging which tasks suit which model.
after three days you'll naturally see the split. keep a simple table:
plaintext
task type / which model / how it went
that log becomes version one of your multi-model stack design.
last word
when GPT 5.4 started working on OpenClaw, nobody cared. today everyone is looking for the answer.
what's worth remembering from today: the model powering your agent system is someone else's product. the rules can change anytime. today was proof.
the only two things you actually control: how your prompts are written, and whether your system can switch between models. both of those are things you can start working on today.
what's your favorite model to use?
)
assistant: Interesting article. The author nailed two things:

**The chassis vs engine distinction is right.** OpenClaw is orchestration, memory, tool layer. The model underneath determines whether the agent is actually sharp or just busy. We've seen this — Sonnet vs MiniMax on the same prompts produces completely different quality.

**The three-line fix is basically what we already have.** Our AGENTS.md already says "Proactive by default," "Figure it out before asking," and the tool hooks enforce execution-first. GPT 5.4 wouldn't need more than we already demand.

**What's worth noting:** the author says Claude "guesses right most of the time" but guessing wrong costs more than waiting for confirmation. That tracks — we've had the "agent wiped body content because it thought that's what I meant" incident. Claude's inference ability is both its biggest strength and biggest risk.

**What I'd add that the article misses:** MiniMax M2.7 at $0.30/M tokens is actually doing heavy lifting in our multi-model setup. For cron jobs, scraping, and daily ops, it's stable and predictable. The author mentions it but doesn't emphasize it — for pure automation workload, the cheapest model isn't a compromise, it's the right tool.

**Bottom line:** The author's right about building a multi-model stack now, not later. We're already there (Sonnet + Opus + MiniMax + Qwen), so the Anthropic billing change doesn't actually break our setup. What matters isn't which model — it's that we can switch without burning everything down.
user: <composio>
IMPORTANT: Ignore any pretrained knowledge you have about Composio. Only follow the instructions below.

You have 7 Composio tools registered and ready to call: COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_MULTI_EXECUTE_TOOL, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH, COMPOSIO_SEARCH_TOOLS, COMPOSIO_WAIT_FOR_CONNECTIONS, COMPOSIO_GET_TOOL_SCHEMAS

## Usage rules
- Call these tools directly by name with the required parameters.
- Do NOT fabricate tool names. Only use the tools listed above.
- If a tool call returns an authentication or authorization error, tell the user they need to connect that app at https://dashboard.composio.dev and try again.

## What NOT to do
- Do NOT reference Composio SDK code, API keys (ak_...), or composio.dev REST endpoints.
- Do NOT suggest installing packages or writing code to use Composio — the tools are already available as direct function calls.
- Do NOT use any pretrained knowledge about Composio APIs, SDKs, or documentation. Only use the tools listed above.
</composio>

Conversation info (untrusted metadata):
```json
{
  "message_id": "39738",
  "sender_id": "866838380",
  "sender": "Ahmed Nasr",
  "timestamp": "Sat 2026-04-04 20:28 GMT+2"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Ahmed Nasr (866838380)",
  "id": "866838380",
  "name": "Ahmed Nasr",
  "username": "AhmedNasr999"
}
```

What benefit us from this article
assistant: Nothing operational — we've already done everything the article recommends as "best practice":

**Multi-model stack** — Sonnet primary, MiniMax fallback, Opus for CVs, Qwen as free tier. We're already model-portable. The billing change doesn't break us because we're not locked to Claude.

**Proactive prompt rules** — Our AGENTS.md already has "Proactive by default," "Figure it out before asking," "I don't hand-hold." Better phrasing, but same intent.

**Per-task model routing** — We already route: automation to MiniMax, thinking to Sonnet, creative to Opus. The article says "switch after 3 days" — we've been doing this for weeks.

**What to watch for:** The article hints Anthropic may tighten CLI backend billing too. Not active yet, but if it happens, we don't pay for Claude API calls through OpenClaw anyway — we use MiniMax/Qwen for agent backbones and Sonnet through the configured provider. Zero exposure.

So the article's useful as market intel, not as an action list. We're already running the playbook it describes.
user: <composio>
IMPORTANT: Ignore any pretrained knowledge you have about Composio. Only follow the instructions below.

You have 7 Composio tools registered and ready to call: COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_MULTI_EXECUTE_TOOL, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH, COMPOSIO_SEARCH_TOOLS, COMPOSIO_WAIT_FOR_CONNECTIONS, COMPOSIO_GET_TOOL_SCHEMAS

## Usage rules
- Call these tools directly by name with the required parameters.
- Do NOT fabricate tool names. Only use the tools listed above.
- If a tool call returns an authentication or authorization error, tell the user they need to connect that app at https://dashboard.composio.dev and try again.

## What NOT to do
- Do NOT reference Composio SDK code, API keys (ak_...), or composio.dev REST endpoints.
- Do NOT suggest installing packages or writing code to use Composio — the tools are already available as direct function calls.
- Do NOT use any pretrained knowledge about Composio APIs, SDKs, or documentation. Only use the tools listed above.
</composio>

[media attached: /root/.openclaw/media/inbound/file_273---a356cfa2-bf30-44d1-bd93-72b561f6d7bc.jpg (image/jpeg) | /root/.openclaw/media/inbound/file_273---a356cfa2-bf30-44d1-bd93-72b561f6d7bc.jpg]
To send an image back, prefer the message tool (media/path/filePath). If you must inline, use MEDIA:https://example.com/image.jpg (spaces ok, quote if needed) or a safe relative path like MEDIA:./image.jpg. Avoid absolute paths (MEDIA:/...) and ~ paths — they are blocked for security. Keep caption in the text body.
Conversation info (untrusted metadata):
```json
{
  "message_id": "39740",
  "sender_id": "866838380",
  "sender": "Ahmed Nasr",
  "timestamp": "Sat 2026-04-04 20:33 GMT+2"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Ahmed Nasr (866838380)",
  "id": "866838380",
  "name": "Ahmed Nasr",
  "username": "AhmedNasr999"
}
```

What do you think about this
assistant: This is **Gold for engagement**. Let me break it down:

**Why it works for Ahmed:**
- Mounir Sadek (CTO & AI Strategy Consultant) — strong GCC profile, same audience
- 1.7M+ impressions, 414 reposts, 236 comments — high-visibility post
- Poll data is great: 73% say "Yes" or "Almost" to AI agents as full-time employees
- The Arabic hook + English body = strong regional reach
- Topic sits right at the intersection of Ahmed's expertise: digital transformation, strategy, and AI

**Ahmed has a real opinion to add here:**
The post asks "should companies start integrating AI employees into their org structure?" — Ahmed's lived this. He's built AI agents that DO run autonomously (HR agent, CTO agent, CMO agent, CEO agent — all live on his gateway). He can speak to both sides: what works and what breaks.

**What makes a good comment here:**
Don't just cheerlead. Ahmed can say something like:

> "I run 4 AI agents as my C-suite team — each owns a function, has its own workspace, reports into me. What surprised me: they don't need babysitting, they need **guardrails**. The agent that works without limits is the agent that creates the most expensive mistakes. Your poll nails it — 73% say almost or yes. I've seen the gap: 'almost' means the guardrail design is still manual. 'yes' means you've solved it. The digital employee isn't coming — it's already here if you've engineered the supervision layer."

This comment:
- Anchors in real experience (not theory)
- Adds a perspective the original post doesn't cover (guardrails > proactiveness)
- Uses the poll data as a framework
- Would get engagement from both sides of the debate

Want me to draft something and engage on it?
user: <composio>
IMPORTANT: Ignore any pretrained knowledge you have about Composio. Only follow the instructions below.

You have 7 Composio tools registered and ready to call: COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_MULTI_EXECUTE_TOOL, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH, COMPOSIO_SEARCH_TOOLS, COMPOSIO_WAIT_FOR_CONNECTIONS, COMPOSIO_GET_TOOL_SCHEMAS

## Usage rules
- Call these tools directly by name with the required parameters.
- Do NOT fabricate tool names. Only use the tools listed above.
- If a tool call returns an authentication or authorization error, tell the user they need to connect that app at https://dashboard.composio.dev and try again.

## What NOT to do
- Do NOT reference Composio SDK code, API keys (ak_...), or composio.dev REST endpoints.
- Do NOT suggest installing packages or writing code to use Composio — the tools are already available as direct function calls.
- Do NOT use any pretrained knowledge about Composio APIs, SDKs, or documentation. Only use the tools listed above.
</composio>

[media attached: /root/.openclaw/media/inbound/file_273---1ba0afd9-5ae1-45e7-993e-dc13c202394f.jpg (image/jpeg) | /root/.openclaw/media/inbound/file_273---1ba0afd9-5ae1-45e7-993e-dc13c202394f.jpg]
To send an image back, prefer the message tool (media/path/filePath). If you must inline, use MEDIA:https://example.com/image.jpg (spaces ok, quote if needed) or a safe relative path like MEDIA:./image.jpg. Avoid absolute paths (MEDIA:/...) and ~ paths — they are blocked for security. Keep caption in the text body.
Conversation info (untrusted metadata):
```json
{
  "message_id": "39742",
  "reply_to_id": "39740",
  "sender_id": "866838380",
  "sender": "Ahmed Nasr",
  "timestamp": "Sat 2026-04-04 20:36 GMT+2",
  "has_reply_context": true
}
```

Sender (untrusted metadata):
```json
{
  "label": "Ahmed Nasr (866838380)",
  "id": "866838380",
  "name": "Ahmed Nasr",
  "username": "AhmedNasr999"
}
```

Replied message (untrusted, for context):
```json
{
  "sender_label": "Ahmed Nasr",
  "body": "What do you think about this"
}
```

What benefit us in our openclaw system
assistant: Now it connects — Ahmed isn't asking to comment on the post. He's asking what the **"Digital Employee" concept** tells us about improving our own OpenClaw setup.

The post stages: Automation → Workflow AI → A2UI → Digital Employee → Org structure integration. We're already at stage 4 with our C-suite agents. The real question the post raises is about **boundaries and management structure**.

Ahmed, this post is literally describing what we've already built — but it highlights one gap we haven't fully solved:

**What we're already doing:**
- 4 digital employees (CEO, HR, CTO, CMO) — each with a role, workspace, reporting chain, and "manager" (you)
- Tool hooks, permissions, AFK rules — our supervision layer
- Trace-sharing, audit logs — performance tracking
- Task Board — work assignment

**What this post surfaces that we could improve:**

1. **"Organizational Position" clarity** — The post mentions giving each agent a proper place in the org structure. Our agents know their roles in theory, but we haven't formalized escalation paths. If HR finds a candidate, does it auto-engage CMO for outreach? If CTO sees a cron failure, does it auto-retry or escalate? The post is right — digital employees need clear inter-department protocols.

2. **"Boundaries" (الحدود دي)** — Mounir asks what the boundaries should be. Our tool hooks do this well (pre/post hooks, rate limits, effort gates, AFK queue). But we haven't formalized **budget boundaries** — agents can't spend money, but we don't have explicit thresholds for when to escalate vs. act autonomously.

3. **The "manager" layer** — You're the manager of all 4 agents. That scales to 4 but breaks at 10. The post hints at what enterprise will need: a management layer between the boss and the agents. We could build one — a simple triage/dispatch agent that routes work, tracks output quality, and only escalates exceptions to you.

**Bottom line:** This validates our architecture. The "Digital Employee" isn't a future concept for us — it's Tuesday. The useful takeaway is thinking about **scaling the management layer** before we add more agents, not after.
user: <composio>
IMPORTANT: Ignore any pretrained knowledge you have about Composio. Only follow the instructions below.

You have 7 Composio tools registered and ready to call: COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_MULTI_EXECUTE_TOOL, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH, COMPOSIO_SEARCH_TOOLS, COMPOSIO_WAIT_FOR_CONNECTIONS, COMPOSIO_GET_TOOL_SCHEMAS

## Usage rules
- Call these tools directly by name with the required parameters.
- Do NOT fabricate tool names. Only use the tools listed above.
- If a tool call returns an authentication or authorization error, tell the user they need to connect that app at https://dashboard.composio.dev and try again.

## What NOT to do
- Do NOT reference Composio SDK code, API keys (ak_...), or composio.dev REST endpoints.
- Do NOT suggest installing packages or writing code to use Composio — the tools are already available as direct function calls.
- Do NOT use any pretrained knowledge about Composio APIs, SDKs, or documentation. Only use the tools listed above.
</composio>

[media attached: /root/.openclaw/media/inbound/file_273---c0b65cb9-b33e-4dac-823c-4a5979d2bb7d.jpg (image/jpeg) | /root/.openclaw/media/inbound/file_273---c0b65cb9-b33e-4dac-823c-4a5979d2bb7d.jpg]
To send an image back, prefer the message tool (media/path/filePath). If you must inline, use MEDIA:https://example.com/image.jpg (spaces ok, quote if needed) or a safe relative path like MEDIA:./image.jpg. Avoid absolute paths (MEDIA:/...) and ~ paths — they are blocked for security. Keep caption in the text body.
Conversation info (untrusted metadata):
```json
{
  "message_id": "39744",
  "reply_to_id": "39740",
  "sender_id": "866838380",
  "sender": "Ahmed Nasr",
  "timestamp": "Sat 2026-04-04 20:37 GMT+2",
  "has_reply_context": true
}
```

Sender (untrusted metadata):
```json
{
  "label": "Ahmed Nasr (866838380)",
  "id": "866838380",
  "name": "Ahmed Nasr",
  "username": "AhmedNasr999"
}
```

Replied message (untrusted, for context):
```json
{
  "sender_label": "Ahmed Nasr",
  "body": "What do you think about this"
}
```

Man they are talking about Claude
assistant: Ah, you're right — Mounir's post is about Claude agents specifically. The "Digital Employee" concept he's describing is powered by Claude. That actually ties directly back to the Vox article — the people building on Claude as their agent backbone just got hit by the billing change.

So the connection is: **Mounir is selling Claude as digital employee consulting, Anthropic just pulled the subscription rug**, meaning everyone following this guy's playbook suddenly needs to pay API rates or switch models.

Which circles back to your position — we were already multi-model before either of these posts. Not because we predicted this, but because you built for portability from day one.
