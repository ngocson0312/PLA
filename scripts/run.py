# -*- coding: utf-8 -*-
"""Cổng lệnh của skill ban-do-tien-ich-nha-dat (thông tin nhà + audio + ảnh/clip nhà → video BẢN ĐỒ tiện ích 9:16).

    python -I -X utf8 scripts/run.py quet --audio <file> [--res <thư mục ảnh/clip>] [--info <thong_tin.txt|json>]
    python -I -X utf8 scripts/run.py tim "<tên>"                      # cần mạng: tìm ứng viên OSM (Photon)
    python -I -X utf8 scripts/run.py tien-ich --work <dir>            # cần mạng: quét tiện ích thật quanh nhà + đường đi
    python -I -X utf8 scripts/run.py dia-diem --work <dir>            # cần mạng: hình học OSM (đường, hồ, metro, sân bay…)
    python -I -X utf8 scripts/run.py kiem-kh --work <dir>             # kiểm ke_hoach.json (số liệu nhà phải có trong lời …)
    python -I -X utf8 scripts/run.py duyet --work <dir>               # cần mạng: ảnh xem trước → duyet.jpg + bảng đồ hoạ
    python -I -X utf8 scripts/run.py dung --work <dir> [--out …]      # cần mạng (ô ảnh / đường đi chưa cache)
    python -I -X utf8 scripts/run.py kiem --work <dir>                # tự kiểm trên file cuối → soat_*.jpg
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chung as C

HERE = os.path.dirname(os.path.abspath(__file__))
SO_RE = re.compile(r"\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?")
FILE_CLIP = (".mp4", ".mov", ".m4v", ".mkv", ".webm")


def goi(script, args):
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, script)] + list(args))
    return r.returncode


def lay_arg(args, ten, mac_dinh=None):
    if ten in args:
        i = args.index(ten)
        if i + 1 < len(args):
            return args[i + 1]
    return mac_dinh


# ---------------------------------------------------------------- kiểm kế hoạch

def so_trong_loi(work, plan=None):
    """số trong lời đọc (+ số trong thong_tin nhà do người dùng đưa) → tập số chuẩn hoá"""
    import dung
    src = C.jload(os.path.join(work, "loi_doc.json"))
    words = dung.gop_so([dict(w) for w in src["words"] if w.get("w")])
    text = " ".join(w["w"] for w in words)
    so = {C.chuan_hoa_so(m.group(0)) for m in SO_RE.finditer(text)}
    so_tt = set()
    tt = (plan or {}).get("thong_tin") or {}

    def quet(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if not k.startswith("_"):
                    quet(x)
        elif isinstance(v, list):
            for x in v:
                quet(x)
        elif isinstance(v, (str, int, float)):
            for m in SO_RE.finditer(str(v)):
                so_tt.add(C.chuan_hoa_so(m.group(0)))
    if tt.get("_nguon", "").startswith("người dùng") or tt.get("_nguon", "").startswith("file"):
        quet(tt)
    return so | so_tt, words


def chu_nha(plan):
    """chữ về NHÀ (giá, diện tích, mặt tiền, SĐT, tên…) → số trong đó PHẢI có trong lời / thông tin người dùng"""
    out = []
    hk = plan.get("hook") or {}
    for k in ("dong1", "dong2", "dong3"):
        if hk.get(k):
            out.append(("hook." + k, hk[k]))
    for i, c in enumerate(plan.get("canh", [])):
        tag = "canh[%d]" % i
        for j, d in enumerate(c.get("dau_de") or []):
            for k in ("tieu_de", "phu"):
                if d.get(k):
                    out.append((tag + ".dau_de[%d].%s" % (j, k), d[k]))
        if isinstance(c.get("nha"), dict):
            for k in ("nhan", "phu"):
                if isinstance(c["nha"].get(k), str):
                    out.append((tag + ".nha." + k, c["nha"][k]))
        for j, n in enumerate(c.get("nhan_manh") or []):
            for k in ("text", "phu"):
                if n.get(k):
                    out.append((tag + ".nhan_manh[%d].%s" % (j, k), n[k]))
        # kiểu mẫu: tiêu đề trên cùng (dòng có ≈ = số đo bản đồ ⇒ kiểm ở chu_ban_do), chữ trong hình lô đất
        for j, d in enumerate(c.get("tieu_de_tren") or []):
            for jj, x in enumerate(d.get("dong") or []):
                if "≈" not in x:
                    out.append((tag + ".tieu_de_tren[%d].dong[%d]" % (j, jj), x))
        ld = c.get("lo_dat") or {}
        if isinstance(ld.get("nhan"), str):
            out.append((tag + ".lo_dat.nhan", ld["nhan"]))
        for j, e in enumerate(ld.get("canh") or []):
            if isinstance(e.get("chu"), str):
                out.append((tag + ".lo_dat.canh[%d].chu" % j, e["chu"]))
    for i, t in enumerate(plan.get("the", []) or []):
        tag = "the[%d] %s" % (i, t.get("kieu"))
        for k in ("tieu_de", "nhan", "gia", "ten", "sdt", "dong_cuoi"):
            if isinstance(t.get(k), str):
                out.append((tag + "." + k, t[k]))
        ch = t.get("chu")
        for j, x in enumerate(ch if isinstance(ch, list) else [ch] if ch else []):
            out.append((tag + ".chu[%d]" % j, x))
        for j, d in enumerate(t.get("dong") or []):
            if isinstance(d, str):          # theo_doi.dong = [dòng chính, dòng phụ]
                out.append((tag + ".dong[%d]" % j, d))
                continue
            for k in ("nhan", "gia_tri"):
                if d.get(k):
                    out.append((tag + ".dong[%d].%s" % (j, k), d[k]))
    return out


def chu_ban_do(plan):
    """nhãn bản đồ do Claude gõ tay (tên đường, tên tiện ích, chữ khoảng cách) — số phải lấy từ OSM / đo bản đồ"""
    out = []
    for i, c in enumerate(plan.get("canh", [])):
        tag = "canh[%d]" % i
        for k in ("tuyen_sang", "vung_sang", "tien_ich", "neon", "chu_lon", "bien_anh", "thuoc"):
            for j, d in enumerate(c.get(k) or []):
                for f in ("ten", "nhan", "chu"):
                    if isinstance(d.get(f), str):
                        out.append(("%s.%s[%d].%s" % (tag, k, j, f), d[f]))
        for j, d in enumerate(c.get("tieu_de_tren") or []):
            for jj, x in enumerate(d.get("dong") or []):
                if "≈" in x:
                    out.append(("%s.tieu_de_tren[%d].dong[%d]" % (tag, j, jj), x))
    return out


def kiem_ke_hoach(work, in_ra=True):
    plan = C.doc_ke_hoach(work)
    dd = plan.get("dia_diem") or {}
    cd = plan.get("cai_dat") or {}
    dur = C.probe(plan["audio"])["duration"] + float(cd.get("duoi", C.DUOI_SAU_TIENG_CUOI))
    loi, canh_bao = [], []
    so_loi, words = so_trong_loi(work, plan)
    p_ti = os.path.join(work, "tien_ich.json")
    ti = C.jload(p_ti)["muc"] if os.path.isfile(p_ti) else {}
    # 1. số về NHÀ phải có trong lời / thông tin người dùng (không bịa giá, diện tích, SĐT …)
    for cho, txt in chu_nha(plan):
        for m in SO_RE.finditer(txt):
            s = C.chuan_hoa_so(m.group(0))
            if s not in so_loi:
                loi.append("%s: số '%s' trong \"%s\" KHÔNG có trong lời đọc / thông tin nhà — bỏ hoặc sửa (không bịa số)"
                           % (cho, m.group(0), txt))
    for cho, txt in chu_ban_do(plan):
        for m in SO_RE.finditer(txt):
            s = C.chuan_hoa_so(m.group(0))
            if s not in so_loi:
                canh_bao.append("%s: số '%s' trong \"%s\" không có trong lời — chỉ được nếu là TÊN OSM / số đo bản đồ (≈)"
                                % (cho, m.group(0), txt))
                if ("km" in txt.lower() or " m" in txt.lower()) and "≈" not in txt:
                    loi.append("%s: khoảng cách \"%s\" thiếu dấu ≈ (số đo bản đồ luôn xấp xỉ)" % (cho, txt))
    # 2. nhà
    nha = plan.get("nha") or {}
    if nha.get("lat") is None or nha.get("lon") is None:
        loi.append("ke_hoach.nha thiếu lat/lon")
    elif not nha.get("chinh_xac", True):
        canh_bao.append("vị trí lô đất là ĐOÁN (chinh_xac=false) — hiện vòng 'KHU VỰC LÔ ĐẤT'; PHẢI hỏi ở cổng duyệt")

    def co_diem(x):
        return x == "nha" or (isinstance(x, list) and len(x) == 2) or (isinstance(x, str) and (x in dd or x in ti))
    # 3. cảnh phủ kín 0 → hết
    canh = sorted(plan.get("canh", []), key=lambda x: float(x["tu"]))
    if not canh:
        loi.append("chưa có cảnh nào")
    else:
        if float(canh[0]["tu"]) > 0.05:
            loi.append("cảnh đầu bắt đầu ở %.2f s (phải 0)" % float(canh[0]["tu"]))
        for i, c in enumerate(canh):
            den = c.get("den")
            nxt = float(canh[i + 1]["tu"]) if i + 1 < len(canh) else dur
            if den is not None and float(den) < nxt - 0.05:
                loi.append("hở hình %.2f–%.2f sau cảnh %d" % (float(den), nxt, i))
            d = (float(den) if den is not None else nxt) - float(c["tu"])
            if d < 1.5 and c.get("loai") != "cta":
                canh_bao.append("cảnh %d (%s) chỉ %.2f s — dưới 1,5 s dễ giật" % (i, c.get("loai"), d))
            if c.get("loai") == "ban_do":
                for j, k in enumerate(c.get("cam") or []):
                    for x in (k.get("vua") or []) + ([k["tam"]] if k.get("tam") else []):
                        if not co_diem(x):
                            loi.append("cảnh %d cam[%d]: '%s' không phải nha / id tien_ich / key dia_diem" % (i, j, x))
                    vy = k.get("vung_y")
                    if vy and float(vy[1]) > 0.72:
                        loi.append("cảnh %d cam[%d]: vung_y đáy %.2f > 0,72 — sẽ đè dải sub" % (i, j, float(vy[1])))
                for j, d_ in enumerate(c.get("tien_ich") or []):
                    k = d_.get("id") or d_.get("diem")
                    if not co_diem(k) or k == "nha":
                        loi.append("cảnh %d tien_ich[%d]: '%s' không có trong tien_ich.json / dia_diem" % (i, j, k))
                    if not (float(c["tu"]) - 0.01 <= float(d_.get("t", -1)) < (float(den) if den is not None else nxt)):
                        loi.append("cảnh %d tien_ich[%d]: t=%s ngoài cảnh" % (i, j, d_.get("t")))
                for f, kk in (("tuyen_sang", "tuyen"), ("vung_sang", "vung"), ("neon", "tuyen")):
                    for j, d_ in enumerate(c.get(f) or []):
                        if d_.get(kk) not in dd:
                            loi.append("cảnh %d %s[%d]: %s chưa khai trong dia_diem" % (i, f, j, d_.get(kk)))
                # kiểu mẫu
                for j, d_ in enumerate(c.get("bien_anh") or []):
                    k = d_.get("id") or d_.get("diem")
                    if not co_diem(k) or k == "nha":
                        loi.append("cảnh %d bien_anh[%d]: '%s' không có trong tien_ich.json / dia_diem" % (i, j, k))
                    if d_.get("anh"):
                        f_ = d_["anh"]
                        if not any(os.path.isfile(f_ if os.path.isabs(f_) else os.path.join(b, f_))
                                   for b in ([plan.get("res")] if plan.get("res") else []) + [work]):
                            loi.append("cảnh %d bien_anh[%d]: không thấy ảnh %s" % (i, j, f_))
                    else:
                        canh_bao.append("cảnh %d bien_anh[%d] '%s': không có ảnh ⇒ dùng ẢNH VỆ TINH cận cảnh — hỏi ở "
                                        "cổng duyệt có ảnh thật không" % (i, j, k))
                for j, d_ in enumerate(c.get("chu_lon") or []):
                    if not co_diem(d_.get("tai")):
                        loi.append("cảnh %d chu_lon[%d]: tai=%s không phải điểm" % (i, j, d_.get("tai")))
                for j, d_ in enumerate(c.get("thuoc") or []):
                    for kk in ("a", "b"):
                        if not co_diem(d_.get(kk, "nha")):
                            loi.append("cảnh %d thuoc[%d].%s = %s không phải điểm" % (i, j, kk, d_.get(kk)))
                ld = c.get("lo_dat")
                if ld:
                    if ld.get("theo_duong") and ld["theo_duong"] not in dd:
                        loi.append("cảnh %d lo_dat.theo_duong = %s chưa khai trong dia_diem" % (i, ld["theo_duong"]))
                    if ld.get("doan", True):
                        canh_bao.append("cảnh %d lo_dat: HÌNH LÔ ĐOÁN (%s × %s m, chưa có sơ đồ sổ đỏ) — PHẢI hỏi ở cổng duyệt"
                                        % (i, ld.get("rong_m"), ld.get("sau_m")))
            for k in ("tuyen", "diem", "a", "b"):
                v = c.get(k)
                if isinstance(v, str) and v not in dd:
                    loi.append("cảnh %d: '%s' = %s chưa khai trong dia_diem" % (i, k, v))
            for j, n in enumerate(c.get("nhan_manh") or []):
                if isinstance(n.get("diem"), str) and n["diem"] not in dd:
                    loi.append("cảnh %d: nhan_manh[%d].diem = %s chưa khai trong dia_diem" % (i, j, n["diem"]))
    # 4. địa điểm đã giải
    for k in dd:
        if not os.path.isfile(os.path.join(work, "dia_ly", k + ".json")):
            loi.append("địa điểm %s chưa có dia_ly/%s.json — chạy `run.py dia-diem`" % (k, k))
    # 5. thẻ
    res = plan.get("res")
    for i, t in enumerate(plan.get("the", []) or []):
        k = t.get("kieu")
        if k not in ("anh", "thong_tin", "gia", "lien_he", "theo_doi"):
            loi.append("the[%d]: kieu=%s (có: anh, thong_tin, gia, lien_he, theo_doi)" % (i, k))
            continue
        tu, den_ = float(t.get("tu", -1)), float(t.get("den", -1))
        if not (0 <= tu < den_ <= dur + 0.01):
            loi.append("the[%d] %s: tu/den sai (%.2f–%.2f, video %.2f s)" % (i, k, tu, den_, dur))
        if k == "anh":
            fs = t.get("anh") if isinstance(t.get("anh"), list) else [t.get("anh")]
            for f in fs:
                ok = f and any(os.path.isfile(f if os.path.isabs(f) else os.path.join(b, f))
                               for b in ([res] if res else []) + [work, os.path.dirname(plan["audio"])])
                if not ok:
                    loi.append("the[%d] anh: không thấy file %s trong Resources" % (i, f))
            if len(fs) > 1 and (den_ - tu) / len(fs) < 1.2:
                canh_bao.append("the[%d] anh: %d ảnh trong %.1f s — mỗi ảnh < 1,2 s, đổi dồn dập" % (i, len(fs), den_ - tu))
        if k == "lien_he":
            so = re.sub(r"\D", "", t.get("sdt", ""))
            loi_so = re.sub(r"\D", "", " ".join(w["w"] for w in words))
            if not so or so not in loi_so:
                tt_so = re.sub(r"\D", "", str(((plan.get("thong_tin") or {}).get("lien_he") or {}).get("sdt", "")))
                if so != tt_so or not (plan.get("thong_tin") or {}).get("_nguon", "").startswith(("người dùng", "file")):
                    loi.append("the[%d] lien_he: SĐT %s không có trong lời đọc / thông tin người dùng" % (i, t.get("sdt")))
        if k == "gia" and not t.get("gia"):
            loi.append("the[%d] gia: thiếu 'gia'" % i)
    # CTA cuối BẮT BUỘC (chốt 09/11/2026): lời có đọc SĐT ⇒ lien_he; không có SĐT ⇒ theo_doi (nút FOLLOW + tay nhấn)
    cta_ = [t for t in plan.get("the", []) or [] if t.get("kieu") in ("lien_he", "theo_doi")]
    if not cta_ and not any(c.get("loai") == "cta" for c in canh) and cd.get("cta", True) is not False:
        loi.append("cuối video chưa có CTA: lời có đọc SĐT ⇒ thẻ lien_he; KHÔNG có SĐT ⇒ thẻ theo_doi "
                   "(nút FOLLOW + bàn tay nhấn, ≥ 3 s, kéo tới hết video)")
    for t in cta_:
        if float(t.get("den", 0)) < dur - 1.0:
            canh_bao.append("CTA %s hết ở %.2f s, video %.2f s — nên kéo tới hết video" % (t["kieu"], float(t["den"]), dur))
        if t["kieu"] == "theo_doi" and float(t.get("den", 0)) - float(t.get("tu", 0)) < 2.5:
            canh_bao.append("CTA theo_doi chỉ %.1f s — dưới 2,5 s tay chưa kịp nhấn" % (float(t["den"]) - float(t["tu"])))
    # kiểu MẪU (chốt 09/11/2026 theo Video_Mau.mp4 của khách) — mặc định cho job khách BĐS
    mau = cd.get("phong_cach") == "mau" or any(c.get("phong_cach") == "mau" for c in canh)
    if not mau:
        canh_bao.append("chưa bật kiểu MẪU (cai_dat.phong_cach \"mau\") — kiểu đã chốt cho video khách BĐS, chỉ tắt khi "
                        "người dùng bảo")
    else:
        if plan.get("hook"):
            canh_bao.append("kiểu mẫu: còn hook navy cũ — dùng tieu_de_tren (2 dòng trắng + VÀNG) thay, bỏ hook")
        co_lo = [c for c in canh if c.get("lo_dat")]
        if not co_lo and (plan.get("thong_tin") or {}).get("dien_tich"):
            canh_bao.append("kiểu mẫu: chưa có cận cảnh lo_dat (khối xanh sáng + chữ diện tích, zoom ~21,2, nen_sang 0,92) "
                            "dù lời có diện tích")
        for c in co_lo:
            zm = max([float(k.get("zoom", 0)) for k in (c.get("cam") or []) if isinstance(k, dict)] or [0])
            if zm < 20.5:
                canh_bao.append("cảnh %.2f s lo_dat: camera chỉ zoom %.1f — chốt zoom sát ~21,2 cho lô to (~250 px)"
                                % (float(c["tu"]), zm))
    # thẻ giữa màn hình chồng nhau
    giua = [(float(t["tu"]), float(t["den"]), i) for i, t in enumerate(plan.get("the", []) or [])
            if t.get("kieu") in ("gia", "lien_he", "theo_doi")
            or (t.get("kieu") == "anh" and t.get("vi_tri", "giua") == "giua")]
    giua.sort()
    for a, b in zip(giua, giua[1:]):
        if b[0] < a[1] - 0.05:
            canh_bao.append("the[%d] và the[%d] cùng ở giữa màn hình, chồng %.2f s" % (a[2], b[2], a[1] - b[0]))
    # 6. tiện ích
    if any(d_.get("id") in ti for c in canh for d_ in (c.get("tien_ich") or [])) and not ti:
        loi.append("chưa có tien_ich.json — chạy `run.py tien-ich`")
    # 7. hook
    hk = plan.get("hook")
    if hk and float(hk.get("den", 0)) <= float(hk.get("tu", 0)):
        loi.append("hook: den ≤ tu")
    if in_ra:
        for x in canh_bao:
            print("⚠ " + x)
        for x in loi:
            print("⛔ " + x)
        if not loi:
            print("✅ ke_hoach.json đạt: %d cảnh, %d địa điểm, %d thẻ, %d chữ về nhà (số liệu đều có trong lời)"
                  % (len(canh), len(dd), len(plan.get("the", []) or []), len(chu_nha(plan))))
    return loi, plan, words


# ---------------------------------------------------------------- duyệt

def moc_xem(plan, dur):
    """các giây xem trước: sau mỗi chặng camera, sau lớp cuối mỗi cảnh, giữa mỗi thẻ"""
    canh = sorted(plan["canh"], key=lambda x: float(x["tu"]))
    moc = []
    for i, c in enumerate(canh):
        tu = float(c["tu"])
        den = float(c["den"]) if c.get("den") is not None else (float(canh[i + 1]["tu"]) if i + 1 < len(canh) else dur)
        ts = []
        for k in (c.get("cam") or [])[1:]:
            ts.append(float(k.get("t", tu)) + float(k.get("dai", 1.2)) + 0.25)
        lop = [float(d_["t"]) for f in ("tien_ich", "tuyen_sang", "vung_sang", "neon", "bien_anh", "chu_lon", "thuoc")
               for d_ in (c.get(f) or [])]
        ld = c.get("lo_dat") or {}
        lop += [float(e.get("t", 0)) for e in ld.get("canh") or []]
        if lop:
            ts.append(max(lop) + 1.3)
        if not ts:
            ts.append(tu + (den - tu) * 0.6)
        for t in ts:
            moc.append((min(den - 0.3, max(tu + 0.2, t)), "canh %d" % i))
    hk = plan.get("hook")
    if hk:
        moc.append((min(float(hk["den"]) - 0.1, float(hk.get("tu", 0)) + 2.2), "hook"))
    for i, t in enumerate(plan.get("the", []) or []):
        tu, den = float(t["tu"]), float(t["den"])
        if t.get("kieu") == "lien_he":
            moc.append((min(den - 0.2, float(t.get("t_bam", tu + 4)) + 0.05), "the %d %s" % (i, t["kieu"])))
            moc.append((den - 0.3, "the %d %s" % (i, t["kieu"])))
        elif t.get("kieu") == "theo_doi":
            tb = float(t.get("t_bam", tu + 1.2))
            for x in (tb - 0.1, tb + 0.35, tb + 1.15, den - 0.3):
                moc.append((min(den - 0.2, x), "the %d %s" % (i, t["kieu"])))
        else:
            moc.append((min(den - 0.15, tu + max(0.9, (den - tu) * 0.6)), "the %d %s" % (i, t["kieu"])))
    moc.sort()
    out = []
    for t, nh in moc:
        if out and t - out[-1][0] < 0.45:
            continue
        out.append((round(t, 2), nh))
    return out


def bang_do_hoa(plan, dur):
    canh = sorted(plan["canh"], key=lambda x: float(x["tu"]))
    print("\n▶ BẢNG ĐỒ HOẠ (lời → hình):")
    for i, c in enumerate(canh):
        den = c.get("den") if c.get("den") is not None else (canh[i + 1]["tu"] if i + 1 < len(canh) else round(dur, 2))
        lop = []
        for k in c.get("cam") or []:
            if k.get("vua"):
                lop.append("cam→vừa[%s]@%.1f" % (",".join(k["vua"]), float(k.get("t", 0))))
            else:
                lop.append("cam→%s z%.1f@%.1f" % (k.get("tam", "nha"), float(k.get("zoom", 16)), float(k.get("t", 0))))
        for d_ in c.get("tien_ich") or []:
            lop.append("📍%s%s@%.1f" % (d_.get("id"), " +đường" if d_.get("duong", True) else "", float(d_["t"])))
        for d_ in c.get("tuyen_sang") or []:
            lop.append("〰%s@%.1f" % (d_["tuyen"], float(d_["t"])))
        for d_ in c.get("vung_sang") or []:
            lop.append("▧%s@%.1f" % (d_["vung"], float(d_["t"])))
        for d_ in c.get("vong") or []:
            lop.append("◯%dm@%.1f" % (int(d_["r_m"]), float(d_.get("t", 0))))
        for d_ in c.get("dau_de") or []:
            lop.append("«%s»" % d_.get("tieu_de"))
        for d_ in c.get("neon") or []:
            lop.append("✦neon %s%s@%.1f" % (d_["tuyen"], (" «%s»" % d_["ten"]) if isinstance(d_.get("ten"), str) else "",
                                            float(d_["t"])))
        for d_ in c.get("chu_lon") or []:
            lop.append("Ａ%s@%.1f" % (d_["chu"], float(d_["t"])))
        for d_ in c.get("thuoc") or []:
            lop.append("📏%s→%s %s@%.1f" % (d_.get("a", "nha"), d_["b"], d_.get("chu") or "≈ tự đo", float(d_["t"])))
        for d_ in c.get("bien_anh") or []:
            lop.append("🖼%s%s@%.1f" % (d_.get("id") or d_.get("diem"), "" if d_.get("anh") else " (ảnh vệ tinh)",
                                       float(d_["t"])))
        if c.get("lo_dat"):
            ld = c["lo_dat"]
            lop.append("▭lô %s×%s m «%s»%s@%.1f" % (ld.get("rong_m"), ld.get("sau_m"), ld.get("nhan", ""),
                                                  " ĐOÁN" if ld.get("doan", True) else "", float(ld.get("t", 0))))
        for d_ in c.get("tieu_de_tren") or []:
            lop.append("⌃«%s»@%.1f" % (" / ".join(d_.get("dong") or []), float(d_.get("t", 0))))
        print("   #%-2d %6.2f–%6.2f  %s\n        lời: %s" % (i, float(c["tu"]), float(den), " · ".join(lop),
                                                         (c.get("_loi") or "")[:110]))
    print("▶ THẺ:")
    for i, t in enumerate(plan.get("the", []) or []):
        mo = t.get("gia") or t.get("tieu_de") or t.get("sdt") or ""
        if t.get("kieu") == "theo_doi":
            mo = "nút %s + tay nhấn @%.1f" % (t.get("nut") or "FOLLOW", float(t.get("t_bam", float(t["tu"]) + 1.2)))
        if t.get("kieu") == "anh":
            fs = t["anh"] if isinstance(t["anh"], list) else [t["anh"]]
            mo = ", ".join(os.path.basename(f) for f in fs)
        if t.get("dong"):
            mo += " | " + " | ".join("%s: %s" % (d_.get("nhan"), d_.get("gia_tri")) for d_ in t["dong"])
        print("   the[%d] %-9s %6.2f–%6.2f  %s" % (i, t.get("kieu"), float(t["tu"]), float(t["den"]), mo[:120]))


def duyet(work):
    loi, plan, words = kiem_ke_hoach(work)
    if loi:
        C.die("sửa hết ⛔ rồi duyệt lại")
    from PIL import Image, ImageDraw
    dur = C.probe(plan["audio"])["duration"] + float(plan.get("cai_dat", {}).get("duoi", C.DUOI_SAU_TIENG_CUOI))
    moc = moc_xem(plan, dur)
    rc = goi("dung.py", ["--work", work, "--xem-truoc", ",".join("%.2f" % m[0] for m in moc)])
    if rc != 0:
        C.die("xem trước lỗi")
    thumbs = []
    f_ = C.font("bold", 17)
    for t, nh in moc:
        p = os.path.join(work, "xem_truoc_%06.2f.jpg" % t)
        if not os.path.isfile(p):
            continue
        loi_c = " ".join(w["w"] for w in words if t - 2.2 <= w["start"] <= t + 0.3)
        im = Image.new("RGB", (360, 640 + 50), (0, 0, 0))
        im.paste(Image.open(p).convert("RGB").resize((360, 640), Image.LANCZOS), (0, 0))
        d = ImageDraw.Draw(im)
        d.text((6, 644), "%s · %.2f s" % (nh, t), font=f_, fill=(255, 230, 120))
        d.text((6, 668), loi_c[-46:], font=C.font("semi", 13), fill=(255, 255, 255))
        thumbs.append(im)
    cot = 5
    hang = (len(thumbs) + cot - 1) // cot
    sheet = Image.new("RGB", (cot * 366 + 6, hang * 696 + 6), (30, 30, 30))
    for k, im in enumerate(thumbs):
        sheet.paste(im, (6 + (k % cot) * 366, 6 + (k // cot) * 696))
    out = os.path.join(work, "duyet.jpg")
    sheet.save(out, quality=86)
    bang_do_hoa(plan, dur)
    print("✅ duyet.jpg: %s (%d khung) — Claude MỞ XEM (và các xem_truoc_*.jpg cần soi) rồi mới hỏi ở cổng duyệt"
          % (out, len(thumbs)))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "quet":
        sys.exit(goi("quet.py", args))
    if cmd == "tim":
        sys.exit(goi("dia_ly.py", ["tim"] + args))
    work = lay_arg(args, "--work")
    if not work:
        C.die("thiếu --work <thư mục làm việc>")
    work = os.path.abspath(work)
    if cmd == "tien-ich":
        sys.exit(goi("tien_ich.py", args))
    if cmd == "dia-diem":
        import dia_ly as G
        kh = os.path.join(work, "ke_hoach.json")
        raw = C.jload(kh)
        bao = G.giai_quyet(raw, work)
        C.jsave(kh, raw)
        n = sum(1 for b in bao if b[2].startswith("⛔"))
        if n:
            C.die("%d địa điểm chưa giải được — sửa ten / osm / ten_osm_re / lat,lon rồi chạy lại" % n)
        print("✅ %d địa điểm → %s" % (len(bao), os.path.join(work, "dia_ly")))
    elif cmd == "kiem-kh":
        loi, _, _ = kiem_ke_hoach(work)
        sys.exit(1 if loi else 0)
    elif cmd == "duyet":
        duyet(work)
    elif cmd == "dung":
        loi, _, _ = kiem_ke_hoach(work)
        if loi:
            C.die("ke_hoach.json còn ⛔ — không dựng")
        sys.exit(goi("dung.py", args))
    elif cmd == "kiem":
        sys.exit(goi("kiem.py", args))
    else:
        print(__doc__)
        C.die("lệnh lạ: " + cmd)


if __name__ == "__main__":
    main()
