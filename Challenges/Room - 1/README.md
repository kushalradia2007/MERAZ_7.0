# Room 1 — The Empty Signal

## Domain: OSINT, Reconnaissance, Source Verification

---

## 🔊 Opening Transmission

> **INCIDENT LOG // 23:17 IST**
>
> *"NEXUS is offline. We have no breach, no attacker, and no reason for this message. Find the first person who knew it was coming."*
>
> — **Commander Ila Sen**, Incident Commander

---

## Story Context

At 23:17, every display connected to the Meraz NEXUS festival platform went dark. When they came back — seven seconds later — the screens showed a message that no administrator had written:

```
THE SHOW MUST NOT CONTINUE
WE ARE NOT THE FIRST
```

The festival's digital noticeboard has been replaced. Every page looks official. Every page was modified before anyone on the SPECTRE team knew something was wrong.

Your mission: Inspect the public-facing festival pages, their metadata, and the digital trail they left behind. **Someone prepared for this breach months in advance.** Find them.

---

## Room Mood

A public-facing digital noticeboard where every official-looking page has been replaced by a calm, unsettling countdown. The pages look like festival information, but their metadata and wording reveal they were prepared months before the incident. The atmosphere is one of quiet wrongness — everything *looks* normal, but nothing *is*.

---

## Evidence Files

| File | Description |
|------|-------------|
| `evidence/meraz_festival_hub.html` | The official Meraz NEXUS festival hub page — contains a hidden page link |
| `evidence/aether_07.html` | A page that should not exist on the festival portal |
| `evidence/meraz_schedule_2026.pdf` | The downloadable festival schedule PDF (contains hidden metadata) |
| `evidence/nexus_banner_final.png` | Official festival banner image with embedded EXIF data |
| `evidence/nexus_official_page.html` | The real NEXUS system status page |
| `evidence/nexus_mirror_page.html` | A convincing mirror/impersonation of the official page |
| `evidence/osint_archive/` | A contained social media / profile archive for identity research |

---

## Challenge 1.1 — The Page That Should Not Exist

**Points:** 25

**Technical Concept:** OSINT and public-source verification.

**Briefing:**
> The Meraz public portal hosts the usual festival pages — schedule, venue map, sponsor list, volunteer info. But Rhea's automated audit flagged a page that was never approved by the festival committee. It lives at a path that doesn't match anything in the content management system. Find it.

**Task:** Inspect the Meraz festival hub page (`meraz_festival_hub.html`) and identify the hidden page. Examine its contents. The page title, creation date, and a specific phrase inside it are your evidence.

**Flag:** `NIGHTJAR{aether_07_nothing_stays_local}`

**Narrative Reward:** The hidden page is titled `AETHER/07`. It contains a single sentence that will later appear in MIRA-7's configuration: *"Nothing stays local."* This phrase was planted months before the incident — proof that someone was preparing.

**Hints:**
- **Level 1:** "Not every link is visible. The page exists, but it was never meant to be found through navigation."
- **Level 2:** "Inspect the HTML source of the festival hub. Look for commented-out links or hidden elements."
- **Level 3:** "Search the page source for 'aether'. The hidden link points to a page with a message from the future."

---

## Challenge 1.2 — A Name in the Metadata

**Points:** 25

**Technical Concept:** File metadata, EXIF data, document properties, and version-control leaks.

**Briefing:**
> The festival schedule was distributed as a PDF, and the banner image was uploaded to every NEXUS-connected display two weeks before the event. These files were approved by the organising committee — but the committee didn't create them. Someone else did. Their name is still in the metadata.

**Task:** Download and examine the festival schedule PDF (`meraz_schedule_2026.pdf`) and the banner image (`nexus_banner_final.png`). Extract the hidden author name, creator tool, or organization from their metadata fields.

**Flag:** `NIGHTJAR{parallax_systems_aman}` (also accepted: `NIGHTJAR{parallax_systems_aman_v}`). Format: `NIGHTJAR{PARALLAX_SYSTEMS_<author>}`

**Narrative Reward:** The PDF's author field reads `Aman V. // Parallax Systems`. The banner image's EXIF data contains GPS coordinates pointing to a fictional research lab and a creator tool called `AetherForge v2.1`. **Parallax Systems** is a nonexistent research group — but the name will appear again in Room 8 when the malware sample is analysed.

