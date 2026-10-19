# Generate see-also links locally

The source `also_see` array is included in `core.SEMANTIC`. It also participates in the pinned snapshots for the supplied Claude reviews. No source entry is edited. Term pages instead read `data/also_see.json` directly, preserving signal order, with a separate input fingerprint. Entry hashes, definitions, model verdicts and downloaded entry records are unchanged.

Use Python 3.12 and `docs/requirements-also-see.txt` in a local virtual environment. These packages are not required in CI. Download the model assets before running the builder; no dictionary input is sent to the model host:

```sh
hf download BAAI/bge-small-en-v1.5 --revision 5c38ec7c405ec4b44b94cc5a9bb96e735b38267a --local-dir .cache/models/bge-small-en-v1.5 --include README.md config.json config_sentence_transformers.json sentence_bert_config.json modules.json 1_Pooling/config.json tokenizer.json tokenizer_config.json special_tokens_map.json vocab.txt model.safetensors
python scripts/build_also_see.py --generated 2026-10-18
python scripts/also_see.py
```

`data/also_see_model.json` pins the publisher revision, MIT licence evidence, weight hash and every model/tokenizer asset hash. Loading uses a local path with offline flags, telemetry disabled and remote code disabled. No inference API, paid call or generative model is used. The builder checks the retagged published corpus, current risk register, drop decisions and redirects.

The matrix is saved as `.cache/embeddings-{model_hash}-{entry_set_hash}.npy`. Per-text row caches allow additions or definition edits to embed only the missing rows. Unchanged inputs reuse the matrix. A rerun without `--generated` preserves the recorded generation date, so identical inputs and caches produce byte-identical data and reports. CPU inference uses deterministic PyTorch operations; neighbour ranking uses normalized float64 vectors and stable ID ties. To regenerate without caches, keep the same pinned assets and Python numerical-library versions.

The BGE encode loop stops after 30 minutes. If that limit is reached, the specified fallback is `sentence-transformers/all-MiniLM-L6-v2` under Apache 2.0: acquire and verify its assets, replace the model pin and supply its directory with `--model-dir`. Record the actual model and weight hash in the output.

Review `reports/also_see_report.md` before merge. Its 20 entries are sampled uniformly with seed `20261018`, without substituting attractive examples. The initial stop list, 0.60 threshold and same-field embedding rule are unchanged from the requested specification. Published CI validates the frozen graph using only the standard library; it never computes embeddings or downloads weights.
