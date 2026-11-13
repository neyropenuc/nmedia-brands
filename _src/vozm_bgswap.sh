#!/bin/bash
# «Замена фона»: сцена 1 — ДО → ПОСЛЕ (линия слева направо), сцена 2 — ПОСЛЕ → ДО (линия справа налево).
set -e
D="/mnt/user-data/uploads/кейсы/замена фона"
O=/home/claude/vozm/out
T=/home/claude/vozm/tmp_bg; mkdir -p $T
LINE=0xC0E800
# wipe before after b_delay(frames) nframes t0 t1 dir(ltr|rtl) out
#   ltr: линия идёт слева направо, слева от неё ПОСЛЕ, справа ДО
#   rtl: линия идёт справа налево, слева от неё ПОСЛЕ, справа ДО (то есть ДО «наезжает» справа)
wipe() {
  local SP="st(0,clip((T-$5)/($6-$5),0,1));ld(0)*ld(0)*(3-2*ld(0))"
  local SPt="st(0,clip((t-$5)/($6-$5),0,1));ld(0)*ld(0)*(3-2*ld(0))"
  local POS POSt
  if [ "$7" = ltr ]; then POS="($SP)"; POSt="($SPt)"; else POS="(1-($SP))"; POSt="(1-($SPt))"; fi
  ffmpeg -v error -y -i "$1" -i "$2" -f lavfi -i "color=c=$LINE:s=4x1080:r=24" -f lavfi -i "color=c=$LINE@0.28:s=18x1080:r=24" -filter_complex "
    [0:v]fps=24,scale=1920:1080:flags=lanczos,setsar=1,format=yuv444p,tpad=start=$3:start_mode=clone,trim=end_frame=$4[b];
    [1:v]fps=24,scale=1920:1080:flags=lanczos,setsar=1,format=yuv444p,trim=end_frame=$4[a];
    [b][a]blend=all_expr='if(lt(X,W*$POS),B,A)',format=yuv420p[w];
    [3:v]format=rgba[glow];[2:v]format=rgba[ln];
    [w][glow]overlay=x='1920*$POSt-9':y=0:enable='between(t,$5,$6)':shortest=1[w2];
    [w2][ln]overlay=x='1920*$POSt-2':y=0:enable='between(t,$5,$6)':shortest=1,format=yuv420p[out]" \
    -map "[out]" -frames:v $4 -an -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p "$8"
}
# сцена 1, пара 22: синхронна кадр в кадр, 60 кадров; ДО → ПОСЛЕ
wipe "$D/22.mp4" "$D/22 (1).mp4" 0 60 0.30 1.70 ltr $T/p1.mp4
# сцена 2, пара 38: «до» отстаёт от «после» на 10 кадров; начинаем с чистого ПОСЛЕ, затем линия справа налево открывает ДО
wipe "$D/38.mp4" "$D/38 (1).mp4" 10 33 0.45 1.30 rtl $T/p2.mp4
ffmpeg -v error -y -i $T/p1.mp4 -i $T/p2.mp4 -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[o]" -map "[o]" -an \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -movflags +faststart $O/bgswap.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 $O/bgswap.mp4
