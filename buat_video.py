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
import subprocess
import time
import urllib.parse
from pathlib import Path

import edge_tts
import requests
from PIL import Image, ImageDraw, ImageFont

API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip().strip('"\'') or None
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
MODEL_CADANGAN = ["gemini-2.5-flash-lite", "gemini-3-flash-preview", "gemini-3.1-flash-lite", "gemini-2.0-flash"]
VOICE = "id-ID-ArdiNeural"  # suara cowok. Ganti "id-ID-GadisNeural" untuk cewek
W, H = 1080, 1920
WORK = Path("work")
OUT = Path("output")
HISTORY = Path("used_topics.json")


def pilih_font(size):
    kandidat = [
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for p in kandidat:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def baca_riwayat():
    if HISTORY.exists():
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    return []


def tulis_naskah(riwayat):
    if not API_KEY:
        raise SystemExit("GEMINI_API_KEY belum di-set.")
    sudah = "; ".join(riwayat[-40:]) or "(belum ada)"
    prompt = f"""Kamu kreator konten Reels Instagram berbahasa Indonesia.
Buat SATU video fakta unik yang menarik dan BENAR (bisa diverifikasi, jangan mengarang).
Topik yang sudah pernah dipakai, JANGAN diulang: {sudah}

Aturan:
- 6 scene. Scene 1 adalah hook yang bikin penasaran.
- Narasi tiap scene 1-2 kalimat pendek, gaya santai, maksimal 25 kata.
- Scene terakhir ajak penonton follow.
- image_prompt dalam bahasa Inggris, visual jelas, tanpa teks/huruf di gambar, tanpa orang terkenal.
- keyword: 1-3 kata Inggris SANGAT umum untuk cari foto stok (contoh: "jellyfish", "deep ocean", "microscope", "clock").
- Total narasi sekitar 35-50 detik jika dibaca.

Balas HANYA JSON dengan format:
{{"topik": "...", "caption": "caption IG singkat + emoji", "hashtags": ["#faktaunik", "..."],
 "scenes": [{{"narasi": "...", "image_prompt": "...", "keyword": "..."}}]}}"""
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0},
    }
    daftar_model = [MODEL] + [m for m in MODEL_CADANGAN if m != MODEL]
    teks = None
    for m in daftar_model:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
        # key dikirim lewat header supaya tidak muncul di pesan error
        r = requests.post(url, json=body, headers={"x-goog-api-key": API_KEY}, timeout=120)
        if r.status_code == 200:
            print("   Model dipakai:", m)
            teks = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            break
        print(f"   Model {m} gagal ({r.status_code}): {r.text[:200]}")
    if teks is None:
        raise SystemExit("Semua model gagal. Cek API key / kuota di aistudio.google.com")
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


def bikin_frame(gambar_path, narasi, bg_path, teks_path):
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
    img.save(bg_path)

    # lapisan teks transparan (gradasi gelap di bawah + subtitle)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(layer)
    for y in range(int(H * 0.50), H):
        a = int(215 * (y - H * 0.50) / (H * 0.50))
        od.line([(0, y), (W, y)], fill=(0, 0, 0, min(a, 215)))
    font = pilih_font(66)
    baris = bungkus(od, narasi, font, W - 160)
    y = int(H * 0.70)
    for b in baris:
        lebar = od.textlength(b, font=font)
        od.text(((W - lebar) / 2, y), b, font=font, fill="white", stroke_width=6, stroke_fill="black")
        y += 84
    layer.save(teks_path)


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


def durasi(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def jalan(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
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
        teks = WORK / f"teks{i}.png"
        suara = WORK / f"voice{i}.mp3"
        mp4 = WORK / f"scene{i}.mp4"

        bikin_gambar(sc, gambar, i)
        bikin_frame(gambar, sc["narasi"], bg, teks)
        asyncio.run(bikin_suara(sc["narasi"], suara))
        dur = durasi(suara) + 0.4
        n = int(dur * 30) + 1
        # zoom pelan (Ken Burns), arah selang-seling per scene
        if i % 2:
            z = "min(1.0+0.0010*on,1.20)"
        else:
            z = "max(1.20-0.0010*on,1.0)"
        filt = (
            f"[0:v]scale=1620:2880,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={n}:s={W}x{H}:fps=30[bg];[bg][1:v]overlay=0:0,format=yuv420p[v]"
        )
        jalan([
            "ffmpeg", "-y", "-i", str(bg), "-loop", "1", "-i", str(teks), "-i", str(suara),
            "-filter_complex", filt, "-map", "[v]", "-map", "2:a",
            "-af", "apad", "-t", f"{dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", str(mp4),
        ])
        klip.append(mp4)

    print("3/4 Menggabungkan scene...")
    daftar = WORK / "list.txt"
    daftar.write_text("".join(f"file '{k.name}'\n" for k in klip), encoding="utf-8")
    hasil = OUT / "reel.mp4"
    jalan([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(daftar),
        "-c", "copy", "-movflags", "+faststart", str(hasil),
    ])

    print("4/4 Menyimpan caption...")
    caption = data["caption"].strip() + "\n\n" + " ".join(data["hashtags"])
    (OUT / "meta.json").write_text(
        json.dumps({"topik": data["topik"], "caption": caption}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    riwayat.append(data["topik"])
    HISTORY.write_text(json.dumps(riwayat, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Selesai! Cek:", hasil.resolve())


if __name__ == "__main__":
    main()
