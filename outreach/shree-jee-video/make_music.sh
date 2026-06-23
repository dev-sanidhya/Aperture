#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/out"

# ---- PAD: 4-chord ambient bed (Cmaj7 - Amin7 - Fmaj7 - G7), 4s each ----
gen_chord () {
  local out=$1 f1=$2 f2=$3 f3=$4 f4=$5
  ffmpeg -y -loglevel error \
    -f lavfi -i "sine=frequency=$f1:duration=4" \
    -f lavfi -i "sine=frequency=$f2:duration=4" \
    -f lavfi -i "sine=frequency=$f3:duration=4" \
    -f lavfi -i "sine=frequency=$f4:duration=4" \
    -filter_complex "[0][1][2][3]amix=inputs=4:normalize=1,afade=t=in:st=0:d=0.5,afade=t=out:st=3.3:d=0.7,volume=0.8[a]" \
    -map "[a]" -ar 44100 "$out"
}
gen_chord pC.wav 261.63 329.63 392.00 493.88
gen_chord pA.wav 220.00 261.63 329.63 392.00
gen_chord pF.wav 174.61 220.00 261.63 329.63
gen_chord pG.wav 196.00 246.94 293.66 349.23
printf "file 'pC.wav'\nfile 'pA.wav'\nfile 'pF.wav'\nfile 'pG.wav'\n" > pad.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i pad.txt -c copy pad16.wav

# ---- ARP: plucky eighth-note arpeggio for movement/presence ----
notes=(
  523.25 659.25 783.99 987.77 523.25 659.25 783.99 987.77
  440.00 523.25 659.25 783.99 440.00 523.25 659.25 783.99
  349.23 440.00 523.25 659.25 349.23 440.00 523.25 659.25
  392.00 493.88 587.33 698.46 392.00 493.88 587.33 698.46
)
: > arp.txt
i=0
for f in "${notes[@]}"; do
  ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=$f:duration=0.5" \
    -af "afade=t=in:st=0:d=0.01,afade=t=out:st=0.10:d=0.38,volume=0.9" \
    -ar 44100 "n$i.wav"
  echo "file 'n$i.wav'" >> arp.txt
  i=$((i+1))
done
ffmpeg -y -loglevel error -f concat -safe 0 -i arp.txt -c copy arp16.wav

# ---- MIX: loop both to 70s, blend, add light space, loudness-normalize ----
ffmpeg -y -loglevel error \
  -stream_loop 5 -i pad16.wav \
  -stream_loop 5 -i arp16.wav \
  -filter_complex "[0:a]volume=0.55,lowpass=f=3200[pad];[1:a]volume=0.42,aecho=0.8:0.7:90|180:0.25|0.15[arp];[pad][arp]amix=inputs=2:normalize=0,tremolo=f=0.12:d=0.25,afade=t=in:st=0:d=1.5,afade=t=out:st=68:d=2,loudnorm=I=-16:TP=-1.5:LRA=11[mix]" \
  -map "[mix]" -t 70 -ar 44100 -ac 2 music.wav

# cleanup temp note/chord files
rm -f pC.wav pA.wav pF.wav pG.wav pad16.wav pad.txt arp16.wav arp.txt n*.wav
echo "music.wav created"
