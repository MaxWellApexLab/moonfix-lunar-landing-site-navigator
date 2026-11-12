# Moonfix — Lunar South-Pole Site Navigator

**Independent lunar engineering research toolkit · upgraded November 6, 2026**  
**Working offline interactive site comparator with source-validated data and scientific window audit; not a certified operational mission planner or NASA-sponsored software.**

## Open immediately

Open **`index.html`** in a modern browser. No login, server, API key, CDN, package installation, JavaScript build tool, or NASA web API is needed for the viewer. The actual 10-site dataset and 10 relief tiles are embedded in the HTML. The page remains usable without Internet.

The preview is in `screenshots/01_lunar_navigator_best_visibility.png`; a 25-second original browser demo is in `demo_moonfix_2026.mp4`; the new 16-second window explorer video is in `demo_moonfix_v2_window_explorer.mp4`.

## Why the NASA challenge matches the research

The official [Lunar Landing Site Navigator](https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/) asks for an intuitive way to compare landing sites and dates, visualizing solar illumination and direct-to-Earth communication relative to local horizons. This toolkit specifically supports those two questions using already measured Sun and Earth angles and LOLA terrain-derived skyline values. It does not rank sites by a falsely precise universal landing-safety score.

**The science and UI are independently developed research artifacts.** Their source and build history is preserved by the release manifest. This ZIP is not an official submitted project, and does not assert NASA endorsement.

## Measured content — not simulated scores

- **10 genuine south-pole candidate coordinates**, each having 72 dated hourly samples in JPL TDB time, November 14–16, 2026 (720 input rows).
- Each observation includes Sun and Earth azimuth, apparent elevation and previously computed terrain skyline at that direction.
- Original 80-m NASA LOLA local DEM tiles (27×27 pixels; 2.16 km square at the DEM grid scale), embedded as small visual hillshades. **Not** a boulder-resolution landing-hazard map.
- Site comparisons change when requiring an extra **0°, 0.5°, 1°, 2°, or 3°** of angular skyline margin for **both** Sun and Earth.
- Site-hour clearance plots, clickable polar schematic, actual DEM tile, timestamp slider, date tabs, hourly playback, dynamic Pareto trade-offs, and printable report.
- A *separate, explicitly conditional* linear-between-hour interpolation proxy can estimate the fraction of the **71 between-hour intervals** that satisfy both clearances. This is **not** verified continuous visibility, power/communication link budget, or future prediction.

For example, at 1° terrain-horizon margin, the data show:

| Site | Both clear among 72 hourly samples | Linear interpolation proxy of 71 gaps | Local slope P95 |
| --- | ---: | ---: | ---: |
| South_84E40 | **45/72** | **44.0284 h** | **16.440°** |
| South_83E60 | **17/72** | **16.7186 h** | **8.459°** |

This illustrates a real engineering trade-off: better visibility versus flatter local terrain. The other eight sites provide alternate slope/visibility combinations. Some have 0/72 at +1° margin; this is a condition of this **three-day sample only**, not proof that those sites are forever unsuitable.


## V2: Scientific mission-window explorer (new)

The browser now includes an **interactive modeled-window timeline** and offline **CSV export** for the selected site and angular margin. With 10 locations and 5 margins, the new research solver calculates **100 scenarios (10 × 5 × 2 interpolation models)**, using event-root finding instead of coarse 1-minute approximation. Every positive visibility subinterval must satisfy *both* Sun and Earth skyline clearances. An independent dense-grid numeric check confirms the PCHIP window integrals in all scenarios.

- **PCHIP** uses shape-preserving cubic interpolation between each observed hourly clearance. **Linear** interpolates endpoints. Neither produces new JPL observations or certifies uninterrupted communications/illumination.
- Reports model-specific total hours, longest run, start/end TDB stamps, signed differences and alternate-hour withheld sample P95 interpolation errors.
- **Observation boundary truncation:** windows touching sample 0 or 71 are marked as truncated by the measured time span, **not physical end/start events**.
- Click a window to inspect its midpoint in the original 72-hour hourly chart. Click **Export windows CSV** for a site-and-margin machine-readable report.
- New files: `src/mission_windows.py`, `data/window_audit.json`, `data/window_runs.csv`, `docs/ENGINEERING_AUDIT_V2.md`, `docs/PROJECT_PAGE_READY.md`, new browser screenshots.

