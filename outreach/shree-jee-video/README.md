# Shree Jee Packaging - Aperture Concept Video

Personalized 70-second concept video for **Divyansh Ahuja** (Founder & Director, Shree Jee Packaging Industries) — a warm LinkedIn outreach asset for Aperture.

## The deliverable
`out/shree-jee-aperture-1080.mp4`
- 1080×1080 square (legible on mobile without rotating, clean on desktop)
- 70s, ~4.7 MB (well inside LinkedIn DM limits)
- H.264 / yuv420p (limited range) + AAC, `+faststart` → plays identically on any phone/laptop/browser
- Music bed only (no voiceover); all key copy is burned in for muted autoplay

## Flow
1. **Cold open** — "Hey Divyansh, a 60-second look"
2. **The gap** — supplies Amazon Basics, but runs on WhatsApp quotes + no website
3. **Fix #1** — a catalog site that matches their scale (flexible/laminated/printed packaging)
4. **Fix #2** — AI instant-quote tool, no manual work
5. **Close** — proof + "want a real, quick demo built around your product? Let's grab 10 minutes"

## Re-rendering
```bash
npm install
npx remotion render Main out/video-raw.mp4 --codec=h264
bash make_music.sh                       # regenerates out/music.wav
# final compatible mux:
ffmpeg -y -i out/video-raw.mp4 -i out/music.wav -map 0:v:0 -map 1:a:0 \
  -vf "scale=in_range=full:out_range=tv,format=yuv420p" -color_range tv \
  -c:v libx264 -profile:v high -level 4.0 -crf 20 -preset slow \
  -c:a aac -b:a 192k -ar 44100 -movflags +faststart -shortest \
  out/shree-jee-aperture-1080.mp4
```

Edit copy/timing in `src/scenes/*` and durations in `src/lib.tsx` (`D`).

## Preview
`npx remotion studio`
