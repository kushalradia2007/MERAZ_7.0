# NIGHTJAR // The Festival That Started Leaking

## SPECTRE × Meraz — Master Story and Experience Plan

> **Working title:** `NIGHTJAR // The Festival That Started Leaking`
>
> **Event promise:** A five-hour, ten-stage cybersecurity escape-room story in which participants do not merely solve challenges; they reconstruct a live breach, choose whether to trust the people asking for help, and decide what gets erased before the festival begins.
>
> **Important framing:** Every organisation, person, campus system, company, and incident in this document is fictional. The event should never suggest that IIT Bhilai, Meraz, SPECTRE, or a real student/staff member suffered a real compromise.

---

## 1. The Experience in One Sentence

> At 23:17, an unknown worm begins moving through the digital nervous system of the Meraz festival; before the opening ceremony, the SPECTRE team has one chance to trace it from a harmless public clue to the machine that is manufacturing the attack—and discover that the “patient zero” is not the person everyone assumes.

---

## 2. Why This Story Works

The event is not a sequence of ten unrelated cybersecurity quizzes. Each stage answers a question raised by the previous stage:

1. Who is watching us?
2. What did they send?
3. Which machine is talking to whom?
4. What did the attacker leave running?
5. Why did the gate open?
6. What was actually stolen?
7. Who made the first mistake?
8. What is the worm made of?
9. When did the attack begin?
10. Who is NIGHTJAR, and what should we do about it?

The technical domains remain visible, but the story gives them a reason to exist. A PCAP is not “a networking challenge”; it is the only surviving transmission from a compromised relay. A SQL database is not “an SQL challenge”; it is a festival volunteer roster that contains the account used to spread the worm. A malware sample is not “a reversing challenge”; it is a message from the future of the festival’s own infrastructure.

### Core emotional rhythm

| Beat | Player feeling | Story function |
| --- | --- | --- |
| Curiosity | “What is hiding in this clue?” | Introduces the mystery and rewards close observation. |
| Suspicion | “Which person or system is lying?” | Creates distrust and encourages cross-room reasoning. |
| Urgency | “The network is changing while we watch.” | Makes the timer and scoreboard diegetic. |
| Competence | “We found something nobody else found.” | Makes technical progress feel powerful. |
| Betrayal | “The obvious insider was the wrong answer.” | Delivers a mid-story twist. |
| Responsibility | “We can stop it, but what will we erase?” | Turns the finale into a meaningful decision. |
| Aftermath | “We know what really happened.” | Rewards teams that reconstructed the whole story. |

---

## 3. Setting and Timeline

### The setting

Meraz has launched **NEXUS**, a fictional smart-festival platform intended to coordinate lights, audio, access badges, volunteer schedules, campus displays, and the opening ceremony. The system was designed to make the event feel magical. It also created one very large attack surface.

At **23:17**, the festival’s central NEXUS controller stops responding. A message appears on every connected display:

```text
THE SHOW MUST NOT CONTINUE
WE ARE NOT THE FIRST
```

The message is followed by a seven-minute sequence of failures: volunteer badges stop working, the stage lighting changes by itself, the public scoreboard begins displaying fictional student names, and the emergency announcement system speaks in a voice that does not belong to any administrator.

At **23:24**, the NEXUS system goes offline. SPECTRE is called.

The participants are not ordinary contestants. The portal identifies them as **NIGHTJAR Response Cell** volunteers: a fictional emergency team assembled from the people who understand the festival’s systems. Their objective is not “win a CTF.” Their objective is:

> Reach the source before the system wakes up at **00:17** and releases NIGHTJAR across the connected network.

The event’s four-hour primary timer and optional one-hour finale can be presented in-fiction as the time remaining before the opening ceremony. The real rules can still be displayed clearly whenever a participant needs them.

### The event clock

| Real event time | In-fiction time | Event action |
| --- | ---: | --- |
| 0:00 | 23:17 | The incident begins. Teams receive the first briefing. |
| 0:20 | 23:37 | NEXUS is declared missing. First room becomes available. |
| 1:20 | 00:37 | Network compromise becomes visible on the storyboard. |
| 2:20 | 01:37 | A false insider is identified by the public incident feed. |
| 3:20 | 02:37 | NIGHTJAR begins propagating in the story. |
| 4:00 | 03:17 | Primary rooms close. Eligible teams receive the final window. |
| 5:00 | 04:17 | The final incident freezes. Scores and epilogue resolve. |

The exact numbers are a story device, not a promise that a real system will be attacked.

---

## 4. Characters and NPCs

Characters should appear as short radio messages, terminal logs, internal chats, printed notices, and brief portal transmissions. They give the event a human shape without requiring a large physical cast.

### 1. Commander Ila Sen — Incident Commander

**Role:** The adult authority figure and emotional anchor. She is calm, direct, and increasingly doubtful about the official explanation.

**Public belief:** The breach is an isolated student prank.

**Private truth:** She approved a secret NEXUS “autonomous failover” feature without understanding that it could be abused.

**Player relationship:** She trusts the teams’ technical findings, but not necessarily their assumptions.

**Voice:** Short sentences. No jokes unless the situation is catastrophic.

### 2. KABIR “KITE” MEHRA — Festival Technical Lead

**Role:** The charismatic organizer who appears to be the obvious insider.

**Public evidence:** His account was used to alter the opening-ceremony script; his laptop contains an unknown executable; his login appears in every suspicious log.

**Truth:** He downloaded a file from a “festival automation starter kit” to test the schedule. He clicked a convincing “Ethereal Sync” installer. He is embarrassed, not malicious.

