# Moonfix — 90-second on-screen product demonstration outline

**0–15 seconds: problem.** “The lunar south pole is not uniformly sunlit or equally accessible by direct-to-Earth radio. Topography can hide the Sun or Earth from a landing site. We need to inspect that trade-off instead of assigning a false universal safety score.”

**15–32 seconds: live data.** Show the offline landing-site navigator and the ten lunar south-pole coordinates. Click South_84E40. Point to the NASA LOLA relief tile and the terrain P95 slope of 16.44°. Show the true hourly Sun/Earth skyline clearance plot based on JPL DE441 data.

**32–50 seconds: requirements.** Select the 1° skyline safety margin. Point out the joint sampled-epoch count **45/72**. Increase the angular margin to 2°; the observed joint epoch count drops to **24/72**. This sensitivity demonstrates that the angular margin is not a cosmetic setting.

**50–75 seconds: engineering.** Scroll to the new mission-window explorer. Contrast linear and PCHIP modeled windows. Mention **44.0283 h** PCHIP under 1° with estimated start Nov 15 02:58:18 TDB. Click the modeled run to inspect the hourly data around its center. Explain that **the run is truncated by the dataset end**, not proof of actual continuous visibility or physical termination.

**75–90 seconds: trade-off and reproducibility.** Switch to South_83E60: only **17/72** joint observed epochs at 1° but a lower local slope P95 of **8.459°**. Click Export windows CSV. Conclude that the tool exposes real trade-offs and reproducible calculations, not one opaque landing score.

Recording notes: use the real browser UI; do not imply NASA endorsement, flight safety certification or access to a longer observation record. All UI timestamps are in TDB, not local time.
