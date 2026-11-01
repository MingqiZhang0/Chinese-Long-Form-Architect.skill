#!/usr/bin/env python3
"""Historical integration suite intentionally excluded from public source.

The original extended suite depends on confidential project snapshots and
private-derived regression corpora. It is not reproducible from this checkout.
Use scripts/test_public_release.py and scripts/test_public_fast.py for the
public, independently runnable checks. Fail closed instead of faking passes.
"""
import sys
print("PRIVATE_FIXTURES_UNAVAILABLE: full historical integration tests are not shipped; run test_public_release.py and test_public_fast.py instead.", file=sys.stderr)
sys.exit(2)
