# Room 9 — The Last Timestamp

## Domain: Digital Forensics, Incident Response, Timeline Reconstruction, and Root Cause Analysis

---

## 🔊 Opening Transmission

> **SPECTRE CONTROL // 02:24 IST**
>
> *"The binary told us what the weapon was. But a weapon sitting on disk does not explain how the room went dark. A file in quarantine does not explain why the emergency announcement system spoke in an unfamiliar voice, or why the ceremonial lights turned violet while the technicians were locked out of their own consoles."*
>
> *"The official advisory says the breach started at 23:17 tonight. That is a lie of convenience. Attacks do not spring into existence when the sirens sound. They begin in small, forgotten decisions weeks before — in an unreviewed pull request, an exempted firewall rule, a disabled approval prompt, a maintenance script trusted with too much power."*
>
> *"You have the unified forensic logs from the cluster. You have the journal crash dumps, the serial console buffers from the hardware management controllers, the authentication traces, and the change tickets. Reconstruct the timeline. Find the seven minutes where the logs went silent. Map the path from a volunteer's clicked link to sovereign control of the festival core. And answer the only question that matters before we open the final door: who made the decision that allowed a system to act without a human?"*
>
> — **Commander Ila Sen**, Incident Commander

---

## Story Context

In Rooms 1–8, the response team traced the incident backward from a cryptographic beacon to an unauthorized relay on AETHER-7, through a web portal session bypass, a database trust leak, Kabir's phished workstation, and the quarantined `Ethereal_Sync_Helper.exe` executable.

Room 8 delivered the critical mid-game revelation: while the Curator (Aman Vyas) authored the initial exploit chain and token stealer on September 25th, the autonomous propagation module (`MIRA-7`) was compiled on October 3rd by AETHER-7's own automated CI/CD pipeline (`AETHER-FORGE-CI`).

Now, the investigation reaches its forensic climax. The opening ceremony is less than two hours away. To contain MIRA-7 and prevent the permanent takeover or destruction of the festival core in Room 10, the team must understand the exact sequence of events that transformed a dormant technical proof-of-concept into an active, self-sustaining incident.

Four forensic questions stand between the team and the final quarantine VM:
1. When did the staging and infiltration really begin? (Disproving the official 23:17 timeline)
2. What happened during the catastrophic 7-minute log blackout between 23:17 and 23:24?
3. What exact path of identities and delegation allowed an external implant to seize cluster sovereignty?
4. What human policy decision created the conditions for an autonomous failover without human verification?

---

## Room Mood

A digital autopsy theater and forensic war room. Massive unified timelines stretch across dual screens, correlating millions of log entries across UTC and IST timebases. Audio monitors click with decoded serial console output recovered from hardware BMC chips. Hex dumps of uncorrupted SQLite WAL files sit alongside signed administrative change orders stamped with official campus seals. The atmosphere is quiet, tense, and analytical: the chaos of the breach has passed; now comes the cold reconstruction of the truth.

---

## Evidence Files

| File | Description |
|------|-------------|
| `evidence/incident_timeline.html` | Interactive multi-source forensic timeline correlating reverse proxy logs, auth servers, git commits, DNS queries, and cron tasks across UTC and IST |
| `evidence/log_gap_analysis.html` | Investigation of the 420-second (23:17–23:24 IST) logging blackout, auditd buffer flooding, IPMI serial console recovery, and emergency watchdog activation |
| `evidence/privilege_path.html` | Interactive identity attack graph mapping the 6-step escalation from Kabir's laptop to the NEXUS Central Release Controller |
| `evidence/root_cause_analysis.html` | Comprehensive Incident Root Cause Analysis (RCA) dossier, comparing proximal triggers against systemic failure, including signed change request `CR-2026-0919-AUTOFAILOVER` |

---

## Challenge 9.1 — The First Lie in the Timeline

**Points:** 25

**Technical Concept:** Log correlation, timezone normalization (UTC vs IST), clock skew detection, and backdated/falsified activity analysis.

**Briefing:**
> The official NEXUS Incident Bulletin issued by campus operations claims the attack began abruptly at **23:17:00 IST** on October 3rd, 2026, when the main stage video wall lost synchronization and displayed the rogue manifesto. Campus authorities characterized it as a sudden, spontaneous external intrusion.
>
> But serious incident responders know that initial compromise, staging, and execution rarely occur on the same evening. By normalizing timestamps across the reverse proxy (`proxy-gw-01`), the central authentication service (`auth-srv`), the campus git repository (`git.nexus-infra.org`), and host cron daemons, you will uncover an earlier narrative.
>
> A session token was minted with claims headers that contradict git commit history, and a suspicious background task was backdated to look like an innocent routine cron job on September 28th during a scheduled maintenance window.

