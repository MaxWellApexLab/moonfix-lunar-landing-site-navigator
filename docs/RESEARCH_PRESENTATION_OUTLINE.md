# Technical review outline — Moonfix pre-event study

**This is a technical explanation template, not the final NASA Space Apps 2026 hackathon submission.**

## 30-second technical overview

Lunar south-pole landings involve a geometric trade-off: candidate locations differ in terrain roughness, solar illumination and direct-to-Earth visibility. Moonfix makes these trade-offs inspectable using a real NASA LOLA 80-meter DEM and hourly JPL DE441 Sun/Earth geometry for ten selected candidate coordinates. It visualizes each observation at its actual TDB epoch, supports 0°–3° terrain-horizon clearance margins and compares the resulting 72 sampled epochs. The app is a planning-study prototype, not a safe-landing certification.

## Explain the figures and limitations

**Main controls:** Choose one of ten sites, set minimum angular horizon margin, select any observation from Nov 14–16 (TDB). The Sun and Earth cards display terrain-skylined clearance and azimuth. Their dual-line chart shows each hourly sample, not an interpolated astronomical ephemeris.

**Site comparison:** With a 1° margin, South_84E40 has 45 out of 72 joint clear samples and local 80-meter DEM slope P95 16.44°, whereas South_83E60 has 17 out of 72 and slope P95 8.46°. Higher visibility and flatter terrain pull in opposite directions. Pareto labels are computed on exactly these two screening metrics; they do not imply global mission optimality.

**Terrain panel:** A real local NASA LOLA 27×27 pixel height tile is shown as relative-elevation hillshade. It is not a lunar surface photograph and lacks small-hazard information. The second display, an interpolation proxy, estimates within-hour interval durations under an explicitly stated straight-line-between-samples assumption; it does not prove a continuous link or power generation period.

## Evidence to show reviewers

1. Real DEM patch and source SHA-256 checks in `sources.json`.
2. One site switching test that changes the 45/72 and 17/72 metrics.
3. A margin sweep from 0° to 3°, showing changing candidate ranks.
4. Date stepping and the plotted Sun/Earth clearance at one true TDB observation.
5. Statement of what is **not** modeled: thermal power budget, high-cadence ephemerides, boulder hazards, terrain-to-orbit occultation, precision site certification, and spacecraft operations.
6. Browser tests and offline operation without NASA web API access.

## Next research directions after the event (not completed here)

Extend to full lunar synodic and seasonal windows using valid time spans, NASA SPICE Moon body-fixed transformations, true azimuth-dependent horizon raytracing on DEM, lander power subsystem constraints, terrain hazard ellipses and uncertainty-aware communication link analysis. None is claimed as completed in this package.
