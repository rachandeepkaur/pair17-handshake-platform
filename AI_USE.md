# AI Use

## 1. What we used an AI assistant for and what we did ourselves
We used an AI assistant to help implement the front-end design, making sure we are meeting the requirements. We also used it to help verify and debug the backend code.
Since creating the AI chat application was new to us, we also used the tool as a learning resource to help understand the pipeline and the tool calls. Finally, we also used it to help polish sentences and grammar in our reports for correctness and readability.
The main understanding, pipeline design, and evaluation were done by us.

## 2. One AI-produced output that was wrong/unsuitable, or one thing we independently verified
We independently verified the AI assistant workflows and the Part C safety improvements. For Part B, we reviewed five assistant transcripts covering job searches, event searches, follow-up refinements, and a 'no-results' request. We also tested the available Part A backend endpoints for the main resources to confirm that supported create, read, update, and delete operations worked correctly.
For Part C, we tested the save-confirmation flow, prompt-injection resistance, and tool-call reliability.

## 3. How we detected the problem or verified the result
For Part A, we tested the available backend endpoints using authenticated student and company accounts. We verified that supported operations were limited to the resources allowed by each role and that invalid or unauthorized requests returned appropriate errors.
For Part B, we reviewed the transcripts to verify that the assistant called the appropriate tools before answering, used student preferences when needed, handled a follow-up search, and correctly reported when no matching job existed.


## 4. What we changed and why it works now
For Part B, we implemented a bounded agent loop with role-based tools for retrieving student preferences, searching jobs, viewing job details, searching events, and saving jobs or events. A repair layer validates model-requested tool calls against each tool's JSON schema before they run, and tools use the signed-in student context to return either useful data or a clear error message.
For Part C, we added a confirmation gate before saving, schema validation with retries for malformed tool calls, and defenses against prompt injection in retrieved database content. Listing descriptions are treated as untrusted data, text resembling instructions is filtered out, and the system prompt explicitly tells the model not to follow instructions found in job or event listings.
These changes make the assistant more reliable, prevent unauthorized saves, and reduce the risk of malicious listing text being treated as instructions. The backend CRUD tests also confirmed that the core Part A operations work correctly and enforce the appropriate authorization rules.