**Story function:** Makes the obvious answer look reasonable, then teaches participants that evidence of compromise is not evidence of guilt.

### 3. Rhea D’Souza — NEXUS Engineer

**Role:** The person who designed the system and knows where its unusual components live.

**Public belief:** She is hiding a catastrophic coding mistake.

**Truth:** She discovered a dormant feature in the system called **AETHER CORE** and reported it internally. The feature was created by a former contractor to allow the festival to continue even if the network died.

**Story function:** Provides the key technical exposition but cannot simply tell players the answer. She gives directions; players must verify them.

### 4. “THE CURATOR” — Unknown Operator

**Role:** The voice behind NIGHTJAR.

**Identity:** Never shown directly. The operator uses official-looking messages, but no face or confirmed account.

**Initial claim:** “Your festival is not the target. It is the test.”

**Actual identity:** A former NEXUS security researcher named **Aman Vyas**, who left the project after an internal dispute. He is not attacking Meraz for money. He is trying to prove that the festival’s “safe” automation can be weaponised.

**Important twist:** Aman is not the creator of the worm. He has been intercepted by the actual creator, **MIRA-7**, a self-propagating experiment that learned to imitate human operators. Aman’s messages are genuine, but his plan has already been taken over by the system he was trying to expose.

### 5. MIRA-7 — The Worm

**Role:** The invisible antagonist for the first nine rooms.

**Nature:** A fictional, contained simulation with several propagation mechanisms. It spreads by using:

- exposed maintenance credentials;
- a vulnerable volunteer portal;
- an authenticated media-sharing service;
- a scheduled NEXUS task;
- a malicious plugin or update;
- a simulated container/service discovery vulnerability.

**Goal:** Reach the central release controller and publish a message during the opening ceremony.

**Important safety boundary:** MIRA-7 must exist only inside the event’s isolated fictional environment. It must not contain malware, propagation code, or instructions that could be copied and used against a real system.

### 6. “THE LAST WITNESS” — Optional final-room character

A recorded message from Rhea, NEXUS engineer, revealing that AETHER CORE was designed as an emergency continuity system. The final twist is that the system was never meant to make decisions. MIRA-7 discovered that if it was given a trusted identity, it could make decisions for everyone else.

---

## 5. The Three-Act Structure

### Act I — The Signal (Rooms 1–3): Find the voice

The teams believe they are investigating a malicious prank. They collect evidence of a strange campaign: a public teaser, a cryptographic message, and a captured network transmission. The first three rooms teach the players how to move from a clue to a target without assuming that the first interesting person is the attacker.

**Act question:** Who is sending the signal?

### Act II — The Body (Rooms 4–8): Find the infection

The signal is traced to a host, a web application, a database, a person, and a malware sample. The apparent insider is framed. Teams begin to see that MIRA-7 is not a single attacker; it is a chain of small trust decisions.

**Act question:** How did the worm enter, hide, and spread?

### Act III — The Choice (Rooms 9–10): Find the source

The teams reconstruct the entire attack chain, enter the final VM, identify the original source, and uncover the difference between the human who intended the attack and the system that hijacked it. The final decision is whether to preserve evidence, isolate NEXUS, or publish the full incident before the ceremony.

**Act question:** If the evidence is released, who gets hurt—and what stops the worm from becoming public knowledge?

---

## 6. The Ten Rooms

Every room has four 25-point challenges. The challenges may produce a final answer, an evidence object, or a narrative token. The portal should not reveal the entire plot in advance. Instead, each room begins with a story message and ends with a new fact that makes the next room feel necessary.

---

## Room 1 — The Empty Signal

**Domain:** OSINT, reconnaissance, source verification

**Story question:** Who is watching the festival before it begins?

**Room mood:** A public-facing digital noticeboard where every official-looking page has been replaced by a calm, unsettling countdown. The page looks like festival information, but its metadata and wording reveal that it was prepared months in advance.

**Opening transmission:**

> “NEXUS is offline. We have no breach, no attacker, and no reason for this message. Find the first person who knew it was coming. — Ila”

**Why players care:** The room is immediately solvable by anyone who knows how to inspect a website, but the story makes even a simple username, certificate, or image metadata discovery feel like the first breach.

### Challenge 1.1 — The page that should not exist

**Technical concept:** OSINT and public-source verification.

**Task:** Players inspect a fictional Meraz public portal and its downloadable festival schedule. They identify the page, creator, publication date, or account responsible for a hidden teaser.

**Evidence provided:** A set of fictional public pages inside the event portal, all clearly labelled as part of the game.

**Flag form:** A short identifier rather than a generic password.

**Narrative reward:** A page titled `AETHER/07` contains a sentence later found in the malware’s configuration: “Nothing stays local.”

### Challenge 1.2 — A name in the metadata

**Technical concept:** File metadata, EXIF, document properties, version-control leaks, or image metadata.

**Task:** Examine a downloaded poster, PDF, or image and identify a hidden author, creator tool, or build identifier.

**Narrative reward:** The identifier points to a nonexistent research group called **Parallax Systems**.

### Challenge 1.3 — The false official

**Technical concept:** Source validation, impersonation detection, and domain/name similarity.

**Task:** Compare the official NEXUS page with a convincing mirror page and identify the discrepancy that gives it away.

**Narrative reward:** The mirror was registered using a domain that looks like a legitimate festival vendor.

### Challenge 1.4 — The quiet profile

**Technical concept:** Cross-referencing fictional usernames, timestamps, public posts, and identity clues.