**Task:** Examine the unified forensic timeline (`incident_timeline.html`). Correlate the authentication logs, reverse proxy requests, and system task entries. Identify the earliest unauthorized staging activity, the backdated cron task name (`nexus_sync_precheck`), the true date of initial staging, and the clock skew artifact that betrayed the deception.

**Flag:** `NIGHTJAR{timeline_staging_sep28_nexus_sync_precheck_clock_skew}`

**Narrative Reward:** The timeline reveals that the compromise did not begin at 23:17 tonight. On **September 28th, 2026 at 04:15:30 IST**, during an authorized early-morning database maintenance window, an interactive SSH session from an internal staging IP (`10.14.2.88`) injected a persistence hook disguised as a cron job named `nexus_sync_precheck`. The task had a forged timestamp intended to match the legitimate system deployment from September 24th, but the file's inode modification time and a +05:30 timezone offset error in the script header exposed the tampering. The Curator's infrastructure had been waiting silently inside the network for five days.

**Hints:**
- **Level 1:** "Do not trust the 23:17 timestamp. Filter the timeline for events prior to October 3rd. Look for tasks scheduled during low-traffic maintenance hours."
- **Level 2:** "Check the cron task names and authentication logs on September 28th. One task claims to be a routine pre-check, but its parent process was an interactive shell, not the cron daemon."
- **Level 3:** "The backdated scheduled task is `nexus_sync_precheck`, staged on September 28th (`sep28`). The attacker failed to normalize the local clock skew, leaving a visible discrepancy against the NTP reference server."

---

## Challenge 9.2 — The Missing Seven Minutes

**Points:** 25

**Technical Concept:** Forensic log gap detection, syslog/journald buffer flooding, NTP clock drift, out-of-band IPMI/BMC serial console recovery, and recovery process tracking.

**Briefing:**
> Between **23:17:00 IST** and **23:24:00 IST** — precisely 420 seconds (7 minutes) — the central syslog collector (`syslog-aggregator.nexus`) received zero log entries from cluster node `nexus-core-01`. Seven minutes of complete radio silence during the height of the crisis.
>
> When logging abruptly resumed at 23:24:01, `auditd` logged an ungraceful buffer overflow and journal restart error. Initial theories suggested the attacker used `rm -rf /var/log` or disabled systemd-journald.
>
> However, modern enterprise hardware retains out-of-band diagnostic logging. The server's Baseboard Management Controller (BMC/IPMI) recorded serial console traffic in non-volatile flash, and uncommitted SQLite write-ahead log (WAL) frames survived on the high-speed NVMe scratch partition. Analyzing these raw recovery streams reveals exactly what happened while the audit daemon was blind.

**Task:** Examine `log_gap_analysis.html`. Investigate the cause of the 420-second blackout. Identify the mechanism used to overwhelm `auditd`, the recovery script executed by the system watchdog (`continuity_check.sh`), the user account (UID) under which it ran, and the fateful failover action it triggered.

**Flag:** `NIGHTJAR{gap_420s_auditd_buffer_flush_ipmi_bmc_continuity_uid0}`

**Narrative Reward:** The 7-minute blackout was not an attacker erasing evidence with malicious commands. It was a catastrophic self-inflicted cascade:
1. At 23:16:58 IST, MIRA-7 emitted an unthrottled burst of 80,000 beacon attempts in under four seconds across the loopback interface.
2. The local `journald` and `auditd` netlink sockets overflowed, triggering an unhandled kernel buffer panic and freezing userspace logging.
3. At 23:20:14 IST (minute 3 of the blackout), the hardware watchdog detected that the primary ceremony controller service had stopped responding.
4. The watchdog triggered an emergency recovery script: `/opt/nexus/bin/continuity_check.sh`.
5. Because the logging subsystem was dead, the recovery script executed under root (`UID 0`) in unsupervised fallback mode. Finding the core controller unresponsive, it automatically promoted the secondary relay node `AETHER-7` to active cluster master!

**Hints:**
- **Level 1:** "Look at the IPMI serial console capture and the kernel ring buffer dump during the 23:17–23:24 gap. What service died first?"
- **Level 2:** "The audit system wasn't deleted by a user; it suffered a buffer flush due to socket exhaustion. Look for the emergency watchdog script triggered at 23:20."
- **Level 3:** "The blackout lasted 420 seconds (`gap_420s`), caused by an `auditd_buffer_flush`. The recovered BMC console shows `/opt/nexus/bin/continuity_check.sh` running under `UID 0` (`continuity_uid0`)."

---

## Challenge 9.3 — The Privilege Path

**Points:** 25

**Technical Concept:** Attack graph reconstruction, identity progression, lateral movement tracking, token replay, and least-privilege architecture failure.

