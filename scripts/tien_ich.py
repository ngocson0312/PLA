# -*- coding: utf-8 -*-
"""TIỆN ÍCH quanh nhà (dữ liệu THẬT, không bịa): quét OSM theo nhóm bằng Photon reverse (bán kính quanh nhà),
đo khoảng cách + đường đi THẬT (OSRM: ô tô router.project-osrm.org, đi bộ routing.openstreetmap.de), ghi:

    work/tien_ich.json   {"nha": [lat, lon], "ban_kinh_m": R, "muc": {id: {ten, nhom, lat, lon, osm, cach_m,
                          dich [lat, lon] (điểm đến: bờ hồ / cổng gần nhất), duong {kieu, met, giay, diem}}}}
    work/tien_ich.txt    bảng: id · nhóm · tên · đường đi · thời gian  (Claude đọc để chọn tiện ích cho từng cảnh)
    work/tien_ich.jpg    bản đồ vệ tinh quanh nhà: vòng bán kính + ghim đánh số theo id (Claude MỞ XEM)

    python -I -X utf8 scripts/tien_ich.py --work <dir> [--ban-kinh 1500] [--nhom khach_san,truong,...] [--toi-da 6]

Id: <nhóm>_<thứ tự gần → xa>, vd khach_san_1. Đường đi: ≤ 1,2 km đi bộ (foot), xa hơn ô tô (car).
Số trên hình lấy từ đây luôn ghi "≈" (đo từ bản đồ), không phải số người bán nói.
"""
import argparse
import hashlib
import math
import os
import re
import sys
import time

import numpy as np
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bieu_tuong as BT
import chung as C
import dia_ly as G

OSRM = {"o_to": "https://router.project-osrm.org/route/v1/driving/%f,%f;%f,%f",
        "di_bo": "https://routing.openstreetmap.de/routed-foot/route/v1/driving/%f,%f;%f,%f"}
DI_BO_TOI_DA = 1200.0
VONG_NHOM = ("ho", "cong_vien")      # nhóm là VÙNG: khoảng cách tính tới mép gần nhất (bờ hồ, cổng công viên)


# ---------------------------------------------------------------- đường đi

def duong_di(a, b, kieu="o_to", chi_cache=False):
    """OSRM a → b ([lat, lon]); kieu o_to | di_bo | thang. → {kieu, met, giay, diem [[lat, lon]…]} (cache đĩa).
    Lỗi mạng ⇒ đường thẳng (kieu 'thang', giay None) — không bịa thời gian."""
    if kieu == "thang":
        return {"kieu": "thang", "met": C.khoang_cach_m(a, b), "giay": None, "diem": [list(a), list(b)]}
    key = hashlib.md5(("%s|%.6f,%.6f|%.6f,%.6f" % (kieu, a[0], a[1], b[0], b[1])).encode()).hexdigest()
    p = os.path.join(C.cache_dir("duong_di"), key + ".json")
    if os.path.isfile(p):
        return C.jload(p)
    if chi_cache:
        return duong_di(a, b, "thang")
    url = OSRM.get(kieu, OSRM["o_to"]) % (a[1], a[0], b[1], b[0])
    for lan in range(3):
        try:
            r = requests.get(url, params={"overview": "full", "geometries": "geojson"}, headers=C.UA, timeout=30)
            j = r.json()
            if j.get("code") == "Ok" and j.get("routes"):
                rt = j["routes"][0]
                out = {"kieu": kieu, "met": round(float(rt["distance"]), 1), "giay": round(float(rt["duration"]), 1),
                       "diem": [[c[1], c[0]] for c in rt["geometry"]["coordinates"]]}
                # nối 2 đầu về đúng điểm (OSRM bám vào đường gần nhất)
                if C.khoang_cach_m(out["diem"][0], a) > 3:
                    out["diem"].insert(0, list(a))
                if C.khoang_cach_m(out["diem"][-1], b) > 3:
                    out["diem"].append(list(b))
                C.jsave(p, out)
                time.sleep(0.25)
                return out
        except Exception:
            pass
        time.sleep(1.2 * (lan + 1))
    C.canh_bao("OSRM lỗi %s → %s (%s) — dùng đường thẳng" % (a, b, kieu))
    return duong_di(a, b, "thang")


