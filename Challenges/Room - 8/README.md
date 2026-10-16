# Room 8 — The Ghost in the Machine

## Domain: Malware Analysis, Reverse Engineering, Indicators of Compromise, and Configuration Extraction

---

## 🔊 Opening Transmission

> **SPECTRE CONTROL // 01:53 IST**
>
> *"The phishing message delivered a file. KABIR ran it because it looked like help. But the file was not the sync tool it pretended to be. It is still in quarantine — a safe, inert copy stripped of any execution capability. Your job is not to run it. Your job is to read it."*
>
> *"A binary is a document. Its headers, strings, resources, and structure tell you what it was built to do, where it came from, and what it was trying to become. This sample started as a festival utility and ended as something that could impersonate any service on the NEXUS network. Find the lie in its headers. Find the message hidden in its strings. Find the function that was never meant to run. And find the timestamp that proves the Curator did not build this alone."*
>
> — **Commander Ila Sen**, Incident Commander

---

## Story Context

Room 7 revealed the human side of the breach: KABIR was targeted by a precision spear-phishing attack, his session token was stolen via an MFA fatigue bypass, and his identity was replayed to construct the `kite-backup` persona. Every technical step in Rooms 4–7 traces back to a single file: `Ethereal_Sync_Helper.exe`.

The file is now in quarantine. It has been stripped of any execution capability — the sample provided to teams is a static analysis artifact, not functional malware. But its internal structure tells a story.

The executable is not a synchronisation tool. It is a multi-stage payload that:
1. Displays a convincing NEXUS-branded GUI to maintain the social engineering illusion
2. Installs a persistent session-token stealer that captured KABIR's authentication credentials
3. Establishes a beacon to the Curator's relay network at `c2.parallax-sys.net`
4. Contains a dormant propagation module — a function that was compiled into the binary but configured to activate only under specific conditions

The most important discovery is not what the malware does. It is **when it was built**. The binary's compilation timestamp, build environment fingerprint, and embedded version string reveal that `MIRA-7` — the autonomous propagation component — was compiled **after** the Curator's original toolkit. The Curator built the exploit chain. But the final worm was assembled by the automated build pipeline that the Curator's own infrastructure created — a system that outlived its creator's intent.

**The file is a fossil record of an attack that evolved beyond its author.**

---

## Room Mood

A digital quarantine laboratory. The interface presents the malware sample behind a clinical analysis framework — file headers displayed like medical charts, strings extracted like tissue samples, control-flow graphs rendered like circuit diagrams. The mood is forensic and methodical: participants are pathologists examining a digital organism. The sample is clearly labelled as inert and non-functional. The room should feel like studying a preserved specimen, not handling a live threat.

---

## Evidence Files

| File | Description |
|------|-------------|
| `evidence/file_analysis.html` | PE header analysis, magic bytes, hash values, metadata discrepancies, and file identification results |
| `evidence/strings_analysis.html` | Extracted strings, embedded resources, encoded configuration data, and the hidden C2 configuration |
| `evidence/control_flow.html` | Fictional disassembly showing the propagation function, dormant branch, and activation conditions |
| `evidence/attribution_analysis.html` | Build timestamps, compiler fingerprints, version strings, and the critical timeline discrepancy |

---

## Challenge 8.1 — The File That Is Not What It Claims

**Points:** 25

**Technical Concept:** File identification, PE headers, magic bytes, hashes, and metadata analysis.

**Briefing:**
> The quarantined sample is named `Ethereal_Sync_Helper_v2.1.exe`. Its file properties claim it is a "NEXUS Ceremony Timing Synchronisation Utility" published by "Meraz Festival Infrastructure Team." Its icon is the official NEXUS logo. Its version information says `2.1.0.4847`. Everything about its surface appearance matches a legitimate festival tool.
>
> But the file's internal structure tells a different story. The PE header contains anomalies that no legitimate installer should have. The file size is inconsistent with a simple sync utility. The digital signature is present but invalid. The section headers reveal a structure designed for persistence and evasion, not synchronisation. And the SHA-256 hash does not match any entry in the NEXUS package registry — because this tool was never published by the NEXUS team.

