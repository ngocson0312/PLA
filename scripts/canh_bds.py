# -*- coding: utf-8 -*-
"""Cảnh BẢN ĐỒ BĐS (loai "ban_do") — 1 cảnh = camera nhiều điểm dừng + các lớp bám lời:

  {"loai": "ban_do", "tu": 11.4, "den": 15.4, "loi": "...",
   "cam": [ {"t": 11.4, "tam": "nha", "zoom": 16.2},                      # điểm dừng đầu (camera đứng sẵn)
            {"t": 12.9, "dai": 1.4, "vua": ["nha", "dai_su_quan_1", "truong_3"], "le": 0.2},   # bay tới khung vừa
            {"t": 27.3, "dai": 1.6, "tam": "ho_hoan_kiem", "zoom": 14.0} ],
   "troi": 0.015,                     # zoom trôi chậm / giây khi camera đứng (mặc định 0,015)
   "nha": true | {"t": 0.9, "nhan": false},       # ghim lô đất (mặc định có, hiện sẵn); t = lúc ghim rơi
   "vong": [{"r_m": 500, "t": 12.0}],             # vòng bán kính quanh nhà
   "tien_ich": [{"id": "ho_6", "t": 16.1, "duong": true, "nhan": "HỒ TÂY"}, …],   # id tien_ich.json | key dia_diem
   "tuyen_sang": [{"tuyen": "xuan_dieu", "t": 9.8, "kieu": "duong", "ten": "PHỐ XUÂN DIỆU"}],
   "vung_sang": [{"vung": "ho_tay", "t": 16.1, "nhan": "HỒ TÂY"}],
   "toi": [[t, muc], …],              # làm tối bản đồ (0–0,7) theo mốc giây — khi có thẻ ảnh/thông tin ở giữa
   "nhan_manh": [...], "dau_de": [...], "dia_danh": false,
   # KIỂU MẪU (cai_dat.phong_cach = "mau" hoặc canh.phong_cach = "mau" — bản đồ tối, nét neon, ghim vàng; xem lop_mau.py):
   "neon": [{"tuyen": "dang_thai_mai", "t": 10.4, "ten": "ĐƯỜNG ĐẶNG THAI MAI", "lech_m": 120, "lech_px": 44}],
   "lo_dat": {"t": 41.0, "rong_m": 15, "sau_m": 16.7, "theo_duong": "duong_truoc_nha", "nhan": "250m²",
              "canh": [{"canh": "truoc", "chu": "15m", "t": 44.9}]},
   "chu_lon": [{"t": 16.2, "chu": "HỒ TÂY", "tai": [21.06, 105.82], "goc": -6}],
   "bien_anh": [{"id": "nha_hat", "t": 23.0, "anh": "x.jpg" | null, "nhan": "Nhà hát Cánh Buồm"}],
   "thuoc": [{"t": 16.4, "a": "nha", "b": "ho_6", "chu": "≈ 130 m"}],
   "tieu_de_tren": [{"t": 11.4, "dong": ["Nơi định vị", "ĐẲNG CẤP SỐNG"], "vang": ["ĐẲNG CẤP SỐNG"]}]}

Tiện ích lấy từ work/tien_ich.json (đã đo đường OSRM) hoặc từ dia_ly/<key>.json (đường đi tự tính OSRM, cache).
Chữ khoảng cách = số đo bản đồ, luôn "≈"; ô tô KHÔNG ghi phút (trừ khi "thoi_gian": true).
"""
import os

import numpy as np

import ban_do as B
import bieu_tuong as BT
import chung as C
import diem_nhan as DN
import lop_bds as L
import lop_mau as LM
import tien_ich as TI
from chung import W, H, clamp, ramp, smooth


def _ctx_ti(ctx):
    if "_ti" not in ctx:
        p = os.path.join(ctx["dl"].work, "tien_ich.json")
        ctx["_ti"] = C.jload(p)["muc"] if os.path.isfile(p) else {}
    return ctx["_ti"]


def diem_bds(ctx, x):
    """'nha' | id tiện ích | key địa điểm | [lat, lon] → [lat, lon]"""
    if x == "nha":
        return list(ctx["nha_p"])
    if isinstance(x, str):
        ti = _ctx_ti(ctx)
        if x in ti:
            m = ti[x]
            return [m["lat"], m["lon"]]
    return ctx["dl"].diem(x)


def diem_ghim(ctx, x):
    """như diem_bds nhưng hồ / công viên lớn trả `dich` (mép gần nhà, chỗ ghim) thay vì tâm vùng"""
    if isinstance(x, str) and x != "nha":
        ti = _ctx_ti(ctx)
        if x in ti and ti[x].get("dich"):
            return list(ti[x]["dich"])
    return diem_bds(ctx, x)


