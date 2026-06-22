"""SRM detection + multiple-comparison correction (cross-checked vs statsmodels)."""

from __future__ import annotations

import numpy as np
from app.stats.diagnostics import benjamini_hochberg, bonferroni, holm, srm_check
from statsmodels.stats.multitest import multipletests

PVALS = [0.001, 0.008, 0.039, 0.041, 0.2]


def test_srm_flags_mismatch() -> None:
    res = srm_check({"control": 600, "treatment": 400}, {"control": 0.5, "treatment": 0.5})
    assert res.is_mismatch
    assert res.p_value < 0.001


def test_srm_passes_balanced() -> None:
    res = srm_check({"control": 5050, "treatment": 4950}, {"control": 0.5, "treatment": 0.5})
    assert not res.is_mismatch
    assert res.p_value > 0.001


def test_bonferroni_matches_statsmodels() -> None:
    mine = [adj for _, adj in bonferroni(PVALS)]
    reject, p_adj, _, _ = multipletests(PVALS, alpha=0.05, method="bonferroni")
    assert np.allclose(mine, p_adj, atol=1e-9)
    assert [r for r, _ in bonferroni(PVALS)] == list(reject)


def test_holm_matches_statsmodels() -> None:
    mine = [adj for _, adj in holm(PVALS)]
    reject, p_adj, _, _ = multipletests(PVALS, alpha=0.05, method="holm")
    assert np.allclose(mine, p_adj, atol=1e-9)
    assert [r for r, _ in holm(PVALS)] == list(reject)


def test_benjamini_hochberg_matches_statsmodels() -> None:
    mine = [adj for _, adj in benjamini_hochberg(PVALS)]
    reject, p_adj, _, _ = multipletests(PVALS, alpha=0.05, method="fdr_bh")
    assert np.allclose(mine, p_adj, atol=1e-9)
    assert [r for r, _ in benjamini_hochberg(PVALS)] == list(reject)