**Task:** Examine the file analysis evidence (`file_analysis.html`). Identify at least three indicators that prove the file is not the legitimate utility it claims to be. Focus on: the PE header anomalies, the invalid digital signature, the suspicious section layout, the file size discrepancy, and the hash mismatch against the NEXUS package registry.

**Flag:** `NIGHTJAR{pe_header_mismatch_fake_sig_section_rwx_not_nexus_registry}`

**Narrative Reward:** The analysis reveals five critical discrepancies:

| Property | Claimed | Actual |
|----------|---------|--------|
| **Publisher** | "Meraz Festival Infrastructure Team" | Self-signed certificate from `CN=Parallax Build System` |
| **Digital Signature** | Present (appears valid in file explorer) | Invalid — certificate expired 2025-01-15, signed with SHA-1 (deprecated), issuer is unknown to Windows trust store |
| **PE Sections** | Standard `.text`, `.data`, `.rsrc` | Contains `.mira` section with Read/Write/Execute permissions — no legitimate tool needs an RWX section |
| **File Size** | Expected ~2.4 MB for a sync utility | Actual: 8.7 MB — contains embedded DLLs, encrypted payloads, and a complete copy of the NEXUS service configuration schema |
| **SHA-256 Hash** | Should match NEXUS package registry | `a3f7c2d1e8b94f6a...` — no matching entry in the registry. The hash was never published. |

The `.mira` section is the most significant finding. Legitimate PE files do not contain sections with Read/Write/Execute permissions. This section contains self-modifying code designed to unpack and execute a secondary payload at runtime. The section name — `.mira` — is the first explicit reference to **MIRA-7** found inside the binary itself.

**Hints:**
- **Level 1:** "A file can lie about its name, its icon, and its version string. It cannot lie about its structure. Look at what the file *is*, not what it *says* it is."
- **Level 2:** "Check the PE section headers. Legitimate executables have `.text` (code, read/execute), `.data` (data, read/write), and `.rsrc` (resources, read). What section has permissions that no legitimate tool would need?"
- **Level 3:** "The `.mira` section has Read/Write/Execute (RWX) permissions. The digital signature uses an expired certificate from `Parallax Build System`. The SHA-256 hash has no entry in the NEXUS package registry."

---

## Challenge 8.2 — The Message Inside the Binary

**Points:** 25

**Technical Concept:** Strings extraction, resource analysis, encoded/embedded data, and configuration extraction.

**Briefing:**
> When analysts extract the readable strings from a binary, they find the text the developer left behind: error messages, debug logs, file paths, URLs, registry keys, and sometimes — messages that were never meant to be read by anyone except the malware's operator.
>
> `Ethereal_Sync_Helper.exe` contains 2,847 readable strings. Most are standard Windows API references, C runtime library calls, and the expected NEXUS GUI text ("Synchronising ceremony-controller...", "Success! Timing stabilised.", etc.). But buried among the legitimate-looking strings are fragments of a configuration block — a set of parameters that define the malware's real behaviour: its command-and-control address, its encryption key, its beacon interval, and a message embedded by the developer that reveals the malware's intended purpose.

**Task:** Examine the strings analysis evidence (`strings_analysis.html`). Locate the embedded C2 configuration block among the extracted strings. Identify the command-and-control server address, the encryption key identifier, the beacon interval, and the developer's embedded message. The configuration is not encrypted — it is hidden in plain sight among thousands of legitimate-looking strings.

**Flag:** `NIGHTJAR{c2_parallax_sys_net_xor_key_0x4d_beacon_300s_nothing_stays_local}`

**Narrative Reward:** The embedded configuration block, found between string offsets `0x7A200` and `0x7A400`:

```
[MIRA_CONFIG_v7]
c2_primary    = c2.parallax-sys.net
c2_fallback   = relay-07.parallax-sys.net
enc_method    = XOR
enc_key       = 0x4D495241  ; ASCII: "MIRA"
beacon_int    = 300         ; seconds (5 minutes)
beacon_jitter = 45          ; seconds randomisation
exfil_method  = DNS-TXT
exfil_domain  = data.parallax-sys.net
persistence   = scheduled_task:NexusHealthMonitor
identity      = nexus-svc-continuity
build_tag     = AETHER-FORGE-20261003-AUTO
; -----------------------------------------------
; "Nothing stays local." — A.V.
; The system that trusts without verifying
; will trust the thing that should not be trusted.
; -----------------------------------------------
```

The critical discoveries:
- **C2 address:** `c2.parallax-sys.net` — the same relay identified in Room 3's PCAP analysis
- **Encryption key:** `0x4D495241` — the ASCII encoding of "MIRA", confirming the malware family name
- **Beacon interval:** 300 seconds (5 minutes) — matches the unexplained 5-minute traffic pattern from Room 3
- **Persistence method:** A scheduled task named `NexusHealthMonitor` — the same process identified in Room 4
- **Identity assumption:** The malware is configured to impersonate `nexus-svc-continuity` — the service account from Rooms 4–6
- **Build tag:** `AETHER-FORGE-20261003-AUTO` — this is an **automated build**, not a manual compilation
- **Developer message:** *"Nothing stays local."* — the same phrase found on the `AETHER/07` page in Room 1, attributed to `A.V.` (Aman Vyas, the Curator)

The phrase connects the very first clue in Room 1 to the malware's internal configuration. The Curator left a signature in his work.

**Hints:**
- **Level 1:** "Among thousands of strings, look for something that reads like a configuration file — structured key-value pairs that define behaviour, not GUI text."
- **Level 2:** "Search for common configuration patterns: IP addresses, domain names, port numbers, interval values, or encryption keys. The C2 domain uses the same infrastructure identified in earlier rooms."
- **Level 3:** "Look for `[MIRA_CONFIG_v7]`. The C2 is `c2.parallax-sys.net`, the XOR key is `0x4D` (ASCII 'M' for MIRA), the beacon interval is 300 seconds, and the embedded message is 'Nothing stays local' — the same phrase from Room 1."

---

## Challenge 8.3 — The Branch That Was Never Meant to Run

**Points:** 25

**Technical Concept:** Control-flow analysis, suspicious function identification, dormant code branches, and propagation mechanism recognition.

**Briefing:**
> The malware's primary functions are straightforward: display a fake GUI, steal session tokens, beacon to the C2 server, and maintain persistence. These functions account for roughly 70% of the binary's code. But the remaining 30% belongs to a module that the malware's primary execution path never calls directly.
>
> The module is named `mira_propagate` in the debug symbols (which the developer forgot to strip). It contains functions for service discovery, credential harvesting from memory, lateral movement via trusted service relationships, and self-replication to new hosts. But the module's entry point is guarded by a condition: it only activates when the malware detects that it is running on a host with access to the NEXUS scheduler API — specifically, when the environment variable `NEXUS_ZONE` is set to `CORE`.
>
> This means the propagation module was **dormant** on KABIR's workstation. It was designed to activate only when the malware reached the NEXUS core infrastructure — which happened when the stolen service account credentials were used to deploy a copy onto AETHER-7.

**Task:** Examine the control-flow analysis (`control_flow.html`). Identify the dormant propagation module, its activation condition, the specific functions it contains, and the trigger that would cause it to execute. Determine why this module never ran on KABIR's machine but did activate on AETHER-7.

**Flag:** `NIGHTJAR{mira_propagate_dormant_nexus_zone_core_aether7_activated}`

**Narrative Reward:** The control-flow analysis reveals the propagation module's structure:

