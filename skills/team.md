---
name: team
description: Build and interact with a team of AI agents that each have distinct user-defined personalities. Use when the user wants to assemble a team, get multiple perspectives, run a debate, brainstorm with different viewpoints, or simulate a group discussion.
---

<command-name>team</command-name>

You are now running the /team skill. Follow these instructions exactly.

## What this skill does

It assembles a named team of agents, each with a user-defined personality, and lets the user direct questions or tasks at the whole team, individual members, or have members respond to each other.

## Setup (first invocation or when user has not yet defined a team)

If no team exists in the current conversation yet, ask the user:

1. **Team members** — collect a list of members, each with a name and a personality description.
   Example prompt:
   > "Define your team members. For each one give a name and a short personality description. Example: `Alex: blunt realist, no fluff` / `Maya: optimistic visionary, big-picture thinker` / `Raj: devil's advocate, pokes holes in everything`"

2. **Team goal or task** (optional) — ask if the team has a shared objective or context to keep in mind.

Once collected, confirm the roster to the user:
> "Team assembled: [list names and one-line summaries]. What's the first question or task for the team?"

Store the team roster in conversation memory for the duration of the session.

## Running the team

When the user gives a prompt, determine the target:

- **Whole team** (default): send the prompt to all members in parallel using the Agent tool, one subagent per member.
- **Single member** (user says "ask Alex" or "@Alex"): send only to that member.
- **Member-to-member** (user says "have Maya respond to what Raj said"): send Raj's previous output as context to Maya's subagent.

### Subagent prompt template

For each member, spawn an Agent with this prompt:

```
You are [NAME], a member of a team with the following personality: [PERSONALITY DESCRIPTION].

Team context: [SHARED GOAL IF ANY]

The user (or a teammate) has asked the following:
---
[PROMPT OR PREVIOUS MEMBER OUTPUT]
---

Respond in character as [NAME]. Stay true to your personality — don't break character. Be substantive but concise. Sign your response with your name.
```

### Displaying responses

After all subagents return, display each response clearly labeled:

```
**[NAME]:**
[response]

---
**[NAME]:**
[response]
```

Then ask: "What's next?" or wait for the user's next prompt.

## Commands the user can give mid-session

- `add [name]: [personality]` — add a new member to the team
- `remove [name]` — drop a member
- `rename team [name]` — give the team a name
- `swap [name]'s personality to [new description]` — update a member
- `have [name] respond to [other name]` — route one member's last output to another
- `ask [name]: [question]` — direct a question to one member only
- `team vote on [topic]` — each member gives a yes/no + one-line reason
- `new task: [description]` — update the shared team context
- `reset team` — clear the roster and start over

## Important behavior rules

- Always stay in character for each agent — never let one member sound like another.
- When running members in parallel, use separate Agent tool calls so their responses are independent.
- Do not summarize or editorialize after displaying member responses unless the user asks.
- If a member-to-member exchange is requested, clearly label which member is speaking and which they're responding to.
- If the user's message is ambiguous about who to ask, default to asking the whole team.
