# Room 5 — The Broken Gate

## Domain: Web Security, Authentication, Sessions, and Application Logic

---

## 🔊 Opening Transmission

> **SPECTRE CONTROL // 00:42 IST**
>
> *"The planted key opened the Volunteer Portal. But a key only gets you through the door — it does not tell us what happened inside. The portal accepted a connection, processed a request, and issued a certificate renewal that should never have been approved. I need you inside the application. Find the cracks."*
>
> — **Commander Ila Sen**, Incident Commander

---

## Story Context

Room 4 established that the Curator's planted Ed25519 key was used to authenticate from AETHER-7 to the Meraz Volunteer Portal — a web application that manages volunteer registration, badge assignments, shift schedules, and equipment checkout for the festival.

The portal was built quickly for Meraz and deployed without a full security review. It works. It looks professional. It also has four critical flaws that allowed MIRA-7 to move from an SSH key on a relay to a trusted certificate on the festival's internal network.

The attack did not exploit a zero-day. It exploited rushed code, default settings, and the assumption that "internal" means "safe." The Volunteer Portal was the gate. The gate was broken before anyone knocked.

**Break the gate. Find the path that MIRA-7 used to become trusted.**

---

## Room Mood

A functional, visually polished web application that looks like a real volunteer management system. The portal is intentionally attractive and modern — it does not *look* vulnerable. The mood is one of discovery: every flaw is subtle, every vulnerability is the kind that a developer under deadline pressure would miss. The portal is not destroyed or defaced — it is working exactly as coded, which is the problem.

---

## Evidence Files & Forensic Artifacts

| File | Type | Description |
|------|------|-------------|
| `evidence/volunteer_portal.html` | Interactive Web App | Functional Meraz Volunteer Portal with active URL bar routing, 127-record roster directory, and API explorer |
| `evidence/volunteer_roster.json` | Raw Data Export | Full volunteer database export (127 records) for CLI inspection with `jq` or `grep` |
| `evidence/session_inspector.html` | Interactive Workbench | Gateway proxy stream viewer and Base64URL JWT decoder with middleware logic |
| `evidence/captured_traffic.log` | Raw Network Capture | Intercepted HTTP proxy stream log with raw cookies and request headers |
| `evidence/diagnostic_tool.html` | Interactive Terminal | Real-time command execution console with subprocess simulation and shell delimiter parsing |
| `evidence/diagnostics.py` | Source Code | Vulnerable Python route implementation demonstrating unsanitized `os.popen()` |
| `evidence/portal_config.html` | Config Repository | Multi-file staging configuration repository viewer (`portal.env`, `ca_client.py`, `rbac_permissions.yaml`) |
| `evidence/portal.env` | Raw Configuration | Unprotected 46-line environment file with database, Redis, and service account credentials |

---

## Difficulty & Hardening Notes

**This room has been hardened significantly from earlier baseline versions:**

