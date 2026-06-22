# Mallard Python SDK

Deterministic assignment + privacy-guarded event tracking. **Zero runtime dependencies**
(pure stdlib); local bucketing reproduces the server byte-for-byte (see
`../fixtures/bucketing.json`).

```python
from mallard_sdk import Mallard, ExperimentSpec, VariantSpec

mallard = Mallard(api_key="...", base_url="http://localhost:8000")
mallard.load_specs([
    ExperimentSpec("new_checkout", salt="new_checkout",
                   variants=(VariantSpec("control", 50), VariantSpec("treatment", 50))),
])

variant = mallard.get_variant("new_checkout", unit_id=user_id, attributes={"country": "US"})
if variant.variant_key == "treatment":
    ...

mallard.track(user_id, "purchase", value=42.00, props={"sku_count": 3})
mallard.flush()
```

- `get_variant` logs an exposure; `peek_variant` does not (for triggered analysis).
- `track` batches; `flush` is best-effort and **never throws** into your app.
- Privacy guards reject obvious PII (`email`, `phone`, …) and non-pseudonymous unit ids.

## Develop
```bash
cd sdks/python && uv sync && uv run pytest
```
`tests/test_parity.py` asserts this SDK matches the cross-language fixture — the contract
that keeps client and server assignment identical.