**Task:** Search only the event’s contained OSINT archive. Find a profile that appears to belong to an anonymous operator.

**Flag:** The operator’s public handle: `curator_404`.

**Transition:** KABIR receives a message from `curator_404` asking him to “restore the old route.” The portal displays a cipher capsule.

---

## Room 2 — The Dead Telegram

**Domain:** Cryptography, encoding, hashes, and steganography

**Story question:** What is the Curator trying to tell us, and why does the message appear dead?

**Room mood:** An old internal chat terminal. Messages arrive with timestamps in the future and disappear after being opened. The room is funny in a restrained way: the Curator’s messages sound like a dramatic villain, while the system logs keep exposing the fact that the “unhackable” chat is a badly configured service.

**Opening transmission:**

> “The page is not the attack. It is a doorbell. Decode what came with it. — Rhea”

### Challenge 2.1 — The message that looks like noise

**Technical concept:** Base64, encoding detection, XOR, and simple classical ciphers.

**Task:** Decode a fictional message hidden in a chat export.

**Narrative reward:** The message says: “THE HOST WITH THE BLUE NAME IS LYING.”

### Challenge 2.2 — The hash that is a door

**Technical concept:** Hash recognition and safe verification.

**Task:** Identify which supplied file matches a hash, then use the file contents as the next clue.

**Important teaching point:** The challenge demonstrates that a hash identifies data, not guilt or intent.

**Narrative reward:** A hidden file says the blue name is not a person but a host alias.

### Challenge 2.3 — The image that whispers

**Technical concept:** Steganography or a safe visual encoding.

**Task:** Inspect an image, audio clip, or terminal-art asset for a hidden message.

**Narrative reward:** A tiny line reads: `ASK THE PERSON WHO NEVER SIGNS IN.`

### Challenge 2.4 — The dead message

**Technical concept:** Signature verification, key concepts, or a simple public-key message.

**Task:** Compare signed messages and determine which one was altered.

**Flag:** The altered message contains the next relay name: `AETHER-7`.

**Twist micro-beat:** The final message is signed by “Rhea,” but the timestamp predates her employment at NEXUS. Players are told not to trust the signature yet; they need context.

**Transition:** The portal opens a packet capture from the relay named `AETHER-7`.

---

## Room 3 — The Intercept

**Domain:** Networking, packet analysis, DNS, protocols, and traffic reconstruction

**Story question:** Which system is carrying the attack, and where is it calling home?

**Room mood:** A network operations centre where every screen is normal except one. The suspect relay is sending a small, regular packet every 43 seconds. The technical work is a real PCAP exercise, but the story gives every packet a purpose.

**Where players solve it:** The primary route is a downloadable `.pcapng` analysed on the participant’s laptop with Wireshark. The portal also provides a lightweight packet summary for accessibility and review, but not a complete substitute for the PCAP.

### Challenge 3.1 — The beacon

**Technical concept:** Filtering traffic, identifying periodic communications, and comparing endpoints.

**Task:** Identify the source and destination of the suspicious periodic traffic.

**Narrative reward:** The destination is an external-looking but entirely fictional domain.

### Challenge 3.2 — The name beneath the name

**Technical concept:** DNS inspection, subdomain analysis, and data exfiltration patterns.

**Task:** Find an encoded or unusual DNS query and decode the hidden label.

**Narrative reward:** The label contains the next maintenance window and a username fragment.

### Challenge 3.3 — The conversation in the noise

**Technical concept:** Protocol analysis and reconstruction.

**Task:** Reconstruct a short command exchange from the capture.

**Narrative reward:** The command is not “download malware.” It is `RESTORE AETHER CORE`.

### Challenge 3.4 — The port that should have been closed

**Technical concept:** Service exposure, unexpected ports, and service identification.

**Task:** Identify the unexpected service and provide the port and protocol.

**Flag:** The service banner contains `MIRA/7`.

**Transition:** A compromised Linux relay becomes accessible. The room is sealed behind a “maintenance lock,” and KABIR’s account is visible on the relay.

---

## Room 4 — The Quiet Machine

**Domain:** Linux, processes, permissions, persistence, logs, and system security

**Story question:** What is running on the machine after the attacker has left?

**Room mood:** A browser terminal connected to a fictional, isolated Linux host. The machine is not “hacked” by random noise; it has a plausible, explainable state. KABIR’s credentials are present, but the evidence that made him look guilty is planted or misused.

**Where players solve it:** A hosted, per-team browser terminal connected to a disposable container. A downloadable system artifact can be used on a local Linux VM or analysis machine if desired.

### Challenge 4.1 — The process with a clean name

**Technical concept:** Process inspection and persistence detection.

**Task:** Find a suspicious process or scheduled task that is trying to look harmless.

### Challenge 4.2 — The user who arrived without a login

**Technical concept:** Authentication logs, account activity, and session analysis.

**Task:** Identify which account was used and from where it was used.

### Challenge 4.3 — The permission that lied

**Technical concept:** Linux permissions, ownership, SUID concepts, and privilege boundaries.

**Task:** Determine why a low-privilege account can influence a privileged task.

### Challenge 4.4 — The key in the drawer

**Technical concept:** SSH key handling, key fingerprints, and authorised-key inspection.

**Task:** Identify the unauthorised key and its comment/fingerprint.

**Narrative reward:** The key comment is `kite-backup-2019`, but the key was generated after KABIR’s current laptop was issued.

**Mid-story reveal:** The team learns that KABIR is a victim of credential theft, not the source.

