# Lab 1 Assistant Architecture

This document describes the assistant architecture for Lab 1 Part B.

## What is shared

```text
Chat page
  -> POST /assistant/chat
  -> agent loop
  -> role-based tool registry
  -> Ollama client
```

The agent loop receives a system prompt, the conversation history, and the
tool schemas. It asks the model for either a response or tool calls, runs each
requested tool, adds string results to the conversation, and repeats until it
has a final response or reaches a fixed iteration limit.

Only one client class may communicate with Ollama:

```text
complete(messages, tools)
```

No frontend component, route, or tool calls Ollama directly.

## Proposed backend layout

```text
backend/app/assistant/
  client.py        Model client interface and Ollama implementation
  agent.py         Bounded hand-built agent loop
  schemas.py       Message, tool, and context types
  prompts.py       System prompts
  registry.py      Chooses a tool registry from the signed-in role
  tools/
    student.py     Working student tools
    company.py     Company-role tool definitions
```

## Student tools for Part B

The student registry will provide the required tools:

- `get_student_preferences`
- `search_jobs`
- `get_job_details`
- `search_events`
- `save_job_or_event`

Each tool will validate its arguments, use the authenticated student context,
return a string in every case, and handle errors instead of raising them.

## Role-specific tool registries

`registry.py` selects tool schemas and handlers from the authenticated role.
The student registry exposes the required Part B tools. A role with no
available tools receives a clear "not available yet" response.

Tool modules follow the same schema and handler structure, so additional
role-specific tools can be added without changing the client or agent loop.
