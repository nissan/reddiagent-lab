# v0.2.0-beta Publish Runbook

Maintainer checklist for shipping the beta release and its announcement wave.
Every step before "Announce" is an owner-only action — agents have prepared the
artifacts but cannot press these buttons.

## 1. Pre-flight (verify, ~5 min)

- [ ] Repo visibility: confirm `nissan/reddiagent-lab` is **public** (Settings → General → Danger Zone). The STATUS log has carried "flip repo public" as owed since 2026-07-29.
- [ ] Bundle integrity: `https://agent-protocol.reddi.tech/downloads/adl-v0.2.0-beta.zip` downloads and unzips; spec + schema inside match `specs/ADL-v0.2.md` / `specs/ADL-v0.2.schema.json` on `main`.
- [ ] Issue links resolve publicly: [#389](https://github.com/nissan/reddiagent-lab/issues/389), [#440](https://github.com/nissan/reddiagent-lab/issues/440), [#441](https://github.com/nissan/reddiagent-lab/issues/441).
- [ ] Reddi Arena live check: https://reddi-arena-production.up.railway.app loads; waitlist form submits.

## 2. Publish the GitHub release

- [ ] Open the existing **draft** release "ReddiAgent ADL v0.2.0-beta" (tag `v0.2.0-beta`).
- [ ] **Replace the draft body** with the contents of `docs/release/ADL-v0.2.0-beta-RELEASE-NOTES.md` (below the `---` separator). The draft's `reddinft/…` links are wrong; the notes file fixes them and adds the Arena + v0.3 sections.
- [ ] Confirm the tag targets current `main`.
- [ ] Optionally attach `adl-v0.2.0-beta.zip` as a release asset (same file the site serves).
- [ ] Mark as **pre-release** (it is a beta), then **Publish**.

## 3. Merge the announcement PRs (in order)

- [ ] Lab repo PR (this branch): release notes, runbook, blog post, social pack.
- [ ] Protocol repo PR: `/updates` entry announcing the release + Arena early access, and the `reddinft→nissan` link fixes on `/spec` and `/feedback`. **Merge only after step 2** — the live site must not announce an unpublished release.
- [ ] Verify https://agent-protocol.reddi.tech/updates shows the 2026-08-16 entry and `/spec` + `/feedback` links resolve.

## 4. Announce

Post from `docs/announcements/2026-08-16-social-media-pack.md`, in order:

- [ ] X/Twitter thread (pin it), or the single-post variant if a thread is too much.
- [ ] LinkedIn post.
- [ ] Discord/community announcement.
- [ ] Email/newsletter blurb to any existing contact list (incl. Superteam AU channel if appropriate).

## 5. Aftercare (first week)

- [ ] Triage incoming `open-spec-review` issues within 48h; label v0.3 candidates.
- [ ] Watch the Arena waitlist count; greet early-access cohort with the quickstart (`QUICKSTART.md`, `tutorials/vault-duel.md`).
- [ ] Submit the Superteam AU tranche-2 form (owed since 2026-07-29, milestone #406) — the published release satisfies its evidence link.
- [ ] Log the publish in STATUS.md (release URL, date, first-week feedback count).