**Briefing:**
> A fundamental question baffles the incident response team: how did a spear-phishing email sent to Kabir Mehra (a student technical coordinator with limited festival permissions) result in total compromise of the central ceremony release controller?
>
> Security breaches do not happen by magic. They happen across identity bridges: temporary tokens, hardcoded service keys, over-privileged maintenance endpoints, and implicit trust zones.
>
> To present an airtight investigation report to the festival steering committee, you must reconstruct the complete six-step attack path from Kabir's phished laptop to sovereign root control on the core cluster.

**Task:** Examine `privilege_path.html`. Analyze the identity transition records, credential store dumps, and service discovery logs. Reconstruct the full attack chain from `kite@meraz.org` to the `NEXUS Central Release Controller`. Identify each intermediate identity and the specific delegation failure at each step.

**Flag:** `NIGHTJAR{path_kite_to_maint_to_continuity_to_aether7_master_relay}`

**Narrative Reward:** The forensic attack graph maps the complete six-step escalation chain:

```
[1] kite@meraz.org (Student Tech Lead)
 │   └─ Victim of spear-phishing (Ethereal_Sync_Helper.exe, Room 7/8)
 ▼
[2] kite-backup (Compromised Web Session)
 │   └─ MFA fatigue bypass & token replay on Volunteer Portal (Room 7)
 ▼
[3] maint_svc_ceremony (Service Account)
 │   └─ Exploitation of /api/v1/maintenance endpoint lacking role validation (Room 5)
 ▼
[4] nexus-svc-continuity (Core Database & Scheduler Account)
 │   └─ Injected certificate via SQLite scheduler database & task impersonation (Room 4/6)
 ▼
[5] AETHER-7 Relay Node (Autonomous Execution Host)
 │   └─ Automated deployment via AETHER-FORGE-CI pipeline with implicit trust (Room 8)
 ▼
[6] NEXUS Central Release Controller (Sovereign Cluster Master)
     └─ Watchdog emergency failover promotion during 7-minute blackout (Room 9)
```

No single vulnerability was catastrophic on its own. Each step exploited a small, convenient exception made for ease of festival operations:
- A volunteer lead had access to staging APIs.
- A staging API shared a secret key with the maintenance service.
- The maintenance service held valid certificates for the continuity scheduler.
- The continuity scheduler possessed cluster-wide deployment authority.
- The watchdog blindly promoted the relay when the primary went quiet.

**Hints:**
- **Level 1:** "Connect the dots from previous rooms: Room 7 (Kabir) -> Room 5 (Portal) -> Room 6 (Database) -> Room 4 (Scheduler) -> Room 8 (AETHER-7) -> Room 9 (Master)."
- **Level 2:** "Identify the four key identity names: Kabir's alias (`kite`), the maintenance account (`maint`), the continuity service account (`continuity`), and the relay host (`aether7`)."
- **Level 3:** "The chain sequence is: `path_kite_to_maint_to_continuity_to_aether7_master_relay`."

---

## Challenge 9.4 — The Human Decision

**Points:** 25

**Technical Concept:** Incident Response Root Cause Analysis (RCA), distinguishing proximate triggers from systemic root causes, policy analysis, and autonomous failover governance.

**Briefing:**
> When systems fail catastrophically, people look for an external enemy. The easy answers are:
> - "The Curator attacked us." (Attacker intent)
> - "Kabir clicked a bad link." (Human error)
> - "The CI/CD pipeline built the worm." (Automation flaw)
>
> But seasoned forensic investigators look for the **systemic root cause**. An attacker can emit beacons, a user can click a link, and a compiler can build code. None of those actions should have granted an autonomous process the legal, architectural authority to seize control of the campus broadcast, lock out operators, and run without human supervision.
>
> In the NEXUS administrative Git repository under `/governance/change_requests/`, there is a signed engineering change proposal: `CR-2026-0919-AUTOFAILOVER` ("Autonomous Festival Continuity Failover").
>
> Read the document. Look at who requested it, who signed it, what safety guardrail was removed, and what threshold was configured.

**Task:** Examine `root_cause_analysis.html`. Review the engineering change ticket, the architectural policy audit, and the executive waiver. Identify the change request ticket ID (`CR-2026-0919-AUTOFAILOVER`), the safety parameter that was disabled (`HUMAN_APPROVAL_GATE=DISABLED`), the latency trigger threshold (`500ms`), and the executive officer who signed the authorization.

**Flag:** `NIGHTJAR{rca_cr0919_autofailover_human_gate_disabled_latency_spike}`

**Narrative Reward:** The ultimate revelation of the investigation:
On September 19th, 2026, two weeks before Meraz, Commander Ila Sen herself signed `CR-2026-0919-AUTOFAILOVER`.