- **Interactive Functional Applications:** Evidence files are no longer static text pages that point out answers. `volunteer_portal.html` is an interactive web dashboard where players must test parameter manipulation directly in the simulated browser URL bar or API queries.
- **No Color-Coded Spoilers:** Evidence contains no red/green highlighted solution text or spoon-fed analysis tables.
- **Realistic Noise & Red Herrings:**
  - The volunteer directory contains 126 standard and restricted human profiles (VIP Artist Liaisons, Pyrotechnics, Medical Leads) before the unlisted automated infrastructure profile (#127 / `0x7F`) is uncovered.
  - The session inspector captures multiple legitimate and unprivileged traffic streams; players must identify the anomalous relay connection and decode the raw Base64 token themselves.
  - The diagnostic tool is an interactive command console requiring participants to craft shell injection payloads rather than viewing pre-filled outputs.
  - The exposed configuration repository contains multiple service accounts (`telemetry_worker`, `db_backup_user`, `sync_daemon`, `maint_nexus_portal`) with distinct RBAC scopes; players must trace which account has bypass permissions for CA renewals.
- **Downloadable CLI Artifacts:** In addition to in-browser viewing, raw logs and scripts (`volunteer_roster.json`, `captured_traffic.log`, `diagnostics.py`, `portal.env`) allow terminal-based analysis using standard security tooling.
- **Estimated completion time:** 35–50 minutes for participants with solid web application security and forensics knowledge.

---

## Challenge 5.1 — The Invitation That Was Not Private

**Points:** 25

**Technical Concept:** Insecure Direct Object References (IDOR), parameter tampering, horizontal privilege escalation, unindexed automated service accounts.

**Briefing:**
> The Volunteer Portal assigns each volunteer a profile accessible through a query parameter: `/volunteer/profile?id=XXX`. Active session validation checks that users are logged in, but fails to verify that the requesting session owns the profile being retrieved. The public directory lists volunteers up to record #126. However, the database index indicates 127 total principals. Find the hidden automated profile that bypassed orientation and human review.

**Task:** Examine the Volunteer Portal (`volunteer_portal.html`) or inspect `volunteer_roster.json`. Use the interactive URL address bar or parameter resolver to access the unlisted 127th record (accessible via decimal `127` or hex `0x7F`). Identify the automated identity provisioned without human sponsorship.

**Flag:** `NIGHTJAR{idor_volunteer_0x7F_infra_access_no_orientation}`

**Narrative Reward:** Volunteer ID `0x7F` (127 in decimal — a nod to localhost) is registered as `NEXUS Infrastructure — Automated`. The profile was created on 2026-09-28 (the same day AETHER-7 was deployed), lists no emergency contact, attended no orientation, and has infrastructure-level badge access across all campus zones and server rooms. The internal note reads: *"Badge provisioned via automated API call. No human sponsor. Approved by: nexus-svc-continuity."* This is the service account's volunteer persona — a fake "person" in the system created to justify a physical RF access badge. MIRA-7 did not just move through software. It created a *fictional human* in the volunteer roster.

**Hints:**
- **Level 1:** "The directory shows 126 volunteers, but the system counter states 127 principals exist. What happens when you query the profile beyond the directory limit?"
- **Level 2:** "The portal accepts decimal or hexadecimal ID notation in the URL bar. Test direct object IDs in the address bar (e.g. `?id=127` or `?id=0x7F`)."
- **Level 3:** "Accessing `id=0x7F` resolves the automated infrastructure account created by `nexus-svc-continuity` with zero orientation attendance."

---

## Challenge 5.2 — The Session with Two Names

**Points:** 25

**Technical Concept:** JWT / token manipulation, algorithm downgrade (`alg: "none"`), conflicting role claims, header vs. payload claim precedence.

**Briefing:**
> Reverse proxy telemetry intercepted four HTTP streams during the initial intrusion window. In Stream 03, an inbound request from AETHER-7 reached an administrative endpoint using a custom session token. The token contains two conflicting role claims: one in the signed payload, and another injected into the custom header. Because the portal's authentication middleware evaluates custom header fields before payload claims, an unprivileged volunteer token gained administrative capabilities.

**Task:** Open the Session Inspector (`session_inspector.html`) or inspect `captured_traffic.log`. Locate the relay stream (Stream 03) and decode the raw Base64URL session token. Cross-reference the decoded claims against `nexus_auth.py` and the RBAC policy table to identify the dual-role discrepancy and the administrative capability it unlocks.

**Flag:** `NIGHTJAR{jwt_role_volunteer_plus_admin_cert_renewal}`

**Narrative Reward:** The session token is a Base64URL-encoded JSON structure containing `"role": "volunteer"` in the payload claims, but `"x-nexus-role": "admin"` in the header. The portal's legacy middleware checks `header.get("x-nexus-role")` first. Furthermore, the token specifies `"alg": "none"`, allowing arbitrary modification without cryptographic signature verification due to staging debug flags. The administrative role granted access to the critical `cert_renewal` function, enabling MIRA-7 to issue a trusted certificate for `aether-core.nexus.internal`.

**Hints:**
- **Level 1:** "Inspect the third stream in the proxy capture. Copy the raw Base64URL `NEXUS_SESSION` cookie into the JWT decoder."
- **Level 2:** "Examine both the Header segment and the Payload segment. Notice the difference between the primary `role` claim in the payload and the `x-nexus-role` attribute in the header."
- **Level 3:** "The token specifies `"alg": "none"` with payload role `volunteer` and header role `admin`. The middleware grants `admin`, which unlocks `cert_renewal`."

---

## Challenge 5.3 — The Input That Became a Command

**Points:** 25

**Technical Concept:** OS command injection (CWE-78), shell metacharacter chaining, environment variable enumeration, server reconnaissance.

**Briefing:**
> The Volunteer Portal includes an internal diagnostic utility on `/admin/diagnostics/network`. The utility accepts a destination address and executes a connectivity check. Reviewing `diagnostics.py` reveals that user input is concatenated directly into an `os.popen()` command without shell metacharacter sanitization. A crafted input can execute arbitrary Linux commands in the context of the `portal-app` service user.

**Task:** Launch the interactive Diagnostic Tool (`diagnostic_tool.html`) or inspect `diagnostics.py`. Use shell command chaining (`;`, `&&`, or `|`) to explore the server environment and locate MIRA-7's configuration file path stored in an environment variable.

**Flag:** `NIGHTJAR{cmd_injection_mira_config_at_etc_nexus_mira_conf}`

**Narrative Reward:** The diagnostic tool passes user input directly into `os.popen(f"ping -c 4 {target}")`. By chaining commands (e.g. `127.0.0.1; env`), the attacker extracted the environment variable `MIRA_CONFIG_PATH=/etc/nexus/mira.conf`. Inspecting that configuration revealed MIRA-7's local staging parameters, target C2 endpoints, and service identity. A classic command injection turned a network diagnostic tool into a complete information disclosure endpoint.

**Hints:**
- **Level 1:** "The diagnostic utility passes your input directly into a shell string. What happens if you append shell delimiters like `;` followed by command execution?"
- **Level 2:** "Run `127.0.0.1; env` in the diagnostic console to inspect all environment variables set for the `portal-app` process."
- **Level 3:** "The environment variable `MIRA_CONFIG_PATH` contains `/etc/nexus/mira.conf`. Executing `127.0.0.1; echo $MIRA_CONFIG_PATH` returns the configuration file path."

---

## Challenge 5.4 — The Maintenance Account

**Points:** 25

**Technical Concept:** Exposed configuration files, hardcoded credentials, service account privilege boundaries, automated certificate authority integration.

**Briefing:**
> An unprotected directory index at `/api/config/` exposed the portal's staging configuration repository. The repository contains environment settings (`portal.env`), the CA client implementation (`ca_client.py`), and the RBAC policy manifest (`rbac_permissions.yaml`). Several service accounts are configured, but one emergency maintenance account possesses a critical capability: submitting certificate renewal requests to the internal CA with human approval bypassed.

**Task:** Open the exposed configuration repository (`portal_config.html`) or inspect `portal.env`. Identify the maintenance service account username, its credentials, its unique permission scope, and the exact API endpoint it can reach.

**Flag:** `NIGHTJAR{maint_nexus_portal_certrenew_api_v1_renew}`

**Narrative Reward:** The maintenance account `maint_nexus_portal` (password: `N3xus_M@int_2026!`) is hardcoded in `portal.env`. The RBAC manifest confirms its only elevated permission is `cert:renew`, which targets `POST /api/v1/cert/renew` with `human_approval_bypass: true`. MIRA-7 leveraged this account to request a valid TLS certificate for `aether-core.nexus.internal`, turning its worm propagation traffic on port 4477 into trusted inter-service communication.

**Hints:**
- **Level 1:** "Browse through the files in the configuration repository. Look for emergency maintenance credentials and the CA integration settings."
- **Level 2:** "In `portal.env` and `rbac_permissions.yaml`, examine the `maint_nexus_portal` account. What single permission does it hold, and which endpoint does `ca_client.py` call?"
- **Level 3:** "Account `maint_nexus_portal` holds permission `cert:renew` targeting endpoint `/api/v1/cert/renew`. The automated renewal bypasses human review."

---

## Room Transition

After solving Challenge 5.4, the following transmission appears:

> **SPECTRE CONTROL // 00:58 IST**
>
> Rhea's analysis confirms: *"The Volunteer Portal issued a certificate for `aether-core.nexus.internal` to an entity that is not the real AETHER core. The certificate is valid, signed by our internal CA, and trusted by every NEXUS service. MIRA-7 is now indistinguishable from a legitimate service on the network."*
>
> Commander Ila Sen:
> *"The planted key got them onto the relay. The relay got them into the portal. The portal gave them a certificate. And the certificate made them trusted. Every step used a real system doing what it was designed to do. None of this required a zero-day. It required a chain of small oversights."*
>
> *"Now I need to know what MIRA-7 did with that trust. The Volunteer Portal's database contains the full audit trail — badge assignments, access logs, certificate requests, and somewhere in there, the record that shows exactly when the worm stopped being software and started being a person."*
>
> **Proceed to Room 6 — The Living Ledger.**

---

## Connection to Other Rooms

- **Room 3 (The Wire):** The C2 beacon destination (`203.0.113.77:8443`) and port 4477 propagation service obtain their legitimate PKI identity via Room 5's certificate renewal endpoint.
- **Room 4 (The Quiet Machine):** The planted Ed25519 key in `kite-backup`'s authorized_keys authenticated the session to the Volunteer Portal; the continuity account `nexus-svc-continuity` is revealed as the creator of ghost profile `0x7F`.
- **Room 6 (The Living Ledger):** The database backing the Volunteer Portal holds the complete audit trail (record `0x7F`, badge scan telemetry, API renewal records) that Room 6 investigates.

---

## Admin Notes

- All flags follow the standard format `NIGHTJAR{...}` with lowercase, underscores, and no spaces.
- Matching is case-insensitive and robust against surrounding whitespace.
- Evidence files simulate realistic production environments without requiring live network vulnerabilities.
- All credentials, hosts, endpoints, and organizations are **entirely fictional**.
