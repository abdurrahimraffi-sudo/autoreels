"""
Pabrik video "Fakta Unik" (gratis, bahasa Indonesia).
Alur: Gemini (naskah) -> Pollinations (gambar) -> edge-tts (suara) -> Pillow (teks) -> FFmpeg (rakit)

Butuh: Python 3.10+, FFmpeg, dan:
    pip install edge-tts pillow requests
API key Gemini (gratis): https://aistudio.google.com/apikey
    Windows (CMD):  set GEMINI_API_KEY=isi_key_lu
Jalankan:  python buat_video.py
Hasil: folder output/ (reel.mp4 dan meta.json)
"""
import asyncio
import json
import os
import random
import re
import subprocess
import time
from datetime import datetime, timezone
import urllib.parse
from pathlib import Path

import edge_tts
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip().strip('"\'') or None
MODEL = (os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash").strip()
MODEL_CADANGAN = ["gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-3.1-flash-lite"]
VOICE = "id-ID-ArdiNeural"  # suara cowok. Ganti "id-ID-GadisNeural" untuk cewek
W, H = 1080, 1920
WORK = Path("work")
OUT = Path("output")
HISTORY = Path("used_topics.json")


def cari_montserrat():
    """Cari file Montserrat apa pun di folder script / folder kerja / folder fonts."""
    folder = Path(__file__).resolve().parent
    lokasi = [folder, Path("."), Path("fonts"), folder / "fonts"]
    urutan = ["extrabold", "bold", "semibold", "medium"]
    temuan = []
    for lok in lokasi:
        if lok.exists():
            temuan += [f for f in lok.glob("*.ttf") if "montserrat" in f.name.lower()]
    # utamakan bobot tebal, abaikan versi italic
    for kunci in urutan:
        for f in temuan:
            n = f.name.lower()
            if kunci in n.replace("-", "").replace("_", "") and "italic" not in n:
                return f
    for f in temuan:  # font variabel, mis. Montserrat[wght].ttf
        if "italic" not in f.name.lower():
            return f
    return None


def pilih_font(size):
    mont = cari_montserrat()
    if mont:
        try:
            font = ImageFont.truetype(str(mont), size)
            n = mont.name.lower()
            if "wght" in n or "variable" in n:
                try:
                    font.set_variation_by_axes([800])  # ExtraBold
                except Exception:
                    pass
            return font
        except Exception:
            pass
    for p in [
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ]:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def baca_riwayat():
    if HISTORY.exists():
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    return []


def tulis_naskah(riwayat):
    if not API_KEY:
        raise SystemExit("GEMINI_API_KEY belum di-set.")
    sudah = "; ".join(riwayat[-40:]) or "(belum ada)"
    prompt = f"""Kamu kreator Reels Instagram Indonesia yang jago bikin video fakta unik yang bikin orang nonton sampai habis.
Pilih SATU topik yang BENAR dan bisa diverifikasi (jangan mengarang). Variasikan kategori: sains, hewan, tubuh manusia, luar angkasa, sejarah, teknologi, psikologi, alam, makanan.
Topik yang sudah pernah dipakai, JANGAN diulang: {sudah}

Struktur:
- Scene 1 adalah HOOK: kalimat pembuka yang mengejutkan atau bikin penasaran. Jangan pakai sapaan basa-basi seperti "halo guys".
- Total 9 scene. Tiap scene SATU kalimat pendek (maksimal 14 kata), gaya bercerita santai, ada detail atau plot twist yang mengejutkan, dan alurnya saling nyambung.
- Scene terakhir: pertanyaan untuk memancing komentar, lalu ajak follow.
- judul_hook: 2-5 kata KAPITAL untuk teks besar di awal video.
- kata_kunci: SATU kata penting dari narasi scene itu (persis sama ejaannya) untuk disorot warna emas.
- image_prompt: bahasa Inggris, visual jelas, tanpa teks/huruf di gambar, tanpa orang terkenal.
- keyword: 1-3 kata Inggris SANGAT umum untuk cari foto stok (contoh: "jellyfish", "deep ocean", "microscope", "clock").

Aturan caption (field "caption"): 2-3 kalimat yang membahas HANYA fakta pada video ini, bukan topik lain: kalimat
pembuka menggugah, inti faktanya, lalu pertanyaan ajakan komentar. Boleh 1-2 emoji. Tulis caption TERAKHIR.

Balas HANYA JSON dengan format (caption dan hashtags di paling akhir):
{{"topik": "...", "judul_hook": "...",
 "scenes": [{{"narasi": "...", "kata_kunci": "...", "image_prompt": "...", "keyword": "..."}}],
 "caption": "caption sesuai fakta video ini", "hashtags": ["#faktaunik", "..."]}}"""
    return panggil_gemini(prompt)


def model_tersedia():
    """Tanya Google model apa saja yang bisa dipakai key ini (flash terbaru lebih dulu)."""
    try:
        r = requests.get("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200",
                         headers={"x-goog-api-key": API_KEY}, timeout=30)
        nama = [m["name"].split("/", 1)[1] for m in r.json().get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", [])]
    except Exception:
        return []
    buang = ("image", "tts", "audio", "live", "embedding", "robotics", "computer", "vision", "native")

    def kunci(n):
        v = re.search(r"gemini-(\d+(?:\.\d+)?)", n)
        return (-(float(v.group(1)) if v else 0), "lite" in n, n)

    return sorted([n for n in nama if "flash" in n and not any(x in n for x in buang)], key=kunci)


def panggil_gemini(prompt):
    if not API_KEY:
        raise SystemExit("GEMINI_API_KEY belum di-set.")
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0},
    }
    antrian = [MODEL] + [m for m in MODEL_CADANGAN if m != MODEL]
    dicoba, daftar_api_diambil, teks = set(), False, None
    while antrian and teks is None:
        m = antrian.pop(0)
        if m in dicoba:
            continue
        dicoba.add(m)
        pesan = ""
        for percobaan in range(3):  # model sibuk (503/429): tunggu lalu ulangi model yang sama
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
            # key lewat header supaya tidak muncul di pesan error
            r = requests.post(url, json=body, headers={"x-goog-api-key": API_KEY}, timeout=120)
            if r.status_code == 200:
                print("   Model dipakai:", m)
                teks = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                break
            pesan = r.text
            print(f"   Model {m} gagal ({r.status_code}): {pesan[:160].strip()}")
            if r.status_code in (429, 500, 502, 503, 504) and percobaan < 2:
                time.sleep(10 * (percobaan + 1))
                continue
            break
        if teks is not None:
            break
        # Google sering menyebut model pengganti di pesan error -> coba itu dulu
        for saran in re.findall(r"models/([A-Za-z0-9.\-]+)", pesan)[::-1]:
            if saran not in dicoba:
                antrian.insert(0, saran)
        # kehabisan kandidat -> minta daftar model terbaru langsung dari Google
        if not antrian and not daftar_api_diambil:
            daftar_api_diambil = True
            antrian += [n for n in model_tersedia() if n not in dicoba]
    if teks is None:
        raise SystemExit("Semua model Gemini gagal. Cek API key / kuota di aistudio.google.com "
                         "atau coba lagi nanti (mungkin sedang sibuk).")
    return json.loads(teks)


