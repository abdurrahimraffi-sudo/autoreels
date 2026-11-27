"""
Upload Reels ke Instagram lewat Graph API resmi.

Butuh env (di CMD, tanpa tanda kutip):
    set IG_USER_ID=17841426008652534
    set IG_ACCESS_TOKEN=token_lu
Pemakaian:
    python upload_ig.py URL_VIDEO_PUBLIK
Contoh:
    python upload_ig.py https://raw.githubusercontent.com/USERNAME/REPO/main/reel.mp4
Caption diambil dari output/meta.json (hasil buat_video.py).
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v27.0")


def bersih(v):
    return (v or "").strip().strip("\"'")


IG_USER_ID = bersih(os.environ.get("IG_USER_ID"))
TOKEN = bersih(os.environ.get("IG_ACCESS_TOKEN"))


def cek(r, langkah):
    """Tampilkan error dari Meta tanpa membocorkan token."""
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text[:300]}
    if r.status_code != 200 or "error" in data:
        err = data.get("error", data)
        raise SystemExit(f"[GAGAL] {langkah}: {json.dumps(err, ensure_ascii=False)[:600]}")
    return data


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Pakai: python upload_ig.py URL_VIDEO_PUBLIK")
    if not IG_USER_ID or not TOKEN:
        raise SystemExit("IG_USER_ID / IG_ACCESS_TOKEN belum di-set.")
    video_url = sys.argv[1]

    meta = Path("output/meta.json")
    caption, info = "", {}
    if meta.exists():
        info = json.loads(meta.read_text(encoding="utf-8"))
        caption = info.get("caption", "")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if run_id and info.get("run") != run_id:
        # di GitHub: caption wajib berasal dari run yang sama, supaya tidak memakai caption video lain
        raise SystemExit("[BERHENTI] output/meta.json bukan dari run ini (caption basi). Upload dibatalkan.")
    if info.get("dibuat") and not run_id:
        umur = datetime.now(timezone.utc) - datetime.fromisoformat(info["dibuat"])
        if umur.total_seconds() > 6 * 3600:
            print(f"PERINGATAN: meta.json dibuat {umur.total_seconds() / 3600:.0f} jam lalu, caption mungkin bukan untuk video ini.")
    print("Topik  :", info.get("topik", "(tidak ada)"))
    print("Caption:", caption[:200].replace("\n", " / "))

    # tunggu sampai URL video benar-benar bisa dibuka publik (GitHub Pages butuh waktu)
    ok = False
    for i in range(20):
        try:
            head = requests.get(video_url, stream=True, timeout=60)
            status = head.status_code
            head.close()
        except Exception as e:
            status = type(e).__name__
        print(f"Cek URL video ({i + 1}/20):", status)
        if status == 200:
            ok = True
            break
        time.sleep(15)
    if not ok:
        raise SystemExit("[GAGAL] URL video tidak bisa dibuka publik (harus status 200).")

    print("1/3 Membuat container Reels...")
    r = requests.post(
        f"{GRAPH}/{IG_USER_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": TOKEN,
        },
        timeout=120,
    )
    creation_id = cek(r, "buat container")["id"]
    print("   creation_id:", creation_id)

    print("2/3 Menunggu Instagram memproses video...")
    for i in range(40):  # maks sekitar 6-7 menit
        time.sleep(10)
        s = requests.get(
            f"{GRAPH}/{creation_id}",
            params={"fields": "status_code,status", "access_token": TOKEN},
            timeout=60,
        )
        info = cek(s, "cek status")
        kode = info.get("status_code")
        print("   status:", kode)
        if kode == "FINISHED":
            break
        if kode in ("ERROR", "EXPIRED"):
            raise SystemExit(f"[GAGAL] proses video: {info}")
    else:
        raise SystemExit("[GAGAL] timeout menunggu proses video.")

    print("3/3 Publish...")
    p = requests.post(
        f"{GRAPH}/{IG_USER_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": TOKEN},
        timeout=120,
    )
    media_id = cek(p, "publish")["id"]
    print("BERHASIL! Media ID:", media_id)


if __name__ == "__main__":
    main()
