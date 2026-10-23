# Room 4 — The Quiet Machine

## Domain: Linux, Processes, Permissions, Persistence, Logs, and System Security

---

## 🔊 Opening Transmission

> **SPECTRE CONTROL // 00:19 IST**
>
> *"AETHER-7 is not just a relay — it is a staging point. A browser terminal is now connected to the machine. Find what is running, find who logged in, and find out why KABIR's credentials are on a relay he has never accessed."*
>
> — **Commander Ila Sen**, Incident Commander

---

## Story Context

The network capture from Room 3 confirmed that AETHER-7 is hosting MIRA-7's propagation service and beaconing to a Parallax Systems command-and-control domain. Commander Ila Sen has ordered a forensic examination of the relay itself.

A browser terminal connected to a snapshot of AETHER-7's filesystem is now available. The machine is a small Debian-based Linux relay that was supposed to be air-gapped after testing. Someone reconnected it, installed a service, created an account, and planted a key — all without generating a standard deployment ticket.

KABIR's name is everywhere on this machine. His credentials, his SSH key comment, his username in the crontab. But the timestamps tell a different story: the account was configured after KABIR last changed his password, the key was generated on hardware he has never owned, and the crontab entry was written by a script, not a human.

**Get inside the machine. Separate the evidence from the framing.**

---

## Room Mood

A clean, quiet Linux terminal. The machine is not destroyed or obviously compromised — it looks like a well-maintained server with a few extra entries that do not belong. The mood is one of careful forensic work: every file, process, timestamp, and permission tells a story, but the obvious story is a lie. The attacker did not ransack the machine. They set it up to look like KABIR did everything.

---

## Evidence Files

| File | Description |
|------|-------------|
| `evidence/process_list.html` | Full `ps aux` and `ps -eo` output (with PPID), plus `dpkg -S` package verification checks |
| `evidence/auth_log.html` | Full `/var/log/auth.log` (~90+ lines, 4 days of events, no colour coding) |
| `evidence/filesystem_snapshot.html` | SUID binary audit (20 files), directory listings, group/user info, PAM config, crontabs, systemd units |
| `evidence/ssh_keys.html` | Raw authorized_keys, stat output, fingerprints, NEXUS device key registry, auth event log, journal entries |

---

## Difficulty Notes

**This room has been hardened significantly from earlier versions:**

- Evidence files contain **no colour-coded highlights**. No reds, no ambers visually marking the suspicious items.
- Evidence includes **red-herring entries** designed to mislead (e.g. `aether-token-helper` is a real dpkg-registered SUID binary; only one SUID file is unregistered and dangerous).
- The auth log is **~90 lines of realistic noise** — brute-force scans, legitimate admin logins, cron sessions — with the anomaly buried in the middle.
- The SSH key challenge requires **manual fingerprint cross-referencing** against a NEXUS device registry table rather than a pre-built comparison table.
- **Estimated completion time:** 35–50 minutes for participants with solid Linux knowledge.

---

## Challenge 4.1 — The Process with a Clean Name

**Points:** 25

**Technical Concept:** Process inspection, persistence detection, binary path analysis, package verification.

**Briefing:**
> 47 processes are running on AETHER-7. Most are exactly where they should be — systemd children, standard daemons, a couple of NEXUS-specific relay services. One process is running from a path that does not correspond to any installed package, under a service account that should not be spawning executables from hidden directories. Its name sounds legitimate. Its PID is unremarkable. Its interval hints at automation. But `dpkg -S` will tell you what the package database does not know.

**Task:** Examine the process list (`process_list.html`). Use both `ps aux` and the `ps -eo` output (which includes PPID). Cross-reference binary paths against the `dpkg -S` verification output at the bottom. Identify the process that is not registered to any installed package. Note its name, PID, and binary path.

**Flag:** `NIGHTJAR{nexus_health_monitor_pid_2847_opt_mira}`

**Narrative Reward:** The process is called `nexus-health-monitor` (PID 2847) and runs from `/opt/.mira/nexus-health-monitor`. It looks like a legitimate NEXUS monitoring daemon, but no such package exists in the APT database. The binary was placed in a hidden directory under `/opt/` and registered as a systemd service called `nexus-healthd.service`. It runs as the user `nexus-svc-continuity` — the same service account from Room 3's TCP exchange. The `--beacon-target=203.0.113.77:8443` flag on its command line is the same C2 endpoint from Room 3. This is MIRA-7's persistence mechanism.

