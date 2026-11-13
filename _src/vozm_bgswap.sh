#!/bin/bash
# «Замена фона»: шторка-линия едет слева направо, за ней студия превращается в новую локацию.
set -e
D="/mnt/user-data/uploads/кейсы/замена фона"
O=/home/claude/vozm/out
T=/home/claude/vozm/tmp_bg; mkdir -p $T
LINE=0xC0E800
# p(t): плавный ход линии (smoothstep) от t0 до t1
wipe() { # $1 before, $2 after, $3 before_start_frame, $4 after_start_frame, $5 nframes, $6 t0, $7 t1, $8 out
  local P="(st(0,clip((T-$6)/($7-$6),0,1));ld(0)*ld(0)*(3-2*ld(0)))"
  local PX="(st(0,clip((t-$6)/($7-$6),0,1));ld(0)*ld(0)*(3-2*ld(0)))"
  ffmpeg -v error -y -i "$1" -i "$2" -f lavfi -i "color=c=$LINE:s=4x1080:r=24" -f lavfi -i "color=c=$LINE@0.28:s=18x1080:r=24" -filter_complex "
    [0:v]select='gte(n,$3)',setpts=PTS-STARTPTS,fps=24,scale=1920:1080:flags=lanczos,setsar=1,format=yuv444p,trim=end_frame=$5[b];
    [1:v]select='gte(n,$4)',setpts=PTS-STARTPTS,fps=24,scale=1920:1080:flags=lanczos,setsar=1,format=yuv444p,trim=end_frame=$5[a];
    [b][a]blend=all_expr='if(lt(X,W*$P),B,A)',format=yuv420p[w];
    [3:v]format=rgba[glow];[2:v]format=rgba[ln];
    [w][glow]overlay=x='1920*$PX-9':y=0:enable='between(t,$6,$7)':shortest=1[w2];
    [w2][ln]overlay=x='1920*$PX-2':y=0:enable='between(t,$6,$7)':shortest=1,format=yuv420p[out]" \
    -map "[out]" -frames:v $5 -an -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p "$8"
}
# пара 22: синхронны кадр в кадр, 60 кадров
wipe "$D/22.mp4" "$D/22 (1).mp4" 0 0 60 0.30 1.70 $T/p1.mp4
# пара 38: «до» и «после» сняты разными дублями (руки не совпадают) — шторку не делаем, ставим результат целиком
ffmpeg -v error -y -i "$D/38 (1).mp4" -vf "fps=24,scale=1920:1080:flags=lanczos,setsar=1" -an -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p $T/p2.mp4
ffmpeg -v error -y -i $T/p1.mp4 -i $T/p2.mp4 -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[o]" -map "[o]" -an \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -movflags +faststart $O/bgswap.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 $O/bgswap.mp4