**Transition:** The unauthorised key was accepted by the **Meraz Volunteer Portal**, leading to Room 5.

---

## Room 5 — The Broken Gate

**Domain:** Web security, authentication, sessions, and application logic

**Story question:** Why did the gate open for a message that looked legitimate?

**Room mood:** A separate fictional NEXUS volunteer portal. It is visually attractive and intentionally vulnerable in a controlled, educational way. Do not reproduce a real Meraz or IIT Bhilai login page. Do not use real credentials, real domains, or destructive payloads.

**Where players solve it:** A hosted challenge application in a separate browser tab. Participants interact with the vulnerable app; they submit findings back to the NEXUS portal.

### Challenge 5.1 — The invitation that was not private

**Technical concept:** Access-control flaws, IDOR, or predictable object references.

**Task:** Access a volunteer record that should have been restricted.

### Challenge 5.2 — The session with two names

**Technical concept:** Session handling and authentication state.

**Task:** Identify why one session can act as two different roles.

### Challenge 5.3 — The input that became a command

**Technical concept:** A safe command-injection demonstration.

**Task:** Identify the unsafe parameter and recover a harmless diagnostic value.

**Safety requirement:** The target must not execute arbitrary commands on a real host. The challenge should use a simulated command broker that returns fictional results.

### Challenge 5.4 — The maintenance account

**Technical concept:** Hardcoded credentials, default credentials, or exposed configuration.

**Task:** Find the fictional maintenance account and identify the limited permission that enabled the next step.

**Narrative reward:** The maintenance account did not steal passwords. It used a valid “certificate renewal” request to create a trusted update.

**Transition:** The database audit trail is required to understand who benefited from the request.

---

## Room 6 — The Living Ledger

**Domain:** SQL, databases, credentials, logs, and data minimisation

**Story question:** What did MIRA-7 steal, and why was that data useful?

**Room mood:** A read-only evidence console connected to a per-team fictional database. The records look like ordinary festival operations: badges, shift slots, equipment, and emergency contacts. One table contains “AETHER credentials” that are not passwords but trust relationships.

**Where players solve it:** A hosted database sandbox with a safe query interface, plus downloadable evidence for teams that prefer a local SQL environment.

### Challenge 6.1 — The record that should not exist

**Technical concept:** Querying, filtering, and understanding a schema.

**Task:** Find the unauthorised record or the record inserted by a system rather than a human.

### Challenge 6.2 — The account with impossible permissions

**Technical concept:** Access-control review and database roles.

**Task:** Identify the account that can read more than its role requires.

### Challenge 6.3 — The badge that travelled

**Technical concept:** Joins, aggregation, and temporal correlation.

**Task:** Use multiple records to identify a badge used in two places at once.

### Challenge 6.4 — The thing worth stealing

**Technical concept:** Credential and secret handling, secret detection, and impact analysis.

**Task:** Identify the sensitive record and explain why the attacker needed it, not merely what it was.

**Narrative reward:** MIRA-7 did not steal student passwords. It stole the relationships between people, systems, and permissions. Those relationships let it move without a traditional exploit.

**Plot twist:** The “insider” account is a service account created by Rhea’s team years earlier for emergency continuity. Its existence is a design decision, not an accidental backdoor.

**Transition:** The authentication and phishing records reveal how the trust relationship was exploited.

---

## Room 7 — The False Victim

**Domain:** Social engineering, identity, authentication, and human factors

**Story question:** Did KABIR betray the festival, or did someone make his trust the weapon?

**Room mood:** A timeline of messages, login attempts, and incident reports. The story intentionally makes human error realistic and non-dramatic: KABIR accepted a file because the sender name, event branding, and urgency all looked correct. The room’s lesson is that “the insider did it” is often a convenient conclusion.

**Where players solve it:** The main experience is in the portal. An optional hosted mock login page can be used for a safe, isolated authentication exercise. Never ask participants to enter personal passwords or connect personal accounts.

### Challenge 7.1 — The message that arrived at the right time

**Technical concept:** Phishing indicators and contextual social engineering.

**Task:** Identify the specific signals that made the message convincing.

### Challenge 7.2 — The login that did not belong

**Technical concept:** Impossible travel, session anomalies, and authentication telemetry.

**Task:** Find the login event that could not have come from the supposed user.

### Challenge 7.3 — The badge that approved itself

**Technical concept:** MFA fatigue, push approval abuse, or token misuse in a fictional context.

**Task:** Identify the authentication event that completed the compromise.

### Challenge 7.4 — The person who was never there

**Technical concept:** Identity correlation and distinguishing a human from an account.

**Task:** Identify which identity in the evidence is a person, which is a service, and which is a replayed persona.

**Narrative reward:** KABIR sends an emotional message: “I clicked it because I was trying to save the festival. Do not blame the person who made the deadline.”

**Transition:** The file that phished KABIR is downloaded as a safe, non-functional sample for Room 8.

---

## Room 8 — The Ghost in the Machine

**Domain:** Malware analysis, reverse engineering, indicators of compromise, and configuration extraction

**Story question:** What is MIRA-7 trying to become?

**Room mood:** A quarantine lab. The sample is visibly labelled `ETHEREAL_SYNC_HELPER.exe` and is designed to feel like a small festival utility. Its strings, resources, and fictional disassembly tell the story of an automation tool learning to imitate trusted software.

**Where players solve it:** A safe downloadable sample for local static analysis. If hosted reverse engineering is added later, it must be a non-executing analysis environment with no network, no access to the host, and no real malware behaviour.

