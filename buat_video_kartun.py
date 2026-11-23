"""
Mesin video KARTUN (konten psikologi populer).
Alur: Gemini (naskah + arahan adegan) -> karakter.py (gambar karakter acak) -> edge-tts (suara)
      -> FFmpeg (gerak, balon, teks besar, subtitle) -> output/reel.mp4 + meta.json

Pakai:   python buat_video_kartun.py          (butuh GEMINI_API_KEY)
Contoh:  python buat_video_kartun.py --demo   (naskah contoh, tanpa Gemini & tanpa suara)
File pendamping di folder yang sama: buat_video.py, karakter.py
"""
import asyncio
import json
import os
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image

import buat_video as bv
import karakter as kr

W, H = bv.W, bv.H
WORK, OUT, HISTORY = bv.WORK, bv.OUT, bv.HISTORY
DEMO = "--demo" in sys.argv

HOODIE = [(38, 166, 154), (196, 92, 84), (72, 110, 190), (150, 100, 190),
          (226, 160, 56), (90, 150, 90), (210, 100, 150), (96, 104, 128)]
RAMBUT = [(36, 30, 40), (70, 44, 40), (120, 80, 50), (30, 40, 70), (150, 60, 50)]
KULIT = [(255, 232, 208), (240, 204, 170), (214, 168, 128), (172, 120, 88)]

DISCLAIMER = "Edukasi umum, bukan pengganti konsultasi dengan psikolog atau tenaga profesional."


# ------------------------------------------------------------------ NASKAH
def tulis_naskah(riwayat, aksi_A=None, aksi_B=None, jenis_B="teman"):
    sudah = "; ".join(riwayat[-40:]) or "(belum ada)"
    if aksi_A:
        semua = sorted(set(aksi_A) | set(aksi_B or []))
        daftar = "\n".join(f"  - {n}: {kr.AKSI_DESKRIPSI.get(n, n)}" for n in semua)
        field_aksi = (f"- aksi_A / aksi_B: pose tokoh, pilih HANYA dari daftar ini (sesuaikan dengan emosi narasi, "
                      f"variasikan, jangan sama dua scene berturut-turut):\n{daftar}")
    else:
        field_aksi = ("- ekspresi_A / ekspresi_B: netral, kaget, sedih, marah, senang\n"
                      "- pose_A / pose_B: turun, angkat, dagu, tunjuk")
    daftar_latar = "\n".join(f"  - {n}: {d}" for n, d in kr.LATAR_DESKRIPSI.items())
    daftar_ikon = "\n".join(f"  - {n}: {d}" for n, d in kr.IKON_DESKRIPSI.items())
    prompt = f"""Kamu penulis konten edukasi psikologi populer untuk Reels Instagram berbahasa Indonesia.
Gayanya cerita animasi dengan dua tokoh: A (tokoh utama, laki-laki berhoodie merah) dan B ({jenis_B}, lawan bicara A).
Pilih SATU topik psikologi umum yang akurat dan dikenal (contoh: people pleasing, overthinking, burnout,
batasan diri, gaya kelekatan, imposter syndrome, menunda-nunda, membandingkan diri, FOMO, perfeksionisme).
Variasikan topiknya. Topik yang sudah dipakai, JANGAN diulang: {sudah}

Aturan keselamatan (wajib):
- Bahas sebagai kecenderungan umum ("sering kali", "banyak orang"). Jangan mendiagnosis siapa pun.
- Jangan klaim menyembuhkan, jangan menyebut obat atau terapi tertentu sebagai solusi pasti.
- Jangan menyudutkan kelompok tertentu. Jangan mengarang riset atau angka.

Struktur: 10 scene. Scene 1 adalah HOOK yang bikin penasaran. Tiap narasi SATU kalimat, maksimal 16 kata,
gaya santai. Scene terakhir: pertanyaan untuk komentar + ajakan follow.
Tokoh A tampil di hampir semua scene; B muncul hanya di scene yang butuh lawan bicara.

Tiap scene punya field:
- narasi
- tokoh: ["A"] atau ["B"] atau ["A","B"]
{field_aksi}
- kata_besar: 1-3 kata KAPITAL berakhiran titik untuk momen penting (contoh "DIAM."), selain itu "" (maksimal 4 scene)
- balon: true/false (balon di atas kepala tokoh). Pakai di maksimal 5 scene.
- jenis_balon: "ucap" (tokoh bicara) atau "pikir" (tokoh berpikir dalam hati)
- dialog: isi balon, kalimat pendek maksimal 12 kata, gaya santai, diucapkan/dipikirkan tokoh itu.
  Wajib diisi jika balon true. JANGAN sama dengan narasi (narasi = penutur, dialog = suara tokoh).
- bicara: "A" atau "B" (siapa yang punya balon)
- ikon: nama ikon ilustrasi yang memperkuat makna scene, atau "" (maksimal 5 scene), hanya dari daftar:
{daftar_ikon}
- kata_kunci: SATU kata dari narasi (persis ejaannya) untuk disorot emas

Pilih juga SATU latar untuk seluruh video yang paling cocok dengan topik, hanya dari daftar ini:
{daftar_latar}

Balas HANYA JSON:
{{"topik": "...", "latar": "salah satu nama latar", "judul_hook": "2-5 kata KAPITAL", "caption": "caption IG singkat + emoji",
 "hashtags": ["#psikologi", "..."], "scenes": [{{"narasi": "...", "tokoh": ["A"], "aksi_A": "netral",
 "kata_besar": "", "balon": false, "jenis_balon": "ucap", "dialog": "", "bicara": "A", "ikon": "",
 "kata_kunci": "..."}}]}}"""
    return bv.panggil_gemini(prompt)


