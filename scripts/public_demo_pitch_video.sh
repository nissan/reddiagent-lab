#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_URL="${DEMO_URL:-https://present-hearth-vhey.here.now}"
PITCH_PAGE_URL="${PITCH_PAGE_URL:-file://$ROOT/docs/public-demo-pitch.html}"
OUT="${OUT:-/tmp/reddiagent-demo-pitch-video}"
SPEAK="${SPEAK:-/Users/loki/.openclaw/workspace/scripts/speak.py}"
FFMPEG="${FFMPEG:-/Users/loki/.local/bin/ffmpeg}"
FFPROBE="${FFPROBE:-/opt/homebrew/bin/ffprobe}"

mkdir -p "$OUT"/{audio,captions,clips,final,manifests,qc,stills}

cat > "$OUT/narration.txt" <<'TEXT'
Most agent demos start too late.
They show something running before anyone can inspect what the agent was allowed to do, what the target preserved, or what should have been blocked.
Meet Maya. She is preparing an agent for a partner review.
Before she talks about runtime, payments, MCP, or deployment, she needs one thing: a contract everyone can inspect.
That contract is ADL.
In ReddiAgent, the agent starts as a declarative definition: model needs, tools, data, policies, eval gates, traces, runtime intent, and optional payment or reputation metadata.
Maya validates the ADL first.
If a required harness field is missing, the demo stops with a specific fix instead of generating unsafe code.
Then she checks export readiness.
Agent Spec, A2A Agent Card, Agent Skills, provider reports, RAP bridge metadata, and Vercel eve are treated as targets.
ReddiAgent shows what is report-ready, what is metadata-only, and what is blocked before generation.
Now the reviewer has a surface too.
The beta review UI ties the candidate to pinned evidence, boundary flags, dry-run transcripts, rollback cues, and fail-closed denial cases.
So the claim is deliberately narrow.
This public demo does not activate a runtime, call providers, invoke MCP, settle payments, start infrastructure, or touch mainnet.
It proves the safer first milestone: describe the agent, inspect the harness, review target loss, and block unsafe claims before anything risky runs.
TEXT

cat > "$OUT/captions/01.txt" <<'TEXT'
Most agent demos start too late.
TEXT
cat > "$OUT/captions/02.txt" <<'TEXT'
Maya needs a contract everyone can inspect.
TEXT
cat > "$OUT/captions/03.txt" <<'TEXT'
ADL captures the agent and its harness.
TEXT
cat > "$OUT/captions/04.txt" <<'TEXT'
Invalid definitions stop before generation.
TEXT
cat > "$OUT/captions/05.txt" <<'TEXT'
Export readiness makes loss visible.
TEXT
cat > "$OUT/captions/06.txt" <<'TEXT'
The important moment: unsafe claims stop here.
TEXT
cat > "$OUT/captions/07.txt" <<'TEXT'
Reviewers get evidence, rollback, and boundaries.
TEXT
cat > "$OUT/captions/08.txt" <<'TEXT'
Static proof before runtime.
TEXT

curl -fsSI -L "$DEMO_URL/builder-report.html" >/dev/null
curl -fsSI -L "$DEMO_URL/adl-validation-ui.html" >/dev/null
curl -fsSI -L "$DEMO_URL/beta-review-ui.html" >/dev/null
curl -fsSI -L "$DEMO_URL/reports/BETA-RELEASE-VERIFICATION-CLI-REPORT.md" >/dev/null

npx --yes playwright screenshot --channel chrome --viewport-size=1920,1080 --wait-for-timeout=1000 \
  "$PITCH_PAGE_URL" "$OUT/stills/01-pitch-hero.png"
npx --yes playwright screenshot --channel chrome --viewport-size=1920,1080 --wait-for-timeout=1000 \
  "$DEMO_URL/builder-report.html" "$OUT/stills/02-builder-report.png"
npx --yes playwright screenshot --channel chrome --viewport-size=1920,1080 --wait-for-timeout=1000 \
  "$DEMO_URL/adl-validation-ui.html" "$OUT/stills/03-validation.png"
npx --yes playwright screenshot --channel chrome --viewport-size=1920,1080 --wait-for-timeout=1000 \
  "$DEMO_URL/beta-review-ui.html" "$OUT/stills/04-beta-review.png"
npx --yes playwright screenshot --channel chrome --viewport-size=1920,1080 --wait-for-timeout=1000 \
  "$DEMO_URL/reports/BETA-RELEASE-VERIFICATION-CLI-REPORT.md" "$OUT/stills/05-verification-report.png"