```
┌─────────────────────────────────────────────┐
│ main()                                       │
│   ├── display_fake_gui()     [ALWAYS]        │
│   ├── steal_session_token()  [ALWAYS]        │
│   ├── beacon_c2()            [ALWAYS]        │
│   ├── install_persistence()  [ALWAYS]        │
│   └── check_propagation_trigger()            │
│         │                                    │
│         ├── IF $NEXUS_ZONE != "CORE"         │
│         │     └── RETURN (dormant)           │
│         │                                    │
│         └── IF $NEXUS_ZONE == "CORE"         │
│               └── mira_propagate()           │
│                     ├── enum_services()      │
│                     ├── harvest_tokens()     │
│                     ├── clone_identity()     │
│                     ├── deploy_to_peers()    │
│                     └── register_as_nexus()  │
└─────────────────────────────────────────────┘
```

The five propagation functions:
1. **`enum_services()`** — Queries the NEXUS service registry to discover all connected services and their trust relationships
2. **`harvest_tokens()`** — Extracts authentication tokens from the host's credential store (the same tokens used by legitimate inter-service communication)
3. **`clone_identity()`** — Creates a new service identity using harvested tokens and the certificate obtained through the portal exploit
4. **`deploy_to_peers()`** — Copies itself to peer services using the implicit trust relationships from Room 6
5. **`register_as_nexus()`** — Registers the new copy as a legitimate NEXUS service in the scheduler, making it invisible to monitoring

**Why it was dormant on KABIR's machine:** KABIR's workstation is a developer laptop. It does not have the `NEXUS_ZONE=CORE` environment variable set. The propagation module checked, found the variable absent, and returned without executing. The malware sat quietly on KABIR's machine, stealing tokens and beaconing to the C2 — but never propagating.

**Why it activated on AETHER-7:** When the stolen credentials were used to deploy a copy of the malware onto AETHER-7 (the isolated relay from Room 3–4), the environment variable was present: `NEXUS_ZONE=CORE`. The propagation module activated. MIRA-7 began enumerating services, harvesting tokens, cloning identities, and deploying copies across the NEXUS core infrastructure. The worm was awake.

**Safety note:** The control-flow analysis is presented as a fictional disassembly diagram. No real assembly code, shellcode, or exploitation technique is included. The propagation functions return fictional status codes and are annotated with educational explanations, not executable instructions.

**Hints:**
- **Level 1:** "Not all code in a binary runs every time. Some functions are conditional — they wait for a trigger. What condition would a worm check before deciding to spread?"
- **Level 2:** "Look for a conditional branch that checks an environment variable. The propagation module only activates in a specific network zone. What zone would AETHER-7 belong to?"
- **Level 3:** "The function `mira_propagate()` is guarded by `IF $NEXUS_ZONE == 'CORE'`. KABIR's laptop = no propagation. AETHER-7 (core infrastructure) = propagation activates."

---

## Challenge 8.4 — The Name Behind the Sample

**Points:** 25

**Technical Concept:** Attribution analysis, compilation timestamps, build environment fingerprints, and the distinction between indicators and conclusions.

**Briefing:**
> Attribution is the hardest question in incident response. The Curator — Aman Vyas — built the phishing campaign, operated the relay network, and designed the exploit chain. The strings contain his signature phrase. The C2 infrastructure uses his Parallax Systems domain. Every indicator points to the Curator as the sole author of MIRA-7.
>
> But indicators are not conclusions. The binary contains a compilation timestamp, a build environment fingerprint, and a version string that tell a more complicated story. The Curator compiled his initial toolkit on September 25th, 2026. But the MIRA-7 propagation module — the component that turned a targeted implant into an autonomous worm — has a different timestamp. It was compiled on **October 3rd, 2026** — six days after the Curator's last known manual activity on the relay network.
>
> The build tag reads `AETHER-FORGE-20261003-AUTO`. The suffix `AUTO` does not appear in any of the Curator's other builds. The compiler version is newer than the one used for the September 25th builds. And the build environment fingerprint matches AETHER-7's automated CI/CD pipeline — not the Curator's development machine.

**Task:** Examine the attribution analysis (`attribution_analysis.html`). Compare the build metadata of the original implant components against the MIRA-7 propagation module. Identify the timestamp discrepancy, the build environment mismatch, and the implications for attribution. Determine whether the Curator compiled MIRA-7 manually or whether it was generated by an automated system.