def giai_tien_ich(ctx, d):
    """1 mục tiện ích của cảnh → tham số cho lop_bds.DiemTienIch"""
    ti = _ctx_ti(ctx)
    k = d.get("id") or d.get("diem")
    out = {"t": float(d["t"]), "nhan": d.get("nhan", True) is not False, "co": d.get("co", 0.95),
           "dai_ve": d.get("dai_ve"), "mau": d.get("mau"), "co_chu": d.get("co_chu", 25)}
    muon_duong = d.get("duong", True)
    if isinstance(k, str) and k in ti:
        m = ti[k]
        out["p"] = [m["lat"], m["lon"]]
        out["ten"] = d["nhan"] if isinstance(d.get("nhan"), str) else m["ten"]
        out["nhom"] = d.get("nhom") or m["nhom"]
        dg = m.get("duong") or {}
        out["kieu"] = dg.get("kieu")
        out["chu"] = d["chu"] if "chu" in d else m.get("chu")
        if muon_duong and dg.get("diem"):
            out["duong"] = dg["diem"]
        if m.get("dich") and out.get("duong"):
            out["p"] = list(m["dich"])          # hồ / công viên: ghim ở mép gần nhà (đích đường đi)
    else:
        dl = ctx["dl"]
        p = diem_bds(ctx, k)
        out["p"] = p
        out["ten"] = d["nhan"] if isinstance(d.get("nhan"), str) else dl.ten(k, "")
        out["nhom"] = d.get("nhom", "trung_tam")
        kieu = d.get("kieu") or ("o_to" if C.khoang_cach_m(ctx["nha_p"], p) > 1200 else "di_bo")
        if muon_duong:
            r = TI.duong_di(ctx["nha_p"], p, kieu, chi_cache=not ctx.get("mang", True))
            out["duong"] = r["diem"]
            out["kieu"] = r["kieu"]
            if "chu" in d:
                out["chu"] = d["chu"]
            else:
                out["chu"] = TI.chu_khoang_cach(r["met"], r.get("giay"), r["kieu"], d.get("thoi_gian"))
        else:
            out["chu"] = d.get("chu")
            out["kieu"] = None
    if out.get("dai_ve") is None:
        out.pop("dai_ve")
    if out.get("mau") is None:
        out.pop("mau")
    return out


def bbox_cua(ctx, ds, them_duong=True):
    pts = []
    for x in ds:
        if isinstance(x, str) and x != "nha":
            ti = _ctx_ti(ctx)
            if x in ti:
                m = ti[x]
                # hồ / công viên lớn: lat/lon là TÂM vùng (Hồ Tây ⇒ giữa hồ) còn ghim vẽ ở `dich` (mép gần nhà) ⇒ khung theo dich
                pts.append(list(m.get("dich") or [m["lat"], m["lon"]]))
                if them_duong and (m.get("duong") or {}).get("diem"):
                    pts += m["duong"]["diem"]
                continue
            g = ctx["dl"].lay(x)
            if g.get("bbox") and (g.get("vong") or g.get("tuyen")) and not g.get("diem_chi"):
                b = g["bbox"]
                pts += [[b[0], b[1]], [b[2], b[3]]]
                continue
        pts.append(diem_bds(ctx, x))
    a = np.asarray(pts, dtype=np.float64)
    return [float(a[:, 0].min()), float(a[:, 1].min()), float(a[:, 0].max()), float(a[:, 1].max())]


