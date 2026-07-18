# Public Demo Walkthrough Video

Issue: #271  
Public demo with draft video: https://present-hearth-vhey.here.now/  
Initial static-only demo: https://poppy-rafter-79h2.here.now/  
Target length: 75-90 seconds  
Primary audience: builders, reviewers, and early users evaluating what ReddiAgent can do today
Verified public routes: `/`, `/media/reddiagent-demo-walkthrough.mp4`, `/builder-report.html`, and `/reports/BETA-RELEASE-VERIFICATION-CLI-REPORT.md` returned HTTP 200 on 2026-07-19 04:36 AEST.

## Intent

Create a short public walkthrough that helps a viewer understand the current ReddiAgent static demo without a live call. The video should show the actual published demo, explain the use cases covered by the current ADL/export work, and make the boundary clear: this is static evidence and local dry-run tooling, not a live runtime or mainnet activation.

Core line:

> ReddiAgent does not just describe an agent; it tells you what can be exported, what must stay review-only, and what is blocked before anything risky runs.

## Non-Goals And Guardrails

- Do not claim live agent runtime activation.
- Do not claim Docker, Surfpool, or Coolify were started for the demo.
- Do not claim provider/model product calls, live MCP invocation, credential access, payment/wallet/facilitator/settlement access, devnet/mainnet use, package publishing, or production gateway mutation.
- Do not use paid TTS, paid video generation, or paid model calls unless Nissan explicitly approves a later production pass.
- Do not expose secrets, private operator state, internal Telegram metadata, or local filesystem paths in the public video.

## Variant

This first pass is a single walkthrough variant. A review draft is already embedded in the video-enabled public demo; it is intentionally still-based and uses local macOS TTS fallback because the shared Kokoro helper hit a local CPU API mismatch during this run.

- Label: `A`
- Style: guided product walkthrough
- Duration: 75-90 seconds
- Format: 16:9, 1920x1080, H.264/AAC MP4
- Voice: local Kokoro TTS, agent profile `sara` or `loki`
- Music: optional low-volume local/free bed only if already available; otherwise narration-only

Draft output evidence:

- Public page: https://present-hearth-vhey.here.now/
- MP4: https://present-hearth-vhey.here.now/media/reddiagent-demo-walkthrough.mp4
- Local build path: `/tmp/reddiagent-demo-video/final/reddiagent-demo-walkthrough.mp4`
- QC: H.264 video, AAC audio, 1920x1080, 30fps, 68 seconds, 2.7 MB; `ffprobe`, `silencedetect`, and `blackdetect` completed with no reported silence/black findings in the summary grep.

## Scene Plan

| Scene | Time | Screen | Action | Caption | Narration |
| --- | ---: | --- | --- | --- | --- |
| 1. Evidence-First Builder | 0:00-0:10 | Public demo landing page | Load `https://poppy-rafter-79h2.here.now/`; hold on title and guardrail chips, then slow scroll into coverage cards. | Static review surface, no live runtime. | "This is the public static ReddiAgent demo: no runtime activation, no provider calls, no MCP invocation, no payments, no mainnet. It is a reviewable snapshot of the spec and export layer." |
| 2. Three ADL Examples | 0:10-0:25 | Prosumer Builder static export | Scroll through `simple-research-helper`, `source-checker`, and `paid-specialist-researcher` rows. | One ADL source, many review targets. | "A builder starts with ADL: a simple local agent, a tool-using agent, or a payment-metadata agent. The same source contract is evaluated across export targets." |
| 3. Honest Readiness | 0:25-0:40 | Prosumer Builder target tables | Land on readiness states and blocked rows for Agent Spec, A2A Agent Card, Agent Skills, provider compatibility, RAP bridge, and Vercel eve. | Report-ready, metadata-only, or blocked. | "Instead of claiming everything is production-ready, ReddiAgent labels each target honestly: report-ready, metadata-only, blocked before generation, or blocked by validation." |
| 4. Validation Workspace | 0:40-0:55 | `adl-validation-ui.html` | Show two-column editor/results layout; select bundled example; validate. | Validate ADL before generation. | "Here the builder can inspect or paste ADL and see validation feedback. Invalid ADL is stopped with a clear fix before any runtime path exists." |
| 5. Beta Review Surface | 0:55-1:15 | `beta-review-ui.html` | Show header badges, package summary, boundary status, evidence index, rollback transcript, and fail-closed cues. | Operator review is first-class. | "This is the operator-facing beta review surface: release, selected ADL, pinned evidence, dry-run transcript, rollback transcript, and fail-closed cases." |
| 6. Try It | 1:15-1:30 | Landing page or title card over blurred browser background | Return to demo URL; show direct page links and CTA. | Describe, review, export, block. | "The point is not that an agent ran onchain. The point is the safer first milestone: static, deterministic proof that ReddiAgent can describe agents, review them, export them, and block unsafe claims before runtime." |

## Visual Direction

Tone: cinematic restraint, not hype. Treat ReddiAgent as evidence-first builder tooling: clean browser captures, slow push-ins, precise lower-third callouts, shallow UI focus, and quick evidence montages.

