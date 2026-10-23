# Enigma: brief history and operational use

Enigma was a family of electromechanical cipher machines, not one unchanged device. This project models a particular three-rotor Enigma I configuration. It is a historical learning tool, not an endorsement of the regimes that used it and not safe modern encryption.

## From a commercial invention to military equipment

German engineer **Arthur Scherbius** applied for an Enigma-related patent in 1918. Commercial machines appeared in the early 1920s, intended to protect business communications. Rotor-machine ideas also emerged independently elsewhere; the history of mechanical cryptography is broader than Enigma alone. [1]

The German military adapted the design. Crypto Museum describes the first batch of the Army's Enigma I being delivered in December 1927. The Army and later Luftwaffe used plugboard-equipped versions. Two additional rotors, IV and V, were supplied in December 1938, allowing operators to select three from five rather than merely rearrange three. [1]

German naval machines had their own development and procedures. M3 and the later four-rotor M4 should not be treated as identical to the Army machine. Our simulator does not implement naval VI–VIII rotors, the M4's extra wheel or all reflector variants. [1][2]

## What an operator actually did

An operator did not simply turn the machine on and type arbitrary text. Authorized stations needed compatible equipment and shared instructions. Key sheets could specify rotor selection/order, ring settings and plugboard connections, with keys changed according to the relevant network's schedule. Message procedures governed starting positions and how recipients obtained the information needed for a particular message. These procedures changed by service, network and date. [1][2]

In broad terms:

1. Set up the machine using the applicable instructions and key material.
2. Prepare the message using the prescribed alphabet/formatting conventions.
3. Enter the message one letter at a time and record illuminated letters.
4. Transmit the ciphertext, often by radio, commonly arranged into groups.
5. At the receiving station, reproduce the required settings and starting state, then type the ciphertext to recover the message.

There was no universal “always use AAA” procedure. AAA is just a convenient classroom starting point in this project. A machine's current window letters, its daily setup and an individual message's starting state are different concepts. This app does not implement historical indicator systems or key distribution.

## The Polish breakthrough

In 1932, mathematician **Marian Rejewski** reconstructed crucial aspects of the military Enigma using mathematical analysis, intercepted traffic and intelligence material supplied through French cooperation. The intelligence included material obtained from German source Hans-Thilo Schmidt. **Jerzy Różycki** and **Henryk Zygalski** made major contributions to subsequent methods and tools. [3][4]

The Polish team developed techniques and equipment including the *bomba kryptologiczna* and Zygalski's perforated sheets. In July 1939, Polish specialists shared their achievements with British and French counterparts near Warsaw. This was foundational work, not a minor prelude to a single British inventor solving the machine from scratch. [3][4]

## Bletchley Park and a much larger effort

At Britain's Government Code and Cypher School at Bletchley Park, **Alan Turing**, **Gordon Welchman** and many other cryptanalysts, engineers, operators and intelligence staff developed further methods. The British **Bombe** was a distinct machine that tested implications of guessed plaintext/ciphertext relationships; it was not an Enigma simulator that simply tried every possible full message. Welchman's diagonal board improved the process. British and later American engineering and operational efforts expanded capacity. [3][4]

Important ingredients included:

- **Mathematical structure:** reciprocal wiring and the impossibility of a letter encrypting to itself.
- **Cribs:** plausible fragments of plaintext, sometimes suggested by predictable message formats.
- **Procedural weaknesses and operator mistakes:** repeated or predictable choices could expose relationships.
- **Captured key material and equipment:** sometimes crucial, but not a universal replacement for cryptanalysis.
- **Large-scale interception, processing and interpretation:** breaking a key was only one stage in producing useful intelligence.

The work was uneven. Different networks and changing procedures created periods of success, difficulty and blackout. Not every message was read instantly, and Enigma's defeat cannot accurately be credited to one person or one flaw. [3][4]

## Why study it now?

Enigma makes several enduring ideas visible: permutations, inverse functions, modular arithmetic, stateful algorithms, and the difference between a sound-looking mechanism and a secure communications system. The machine, the procedures around it and the behavior of its users all mattered.

Modern cryptography has different threat models, algorithms and authentication requirements. A historical simulator should never be used to protect passwords, personal messages or other secrets.

## Sources and further reading

These are references for the historical narrative, not copied source text or bundled illustrations:

1. [Crypto Museum: Enigma I](https://www.cryptomuseum.com/crypto/enigma/i/index.htm) — machine development, users, rotor additions and plugboard details.
2. [Crypto Museum: how Enigma works](https://www.cryptomuseum.com/crypto/enigma/working.htm) and [wiring tables](https://www.cryptomuseum.com/crypto/enigma/wiring.htm) — mechanisms and differences between models.
3. [Bletchley Park: Our Story](https://bletchleypark.org.uk/our-story/) — institutional history and links to people, Enigma and the Bombe.
4. [NSA: World War II historical publications](https://www.nsa.gov/History/Cryptologic-History/Historical-Publications/WWII/) — historical research, including accounts of the Polish contribution and Allied cryptanalysis. Individual publications should be read in their historical context.

Reference-access note: Crypto Museum's cited mechanics/wiring pages and Bletchley Park's overview were accessible during development. The NSA publications index returned HTTP 403 to an automated request; it is retained as an institutional further-reading link, not a claim that every linked publication was checked.

Own documentation: [MIT licence](../LICENSE). Linked sources retain their authors' rights. See [third-party notices](../THIRD_PARTY_NOTICES.md).