PEXELS_KEY = os.environ.get("PEXELS_API_KEY")
PIXABAY_KEY = (os.environ.get("PIXABAY_API_KEY") or "").strip().strip('"\'') or None


def gambar_pixabay(keyword, path, nomor):
    if not PIXABAY_KEY:
        return False
    try:
        r = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": PIXABAY_KEY, "q": keyword, "image_type": "photo",
                "orientation": "vertical", "safesearch": "true",
                "per_page": 20, "min_height": 1200,
            },
            timeout=60,
        )
        hits = r.json().get("hits", [])
        if not hits:
            return False
        pilih = hits[(nomor + random.randint(0, 3)) % len(hits)]
        img = requests.get(pilih["largeImageURL"], timeout=120)
        path.write_bytes(img.content)
        Image.open(path).verify()
        return True
    except Exception as e:
        print("  pixabay gagal:", e)
        return False


def gambar_pexels(keyword, path, nomor):
    if not PEXELS_KEY:
        return False
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": keyword, "orientation": "portrait", "per_page": 15},
            headers={"Authorization": PEXELS_KEY},
            timeout=60,
        )
        foto = r.json().get("photos", [])
        if not foto:
            return False
        pilih = foto[(nomor + random.randint(0, 3)) % len(foto)]
        img = requests.get(pilih["src"]["large2x"], timeout=120)
        path.write_bytes(img.content)
        Image.open(path).verify()
        return True
    except Exception as e:
        print("  pexels gagal:", e)
        return False


