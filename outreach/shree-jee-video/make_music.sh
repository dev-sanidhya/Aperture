#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/out"
SR=44100

# ============================================================
# Energetic electronic bed @ 100 BPM (-> ~120 BPM after 1.2x).
# 8-chord progression, 1 bar (2.4s) each = 19.2s loop.
#   Cmaj7 Amin7 Fmaj7 G7  Em7 Amin7 Dm7 G7
# ============================================================

# ---- PAD (mid-octave 7th chords, 1 bar each) ----
pad_chord () {
  ffmpeg -y -loglevel error \
    -f lavfi -i "sine=frequency=$2:duration=2.4" \
    -f lavfi -i "sine=frequency=$3:duration=2.4" \
    -f lavfi -i "sine=frequency=$4:duration=2.4" \
    -f lavfi -i "sine=frequency=$5:duration=2.4" \
    -filter_complex "[0][1][2][3]amix=inputs=4:normalize=1,afade=t=in:st=0:d=0.4,afade=t=out:st=1.95:d=0.45,volume=0.8[a]" \
    -map "[a]" -ar $SR "$1"
}
pad_chord p0.wav 261.63 329.63 392.00 493.88
pad_chord p1.wav 220.00 261.63 329.63 392.00
pad_chord p2.wav 174.61 220.00 261.63 329.63
pad_chord p3.wav 196.00 246.94 293.66 349.23
pad_chord p4.wav 164.81 196.00 246.94 293.66
pad_chord p5.wav 220.00 261.63 329.63 392.00
pad_chord p6.wav 146.83 174.61 220.00 261.63
pad_chord p7.wav 196.00 246.94 293.66 349.23
printf "file 'p%d.wav'\n" 0 1 2 3 4 5 6 7 > pad.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i pad.txt -c copy pad19.wav

# ---- BASS (root notes, mid-bass octave, 1 bar each) ----
bass_note () {
  ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=$2:duration=2.4" \
    -af "afade=t=in:st=0:d=0.02,afade=t=out:st=2.1:d=0.25,volume=0.9" -ar $SR "$1"
}
bass_note b0.wav 130.81
bass_note b1.wav 110.00
bass_note b2.wav 87.31
bass_note b3.wav 98.00
bass_note b4.wav 164.81
bass_note b5.wav 110.00
bass_note b6.wav 146.83
bass_note b7.wav 98.00
printf "file 'b%d.wav'\n" 0 1 2 3 4 5 6 7 > bass.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i bass.txt -c copy bass19.wav

# ---- ARP (eighth notes, 8 per bar @ 0.3s, octave-up chord tones) ----
arp=(
  523.25 659.25 783.99 987.77 523.25 659.25 783.99 987.77
  440.00 523.25 659.25 783.99 440.00 523.25 659.25 783.99
  349.23 440.00 523.25 659.25 349.23 440.00 523.25 659.25
  392.00 493.88 587.33 698.46 392.00 493.88 587.33 698.46
  329.63 392.00 493.88 587.33 329.63 392.00 493.88 587.33
  440.00 523.25 659.25 783.99 440.00 523.25 659.25 783.99
  293.66 349.23 440.00 523.25 293.66 349.23 440.00 523.25
  392.00 493.88 587.33 698.46 392.00 493.88 587.33 698.46
)
: > arp.txt
i=0
for f in "${arp[@]}"; do
  ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=$f:duration=0.3" \
    -af "afade=t=in:st=0:d=0.005,afade=t=out:st=0.07:d=0.21,volume=0.85" -ar $SR "a$i.wav"
  echo "file 'a$i.wav'" >> arp.txt
  i=$((i+1))
done
ffmpeg -y -loglevel error -f concat -safe 0 -i arp.txt -c copy arp19.wav

# ---- DRUMS ----
# kick: punchy low sine + click, on every beat (0.6s cell)
ffmpeg -y -loglevel error \
  -f lavfi -i "sine=frequency=55:duration=0.35" \
  -f lavfi -i "sine=frequency=95:duration=0.12" \
  -filter_complex "[0]afade=t=out:st=0.03:d=0.26[lo];[1]afade=t=out:st=0:d=0.1[hi];[lo][hi]amix=inputs=2:normalize=0,volume=2.4[k]" \
  -map "[k]" -ar $SR kick.wav
ffmpeg -y -loglevel error -i kick.wav -af "apad=whole_dur=0.6,atrim=0:0.6" -ar $SR kick_cell.wav
# hat: short pink-noise burst, eighth notes (0.3s cell)
ffmpeg -y -loglevel error -f lavfi -i "anoisesrc=d=0.05:c=pink:a=0.6" \
  -af "highpass=f=7500,afade=t=out:st=0:d=0.045,volume=0.8" -ar $SR hat.wav
ffmpeg -y -loglevel error -i hat.wav -af "apad=whole_dur=0.3,atrim=0:0.3" -ar $SR hat_cell.wav

# ---- RISER (noise swell into the scene-2 drop @ 6s) ----
ffmpeg -y -loglevel error -f lavfi -i "anoisesrc=d=1.6:c=pink:a=0.7" \
  -af "highpass=f=1600,afade=t=in:st=0:d=1.55,afade=t=out:st=1.5:d=0.1,volume=0.5" -ar $SR riser.wav

# ---- FINAL MIX (drums drop at 6s, glue compression, loud master) ----
ffmpeg -y -loglevel error \
  -stream_loop 4 -i pad19.wav \
  -stream_loop 4 -i arp19.wav \
  -stream_loop 4 -i bass19.wav \
  -stream_loop 130 -i kick_cell.wav \
  -stream_loop 260 -i hat_cell.wav \
  -i riser.wav \
  -filter_complex "\
    [0:a]volume=0.35,lowpass=f=2800[pad];\
    [1:a]volume=0.5[arp];\
    [2:a]volume=0.8,lowpass=f=700[bass];\
    [3:a]volume=1.3,adelay=6000|6000[kick];\
    [4:a]volume=0.45,adelay=6000|6000[hat];\
    [5:a]adelay=4400|4400[riser];\
    [pad][arp][bass][kick][hat][riser]amix=inputs=6:normalize=0,\
    acompressor=threshold=-16dB:ratio=4:attack=5:release=150,\
    alimiter=limit=0.95,\
    afade=t=in:st=0:d=0.8,afade=t=out:st=68:d=2,\
    loudnorm=I=-14:TP=-1.0:LRA=11[mix]" \
  -map "[mix]" -t 70 -ar $SR -ac 2 music.wav

rm -f p?.wav b?.wav a*.wav pad.txt bass.txt arp.txt pad19.wav bass19.wav arp19.wav \
      kick.wav kick_cell.wav hat.wav hat_cell.wav riser.wav
echo "music.wav created"
