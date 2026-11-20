# Signed Camera

With the rise of modern AI, it is becoming harder and harder to tell fake images from real ones. In 2026, AI-generated satellite images of a "destroyed" US radar reached millions of views before being debunked [1]. This project aims to develop a low-cost, low-power camera for CubeSats that signs each image at the moment of capture with a secure element, together with its GPS position and timestamp, so that anyone can verify its authenticity on the ground.

The idea is not completely new: capture-time signing has already been proposed for satellites [2][3], and professional cameras already sign photos at capture through the C2PA standard [4][5]. This project adds two features to that approach. First, images keep a valid signature even when packets are lost on the radio downlink, a frequent situation on low-power satellite links. Second, a cropped region of an image remains verifiable, while any other change is detected. Finally, since this is a university project, it is designed to be as low-cost as possible.

> **Status:** design phase. Components selected and power budget done. Next: first working prototype (capture → sign → verify).

## How it works

1. **Capture.** The camera (OV2640) takes the picture and the ESP32-S3 receives it as a JPEG. At that exact moment, the time and GPS position are read, and a counter is incremented with every photo.
2. **Image fingerprint.** The image is split into blocks and the SHA-256 hash of each block is calculated. These hashes are combined into a Merkle tree, whose root is a single fingerprint that represents the whole image. Because each block can be checked on its own, crops can be verified and the image survives lost packets.
3. **Signature.** The ESP32 sends the root of the tree to the secure element (ATECC608B), together with the time, the GPS position and the counter. The chip signs them with ECDSA P-256. The private key is generated inside the chip and never leaves it.
4. **Downlink.** The image is sent to the ground by radio in packets, along with the signature and the data needed to verify each block.
5. **Verification.** The ground station verifies the signature with the chip's public key, using an open-source verifier (first a Python script, later a web tool that runs entirely in the browser):
   - If packets are lost, the blocks that did arrive can still be verified.
   - If someone crops the image, the crop can still be verified.
   - If someone changes a single pixel, verification of that block fails.
   - The counter prevents an old photo from being passed off as a new one.

*Steps 2 and 5 describe the planned design. The first prototype will implement capture, signing of the whole image and verification on a PC.*

## Block diagram

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

**Design decision: buck-boost instead of an LDO.** An LDO regulator needs the battery to stay above about 3.55 V to deliver 3.3 V, which would leave 15–25 % of the LiPo unused. The TPS63802 buck-boost keeps 3.3 V down to 3.0 V, with about 90 % efficiency and only 11 µA of quiescent current.

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

The budget leaves a comfortable margin: the panel provides 3.20 Wh per day against 1.87 Wh of consumption (including margin), so there is room for more photos or longer transmissions. The image downlink is the longest active phase of the cycle, so sending only the regions of interest, which croppable signatures make possible [9], is also the most effective way to save energy.

## Roadmap

- [x] Component selection
- [x] Power budget
- [ ] Prototype: ESP32-S3 + OV2640 + ATECC608B — capture, sign and verify an image on a PC
- [ ] Add GPS position and time to the signed metadata
- [ ] LoRa control link (868 MHz)
- [ ] 2.4 GHz image downlink
- [ ] Schematic and PCB in KiCad

## Related work

Fake satellite imagery is not only a theoretical risk: researchers have shown that AI can generate realistic satellite images of places that do not exist [6], and such images are already used in disinformation [1]. Signing images at capture has been proposed for satellites [2][3] and is already available in professional cameras through C2PA [4][5]. Other work protects data in space at a different level: Space Fabric uses secure elements on board to attest which software runs on a satellite [7], and the CCSDS Space Data Link Security protocol authenticates the frames of the radio link [8], but neither keeps the image itself verifiable once it is stored on the ground. Croppable signatures, which keep a cropped image verifiable, have been proposed for photographs [9], but not for satellite downlinks with packet loss. This project combines these ideas in a low-cost CubeSat camera.

## References

1. AFP via Taipei Times, "Fake AI satellite imagery spurs war disinformation", March 2026. [Link](https://www.taipeitimes.com/News/world/archives/2026/03/10/2003853579)
2. S. Crosby, K. Brenning, "On Trusting Third-party Satellite Data", Small Satellite Conference, Utah State University, 2022. [Link](https://digitalcommons.usu.edu/smallsat/2022/all2022/105)
3. S. M. Crosby, W. Marchetto II, K. D. Brenning (Sandia National Laboratories), "Systems and methods for verification and authentication of remote sensing imagery", US Patent 11,646,896, 2023. [Link](https://patents.justia.com/patent/11646896)
4. Content Authenticity Initiative, "Leica launches world's first camera with Content Credentials", October 2023. [Link](https://contentauthenticity.org/blog/leica-launches-worlds-first-camera-with-content-credentials)
5. IEEE Spectrum, "Is that photo real?", on the Leica M11-P signing photos with a secure chipset. [Link](https://spectrum.ieee.org/leica-camera-content-credentials)
6. B. Zhao et al., "Deep fake geography? When geospatial data encounter Artificial Intelligence", *Cartography and Geographic Information Science*, 2021. [Summary](https://www.washington.edu/news/2021/04/21/a-growing-problem-of-deepfake-geography-how-ai-falsifies-satellite-images/)
7. F. Rezabek, D. Malkhi, A. Yahalom, "Space Fabric: A Satellite-Enhanced Trusted Execution Architecture", arXiv:2603.23745, 2026. [Link](https://arxiv.org/abs/2603.23745)
8. CCSDS 355.0-B, "Space Data Link Security Protocol", Consultative Committee for Space Data Systems. [Link](https://public.ccsds.org)
9. P. Perazzo et al., "JPEGs Just Got Snipped: Croppable Signatures Against Deepfake Images", arXiv:2512.01845, 2025. [Link](https://arxiv.org/abs/2512.01845)

## Author

Jorge Tarriño — Industrial Electronics and Automation Engineering student, Universidad Carlos III de Madrid.