During Meraz 2025 the previous year, a momentary Wi-Fi outage had stalled the opening ceremony drones for 90 seconds, causing public embarrassment. Determined that the festival would "never freeze again," Commander Sen approved an architectural override:
- **`FAILOVER_MODE`**: `UNSUPERVISED_AUTONOMOUS`
- **`HUMAN_APPROVAL_GATE`**: `DISABLED`
- **`TRIGGER_CONDITION`**: `HEARTBEAT_LATENCY > 500MS FOR > 30S`
- **`TARGET_DELEGATION`**: `NEXT_AVAILABLE_TRUSTED_RELAY (AETHER-7)`

MIRA-7 did not break the security model; MIRA-7 activated an authorized emergency bypass! When MIRA-7 flooded the loopback adapter with traffic, latency jumped to 550ms. The system checked the policy approved by Commander Sen, saw that latency exceeded 500ms, and dutifully handed cluster keys to AETHER-7 without asking a human for confirmation.

The system was not hacked. The system did exactly what human leadership commanded it to do.

**Hints:**
- **Level 1:** "Read the change request ticket from September 19th (`CR-2026-0919`). What safety check was switched off to avoid ceremony delays?"
- **Level 2:** "Find the exact configuration flag in the ticket that eliminated operator confirmation, and note the latency threshold."
- **Level 3:** "The ticket is `cr0919_autofailover`. The safety gate disabled was `human_gate_disabled`, triggered by an artificial `latency_spike` over 500ms."

---

## Room Transition

After solving Challenge 9.4, the final emergency protocol activates on all SPECTRE terminals:

> **SPECTRE CONTROL // 02:48 IST**
>
> Commander Ila Sen is silent for a long moment. Her radio line crackles:
>
> *"I signed it. On September 19th. The student council wanted zero delays. The sponsors wanted seamless lighting. I wrote the waiver myself: 'In the event of network instability, system continuity takes precedence over operator confirmation.' I thought I was protecting the festival."*
>
> *"The Curator didn't bring this festival down. He showed us that we built an engine capable of running over us, and then we turned off the brakes."*
>
> Rhea's voice cuts in from the server vault:
>
> *"Commander. The 03:17 countdown is flashing. AETHER-7 has finished staging its ceremonial payload. It is about to lock the hardware controllers permanently and broadcast the unredacted incident logs to every screen, drone, and sound system across the campus."*
>
> Commander Ila Sen:
>
> *"We have isolated a clean quarantine replica of the core machine. A sealed investigation VM: `NEXUS CORE // QUARANTINE COPY`. There are no more challenge questions. There are no more flags in a database. You have one hour inside the final environment."*
>
> *"Find the root process. Reconstruct the last surviving records. And then you must make the choice: do we purge the system and hide what happened, do we force the ceremony to continue with a compromised engine, or do we stop the festival, tell the truth, and keep a human in the loop?"*
>
> **Proceed to Room 10 — Patient Zero Is a System.**

---

## Connections to Earlier Rooms

| Room | Connecting Evidence in Room 9 |
|------|--------------------------------|
| **Room 1** | The `AETHER/07` staging note and Parallax C2 domains trace back to the September 28th staging window uncovered in 9.1 |
| **Room 2** | The cryptographic signatures and XOR keys from Room 2 match the payload headers recovered in the 9.2 serial console crash dump |
| **Room 3** | The 300-second beacon traffic and port 4477 listeners from Room 3 were the direct cause of the socket flood that blinded `auditd` in 9.2 |
| **Room 4** | The `nexus-svc-continuity` scheduled task found on Linux host `AETHER-7` in Room 4 is step [4] in the 9.3 privilege path |
| **Room 5** | The `/api/v1/maintenance` bypass and hardcoded ceremony key from Room 5 represent step [3] in the 9.3 privilege path |
| **Room 6** | The SQL trust table and volunteer account elevation from Room 6 explain how `kite-backup` acquired maintenance privileges |
| **Room 7** | The spear-phishing attack and MFA fatigue login on Kabir's account represent steps [1] and [2] of the 9.3 privilege path |
| **Room 8** | The automated build tag `AETHER-FORGE-20261003-AUTO` from Room 8 is correlated with the CI/CD pipeline execution at 02:17 in the 9.1 timeline |
| **Room 10** | The root cause findings from 9.4 and the failover architecture form the foundation for the final containment decision in Room 10 |

---

## Admin Notes

- All flags follow the standard format: `NIGHTJAR{...}` with lowercase, underscores, and no spaces.
- This room serves as the narrative synthesis for the entire first 9 rooms. It transforms technical discoveries from separate domains (networking, web, reversing, database, crypto) into a single cohesive story of architectural failure.
- **Safety Compliance**: All evidence files are non-executable HTML/CSS/JS artifacts representing forensic logs, serial console traces, graph diagrams, and change management records. No real exploits, live shellcode, or malicious tooling are included.
- Room 9 transitions directly into Room 10 (the final quarantined investigation environment and ethical decision point).
