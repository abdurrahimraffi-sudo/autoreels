"""
Karakter kartun flat (digambar lewat kode, hanya butuh Pillow).
Dipakai sebagai dasar "mesin animasi" Auto Reels.

Contoh:  python karakter.py   -> menghasilkan contoh_scene.png dan lembar_ekspresi.png
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
SS = 2  # supersampling biar garis halus

KULIT = (255, 232, 208)
GELAP = (36, 30, 40)


def font(ukuran):
    """Montserrat (bobot tebal apa pun) jika ada di folder; jika tidak, font bawaan sistem."""
    folder = Path(__file__).resolve().parent
    temuan = []
    for lok in (folder, Path("."), folder / "fonts", Path("fonts")):
        if lok.exists():
            temuan += [f for f in lok.glob("*.ttf") if "montserrat" in f.name.lower() and "italic" not in f.name.lower()]
    for kunci in ("extrabold", "bold", "semibold", "medium"):
        for f in temuan:
            if kunci in f.name.lower().replace("-", "").replace("_", ""):
                return ImageFont.truetype(str(f), ukuran)
    for f in temuan:  # font variabel mis. Montserrat[wght].ttf
        ft = ImageFont.truetype(str(f), ukuran)
        try:
            ft.set_variation_by_axes([800])
        except Exception:
            pass
        return ft
    for p in (Path("C:/Windows/Fonts/arialbd.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
              Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")):
        if p.exists():
            return ImageFont.truetype(str(p), ukuran)
    return ImageFont.load_default()


def lerp(c1, c2, t):
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))


def gelapkan(c, f=0.78):
    return tuple(int(v * f) for v in c)


# ---------------------------------------------------------------- KARAKTER
def karakter(img, cx, ground, tinggi, ekspresi="netral", lengan="turun",
             hoodie=(38, 166, 154), rambut=GELAP, gaya="pendek", kacamata=False, kulit=KULIT):
    """Gambar satu karakter ke img (sudah dalam skala SS).
    cx, ground, tinggi dalam piksel output (bukan skala SS)."""
    d = ImageDraw.Draw(img, "RGBA")
    k = tinggi / 100.0 * SS
    X0, Y0 = cx * SS, ground * SS

    def L(x, y):
        return (X0 + x * k, Y0 + y * k)

    def kotak(x1, y1, x2, y2):
        return [L(x1, y1), L(x2, y2)]

    def lingkar(x, y, r, **kw):
        d.ellipse([L(x - r, y - r), L(x + r, y + r)], **kw)

    def elips(x, y, rx, ry, **kw):
        d.ellipse([L(x - rx, y - ry), L(x + rx, y + ry)], **kw)

    celana, sepatu = (44, 48, 66), (245, 245, 245)
    # bayangan di lantai
    elips(0, 0, 22, 3, fill=(0, 0, 0, 70))
    # rambut belakang (untuk cepol / rambut panjang)
    elips(0, -78, 23.5, 24, fill=rambut)
    if gaya == "panjang":
        d.rounded_rectangle(kotak(-24, -92, 24, -50), radius=9 * k, fill=rambut)
    if gaya == "cepol":
        lingkar(0, -101, 8, fill=rambut)
        d.rounded_rectangle(kotak(-24, -90, -17, -62), radius=3 * k, fill=rambut)
        d.rounded_rectangle(kotak(17, -90, 24, -62), radius=3 * k, fill=rambut)
    # kaki + sepatu
    d.rounded_rectangle(kotak(-12, -26, -2, -3), radius=3 * k, fill=celana)
    d.rounded_rectangle(kotak(2, -26, 12, -3), radius=3 * k, fill=celana)
    elips(-8, -1, 7, 3.2, fill=sepatu)
    elips(8, -1, 7, 3.2, fill=sepatu)
    # badan (hoodie)
    d.rounded_rectangle(kotak(-17, -55, 17, -21), radius=8 * k, fill=hoodie)
    elips(0, -55, 11, 4.5, fill=gelapkan(hoodie))
    d.rounded_rectangle(kotak(-10, -40, 10, -29), radius=3 * k, fill=gelapkan(hoodie, 0.86))
    d.line([L(-4, -53), L(-4, -44)], fill=(235, 235, 235), width=max(1, int(0.8 * k)))
    d.line([L(4, -53), L(4, -44)], fill=(235, 235, 235), width=max(1, int(0.8 * k)))
    # telinga + kepala
    lingkar(-21, -73, 3.6, fill=kulit)
    lingkar(21, -73, 3.6, fill=kulit)
    elips(0, -74, 21, 23, fill=kulit)
    # poni
    d.polygon([L(-22, -79), L(-20, -93), L(0, -99), L(20, -93), L(22, -79), L(15, -85),
               L(7, -80), L(-3, -86), L(-12, -81)], fill=rambut)
    # pipi merona
    pipi = lerp(kulit, (255, 120, 120), 0.45)  # merona menyesuaikan warna kulit
    elips(-13, -67, 4.2, 2.6, fill=pipi)
    elips(13, -67, 4.2, 2.6, fill=pipi)

    gw = max(2, int(1.3 * k))  # tebal garis wajah
    ey = -72
    if ekspresi == "netral":
        for sx in (-8, 8):
            elips(sx, ey, 4.4, 3.4, fill="white")
            lingkar(sx, ey + 0.8, 1.9, fill=GELAP)
            d.pieslice([L(sx - 4.6, ey - 3.8), L(sx + 4.6, ey + 3.8)], 180, 360, fill=kulit)
            d.line([L(sx - 4.6, ey), L(sx + 4.6, ey)], fill=GELAP, width=gw)
        d.line([L(-12, -78), L(-4, -78)], fill=rambut, width=gw)
        d.line([L(4, -78), L(12, -78)], fill=rambut, width=gw)
        d.line([L(-3, -63), L(3, -63)], fill=GELAP, width=gw)
    elif ekspresi == "kaget":
        for sx in (-8, 8):
            elips(sx, ey, 5.2, 5.8, fill="white", outline=GELAP, width=max(1, int(0.6 * k)))
            lingkar(sx, ey, 1.5, fill=GELAP)
        d.arc([L(-13, -88), L(-3, -78)], 200, 340, fill=rambut, width=gw)
        d.arc([L(3, -88), L(13, -78)], 200, 340, fill=rambut, width=gw)
        elips(0, -62, 3.2, 4.4, fill=(120, 40, 50))
        elips(0, -60.5, 2, 1.8, fill=(220, 100, 110))
        # keringat
        d.polygon([L(23, -86), L(21, -82), L(25, -82)], fill=(120, 190, 255))
    elif ekspresi == "sedih":
        for sx in (-8, 8):
            elips(sx, ey + 0.4, 4.2, 4.3, fill="white")
            lingkar(sx, ey - 0.4, 2.1, fill=GELAP)
        d.line([L(-12.5, -79), L(-4.5, -82.5)], fill=rambut, width=gw)
        d.line([L(4.5, -82.5), L(12.5, -79)], fill=rambut, width=gw)
        d.arc([L(-4, -63), L(4, -57)], 200, 340, fill=GELAP, width=gw)
        d.polygon([L(-9, -68), L(-11, -63), L(-7, -63)], fill=(120, 190, 255))
        elips(-9, -62.5, 2, 2, fill=(120, 190, 255))
    elif ekspresi == "marah":
        for sx in (-8, 8):
            elips(sx, ey + 0.5, 4.3, 2.8, fill="white")
            lingkar(sx, ey + 0.5, 1.7, fill=GELAP)
        d.line([L(-13, -83), L(-4, -77.5)], fill=rambut, width=int(gw * 1.4))
        d.line([L(4, -77.5), L(13, -83)], fill=rambut, width=int(gw * 1.4))
        d.rounded_rectangle(kotak(-5, -66, 5, -61), radius=1.2 * k, fill="white", outline=GELAP,
                            width=max(1, int(0.7 * k)))
        d.line([L(0, -66), L(0, -61)], fill=GELAP, width=max(1, int(0.6 * k)))
        # tanda marah
        for dx, dy in ((0, 0), (3.5, 1.5)):
            d.arc([L(20 + dx, -92 + dy), L(28 + dx, -84 + dy)], 180, 270, fill=(230, 60, 60), width=gw)
            d.arc([L(20 + dx, -92 + dy), L(28 + dx, -84 + dy)], 0, 90, fill=(230, 60, 60), width=gw)
    elif ekspresi == "senang":
        d.arc([L(-12, -76), L(-4, -69)], 200, 340, fill=GELAP, width=gw)
        d.arc([L(4, -76), L(12, -69)], 200, 340, fill=GELAP, width=gw)
        d.chord([L(-5, -66), L(5, -58)], 0, 180, fill=(120, 40, 50))
        d.line([L(-12, -79), L(-4, -79.5)], fill=rambut, width=gw)
        d.line([L(4, -79.5), L(12, -79)], fill=rambut, width=gw)

    if kacamata:
        for sx in (-8, 8):
            lingkar(sx, ey, 7.2, outline=(60, 50, 50), width=max(2, int(1.0 * k)))
        d.line([L(-1, ey), L(1, ey)], fill=(60, 50, 50), width=max(2, int(1.0 * k)))

    # lengan (digambar terakhir supaya di depan badan/kepala)
    poses = {
        "turun": [[(-17, -50), (-21, -38), (-20, -27)], [(17, -50), (21, -38), (20, -27)]],
        "angkat": [[(-17, -50), (-30, -57), (-33, -73)], [(17, -50), (30, -57), (33, -73)]],
        "dagu": [[(-17, -50), (-21, -38), (-20, -27)], [(17, -50), (14, -41), (6, -53)]],
        "tunjuk": [[(-17, -50), (-21, -38), (-20, -27)], [(17, -50), (30, -52), (45, -55)]],
    }
    for pts in poses.get(lengan, poses["turun"]):
        p = [L(*q) for q in pts]
        d.line(p, fill=hoodie, width=int(7.5 * k), joint="curve")
        for q in p[:2]:
            d.ellipse([q[0] - 3.75 * k, q[1] - 3.75 * k, q[0] + 3.75 * k, q[1] + 3.75 * k], fill=hoodie)
        hx, hy = p[2]
        d.ellipse([hx - 3.9 * k, hy - 3.9 * k, hx + 3.9 * k, hy + 3.9 * k], fill=kulit,
                  outline=gelapkan(kulit, 0.85), width=max(2, int(0.9 * k)))


# ---------------------------------------------------------------- ASET PNG
# Struktur:  aset_karakter/<tokoh>/<aksi>.png   (tokoh: A, B1, B2, ...)  + meta.json (tinggi_ref)
ASET = Path(__file__).resolve().parent / "aset_karakter"

# deskripsi aksi (dikirim ke Gemini supaya tahu pose apa yang tersedia)
AKSI_DESKRIPSI = {
    "netral": "berdiri tenang / datar",
    "sedih": "murung, wajah sedih",
    "senang": "tersenyum, tanda peace",
    "marah": "marah, tangan menyilang",
    "kaget": "terkejut (tanda seru)",
    "berpikir": "berpikir, tangan di dagu (tanda tanya)",
    "bingung": "bingung / ragu (tanda tanya)",
    "malu": "tersipu malu",
    "keren": "bergaya kacamata hitam",
    "girang": "sangat gembira, melompat",
    "menunjuk": "menunjuk ke depan / menegur",
    "kesal": "bete, tangan menyilang",
    "bosan": "duduk bosan / jenuh",
    "terpuruk": "jongkok memeluk lutut, sangat terpuruk",
    "tidur": "tertidur",
    "mengantuk": "mengantuk, mengucek mata",
    "melamun": "melamun",
    "jalan": "berjalan",
    "belakang": "membelakangi kamera (pergi / menjauh)",
    "minum": "menikmati minuman, senang",
}
# kalau aksi tidak dimiliki tokoh itu, pakai pengganti terdekat
FALLBACK = {
    "sedih": ["terpuruk", "bosan", "malu", "netral"], "bingung": ["berpikir", "netral"],
    "berpikir": ["bingung", "netral"], "menunjuk": ["bingung", "marah", "netral"],
    "keren": ["senang", "netral"], "kesal": ["marah", "bosan", "netral"],
    "bosan": ["kesal", "malu", "netral"], "terpuruk": ["malu", "bosan", "netral"],
    "tidur": ["mengantuk", "terpuruk", "netral"], "mengantuk": ["tidur", "malu", "netral"],
    "melamun": ["mengantuk", "malu", "netral"], "jalan": ["netral"], "belakang": ["netral"],
    "minum": ["senang", "netral"], "girang": ["senang", "netral"], "senang": ["girang", "netral"],
    "marah": ["kesal", "netral"], "kaget": ["bingung", "netral"], "malu": ["netral"],
}
# istilah lama (ekspresi) -> aksi
EKSPRESI_KE_AKSI = {"netral": "netral", "kaget": "kaget", "sedih": "sedih", "marah": "marah", "senang": "senang"}


def folder_aset(nama):
    for f in (ASET / nama, Path("aset_karakter") / nama):
        if f.exists() and list(f.glob("*.png")):
            return f
    return None


def daftar_folder(awalan):
    """Nama folder tokoh yang berawalan `awalan` (A -> ['A'], B -> ['B1','B2'])."""
    hasil = []
    for base in (ASET, Path("aset_karakter")):
        if base.exists():
            for f in sorted(base.iterdir()):
                if f.is_dir() and f.name.startswith(awalan) and list(f.glob("*.png")) and f.name not in hasil:
                    hasil.append(f.name)
    return hasil


def aksi_tersedia(nama):
    f = folder_aset(nama)
    return {p.stem for p in f.glob("*.png")} if f else set()


def pilih_aksi(nama, aksi):
    ada = aksi_tersedia(nama)
    for kandidat in [aksi] + FALLBACK.get(aksi, []) + ["netral"]:
        if kandidat in ada:
            return kandidat
    return sorted(ada)[0] if ada else None


def tempel_aset(img, nama, aksi, cx, ground, tinggi):
    """Tempel sprite (kaki di garis ground). Skala memakai tinggi_ref sprite 'netral' tokoh itu.
    Mengembalikan y puncak sprite (piksel output) untuk menaruh balon ucapan."""
    f = folder_aset(nama)
    aksi = pilih_aksi(nama, aksi)
    a = Image.open(f / f"{aksi}.png").convert("RGBA")
    ref = a.height
    meta = f / "meta.json"
    if meta.exists():
        import json
        ref = json.loads(meta.read_text()).get("tinggi_ref", ref)
    skala = tinggi * SS / ref
    a = a.resize((max(1, int(a.width * skala)), max(1, int(a.height * skala))), Image.LANCZOS)
    d = ImageDraw.Draw(img, "RGBA")
    lw, lh = min(a.width * 0.5, tinggi * SS * 0.30), tinggi * SS * 0.016
    d.ellipse([cx * SS - lw, ground * SS - lh, cx * SS + lw, ground * SS + lh * 1.6], fill=(0, 0, 0, 70))
    atas = int(ground * SS - a.height)
    img.alpha_composite(a, (int(cx * SS - a.width / 2), atas))
    return atas / SS


# ---------------------------------------------------------------- LATAR
def glow(img, cx, cy, radius, warna=(255, 196, 80), kuat=0.55):
    r = int(radius * SS)
    g = Image.radial_gradient("L").resize((2 * r, 2 * r))
    mask = g.point(lambda v: int(max(0, 255 - v) * kuat))
    layer = Image.new("RGBA", (2 * r, 2 * r), warna + (0,))
    layer.putalpha(mask)
    img.alpha_composite(layer, (int(cx * SS - r), int(cy * SS - r)))


TEMA = {
    "malam": dict(dinding=((78, 84, 136), (58, 64, 112)), lantai=((96, 84, 110), (72, 62, 88)),
                  kaca=(26, 36, 82), bintang=True, matahari=None, glow=((255, 196, 80), 0.5),
                  lampu=(255, 196, 70)),
    "sore": dict(dinding=((196, 134, 104), (160, 104, 84)), lantai=((156, 108, 84), (126, 84, 66)),
                 kaca=(246, 158, 92), bintang=False, matahari=(255, 226, 150), glow=((255, 170, 90), 0.32),
                 lampu=(255, 214, 120)),
    "pagi": dict(dinding=((200, 212, 222), (170, 184, 198)), lantai=((158, 126, 100), (128, 98, 78)),
                 kaca=(168, 214, 250), bintang=False, matahari=None, glow=((255, 244, 210), 0.22),
                 lampu=(250, 236, 190)),
}


def lerp(c1, c2, t):
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))


def latar_kamar(img, tema="malam"):
    cfg = TEMA[tema]
    d = ImageDraw.Draw(img, "RGBA")
    lantai = int(H * 0.77) * SS
    for y in range(lantai):
        d.line([(0, y), (W * SS, y)], fill=lerp(cfg["dinding"][0], cfg["dinding"][1], y / lantai))
    for y in range(lantai, H * SS):
        t = (y - lantai) / (H * SS - lantai)
        d.line([(0, y), (W * SS, y)], fill=lerp(cfg["lantai"][0], cfg["lantai"][1], t))
    for i in range(1, 9):
        y = lantai + int((H * SS - lantai) * (i / 9) ** 1.4)
        d.line([(0, y), (W * SS, y)], fill=(20, 15, 16, 110), width=SS * 3)
    d.rectangle([0, lantai - SS * 8, W * SS, lantai + SS * 2], fill=gelapkan(cfg["lantai"][0], 0.7))
    # jendela
    x1, y1, x2, y2 = [int(v * SS) for v in (W * 0.60, H * 0.20, W * 0.90, H * 0.44)]
    bingkai = gelapkan(cfg["dinding"][1], 0.55)
    d.rounded_rectangle([x1 - 14 * SS, y1 - 14 * SS, x2 + 14 * SS, y2 + 14 * SS], radius=10 * SS, fill=bingkai)
    d.rectangle([x1, y1, x2, y2], fill=cfg["kaca"])
    if cfg["bintang"]:
        for (sx, sy) in ((0.15, 0.2), (0.55, 0.12), (0.8, 0.35), (0.3, 0.62), (0.7, 0.7), (0.9, 0.15)):
            r = 4 * SS
            d.ellipse([x1 + (x2 - x1) * sx - r, y1 + (y2 - y1) * sy - r,
                       x1 + (x2 - x1) * sx + r, y1 + (y2 - y1) * sy + r], fill=(255, 230, 150))
    if cfg["matahari"]:
        r = 60 * SS
        cxs, cys = x1 + (x2 - x1) * 0.3, y1 + (y2 - y1) * 0.72
        d.ellipse([cxs - r, cys - r, cxs + r, cys + r], fill=cfg["matahari"])
    if tema == "pagi":
        for (sx, sy, rr) in ((0.25, 0.3, 36), (0.4, 0.28, 28), (0.7, 0.55, 40), (0.82, 0.52, 28)):
            r = rr * SS
            d.ellipse([x1 + (x2 - x1) * sx - r, y1 + (y2 - y1) * sy - r * 0.6,
                       x1 + (x2 - x1) * sx + r, y1 + (y2 - y1) * sy + r * 0.6], fill=(255, 255, 255, 230))
    d.line([((x1 + x2) // 2, y1), ((x1 + x2) // 2, y2)], fill=bingkai, width=10 * SS)
    d.line([(x1, (y1 + y2) // 2), (x2, (y1 + y2) // 2)], fill=bingkai, width=10 * SS)
    # rak buku
    rx1, rx2, ry = int(W * 0.06 * SS), int(W * 0.40 * SS), int(H * 0.30 * SS)
    d.rectangle([rx1, ry, rx2, ry + 12 * SS], fill=bingkai)
    warna_buku = [(176, 84, 80), (86, 120, 160), (200, 170, 90), (96, 140, 110), (150, 100, 150)]
    x = rx1 + 16 * SS
    i = 0
    while x < rx2 - 40 * SS:
        lebar = (28 + (i * 7) % 18) * SS
        tinggi = (70 + (i * 13) % 40) * SS
        d.rectangle([x, ry - tinggi, x + lebar, ry], fill=warna_buku[i % 5])
        x += lebar + 4 * SS
        i += 1
    # jam dinding
    cx, cy, r = int(W * 0.84 * SS), int(H * 0.10 * SS), int(W * 0.05 * SS)
    d.ellipse([cx - r - 8 * SS, cy - r - 8 * SS, cx + r + 8 * SS, cy + r + 8 * SS], fill=bingkai)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(236, 228, 214) if tema != "malam" else (34, 30, 38))
    tangan = (60, 50, 50) if tema != "malam" else (255, 205, 80)
    d.line([(cx, cy), (cx, cy - r * 0.62)], fill=tangan, width=5 * SS)
    d.line([(cx, cy), (cx + r * 0.5, cy + r * 0.2)], fill=tangan, width=5 * SS)
    # lampu gantung + cahaya
    lx = int(W * 0.50)
    d.line([(lx * SS, 0), (lx * SS, int(H * 0.07) * SS)], fill=bingkai, width=4 * SS)
    glow(img, lx, H * 0.12, W * 0.62, warna=cfg["glow"][0], kuat=cfg["glow"][1])
    d.pieslice([(lx - 70) * SS, int(H * 0.07) * SS, (lx + 70) * SS, int(H * 0.07 + 120) * SS],
               180, 360, fill=cfg["lampu"])
    d.ellipse([(lx - 20) * SS, int(H * 0.07 + 40) * SS, (lx + 20) * SS, int(H * 0.07 + 80) * SS], fill=(255, 245, 200))


# ---------------------------------------------------------------- LATAR TAMBAHAN (pastel, selaras karakter)
import random as _random

LATAR_DESKRIPSI = {
    "kamar_pagi": "kamar siang hari yang tenang (cocok: refleksi diri, kebiasaan sehari-hari)",
    "kamar_sore": "kamar suasana sore hangat (cocok: perenungan, kelelahan)",
    "kamar_malam": "kamar malam hari (cocok: overthinking, susah tidur, kecemasan)",
    "kafe": "kafe, ngobrol santai dengan teman (cocok: hubungan, pertemanan, people pleasing)",
    "jalan": "jalan kota saat sore (cocok: kesibukan, tekanan hidup, membandingkan diri)",
    "taman": "taman terbuka yang lega (cocok: ketenangan, self-care, batasan diri)",
    "kelas": "ruang kelas / kampus (cocok: belajar, menunda-nunda, perfeksionisme, tekanan akademik)",
}


def _grad(d, y1, y2, c1, c2):
    a, b = int(y1 * SS), int(y2 * SS)
    for y in range(a, b):
        d.line([(0, y), (W * SS, y)], fill=lerp(c1, c2, (y - a) / max(1, b - a)))


def _rect(d, x1, y1, x2, y2, fill, r=0):
    d.rounded_rectangle([x1 * SS, y1 * SS, x2 * SS, y2 * SS], radius=r * SS, fill=fill)


def _ell(d, cx, cy, rx, ry, fill):
    d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=fill)


def _awan(d, cx, cy, skala=1.0, warna=(255, 255, 255, 235)):
    for dx, dy, rx, ry in ((0, 0, 90, 38), (-70, 12, 60, 30), (72, 10, 66, 32), (20, -22, 60, 34)):
        _ell(d, cx + dx * skala, cy + dy * skala, rx * skala, ry * skala, warna)


def _lantai_kayu(d, y1, c1, c2, garis=(40, 28, 22, 90)):
    _grad(d, y1, H, c1, c2)
    top = int(y1 * SS)
    for i in range(1, 9):
        y = top + int((H * SS - top) * (i / 9) ** 1.4)
        d.line([(0, y), (W * SS, y)], fill=garis, width=SS * 3)


def latar_kafe(img):
    d = ImageDraw.Draw(img, "RGBA")
    lantai = H * 0.77
    _grad(d, 0, lantai / 1, (246, 230, 206), (232, 208, 178))
    _rect(d, 0, H * 0.50, W, lantai, (156, 184, 156))
    _rect(d, 0, H * 0.50 - 8, W, H * 0.50 + 6, (122, 98, 76))
    for x in range(60, W, 140):
        d.line([(x * SS, int(H * 0.52 * SS)), (x * SS, int(lantai * SS))], fill=(170, 198, 170, 200), width=SS * 3)
    _lantai_kayu(d, lantai, (180, 136, 98), (142, 102, 74))
    d.rectangle([0, int(lantai * SS) - 8 * SS, W * SS, int(lantai * SS) + 2 * SS], fill=(110, 82, 62))
    # jendela kiri
    _rect(d, 50, H * 0.15, 480, H * 0.44, (116, 88, 64), 8)
    _rect(d, 66, H * 0.15 + 16, 464, H * 0.44 - 16, (198, 232, 246))
    _awan(d, 190, H * 0.21, 0.6)
    for cx, r, c in ((120, 60, (104, 170, 110)), (250, 74, (86, 152, 100)), (390, 56, (112, 176, 116))):
        _ell(d, cx, H * 0.44 - 14, r, r * 0.8, c)
    d.line([(265 * SS, int((H * 0.15 + 16) * SS)), (265 * SS, int((H * 0.44 - 16) * SS))], fill=(116, 88, 64), width=8 * SS)
    d.line([(66 * SS, int(H * 0.295 * SS)), (464 * SS, int(H * 0.295 * SS))], fill=(116, 88, 64), width=8 * SS)
    # papan menu
    _rect(d, 600, H * 0.16, 1030, H * 0.34, (122, 92, 66), 8)
    _rect(d, 614, H * 0.16 + 14, 1016, H * 0.34 - 14, (50, 78, 66))
    for i, w in enumerate((260, 200, 300, 160)):
        _rect(d, 650, H * 0.205 + i * 38, 650 + w, H * 0.205 + i * 38 + 8, (240, 238, 226, 210), 4)
    _ell(d, 940, H * 0.255, 34, 28, (240, 238, 226, 0))
    d.arc([906 * SS, int(H * 0.235 * SS), 974 * SS, int(H * 0.285 * SS)], 0, 180, fill=(240, 238, 226), width=5 * SS)
    # rak cangkir
    _rect(d, 590, H * 0.41, 1040, H * 0.41 + 12, (118, 88, 64), 3)
    for i, c in enumerate(((220, 120, 110), (240, 200, 110), (120, 170, 210), (200, 150, 200), (130, 190, 140), (236, 150, 90))):
        _rect(d, 620 + i * 66, H * 0.41 - 40, 656 + i * 66, H * 0.41, c, 5)
    # lampu gantung
    for x, panjang in ((270, 0.07), (560, 0.10), (850, 0.07)):
        d.line([(x * SS, 0), (x * SS, int(H * panjang * SS))], fill=(90, 70, 56), width=4 * SS)
        glow(img, x, H * panjang + 50, 300, warna=(255, 200, 110), kuat=0.33)
        d.pieslice([(x - 62) * SS, int(H * panjang * SS), (x + 62) * SS, int((H * panjang + 100) * SS)], 180, 360, fill=(232, 164, 78))
        _ell(d, x, H * panjang + 52, 16, 16, (255, 244, 200))
    # tanaman pot di kiri
    _rect(d, 30, lantai - 70, 120, lantai + 20, (200, 120, 90), 8)
    for dx, dy, rx, ry in ((75, -150, 28, 70), (40, -120, 24, 56), (110, -120, 24, 56), (75, -190, 22, 50)):
        _ell(d, 30 + dx - 30, lantai + dy, rx, ry, (96, 160, 104))


def latar_jalan(img):
    d = ImageDraw.Draw(img, "RGBA")
    rg = _random.Random(11)
    _grad(d, 0, H * 0.66, (146, 194, 240), (255, 216, 176))
    glow(img, 790, H * 0.37, 330, warna=(255, 236, 190), kuat=0.55)
    _ell(d, 790, H * 0.37, 100, 100, (255, 240, 196))
    _awan(d, 200, H * 0.16, 0.9)
    _awan(d, 880, H * 0.11, 0.7)
    dasar = H * 0.67
    for lapis, (warna, tmin, tmax, lebar) in enumerate((((170, 176, 214), 0.20, 0.36, 130), ((126, 136, 184), 0.32, 0.50, 150))):
        x = -30 if lapis == 0 else 20
        while x < W:
            t = rg.uniform(tmin, tmax) * H
            _rect(d, x, dasar - t, x + lebar, dasar + 4, warna)
            for wy in range(int(dasar - t + 24), int(dasar - 30), 52):
                for wx in range(int(x + 16), int(x + lebar - 24), 38):
                    if rg.random() < 0.55:
                        _rect(d, wx, wy, wx + 18, wy + 26, (255, 240, 192) if rg.random() < 0.6 else (110, 124, 170))
            x += lebar + rg.randint(6, 24)
    for x in (260, 560, 940):
        _rect(d, x - 7, dasar - 70, x + 7, dasar + 4, (110, 84, 62))
        _ell(d, x, dasar - 90, 50, 46, (104, 168, 116))
    # trotoar + jalan
    _rect(d, 0, dasar, W, H * 0.86, (216, 210, 202))
    for i in range(1, 9):
        y = dasar + (H * 0.86 - dasar) * (i / 9) ** 1.5
        d.line([(0, int(y * SS)), (W * SS, int(y * SS))], fill=(190, 184, 176, 190), width=SS * 3)
    _rect(d, 0, H * 0.86, W, H * 0.875, (170, 166, 160))
    _grad(d, H * 0.875, H, (92, 98, 110), (72, 78, 90))
    for x in range(30, W, 200):
        _rect(d, x, H * 0.94, x + 110, H * 0.945, (246, 232, 170), 3)
    # tiang lampu
    for x in (110, 970):
        _rect(d, x - 6, H * 0.30, x + 6, dasar + 10, (64, 68, 86))
        _rect(d, x - 40, H * 0.30 - 10, x + 8, H * 0.30 + 4, (64, 68, 86), 4)
        _ell(d, x - 34, H * 0.30 + 12, 18, 12, (255, 236, 170))


def latar_taman(img):
    d = ImageDraw.Draw(img, "RGBA")
    rg = _random.Random(5)
    _grad(d, 0, H * 0.62, (148, 204, 244), (226, 244, 252))
    glow(img, 880, H * 0.12, 260, warna=(255, 244, 190), kuat=0.5)
    _ell(d, 880, H * 0.12, 62, 62, (255, 244, 188))
    _awan(d, 220, H * 0.15, 0.9)
    _awan(d, 640, H * 0.26, 0.7)
    _ell(d, 220, H * 0.70, 760, H * 0.17, (150, 206, 142))
    _ell(d, 920, H * 0.72, 800, H * 0.2, (120, 184, 116))
    for x, h, r in ((90, 220, 120), (980, 260, 130), (760, 150, 80), (400, 120, 70)):
        _rect(d, x - 14, H * 0.66 - h, x + 14, H * 0.68, (122, 86, 62), 4)
        _ell(d, x, H * 0.66 - h - r * 0.4, r, r * 0.9, (86, 156, 96))
        _ell(d, x - r * 0.4, H * 0.66 - h - r * 0.1, r * 0.6, r * 0.55, (108, 176, 112))
    _grad(d, H * 0.70, H, (126, 192, 106), (94, 162, 84))
    pts = [(W * 0.38 * SS, H * 0.70 * SS), (W * 0.62 * SS, H * 0.70 * SS), (W * 1.12 * SS, H * SS), (-W * 0.12 * SS, H * SS)]
    d.polygon(pts, fill=(234, 216, 172, 235))
    for _ in range(70):
        x, y = rg.randint(0, W), rg.randint(int(H * 0.72), H)
        if W * 0.30 < x < W * 0.70 and y < H * 0.9:
            continue
        _ell(d, x, y, 7, 7, rg.choice([(250, 176, 190), (255, 240, 170), (255, 255, 255), (200, 170, 240)]))


def latar_kelas(img):
    d = ImageDraw.Draw(img, "RGBA")
    lantai = H * 0.77
    _grad(d, 0, lantai, (238, 242, 228), (220, 228, 208))
    _lantai_kayu(d, lantai, (208, 174, 134), (176, 140, 104))
    d.rectangle([0, int(lantai * SS) - 8 * SS, W * SS, int(lantai * SS) + 2 * SS], fill=(150, 116, 86))
    _rect(d, 120, H * 0.13, 960, H * 0.41, (142, 106, 72), 10)
    _rect(d, 136, H * 0.13 + 16, 944, H * 0.41 - 16, (58, 108, 90))
    for i, w in enumerate((420, 300, 520)):
        _rect(d, 190, H * 0.185 + i * 46, 190 + w, H * 0.185 + i * 46 + 9, (240, 242, 232, 215), 4)
    d.arc([700 * SS, int(H * 0.27 * SS), 800 * SS, int(H * 0.34 * SS)], 200, 500, fill=(240, 242, 232), width=7 * SS)
    _rect(d, 120, H * 0.41, 960, H * 0.41 + 14, (118, 86, 58), 4)
    for x in (260, 330, 420):
        _rect(d, x, H * 0.41 - 12, x + 38, H * 0.41, (246, 236, 214), 3)
    _ell(d, 540, H * 0.075, 52, 52, (122, 92, 66))
    _ell(d, 540, H * 0.075, 44, 44, (246, 242, 230))
    d.line([(540 * SS, int(H * 0.075 * SS)), (540 * SS, int((H * 0.075 - 30) * SS))], fill=(60, 50, 50), width=4 * SS)
    d.line([(540 * SS, int(H * 0.075 * SS)), (562 * SS, int((H * 0.075 + 8) * SS))], fill=(60, 50, 50), width=4 * SS)
    _rect(d, 30, H * 0.17, 100, H * 0.27, (255, 226, 150), 4)
    _rect(d, 980, H * 0.20, 1050, H * 0.30, (250, 190, 200), 4)
    for x0 in (-40, 760):  # meja belakang
        _rect(d, x0, lantai - 130, x0 + 360, lantai - 100, (190, 142, 98), 6)
        _rect(d, x0 + 30, lantai - 100, x0 + 46, lantai + 4, (140, 104, 76))
        _rect(d, x0 + 314, lantai - 100, x0 + 330, lantai + 4, (140, 104, 76))


def latar(img, nama):
    if nama.startswith("kamar_"):
        latar_kamar(img, nama.split("_", 1)[1])
    elif nama == "kafe":
        latar_kafe(img)
    elif nama == "jalan":
        latar_jalan(img)
    elif nama == "taman":
        latar_taman(img)
    elif nama == "kelas":
        latar_kelas(img)
    else:
        latar_kamar(img, "pagi")


# ---------------------------------------------------------------- ELEMEN
def balon(img, x, y, w, h, baris=4):
    d = ImageDraw.Draw(img, "RGBA")
    box = [x * SS, y * SS, (x + w) * SS, (y + h) * SS]
    d.rounded_rectangle(box, radius=30 * SS, fill=(250, 240, 224))
    for i in range(baris):
        yy = (y + 38 + i * (h - 76) / max(1, baris - 1)) * SS
        lebar = w - 80 - (40 if i == baris - 1 else 0)
        d.rounded_rectangle([(x + 40) * SS, yy - 4 * SS, (x + 40 + lebar) * SS, yy + 4 * SS],
                            radius=4 * SS, fill=(70, 62, 66))
    d.ellipse([(x + w * 0.18) * SS, (y + h + 14) * SS, (x + w * 0.18 + 30) * SS, (y + h + 44) * SS],
              fill=(250, 240, 224))
    d.ellipse([(x + w * 0.12) * SS, (y + h + 52) * SS, (x + w * 0.12 + 16) * SS, (y + h + 68) * SS],
              fill=(250, 240, 224))


def teks_besar(img, teks, cx, cy, ukuran=170, sudut=-5, warna=(255, 205, 50)):
    tmp = Image.new("RGBA", (W * SS, 400 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    f = font(ukuran * SS)
    lebar = d.textlength(teks, font=f)
    if lebar > 920 * SS:  # kecilkan otomatis kalau kepanjangan
        ukuran = int(ukuran * 920 * SS / lebar)
        f = font(ukuran * SS)
        lebar = d.textlength(teks, font=f)
    d.text(((W * SS - lebar) / 2, 100 * SS), teks, font=f, fill=warna, stroke_width=10 * SS,
           stroke_fill=(20, 14, 18))
    tmp = tmp.rotate(sudut, resample=Image.BICUBIC, center=(W * SS / 2, 200 * SS))
    img.alpha_composite(tmp, (int(cx * SS - W * SS / 2), int(cy * SS - 200 * SS)))


# ---------------------------------------------------------------- IKON ILUSTRASI + BALON DIALOG
OUTLINE = (52, 42, 56)

IKON_DESKRIPSI = {
    "otak": "otak (pikiran, overthinking)", "hati": "hati (perasaan, kasih sayang)",
    "hati_patah": "hati patah (kecewa, ditolak)", "jam": "jam alarm (waktu, menunda)",
    "ponsel": "ponsel dengan notifikasi (media sosial, FOMO)", "kalender": "kalender (jadwal, tenggat)",
    "lampu": "lampu ide (solusi, kesadaran)", "gembok": "gembok (batasan, menahan diri)",
    "perisai": "perisai (perlindungan, rasa aman)", "centang": "centang hijau (benar, berhasil)",
    "silang": "silang merah (salah, menolak)", "petir": "petir (stres, kaget)",
    "baterai": "baterai hampir habis (lelah, burnout)", "buku": "tumpukan buku (belajar, beban)",
    "kopi": "kopi (santai, istirahat)", "api": "api (burnout, amarah)",
}


def _kontur(layer, tebal):
    """Beri garis tepi gelap di sekeliling bentuk (alpha) pada layer RGBA."""
    a = layer.getchannel("A")
    ukuran = int(tebal) * 2 + 1
    lebar = a.filter(ImageFilter.MaxFilter(ukuran if ukuran % 2 else ukuran + 1))
    dasar = Image.new("RGBA", layer.size, OUTLINE + (0,))
    dasar.putalpha(lebar)
    dasar.alpha_composite(layer)
    return dasar


def gambar_ikon(nama, ukuran=300):
    S3 = 3
    px = ukuran * S3
    k = px / 100.0
    fill = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(fill)
    detail = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    dd = ImageDraw.Draw(detail)

    def P(x, y):  # ada margin 6% supaya garis tepi tidak terpotong
        return ((6 + 0.88 * x) * k, (6 + 0.88 * y) * k)

    def box(x1, y1, x2, y2):
        return [P(x1, y1), P(x2, y2)]

    def poly(pts, **kw):
        d.polygon([P(x, y) for x, y in pts], **kw)

    def garis(pts, w, warna=OUTLINE, di=None):
        (di or dd).line([P(x, y) for x, y in pts], fill=warna, width=int(w * k), joint="curve")

    if nama in ("hati", "hati_patah"):
        c = (236, 84, 104)
        d.ellipse(box(15, 18, 55, 58), fill=c)
        d.ellipse(box(45, 18, 85, 58), fill=c)
        poly([(17, 46), (83, 46), (50, 88)], fill=c)
        d.ellipse(box(22, 24, 34, 36), fill=(255, 150, 160))
        if nama == "hati_patah":
            garis([(52, 20), (44, 40), (56, 52), (46, 70), (52, 84)], 3.4)
    elif nama == "otak":
        c = (244, 150, 172)
        for cx, cy, rx, ry in ((36, 44, 24, 24), (64, 44, 24, 24), (50, 36, 26, 20), (42, 62, 20, 18), (60, 62, 20, 18)):
            d.ellipse(box(cx - rx, cy - ry, cx + rx, cy + ry), fill=c)
        d.rectangle(box(46, 70, 54, 86), fill=(214, 120, 144))
        garis([(50, 22), (50, 66)], 2.6)
        garis([(30, 38), (40, 46), (32, 56)], 2.6)
        garis([(70, 38), (60, 46), (68, 56)], 2.6)
    elif nama == "jam":
        d.ellipse(box(8, 8, 36, 34), fill=(236, 90, 90))
        d.ellipse(box(64, 8, 92, 34), fill=(236, 90, 90))
        d.ellipse(box(12, 14, 88, 90), fill=(252, 246, 232))
        garis([(50, 52), (50, 30)], 4.2)
        garis([(50, 52), (66, 60)], 4.2)
        dd.ellipse(box(46, 48, 54, 56), fill=OUTLINE)
    elif nama == "ponsel":
        d.rounded_rectangle(box(28, 6, 72, 94), radius=8 * k, fill=(70, 76, 100))
        d.rounded_rectangle(box(33, 16, 67, 82), radius=3 * k, fill=(196, 226, 248))
        d.ellipse(box(60, 4, 84, 28), fill=(236, 70, 70))
        dd.rounded_rectangle(box(38, 30, 62, 36), radius=2 * k, fill=(120, 150, 190))
        dd.rounded_rectangle(box(38, 44, 58, 50), radius=2 * k, fill=(120, 150, 190))
    elif nama == "kalender":
        d.rounded_rectangle(box(12, 18, 88, 90), radius=6 * k, fill=(255, 252, 244))
        d.rounded_rectangle(box(12, 18, 88, 40), radius=6 * k, fill=(236, 90, 90))
        d.rectangle(box(12, 32, 88, 40), fill=(236, 90, 90))
        for x in (30, 70):
            d.rounded_rectangle(box(x - 4, 8, x + 4, 28), radius=3 * k, fill=(96, 100, 120))
        for r in range(3):
            for c in range(4):
                dd.rectangle(box(20 + c * 17, 48 + r * 14, 28 + c * 17, 54 + r * 14), fill=(150, 156, 176))
    elif nama == "lampu":
        d.ellipse(box(24, 10, 76, 66), fill=(255, 224, 98))
        poly([(38, 58), (62, 58), (58, 78), (42, 78)], fill=(190, 196, 210))
        d.rounded_rectangle(box(40, 78, 60, 90), radius=3 * k, fill=(150, 156, 172))
        d.ellipse(box(32, 20, 44, 32), fill=(255, 246, 190))
        for ang in ((14, 16, 6, 8), (86, 16, 94, 8), (6, 40, 0, 40), (94, 40, 100, 40)):
            garis([(ang[0], ang[1]), (ang[2], ang[3])], 3.2, (255, 190, 60), dd)
    elif nama == "gembok":
        d.arc(box(28, 12, 72, 62), 180, 360, fill=(140, 146, 164), width=int(9 * k))
        d.rectangle(box(28, 36, 34, 52), fill=(140, 146, 164))
        d.rectangle(box(66, 36, 72, 52), fill=(140, 146, 164))
        d.rounded_rectangle(box(20, 44, 80, 92), radius=8 * k, fill=(250, 196, 84))
        dd.ellipse(box(44, 58, 56, 70), fill=OUTLINE)
        dd.rectangle(box(48, 66, 52, 80), fill=OUTLINE)
    elif nama == "perisai":
        poly([(50, 6), (88, 20), (84, 58), (50, 94), (16, 58), (12, 20)], fill=(96, 150, 230))
        poly([(50, 16), (76, 26), (73, 54), (50, 82), (27, 54), (24, 26)], fill=(138, 186, 250))
        garis([(36, 50), (47, 62), (66, 38)], 5, (255, 255, 255))
    elif nama == "centang":
        d.ellipse(box(8, 8, 92, 92), fill=(98, 200, 120))
        garis([(28, 52), (43, 67), (72, 34)], 10, (255, 255, 255))
    elif nama == "silang":
        d.ellipse(box(8, 8, 92, 92), fill=(236, 92, 92))
        garis([(32, 32), (68, 68)], 10, (255, 255, 255))
        garis([(68, 32), (32, 68)], 10, (255, 255, 255))
    elif nama == "petir":
        poly([(58, 4), (20, 54), (46, 54), (36, 96), (82, 38), (54, 38)], fill=(255, 214, 64))
    elif nama == "baterai":
        d.rounded_rectangle(box(8, 28, 82, 74), radius=7 * k, fill=(250, 250, 246))
        d.rounded_rectangle(box(82, 42, 94, 60), radius=3 * k, fill=(250, 250, 246))
        d.rounded_rectangle(box(14, 34, 32, 68), radius=3 * k, fill=(236, 80, 80))
    elif nama == "buku":
        d.rounded_rectangle(box(10, 60, 90, 86), radius=4 * k, fill=(236, 120, 100))
        d.rounded_rectangle(box(16, 36, 84, 60), radius=4 * k, fill=(92, 140, 214))
        d.rounded_rectangle(box(22, 12, 78, 36), radius=4 * k, fill=(250, 200, 90))
        for y in (73, 48, 24):
            dd.rectangle(box(24, y - 2, 60, y + 2), fill=(255, 255, 255))
    elif nama == "kopi":
        d.ellipse(box(66, 38, 92, 64), outline=(250, 250, 246), width=int(7 * k))
        poly([(20, 34), (74, 34), (68, 80), (26, 80)], fill=(250, 250, 246))
        d.ellipse(box(12, 80, 88, 94), fill=(226, 190, 150))
        poly([(23, 42), (71, 42), (69, 52), (25, 52)], fill=(150, 96, 70))
        for x in (36, 52):
            garis([(x, 26), (x - 5, 18), (x + 5, 10), (x, 2)], 3, (190, 196, 210), dd)
    elif nama == "api":
        poly([(50, 4), (70, 32), (86, 58), (78, 86), (50, 96), (22, 86), (14, 58), (32, 36), (40, 52)], fill=(255, 140, 60))
        poly([(50, 40), (64, 62), (60, 84), (50, 90), (40, 84), (36, 64)], fill=(255, 214, 90))
    else:
        d.ellipse(box(10, 10, 90, 90), fill=(200, 200, 210))

    hasil = _kontur(fill, int(3.4 * k))
    hasil.alpha_composite(detail)
    return hasil.resize((ukuran, ukuran), Image.LANCZOS)


def tempel_ikon(img, nama, cx, cy, ukuran=260):
    ik = gambar_ikon(nama, ukuran * SS // SS)
    ik = ik.resize((ukuran * SS, ukuran * SS), Image.LANCZOS)
    img.alpha_composite(ik, (int(cx * SS - ik.width / 2), int(cy * SS - ik.height / 2)))


def balon_dialog(img, teks, cx, puncak, jenis="ucap", maks_lebar=640, ukuran=50):
    """Balon ucapan / pikiran berisi tulisan, diletakkan di atas kepala tokoh (cx, puncak dalam px output)."""
    d = ImageDraw.Draw(img, "RGBA")
    f = font(ukuran * SS)
    kata, baris, cur = teks.split(), [], ""
    for kt in kata:
        coba = (cur + " " + kt).strip()
        if d.textlength(coba, font=f) <= (maks_lebar - 90) * SS:
            cur = coba
        else:
            baris.append(cur)
            cur = kt
    baris.append(cur)
    lh = int(ukuran * 1.32 * SS)
    lebar = int(max(d.textlength(b, font=f) for b in baris)) + 90 * SS
    tinggi = lh * len(baris) + 60 * SS
    x = min(max(cx * SS - lebar / 2, 28 * SS), W * SS - 28 * SS - lebar)
    y = max(puncak * SS - tinggi - 120 * SS, 40 * SS)
    krm = (255, 252, 244)
    tb = 6 * SS
    if jenis == "pikir":
        bentuk = [(x, y, x + lebar, y + tinggi)]
        jumlah = max(4, int(lebar / (64 * SS)))
        gel = []
        for i in range(jumlah):
            bx = x + 40 * SS + (lebar - 80 * SS) * i / (jumlah - 1)
            gel.append((bx, y + 4 * SS, 34 * SS))
            gel.append((bx, y + tinggi - 4 * SS, 34 * SS))
        for pass_ in (0, 1):
            ex = tb if pass_ == 0 else 0
            warna = OUTLINE if pass_ == 0 else krm
            d.rounded_rectangle([x - ex, y - ex, x + lebar + ex, y + tinggi + ex], radius=40 * SS, fill=warna)
            for bx, by, r in gel:
                d.ellipse([bx - r - ex, by - r - ex, bx + r + ex, by + r + ex], fill=warna)
        tx, ty = cx * SS, puncak * SS - 16 * SS
        for r, dy in ((22, 100), (15, 62), (9, 30)):
            ccx = cx * SS
            ccy = y + tinggi + dy * SS * 0.8 + 4 * SS
            d.ellipse([ccx - r * SS - tb, ccy - r * SS - tb, ccx + r * SS + tb, ccy + r * SS + tb], fill=OUTLINE)
            d.ellipse([ccx - r * SS, ccy - r * SS, ccx + r * SS, ccy + r * SS], fill=krm)
    else:
        d.rounded_rectangle([x - tb, y - tb, x + lebar + tb, y + tinggi + tb], radius=38 * SS, fill=OUTLINE)
        ekor_x = min(max(cx * SS, x + 70 * SS), x + lebar - 70 * SS)
        ekor = [(ekor_x - 34 * SS, y + tinggi - 6 * SS), (ekor_x + 34 * SS, y + tinggi - 6 * SS),
                (cx * SS, y + tinggi + 78 * SS)]
        d.polygon([(a - (0 if i else 0), b) for i, (a, b) in enumerate(ekor)], fill=OUTLINE)
        d.polygon([(ekor_x - 26 * SS, y + tinggi - 8 * SS), (ekor_x + 26 * SS, y + tinggi - 8 * SS),
                   (cx * SS, y + tinggi + 66 * SS)], fill=krm)
        d.rounded_rectangle([x, y, x + lebar, y + tinggi], radius=34 * SS, fill=krm)
        d.polygon([(ekor_x - 28 * SS, y + tinggi - 10 * SS), (ekor_x + 28 * SS, y + tinggi - 10 * SS),
                   (ekor_x + 20 * SS, y + tinggi + 10 * SS), (ekor_x - 20 * SS, y + tinggi + 10 * SS)], fill=krm)
    ty = y + 30 * SS
    for b in baris:
        w = d.textlength(b, font=f)
        d.text((x + (lebar - w) / 2, ty), b, font=f, fill=OUTLINE)
        ty += lh


def selesai_rgba(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


def selesai(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS).convert("RGB")


# ---------------------------------------------------------------- CONTOH
def contoh_scene(path="contoh_scene.png"):
    img = Image.new("RGBA", (W * SS, H * SS))
    latar_kamar(img)
    ground = int(H * 0.835)
    karakter(img, int(W * 0.30), ground, 600, "sedih", "dagu")
    karakter(img, int(W * 0.72), ground, 570, "kaget", "angkat",
             hoodie=(196, 92, 84), rambut=(70, 44, 40), gaya="cepol", kacamata=True)
    balon(img, 560, 330, 420, 210)
    teks_besar(img, "DIAM.", W * 0.30, 330)
    selesai(img).save(path)


def lembar_ekspresi(path="lembar_ekspresi.png"):
    lebar, tinggi = 1500, 560
    img = Image.new("RGBA", (lebar * SS, tinggi * SS), (46, 38, 44, 255))
    d = ImageDraw.Draw(img)
    daftar = [("netral", "turun"), ("kaget", "angkat"), ("sedih", "dagu"), ("marah", "tunjuk"), ("senang", "turun")]
    f = font(28 * SS)
    for i, (eks, leng) in enumerate(daftar):
        cx = 150 + i * 300
        karakter(img, cx, 500, 380, eks, leng)
        t = f"{eks} + {leng}"
        d.text((cx * SS - d.textlength(t, font=f) / 2, 515 * SS), t, font=f, fill=(230, 220, 210))
    img.resize((lebar, tinggi), Image.LANCZOS).convert("RGB").save(path)


if __name__ == "__main__":
    contoh_scene()
    lembar_ekspresi()
    print("Selesai: contoh_scene.png dan lembar_ekspresi.png")