NASKAH_DEMO = {
    "topik": "Susah Bilang Tidak (people pleasing)",
    "latar": "kafe",
    "judul_hook": "SUSAH BILANG TIDAK?",
    "caption": "Pernah iya-in padahal capek banget? Ceritanya ada di sini \U0001F447",
    "hashtags": ["#psikologi", "#peoplepleasing", "#selfgrowth", "#edukasi"],
    "scenes": [
        {"narasi": "Pernah nggak, kamu iya-in permintaan orang padahal sebenarnya capek banget?",
         "tokoh": ["A"], "aksi_A": "sedih", "kata_besar": "", "balon": False, "bicara": "A",
         "ikon": "baterai", "kata_kunci": "capek"},
        {"narasi": "Dalam psikologi, kebiasaan ini sering disebut people pleasing.",
         "tokoh": ["A", "B"], "aksi_A": "netral", "aksi_B": "senang", "kata_besar": "PEOPLE PLEASING.",
         "balon": False, "bicara": "B", "ikon": "", "kata_kunci": "people"},
        {"narasi": "Bukan karena kamu lemah, tapi sering kali karena takut ditolak.",
         "tokoh": ["A"], "aksi_A": "malu", "kata_besar": "", "balon": True, "jenis_balon": "ucap",
         "dialog": "Iya deh, aku bisa kok bantuin kamu.", "bicara": "A", "ikon": "hati_patah",
         "kata_kunci": "takut"},
        {"narasi": "Otak kita menganggap penolakan sosial mirip sebuah ancaman.",
         "tokoh": ["A", "B"], "aksi_A": "kaget", "aksi_B": "berpikir", "kata_besar": "ANCAMAN.",
         "balon": False, "bicara": "A", "ikon": "otak", "kata_kunci": "ancaman"},
        {"narasi": "Jadi mengiyakan terasa jauh lebih aman, walau hati sebenarnya berat.",
         "tokoh": ["A"], "aksi_A": "berpikir", "kata_besar": "LEBIH AMAN.", "balon": True,
         "jenis_balon": "pikir", "dialog": "Kalau aku nolak, dia kecewa nggak ya?", "bicara": "A",
         "ikon": "perisai", "kata_kunci": "aman"},
        {"narasi": "Masalahnya, makin sering bilang iya, makin menumpuk lelah yang nggak terlihat.",
         "tokoh": ["A"], "aksi_A": "bosan", "kata_besar": "", "balon": False, "bicara": "A",
         "ikon": "buku", "kata_kunci": "lelah"},
        {"narasi": "Banyak orang akhirnya merasa kesal pada dirinya sendiri.",
         "tokoh": ["A"], "aksi_A": "kesal", "kata_besar": "", "balon": True, "jenis_balon": "pikir",
         "dialog": "Kenapa sih aku susah bilang tidak?", "bicara": "A", "ikon": "api", "kata_kunci": "kesal"},
        {"narasi": "Mulailah dari hal kecil, misalnya bilang, aku pikirkan dulu ya.",
         "tokoh": ["A", "B"], "aksi_A": "menunjuk", "aksi_B": "senang", "kata_besar": "",
         "balon": True, "jenis_balon": "ucap", "dialog": "Aku pikirkan dulu ya.", "bicara": "A",
         "ikon": "jam", "kata_kunci": "kecil"},
        {"narasi": "Menolak dengan sopan bukan berarti kamu egois.",
         "tokoh": ["A"], "aksi_A": "girang", "kata_besar": "BOLEH.", "balon": False, "bicara": "A",
         "ikon": "centang", "kata_kunci": "egois"},
        {"narasi": "Menurutmu, apa yang paling susah kamu tolak? Tulis di komentar dan follow ya!",
         "tokoh": ["A", "B"], "aksi_A": "senang", "aksi_B": "girang", "kata_besar": "", "balon": False,
         "bicara": "A", "ikon": "hati", "kata_kunci": "komentar"},
    ],
}


