# Gentle AI defect report — draft (not published)

Status: **draft, unpublished**. Nothing has been sent, commented, or filed.
Classified as a Gentle AI provider defect: both failures arrived as native
typed envelopes from `gentle-ai`, not from the client runtime or the code under
review.

Privacy: this text is already scrubbed. No project name, user, host, absolute
path, diff, source content, or environment value appears below. Opaque ids are
placeholders.

---

## Environment

- `gentle-ai` 4.6.0 (CLI), contract `gentle-ai.review-integration/v2`
- Client: Pi agent host with the compact `gentle_review*` facade (host relay
  transport, `pi_host_relay`)
- OS/arch: Linux x86_64
- Scope: private repository, `base-diff` candidate (`committed-only`), 16 changed
  paths, ~1.5k changed lines
- Lenses requested: 3 (`risk`, `resilience`, `reliability`)

## Expected

After `review capture-result`/group admission, `review status` re-offers the
remaining collect slots (or the closure/acknowledgement transition) so the
transaction can finish. A reviewer result that fails admission is reported so
the same slot can be regenerated.

## Actual

Two distinct failures in one lifecycle:

### A. Reviewer result refused at admission (transport failure)

Operation: host-relayed reviewer group capture (3 reviewer model runs).

```
status:  blocked
outcome: pi-host-relay-transport-failure
reason:  Error: decode reviewer result: json: unknown field "evidence"
         [invalid_request]
stderr:  same, plus the preserved payload path
mutation_performed: true
mutation_outcome:   partial
prepared_reviewers: 3   submitted_reviewers: 1
```

The reviewer model returned a result object carrying an extra `evidence` field;
the admission decoder rejects unknown fields, so the group stops at slot 1 of 3.
The rejected payload was preserved under the lineage's `rejected-results`
directory, which is the right behaviour — but the group is all-or-nothing, so
two reviewers' work produced no verdict.

### B. STATUS loses the route for a live lineage (selector mismatch)

Immediately after A, for the same lineage and the same unchanged candidate:

```
status:   blocked
outcome:  capture-route-registration-rejected
reason:   selector-mismatch
blocker:  category authority-unavailable, actor unknown,
          automatic_retry false,
          next_step "use only the supported native continuation"
```

No continuation is named, and none of the documented stop reason codes covers
`capture-route-registration-rejected`. The authority is neither consumed nor
reachable: no approved verdict, no correction, no invalidation route.

`review inspect` for the same target still reports `status: ready`,
`action: start`, `reason_code: fresh_target_ready`, and the offered START
replays (`action: "replayed"`) — its returned status binding carries a
`--base-ref` that is a tree id rather than the candidate base commit. Executing
exactly that returned STATUS (lineage only) reproduces B unchanged.

### C. Client-facade schema observation (not a Go failure)

Starting a second time on an existing lineage without `requestContextPath`
fails with `atomic_start_conflict` on immutable field `request_context_hash`
(`retry_safe: true`, `next_action: correct_request`). Passing
`requestContextPath` inside `input` resolves it; the facade's `start` rejects it
as a top-level argument. Diagnosable, but the pair of surfaces is asymmetric.

## Minimal reproduction

1. `review inspect` on a `base-diff` + `committed-only` candidate → `action: start`
2. `review start` with 3 lenses and a request-context path → lineage `reviewing`
3. relay the reviewer group → one reviewer payload refused:
   `decode reviewer result: json: unknown field "evidence"`, `outcome: partial`
4. `review status --lineage=<id>` → `capture-route-registration-rejected` /
   `selector-mismatch` / `automatic_retry: false`
5. `review inspect` again → still offers `start`; the replay returns
   `action: "replayed"`, and the STATUS it binds (lineage only) repeats step 4

## Preserved state

- Rejected reviewer payload kept by Go under
  `.git/gentle-ai/rejected-results/<lineage>/<lens>-<slot>.json`
- Authority unconsumed: no acknowledgement executed, no approval burned
- Working tree and candidate untouched by the review

## Impact

The review gate cannot close for this candidate, so delivery stays blocked in
receipt-driven development with no available native continuation. Rerunning the
whole review costs three fresh reviewer model runs and lands on the same
admission decoder, so a retry is not a workaround.

## Not claimed

No root cause is asserted here. Both observed signatures — an unknown `evidence`
field in a reviewer result, and a `selector-mismatch` between the offered START
binding and the accepted STATUS selector — are reported as observed evidence
only.
