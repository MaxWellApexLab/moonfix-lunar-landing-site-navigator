# Moonfix — project page text (engineering draft, not a claim of submission)

**Title:** Moonfix: Lunar South-Pole Landing Site Navigator

**One-line description:** An offline interactive scientific screening tool that compares lunar south-pole landing candidates using NASA LOLA terrain and JPL solar/Earth geometry.

**Problem:** At the lunar south pole, the surrounding terrain and low solar elevations create competing constraints. Landing-site screening must consider local slope, available sunlight, and whether a direct-to-Earth line of sight clears terrain, and must communicate uncertainties without presenting a single misleading risk score.

**Solution:** Moonfix connects actual NASA/JPL DE441 Sun/Earth ephemeris-based clearance observations with NASA LRO LOLA 80-m terrain neighborhoods. A user can explore 10 site candidates, select from five terrain-horizon clearance margins, scrub 72 real hourly TDB samples, inspect Sun/Earth skyline clearance curves, view real extracted lunar relief tiles, compare Pareto trade-offs and export model-derived visibility-window estimates.

**Engineering differentiation:** The V2 window solver intersects the positive Sun and Earth clearance ranges using two independent within-hour interpolation assumptions: a linear model and a shape-preserving PCHIP cubic, with root-finding at each threshold crossing. It reports both methods, interval sensitivity, the longest modeled window, held-out hourly interpolation diagnostics and explicitly flags when an interval is truncated by the limits of the source observations. The source CSV, JSON audit and reproducible tests ship with the standalone browser application.

**Verified demonstration results (1° horizon margin, Nov 14–16 2026 TDB):** At site South_84E40, 45/72 observed hours show both Sun/Earth above the measured local skyline +1°; the PCHIP within-hour estimate is 44.0283 h. At South_83E60, the corresponding metrics are 17/72 and 16.7183 h, but the local LOLA 80-m P95 terrain slope is lower (8.459° versus 16.440°). Both modeled intervals meet the end of the measured 71-hour gap span and cannot be assumed to end at that time.

**NASA data used:** JPL Horizons DE441 Sun/Moon/Earth vector state data (Nov 14–16 2026, hourly TDB); NASA LRO LOLA 80-m south-polar lunar digital elevation map; derived line-of-sight, relief and slope products. See in-package provenance hash list and hyperlinks to NASA/JPL and PDS.

**Technical stack:** Python, NumPy, SciPy (PCHIP + Brent threshold roots), Rasterio, PyProj, Pillow, HTML5, vanilla JavaScript, SVG, JSON/CSV, Pytest and headless Chromium.

**Scope:** Research-level site screening and transparency, not certified flight/landing safety, long-term power availability, thermal viability, rock hazard classification, or actual communications link budgets.

**Ready-made attachments:** `index.html` (self-contained demo); `demo_moonfix_2026.mp4` (original 25s demo); `demo_moonfix_v2_window_explorer.mp4` (new 16s window explorer); `screenshots/07_window_explorer_v2.png`; `data/window_audit.json`; `data/window_runs.csv`; `docs/ENGINEERING_AUDIT_V2.md`; full source and regression tests.

**Team / creator:** Kuan Ta Wu (solo), Max Well Apex LLC
**Project URL / code repository / final submission:** Live demo: https://maxwellapexlab.github.io/moonfix-lunar-landing-site-navigator/ · Source code: https://github.com/MaxWellApexLab/moonfix-lunar-landing-site-navigator · Final submission: NASA Space Apps project page (submit in the Nov 14-15 window)
