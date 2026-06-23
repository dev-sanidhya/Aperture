#!/usr/bin/env bash
set -e
# Generate a 4-chord ambient pad loop (Cmaj7 - Amin7 - Fmaj7 - G7), each 4s
gen_chord () {
  local out=$1; shift
  local f1=$1 f2=$2 f3=$3 f4=$4
  ffmpeg -y -loglevel error \
    -f lavfi -i "sine=frequency=$f1:duration=4" \
    -f lavfi -i "sine=frequency=$f2:duration=4" \
    -f lavfi -i "sine=frequency=$f3:duration=4" \
    -f lavfi -i "sine=frequency=$f4:duration=4" \
    -filter_complex "[0][1][2][3]amix=inputs=4:normalize=1,afade=t=in:st=0:d=0.6,afade=t=out:st=3.2:d=0.8,volume=0.6[a]" \
    -map "[a]" -ar 44100 "$out"
}
gen_chord cC.wav 261.63 329.63 392.00 493.88
gen_chord cA.wav 220.00 261.63 329.63 392.00
gen_chord cF.wav 174.61 220.00 261.63 329.63
gen_chord cG.wav 196.00 246.94 293.66 349.23

# concat into 16s loop list
printf "file 'cC.wav'\nfile 'cA.wav'\nfile 'cF.wav'\nfile 'cG.wav'\n" > loop.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i loop.txt -c copy loop16.wav

# loop to ~72s and apply warmth: chorus + reverb + lowpass + gentle tremolo + fades
ffmpeg -y -loglevel error -stream_loop 5 -i loop16.wav -t 70 \
  -af "chorus=0.5:0.9:50|60:0.4|0.32:0.25|0.4:2|1.3,aecho=0.8:0.7:60|120:0.3|0.2,lowpass=f=2600,tremolo=f=0.15:d=0.35,volume=0.85,afade=t=in:st=0:d=2,afade=t=out:st=68:d=2" \
  -ar 44100 -ac 2 music.wav
echo "music.wav created"