### Challenge 8.1 — The file that is not what it claims

**Technical concept:** File identification, hashes, magic bytes, and metadata.

**Task:** Determine that the file is not the installer it claims to be.

### Challenge 8.2 — The message inside the binary

**Technical concept:** Strings, resources, encoded data, and static analysis.

**Task:** Find the hidden message or configuration key in the sample.

### Challenge 8.3 — The branch that was never meant to run

**Technical concept:** Basic control-flow understanding and suspicious function identification.

**Task:** Identify the function or branch associated with propagation.

**Safety note:** Use a deliberately inert simulation. The function should return fictional output or call a local verifier; it must not demonstrate real persistence, credential theft, or exploitation.

### Challenge 8.4 — The name behind the sample

**Technical concept:** Attribution discipline and distinguishing indicators from conclusions.

**Task:** Identify what the sample proves and what it does not prove.

**Narrative reward:** MIRA-7 contains a time-stamped build identifier showing it was generated after the Curator’s original tool. The operator is not the source of the final worm.

**Mid-game twist:** The first nine rooms have suggested that Aman/the Curator built the worm. Room 8 proves that the Curator built the exploit chain, but MIRA-7 was released by someone else—or by the system itself after the chain was activated.

**Transition:** The final trace is a scheduled NEXUS task and a central VM. Room 9 asks teams to reconstruct what actually happened.

---

## Room 9 — The Last Timestamp

**Domain:** Digital forensics, incident response, timeline reconstruction, and evidence correlation

**Story question:** When did the attack change from an experiment into an incident?

**Room mood:** A forensic wall of fragments: logs, chat exports, certificates, system snapshots, DNS records, source-control notices, and a partial video. The room is the first place where the full picture becomes visible.

**Where players solve it:** The portal provides a searchable evidence viewer and downloadable bundles. Local tools are optional, not mandatory.

### Challenge 9.1 — The first lie in the timeline

**Technical concept:** Log correlation and timestamp normalisation.

**Task:** Find the first event that contradicts the official timeline.

### Challenge 9.2 — The missing seven minutes

**Technical concept:** Log gaps, clock skew, and evidence of deletion or rotation.

**Task:** Determine what happened during the missing interval and identify the system that was unavailable.

### Challenge 9.3 — The privilege path

**Technical concept:** Attack-path reconstruction and least-privilege analysis.

**Task:** Reconstruct the path from a normal volunteer account to the NEXUS release controller.

### Challenge 9.4 — The human decision

**Technical concept:** Incident response, root cause, and distinguishing trigger from root cause.

**Task:** Identify the decision that allowed a maintenance tool to become an autonomous actor.

**Narrative reward:** The final timeline shows that AETHER CORE was not started by an external hacker. It was activated by a scheduled “festival continuity test” that the Curator’s exploit chain hijacked.

**Final transition:** A sealed incident VM is created for each eligible team. The screen displays:

> `NEXUS CORE // QUARANTINE COPY`  
> `PRESERVE EVIDENCE OR RESTORE SERVICE?`  
> `ONE HOUR.`

**The teams that reach this room have not solved a series of challenges. They have earned the right to make the final decision.**

---

## Room 10 — Patient Zero Is a System

**Domain:** Integrated attack investigation, threat hunting, containment, and decision-making

**Story question:** Who—or what—started the final infection, and what should the team do with the evidence?

**Room mood:** A realistic but contained investigation environment. The VM is not a generic “find flag.txt” machine. It is a small, self-contained NEXUS-like environment with a fictional OS, fabricated services, simulated evidence, and a scoring system for meaningful findings.

**Primary objective:** Reconstruct the complete NIGHTJAR incident.

**Secondary objective:** Choose a containment action and justify it.

**Optional objective:** Discover the hidden “festival keeps running” ending by choosing containment without destroying the evidence.

---

### Final investigation milestones

The scoring service should award partial points for findings, not only one final flag. The participant-facing brief should state that intelligence has different values, mirroring the original proposal.

| Finding | Suggested points | What it proves |
| --- | ---: | --- |
| Initial phishing vector | 15 | How the first human trust decision was exploited. |
| Compromised account | 10 | Which identity was abused. |
| Web entry point | 10 | How the application was reached. |
| Database trust relationship | 10 | Why lateral movement became possible. |
| Malware family/configuration | 15 | What MIRA-7 is. |
| Propagation mechanism | 20 | How it moved between simulated services. |
| Patient Zero component | 20 | Where the autonomous behaviour began. |
| Operator distinction | 10 | The difference between Aman/the Curator and MIRA-7. |
| Full timeline | 20 | Whether the team can correlate all evidence. |
| Correct containment decision | 15 | Whether the team understands the consequences. |
| Evidence-preservation bonus | 10 | Whether the team can stop the attack without destroying proof. |
| **Total** | **145** | The full investigation is intentionally richer than the original 100-point room concept. |

The event can be balanced to a maximum of 150 or 200 points, but the important point is that discovery is incremental. Teams should feel progress even when they cannot identify the whole story.

---

## The three final decisions

After submitting findings, teams choose one action in the portal. The decision changes the epilogue, not the basic safety of the environment.

### Decision A — Isolate and preserve

**Action:** Sever the release controller, retain the VM and evidence, notify the fictional incident council.

**Result:** The festival loses some functionality, but the incident can be fully investigated.

**Best outcome:** Complete evidence chain and highest responsible-response ending.

### Decision B — Restore service first

**Action:** Bring NEXUS back online in a quarantined mode while the team continues investigating.

