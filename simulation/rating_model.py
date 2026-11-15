"""Hidden rating model used ONLY by the data generator.

The M1 proposal says ratings are produced by a model that the matching
algorithm does not see, so that the evaluation is not circular. Nothing in
``app/`` (and, later, nothing in the matcher) may import this module. A test
(`tests/test_simulation.py::test_matcher_does_not_import_rating_model`) checks
that rule.

Model (one rating per completed trip, given by the rider about the driver):

    latent = BASE
           + W_SHARED  * min(shared_interests, SHARED_CAP)
           - W_DETOUR  * detour_min
           - W_PEAK    * is_peak
           + driver_effect                    (fixed per driver, N(0, DRIVER_SD))
           + noise                            (N(0, NOISE_SD))
    rating = clip(round(latent), 1, 5)

The coefficients are assumptions, chosen so that shared interests help and a
long detour hurts, as the proposal's statistical question 3 expects. They are
not estimated from real data. Any result in the report must say so.
"""

from __future__ import annotations

import numpy as np

BASE = 3.4
W_SHARED = 0.45
SHARED_CAP = 4
W_DETOUR = 0.06
W_PEAK = 0.25
DRIVER_SD = 0.30
NOISE_SD = 0.60


def latent_score(
    shared_interests: np.ndarray,
    detour_min: np.ndarray,
    is_peak: np.ndarray,
    driver_effect: np.ndarray,
    noise: np.ndarray,
) -> np.ndarray:
    """Return the continuous (unrounded) trip-compatibility score."""
    return (
        BASE
        + W_SHARED * np.minimum(shared_interests, SHARED_CAP)
        - W_DETOUR * detour_min
        - W_PEAK * is_peak
        + driver_effect
        + noise
    )


def to_rating(latent: np.ndarray) -> np.ndarray:
    """Round the latent score to an integer rating between 1 and 5."""
    return np.clip(np.rint(latent), 1, 5).astype(int)
