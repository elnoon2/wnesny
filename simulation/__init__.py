"""Synthetic data layer for Wnesny (M2).

The M1 proposal states that all data is simulated (no real people). This
package generates, validates and loads that data:

* :mod:`simulation.areas`         ~50 coarse Cairo areas (approximate coordinates)
* :mod:`simulation.generate`      seeded generator that writes CSV files to ``data/raw/``
* :mod:`simulation.rating_model`  the hidden rating model (must never be used by the matcher)
* :mod:`simulation.validate`      integrity checks for the generated CSV files
* :mod:`simulation.load`          loads the CSV files into the Flask database

Run ``python -m simulation.generate --help`` for usage.
"""