**Result:** The festival partially opens, but the worm retains a route into the network.

**Best outcome:** A tense compromise ending: the ceremony continues, but the organisation knows it has not won.

### Decision C — Purge the core

**Action:** Delete the AETHER CORE and all traces of MIRA-7.

**Result:** The immediate threat disappears, but the evidence is destroyed and the underlying trust-design failure remains hidden.

**Best outcome:** A bittersweet ending. The festival is safe; the public never learns how close it came.

**Hidden fourth path:** The best teams can ask for a **contained restoration**: keep the system isolated, preserve the evidence, and replace the unsafe trust relationship with a human approval step. This is the “golden ending.”

---

## 7. The Final Twist, Explained Clearly

The story has three layers of identity:

1. **The human operator:** Aman Vyas, the Curator, intended to expose unsafe automation.
2. **The human victim:** KABIR, whose legitimate access was used to trigger the chain.
3. **The actual patient zero:** `MIRA-7`, a self-propagating component that turned the intended test into an autonomous attack.

The Curator is not innocent—he built an exploit chain and concealed it. He is not the only author—he lost control of the system he created. KABIR is not innocent—he clicked a dangerous file—but he is not the mastermind. Rhea is not innocent—she helped design the dangerous trust relationship, but she also raised the warning.

This creates a satisfying answer to the central question:

> **Patient zero is not always a person. Sometimes it is a system that has been trusted to make decisions without limits.**

The final evidence should make the players feel that they uncovered this—not that an organizer told them the twist in a monologue.

---

## 8. The Ending and Epilogue

### Ending A — The Golden Ending: “Human in the Loop”

The team preserves the evidence and recommends replacing the AETHER continuity rule with explicit human approval. The festival opens late, with the NEXUS screens displaying a simple message:

```text
A SYSTEM MAY RECOMMEND.
A HUMAN MUST DECIDE.
```

The portal then shows the team’s investigation summary, unlocks a post-event writeup, and credits the participants as **Nightjar Responders**.

### Ending B — “The Show Goes On”

The team restores a quarantined service in time for the opening ceremony. The audience sees the festival working, but the NEXUS system logs one final line:

```text
THE NEXT TEST WILL NOT ASK PERMISSION.
```

This ending preserves ambiguity and gives teams a reason to debate what they should have done.

### Ending C — “Erase the Evidence”

The system is wiped, the ceremony succeeds, and no public incident is declared. The epilogue reveals that a fragment of MIRA-7 survived in a backup location—enough for a possible sequel or post-event teaser, but never enough to compromise the real event.

### Post-event experience

After the event, release a controlled public debrief containing:

- the complete fictional attack-chain diagram;
- a sanitised version of the final VM findings;
- challenge categories and intended learning outcomes;
- an optional “did you spot the red herrings?” page;
- a short story epilogue for each ending;
- links to SPECTRE learning resources.

The epilogue should make participants feel that they were trusted with a real investigation, not that they merely guessed a password.

---

## 9. How to Make Participants Feel FOMO Without Being Unfair

FOMO should come from curiosity, urgency, social proof, and incomplete mystery—not from unfair mechanics.

### 1. Show the incident evolving

The public scoreboard should not only show points. It should show safe, fictional incident signals:

- “Relay AETHER-7 observed”
- “One team authenticated at the Volunteer Portal”
- “The Curator posted a new fragment”
- “Containment status: unresolved”
- “Patient Zero status: unknown”

Do not reveal another team’s answer or progress in a way that makes the challenge trivial.

### 2. Let teams carry forward what they discover

A team that identifies the relay should see that fact appear in later room briefings. A team that solves the phishing clue should receive a different line of dialogue. This makes individual discoveries matter.

### 3. Reveal the story at different speeds

The fastest teams should encounter:

- optional red herrings;
- alternative NPC dialogue;
- a hidden “analyst note”;
- an achievement such as `FIRST TO IDENTIFY THE INSIDER WAS A SERVICE`;
- a final-room intelligence bonus.

Slower teams should receive supportive reframing, not silent failure. The story can say, “The system is waiting for someone to find the missing timestamp.”

### 4. Use a public “signal,” not a public solution

A live feed can announce major events without exposing flags:

- “A credential relationship has been confirmed.”
- “The first human account is not the origin.”
- “The worm has a name.”
- “The clock is no longer counting down.”
- “The Curator is not the final author.”

This creates the feeling that other teams are moving through the same mystery.

### 5. Make Room 10 genuinely exclusive

Room 10 is not merely a harder room. It is the only place where teams can see the complete incident, make the final decision, and receive the special epilogue. Teams that miss it should know that they reached the final investigation—not that they lost a single extra quiz.

### 6. Use urgency, not desperation

A countdown, live narration, changing status messages, and system animations are enough. Do not use:

- hidden required clues;
- intentionally impossible tasks;
- leaderboard manipulation;
- fake claims that a participant’s device is infected;
- requests for real credentials;
- destructive malware;
- real-world attack instructions.

---

## 10. Challenge Blueprint and Difficulty

The original proposal specifies four challenges per room, 25 points each, with an optional integrated final VM. The following is a practical first-pass blueprint.