AKSI_KE_KODE = {
    "netral": ("netral", "turun"), "sedih": ("sedih", "turun"), "senang": ("senang", "turun"),
    "marah": ("marah", "turun"), "kaget": ("kaget", "angkat"), "berpikir": ("netral", "dagu"),
    "bingung": ("netral", "dagu"), "malu": ("sedih", "turun"), "keren": ("senang", "tunjuk"),
    "girang": ("senang", "angkat"), "menunjuk": ("netral", "tunjuk"), "kesal": ("marah", "turun"),
    "bosan": ("netral", "dagu"), "terpuruk": ("sedih", "dagu"), "tidur": ("netral", "turun"),
    "mengantuk": ("netral", "turun"), "melamun": ("netral", "dagu"), "jalan": ("netral", "turun"),
    "belakang": ("netral", "turun"), "minum": ("senang", "turun"),
}


# ------------------------------------------------------------------ VALIDASI NASKAH
def validasi_naskah(data):
    """Rapikan & periksa naskah dari Gemini. Melempar ValueError kalau tidak layak dipakai."""
    if not isinstance(data, dict):
        raise ValueError("naskah bukan objek JSON")
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not (6 <= len(scenes) <= 14):
        raise ValueError("jumlah scene tidak sesuai")
    data["topik"] = str(data.get("topik") or "Psikologi").strip()
    data["judul_hook"] = str(data.get("judul_hook") or "").strip()
    data["caption"] = str(data.get("caption") or data["topik"]).strip()
    tag = data.get("hashtags")
    data["hashtags"] = [str(t) for t in tag][:10] if isinstance(tag, list) and tag else ["#psikologi", "#edukasi"]
    n_besar = n_balon = n_ikon = 0
    for sc in scenes:
        if not isinstance(sc, dict):
            raise ValueError("scene bukan objek")
        sc["narasi"] = " ".join(str(sc.get("narasi") or "").split())
        if len(sc["narasi"]) < 8:
            raise ValueError("narasi kosong/terlalu pendek")
        sc["narasi"] = sc["narasi"][:240]
        tokoh = [t for t in (sc.get("tokoh") or ["A"]) if t in ("A", "B")]
        sc["tokoh"] = tokoh or ["A"]
        kb = " ".join(str(sc.get("kata_besar") or "").split())
        if kb and n_besar < 4 and len(kb.split()) <= 3:
            sc["kata_besar"] = kb
            n_besar += 1
        else:
            sc["kata_besar"] = ""
        dialog = " ".join(str(sc.get("dialog") or "").split())
        if sc.get("balon") and dialog and n_balon < 5:
            sc["dialog"] = " ".join(dialog.split()[:14])
            sc["balon"] = True
            n_balon += 1
        else:
            sc["balon"], sc["dialog"] = False, ""
        if sc.get("jenis_balon") not in ("ucap", "pikir"):
            sc["jenis_balon"] = "ucap"
        ik = sc.get("ikon")
        if ik in kr.IKON_DESKRIPSI and n_ikon < 5:
            n_ikon += 1
        else:
            sc["ikon"] = ""
        kk = str(sc.get("kata_kunci") or "")
        sc["kata_kunci"] = kk if kk and kk.lower() in sc["narasi"].lower() else None
    return data


def ambil_naskah(riwayat, aksi_A, aksi_B, jenis_B, percobaan=3):
    terakhir = None
    for n in range(1, percobaan + 1):
        try:
            data = tulis_naskah(riwayat, aksi_A, aksi_B, jenis_B)
            return validasi_naskah(data)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            terakhir = e
            print(f"   Naskah percobaan {n} tidak layak ({type(e).__name__}: {e}), coba lagi...")
    raise SystemExit(f"Gemini gagal menghasilkan naskah yang layak setelah {percobaan} percobaan: {terakhir}")


