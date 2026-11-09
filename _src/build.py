#!/usr/bin/env python3
"""Собирает медиа и json кейсов для трёх репозиториев GitHub Pages."""
import json, os, shutil, subprocess, sys

U = "/mnt/user-data/uploads/кейсы"
A = U + "/сайт/neuromedia"
ENC = "/home/claude/cases/enc"
R = {"brands": "/home/claude/nmedia-brands", "reels": "/home/claude/nmedia-reels", "motion": "/home/claude/nmedia-motion"}
BASE = {k: f"https://neyropenuc.github.io/nmedia-{k}/" for k in R}

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2000:]); sys.exit(1)

def frame(src, t, d, base, vertical=False, maxside=1920, q=90):
    # кадр в родном разрешении -> webp высокого качества
    tmp = os.path.join(d, "_frame.png")
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", tmp])
    name = place_image(tmp, d, base, maxside=maxside, q=q, force=True); os.remove(tmp); return name

def loop(src, start, out, vertical=False, dur=5):
    if vertical:
        # вертикальный ролик — на всю ширину экрана, кадрируем по центру
        args = ["-vf", "crop=iw:iw*9/16,scale=1920:1080:flags=lanczos"]
    else:
        args = ["-vf", "scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080"]
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", src, "-t", str(dur), "-an", *args,
         "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out])

def copy(src, out):
    shutil.copyfile(src, out)

def place_image(src, d, base, maxside=1920, q=90, force=False):
    """webp до 300 КБ кладём как есть; остальное — в webp высокого качества (длинная сторона до maxside)."""
    ext = os.path.splitext(src)[1].lower()
    if not force and ext == ".webp" and os.path.getsize(src) <= 300_000:
        name = base + ".webp"; copy(src, os.path.join(d, name)); return name
    from PIL import Image
    im = Image.open(src).convert("RGB"); im.thumbnail((maxside, maxside), Image.LANCZOS)
    name = base + ".webp"; im.save(os.path.join(d, name), "WEBP", quality=q, method=6); return name