**Hints:**
- **Level 1:** "Not every process with a sensible name belongs here. Names are cheap. Focus on the binary path column and the user running it."
- **Level 2:** "Check `dpkg -S` against every path you find suspicious. If a binary path returns 'no path found', the package manager does not know it exists."
- **Level 3:** "The process at PID 2847 runs from `/opt/.mira/` — a hidden directory. `dpkg -S /opt/.mira/nexus-health-monitor` returns nothing. It was placed there manually."

---

## Challenge 4.2 — The User Who Arrived Without a Login

**Points:** 25

**Technical Concept:** PAM authentication, auth log analysis, non-standard authentication mechanisms.

**Briefing:**
> The full auth log is here — four days of cron sessions, brute-force scan attempts, legitimate admin SSH sessions, and normal `sudo` calls. Standard noise. But somewhere in those four days, an account authenticated successfully and ran privileged commands without a single `Accepted publickey` or `Accepted password` line preceding it. No interactive session marker. No key exchange. Something else let it in. Find the line and the mechanism.

**Task:** Examine the authentication log (`auth_log.html`). Read it fully. Identify the account that got a session through a non-standard PAM module (not `pam_unix`). Note the account name, the PAM module name, and the session timestamp.

**Flag:** `NIGHTJAR{kite_backup_session_via_auth_token_0137}`

**Narrative Reward:** The account `kite-backup` opened a session at 01:37 IST via a PAM module called `pam_nexus_token.so`. The `sufficient` directive in `/etc/pam.d/sshd` means if this module succeeds, no further authentication is attempted — no password, no key. The token was issued by `nexus-svc-continuity`, which means the service account from Room 3 created a session *as KABIR's backup account* using a trust delegation that no human approved.

**Hints:**
- **Level 1:** "A successful login without `Accepted publickey` or `Accepted password` is not a normal SSH login. Something else authenticated this session."
- **Level 2:** "Look for any PAM module name other than `pam_unix`. The `sufficient` control flag in PAM means 'if this succeeds, skip everything else'."
- **Level 3:** "At 01:37:00, `pam_nexus_token` appears. This is not a standard Linux PAM module — it was installed manually on Sep 28 (check the filesystem snapshot for context)."

---

## Challenge 4.3 — The Permission That Lied

**Points:** 25

**Technical Concept:** Linux SUID permissions, package verification, group membership and privilege escalation analysis.

**Briefing:**
> The `find / -perm /6000` output shows 20 files with elevated permission bits. Most are standard — system utilities, OpenSSH helpers, DBus helpers, all registered in dpkg. Two are owned by the `nexus-svc` group. One of those is a registered package binary. The other was never installed by any package manager. That one is the problem. Figure out what group membership gives `kite-backup` access to it, and what running it as root actually does.

**Task:** Examine the filesystem snapshot (`filesystem_snapshot.html`). Cross-reference the SUID file list against `dpkg -S` output, directory origin, group ownership, and the group membership tables. Identify the SUID file that (a) is not registered in dpkg, (b) is group-executable by a group `kite-backup` belongs to, and (c) executes as root.

**Flag:** `NIGHTJAR{suid_aether_restart_owned_by_root_writable_by_nexus}`

**Narrative Reward:** `/opt/.mira/aether-restart.sh` has SUID set, is owned by `root:nexus-svc`, and is not registered in any package. The `nexus-svc` group includes both `nexus-svc-continuity` and `kite-backup`. Any member can execute it; it runs as root and restarts `aether-core.service`, enabling autonomous mode. The legitimate-looking `aether-token-helper` at `/usr/local/bin/` is a registered dpkg package and is a red herring.

**Hints:**
- **Level 1:** "Not all SUID files are dangerous. The standard ones in `/usr/bin/` are fine. Focus on those owned by non-standard groups or installed in non-standard locations."
- **Level 2:** "Run `dpkg -S` mentally on each SUID file. Any file in `/opt/` that returns 'no path found' was placed there manually. Then check which group can execute it."
- **Level 3:** "The file `/opt/.mira/aether-restart.sh` is SUID, not in dpkg, owned by `root:nexus-svc`. The `nexus-svc` group includes `kite-backup` (check `cat /etc/group`)."

---

## Challenge 4.4 — The Key in the Drawer

**Points:** 25

**Technical Concept:** SSH key fingerprint analysis, device registry correlation, temporal inconsistency detection.

