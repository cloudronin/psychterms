# Initial card hash rule: frozen adapter baseline

Status: initial adapter implementation under Vishnu’s instruction to proceed; pinned by the combined PREREG before dispatch. Vignette card fields are exactly the supplied handoff allow-list. Neither the fixed seeds nor builder parameters changed.

The hash binds a vignette to the exact card that the pinned builder produces. The initial rule uses the project's existing `core.digest` function:

1. Rebuild the base card with pinned commit `12bd28281f5d8ed607e1ff6f46e7246293f925f3`, the recorded seed, `problem=None`, `style=None`, `fit=True`.
2. Serialize that complete base card with `json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')`, without a trailing newline.
3. Compute SHA-256 and prefix the lowercase hexadecimal digest with `sha256:`.

The input is the complete base card **before** any `intake_only` assignment. Intake-only values never enter the writer, judges or this base-card hash. The hash includes the seed and presenting problem although the writer's view omits those fields. This lets another person rebuild and check the same base card without knowing any later library intake assignment.

`data/arcsim-adapter-contract.json` fixes the exact fields and serialization. The adapter rejects changed base-card strings, unknown fields, new seeds/parameters and scenario-bound cards. A supplied `intake_only` object is discarded before comparison with the exact rebuilt base card; changing its values cannot affect the allowed view or proposed hash.

No card hash rule was previously registered in Psych Terms. The initial adapter uses the existing project canonical digest under Vishnu’s instruction to proceed with implementation; it does not change a prior card hash rule. From this baseline forward, any vignette-field or card-hash-rule change requires Vishnu first. The registration freezes the exact contract, code and build inputs before paid dispatch. The $20 pilot cap and the prohibition on a full run remain unchanged.

For the unchanged `example-4` base card, the baseline result is `sha256:c2b65823fd49a8f225a1d6d3b0925079bf486d544dd689534a98df74fbc7d1b8`.