def gambar_pollinations(prompt, path, seed):
    full = prompt + ", cinematic, vertical, high detail, no text"
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(full)
        + f"?width={W}&height={H}&nologo=true&seed={seed}"
    )
    for percobaan in range(3):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                path.write_bytes(r.content)
                Image.open(path).verify()
                return True
            print("  pollinations status", r.status_code)
        except Exception as e:
            print("  pollinations gagal:", e)
        time.sleep(8 * (percobaan + 1))
    return False


def bikin_gambar(sc, path, nomor):
    kw = sc.get("keyword") or sc["image_prompt"]
    if gambar_pexels(kw, path, nomor) or gambar_pixabay(kw, path, nomor):
        return
    if gambar_pollinations(sc["image_prompt"], path, random.randint(1, 99999)):
        time.sleep(6)
        return
    print("  pakai background gradasi")
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    c1 = (random.randint(20, 90), random.randint(20, 90), random.randint(60, 160))
    c2 = (10, 10, 30)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    img.save(path)


def bungkus(draw, teks, font, lebar_maks):
    kata, baris, cur = teks.split(), [], ""
    for k in kata:
        coba = (cur + " " + k).strip()
        if draw.textlength(coba, font=font) <= lebar_maks:
            cur = coba
        else:
            baris.append(cur)
            cur = k
    if cur:
        baris.append(cur)
    return baris


KUNING = (255, 221, 0)


def bikin_bg(gambar_path, bg_path):
    """Crop 9:16 + gradasi gelap di bawah (teks ditambah terpisah, per kata)."""
    img = Image.open(gambar_path).convert("RGB")
    rasio = W / H
    w, h = img.size
    if w / h > rasio:
        nw = int(h * rasio)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / rasio)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    img = img.resize((W, H))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(layer)
    for y in range(int(H * 0.52), H):
        a = int(190 * (y - H * 0.52) / (H * 0.48))
        od.line([(0, y), (W, y)], fill=(0, 0, 0, min(a, 190)))
    Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB").save(bg_path)


def png_teks(teks, path, ukuran, warna, y_frac, stroke):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    font = pilih_font(ukuran)
    baris = bungkus(d, teks, font, W - 140)
    y = int(H * y_frac)
    for b in baris:
        lebar = d.textlength(b, font=font)
        d.text(((W - lebar) / 2, y), b, font=font, fill=warna,
               stroke_width=stroke, stroke_fill="black")
        y += int(ukuran * 1.25)
    layer.save(path)


EMAS = (255, 200, 60)
GAYA = (os.environ.get("TEKS_GAYA") or "elegan").strip().lower()


def norm_kata(k):
    return "".join(ch for ch in k.lower() if ch.isalnum())


