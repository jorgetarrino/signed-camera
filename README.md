# Signed Camera

Fake images are becoming harder to tell apart from real ones as generative AI improves. In 2026, AI-generated satellite images of a "destroyed" US radar reached millions of views before they were debunked [1]. Signed Camera is a low-cost, low-power camera for CubeSats that signs each image at the moment of capture with a secure element. The signature also covers the GPS position and the timestamp, so the image can be verified on the ground by anyone with the public key.

Capture-time signing has already been proposed for satellites [2][3], and some professional cameras implement it through the C2PA standard [4][5]. This project combines that approach with two techniques known from other fields and adapts them to a satellite link. The signature remains valid when packets are lost on the radio downlink, which is common on low-power satellite links. Cropped regions of an image also remain verifiable, while any other modification is detected. As a university project, the design prioritises low cost.

**Status:** design phase. Components are selected and the power budget is complete. The next milestone is a first prototype that captures, signs and verifies an image on a PC.

## How it works

1. The camera (OV2640) captures the picture and the ESP32-S3 receives it as a JPEG. The time and GPS position are read at the same moment, and a counter is incremented for every photo.
2. The image is split into blocks and each block is hashed with SHA-256. The hashes are combined into a Merkle tree, whose root acts as a single fingerprint of the whole image. Each block can be checked independently, which allows crops to be verified and limits the effect of lost packets.
3. The ESP32 sends the root, the time, the GPS position and the counter to the secure element (ATECC608B), which signs them with ECDSA P-256. The private key is generated inside the chip and cannot be read out, including by the ESP32 itself.
4. The image is transmitted to the ground in radio packets, together with the signature and the data required to check each block.
5. On the ground, the signature is checked against the chip's public key with an open-source verifier, first as a Python script and later as a web page that runs entirely in the browser.
   - Blocks that arrive are still verifiable when other packets are lost.
   - A cropped image can still be verified.
   - A change to a single pixel makes that block fail verification.
   - The counter prevents an old photo from being presented as a new one.

Steps 2 and 5 describe the planned design. The first prototype signs the whole image and verifies it on a PC.

## Block diagram

![Block diagram](docs/block-diagram.png)

## Components

| Block | Part | Interface | Reason |
|---|---|---|---|
| Microcontroller | ESP32-S3 | – | Camera port (DVP), PSRAM, hardware crypto, Wi-Fi for testing |
| Camera | OV2640 | DVP | 2 MP, hardware JPEG, well documented |
| Secure element | ATECC608B | I2C | ECDSA P-256 in hardware, private key cannot be read out |
| GPS | u-blox MAX-M10S | UART | Position and time for the signature, 1 s hot start, ~12 mA |
| Control radio | SX1262 (868 MHz LoRa) | SPI | Telemetry and commands, −148 dBm sensitivity |
| Image radio | SX1280 (2.4 GHz) | SPI | Image downlink, up to 1.3 Mbps (FLRC) |
| Battery | LiPo 3.7 V, 1000 mAh | – | About 2 days without sun, margin for ageing |
| Regulator | TPS63802 (buck-boost) | – | Full LiPo range down to 3.0 V, 11 µA quiescent current |
| Charger | BQ24074 | – | Power path (system runs from the panel while charging), tolerates a weak panel |
| Solar panel | 6 V, 1 W | – | Matches the power budget |
| Battery gauge | MAX17048 | I2C | State of charge for telemetry, no sense resistor |

### Buck-boost instead of an LDO

An LDO requires the battery to stay above roughly 3.55 V to output a stable 3.3 V, which would leave 15–25 % of the LiPo capacity unused. The TPS63802 holds 3.3 V until the battery reaches 3.0 V, at about 90 % efficiency and 11 µA of quiescent current.

The custom PCB also includes a resettable PTC fuse, a P-MOSFET for reverse-polarity protection, a main switch, a battery NTC, a TVS diode on the panel input and two load switches (TPS22918) that cut power to the camera and the GPS between photos.

## Power budget

The budget assumes a 10-minute cycle: telemetry (10 × 0.5 s), listening for commands (10 × 1 s), GPS fix (5 s), photo and signature (3 s), image downlink (30 s) and sleep for the rest of the cycle.

| | Value |
|---|---|
| Average current (3.3 V) | 14.6 mA |
| Peak current | 148 mA |
| Energy needed per day (with margin) | 1.87 Wh |
| Energy from the panel per day (1 W, 5 h of sun) | 3.20 Wh |
| Daily balance | +2.05 Wh |
| Minimum battery capacity | 506 mAh (1000 mAh selected) |

The panel supplies 3.20 Wh per day against 1.87 Wh of demand, which leaves room for more photos or longer transmissions. The image downlink is the longest active phase, so transmitting only the region of interest, which croppable signatures make possible [9], is also the most effective way to reduce energy use.

## Roadmap

- [x] Component selection
- [x] Power budget
- [ ] Prototype with ESP32-S3, OV2640 and ATECC608B: capture, sign and verify an image on a PC
- [ ] Add GPS position and time to the signature
- [ ] LoRa control link (868 MHz)
- [ ] 2.4 GHz image downlink
- [ ] Schematic and PCB in KiCad

## Related work

AI can generate realistic satellite images of places that do not exist [6], and such images are already used for disinformation [1]. Sandia National Laboratories proposed signing satellite images at capture [2][3], and cameras such as the Leica M11-P sign photos with C2PA [4][5]. Space Fabric places secure elements on satellites to attest which software runs on board, rather than to sign images [7]. The CCSDS SDLS protocol authenticates the radio link [8], although that protection ends once the image is stored on the ground. Croppable signatures have been proposed for photographs [9], and Merkle trees over image tiles have been used to verify crops of ordinary photos [10][11]. Loss-tolerant authentication of data streams is also well established (TESLA, EMSS). No published work was found that combines capture-time signing, packet-loss tolerance and verifiable crops on a low-cost satellite payload. That combination, and in particular how the tree data is distributed across packets so that crops remain verifiable when packets are lost, is the focus of this project.

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
10. P. Della Monica, I. Visconti, A. Vitaletti, M. Zecchini, "Trust Nobody: Privacy-Preserving Proofs for Edited Photos with Your Laptop", IACR ePrint 2024/1074, 2024. [Link](https://eprint.iacr.org/2024/1074)
11. Y.-C. Chen, Y.-P. Chou, Y.-C. Chou, "An Image Authentication Scheme Using Merkle Tree Mechanisms", *Future Internet*, vol. 11, no. 7, 149, 2019. [Link](https://www.mdpi.com/1999-5903/11/7/149)

## Learning resources

The Merkle tree code in this repository was written from scratch. The following material was used to learn how Merkle trees and Merkle proofs work:

- Merkle Tree Algorithms, Smart Contract Programmer (YouTube). [Video](https://www.youtube.com/watch?v=Xj8Pt-bF4yo)
- t4sk, Rust Merkle tree example in *hello-rust*. [Code](https://github.com/t4sk/hello-rust/tree/main/merkle)

## Author

Jorge Tarriño, Industrial Electronics and Automation Engineering student at Universidad Carlos III de Madrid.

*Documentation drafted with the assistance of an AI tool; design decisions and implementation are the author's own.*
