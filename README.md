# Signed Camera

With the rise of modern AI, it is becoming harder and harder to tell fake images from real ones. In 2026, AI-generated satellite images of a "destroyed" US radar reached millions of views before being debunked [1].

<!-- TODO (Jorge): sentence 2 = what this project is (a CubeSat camera that signs every image at capture with a secure element,
     including time and GPS position). Sentence 3 = what makes it different (still verifiable after packet loss and cropping,
     on low-cost, low-power hardware). -->

> **Status:** design phase. Components selected and power budget done. Next: first working prototype (capture → sign → verify).

## How it works

<!-- TODO (Jorge): explain the idea step by step, in your words. Suggested points:
     1. The camera takes a photo.
     2. The secure element signs a hash of the image together with metadata (time, GPS position).
     3. The private key never leaves the secure element.
     4. The image and its signature are sent to the ground.
     5. The ground station verifies the signature with the public key: if a single pixel changes, verification fails. -->

## Block diagram

<!-- TODO (Jorge): export your diagram from draw.io and save it as docs/block-diagram.png -->
![Block diagram](docs/block-diagram.png)

## Components

| Block | Part | Interface | Why this one |
|---|---|---|---|
| Microcontroller | ESP32-S3 | — | Camera port (DVP), PSRAM, hardware crypto, Wi-Fi for testing |
| Camera | OV2640 | DVP | 2 MP, hardware JPEG, widely documented |
| Secure element | ATECC608B | I2C | ECDSA P-256 signing in hardware; private key cannot be read out |
| GPS | u-blox MAX-M10S | UART | Position and time for the signed metadata; 1 s hot start, ~12 mA |
| Control radio | SX1262 (868 MHz LoRa) | SPI | Telemetry and telecommands; −148 dBm sensitivity |
| Image radio | SX1280 (2.4 GHz) | SPI | Image downlink, up to 1.3 Mbps (FLRC) |
| Battery | LiPo 3.7 V, 1000 mAh | — | ~2 days without sun; margin for ageing |
| Regulator | TPS63802 (buck-boost) | — | Uses the full LiPo range down to 3.0 V; 11 µA quiescent |
| Charger | BQ24074 | — | Power path (system runs from the panel while charging), adapts to a weak panel |
| Solar panel | 6 V, 1 W | — | Matches the power budget |
| Battery gauge | MAX17048 | I2C | State of charge for telemetry, no sense resistor |

<!-- TODO (Jorge): add one or two sentences on a decision you found interesting, e.g. why buck-boost instead of an LDO,
     or why LiPo instead of an 18650 cell. This is what interviewers ask about. -->

Protections on the custom PCB: resettable PTC fuse, reverse-polarity P-MOSFET, main switch, battery NTC, TVS on the panel input, and load switches (TPS22918) to cut camera and GPS power between photos.

## Power budget

Operating scenario per 10-minute cycle: telemetry (10 × 0.5 s), listening for commands (10 × 1 s), GPS fix (5 s), photo + signature (3 s), image downlink (30 s), sleep the rest.

| | Value |
|---|---|
| Average current (3.3 V) | 14.6 mA |
| Peak current | 148 mA |
| Daily energy needed (with margin) | 1.87 Wh |
| Daily energy from the panel (1 W, 5 h sun) | 3.20 Wh |
| Daily balance | **+2.05 Wh** |
| Minimum battery capacity | 506 mAh → 1000 mAh chosen |

<!-- TODO (Jorge): one line on the main lesson, e.g. the development board's sleep current dominates the budget,
     which is why the custom PCB needs a low-quiescent regulator and load switches. -->

## Roadmap

- [x] Component selection
- [x] Power budget
- [ ] Prototype: ESP32-S3 + OV2640 + ATECC608B — capture, sign and verify an image on a PC
- [ ] Add GPS position and time to the signed metadata
- [ ] LoRa control link (868 MHz)
- [ ] 2.4 GHz image downlink
- [ ] Schematic and PCB in KiCad

## Related work

<!-- TODO (Jorge): 3–4 sentences comparing this project with existing work, citing the references below by number, e.g. [1].
     Points: fake satellite images are already used in disinformation [1][2]; camera makers sign photos at capture with a
     secure chip (C2PA) [3][4]; onboard signing with secure elements exists for satellite computing [5] and CCSDS SDLS
     protects the radio link [6], but not the image itself once on the ground; croppable signatures exist for photos [7]
     but not for satellite downlinks with packet loss. -->

## References

1. AFP via Taipei Times, "Fake AI satellite imagery spurs war disinformation", March 2026. https://www.taipeitimes.com/News/world/archives/2026/03/10/2003853579
2. B. Zhao et al., "Deep fake geography? When geospatial data encounter Artificial Intelligence", *Cartography and Geographic Information Science*, 2021. Summary: https://www.washington.edu/news/2021/04/21/a-growing-problem-of-deepfake-geography-how-ai-falsifies-satellite-images/
3. Content Authenticity Initiative, "Leica launches world's first camera with Content Credentials", October 2023. https://contentauthenticity.org/blog/leica-launches-worlds-first-camera-with-content-credentials
4. IEEE Spectrum, "Is that photo real?" (Leica M11-P signing with a secure chipset). https://spectrum.ieee.org/leica-camera-content-credentials
5. F. Rezabek, D. Malkhi, A. Yahalom, "Space Fabric: A Satellite-Enhanced Trusted Execution Architecture", arXiv:2603.23745, 2026. https://arxiv.org/abs/2603.23745
6. CCSDS 355.0-B, Space Data Link Security Protocol. https://public.ccsds.org
7. P. Perazzo et al., "JPEGs Just Got Snipped: Croppable Signatures Against Deepfake Images", arXiv:2512.01845. https://arxiv.org/abs/2512.01845

## Author

Jorge Tarriño — Industrial Electronics and Automation Engineering student, Universidad Carlos III de Madrid.