def chu_khoang_cach(met, giay=None, kieu="o_to", thoi_gian=None):
    """'≈ 450 m · 6 phút đi bộ' / '≈ 2,4 km' (ô tô: thời gian chỉ hiện khi thoi_gian=True — OSRM tính đường vắng)"""
    if met < 1000:
        d = "≈ %d m" % max(10, int(round(met / 10.0) * 10))
    else:
        d = ("≈ %.1f km" % (met / 1000.0)).replace(".", ",")
        if met >= 10000:
            d = "≈ %d km" % int(round(met / 1000.0))
    if kieu == "di_bo" and giay:
        return "%s · %d phút đi bộ" % (d, max(1, int(round(giay / 60.0))))
    if kieu == "o_to" and giay and thoi_gian:
        return "%s · %d phút" % (d, max(1, int(round(giay / 60.0))))
    return d


# ---------------------------------------------------------------- quét

def _gan_nhat_tren_vong(nha, vong):
    """điểm trên viền vùng gần nhà nhất → [lat, lon]"""
    best, bd = None, 1e18
    for v in vong:
        a = np.asarray(v, dtype=np.float64)
        if len(a) < 2:
            continue
        P = np.array([C.ll2px(p[0], p[1], 18) for p in a])
        q = np.array(C.ll2px(nha[0], nha[1], 18))
        A, B = P[:-1], P[1:]
        AB = B - A
        L2 = (AB ** 2).sum(1)
        t = np.clip(((q - A) * AB).sum(1) / np.maximum(L2, 1e-9), 0, 1)
        Q = A + AB * t[:, None]
        d = ((Q - q) ** 2).sum(1)
        i = int(np.argmin(d))
        if d[i] < bd:
            bd = d[i]
            best = C.px2ll(Q[i][0], Q[i][1], 18)
    return [best[0], best[1]] if best else None


def quet_nhom(nha, key, ban_kinh_m, toi_da=6, chi_cache=False):
    g = BT.NHOM[key]
    if not g["osm"]:
        return []
    ck = "v1_%s_%.4f_%.4f_%d" % (key, nha[0], nha[1], int(ban_kinh_m))
    p = os.path.join(C.cache_dir("tien_ich"), ck + ".json")
    if os.path.isfile(p):
        feats = C.jload(p)
    elif chi_cache:
        return []
    else:
        params = [("lat", round(nha[0], 6)), ("lon", round(nha[1], 6)), ("radius", round(ban_kinh_m / 1000.0, 2)),
                  ("limit", 50)] + [("osm_tag", t) for t in g["osm"]]
        try:
            r = G._get(G.PHOTON_REV, params, timeout=30, lan=3)
            feats = r.json().get("features", [])
            C.jsave(p, feats)
        except Exception as e:
            C.canh_bao("quét %s lỗi (%s) — bỏ nhóm này" % (key, str(e)[:80]))
            return []
        time.sleep(0.25)
    out, seen = [], []
    for f in feats:
        pr = f["properties"]
        ten = C.nfc((pr.get("name") or "").strip())
        if not ten or len(ten) < 3:
            continue
        lo, la = f["geometry"]["coordinates"]
        osm = "%s%d" % (pr.get("osm_type", "N"), int(pr.get("osm_id", 0)))
        if key == "ho" and pr.get("osm_value") not in ("water", "lake", "pond", "reservoir"):
            continue
        k = C.ten_khong_dau(ten)
        if any(k == s_ or (k in s_ or s_ in k) and C.khoang_cach_m([la, lo], q) < 250 for s_, q in seen):
            continue
        seen.append((k, [la, lo]))
        out.append({"ten": ten, "nhom": key, "lat": float(la), "lon": float(lo), "osm": osm,
                    "the": "%s=%s" % (pr.get("osm_key"), pr.get("osm_value")),
                    "cach_thang_m": round(C.khoang_cach_m(nha, [la, lo]), 1)})
    out.sort(key=lambda x: x["cach_thang_m"])
    return [x for x in out if x["cach_thang_m"] <= ban_kinh_m * 1.15][:toi_da * 2]


