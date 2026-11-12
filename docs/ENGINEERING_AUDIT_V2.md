# Moonfix V2 — Mission-window model sensitivity and audit

## Scope and integrity

This audit analyzes 720 observed hourly Sun/Earth clearance values derived from **real NASA/JPL DE441 geometry and the user-provided NASA LOLA 80-m DEM pipeline**, across 10 lunar south-pole sites from 2026-Nov-14 00:00 TDB to 2026-Nov-16 23:00 TDB. The event times below are *estimates under interpolation assumptions* and are **not observed physical entry/exit events**. Data are never extrapolated outside 71 one-hour intervals.

Clearance in degrees at sample time *t*: `c_s(t) = Sun elevation - Sun skyline`, `c_e(t) = Earth elevation - Earth skyline`. For scenario margin `m`, a joint-clear interval satisfies `c_s(t) > m` **and** `c_e(t) > m`. Margins evaluated: 0, 0.5, 1, 2, and 3 degrees.

## Exact within-model event algorithm

1. Require 72 finite, unique, contiguous one-hour TDB samples for each site.
2. Fit two continuous piecewise interpolants on the *same measured hourly records*:
   - linear interpolation of each clearance over every adjacent sample pair;
   - PCHIP shape-preserving cubic interpolation of the Sun and Earth clearance series.
3. For each of the 71 hourly gaps, use the signs at both endpoints and a **Brent root solver** to locate modeled `clearance = margin` crossings, resolving an interval where clearance is positive. The monotonic-per-piece property of PCHIP is important here.
4. Intersect the Sun and Earth positive intervals, then merge touching runs and report total hours, longest run, estimated TDB boundaries and run count.
5. Mark runs touching `t=0` or `t=71` as `left_boundary_truncated` / `right_boundary_truncated`. A run reaching the dataset end does **not** mean communication or sunlight ends there.
6. Calculate alternate-hour withheld-observation PCHIP interpolation errors from the measured 72-point series. These errors validate *interpolant agreement at withheld observed epochs* only. They are not an uncertainty bound on true subhourly physical geometry or terrain.

Implementation: `src/mission_windows.py`. Source metrics: `data/window_audit.json` (all sites and scenarios), `data/window_runs.csv` (individual runs), also embedded directly in offline `index.html`.

## Scientific results at 1-degree skyline margin

| Candidate | Joint clear sampled epochs | Linear assumed hours | PCHIP assumed hours | Difference PCHIP − Linear | PCHIP starts | PCHIP run boundary |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| South_84E40 | 45/72 | 44.0284141 | 44.0283386 | −0.0000755 h | 2026-Nov-15 02:58:17.981 TDB | 2026-Nov-16 23:00 TDB **dataset end** |
| South_83E60 | 17/72 | 16.7186434 | 16.7182630 | −0.0003804 h | 2026-Nov-16 06:16:54.253 TDB | 2026-Nov-16 23:00 TDB **dataset end** |

At the 1° scenario, the remaining eight evaluated sites have no joint-clear *hourly samples or interpolated modeled intervals* during this particular dataset. This says nothing about future or earlier lunar illumination periods.

## Verification and explicit limitations

- Every one of 10 sites × 5 margins × 2 methods = **100 model/scenario combinations** is checked against the embedded source and CSV. The PCHIP root integral is independently compared against numerical integration at **six-second time spacing** across each full 71-hour interval, with difference below 6 seconds (grid discretization) for each scenario.
- Previous exact linear analysis is independently reproduced from raw clearances. The 72-hour sample counts match original terrain-visibility research reports across margins.
- Chromium browser tests manipulate sites, angular margin, time, run selection and actual Blob/CSV download. The offline app requires no server or API credential.
- **Agreement between PCHIP and linear does not certify true continuous joint visibility**, because both use the same sparse hourly observations and inherited horizon model.
- The *right-censored* runs above may continue beyond the observation window; there are no observations after 2026-Nov-16 23:00 TDB in this dataset.
- LOLA 80-m neighborhood slope and horizon screening do not provide boulder-level landing safety, rover traversability, hazard mapping, power/thermal survivability, or RF communications link budget.
- JPL source times are barycentric dynamical time, **not NYC local time**. Never use these timestamps as wall-clock event schedules.

## Running the release

```bash
python -m pip install -r requirements.txt
python src/mission_windows.py
python -m pytest -q
export MOONFIX_DEM=/absolute/path/to/LDEM_80S_80MPP_ADJ.TIF
python src/build_moonfix.py
python -m pytest -q
```

`index.html` itself is fully self-contained and opens without Python, Internet, NASA sign-in or local source DEM. Building the terrain hillshade afresh requires the original 181 MB LOLA file, intentionally excluded from the distributed ZIP. Artifacts include SHA-256 manifest and clean-extraction verification receipt.