### Reproduced 1° margin comparison (2026-Nov-14–16 TDB)

| Site | Sampled joint epochs | Linear proxy | Exact root-solved PCHIP proxy | Window start under PCHIP | End of observed data |
| --- | ---: | ---: | ---: | --- | --- |
| South_84E40 | 45/72 | 44.0284141 h | **44.0283386 h** | Nov 15 02:58:17.981 TDB | Nov 16 23:00 TDB |
| South_83E60 | 17/72 | 16.7186434 h | **16.7182630 h** | Nov 16 06:16:54.253 TDB | Nov 16 23:00 TDB |

**Both model windows run to the right edge of our measured dataset; the true termination time is unobserved.** The slope/visibility trade-off remains: South_83E60 is flatter locally (P95 8.459° versus 16.440°), while South_84E40 has more joint-clear observed samples.

### Run the extended tests

```bash
python -m pip install -r requirements.txt
python src/mission_windows.py            # requires only bundled CSV + scipy/numpy
python -m pytest -q                      # scientific checks + real Chromium UI tests
```

See `docs/ENGINEERING_AUDIT_V2.md` for assumptions and independent numerical cross-checks.

## Reproduce the scientific data preparation

The generated viewer includes `data.json`, the 720-line source CSV plus header (`data/real_72h_JPL_LOLA.csv`), the actual prior LOLA terrain summary JSON, and `sources.json` with the source file SHA-256 digests.

To rebuild the HTML and re-extract the 80-m terrain tiles from the **full original** NASA LOLA `LDEM_80S_80MPP_ADJ.TIF` (not distributed in this ZIP):

```bash
python -m pip install -r requirements.txt
export MOONFIX_DEM=/path/to/LDEM_80S_80MPP_ADJ.TIF
python src/build_moonfix.py
python -m pytest -q tests
```

The builder refuses to invent missing terrain or observations; in the tested environment, regenerating the standalone HTML from the original DEM produced an **identical SHA-256**. Tests verify all 720 source rows, all five margin metrics against the independently saved scientific report, temporal interpolation invariants, source data embedding, and real Chromium interactions (desktop and mobile).

Optional (Chromium and FFmpeg required): `python scripts/build_demo_video.py` reproduces the real interaction demo from the generated app. No third-party audio or music is included.

## Science limitations

1. **Time is JPL TDB, not NYC local time.** Do not treat November 14 00:00 TDB as November 14 00:00 in New York. There are 72 actual hourly samples across November 14–16; none are extrapolated to other lunar days or years.
2. **Site horizon** means the previously computed terrain skyline in the **specific Sun/Earth azimuth** at that hour. The app does not contain a full 360° azimuthal terrain-horizon panorama for each candidate.
3. **Counted hours are sampled epochs.** A result of `45/72` does not certify 45 continuous hours. The alternate linear proxy within 71 hour gaps requires an interpolation assumption and is never described as independent observation.
4. **Terrain P95 slope** is estimated over a 27×27 80-m DEM neighborhood. It does not cover boulder, regolith, dust, touchdown ellipse, radiation, thermal survivability, spacecraft power, navigation, or Earth-station link budget.
5. NASA/LOLA data were combined in the participant's earlier Moonfix research pipeline. The original JPL Horizons geometric states and LOLA DEM should be cited separately. The toy polar position chart is **schematic** and is not an actual registered DEM basemap.

## Project status, sources, license

This package is an independent engineering research and demonstration artifact. No official NASA project submission, jury score or award is claimed.

- [NASA Space Apps 2026 challenge](https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/)
- [NASA Space Apps 2026 participation & deadlines](https://www.spaceappschallenge.org/2026/)
- [Official 2026 Terms and Conditions](https://www.spaceappschallenge.org/legal/)
- [NASA/JPL Horizons](https://ssd.jpl.nasa.gov/horizons/)
- [NASA LRO LOLA / PDS archive](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)

The newly created interactive UI and code are supplied under the MIT license in `LICENSE`; the source NASA/LOLA/JPL data retain their original provenance and applicable rights. The participant must confirm their right to publish existing preparatory code and any third-party materials. See `docs/SOURCE_AND_RIGHTS.md`. AI assistance was used to prepare this study; human review is required before publication or submission.