def build(section, cases):
    root = R[section]
    out = []
    for c in cases:
        d = os.path.join(root, c["id"]); os.makedirs(d, exist_ok=True)
        url = lambda f: BASE[section] + c["id"] + "/" + f
        item = {"id": c["id"], "title": c["title"]}
        if c.get("views"): item["views"] = c["views"]
        item["description"] = c["description"]
        v = c.get("vertical", False)
        # обложка карточки
        if "cover_file" in c:
            item["preview"] = url(place_image(c["cover_file"], d, "cover"))
        else:
            item["preview"] = url(frame(c["src"], c["cover_t"], d, "cover", v))
        # фон шапки страницы кейса
        if "bg_file" in c:
            ext = os.path.splitext(c["bg_file"])[1].lower()
            copy(c["bg_file"], os.path.join(d, "bg" + ext)); item["preview_vid"] = url("bg" + ext)
        else:
            loop(c["bg_src"] if "bg_src" in c else c["src"], c["bg_t"], os.path.join(d, "bg.mp4"), v); item["preview_vid"] = url("bg.mp4")
        # фото
        imgs = []
        for i, p in enumerate(c.get("image_files", []), 1):
            imgs.append(url(place_image(p, d, f"photo{i}", maxside=1600, q=88)))
        for i, t in enumerate(c.get("photo_t", []), len(imgs) + 1):
            imgs.append(url(frame(c["src"], t, d, f"photo{i}", v, maxside=1600, q=88)))
        item["images"] = imgs
        # ролики (как есть, без пережатия)
        vids = []
        for i, p in enumerate(c["videos"], 1):
            name = "video.mp4" if len(c["videos"]) == 1 else f"video{i}.mp4"
            copy(p, os.path.join(d, name)); vids.append(url(name))
        item["videos"] = vids
        out.append(item)
        print("ok", section, c["id"])
    with open(os.path.join(root, f"{section}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    open(os.path.join(root, ".nojekyll"), "w").close()

M = U + "/облоги материалы"
old = {x["id"]: x for x in json.load(open(A + "/brands.json", encoding="utf-8")) + json.load(open(A + "/reels.json", encoding="utf-8"))}

BRANDS = [
    dict(id="logika-moloka", title="ЛОГИКА МОЛОКА", src=U + "/логика молока.mp4", cover_file="/home/claude/cases/covers/logika.png", bg_t=5.5, image_files=[M + "/Still 2026-08-29 131622_2.11.1.png", M + "/tqg0mEw25HhaWB5xLnV0PCXFnVcTakbvUv7m3Leu6VGvfCkiDdmzZRFTzUceEPU.jpg", M + "/ChatGPT Image 29 авг. 2026 г., 13_43_29.png"],
         videos=[U + "/логика молока.mp4"],
         description="Большой проект для бренда «Логика молока» о любительском спорте: хоккей, футбол, команды и болельщики. Больше 10 спортсменов, их форма, медали и локации воссозданы один в один по материалам бренда. Быстрое движение в кадре, с которым нейросети справляются хуже всего, и максимальный фотореализм — без съёмочной смены."),
    dict(id="arendapro", title="АРЕНДА.PRO", src=U + "/arendapro_render_6.mp4", cover_file=M + "/photo_5444989384609439351_y.jpg", bg_file="/home/claude/cases/covers/arenda_bg.mp4", image_files=[M + "/photo_5444989384609439348_y.jpg", M + "/photo_5444989384609439349_y.jpg", M + "/photo_5444989384609439350_y.jpg"],
         videos=[U + "/arendapro_render_6.mp4"],
         description="Ролик для сервиса Аренда.PRO: история арендодателя Геннадия — двенадцать показов и ноль жильцов — и решение, которое предлагает сервис. Сцены и пролёты камеры сначала собрали в 3D, офис и команду воссоздали по фотографиям клиента, а затем наложили нейросеть. Так камера идёт ровно так, как задумано, а герои не меняются от кадра к кадру."),
    dict(id="sim-kontrol", title="СИМ-КОНТРОЛЬ", src=U + "/самокаты сим контроль.mp4", cover_file=M + "/ОБЛОЖКА_2.47.1 (1).png", bg_t=19, image_files=[M + "/ChatGPT Image 6 июн. 2026 г., 11_11_13.png", M + "/ChatGPT Image 8 июн. 2026 г., 18_07_02.png", M + "/Screenshot_4.png"],
         videos=[U + "/самокаты сим контроль.mp4"],
         description="Рекламный ролик для СИМ-КОНТРОЛЬ — проекта Национальной телематической платформы о безопасности на электросамокатах. Городские сцены, водители, пешеходы и райдеры, активация самоката по Face ID и передача данных в реальном времени. Весь ролик создан с помощью нейросетей, без съёмок."),
    dict(id="yandex", title="МОЯ ВОЛНА", src=U + "/яндекс.mp4", cover_file=M + "/ПРЕВЬЮ ФОТО_2.1.1.png", bg_t=41, photo_t=[43, 45, 35],
         videos=[U + "/яндекс.mp4"],
         description="Рекламный ролик в формате документального интервью: история серфера от детской мечты до финала чемпионата. Волны, тренировки, победа и признание — всё снято без съёмок и выездов, целиком с помощью нейросетей. Герой узнаваем в каждом кадре — от детских воспоминаний до пьедестала."),
    dict(id="h2agency", title=old["h2agency"]["title"], description=old["h2agency"]["description"],
         cover_file=A + "/pictures/h2/h2_preview.webp", bg_file=A + "/cases_previews/tashkent_preview.webm",
         image_files=[A + "/pictures/h2/h2_logo.webp", A + "/pictures/h2/image.webp", A + "/pictures/h2/image2.webp"],
         videos=[U + "/h2_render.mp4"]),
    dict(id="niva", title="NIVA TRAVEL", src=U + "/niva_render.mp4", cover_file=U + "/облоги материалы/нива облока.jpg", bg_t=9.5, photo_t=[1, 12.1, 15.6],
         videos=[U + "/niva_render.mp4"],
         description="Имиджевый ролик NIVA TRAVEL: внедорожник в пустыне, дюны, песчаные вихри и макро-кадры её обитателей. Динамика, свет заката и фактура песка — вся картинка создана с помощью нейросетей, без выезда на съёмку."),
    dict(id="chetko", title=old["chetko"]["title"], description=old["chetko"]["description"],
         cover_file=A + "/pictures/chetko/chetko_preview.png", bg_file=A + "/cases_previews/chetko_preview.webm",
         image_files=[A + "/pictures/chetko/photo_2026-03-16_22-41-55.jpg", A + "/pictures/chetko/IMG_6165.webp", A + "/pictures/chetko/IMG_6694.webp"],
         videos=[U + "/chetko_render_3.mp4"]),
]

CV = A + "/cases_videos"
REELS = [
    dict(id="kinder", title="KINDER", views="2,8 млн", vertical=True, src=U + "/киндер рендер.mp4", cover_t=4.9, bg_t=1.0, image_files=[M + "/Ultra-high_resolution_cinematic_202604162225.png", M + "/Ultra-high_resolution_cinematic_202604162255.png", M + "/поменяй_гитару_в_202604162206.png"],
         videos=[U + "/киндер рендер.mp4"],
         description="Собственный рилс студии в стилистике рекламы Kinder Pingui: пингвины, ледяной дом, семейный оркестр с барабаном Kinder и тающий шоколад. Ролик набрал 2,8 млн просмотров. Весь визуал создан с помощью нейросетей."),
    dict(id="rastishka", title="РАСТИШКА", views="1,6 млн", vertical=True, src=U + "/растишка рилс.mp4", cover_t=29, bg_t=23, image_files=[M + "/ЙАЙАЙАЦУЙАУАЙЦУАУАЙУА_2.3.1.png", M + "/ChatGPT Image 12 мая 2026 г., 15_28_15.png", M + "/ChatGPT Image 13 мая 2026 г., 13_18_47.png"],
         videos=[U + "/растишка рилс.mp4"],
         description="Рилс в стилистике аниме для «Растишки»: героиня проходит путь от слёз до победы на ринге, а Дино всё время рядом. Персонажи узнаваемы от первого до последнего кадра. Весь визуал и анимация созданы с помощью нейросетей."),
    dict(id="motion-vertical", title="МОУШН-РИЛС", views="1,2 млн", vertical=True, src=U + "/моушн вертикальный.MP4", cover_file="/home/claude/cases/covers/motion-vertical-clean.png", bg_t=29.5,
         videos=[U + "/моушн вертикальный.MP4"],
         description="Вертикальный моушн-ролик о том, как мы теперь делаем моушн-дизайн. Claude не рисует видео, как другие нейросети, — он пишет код: каждая буква и каждый поворот камеры расписаны по времени. Начинаем с брифа — хронометраж, цвета бренда, стиль и настроение, — а дальше доводим до ума. Было: недели работы и серьёзный бюджет. Стало: в разы быстрее."),
    dict(id="arcteryx", title=old["arcteryx"]["title"], description=old["arcteryx"]["description"],
         cover_file=A + "/pictures/arcteryx/554a97d6-6b13-40ee-ab0f-addf51cf0a48_min.webp",
         bg_file=A + "/cases_previews/kling_20260303_Image_to_Video_Ultra_real_5866_0.webm",
         image_files=[A + "/pictures/arcteryx/арк реф.webp", A + "/pictures/arcteryx/арк лого (1).webp", A + "/pictures/arcteryx/саломон.webp"],
         videos=[ENC + "/arcteryx_h264.mp4"]),
    dict(id="keos", title="KEOS", vertical=True, src=U + "/Keos.mp4", cover_file="/home/claude/cases/covers/keos.png", bg_t=4, photo_t=[4.3, 6.4, 12.9],
         videos=[U + "/Keos.mp4", U + "/keos3_render.mp4"],
         description="Продуктовые рилсы для бренда инструментов KEOS: техника крупным планом со всеми деталями — мотор, редуктор, патрон, защита, кейс и комплектация. Тёмная студийная подача и акценты на преимуществах продукта. Весь визуал создан с помощью нейросетей на основе фотографий товара."),
    dict(id="wangpack", title=old["wangpack"]["title"], description=old["wangpack"]["description"],
         cover_file=A + "/pictures/frambini/фрамбини прев.webp", bg_file=A + "/cases_previews/sumki_preview.mp4",
         image_files=[A + "/pictures/frambini/фрамбини 2.webp", A + "/pictures/frambini/фрамбини.webp", A + "/pictures/frambini/фрам.webp"],
         videos=[CV + "/reel_1.mp4", CV + "/render2.mp4", CV + "/render_reel6.mp4", CV + "/render_reel7_2.mp4"]),
    dict(id="levshagroup", title=old["levshagroup"]["title"], description=old["levshagroup"]["description"],
         cover_file=A + "/pictures/levsha/A_highend_fashion_202512230837.webp", bg_file=A + "/cases_previews/levsha_preview.mp4",
         image_files=[A + "/pictures/levsha/photo_2025-12-03_13-59-13.webp", A + "/pictures/levsha/photo_2025-12-03_13-58-12 (2).webp", A + "/pictures/levsha/photo_2025-12-03_13-57-39 (2).webp"],
         videos=[CV + "/фешн.mp4", ENC + "/levsha_1080.mp4"]),
]

S = U + "/сайт"
MOTION = [
    dict(id="9-priemov", title="9 ПРИЁМОВ", src=ENC + "/motion_9-priemov.mp4", cover_t=9.4, bg_t=8,
         videos=[ENC + "/motion_9-priemov.mp4"],
         description="Внутренний проект студии: 25-секундный шоурил, где главный герой — один шар. В каждом блоке он показывает отдельный навык моушн-дизайна: тайминг, физику, типографику, ритм, пластику, 3D-формы, частицы, анимационные системы и стилизацию.\n\nТакую графику делаем для рекламы, презентаций продуктов и соцсетей."),
    dict(id="claude", title="CLAUDE", src=ENC + "/motion_claude.mp4", cover_t=1, bg_t=12,
         videos=[ENC + "/motion_claude.mp4"],
         description="Мы дали Claude пять фраз из типичного брифа: «логотип должен дышать», «продажи должны взлететь», «сделай вирусно». Он выполнил каждую дословно: логотип дышит, пока не лопнет, а столбик продаж улетает за край кадра и не возвращается. Анимацию и звук по нашему сценарию Claude написал кодом сам.\n\nНейросеть понимает ТЗ буквально. Мы понимаем, что вы имели в виду."),
    dict(id="duolingo", title="DUOLINGO", src=ENC + "/motion_duolingo.mp4", cover_t=20, bg_t=18,
         videos=[ENC + "/motion_duolingo.mp4"],
         description="Все, кто учил язык в Duolingo, знают эту сову: сначала она вежливо зовёт на урок, потом обижается, а потом начинает угрожать.\n\nСценарий, анимация и озвучка сделаны с помощью нейросетей."),
]

if __name__ == "__main__":
    which = sys.argv[1:] or ["brands", "reels", "motion"]
    if "brands" in which: build("brands", BRANDS)
    if "reels" in which: build("reels", REELS)
    if "motion" in which: build("motion", MOTION)