cp "$OUT/stills/04-beta-review.png" "$OUT/final/reddiagent-demo-story-poster.png"

set +e
"$SPEAK" --agent sara --output "$OUT/audio/narration.raw.wav" "$(tr '\n' ' ' < "$OUT/narration.txt")"
speak_status=$?
set -e
if [ "$speak_status" -ne 0 ] && [ ! -s "$OUT/audio/narration.raw.wav" ]; then
  say -v Samantha -r 168 -o "$OUT/audio/narration.raw.aiff" -f "$OUT/narration.txt"
  "$FFMPEG" -y -i "$OUT/audio/narration.raw.aiff" "$OUT/audio/narration.raw.wav"
fi

"$FFMPEG" -y -i "$OUT/audio/narration.raw.wav" \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" \
  -ac 2 -c:a pcm_s16le "$OUT/audio/narration.norm.wav"

make_clip() {
  local id="$1"
  local image="$2"
  local caption="$3"
  local duration="$4"
  local zoom="${5:-1.035}"
  "$FFMPEG" -y -loop 1 -framerate 30 -t "$duration" -i "$image" \
    -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080:(iw-1920)/2:0,fps=30,format=yuv420p,drawbox=x=0:y=820:w=1920:h=260:color=black@0.48:t=fill,drawtext=textfile='$caption':fontcolor=white:fontsize=54:line_spacing=10:x=90:y=872:box=0" \
    -c:v libx264 -crf 20 -preset medium -an "$OUT/clips/${id}.mp4"
}

make_clip "01-cold-open" "$OUT/stills/01-pitch-hero.png" "$OUT/captions/01.txt" 8
make_clip "02-maya-contract" "$OUT/stills/01-pitch-hero.png" "$OUT/captions/02.txt" 10
make_clip "03-adl-contract" "$OUT/stills/02-builder-report.png" "$OUT/captions/03.txt" 11
make_clip "04-validation" "$OUT/stills/03-validation.png" "$OUT/captions/04.txt" 10
make_clip "05-readiness" "$OUT/stills/02-builder-report.png" "$OUT/captions/05.txt" 12
make_clip "06-says-no" "$OUT/stills/05-verification-report.png" "$OUT/captions/06.txt" 9
make_clip "07-reviewer" "$OUT/stills/04-beta-review.png" "$OUT/captions/07.txt" 16
make_clip "08-close" "$OUT/stills/01-pitch-hero.png" "$OUT/captions/08.txt" 18

{
  printf "file '%s'\n" "$OUT/clips/01-cold-open.mp4"
  printf "file '%s'\n" "$OUT/clips/02-maya-contract.mp4"
  printf "file '%s'\n" "$OUT/clips/03-adl-contract.mp4"
  printf "file '%s'\n" "$OUT/clips/04-validation.mp4"
  printf "file '%s'\n" "$OUT/clips/05-readiness.mp4"
  printf "file '%s'\n" "$OUT/clips/06-says-no.mp4"
  printf "file '%s'\n" "$OUT/clips/07-reviewer.mp4"
  printf "file '%s'\n" "$OUT/clips/08-close.mp4"
} > "$OUT/manifests/video-concat.txt"

"$FFMPEG" -y -f concat -safe 0 -i "$OUT/manifests/video-concat.txt" \
  -c copy "$OUT/final/reddiagent-demo-story-silent.mp4"

"$FFMPEG" -y \
  -i "$OUT/final/reddiagent-demo-story-silent.mp4" \
  -i "$OUT/audio/narration.norm.wav" \
  -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest \
  "$OUT/final/reddiagent-demo-story-cut.mp4"

"$FFPROBE" -v error \
  -show_entries format=duration,size \
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate \
  -of json "$OUT/final/reddiagent-demo-story-cut.mp4" > "$OUT/qc/ffprobe.json"

"$FFMPEG" -i "$OUT/final/reddiagent-demo-story-cut.mp4" \
  -af silencedetect=n=-45dB:d=0.5 -f null - > "$OUT/qc/silencedetect.log" 2>&1 || true
"$FFMPEG" -i "$OUT/final/reddiagent-demo-story-cut.mp4" \
  -vf blackdetect=d=0.5:pix_th=0.10 -an -f null - > "$OUT/qc/blackdetect.log" 2>&1 || true

echo "$OUT/final/reddiagent-demo-story-cut.mp4"
