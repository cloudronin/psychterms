# Candidate definition drafting line

Line: candidate-definitions-v1. Vishnu approved a **$100 hard cap** in this chat on 18 October 2026. The private registration is frozen before dispatch; judging remains deferred.

The first prepared queue contains 10,522 initial retrieval packets, now subject to scope and field checks before paid drafting; the remaining source candidates need suitable packets. Definitions are freshly drafted from these packets and published as **Candidate: drafted from the sources shown, not yet read by the two reviewers.**, with exact source citations. No judge runs or scenes are included. One passing reader who did not draft it makes an entry reviewed; two make it judged, with copy checks clear. Two reader failures drop it with a recorded reason. Status is build-owned and forward only. Released is an additional numbered-release marker. Reader calls need their own registered spend line.

Draft model: gpt-5.4-2026-03-05, retaining the pilot model. Official standard prices checked 18 October 2026: $2.50 per million input tokens and $15.00 per million output tokens. No tools, browsing, batch discount or paid extras.

Pilot drafting receipts total $0.462742 for 200 terms, or $0.00231371 per term. At that rate, 10,522 drafts cost about $24.34 and 21,116 about $48.86. These are projections, not guarantees: longer passages and retries add cost. Authorized shared hard cap: **$100**, including all drafting, one copy redraft and one transport/schema retry.

The runner reserves every call’s maximum bill before dispatch. Outstanding uncertain charges remain reserved. All workers, resumes and retries use the same ledger; changing the cap, model, prompts or queue requires a recorded registration amendment. The old pilot registration, STOP files and ledger stay unchanged.

The private registration binds the queue hash, fixed model, prompts, schema, executor, overlap threshold and exact packet hashes. The model receives no inherited prose. It must decline when a packet does not support the requested definition. Missing support, malformed output, dosing, exact duplicates or a 15-word overlap do not publish; a copy hit gets at most one redraft. These checks do not claim a model judge passed. Risk registration is additive and scenes remain absent.

Source: [Official OpenAI model documentation](https://developers.openai.com/api/docs/models/gpt-5.4). The spending-cap requirement is retained from section 7 of docs/spec.md.

Execution: 32 workers, each reserving its maximum call cost atomically in the same $100 ledger before dispatch. Publication begins with the first validated batch; the remainder resumes from the same frozen queue, cached requests and ledger. The top-left subtitle is “Psychology & Counseling Dictionary”.

An interrupted network call keeps its full reservation; at most one transport retry is allowed across resumes. Terminal packet outcomes are persisted, so insufficient packets are not billed repeatedly. Credential/rate-limit errors or a reservation breach stop dispatch. Every amended registration is retained privately; the same ledger and $100 cap apply throughout.