# ------------------------------------------------------------------ KARAKTER ACAK
def acak_tokoh(rng):
    h1, h2 = rng.sample(HOODIE, 2)
    gaya = ["pendek", "cepol", "panjang"]
    g1 = rng.choice(gaya)
    g2 = rng.choice([g for g in gaya if g != g1])
    return {
        "A": dict(hoodie=h1, rambut=rng.choice(RAMBUT), gaya=g1, kacamata=rng.random() < 0.3,
                  kulit=rng.choice(KULIT)),
        "B": dict(hoodie=h2, rambut=rng.choice(RAMBUT), gaya=g2, kacamata=rng.random() < 0.5,
                  kulit=rng.choice(KULIT)),
    }


# ------------------------------------------------------------------ RENDER LAYER
def latar_png(tema):
    path = WORK / f"latar_{tema}.png"
    if not path.exists():
        img = Image.new("RGBA", (W * kr.SS, H * kr.SS))
        kr.latar(img, tema)
        kr.selesai(img).save(path)
    return path


def render_layer(i, sc, tokoh, rng, pilihan):
    """pilihan: {"A": nama_folder_aset | None, "B": ...}"""
    tampil = [t for t in (sc.get("tokoh") or ["A"]) if t in ("A", "B")] or ["A"]
    ground = int(H * 0.835)
    if len(tampil) == 1:
        tinggi, cx = 900, {tampil[0]: W // 2}
    else:
        tinggi, cx = 680, {"A": int(W * 0.28), "B": int(W * 0.74)}

    chars = Image.new("RGBA", (W * kr.SS, H * kr.SS), (0, 0, 0, 0))
    puncak = {}
    for t in tampil:
        aksi = sc.get(f"aksi_{t}") or kr.EKSPRESI_KE_AKSI.get(sc.get(f"ekspresi_{t}", "netral"), "netral")
        if pilihan.get(t):
            puncak[t] = kr.tempel_aset(chars, pilihan[t], aksi, cx[t], ground, tinggi)
        else:  # karakter gambar-kode (acak tampilan tiap video)
            eks, pose = AKSI_KE_KODE.get(aksi, ("netral", "turun"))
            eks = sc.get(f"ekspresi_{t}") or eks
            pose = sc.get(f"pose_{t}") or pose
            kr.karakter(chars, cx[t], ground, tinggi, eks, pose, **tokoh[t])
            puncak[t] = ground - tinggi
    p_char = WORK / f"chars{i}.png"
    kr.selesai_rgba(chars).save(p_char)

    p_bubble = None
    if sc.get("balon"):
        bicara = sc.get("bicara") if sc.get("bicara") in tampil else tampil[0]
        img = Image.new("RGBA", (W * kr.SS, H * kr.SS), (0, 0, 0, 0))
        dialog = (sc.get("dialog") or "").strip()
        if dialog:
            maks = 620 if len(tampil) == 1 else 520
            kr.balon_dialog(img, dialog, cx[bicara], puncak[bicara], sc.get("jenis_balon") or "ucap",
                            maks_lebar=maks, ukuran=50 if len(tampil) == 1 else 44)
        else:  # tanpa dialog -> balon berisi garis (placeholder)
            lebar, tinggi_b = (520, 210) if len(tampil) == 1 else (440, 200)
            bx = min(max(cx[bicara] - lebar // 2, 40), W - lebar - 40)
            kr.balon(img, bx, max(60, int(puncak[bicara]) - tinggi_b - 120), lebar, tinggi_b)
        p_bubble = WORK / f"balon{i}.png"
        kr.selesai_rgba(img).save(p_bubble)

    p_icon = None
    if sc.get("ikon") in kr.IKON_DESKRIPSI:
        img = Image.new("RGBA", (W * kr.SS, H * kr.SS), (0, 0, 0, 0))
        if len(tampil) == 1:
            kr.tempel_ikon(img, sc["ikon"], W * 0.80, H * 0.56, 250)
        else:
            kr.tempel_ikon(img, sc["ikon"], W * 0.50, H * 0.27, 200)
        p_icon = WORK / f"ikon{i}.png"
        kr.selesai_rgba(img).save(p_icon)

    p_text = None
    if sc.get("kata_besar"):
        img = Image.new("RGBA", (W * kr.SS, H * kr.SS), (0, 0, 0, 0))
        kr.teks_besar(img, sc["kata_besar"].upper(), W / 2, 200 if sc.get("balon") else 330,
                      sudut=rng.choice([-6, -4, 4, 6]))
        p_text = WORK / f"besar{i}.png"
        kr.selesai_rgba(img).save(p_text)
    return p_char, p_bubble, p_text, p_icon


# ------------------------------------------------------------------ SUARA
def siapkan_suara(narasi, path):
    if DEMO:
        n_kata = len(narasi.split())
        dur = max(2.8, n_kata * 0.34 + 0.6)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        "anullsrc=r=44100:cl=stereo", "-t", f"{dur:.2f}", "-q:a", "9", str(path)], check=True)
        return dur
    asyncio.run(bv.bikin_suara(narasi, path))
    return bv.durasi(path)


# ------------------------------------------------------------------ SCENE -> VIDEO
def bikin_scene(i, sc, tokoh, tema, rng, data, pilihan):
    bg = latar_png(tema)
    p_char, p_bubble, p_text, p_icon = render_layer(i, sc, tokoh, rng, pilihan)
    suara = WORK / f"voice{i}.mp3"
    adur = siapkan_suara(sc["narasi"], suara)
    dur = adur + 0.4
    n = int(dur * 30) + 1

    # subtitle bagian bawah (supaya tidak menabrak karakter)
    potongan = bv.bagi_kata(sc["narasi"])
    total = sum(len(c) + 1 for c in potongan)
    t, caps = 0.05, []
    for k, c in enumerate(potongan):
        d_c = (adur - 0.05) * (len(c) + 1) / total
        akhir = dur if k == len(potongan) - 1 else t + d_c
        png = WORK / f"cap{i}_{k}.png"
        bv.png_teks_elegan(c, png, 70, 0.858, sc.get("kata_kunci"))
        caps.append((png, t, akhir))
        t += d_c

    cmd = ["ffmpeg", "-y", "-i", str(bg),
           "-loop", "1", "-framerate", "30", "-t", f"{dur:.2f}", "-i", str(p_char)]
    idx = 2
    ib = it = ii = None
    if p_bubble:
        cmd += ["-loop", "1", "-framerate", "30", "-t", f"{dur:.2f}", "-i", str(p_bubble)]
        ib, idx = idx, idx + 1
    if p_text:
        cmd += ["-loop", "1", "-framerate", "30", "-t", f"{dur:.2f}", "-i", str(p_text)]
        it, idx = idx, idx + 1
    if p_icon:
        cmd += ["-loop", "1", "-framerate", "30", "-t", f"{dur:.2f}", "-i", str(p_icon)]
        ii, idx = idx, idx + 1
    cap_idx = []
    for png, a0, a1 in caps:
        cmd += ["-i", str(png)]
        cap_idx.append((idx, a0, a1))
        idx += 1
    cmd += ["-i", str(suara)]
    ia = idx

    f = (f"[0:v]scale=1296:2304,zoompan=z='min(1.0+0.08*on/{n},1.08)':x='iw/2-(iw/zoom/2)'"
         f":y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps=30[v0]")
    f += ";[1:v]format=rgba[c]"
    f += ";[v0][c]overlay=x=0:y='5*sin(2*PI*t/2.6)':eval=frame[v1]"
    cur, nomor = "v1", 2
    if ib is not None:
        f += (f";[{ib}:v]format=rgba,fade=t=in:st=0.25:d=0.25:alpha=1[b]"
              f";[{cur}][b]overlay=x=0:y='if(lt(t,0.25),30,30*max(0,1-(t-0.25)/0.25))':eval=frame[v{nomor}]")
        cur, nomor = f"v{nomor}", nomor + 1
    if it is not None:
        f += (f";[{it}:v]format=rgba,fade=t=in:st=0.55:d=0.2:alpha=1[x]"
              f";[{cur}][x]overlay=x=0:y='if(lt(t,0.55),-70,-70*max(0,1-(t-0.55)/0.25))':eval=frame[v{nomor}]")
        cur, nomor = f"v{nomor}", nomor + 1
    if ii is not None:
        f += (f";[{ii}:v]format=rgba,fade=t=in:st=0.5:d=0.25:alpha=1[ik]"
              f";[{cur}][ik]overlay=x=0:y='if(lt(t,0.5),50,50*max(0,1-(t-0.5)/0.3))+10*sin(2*PI*t/1.8)'"
              f":eval=frame[v{nomor}]")
        cur, nomor = f"v{nomor}", nomor + 1
    for ci, a0, a1 in cap_idx:
        f += f";[{cur}][{ci}:v]overlay=0:0:enable='between(t,{a0:.2f},{a1:.2f})'[v{nomor}]"
        cur, nomor = f"v{nomor}", nomor + 1
    f += f";[{cur}]format=yuv420p[vout]"

    mp4 = WORK / f"scene{i}.mp4"
    cmd += ["-filter_complex", f, "-map", "[vout]", "-map", f"{ia}:a", "-af", "apad", "-t", f"{dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", str(mp4)]
    bv.jalan(cmd)
    return mp4


def main():
    WORK.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    riwayat = bv.baca_riwayat()
    rng = random.Random()

    # pilih aset karakter: A tetap, lawan bicara B diacak (cowok / cewek) tiap video
    pilihan = {"A": None, "B": None}
    pakai_kode = "--karakter-kode" in sys.argv or (os.environ.get("GAYA_KARAKTER") or "").lower() == "kode"
    fa, fb = ([], []) if pakai_kode else (kr.daftar_folder("A"), kr.daftar_folder("B"))
    if pakai_kode:
        print("   Mode karakter: gambar-kode (acak tampilan)")
    if fa:
        pilihan["A"] = fa[0]
    if fb:
        pilihan["B"] = rng.choice(fb)
    jenis_B = "teman"
    if pilihan["B"] == "B1":
        jenis_B = "laki-laki bersweater hijau"
    elif pilihan["B"] == "B2":
        jenis_B = "perempuan berambut panjang bersweater pink"
    aksi_A = kr.aksi_tersedia(pilihan["A"]) if pilihan["A"] else None
    aksi_B = kr.aksi_tersedia(pilihan["B"]) if pilihan["B"] else None

    print("1/4 Menulis naskah...")
    data = validasi_naskah(json.loads(json.dumps(NASKAH_DEMO))) if DEMO else ambil_naskah(riwayat, aksi_A, aksi_B, jenis_B)
    print("   Topik:", data["topik"])
    if pilihan["A"] and not pilihan["B"]:
        for sc in data["scenes"]:  # tidak ada lawan bicara -> hanya tokoh A
            sc["tokoh"] = ["A"]
            sc["bicara"] = "A"
    if pilihan["A"]:
        print("   Aset karakter:", pilihan)

    tokoh = acak_tokoh(rng)
    tema = data.get("latar") if data.get("latar") in kr.LATAR_DESKRIPSI else rng.choice(list(kr.LATAR_DESKRIPSI))
    print("   Latar:", tema)

    klip = []
    for i, sc in enumerate(data["scenes"], 1):
        print(f"2/4 Scene {i}/{len(data['scenes'])}...")
        klip.append(bikin_scene(i, sc, tokoh, tema, rng, data, pilihan))

    print("3/4 Menggabungkan scene...")
    daftar = WORK / "list.txt"
    daftar.write_text("".join(f"file '{k.name}'\n" for k in klip), encoding="utf-8")
    hasil, mentah = OUT / "reel.mp4", WORK / "mentah.mp4"
    bv.jalan(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(daftar), "-c", "copy", str(mentah)])
    musik = Path("musik.mp3")
    if musik.exists():
        bv.jalan(["ffmpeg", "-y", "-i", str(mentah), "-stream_loop", "-1", "-i", str(musik),
                  "-filter_complex",
                  "[1:a]volume=0.14[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0,volume=2[a]",
                  "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest",
                  "-movflags", "+faststart", str(hasil)])
    else:
        bv.jalan(["ffmpeg", "-y", "-i", str(mentah), "-c", "copy", "-movflags", "+faststart", str(hasil)])

    print("4/4 Menyimpan caption...")
    caption = data["caption"].strip() + "\n\n" + DISCLAIMER + "\n\n" + " ".join(data["hashtags"])
    (OUT / "meta.json").write_text(
        json.dumps({"topik": data["topik"], "caption": caption}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    if not DEMO:
        riwayat.append(data["topik"])
        HISTORY.write_text(json.dumps(riwayat, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        total = bv.durasi(hasil)
        print(f"   Durasi video: {total:.1f} detik")
        if total > 85:
            print("   PERINGATAN: durasi di atas 85 detik, pertimbangkan naskah lebih pendek.")
    except Exception:
        pass
    print("Selesai! Cek:", hasil.resolve())


if __name__ == "__main__":
    main()
