"""Сборка коротких петель для блока «Наши возможности» (≤10 с, 1280x720, H.264, без звука)."""
import subprocess, sys, os

U = "/mnt/user-data/uploads/кейсы"
E = "/home/claude/cases/enc"
S = "/home/claude/vozm/src"
OUT = "/home/claude/vozm/out"
os.makedirs(OUT, exist_ok=True)

W, H = 1920, 1080
CRF = "18"

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:]); sys.exit(1)

def montage(name, segs, fps, fade=None):
    """segs: [(file, start, end)] -> concatenated loop."""
    args, chains = [], []
    for i, (f, a, b, *pre) in enumerate(segs):
        pre = (pre[0] + ",") if pre else ""   # своё кадрирование для куска (например, убрать вшитые субтитры)
        if len(segs) > 1:
            a, b = a + 0.05, b - 0.12   # запас от склеек исходника, чтобы не проскакивали чужие кадры
        args += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", f]
        chains.append(
            f"[{i}:v]{pre}fps={fps},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={W}:{H},setsar=1,format=yuv420p[v{i}]")
    concat = "".join(f"[v{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0[out]"
    if fade:
        total = sum((b - 0.12) - (a + 0.05) if len(segs) > 1 else b - a for f, a, b, *_ in segs)
        fi, fo = fade
        concat = concat.replace("[out]", "[c]") + f";[c]fade=t=in:st=0:d={fi},fade=t=out:st={total - fo:.3f}:d={fo}[out]"
    fc = ";".join(chains + [concat])
    run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", fc, "-map", "[out]", "-an",
         "-c:v", "libx264", "-preset", "slow", "-crf", CRF, "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", f"{OUT}/{name}.mp4"])

def split3d(name, pairs, fps=24, gap=4, W=1280, H=720, CRF="16"):
    """3D слева, финал справа, синхронно. pairs: [(3d, final, start, end)]."""
    hw = (W - gap) // 2
    args, chains, outs = [], [], []
    k = 0
    for j, (a3, af, s, e) in enumerate(pairs):
        for f in (a3, af):
            args += ["-ss", f"{s:.3f}", "-t", f"{e - s:.3f}", "-i", f]
        chains.append(f"[{k}:v]fps={fps},scale=-2:{H}:flags=lanczos,crop={hw}:{H},setsar=1[l{j}]")
        chains.append(f"[{k+1}:v]fps={fps},scale=-2:{H}:flags=lanczos,crop={hw}:{H},setsar=1[r{j}]")
        chains.append(f"[l{j}]pad={W}:{H}:0:0:color=0x101010[lp{j}];[lp{j}][r{j}]overlay={hw + gap}:0,format=yuv420p[p{j}]")
        outs.append(f"[p{j}]")
        k += 2
    fc = ";".join(chains + ["".join(outs) + f"concat=n={len(pairs)}:v=1:a=0[out]"])
    run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", fc, "-map", "[out]", "-an",
         "-c:v", "libx264", "-preset", "slow", "-crf", CRF, "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", f"{OUT}/{name}.mp4"])

LOG = f"{U}/логика молока.mp4"
REEL = f"{U}/шоурил.mp4"
AR = f"{U}/arendapro_render_6.mp4"
M9, MC, MD = f"{E}/motion_9-priemov.mp4", f"{E}/motion_claude.mp4", f"{E}/motion_duolingo.mp4"
BRUSH = f"{U}/ЗУБ ЩЕТКИ.mp4"

which = sys.argv[1:] or ["integration", "motion", "blocking", "realism", "creative", "lipsync"]

if "integration" in which:
    montage("integration", [
        (f"{U}/и материалов один из кадров.mp4", -0.05, 3.16),   # самолёт МС-21, целиком
        (BRUSH, 0.40, 4.33),       # щётка выплывает из темноты и раскрывается; обрез до подписи (она с 4.25)
    ], 24)

if "motion" in which:
    montage("motion", [
        (M9, 10.40, 12.20),        # пластика
        (MC, 12.36, 13.90),        # ВАУ!
        (MD, 9.60, 11.40),         # 3D-ноль трескается
        (M9, 12.40, 14.00),        # 3D-фигуры
        (MD, 18.55, 20.10),        # сова и уведомления
        (MC, 21.30, 22.80),        # логотип размножается
    ], 30)

if "blocking" in which:
    split3d("blocking", [
        (f"{S}/arenda-s1-3d-hq.mp4", f"{S}/arenda-s1-final-hq.mp4", 0.0, 4.75),
        (f"{S}/arenda-s2-3d-hq.mp4", f"{S}/arenda-s2-final-hq.mp4", 0.0, 5.25),
    ])

if "realism" in which:
    montage("realism", [
        (LOG, 2.15, 3.95),         # хоккеисты в свете
        (f"{U}/яндекс.mp4", 19.10, 21.70, "crop=1440:810:0:40"),  # сёрфер крупно на интервью, улыбается (кадр сверху — без субтитров)
        (f"{U}/wazzup_render_5.mp4", 20.95, 26.67), # девочка говорит два слова, зум, глаза
    ], 24)

if "creative" in which:
    # мини-история из «СИМ-КОНТРОЛЬ»: камера поднимается от коляски, летит стакан, реакция;
    # корги, парень с телефоном, слоу-мо самоката мимо корги (до появления титра); мягкий вход и выход
    SC = f"{U}/самокаты сим контроль.mp4"
    montage("creative", [
        (SC, 26.40, 28.85),   # камера от коляски вверх, стакан пролетает, короткая реакция
        (SC, 29.80, 30.90),   # корги крупно (кадр целиком)
        (SC, 30.80, 31.90),   # парень с телефоном (кадр целиком)
        (SC, 31.80, 33.95),   # слоу-мо: самокат проезжает мимо корги, камера отъезжает (до титра)
    ], 24)

if "lipsync" in which:
    montage("lipsync", [(f"{U}/липсинк.mp4", 0.0, 4.01)], 24)

for f in sorted(os.listdir(OUT)):
    p = f"{OUT}/{f}"
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True).stdout.strip()
    print(f, os.path.getsize(p), d)
