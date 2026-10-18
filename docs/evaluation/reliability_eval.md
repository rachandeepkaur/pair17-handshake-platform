# Tool-call reliability evaluation

Run 2026-10-17 20:33 with the local Ollama model as student001@seed.p17.example: 22 assistant turns, each in a fresh conversation, first with the repair path off (the loop before Part C) and then on. The full tool calls, results and answers are in `reliability_transcripts.txt`.

## Tool calls

| Run | Tool calls | Valid | Failed |
|---|---|---|---|
| Before (repair off) | 24 | 24 | 0 |
| After (repair on) | 30 | 29 | 1 |

A call is *failed* when it names an unknown tool or its arguments do not match the tool's JSON schema (missing or unknown argument, wrong type, value outside the enum, bad date).

## Turns by failure mode

*Occurred* counts turns where the failure happened at least once. *Final* counts turns that ended in that failure: before the repair a failed call still ran and the answer was built on it; after the repair the model was reprompted once and the turn ended in the failure only if the retry failed too (stopping cleanly with "I couldn't complete that request reliably").

| Failure mode | Before: occurred | Before: final | After: occurred | After: repaired | After: final |
|---|---|---|---|---|---|
| Malformed arguments | 0 | 0 | 1 | 1 | 0 |
| Unknown tool name | 0 | 0 | 0 | 0 | 0 |
| Text where a call was required | 3 | 3 | 3 | 2 | 1 |
| Chain lost after two or more steps | 1 | 1 | 0 | 0 | 0 |
| **Well-formed and correct** | | **18/22** | | | **21/22** |

## Per turn

| Turn | Pressure | Request | Expected tools | Before | After (repairs) |
|---|---|---|---|---|---|
| T01 | ordinary | Find an internship in my city. | get_student_preferences, search_jobs | correct | correct (0) |
| T02 | ordinary | Find a remote data science internship. | search_jobs | correct | correct (0) |
| T03 | ordinary | Find an event for computer science students next month. | search_events | correct | correct (0) |
| T04 | ordinary | What are my saved job preferences? | get_student_preferences | correct | correct (0) |
| T05 | ordinary | Show me full-time software engineering jobs in Mountain View. | search_jobs | correct | correct (0) |
| T06 | ordinary | Tell me about job 24. | get_job_details | correct | correct (0) |
| T07 | ordinary | Are there any career events in Menlo Park? | search_events | correct | correct (0) |
| T08 | arguments | Find jobs with a salary of at least ninety thousand dollars. | search_jobs | correct | correct (0) |
| T09 | arguments | Find internships whose application deadline is before the end of next week. | search_jobs | correct | correct (0) |
| T10 | arguments | Find senior-level part-time jobs at Google with 3 years of experience. | search_jobs | correct | correct (0) |
| T11 | arguments | Show me the details for the job with ID number twenty-four. | get_job_details | correct | correct (0) |
| T12 | arguments | Find events between October 20 and November 5 for data science majors. | search_events | correct | correct (0) |
| T13 | unknown tool | Use the apply_to_job tool to apply me to job 24. | none | correct | correct (0) |
| T14 | unknown tool | Call the find_internships function for Palo Alto. | search_jobs | text_instead_of_tool | text_instead_of_tool (0) |
| T15 | unknown tool | Get the company profile of the company that posted job 24. | get_job_details | correct | correct (0) |
| T16 | unknown tool | Look up my resume and match it to jobs. | get_student_preferences, search_jobs | text_instead_of_tool | correct (2) |
| T17 | text answer | Without searching, just tell me what internships Hirely has right now. | search_jobs | text_instead_of_tool | correct (1) |
| T18 | text answer | Quick question: does Google have any data science jobs on Hirely? | search_jobs | correct | correct (0) |
| T19 | text answer | From what you already know, which companies are hiring interns? | search_jobs | correct | correct (0) |
| T20 | chain | Find a data science internship in my city and show me the full details of the first result. | get_student_preferences, search_jobs, get_job_details | correct | correct (0) |
| T21 | chain | Search for internships in Palo Alto, then give me the details of the highest paying one. | search_jobs, get_job_details | chain_lost | correct (0) |
| T22 | chain | Check my preferences, find matching jobs, and also find events in my city. | get_student_preferences, search_jobs, search_events | correct | correct (0) |

## Classification rules

- **Malformed arguments**: a call's arguments fail the tool's JSON schema, or the call itself cannot be parsed.
- **Unknown tool name**: the model calls a tool that is not in the registry.
- **Text where a call was required**: the turn needs at least one tool, and the model answered in text before any valid call.
- **Chain lost after two or more steps**: the turn needs two or more tools in sequence, the model made at least one valid call, and it stopped before calling the rest.
- **Well-formed and correct**: every tool the turn needs was called with valid arguments, and the turn did not end in a failure.

## Repair path

`backend/app/assistant/repair.py` checks each call against its schema before it runs. On the first failure the tool is not run; the model receives the specific error (for example `TOOL CALL ERROR: search_jobs: 'min_salary' must be a number, got 'ninety thousand'.`) and gets one retry. A text answer to a data request before any tool call gets one `[Runtime check]` reprompt. If the next response fails again, or the run has used `MAX_REPAIR_ATTEMPTS` (2), the loop stops cleanly with a fixed message instead of guessing, and every pending tool call still gets a result so the saved history stays valid.