def png_teks_elegan(teks, path, ukuran, y_frac, aksen=None):
    """Putih + bayangan halus + garis tipis; satu kata kunci berwarna emas."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bayang = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ds = ImageDraw.Draw(bayang)
    font = pilih_font(ukuran)
    spasi = d.textlength(" ", font=font)
    aksen_n = norm_kata(aksen) if aksen else None
    y = int(H * y_frac)
    for baris in bungkus(d, teks, font, W - 160):
        kata = baris.split()
        total = sum(d.textlength(k, font=font) for k in kata) + spasi * (len(kata) - 1)
        x = (W - total) / 2
        for k in kata:
            warna = EMAS if aksen_n and norm_kata(k) == aksen_n else "white"
            ds.text((x, y + 8), k, font=font, fill=(0, 0, 0, 210))
            d.text((x, y), k, font=font, fill=warna, stroke_width=3, stroke_fill=(0, 0, 0, 255))
            x += d.textlength(k, font=font) + spasi
        y += int(ukuran * 1.32)
    bayang = bayang.filter(ImageFilter.GaussianBlur(8))
    Image.alpha_composite(bayang, layer).save(path)


def bagi_kata(narasi, maks_kata=4, maks_huruf=22):
    """Pecah narasi jadi potongan pendek (gaya subtitle video pendek)."""
    hasil, cur = [], []
    for k in narasi.split():
        cur.append(k)
        if len(cur) >= maks_kata or len(" ".join(cur)) >= maks_huruf:
            hasil.append(" ".join(cur))
            cur = []
    if cur:
        if hasil and len(cur) == 1:
            hasil[-1] += " " + cur[0]
        else:
            hasil.append(" ".join(cur))
    return hasil


async def bikin_suara(teks, path):
    # bersihkan karakter yang kadang bikin edge-tts menolak
    bersih = " ".join(teks.replace("&", " dan ").replace("*", "").replace("#", "").split())
    percobaan = [
        (VOICE, "+5%"),
        (VOICE, "+0%"),
        ("id-ID-GadisNeural", "+0%"),
        (VOICE, "+0%"),
    ]
    for n, (voice, rate) in enumerate(percobaan, 1):
        try:
            await edge_tts.Communicate(bersih, voice, rate=rate).save(str(path))
            if Path(path).exists() and Path(path).stat().st_size > 1000:
                return
        except Exception as e:
            print(f"  suara gagal (percobaan {n}): {type(e).__name__}")
        await asyncio.sleep(3 * n)
    raise SystemExit(
        "Suara gagal terus. Jalankan: pip install -U edge-tts  lalu coba lagi."
    )


def cek_ffmpeg():
    """Pastikan FFmpeg terpasang; beri pesan yang jelas kalau tidak."""
    import shutil
    if not shutil.which("ffmpeg"):
        raise SystemExit("FFmpeg belum terpasang di mesin ini. Di GitHub: tambahkan langkah "
                         "'sudo apt-get install -y ffmpeg'. Di Windows: 'winget install ffmpeg'.")


def durasi(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        return float(r.stdout.strip())
    except FileNotFoundError:
        # ffprobe tidak ada -> baca durasi lewat ffmpeg
        cek_ffmpeg()
        r = subprocess.run(["ffmpeg", "-i", str(path)], capture_output=True, text=True)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr)
        if not m:
            raise SystemExit("Gagal membaca durasi audio/video.")
        h, mi, sec = m.groups()
        return int(h) * 3600 + int(mi) * 60 + float(sec)


def jalan(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    cek_ffmpeg()
    OUT.mkdir(exist_ok=True)
    for f in (OUT / "meta.json", OUT / "reel.mp4"):  # buang sisa video sebelumnya
        f.unlink(missing_ok=True)
    WORK.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    riwayat = baca_riwayat()

    print("1/4 Menulis naskah...")
    data = tulis_naskah(riwayat)
    print("   Topik:", data["topik"])

    klip = []
    for i, sc in enumerate(data["scenes"], 1):
        print(f"2/4 Scene {i}/{len(data['scenes'])}...")
        gambar = WORK / f"img{i}.jpg"
        bg = WORK / f"bg{i}.png"
        suara = WORK / f"voice{i}.mp3"
        mp4 = WORK / f"scene{i}.mp4"

        bikin_gambar(sc, gambar, i)
        bikin_bg(gambar, bg)
        asyncio.run(bikin_suara(sc["narasi"], suara))
        adur = durasi(suara)
        dur = adur + 0.35
        n = int(dur * 30) + 1

        # subtitle kuning per potongan kata, waktunya mengikuti panjang kata
        potongan = bagi_kata(sc["narasi"])
        total = sum(len(c) + 1 for c in potongan)
        t = 0.05
        overlay = []
        for k, c in enumerate(potongan):
            d_c = (adur - 0.05) * (len(c) + 1) / total
            akhir = dur if k == len(potongan) - 1 else t + d_c
            png = WORK / f"cap{i}_{k}.png"
            if GAYA == "kuning":
                png_teks(c, png, 84, KUNING, 0.64, 9)
            else:
                png_teks_elegan(c, png, 78, 0.64, sc.get("kata_kunci"))
            overlay.append((png, t, akhir))
            t += d_c
        if i == 1 and data.get("judul_hook"):
            png = WORK / "hook.png"
            if GAYA == "kuning":
                png_teks(data["judul_hook"].upper(), png, 112, "white", 0.14, 10)
            else:
                png_teks_elegan(data["judul_hook"].upper(), png, 104, 0.14)
            overlay.append((png, 0.0, 2.8))

        if i % 2:
            z = "min(1.0+0.0010*on,1.22)"
        else:
            z = "max(1.22-0.0010*on,1.0)"
        filt = (
            f"[0:v]scale=1620:2880,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={n}:s={W}x{H}:fps=30,eq=saturation=1.18:contrast=1.06[v0]"
        )
        for k, (png, a0, a1) in enumerate(overlay, 1):
            filt += f";[v{k-1}][{k}:v]overlay=0:0:enable='between(t,{a0:.2f},{a1:.2f})'[v{k}]"
        filt += f";[v{len(overlay)}]format=yuv420p[vout]"

        cmd = ["ffmpeg", "-y", "-i", str(bg)]
        for png, _, _ in overlay:
            cmd += ["-i", str(png)]
        cmd += ["-i", str(suara)]
        cmd += [
            "-filter_complex", filt, "-map", "[vout]", "-map", f"{len(overlay) + 1}:a",
            "-af", "apad", "-t", f"{dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", str(mp4),
        ]
        jalan(cmd)
        klip.append(mp4)

    print("3/4 Menggabungkan scene...")
    daftar = WORK / "list.txt"
    daftar.write_text("".join(f"file '{k.name}'\n" for k in klip), encoding="utf-8")
    hasil = OUT / "reel.mp4"
    mentah = WORK / "mentah.mp4"
    jalan([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(daftar),
        "-c", "copy", str(mentah),
    ])
    musik = Path("musik.mp3")
    if musik.exists():
        print("   Menambah musik latar (musik.mp3)...")
        jalan([
            "ffmpeg", "-y", "-i", str(mentah), "-stream_loop", "-1", "-i", str(musik),
            "-filter_complex",
            "[1:a]volume=0.14[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0,volume=2[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
            "-shortest", "-movflags", "+faststart", str(hasil),
        ])
    else:
        jalan(["ffmpeg", "-y", "-i", str(mentah), "-c", "copy", "-movflags", "+faststart", str(hasil)])

    print("4/4 Menyimpan caption...")
    caption = data["caption"].strip() + "\n\n" + " ".join(data["hashtags"])
    (OUT / "meta.json").write_text(
        json.dumps({"topik": data["topik"], "judul_hook": data.get("judul_hook", ""), "caption": caption,
                    "dibuat": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "run": os.environ.get("GITHUB_RUN_ID", "")}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    riwayat.append(data["topik"])
    HISTORY.write_text(json.dumps(riwayat, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Selesai! Cek:", hasil.resolve())


if __name__ == "__main__":
    main()