def quet(work, ban_kinh_m=1500, nhom=None, toi_da=6, chi_cache=False):
    plan = C.jload(os.path.join(work, "ke_hoach.json"))
    nh = plan.get("nha") or {}
    if nh.get("lat") is None or nh.get("lon") is None:
        C.die("ke_hoach.nha chưa có lat/lon — điền vị trí nhà trước (hoặc ĐOÁN + chinh_xac: false)")
    nha = [float(nh["lat"]), float(nh["lon"])]
    ds_nhom = nhom or [k for k, v in BT.NHOM.items() if v["mac_dinh"]]
    muc = {}
    for key in ds_nhom:
        if key not in BT.NHOM:
            C.canh_bao("nhóm lạ: %s (có: %s)" % (key, ", ".join(BT.NHOM)))
            continue
        ds = quet_nhom(nha, key, ban_kinh_m, toi_da, chi_cache)
        n = 0
        for it in ds:
            dich = [it["lat"], it["lon"]]
            if key in VONG_NHOM and it["osm"][0] in "WR":
                try:
                    gh = G.hinh_hoc(it["osm"])
                    if gh.get("vong"):
                        dich = _gan_nhat_tren_vong(nha, gh["vong"]) or dich
                        if G.trong_vung(nha, gh["vong"]):
                            continue
                except Exception:
                    pass
            cach = C.khoang_cach_m(nha, dich)
            kieu = "di_bo" if cach <= DI_BO_TOI_DA else "o_to"
            dd = duong_di(nha, dich, kieu, chi_cache)
            n += 1
            id_ = "%s_%d" % (key, n)
            it.update({"dich": [round(dich[0], 7), round(dich[1], 7)], "cach_m": round(cach, 1), "duong": dd,
                       "chu": chu_khoang_cach(dd["met"], dd["giay"], dd["kieu"])})
            muc[id_] = it
            if n >= toi_da:
                break
        print("   %-12s %2d mục" % (key, n))
    out = {"nha": nha, "ban_kinh_m": ban_kinh_m, "muc": muc}
    C.jsave(os.path.join(work, "tien_ich.json"), out)
    lines = ["# Tiện ích THẬT quanh nhà (OSM qua Photon, đường đi OSRM) — bán kính %d m, nhà %.6f, %.6f" % (ban_kinh_m, nha[0], nha[1]),
             "# id · nhóm · tên · đường đi (chữ trên hình) · thẳng · thẻ OSM", ""]
    for id_, it in muc.items():
        lines.append("%-14s %-11s %-42s %-26s thẳng %5d m  %s %s" % (id_, it["nhom"], it["ten"][:42], it["chu"],
                                                                    it["cach_m"], it["the"], it["osm"]))
    C.ghi_text(os.path.join(work, "tien_ich.txt"), "\n".join(lines) + "\n")
    to_ban_do(work, out)
    return out


