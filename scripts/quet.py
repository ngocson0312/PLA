# -*- coding: utf-8 -*-
"""Bước 1 — quét (ban-do-tien-ich-nha-dat): audio → lời đọc có mốc từng chữ (faster-whisper large-v3) + số liệu trong
lời + tờ tài nguyên (ảnh + khung giữa mỗi clip nhà) + thông tin nhà (file người dùng đưa) + khung ke_hoach.json trống.

    python -I scripts/quet.py --audio <file> [--res <thư mục ảnh/clip nhà>] [--info <thong_tin.txt|.json|.md>]
                              [--work <thư mục>] [--model large-v3] [--kenh <kenh.json>]
"""
import argparse
import io
import os
import re
import sys
import time
import wave

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chung as C

ANH = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")
KHAC = (".pdf", ".docx", ".doc", ".xlsx", ".txt", ".md")
CLIP = (".mp4", ".mov", ".m4v", ".mkv", ".webm")


def khung_giua_clip(p):
    """khung giữa của clip → (ảnh PIL, giây) | (None, 0)"""
    import subprocess
    try:
        dai = C.probe(p)["duration"]
        r = subprocess.run([C.ffbin("ffmpeg"), "-v", "error", "-ss", "%.2f" % (dai / 2), "-i", p, "-frames:v", "1",
                            "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        import io as _io
        return Image.open(_io.BytesIO(r.stdout)).convert("RGB"), dai
    except Exception:
        return None, 0


def tach_wav(audio, wav):
    C.run([C.ffbin("ffmpeg"), "-v", "error", "-y", "-i", audio, "-vn", "-ac", "1", "-ar", "16000",
           "-c:a", "pcm_s16le", wav])
    if not os.path.isfile(wav) or os.path.getsize(wav) < 1024:
        C.die("tách tiếng thất bại: " + wav)


def doc_wav(path):
    """wav → mảng float32: đưa MẢNG cho Whisper, không đưa đường dẫn (PyAV 19 bỏ metadata_errors)"""
    with wave.open(path, "rb") as f:
        raw = f.readframes(f.getnframes())
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def nhan_dang(wav, model="large-v3", lang="vi"):
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        C.die("chưa cài faster-whisper (%s). Chạy: python -I -m pip install faster-whisper" % exc)
    m = None
    if os.environ.get("GVT_DEVICE", "").lower() != "cpu":
        try:
            import ctranslate2
            if ctranslate2.get_cuda_device_count() > 0:
                m = WhisperModel(model, device="cuda", compute_type="float16")
                list(m.transcribe(np.zeros(16000, np.float32), language=lang)[0])
                print("   nhận dạng trên GPU")
        except Exception as e:
            m = None
            print("   GPU không dùng được (%s) → CPU" % str(e).splitlines()[0][:80])
    if m is None:
        print("   nhận dạng trên CPU (int8) — lần đầu tải mô hình ~3 GB, chạy lâu, đừng huỷ")
        m = WhisperModel(model, device="cpu", compute_type="int8")
    t0 = time.time()
    segs, info = m.transcribe(doc_wav(wav), language=lang, word_timestamps=True, vad_filter=True, beam_size=5,
                              condition_on_previous_text=False)
    out_segs, flat = [], []
    for s in segs:
        words = []
        for w in (s.words or []):
            t = C.nfc(w.word.strip())
            if not t:
                continue
            it = {"w": t, "start": round(float(w.start), 3), "end": round(float(w.end), 3),
                  "p": round(float(getattr(w, "probability", 0.0) or 0.0), 3)}
            words.append(it)
            flat.append(it)
        out_segs.append({"start": round(float(s.start), 3), "end": round(float(s.end), 3),
                         "text": C.nfc(s.text.strip()), "words": words})
        print("   [%6.2f-%6.2f] %s" % (s.start, s.end, s.text.strip()))
    print("   xong sau %.0f s: %d câu, %d chữ" % (time.time() - t0, len(out_segs), len(flat)))
    if not flat:
        C.die("không nhận ra chữ nào — audio có tiếng nói không?")
    return out_segs, flat


def to_tai_nguyen(res, out_jpg):
    """mọi ảnh trong Resources → 1 tờ có tên file (Claude mở xem); file khác (pdf, docx…) liệt kê ra"""
    if not res or not os.path.isdir(res):
        return [], []
    anh, khac = [], []
    for root, _, files in os.walk(res):
        for f in sorted(files):
            p = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            if ext in ANH or ext in CLIP:
                anh.append(p)
            elif ext in KHAC:
                khac.append(p)
    if anh:
        n = len(anh)
        cols = 3 if n > 4 else 2 if n > 1 else 1
        cw, ch = 560, 560
        rows = (n + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cw, rows * (ch + 50)), (20, 24, 32))
        d = ImageDraw.Draw(sheet)
        f = C.font("semi", 26)
        for i, p in enumerate(anh):
            nhan = ""
            if os.path.splitext(p)[1].lower() in CLIP:
                im, dai = khung_giua_clip(p)
                if im is None:
                    continue
                nhan = " CLIP %.1f s" % dai
            else:
                try:
                    im = Image.open(p)
                    from PIL import ImageOps
                    im = ImageOps.exif_transpose(im).convert("RGB")
                except Exception:
                    continue
            ow, oh = im.size
            im = C.fit_in(im, cw - 16, ch - 16)
            x, y = (i % cols) * cw, (i // cols) * (ch + 50)
            sheet.paste(im, (x + 8 + (cw - 16 - im.width) // 2, y + 8 + (ch - 16 - im.height) // 2))
            d.text((x + 10, y + ch + 8), "%d. %s (%dx%d)%s" % (i + 1, os.path.relpath(p, res), ow, oh, nhan),
                   font=f, fill=(255, 220, 90))
        sheet.save(out_jpg, quality=88)
    return anh, khac


def so_lieu_theo_cau(segs):
    lines = []
    for s in segs:
        found = C.tim_so_lieu(s["text"])
        if found:
            lines.append("[%6.2f-%6.2f] %s" % (s["start"], s["end"], s["text"]))
            for so, dv, goc in found:
                lines.append("      %s %s   (gốc: %s)" % (so, dv, goc))
    return lines


def doc_thong_tin(info):
    """file thông tin nhà người dùng đưa (.txt/.md/.json) → (dict thong_tin, văn bản gốc)"""
    if not info:
        return None, ""
    if not os.path.isfile(info):
        C.die("không thấy file thông tin nhà: " + info)
    raw = io.open(info, encoding="utf-8", errors="replace").read()
    if info.lower().endswith(".json"):
        try:
            d = C.jload(info)
            d["_nguon"] = "file thông tin người dùng: " + os.path.basename(info)
            return d, raw
        except Exception:
            pass
    return {"_nguon": "file thông tin người dùng: " + os.path.basename(info), "_van_ban": raw.strip()}, raw


def khung_ke_hoach(audio, res, work, dai, kenh, thong_tin=None):
    return {
        "_huong_dan": "Claude điền theo SKILL.md của ban-do-tien-ich-nha-dat. Mốc giây = giây AUDIO. Không bịa toạ độ / số "
                      "liệu nhà; khoảng cách đo bản đồ luôn '≈'. Mẫu: references/vi-du-tay-ho.json.",
        "audio": os.path.relpath(audio, work),
        "res": os.path.relpath(res, work) if res else None,
        "thoi_luong": round(dai, 3),
        "kenh": kenh or {"ten": "", "logo": None, "cta": None},
        "khu_vuc": {"ten": "", "lat": None, "lon": None, "_vi_sao": "tỉnh/thành bao trùm, để Photon ưu tiên đúng vùng"},
        "thong_tin": thong_tin or {"_nguon": "lời đọc (không có file thông tin nhà riêng)", "loai": None, "dien_tich": None,
                                   "mat_tien": None, "phap_ly": None, "gia": None, "vi_tri": None,
                                   "lien_he": {"ten": None, "sdt": None}},
        "nha": {"lat": None, "lon": None, "chinh_xac": False, "ban_kinh_m": 80,
                "_vi_sao": "toạ độ lô đất: số nhà / link bản đồ người dùng đưa ⇒ chinh_xac true; chỉ biết tên phố ⇒ ĐOÁN"},
        "tien_ich": {"ban_kinh_m": 1500, "toi_da": 6},
        "hook": None,
        "dia_diem": {},
        "canh": [],
        "the": [],
        "sua_chu": {},
        "cai_dat": {"sub_kieu": "karaoke", "sub_y": 1545, "sub_co": 56, "sub_max_chu": 6, "sub_max_ky_tu": 30,
                    "hoa_tan": 0.25, "lufs": -14.0, "duoi": C.DUOI_SAU_TIENG_CUOI, "nguon_anh": True,
                    "sfx": True, "nhac": "khong", "dia_danh": True, "dinh_vi": False, "cap_tu": [],
                    "phong_cach": "mau", "nen_sang": 0.66},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--res")
    ap.add_argument("--work")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--kenh", help="kenh.json: {ten, logo, cta}")
    ap.add_argument("--info", help="file thông tin nhà (giá, diện tích, mặt tiền, SĐT, địa chỉ…) .txt/.md/.json")
    ap.add_argument("--lai", action="store_true", help="nhận dạng lại dù đã có loi_doc.json")
    a = ap.parse_args()
    audio = os.path.abspath(a.audio)
    if not os.path.isfile(audio):
        C.die("không thấy audio: " + audio)
    res = os.path.abspath(a.res) if a.res else None
    work = os.path.abspath(a.work) if a.work else os.path.join(os.path.dirname(audio),
                                                               os.path.splitext(os.path.basename(audio))[0] + "_bdti_work")
    os.makedirs(work, exist_ok=True)
    info = C.probe(audio)
    dai = info["duration"]
    print("▶ audio %.2f s → %s" % (dai, work))
    wav = os.path.join(work, "giong.wav")
    if not os.path.isfile(wav) or a.lai:
        tach_wav(audio, wav)
    ld = os.path.join(work, "loi_doc.json")
    if os.path.isfile(ld) and not a.lai:
        print("▶ đã có loi_doc.json — dùng lại (thêm --lai để nhận dạng lại)")
        data = C.jload(ld)
        segs, words = data["segments"], data["words"]
    else:
        segs, words = nhan_dang(wav, a.model)
        C.jsave(ld, {"audio": audio, "thoi_luong": round(dai, 3), "model": a.model, "segments": segs, "words": words})
    lines = ["# Lời đọc: %s (%.1f s). Mỗi câu: [giây] lời; dòng dưới: chữ@giây bắt đầu" % (os.path.basename(audio), dai), ""]
    for s in segs:
        lines.append("[%6.2f-%6.2f] %s" % (s["start"], s["end"], s["text"]))
        lines.append("      " + "  ".join("%s@%.2f" % (w["w"], w["start"]) for w in s["words"]))
    C.ghi_text(os.path.join(work, "loi_doc.txt"), "\n".join(lines) + "\n")
    sl = so_lieu_theo_cau(segs)
    C.ghi_text(os.path.join(work, "so_lieu.txt"),
               "# Số liệu nghe được trong lời (số chuẩn hoá, đơn vị) — thẻ tài liệu chỉ được dùng khi khớp các số này\n"
               + "\n".join(sl) + "\n")
    anh, khac = to_tai_nguyen(res, os.path.join(work, "tai_nguyen.jpg"))
    kenh = C.jload(a.kenh) if a.kenh and os.path.isfile(a.kenh) else None
    tt, raw = doc_thong_tin(os.path.abspath(a.info) if a.info else None)
    if raw:
        C.ghi_text(os.path.join(work, "thong_tin_nha.txt"), raw)
        print("▶ thông tin nhà → thong_tin_nha.txt (Claude đọc, điền ke_hoach.thong_tin; số trong đó được phép lên hình)")
    kh = os.path.join(work, "ke_hoach.json")
    if not os.path.isfile(kh):
        C.jsave(kh, khung_ke_hoach(audio, res, work, dai, kenh, tt))
        print("▶ đã tạo khung ke_hoach.json")
    else:
        print("▶ ke_hoach.json đã có — giữ nguyên")
    print("✅ work: %s" % work)
    print("   loi_doc.txt (%d câu, %d chữ) · so_lieu.txt (%d dòng) · tai_nguyen.jpg (%d ảnh/clip) · file khác: %d"
          % (len(segs), len(words), len(sl), len(anh), len(khac)))
    for p in khac:
        print("   • tài nguyên không phải ảnh: %s" % p)


if __name__ == "__main__":
    main()