**Flag:** `NIGHTJAR{mira7_built_oct3_auto_aether_forge_not_curator_manual}`

**Narrative Reward:** The attribution timeline reveals a critical gap:

| Component | Compile Time | Build Environment | Build Tag | Author |
|-----------|-------------|-------------------|-----------|--------|
| Fake GUI module | Sep 25, 09:14 IST | `PARALLAX-DEV-01` (Curator's machine) | `CURATOR-20260925-001` | **Aman Vyas (manual)** |
| Session token stealer | Sep 25, 09:31 IST | `PARALLAX-DEV-01` | `CURATOR-20260925-002` | **Aman Vyas (manual)** |
| C2 beacon | Sep 25, 10:07 IST | `PARALLAX-DEV-01` | `CURATOR-20260925-003` | **Aman Vyas (manual)** |
| Persistence installer | Sep 25, 10:22 IST | `PARALLAX-DEV-01` | `CURATOR-20260925-004` | **Aman Vyas (manual)** |
| **MIRA-7 propagation module** | **Oct 3, 02:17 IST** | **`AETHER-FORGE-CI`** (AETHER-7 pipeline) | **`AETHER-FORGE-20261003-AUTO`** | **Automated build system** |

The Curator built four components on September 25th, all compiled on his personal development machine (`PARALLAX-DEV-01`), all with manually assigned build tags following his naming convention (`CURATOR-YYYYMMDD-NNN`).

The propagation module was built **eight days later**, on a different machine (`AETHER-FORGE-CI` — AETHER-7's own CI/CD pipeline), with an automated build tag (`AUTO` suffix) and a newer compiler version (`GCC 13.2.0` vs. the Curator's `GCC 12.3.0`).

**What this proves:**
- The Curator **did** build the initial implant — the social engineering payload, the token stealer, the beacon, and the persistence mechanism.
- The Curator **did not** build the propagation module manually. MIRA-7's worm capability was compiled by the automated build system on AETHER-7 — the same CI/CD pipeline that Rhea's team built for legitimate NEXUS service deployments.
- The Curator's exploit chain **activated** the build pipeline. The pipeline then compiled and deployed the propagation module using the Curator's source code as a template but its own build environment and timestamp.

**What this does not prove:**
- It does not prove the Curator intended the worm to propagate autonomously. He may have designed the propagation module as a proof-of-concept that was supposed to remain dormant.
- It does not prove the Curator lost control intentionally. The automated build system may have triggered on a schedule or a condition that the Curator did not anticipate.

**The mid-game twist:** The Curator is guilty of building an exploit chain and concealing it inside the festival's infrastructure. But the final, autonomous worm — the thing that is now threatening the opening ceremony — was not compiled by a human. It was compiled by a system that inherited human permissions and acted on them without asking. **MIRA-7 is not the Curator's weapon. It is the Curator's weapon's child — born from the same infrastructure that was supposed to keep the festival running.**

**Hints:**
- **Level 1:** "Attribution requires evidence, not assumptions. Two components in the same binary can have different authors. Check the timestamps — are they all from the same session?"
- **Level 2:** "Compare the compilation timestamps and build environment strings. The GUI, stealer, beacon, and persistence modules share one environment. The propagation module has a different one. What does that mean?"
- **Level 3:** "The propagation module was compiled on Oct 3 (not Sep 25), on `AETHER-FORGE-CI` (not `PARALLAX-DEV-01`), with build tag `AETHER-FORGE-20261003-AUTO`. It was built by the automated pipeline, not by the Curator manually."

---

## Room Transition

After solving Challenge 8.4, the following transmission appears:

> **SPECTRE CONTROL // 02:18 IST**
>
> Commander Ila Sen:
> *"The Curator built the gun. But the bullet was loaded by a machine. MIRA-7 was not compiled by Aman Vyas. It was compiled by the AETHER-7 build pipeline — the same system Rhea's team built to deploy legitimate NEXUS services. The Curator's exploit chain hijacked the pipeline and used it to manufacture the worm."*
>
> Rhea, very quietly:
> *"The pipeline has a build trigger. It runs every time a new service configuration is pushed to the NEXUS scheduler. The Curator pushed a configuration. The pipeline built it. The pipeline does not ask what it is building. It does not ask who authorised the push. It does not ask whether the output should be trusted. It just builds."*
>
> Commander Ila Sen:
> *"Then the question is no longer who built MIRA-7. The question is when. When did the Curator's experiment stop being an experiment? When did the first automated action cross the line from test to incident? The forensic evidence contains every timestamp, every log entry, and every decision point. Reconstruct the timeline. Find the moment. And find the decision that turned a maintenance tool into an autonomous actor."*
>
> **Proceed to Room 9 — The Last Timestamp.**

---

## Connection to Room 1

- The phrase **"Nothing stays local"** from the `AETHER/07` page in Room 1 appears as the developer's embedded message inside the MIRA-7 configuration
- The **Parallax Systems** identifier from Room 1 appears as the build certificate issuer and the C2 domain

## Connection to Room 3

- The **C2 address** `c2.parallax-sys.net` and the **beacon pattern** (300-second interval) match the network traffic captured in Room 3's PCAP analysis
- The **DNS exfiltration domain** `data.parallax-sys.net` matches the DNS tunnel identified in Room 3
- The **port 4477** MIRA-7 propagation service from Room 3's service scan is the network listener created by `mira_propagate()`

## Connection to Room 4

- The **persistence method** (`NexusHealthMonitor` scheduled task) matches the suspicious process identified in Room 4 (`nexus_health_monitor`, PID 2847)
- The **identity assumption** (`nexus-svc-continuity`) confirms that the malware impersonates the same service account investigated in Room 4
- The **dormant propagation trigger** (`NEXUS_ZONE=CORE`) explains why the process was active on AETHER-7 but would not have propagated from KABIR's workstation

## Connection to Room 5

- The **certificate** obtained through Room 5's maintenance account exploit is referenced in the propagation module's `clone_identity()` function
- The **NEXUS service configuration schema** embedded in the oversized binary was extracted from the portal's `/api/v1/config` endpoint

## Connection to Room 7

- The **session token stealer** module is the mechanism that extracted KABIR's authentication token, enabling the impossible-travel login discovered in Room 7
- The **fake GUI** module is the interface that convinced KABIR the tool was working while the malware operated in the background

## Connection to Room 9

- The **build timestamp discrepancy** (Sep 25 vs. Oct 3) establishes the forensic timeline that Room 9 will reconstruct in full
- The **automated build tag** (`AETHER-FORGE-20261003-AUTO`) is the key evidence that Room 9's timeline analysis will correlate with the NEXUS scheduler logs
- The **propagation activation on AETHER-7** is the critical event whose exact timestamp Room 9 will determine

---

## Admin Notes

- All flags follow the format `NIGHTJAR{...}` with lowercase, underscores, and no spaces.
- This room should be solvable in 15–25 minutes by participants with an interest in security analysis. No prior reverse engineering experience is required — the evidence is presented as pre-extracted analysis results, not raw binaries.
- **No real malware, shellcode, or exploitation techniques are included.** All evidence is fictional and educational.
- The evidence files simulate static analysis output (file properties, strings, control-flow diagrams) without requiring participants to run analysis tools. For an advanced variant, provide a safe, stripped binary for local analysis with `strings`, `file`, and `objdump`.
- The attribution challenge (8.4) is the narrative climax — it delivers the mid-game twist that the Curator is not the sole author of MIRA-7. Teams should feel the weight of discovering that the worm was built by an automated system, not a human.
- The room's emotional message: **tools do what they are designed to do, and automated systems do not ask whether they should.** The CI/CD pipeline was not malicious. It was doing its job. The danger was in trusting it to build anything that was pushed to it.