**Hints:**
- **Level 1:** "The story is in the file, not the filename. Look deeper than the content."
- **Level 2:** "Use an EXIF viewer on the image. Use a PDF metadata reader on the schedule. Look for Author, Creator, and Producer fields."
- **Level 3:** "The PDF author contains a name and an organisation separated by '//'. The organisation is not real."

---

## Challenge 1.3 — The False Official

**Points:** 25

**Technical Concept:** Source validation, impersonation detection, and domain/name similarity.

**Briefing:**
> Two versions of the NEXUS status page exist. One is the real system page maintained by Rhea's engineering team. The other appeared three days ago and has been silently redirecting volunteer queries. They look almost identical. Almost.

**Task:** Compare `nexus_official_page.html` with `nexus_mirror_page.html`. Identify the specific discrepancies that reveal which page is the impersonation: domain inconsistencies, certificate differences, subtle text changes, and a hidden redirect.

**Flag:** `NIGHTJAR{nexus-meraz.festival.in.net}`

**Narrative Reward:** The mirror was registered under the domain `nexus-meraz.festival.in.net` — close enough to look legitimate, different enough to be a separate server entirely. The mirror's SSL certificate was issued by `Parallax CA` (not a real certificate authority). The page also contains a 1-pixel tracking beacon that reports back to an external endpoint. This is the Curator's reconnaissance infrastructure — built to watch who visits before the attack begins.

**Hints:**
- **Level 1:** "Official pages and their copies differ in small but critical ways. Compare everything, not just the text."
- **Level 2:** "Check the page's `<meta>` tags, link `href` values, and any embedded scripts. One page has something the other doesn't."
- **Level 3:** "Look at the domain in the mirror page's `<base>` tag and SSL certificate comment. The domain ends in `.in.net`, not `.in`."

---

## Challenge 1.4 — The Quiet Profile

**Points:** 25

**Technical Concept:** Cross-referencing fictional usernames, timestamps, public posts, and identity clues.

**Briefing:**
> The Curator didn't appear from nowhere. Somewhere in the festival's digital footprint — the volunteer forum, the tech blog, the contributor credits — there is a profile that was created months before the incident, posted exactly once, and has been watching ever since. Find the operator's public handle.

**Task:** Search the contained OSINT archive (`osint_archive/`). Cross-reference usernames, creation dates, posting patterns, and profile details across the provided social profiles. Identify the account that belongs to the anonymous operator behind the breach preparation.

**Flag:** `NIGHTJAR{curator_404}`

**Narrative Reward:** The profile `curator_404` was created on the Meraz volunteer forum exactly 147 days before the incident. It posted a single message: *"Looking forward to the show. I hope the systems hold."* The account's avatar is a nightjar bird silhouette. The email domain on the profile points back to `parallax-sys.net`. This is the Curator — **Aman Vyas** — who has been watching the festival's infrastructure since before anyone knew there was something to watch.

**Hints:**
- **Level 1:** "The operator has been here longer than you think. Look for accounts that are old but silent."
- **Level 2:** "Cross-reference profile creation dates with posting activity. The quietest account with the oldest date is suspicious."
- **Level 3:** "The handle contains 'curator' and a number. Check the forum profiles for a nightjar bird avatar."

---

## Room Transition

After solving Challenge 1.4, the following transmission appears:

> **NEXUS RELAY LOG // 23:41 IST**
>
> `curator_404` has sent a direct message to **KABIR "KITE" MEHRA**, the Festival Technical Lead:
>
> *"Kite — restore the old route. The one Rhea disabled. You know which one. The festival depends on it."*
>
> The portal displays a cipher capsule — an encrypted package attached to the message. It cannot be opened here.
>
> **Proceed to Room 2 to decode the capsule.**

---

## Admin Notes

- All flags follow the format `NIGHTJAR{...}` with lowercase, underscores, and no spaces.
- This room should be solvable in 10–15 minutes by participants with basic security knowledge.
- No external tools are strictly required — all evidence is inspectable in a browser and with built-in OS tools.
- The OSINT archive is fully self-contained. No real internet searches should be needed.
- All organisations, people, domains, and data are **entirely fictional**.
