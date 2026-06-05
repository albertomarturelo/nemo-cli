---
description: Summarise the current nemo-cli project status by reading docs/CURRENT_STATUS.md and the ADR index. Use when the user asks "where are we", "what is the status", "what is in progress", or for a CFD project status read.
---

Summarise the current state of the project for the user. Read **only**:

- `docs/CURRENT_STATUS.md`
- `docs/decisions/_index.md`

Output the summary in this exact shape:

````
In progress:
  - <item> (<short note>)

Blocked / open questions:
  - <item> (<why it is blocked>)

Recently decided:
  - <ADR id and title>

Next priority:
  - <item>
````

Do not read source code. Do not propose changes. The goal is to give the user a
30-second read of where things stand.