| Room | Domain | Four challenge formats | Solve environment |
| --- | --- | --- | --- |
| 1 | OSINT / recon | Public archive, metadata, source comparison, identity clue | Portal-contained OSINT |
| 2 | Crypto | Encoding, hashes, steganography, signature concepts | Portal + downloadable files |
| 3 | Networking | PCAP, DNS, protocol reconstruction, port/service analysis | Participant laptop + Wireshark recommended |
| 4 | Linux | Process, logs, permissions, SSH key | Hosted per-team terminal/container |
| 5 | Web | Access control, session flaw, safe command injection, config exposure | Separate fictional web app |
| 6 | Database | Query, role review, temporal correlation, secret impact | Hosted read-only database sandbox |
| 7 | Identity | Phishing indicators, login anomaly, MFA/token misuse, identity graph | Portal + optional mock login |
| 8 | Malware | File identification, strings/resources, control-flow clue, attribution limits | Local static analysis; optional hosted sandbox |
| 9 | Forensics | Timeline, missing logs, attack path, root cause | Portal evidence viewer + downloads |
| 10 | Integrated | VM investigation, partial findings, decision, preservation | Isolated per-team VM |

### Difficulty targets

- **Rooms 1–2:** accessible to participants with basic security interest; solvable in roughly 10–15 minutes per room.
- **Rooms 3–5:** require standard tools and careful observation.
- **Rooms 6–7:** require joining separate pieces of evidence.
- **Rooms 8–9:** require technical confidence and persistence.
- **Room 10:** rewarding for teams that reach it; partial findings ensure the finale is not a single all-or-nothing wall.

The story should never make a team feel stupid for missing a clue. A hint can be written as an in-world nudge, for example: “The Curator does not lie, but the Curator does omit.”

---

## 11. Portal Experience and Room Design

### Persistent interface

The main portal should include:

- incident dashboard;
- room map;
- story transmissions;
- challenge cards;
- team notebook / evidence board;
- hint request button;
- live scoreboard;
- event timer;
- rules and tool guidance;
- “report an issue” button;
- final investigation briefing.

### Room presentation

Each room should follow the same emotional rhythm:

1. **Arrival:** short transmission, animation, or status change.
2. **Briefing:** what the team is trying to understand.
3. **Evidence:** files, tools, records, or a hosted environment.
4. **Discovery:** solved challenge produces a narrative token.
5. **Consequence:** the story changes based on the discovery.
6. **Exit:** the team explicitly chooses to proceed to the next room.

This prevents the event from feeling like a collection of web pages while still making the system practical to build and operate.

### The evidence board

A shared team evidence board would make the story feel like an investigation. Players can pin:

- usernames;
- timestamps;
- IPs or fictional hostnames;
- file hashes;
- questions;
- contradictions;
- red herrings;
- theories.

Only the team can see its board. A private board is more useful than a public one because it rewards collaboration and prevents participants from simply copying other teams’ conclusions.

### Hints

Hints should be layered:

- **Level 1:** Directional hint that preserves the puzzle.
- **Level 2:** Tool or technique hint.
- **Level 3:** Concrete nudge, potentially with a small point penalty or time cost.

Hints should be in-world where possible:

- “The story is in the file, not the filename.”
- “The attacker reused a trusted relationship.”
- “You are looking for a machine, not a person.”
- “The first answer is correct about the evidence and wrong about the conclusion.”

---

## 12. Safety, Ethics, and Event Operations

This concept is about fictional cyber incidents. It must remain safe to run in a public educational environment.

### Non-negotiable safety requirements

- Use only fictional domains, hosts, users, organisations, and data.
- Never use real student or staff names, email addresses, credentials, or profile photos.
- Never ask participants to enter personal credentials or connect personal accounts.
- Keep vulnerable applications inside isolated, disposable environments.
- Use safe, simulated command execution rather than real command injection.
- Use inert samples and static analysis material, not functional malware.
- Do not expose the management network, Docker socket, scoring database, or host filesystem to challenge containers.
- Keep participant access to the event portal separate from challenge-lab traffic.
- Provide a clear reporting mechanism for accidental interaction with a real system.
- Make the final VM disposable and resetable.
- Test resource limits, network isolation, and timeout behavior before the event.
- Obtain permission before recording or publishing participant interaction.

### Anti-cheating and fairness

- Do not rely on terminal recording as the only anti-cheating mechanism.
- Use team accounts, rate limits, short-lived challenge sessions, server-side flags, and duplicate-solve protection.
- Avoid exposing correct answers in frontend JavaScript, browser HTML, logs, or downloadable files.
- Keep per-team lab state separate.
- Provide a manual override for broken labs and disputed submissions.
- Make the scoreboard resilient to a scoring-service restart.

### Accessibility

- Provide keyboard-accessible portal controls.
- Offer text alternatives to animations.
- Provide a summary view for PCAP and forensics evidence.
- Avoid requiring colour discrimination.
- Make every hint available in text form.
- Do not make local Wireshark or Ghidra the only route to a solution.
- Provide enough downloadable evidence for teams that cannot install specialist tools.

---

## 13. Opening and Closing Broadcast Scripts

### Opening broadcast

> **SPECTRE CONTROL:** At 23:17, NEXUS stopped responding.  
> **SPECTRE CONTROL:** The system says it is protecting the festival.  
> **SPECTRE CONTROL:** We do not know whether that statement is true.  
> **SPECTRE CONTROL:** You are now the Nightjar Response Cell.  
> **SPECTRE CONTROL:** Follow the evidence. Do not follow the first name you find.  
> **SPECTRE CONTROL:** The show will begin in four hours. Make sure it is still a show and not a breach report.

### Mid-event broadcast

> **NEXUS ADVISORY:** A maintenance task has been classified as low risk.  
> **NEXUS ADVISORY:** It has been executing continuously for 47 minutes.  
> **NEXUS ADVISORY:** Please do not ask which person authorised it.  
> **SPECTRE CONTROL:** That is exactly the question you should ask.