**Briefing:**
> Two SSH keys are in `kite-backup`'s authorized_keys file. One comment says 2019, the other says 2024. Do not trust either comment. Look at the algorithm — what was commonly used in 2019 vs 2026? Look at the NEXUS device key registry: does the fingerprint of the suspicious key appear anywhere? Look at the file's `stat` output: when was this file actually created? Then check the journal and outbound auth events to find what tool generated the key and where it was used.

**Task:** Examine the SSH key analysis file (`ssh_keys.html`). Cross-reference the fingerprints in `authorized_keys` against the NEXUS device registry table. Check when the `authorized_keys` file was created (stat output). Find the journald keygen record. Identify the key that does not belong by its fingerprint, algorithm anachronism, and the tool that generated it.

**Flag:** `NIGHTJAR{ed25519_kite_backup_2019_added_oct_2026_aetherforge}`

**Narrative Reward:** The Ed25519 key with comment `kite-backup-2019` is suspicious on two counts: Ed25519 was rarely used in 2019, and its fingerprint (`SHA256:Wz4pLk8aQ3x...`) does not appear in the NEXUS device registry at all. The file `stat` shows it was created on 2026-10-01 — not 2019. The journald record at 01:33:50 confirms the key was generated by `AetherForge v2.1 (Parallax Systems)`. The same fingerprint then appears in the outbound auth event log authenticating to the volunteer portal at 02:10.

**Hints:**
- **Level 1:** "A key comment can say anything. The algorithm and the fingerprint are harder to fake. Compare each fingerprint against the NEXUS device registry."
- **Level 2:** "The NEXUS device registry does not contain the fingerprint `SHA256:Wz4pLk8aQ3x...`. That means this key was never registered on any NEXUS device. Now check when the authorized_keys file was created."
- **Level 3:** "File was created Oct 1, 2026 (stat). The journalctl output shows `AetherForge v2.1` generated the Ed25519 key at 01:33:50 on that same date, with a backdated comment."

---

## Room Transition

After solving Challenge 4.4, the following transmission appears:

> **SPECTRE CONTROL // 00:38 IST**
>
> Rhea confirms: *"The Ed25519 key in KABIR's authorized_keys file is not his. It was generated by the same toolchain that built the festival banner. The key has been used exactly once — to authenticate to the Meraz Volunteer Portal's administrative API."*
>
> Commander Ila Sen:
> *"KABIR is clear. He is embarrassed, not guilty. But the key that was planted in his name opened a door somewhere. The Volunteer Portal accepted a connection from AETHER-7 using this key three days ago. I need to know what the portal let in — and why it did not ask any questions."*
>
> The Meraz Volunteer Portal is now available for investigation.
>
> **Proceed to Room 5 — The Broken Gate.**

---

## Connection to Room 2

- The **"person who never signs in"** (`nexus-svc-continuity`) is confirmed as the service account running the hidden process and creating token-based sessions
- The **AETHER-7** relay from Room 2's tampered signature is the machine under investigation

## Connection to Room 3

- The **beacon** to `203.0.113.77` (c2.parallax-sys.net) is controlled by the `nexus-health-monitor` process discovered in Challenge 4.1
- The **custom protocol on port 7331** was used by the same service account that created the `kite-backup` session
- **MIRA-7's propagation service** on port 4477 is managed by the same systemd unit as the health monitor
- The **DNS exfiltration** username `kite_backup` matches the planted account on this machine

## Connection to Room 5

- The **Ed25519 key** planted in `kite-backup`'s authorized_keys was used to authenticate to the Volunteer Portal
- The **`pam_nexus_token.so`** module demonstrates the trust delegation pattern that the portal also uses
- The **KABIR exoneration** changes how teams approach Room 5 — they are no longer looking for an insider but for a system vulnerability

---

## Admin Notes

- All flags follow the format `NIGHTJAR{...}` with lowercase, underscores, and no spaces.
- **Difficulty:** This room should take 35–50 minutes for participants with solid Linux/forensics knowledge. No colour coding, no section labels, no pre-built comparison tables.
- **Red herrings:** `aether-token-helper` (registered SUID, dpkg-owned); multiple legitimate-looking processes with similar names; the Sep 28 root SSH sessions (legitimate deployment).
- The evidence is presented as HTML snapshots of terminal output. For a full CTF, provide a live container terminal.
- No real system access is required — all evidence is inspectable in a browser.
- All users, keys, paths, processes, and services are **entirely fictional**.