def to_ban_do(work, data, out_name="tien_ich.jpg"):
    """bản đồ vệ tinh quanh nhà: vòng bán kính, ghim nhóm + số thứ tự, bảng tên bên dưới"""
    from PIL import Image, ImageDraw
    import ban_do as B
    nha = data["nha"]
    R = float(data["ban_kinh_m"])
    dlat = R / 111320.0
    dlon = R / (111320.0 * math.cos(math.radians(nha[0])))
    cam = B.Camera.vua_bbox([nha[0] - dlat, nha[1] - dlon, nha[0] + dlat, nha[1] + dlon], le=0.04, vung_y=(0.0, 0.62))
    nen = B.Nen()
    nen.tai_truoc(cam.o_can(nen))
    fr = B.lam_toi(cam.render(nen), 0.85, 0.9)
    im = Image.fromarray(fr).convert("RGBA")
    d = ImageDraw.Draw(im)
    xn, yn = cam.chieu(nha[0], nha[1])
    for r_m in (500, 1000, 1500, 2000):
        if r_m > R * 1.05:
            break
        rp = r_m / cam.m_per_px()
        d.ellipse((xn - rp, yn - rp, xn + rp, yn + rp), outline=(255, 255, 255, 200), width=3)
        d.text((xn + 8, yn - rp + 6), "%d m" % r_m, font=C.font("bold", 26), fill=(255, 255, 255, 255))
    for id_, it in data["muc"].items():
        x, y = cam.chieu(it["dich"][0], it["dich"][1])
        P = np.array([cam.chieu(p[0], p[1]) for p in it["duong"]["diem"]])
        if len(P) >= 2:
            d.line([tuple(q) for q in P], fill=tuple(BT.nhom(it["nhom"])["mau"]) + (150,), width=2)
        sp = BT.ghim(it["nhom"], 0.62)
        im.alpha_composite(sp[0], (int(x - sp[2]), int(y - sp[3])))
        so = id_.rsplit("_", 1)[1]
        d.text((x + 16, y - 52), "%s%s" % (it["nhom"][:2].upper(), so), font=C.font("xbold", 22), fill=(255, 255, 255, 255),
               stroke_width=3, stroke_fill=(0, 0, 0, 255))
    sp = BT.ghim_nha(1.0)
    im.alpha_composite(sp[0], (int(xn - sp[2]), int(yn - sp[3])))
    y = int(C.H * 0.62) + 10
    d.rectangle((0, y - 6, C.W, C.H), fill=(14, 20, 32, 255))
    f = C.font("semi", 21)
    col = 0
    for id_, it in data["muc"].items():
        so = id_.rsplit("_", 1)[1]
        d.text((14 + col * 540, y), "%s%s %s · %s" % (it["nhom"][:2].upper(), so, it["ten"][:26], it["chu"]), font=f,
               fill=tuple(BT.nhom(it["nhom"])["mau"]))
        col = 1 - col
        if col == 0:
            y += 27
        if y > C.H - 30:
            break
    out = os.path.join(work, out_name)
    im.convert("RGB").save(out, quality=88)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--ban-kinh", dest="ban_kinh", type=float)
    ap.add_argument("--nhom", help="danh sách nhóm, phẩy ngăn (mặc định: các nhóm mac_dinh trong bieu_tuong.NHOM)")
    ap.add_argument("--toi-da", dest="toi_da", type=int)
    ap.add_argument("--khong-mang", dest="khong_mang", action="store_true")
    a = ap.parse_args()
    work = os.path.abspath(a.work)
    plan = C.jload(os.path.join(work, "ke_hoach.json"))
    ti = plan.get("tien_ich") or {}
    R = a.ban_kinh or float(ti.get("ban_kinh_m", 1500))
    nhom = a.nhom.split(",") if a.nhom else ti.get("nhom")
    toi_da = a.toi_da or int(ti.get("toi_da", 6))
    print("▶ quét tiện ích bán kính %d m, %s" % (R, ", ".join(nhom) if nhom else "các nhóm mặc định"))
    out = quet(work, R, nhom, toi_da, a.khong_mang)
    print("✅ %d tiện ích → tien_ich.json · tien_ich.txt · tien_ich.jpg (Claude MỞ XEM)" % len(out["muc"]))


if __name__ == "__main__":
    main()