Use captions that say:

- `static review surface`
- `pinned evidence`
- `local/static check`
- `guardrail status`

Avoid captions that imply live integration, runtime activation, production readiness, infrastructure deployment, settlement, or mainnet execution.

Preferred scene treatment:

- Opening: slow zoom into guardrail row, then crossfade to coverage cards.
- Example rows: keep text readable; use small callouts for `ADL source`, `Export target`, `Readiness state`, and `Authoritative check`.
- Readiness rows: focus from green `report-ready` to amber/red blocked states.
- Validation UI: whole viewport first, then crop/right-side metrics.
- Beta UI: top half for badges/boundaries, then 2-3 second holds on package summary, rollback, evidence hashes, and fail-closed cues.
- Closing: static title card over a slightly darkened/blurred Prosumer Builder background.

## Capture Plan

Use segmented takes rather than one continuous recording.

| Take | Scene | URL | Interaction | Target Duration | Tooling |
| --- | --- | --- | --- | ---: | --- |
| `take-01-landing` | 1 | `/` | Load page, slow scroll to coverage area. | 10s | Playwright page video or Peekaboo Chrome window capture |
| `take-02-builder-targets` | 2 | `/` | Scroll through target rows and command snippets. | 15s | Playwright page video or screenshot sequence with ffmpeg pan/zoom |
| `take-03-validation` | 3 | `/adl-validation-ui.html` | Select bundled examples; click validation if needed. | 15s | Playwright preferred |
| `take-04-beta-review` | 4 | `/beta-review-ui.html` | Scroll from summary to boundary flags/evidence. | 18s | Playwright or Peekaboo |
| `take-05-reports-or-close` | 5-6 | `/reports/BETA-RELEASE-VERIFICATION-CLI-REPORT.md` or `/` | Briefly show beta verification report, then return to the demo URL for CTA. | 15s | Playwright or generated title card |

Preferred capture stack:

1. Use Chrome at 1920x1080 or 1280x800.
2. Use `npx playwright` with the installed Chromium/Chrome channel when stable page-level recording is enough.
3. Use Peekaboo for window-level capture only when Chrome DevTools/page recording is insufficient.
4. Fall back to screenshot sequences plus ffmpeg Ken Burns if video recording permissions fail.

## Production Commands

Draft narration locally:

```bash
/Users/loki/.pyenv/versions/3.14.3/bin/python3 /Users/loki/.openclaw/workspace/scripts/speak.py \
  --agent sara \
  --output /tmp/reddiagent-demo-voiceover.wav \
  "$(cat /tmp/reddiagent-demo-narration.txt)"
```

Normalize narration:

```bash
ffmpeg -y -i /tmp/reddiagent-demo-voiceover.wav \
  -af loudnorm=I=-14:TP=-1:LRA=11 -ar 48000 \
  /tmp/reddiagent-demo-voiceover-normalized.wav
```

Assemble locked visual takes:

```bash
ffmpeg -y -f concat -safe 0 -i /tmp/reddiagent-demo-concat.txt \
  -c:v libx264 -pix_fmt yuv420p -r 30 -an \
  /tmp/reddiagent-demo-video-only.mp4
```

Mux video and narration:

```bash
ffmpeg -y \
  -i /tmp/reddiagent-demo-video-only.mp4 \
  -i /tmp/reddiagent-demo-voiceover-normalized.wav \
  -c:v copy -c:a aac -ar 48000 -shortest \
  /tmp/reddiagent-demo-walkthrough.mp4
```

If multiple audio clips are mixed, use `amix=duration=longest:normalize=0`, never `duration=first`.

## Demo Page Embed Plan

After the final MP4 is produced and hosted, update the public demo page landing area with:

```html
<section id="walkthrough-video">
  <h2>Watch The Demo</h2>
  <video controls preload="metadata">
    <source type="video/mp4" src="PUBLIC_MP4_URL">
  </video>
</section>
```

Keep direct links to:

- `/adl-validation-ui.html`
- `/beta-review-ui.html`
- `/examples/simple-agent.yaml`
- `/examples/tool-agent.yaml`
- `/examples/payment-agent.yaml`
- `/reports/BETA-RELEASE-VERIFICATION-CLI-REPORT.md`

Before relying on the links in the public page, verify each returns HTTP 200. If Markdown/YAML paths return 404 in here.now, convert them to linked HTML cards or remove them from visible CTA copy until the bundle is republished cleanly.

## QC Checklist

- [ ] Landing page loads over HTTPS.
- [ ] MP4 plays in browser with video and audio from the first second.
- [ ] No scene includes private workspace paths, tokens, credentials, or hidden operator state.
- [ ] Captions do not overclaim runtime, provider, MCP, payment, Docker, Surfpool, Coolify, devnet, or mainnet use.
- [ ] Audio is intelligible and not rushed.
- [ ] Final MP4 is H.264/AAC, 1920x1080 or lower, and under the practical here.now upload limit.
- [ ] Updated public demo returns HTTP 200 for `/`, the MP4 URL, and the direct UI pages.
