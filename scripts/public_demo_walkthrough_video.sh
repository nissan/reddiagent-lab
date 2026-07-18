#!/usr/bin/env bash
set -euo pipefail

DEMO_URL="${DEMO_URL:-https://present-hearth-vhey.here.now}"
OUT="${OUT:-/tmp/reddiagent-demo-video}"
PYTHON="${PYTHON:-/Users/loki/.pyenv/versions/3.14.3/bin/python3}"
SPEAK="${SPEAK:-/Users/loki/.openclaw/workspace/scripts/speak.py}"
FFMPEG="${FFMPEG:-/Users/loki/.local/bin/ffmpeg}"
FFPROBE="${FFPROBE:-/opt/homebrew/bin/ffprobe}"

mkdir -p "$OUT"/{audio,clips,final,manifests,qc,stills}

cat > "$OUT/narration.txt" <<'TEXT'
This is the public static ReddiAgent demo: no runtime activation, no provider calls, no MCP invocation, no payments, no mainnet.
It is a reviewable snapshot of the spec and export layer.
A builder starts with ADL: a simple local agent, a tool-using agent, or a payment-metadata agent.
The same source contract is evaluated across export targets.
Instead of claiming everything is production-ready, ReddiAgent labels each target honestly: report-ready, metadata-only, blocked before generation, or blocked by validation.
The ADL validation prototype lets a builder inspect or paste a definition and see feedback before any runtime path exists.
The beta review UI ties a release candidate to pinned evidence, rollback cues, and explicit boundary flags.
The latest verification reports show deterministic checks for local validator, Docker, Coolify, and beta readiness evidence.
The point is not that an agent ran onchain.
The point is the safer first milestone: static, deterministic proof that ReddiAgent can describe agents, review them, export them, and block unsafe claims before runtime.
TEXT

curl -fsSI -L "$DEMO_URL/" >/dev/null
curl -fsSI -L "$DEMO_URL/builder-report.html" >/dev/null
curl -fsSI -L "$DEMO_URL/adl-validation-ui.html" >/dev/null
curl -fsSI -L "$DEMO_URL/beta-review-ui.html" >/dev/null
curl -fsSI -L "$DEMO_URL/reports/BETA-RELEASE-VERIFICATION-CLI-REPORT.md" >/dev/null

npx --yes playwright screenshot --channel chrome --viewport-size=1920,1080 --wait-for-timeout=1500 \
  "$DEMO_URL/" "$OUT/stills/01-overview.png"
npx --yes playwright screenshot --channel chrome --viewport-size=1920,1080 --full-page --wait-for-timeout=1500 \
  "$DEMO_URL/builder-report.html" "$OUT/stills/02-builder-full.png"
npx --yes playwright screenshot --channel chrome --viewport-size=1920,1080 --wait-for-timeout=1500 \
  "$DEMO_URL/adl-validation-ui.html" "$OUT/stills/03-validation.png"
npx --yes playwright screenshot --channel chrome --viewport-size=1920,1080 --wait-for-timeout=1500 \
  "$DEMO_URL/beta-review-ui.html" "$OUT/stills/04-beta-review.png"
npx --yes playwright screenshot --channel chrome --viewport-size=1920,1080 --wait-for-timeout=1500 \
  "$DEMO_URL/reports/BETA-RELEASE-VERIFICATION-CLI-REPORT.md" "$OUT/stills/05-verification-report.png"

if ! "$PYTHON" "$SPEAK" --agent sara --output "$OUT/audio/narration.raw.wav" "$(tr '\n' ' ' < "$OUT/narration.txt")"; then
  say -v Samantha -o "$OUT/audio/narration.raw.aiff" -f "$OUT/narration.txt"
  "$FFMPEG" -y -i "$OUT/audio/narration.raw.aiff" "$OUT/audio/narration.raw.wav"
fi
"$FFMPEG" -y -i "$OUT/audio/narration.raw.wav" \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" \
  -ac 2 -c:a pcm_s16le "$OUT/audio/narration.norm.wav"

make_clip() {
  local id="$1"
  local image="$2"
  local duration="$3"
  "$FFMPEG" -y -loop 1 -t "$duration" -i "$image" \
    -vf "scale=1920:-1,crop=1920:1080:0:0,fps=30,format=yuv420p" \
    -c:v libx264 -crf 20 -preset medium -an "$OUT/clips/${id}.mp4"
}

make_clip "01-overview" "$OUT/stills/01-overview.png" 10
make_clip "02-builder" "$OUT/stills/02-builder-full.png" 15
make_clip "03-validation" "$OUT/stills/03-validation.png" 14
make_clip "04-beta-review" "$OUT/stills/04-beta-review.png" 16
make_clip "05-verification" "$OUT/stills/05-verification-report.png" 13

{
  printf "file '%s'\n" "$OUT/clips/01-overview.mp4"
  printf "file '%s'\n" "$OUT/clips/02-builder.mp4"
  printf "file '%s'\n" "$OUT/clips/03-validation.mp4"
  printf "file '%s'\n" "$OUT/clips/04-beta-review.mp4"
  printf "file '%s'\n" "$OUT/clips/05-verification.mp4"
} > "$OUT/manifests/video-concat.txt"

"$FFMPEG" -y -f concat -safe 0 -i "$OUT/manifests/video-concat.txt" \
  -c copy "$OUT/final/reddiagent-demo-silent.mp4"

"$FFMPEG" -y \
  -i "$OUT/final/reddiagent-demo-silent.mp4" \
  -i "$OUT/audio/narration.norm.wav" \
  -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest \
  "$OUT/final/reddiagent-demo-walkthrough.mp4"

"$FFPROBE" -v error \
  -show_entries format=duration,size \
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate \
  -of json "$OUT/final/reddiagent-demo-walkthrough.mp4" > "$OUT/qc/ffprobe.json"

"$FFMPEG" -i "$OUT/final/reddiagent-demo-walkthrough.mp4" \
  -af silencedetect=n=-45dB:d=0.5 -f null - > "$OUT/qc/silencedetect.log" 2>&1 || true
"$FFMPEG" -i "$OUT/final/reddiagent-demo-walkthrough.mp4" \
  -vf blackdetect=d=0.5:pix_th=0.10 -an -f null - > "$OUT/qc/blackdetect.log" 2>&1 || true

echo "$OUT/final/reddiagent-demo-walkthrough.mp4"
