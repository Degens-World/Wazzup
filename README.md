# Wazzup

Claude Code skills for [Degens.World](https://github.com/Degens-World).

## Skills

### `/team` — Multi-Agent Team Builder

Assemble a team of AI agents with user-defined personalities and put them to work on any task.

**Setup** — Define your team members when you invoke `/team`:
```
Alex: blunt realist, cuts through fluff
Maya: optimistic visionary, thinks big
Raj: devil's advocate, pokes holes in everything
```

**Usage**
- Ask the whole team a question → parallel responses, each labeled by name
- `@Alex: what do you think?` → direct a question to one member
- `have Maya respond to what Raj said` → route responses between members
- `team vote on [topic]` → yes/no + reason from each member

**Mid-session commands**
| Command | Action |
|---|---|
| `add [name]: [personality]` | Add a member |
| `remove [name]` | Drop a member |
| `swap [name]'s personality to [description]` | Update a member |
| `have [name] respond to [other name]` | Member-to-member routing |
| `new task: [description]` | Update shared team context |
| `reset team` | Start over |

## Installation

Copy any skill file into your Claude Code skills directory:

```
~/.claude/skills/          # global (available in all projects)
.claude/skills/            # project-local
```

Then invoke with `/team` in any Claude Code session.