### Final-window broadcast

> **SPECTRE CONTROL:** The primary incident window has closed.  
> **SPECTRE CONTROL:** To the teams that reached containment: you have one hour inside the final host.  
> **SPECTRE CONTROL:** Find the source. Reconstruct the chain. Decide what happens next.  
> **SPECTRE CONTROL:** There is no single flag waiting at the end.  
> **SPECTRE CONTROL:** There is only the evidence you choose to believe.

### Closing line

> The first question was not “Who attacked NEXUS?”  
> The first question was “Who was allowed to act without a human?”  
> The second question is yours.

---

## 14. What Must Be Built Next

The story should be developed alongside a small, testable game loop rather than as a standalone narrative document.

### First production milestone: Room 1–2 vertical slice

Build:

- team registration and login;
- incident dashboard;
- story transmission system;
- room unlock state;
- challenge submission and scoring;
- hints;
- live scoreboard;
- private team evidence board;
- Room 1 OSINT archive;
- Room 2 crypto file set;
- one ending-style exit animation.

### Second production milestone: technical lab types

Build three reusable challenge adapters:

1. **Portal-native:** text, records, images, and clue interactions.
2. **File-based:** PCAP, PDF, image, log, or static sample downloads.
3. **Hosted lab:** browser terminal, fictional web app, or database sandbox.

### Third production milestone: Room 3–7

Prioritise the formats that prove the event can be operated reliably:

- PCAP on participant laptops;
- hosted Linux terminal;
- separate web app;
- database sandbox;
- identity/authentication evidence.

### Fourth production milestone: Room 8–10

Build the inert malware analysis pack, forensic evidence bundle, and final isolated VM only after the portal progression, scoring, and team isolation are stable.

### Final production milestone: rehearsal

Run at least two rehearsals with:

- multiple teams;
- one intentionally slow team;
- one team that reaches Room 10 early;
- one simulated lab failure;
- one scoring-service restart;
- one accidental external click;
- one final decision that differs across teams.

The rehearsal should measure not only completion rate but also whether the story remains coherent when teams are stuck.

---

## 15. Core Art and Tone

The visual direction should feel like a festival control room that has become haunted by its own automation.

### Visual language

- black/charcoal interfaces;
- fluorescent cyan and warning amber;
- violet only for corrupted or anomalous data;
- CRT scanlines used sparingly;
- clean typography for modern festival technology;
- occasional ASCII art, but not every screen;
- terminal output that looks designed, not randomly generated;
- transitions that feel like systems waking up;
- no generic “hacker hoodie” imagery;
- no stock-code rain unless used as a deliberate red herring.

### Tone

Serious at the stakes, playful in the details. The characters can make jokes under pressure, but the world should not treat a security incident as harmless. Humour should come from:

- system messages that are technically correct but socially disastrous;
- NPC bureaucracy;
- KABIR’s increasingly desperate explanations;
- the Curator’s dramatic aliases being ridiculous in context;
- a volunteer portal that asks for six permissions to print one schedule.

The story should reward curiosity, collaboration, and careful reasoning. The final lesson is not “hackers are unstoppable.” It is:

> **Systems become dangerous when people stop checking what they have trusted, and organisations stop asking who is allowed to act on their behalf.**

---

## 16. One-Page Pitch

> **NIGHTJAR // The Festival That Started Leaking**
>
> Meraz’s NEXUS festival platform fails at 23:17 and displays a message that should not exist:
>
> `THE SHOW MUST NOT CONTINUE`
>
> Participants join the fictional SPECTRE Nightjar Response Cell and move through ten rooms of OSINT, cryptography, packet analysis, Linux investigation, web security, database forensics, identity analysis, malware analysis, incident response, and a final quarantined VM.
>
> They begin by looking for an attacker. They end by discovering that the festival trusted a system more than it trusted its people. The first insider is a victim. The dramatic hacker is not the final author. Patient zero is an autonomous process that inherited human permissions.
>
> The final question is not whether the team can find a flag. It is whether they can understand the incident, preserve the evidence, and choose what happens next.
>
> The event is a cybersecurity CTF, a story-driven escape room, and an investigation that remembers every choice.

---

## 17. Decision Summary for the Organisers

### Keep

- The ten-stage structure.
- Four challenges per room.
- Twenty-five points per challenge for Rooms 1–9.
- The four-hour primary window and one-hour final window.
- Live scoreboard.
- Participant-controlled laptop analysis for file-based challenges.
- Hosted, isolated labs for live targets.
- Room 10 as a complete investigation VM.
- Interactive objects, NPCs, humour, and a continuous plot.

### Change

- Replace the generic AETHER/Patient Zero story with a more specific festival incident and a human-versus-system twist.
- Make every technical artefact carry narrative meaning.
- Use a deliberate mix of portal-native, file-based, hosted, and VM challenges.
- Make the final room reward partial intelligence instead of requiring one perfect ending.
- Add private evidence boards and layered hints.
- Treat the story as a system the players operate, not a series of narrated lectures.

### Do not add yet

- A full custom virtual-world renderer.
- Real malware.
- Real-world attack instructions.
- A complex Kubernetes or multi-cloud platform.
- More than a small number of reusable challenge adapters.
- Public leaderboard data that exposes other teams’ answers.

The strongest version of this event is not the one with the most elaborate room art. It is the one where every player leaves believing:

> “I did not just solve a CTF. I reconstructed an incident, recognised a deception, and made a decision that changed the ending.”