def tao_canh_bds(Canh):
    """dung.py truyền lớp Canh gốc vào ⇒ trả lớp BanDo kế thừa"""

    class BanDo(Canh):
        loai = "ban_do"

        def __init__(self, it, ctx):
            super().__init__(it, ctx)
            self.kf = []
            cam = it.get("cam") or [{"t": self.t0, "tam": "nha", "zoom": 16.0}]
            for k in cam:
                t = float(k.get("t", self.t0))
                if k.get("vua"):
                    bb = bbox_cua(ctx, k["vua"], k.get("theo_duong", True))
                    c = B.Camera.vua_bbox(bb, le=float(k.get("le", 0.16)), vung_y=tuple(k.get("vung_y", (0.13, 0.70))),
                                          z_max=float(k.get("zoom_toi_da", 17.6)))
                    if k.get("zoom_bot"):
                        c = B.Camera(c.lat, c.lon, c.zf - float(k["zoom_bot"]))
                else:
                    p = diem_bds(ctx, k.get("tam", "nha"))
                    c = B.Camera(p[0], p[1], float(k.get("zoom", 16.0)))
                    if k.get("lech_y"):
                        # dời tâm cho điểm nằm cao/thấp hơn giữa khung (px màn hình, + = điểm nằm cao hơn)
                        cx, cy = C.ll2px(p[0], p[1], c.z)
                        la, lo = C.px2ll(cx, cy + float(k["lech_y"]) / c.k, c.z)
                        c = B.Camera(la, lo, c.zf)
                self.kf.append((t, float(k.get("dai", 1.2)), c))
            self.kf.sort(key=lambda x: x[0])
            self.troi = float(it.get("troi", 0.015))
            # lớp
            self.mau = (it.get("phong_cach") or ctx["cai_dat"].get("phong_cach")) == "mau"
            nha = it.get("nha", True)
            self.nha = None
            if nha:
                nd = dict(ctx["nha"])
                nt = -99.0
                if isinstance(nha, dict):
                    nd.update({k: v for k, v in nha.items() if k in ("nhan", "phu", "chinh_xac", "ban_kinh_m", "mui_ten")})
                    nt = float(nha.get("t", -99.0))
                    if nha.get("nhan") is False:
                        nd["nhan"] = ""
                self.nha = LM.NhaGhimVang(nd) if self.mau else L.NhaMarker(nd)
                self.nha_t = nt
            self.vong = [dict(v) for v in it.get("vong", [])]
            if self.vong:
                # hướng đặt nhãn vòng: xa các ghim tiện ích nhất (tính 1 lần ⇒ nhãn không nhảy)
                import math as _m
                n0 = ctx["nha_p"]
                gg = []
                for d in it.get("tien_ich", []):
                    try:
                        q = diem_ghim(ctx, d.get("id") or d.get("diem"))
                    except SystemExit:
                        continue
                    gg.append(_m.degrees(_m.atan2(-(q[0] - n0[0]), (q[1] - n0[1]) * _m.cos(_m.radians(n0[0])))))
                for v in self.vong:
                    if v.get("huong_nhan") is not None:
                        v["_goc"] = float(v["huong_nhan"])
                    v["_goc_ds"] = LM.huong_trong(gg, bool(it.get("tieu_de_tren")))
            Ghim = LM.GhimVang if self.mau else L.DiemTienIch
            self.ti = [Ghim(giai_tien_ich(ctx, d)) for d in it.get("tien_ich", [])]
            dl = ctx["dl"]
            # lớp kiểu mẫu (dùng được ở cả 2 phong cách)
            self.neon = [LM.DuongNeon(d, dl.lay(d["tuyen"]), ctx["nha_p"]) for d in it.get("neon", [])]
            ld = it.get("lo_dat")
            self.lo_dat = LM.LoDat(ld, diem_bds(ctx, ld.get("tam", "nha")),
                                   dl.lay(ld["theo_duong"]) if ld.get("theo_duong") else None) if ld else None
            self.chu_lon = [LM.ChuLon(d, diem_bds(ctx, d["tai"])) for d in it.get("chu_lon", [])]
            self.bien = []
            for d in it.get("bien_anh", []):
                g = giai_tien_ich(ctx, dict(d, duong=d.get("duong", True)))
                dd = dict(d)
                dd["p"] = g["p"]
                dd["duong"] = g.get("duong") if d.get("duong", True) else None
                nen_ = None
                if d.get("anh"):
                    dd["anh"] = ctx["tim_file"](d["anh"])
                else:
                    nen_ = ctx.setdefault("_nen_bien", B.Nen(mang=ctx.get("mang", True)))
                if not isinstance(dd.get("nhan"), str):
                    dd["nhan"] = g.get("ten") or ""
                self.bien.append(LM.BienAnh(dd, nen_))
            self.thuoc = []
            for d in it.get("thuoc", []):
                a_, b_ = diem_ghim(ctx, d.get("a", "nha")), diem_ghim(ctx, d["b"])
                chu = d.get("chu")
                if chu is None:
                    m_ = C.khoang_cach_m(a_, b_)
                    chu = ("≈ %d m" % (round(m_ / 10.0) * 10)) if m_ < 1000 else ("≈ %.1f km" % (m_ / 1000)).replace(".", ",")
                self.thuoc.append(LM.ThuocNeon({"t": d["t"], "a": a_, "b": b_, "chu": chu}))
            self.td = [LM.TieuDeTren(d, self.t1) for d in it.get("tieu_de_tren", [])]
            self.tuyen = [L.TuyenSang(d, dl.lay(d["tuyen"])) for d in it.get("tuyen_sang", [])]
            self.vung = [L.VungSang(d, dl.lay(d["vung"])) for d in it.get("vung_sang", [])]
            self.toi = [(float(a), float(b)) for a, b in it.get("toi", [])]
            if it.get("dia_danh"):
                c0 = self.kf[-1][2]
                r_km = clamp(960 * c0.m_per_px() / 1000 * 1.3, 0.8, 30.0)
                self.dia_danh = self.tao_dia_danh([[c0.lat, c0.lon]], 1.0, r_km, mac_dinh=True)

        # ---- camera
        def cam(self, t):
            kf = self.kf
            c = kf[0][2]
            t_dung = self.t0
            for i in range(1, len(kf)):
                ti, dai, ci = kf[i]
                if t < ti:
                    break
                u = smooth(clamp((t - ti) / max(0.05, dai)))
                if u < 1:
                    return B.noi_suy(c, ci, u)
                c = ci
                t_dung = ti + dai
            if t < self.t0:
                return c
            return B.Camera(c.lat, c.lon, c.zf + self.troi * max(0.0, t - t_dung))

        def o_can(self, nen):
            ks = set()
            n = max(2, int(self.dur / 0.2) + 1)
            for i in range(n):
                ks |= self.cam(self.t0 + self.dur * i / (n - 1)).o_can(nen)
            return ks

        def vi_tri(self, t, cam):
            return self.ctx["nha_p"]

        def nen(self, t, nen):
            c_ = self.cam(t)
            fr = c_.render(nen)
            k_net = clamp((c_.zf - 19.2) / 1.5) * float(self.it.get("net", 0.9))
            if k_net > 0.02:
                # cận cảnh vượt z19 (ảnh Esri tối đa z19) ⇒ làm nét nhẹ cho đỡ bệt
                import cv2 as _cv
                bl = _cv.GaussianBlur(fr, (0, 0), 2.2)
                fr = _cv.addWeighted(fr, 1 + k_net, bl, -k_net, 0)
            if self.mau:
                cd = self.ctx["cai_dat"]
                LM.nen_toi(fr, float(self.it.get("nen_sang", cd.get("nen_sang", 0.66))),
                           float(cd.get("nen_bao_hoa", 0.78)), float(cd.get("nen_vien", 0.42)))
            return fr

        # ---- lớp
        def lop(self, frame, t, cam):
            k = 0.0
            if self.toi:
                xs = [x[0] for x in self.toi]
                ys = [x[1] for x in self.toi]
                k = float(np.interp(t, xs, ys))
            if k > 0.003:
                frame[:] = (frame.astype(np.float32) * (1 - k)).astype(np.uint8)
            # 0. tiêu đề trên cùng (kiểu mẫu) giữ chỗ trước để nhãn né
            td_on = [d for d in self.td if d.t0 <= t <= d.t1]
            for d in td_on:
                self.chiem.dat(d.rect())
            # 1. nét bản đồ: vùng, tuyến, neon, lô đất, vòng, đường đi
            cung = list(self.chiem.r)          # vùng cấm cứng (sub, đầu đề, thẻ…) + nhãn đã đặt
            for v in self.vung:
                v.ve(frame, cam, t)
            for v in self.tuyen:
                v.ve(frame, cam, t)
            for v in self.neon:
                v.ve(frame, cam, t)
            if self.lo_dat is not None:
                self.lo_dat.ve(frame, cam, t, self.chiem)
            nha_p = self.ctx["nha_p"]
            for v in self.vong:
                tl = t - float(v.get("t", self.t0))
                if self.mau:
                    r = LM.ve_vong_mau(frame, cam, nha_p, float(v["r_m"]), tl, phan="vong")
                else:
                    r = L.ve_vong(frame, cam, nha_p, float(v["r_m"]), tl, C.TRANG, v.get("nhan"))
                if r:
                    self.chiem.dat(r)
                    cung.append(r)
            for d in self.ti:
                d.ve_duong(frame, cam, t)
            for d in self.bien:
                d.ve_duong(frame, cam, t)
            for d in self.thuoc:
                d.ve(frame, cam, t, self.chiem)
            # 2. ghim: nhà rồi tiện ích, biển ảnh, chữ địa danh lớn
            if self.nha is not None:
                self.nha.ve(frame, cam, t - self.nha_t, self.chiem)
                if self.mau:
                    self.nha.dat_nhan(t - self.nha_t, self.chiem, cung)
            if self.mau:
                # kiểu mẫu: tiện ích GIỮ CHỖ nhãn sát ghim trước (theo thứ tự hiện); không có chỗ ⇒ ẩn cả ghim
                for d in sorted(self.ti, key=lambda x: x.t_ghim):
                    d.dat_cho(cam, t, self.chiem, cung)
                for v in self.vong:          # nhãn vòng nhường chỗ cho ghim
                    if "_cuoi" not in v:
                        c1 = self.cam(self.t1 - 0.05)
                        xe, ye = c1.chieu(nha_p[0], nha_p[1])
                        v["_cuoi"] = (xe, ye, float(v["r_m"]) / c1.m_per_px())
                    r = LM.ve_vong_mau(frame, cam, nha_p, float(v["r_m"]), t - float(v.get("t", self.t0)), v.get("nhan"),
                                       chiem=self.chiem, nho=v, phan="nhan")
                    if r:
                        self.chiem.dat(r)
                        cung.append(r)
            for d in self.ti:
                d.ve_ghim(frame, cam, t, self.chiem)
            for d in self.bien:
                d.ve(frame, cam, t, self.chiem)
            for d in self.chu_lon:
                d.ve(frame, cam, t, self.chiem)
            # 3. nhãn: nhà trước (ưu tiên chỗ), tiện ích theo thứ tự xuất hiện, rồi tên tuyến / vùng
            if self.nha is not None:
                self.nha.ve_nhan(frame, t - self.nha_t, self.chiem, cung)
            for d in sorted(self.ti, key=lambda x: x.t_ghim):
                d.ve_nhan(frame, cam, t, self.chiem, cung)
            for v in self.neon:
                v.ve_ten(frame, cam, t, self.chiem)
            for v in self.tuyen:
                v.ve_ten(frame, t, self.chiem)
            for v in self.vung:
                v.ve_nhan(frame, cam, t, self.chiem)
            for d in td_on:
                d.ve(frame, t)

        def sfx(self):
            ev = []
            for i in range(1, len(self.kf)):
                dz = abs(self.kf[i][2].zf - self.kf[i - 1][2].zf)
                dm = C.khoang_cach_m((self.kf[i][2].lat, self.kf[i][2].lon), (self.kf[i - 1][2].lat, self.kf[i - 1][2].lon))
                if dz >= 1.2 or dm > 3 * self.kf[i - 1][2].m_per_px() * 300:
                    ev.append({"t": self.kf[i][0], "file": "whoosh-short.mp3", "muc": "nhe"})
            if self.nha is not None and self.nha_t >= self.t0 - 0.05:
                ev.append({"t": self.nha_t + 0.4, "file": "ding.mp3", "muc": "nhe"})
            for d in self.ti:
                ev.append({"t": d.t_ghim, "file": "pop.mp3", "muc": "rat_nhe"})
                if d.duong is not None and d.dai_ve >= 0.8:
                    ev.append({"t": d.t, "file": "swoosh.mp3", "muc": "rat_nhe"})
            for v in self.vung:
                ev.append({"t": v.t, "file": "pop-2.mp3", "muc": "rat_nhe"})
            for v in self.neon:
                ev.append({"t": v.t, "file": "swoosh.mp3", "muc": "rat_nhe"})
            if self.lo_dat is not None:
                # lô đất: quét đầy (swoosh) → chữ diện tích (sparkle) → mỗi ngoặc đo (pop)
                ev.append({"t": self.lo_dat.t, "file": "swoosh.mp3", "muc": "nhe"})
                if self.lo_dat.d.get("nhan"):
                    ev.append({"t": self.lo_dat.t_nhan, "file": "sparkle.mp3", "muc": "nhe"})
                for c_ in self.lo_dat.canh:
                    ev.append({"t": float(c_.get("t", self.lo_dat.t_nhan + 0.4)) + 0.05, "file": "pop.mp3", "muc": "nhe"})
            for d in self.bien:
                ev.append({"t": d.t_bien + 0.12, "file": "camera-shutter.mp3", "muc": "rat_nhe"})
            for d in self.chu_lon:
                ev.append({"t": d.t, "file": "pop-2.mp3", "muc": "rat_nhe"})
            for d in self.thuoc:
                ev.append({"t": d.t, "file": "quick-swoosh.mp3", "muc": "rat_nhe"})
            for d in self.td:
                ev.append({"t": d.t0, "file": "quick-swoosh.mp3", "muc": "rat_nhe"})
            if self.mau:
                for v in self.vong:
                    ev.append({"t": float(v.get("t", self.t0)), "file": "swoosh.mp3", "muc": "rat_nhe"})
            return ev

    return BanDo
