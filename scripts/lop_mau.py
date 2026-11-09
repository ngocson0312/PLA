# -*- coding: utf-8 -*-
"""Bộ lớp đồ hoạ KIỂU MẪU (phân tích Video_Mau.mp4 khách gửi 09/11/2026 — "chi tiết hình dạng hơn như này"):

  nen_toi        nền vệ tinh TỐI + bớt màu + viền tối (nét neon nổi bật)
  DuongNeon      đường phát sáng NEON vàng chanh (lõi sáng + quầng), VỆT SÁNG chạy dọc tuyến lặp lại,
                 TÊN ĐƯỜNG to viết XOAY THEO HƯỚNG ĐƯỜNG (trắng → vàng cam, hiện dần từ trái sang phải)
  GhimVang       ghim giọt nước VÀNG có icon tối trong vòng trắng, vòng elip dưới chân, nhãn vàng nghiêng phía trên
                 (+ dòng khoảng cách "≈ 130 m"); đường đi NÉT ĐỨT VÀNG từ nhà tới tiện ích
  NhaGhimVang    ghim nhà vàng to RƠI XUỐNG nảy + MŨI TÊN CONG vẽ tay + nhãn "VỊ TRÍ ĐẤT" vàng nghiêng
  ve_vong_mau    vòng bán kính mảnh vàng (quầng nhẹ) + nhãn nhỏ
  LoDat          HÌNH DẠNG LÔ ĐẤT cận cảnh: khối CYAN phát sáng quét đầy dần, xoay theo hướng lô (tự song song đường
                 gần nhất), chữ diện tích giữa lô, NGOẶC ĐO kích thước kèm số (chỉ số có trong lời)
  ChuLon         chữ địa danh LỚN phát sáng đặt trên bản đồ (mặt hồ…), từng chữ nảy lên
  BienAnh        BIỂN ẢNH cắm cọc ở tiện ích (ảnh + dải nhãn xanh), đường nét đứt vàng từ nhà chạy tới
  TieuDeTren     tiêu đề 2 dòng trên cùng: chữ trắng đậm bóng tối, cụm khoá VÀNG
  ThuocNeon      thước đo nét đứt trắng nhà → điểm + nhãn vàng "≈ 130 m"
Mọi hình vẽ bằng PIL / OpenCV, không tải ảnh ngoài (trừ ảnh biển do người dùng / Resources đưa).
"""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import ban_do as B
import bieu_tuong as BT
import chung as C
import diem_nhan as DN
from chung import W, H, clamp, ramp, smooth, ease_out

NEON = (206, 255, 40)
NEON_LOI = (246, 255, 196)
VANG_G1, VANG_G2 = (255, 226, 92), (236, 158, 18)
VANG_CHU = (255, 214, 48)
CYAN = (38, 168, 255)
CYAN_SANG = (140, 226, 255)
XANH_BIEN = (28, 108, 228)
SS = 4


# ---------------------------------------------------------------- tiện ích chung

def nghieng(im, k=0.2):
    """chữ nghiêng giả (Montserrat không có italic): xô ngang theo chiều cao"""
    w, h = im.size
    dx = int(abs(k) * h) + 2
    return im.transform((w + dx, h), Image.AFFINE, (1, k, -dx if k > 0 else 0, 0, 1, 0), resample=Image.BICUBIC)


def chu_gradient(text, key, size, c_tren=C.TRANG, c_duoi=(255, 190, 80), bong=(0, 5, 8, 0.75), vien=0, glow=None,
                 track=1):
    """chữ tô gradient dọc + bóng tối (+ quầng màu) → PIL RGBA"""
    m = C.chu(text, key, size, fill=C.TRANG, stroke=vien, stroke_fill=(20, 16, 10), track=track)
    a = np.asarray(m).astype(np.float32)
    h = a.shape[0]
    g = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    ct, cd = np.array(c_tren, np.float32), np.array(c_duoi, np.float32)
    col = ct * (1 - g) + cd * g
    lum = a[..., :3] / 255.0           # viền tối giữ tối
    a[..., :3] = col * lum
    chu = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    pad = 30
    out = Image.new("RGBA", (chu.width + 2 * pad, chu.height + 2 * pad), (0, 0, 0, 0))
    if glow is not None:
        gl = Image.new("RGBA", out.size, tuple(glow[:3]) + (0,))
        al = Image.new("L", out.size, 0)
        al.paste(chu.getchannel("A"), (pad, pad))
        gl.putalpha(al.filter(ImageFilter.GaussianBlur(glow[3] if len(glow) > 3 else 14)).point(lambda v: int(v * 0.9)))
        out.alpha_composite(gl)
    if bong:
        dx, dy, bl, al_ = bong
        sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
        al = Image.new("L", out.size, 0)
        al.paste(chu.getchannel("A"), (pad + int(dx), pad + int(dy)))
        sh.putalpha(al.filter(ImageFilter.GaussianBlur(bl)).point(lambda v: int(v * al_)))
        out.alpha_composite(sh)
    out.alpha_composite(chu, (pad, pad))
    bb = out.getbbox()
    return out.crop(bb) if bb else out


def _cat(P, u0, u1):
    """đoạn polyline theo tỉ lệ chiều dài [u0, u1]"""
    P = np.asarray(P, np.float64)
    if len(P) < 2:
        return P
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    L = cum[-1]
    if L <= 0:
        return P[:1]
    s0, s1 = clamp(u0) * L, clamp(u1) * L

    def tai(s):
        i = int(np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(P) - 2))
        t = (s - cum[i]) / seg[i] if seg[i] > 0 else 0.0
        return P[i] + (P[i + 1] - P[i]) * t, i
    a, ia = tai(s0)
    b, ib = tai(s1)
    return np.vstack([a[None], P[ia + 1:ib + 1], b[None]])


def ve_net_dut(frame, P, mau, day=4, dash=16, gap=11, alpha=1.0, lech=0.0):
    """nét đứt dọc polyline màn hình"""
    P = np.asarray(P, np.float64)
    if len(P) < 2 or alpha <= 0.003:
        return
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    L = float(seg.sum())
    if L < 2:
        return
    doan = []
    s = -lech % (dash + gap)
    s -= (dash + gap)
    while s < L:
        a, b = max(0.0, s), min(L, s + dash)
        if b > a:
            doan.append(_cat(P, a / L, b / L))
        s += dash + gap
    x0, y0, x1, y1 = _vung(frame, P, day + 4)

    def ve(l, ox, oy):
        cv2.polylines(l, [np.round(Q - [ox, oy]).astype(np.int32) for Q in doan], False, tuple(int(v) for v in mau),
                      day, cv2.LINE_AA)
    if alpha >= 0.999:
        ve(frame, 0, 0)
    else:
        _tron_vung(frame, x0, y0, x1, y1, ve, alpha)


def _vung(frame, pts, pad):
    x0 = int(max(0, np.floor(pts[:, 0].min()) - pad))
    y0 = int(max(0, np.floor(pts[:, 1].min()) - pad))
    x1 = int(min(frame.shape[1], np.ceil(pts[:, 0].max()) + pad))
    y1 = int(min(frame.shape[0], np.ceil(pts[:, 1].max()) + pad))
    return x0, y0, x1, y1


def ve_phat_sang(frame, polys, mau_quang, day_quang, mau_loi, day_loi, cuong=1.0, loi_trang=True):
    """nét phát sáng: quầng mờ (cộng sáng kiểu screen, tính ở nửa độ phân giải) + lõi rõ"""
    polys = [np.asarray(P, np.float64) for P in polys if P is not None and len(P) >= 2]
    if not polys or cuong <= 0.003:
        return
    allp = np.vstack(polys)
    pad = day_quang * 3 + 10
    x0, y0, x1, y1 = _vung(frame, allp, pad)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    h, w = y1 - y0, x1 - x0
    hs, ws = max(2, h // 2), max(2, w // 2)
    q = np.zeros((hs, ws, 3), np.float32)
    for P in polys:
        Q = np.round((P - [x0, y0]) / 2.0).astype(np.int32)
        cv2.polylines(q, [Q], False, tuple(float(v) for v in mau_quang), max(1, day_quang // 2), cv2.LINE_AA)
    q = cv2.GaussianBlur(q, (0, 0), max(1.0, day_quang * 0.45))
    q = cv2.resize(q, (w, h), interpolation=cv2.INTER_LINEAR) * (1.25 * cuong)
    reg = frame[y0:y1, x0:x1].astype(np.float32)
    reg = reg + q - reg * q / 255.0
    core = np.zeros((h, w, 3), np.uint8)
    mk = np.zeros((h, w), np.uint8)
    for P in polys:
        Q = np.round(P - [x0, y0]).astype(np.int32)
        cv2.polylines(core, [Q], False, tuple(int(v) for v in mau_loi), day_loi, cv2.LINE_AA)
        cv2.polylines(mk, [Q], False, 255, day_loi, cv2.LINE_AA)
        if loi_trang and day_loi >= 5:
            cv2.polylines(core, [Q], False, (255, 255, 236), max(1, day_loi // 3), cv2.LINE_AA)
    m = (mk.astype(np.float32) / 255.0 * cuong)[..., None]
    reg = reg * (1 - m) + core.astype(np.float32) * m
    frame[y0:y1, x0:x1] = reg.clip(0, 255).astype(np.uint8)


_VIGNETTE = {}


def nen_toi(frame, sang=0.66, bao_hoa=0.78, vien=0.42):
    """nền vệ tinh tối kiểu mẫu: giảm sáng + bớt màu + viền tối 4 góc"""
    frame[:] = B.lam_toi(frame, sang, bao_hoa)
    if vien > 0:
        k = (frame.shape[0], frame.shape[1], round(vien, 2))
        if k not in _VIGNETTE:
            yy, xx = np.mgrid[0:k[0], 0:k[1]].astype(np.float32)
            r = np.hypot((xx - k[1] / 2) / (k[1] * 0.62), (yy - k[0] / 2) / (k[0] * 0.62))
            _VIGNETTE[k] = (1 - vien * np.clip(r - 0.45, 0, 1) ** 1.5)[..., None].astype(np.float32)
        frame[:] = (frame.astype(np.float32) * _VIGNETTE[k]).astype(np.uint8)


def _ll_cong_m(p, de_m, dn_m):
    """lat/lon + (đông m, bắc m)"""
    return [p[0] + dn_m / 111320.0, p[1] + de_m / (111320.0 * math.cos(math.radians(p[0])))]


# ---------------------------------------------------------------- ghim vàng giọt nước

def _ghim_vang(R, icon_ten, icon_mau=(52, 36, 8)):
    """→ (ảnh PIL, mũi x, mũi y): giọt nước gradient vàng, viền vàng sẫm, vòng trắng ngà + icon tối"""
    S = SS
    w, h = int(2 * R + 8), int(2.75 * R + 8)
    m = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(m)
    cx, cy = w * S / 2, (R + 4) * S
    rr = R * S
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=255)
    tip = (h - 4) * S
    d.polygon([(cx - rr * 0.80, cy + rr * 0.58), (cx + rr * 0.80, cy + rr * 0.58), (cx, tip)], fill=255)
    m = m.resize((w, h), Image.LANCZOS)
    g = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    col = np.array(VANG_G1, np.float32) * (1 - g) + np.array(VANG_G2, np.float32) * g
    rgb = np.repeat(col, w, axis=1).astype(np.uint8)
    im = Image.fromarray(np.dstack([rgb, np.asarray(m)]), "RGBA")
    vi = m.filter(ImageFilter.MaxFilter(3))
    vien = Image.new("RGBA", (w, h), (150, 96, 6, 0))
    vien.putalpha(vi)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(vien)
    out.alpha_composite(im)
    # vòng trắng ngà + icon
    o = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    r2 = rr * 0.66
    ImageDraw.Draw(o).ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=(255, 250, 232, 255))
    o = o.resize((w, h), Image.LANCZOS)
    out.alpha_composite(o)
    ic = BT.icon(icon_ten, int(R * 0.86), icon_mau)
    out.alpha_composite(ic, (int(w / 2 - ic.width / 2), int(R + 4 - ic.height / 2)))
    # bóng kính
    hl = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    ImageDraw.Draw(hl).pieslice((cx - rr * 0.92, cy - rr * 0.92, cx + rr * 0.92, cy + rr * 0.92), 200, 300,
                                fill=(255, 255, 255, 70))
    out.alpha_composite(hl.resize((w, h), Image.LANCZOS))
    return out, w / 2, h - 4


def _nhan_vang(ten, phu=None, co=25, mau=VANG_CHU):
    """nhãn trên ghim: tên vàng IN HOA nghiêng + (dòng phụ trắng nhỏ) — bóng tối, không hộp"""
    t1 = nghieng(C.chu(ten.upper(), "black", co, fill=mau, shadow=(0, 2, 4, 0.9), track=1))
    if not phu:
        return t1
    t2 = C.chu(phu, "bold", int(co * 0.86), fill=C.TRANG, shadow=(0, 2, 4, 0.9))
    w = max(t1.width, t2.width)
    out = Image.new("RGBA", (w, t1.height + t2.height + 2), (0, 0, 0, 0))
    out.alpha_composite(t1, ((w - t1.width) // 2, 0))
    out.alpha_composite(t2, ((w - t2.width) // 2, t1.height + 2))
    return out


def _tron_vung(frame, x0, y0, x1, y1, ve, alpha):
    """vẽ ve(lop, ox, oy) lên bản sao 1 VÙNG rồi trộn alpha (khỏi chép cả khung)"""
    x0, y0 = int(max(0, x0)), int(max(0, y0))
    x1, y1 = int(min(frame.shape[1], x1)), int(min(frame.shape[0], y1))
    if x1 - x0 < 2 or y1 - y0 < 2 or alpha <= 0.003:
        return
    reg = frame[y0:y1, x0:x1]
    lop = reg.copy()
    ve(lop, x0, y0)
    cv2.addWeighted(lop, alpha, reg, 1 - alpha, 0, dst=reg)


def _elip_dat(frame, x, y, rx, ry, alpha):
    if alpha <= 0.01:
        return
    c, ax = (int(x), int(y)), (max(1, int(rx)), max(1, int(ry)))
    _tron_vung(frame, x - rx - 4, y - ry - 4, x + rx + 5, y + ry + 5,
               lambda l, ox, oy: cv2.ellipse(l, (c[0] - ox, c[1] - oy), ax, 0, 0, 360, (24, 20, 12), -1, cv2.LINE_AA),
               0.45 * alpha)
    _tron_vung(frame, x - rx - 4, y - ry - 4, x + rx + 5, y + ry + 5,
               lambda l, ox, oy: cv2.ellipse(l, (c[0] - ox, c[1] - oy), ax, 0, 0, 360, (255, 236, 170), 2, cv2.LINE_AA),
               0.8 * alpha)


class GhimVang:
    """tiện ích kiểu mẫu — cùng giao diện DiemTienIch (ve_duong / ve_ghim / ve_nhan, t, t_ghim, dai_ve, duong).
    d (đã giải bởi canh_bds.giai_tien_ich): {p, ten, nhom, chu, duong, t, dai_ve, nhan, hien_chu (true)}"""

    def __init__(self, d):
        self.d = d
        self.p = d["p"]
        g = BT.nhom(d.get("nhom"))
        self.duong = np.asarray(d["duong"], dtype=np.float64) if d.get("duong") else None
        self.dai_ve = float(d.get("dai_ve", 1.0 if self.duong is not None else 0.0))
        self.t_ghim = float(d["t"])
        self.t = self.t_ghim - (self.dai_ve if self.duong is not None else 0.0)
        R = float(d.get("r", 30))
        self.img, self.tx, self.ty = _ghim_vang(R, g["icon"])
        self.arr = np.asarray(self.img)
        phu = d.get("chu") if d.get("hien_chu", True) else None
        self.lab = np.asarray(_nhan_vang(d["ten"], phu, int(d.get("co_chu", 24)))) \
            if d.get("nhan", True) and d.get("ten") else None

    def ve_duong(self, frame, cam, t, alpha=1.0):
        if self.duong is None or t < self.t or alpha <= 0.003:
            return
        P = cam.chieu_mang(self.duong)
        u = smooth(clamp((t - self.t) / max(0.05, self.dai_ve)))
        part, head = B.doan_theo_tien_do(P, u)
        ve_net_dut(frame, part, (20, 16, 6), 7, 16, 11, alpha * 0.55)
        ve_net_dut(frame, part, VANG_CHU, 4, 16, 11, alpha)
        if u < 0.999 and head is not None:
            B.ve_cham(frame, head[0], head[1], 6, C.TRANG, alpha=alpha)

    def dat_cho(self, cam, t, chiem, cung):
        """GIỮ CHỖ trước khi vẽ (chốt 09/11/2026: không có icon trơ không tên): nhãn phải nằm NGAY TRÊN (hoặc ngay
        dưới) đúng ghim của nó; cả 2 chỗ đều vướng (sub, tiêu đề, nhãn khác, mép màn hình) ⇒ ẨN CẢ GHIM lẫn nhãn."""
        self._xy = self._hop = None
        tl = t - self.t_ghim
        if tl < 0:
            return
        x, y = cam.chieu(self.p[0], self.p[1])
        if not (-80 < x < W + 80 and -80 < y < H + 80):
            return
        r_ghim = (x - self.tx, y - self.ty, x + self.tx, y)
        if self.lab is None:                   # nhan: false (khai rõ) ⇒ ghim trơn
            self._xy = (x, y)
            chiem.dat(r_ghim)
            return
        h, w = self.lab.shape[:2]
        top = y - self.ty
        ung = [(x - w / 2, top - h - 4), (x - w / 2, y + 10)]
        hop = [(px, py, px + w, py + h) for px, py in ung]
        ok = [8 <= r[0] and r[2] <= W - 8 and 150 < r[1] and r[3] < H - 380 and not chiem.trung(r, 4) for r in hop]
        k = getattr(self, "_cho", None)
        if k is None or not ok[k]:
            k = next((i for i in range(len(hop)) if ok[i]), None)
            self._cho = k
        if k is None:
            return
        self._xy, self._hop, self._lab_xy = (x, y), hop[k], ung[k]
        chiem.dat(r_ghim)
        chiem.dat(hop[k])
        cung.append(hop[k])

    def ve_ghim(self, frame, cam, t, chiem, alpha=1.0):
        if getattr(self, "_xy", None) is None or alpha <= 0.003:
            return
        tl = t - self.t_ghim
        x, y = self._xy
        u = clamp(tl / 0.45)
        dy = -70 * (1 - DN.bounce_out(u))
        _elip_dat(frame, x, y, 24 * (0.5 + 0.5 * u), 8 * (0.5 + 0.5 * u), alpha * u)
        s = 0.55 + 0.45 * DN.back_out(clamp(tl / 0.3))
        C.dan_giua(frame, self.arr, x, y + dy - (self.ty - self.arr.shape[0] / 2) * s, alpha * clamp(tl / 0.1), s)

    def ve_nhan(self, frame, cam, t, chiem, cung, alpha=1.0):
        tl = t - self.t_ghim - 0.15
        if self.lab is None or tl < 0 or getattr(self, "_hop", None) is None:
            return
        a = ease_out(clamp(tl / 0.25)) * alpha
        px, py = self._lab_xy
        C.dan(frame, self.lab, px, py + 8 * (1 - a), a)


class NhaGhimVang:
    """ghim nhà kiểu mẫu: rơi xuống nảy + mũi tên cong + nhãn 'VỊ TRÍ ĐẤT' (+ dòng phụ). Giao diện như NhaMarker."""

    def __init__(self, nha):
        self.p = [float(nha["lat"]), float(nha["lon"])]
        self.chinh_xac = bool(nha.get("chinh_xac", True))
        self.r_m = float(nha.get("ban_kinh_m", 80))
        self.nhan = nha.get("nhan") if nha.get("nhan") is not None else \
            ("VỊ TRÍ ĐẤT" if self.chinh_xac else "KHU VỰC LÔ ĐẤT")
        self.phu = nha.get("phu")
        self.mui_ten = nha.get("mui_ten", True)
        self.img, self.tx, self.ty = _ghim_vang(44, "nha", (40, 28, 6))
        self.arr = np.asarray(self.img)
        self.lab = np.asarray(_nhan_vang(self.nhan, self.phu, 28)) if self.nhan else None

    def ve(self, frame, cam, tl, chiem, alpha=1.0):
        self._xy = None
        if tl < 0 or alpha <= 0.003:
            return None
        x, y = cam.chieu(self.p[0], self.p[1])
        if not (-300 < x < W + 300 and -300 < y < H + 300):
            return None
        if not self.chinh_xac:
            rp = self.r_m / cam.m_per_px()
            if rp > 16:
                from lop_bds import ve_hinh_tron, ve_vong_dut
                a = smooth(clamp(tl / 0.5)) * alpha
                ve_hinh_tron(frame, x, y, rp, VANG_CHU, 0.15, a)
                ve_vong_dut(frame, x, y, rp, VANG_CHU, 3, so=max(18, min(72, int(rp / 9))), goc=tl * 18, alpha=a)
        DN.ve_song(frame, x, y, tl - 0.45, VANG_CHU, r0=16, r1=96, chu_ky=1.8, so_vong=2, day=3, alpha=alpha * 0.8)
        u = clamp(tl / 0.6)
        dy = -260 * (1 - DN.bounce_out(u))
        nen = 1.0
        if 0.6 * 0.36 < tl < 0.6 * 0.55:      # nhún khi chạm đất
            nen = 1 - 0.10 * math.sin(math.pi * (tl - 0.216) / 0.114)
        _elip_dat(frame, x, y, 34 * (0.4 + 0.6 * u), 11 * (0.4 + 0.6 * u), alpha * u)
        arr = self.arr
        if nen != 1.0:
            arr = np.asarray(self.img.resize((self.img.width, max(1, int(self.img.height * nen))), Image.BICUBIC))
        C.dan(frame, arr, x - self.tx, y + dy - arr.shape[0] + (arr.shape[0] - self.ty * nen), alpha * clamp(u * 5))
        # mũi tên cong vẽ tay (sau khi chạm đất)
        if self.mui_ten:
            self._mui_ten(frame, x, y - self.ty, tl - 0.6, alpha)
        r = (x - self.tx, y - self.ty, x + self.tx, y)
        chiem.dat(r)
        self._r = chiem.r[-1]
        self._xy = (x, y + dy)
        return r

    def _mui_ten(self, frame, x, y_dinh, k, alpha):
        """mũi tên cong vẽ tay bên phải (mui_ten: true | 'phai') hoặc trái ('trai') ghim — né nhãn phía trên:
        từ dưới vồng lên rồi chỉ vào đầu ghim"""
        if k < 0 or k > 2.6:
            return
        a = alpha * (1.0 if k < 2.2 else 1 - (k - 2.2) / 0.4)
        u = ease_out(clamp(k / 0.45))
        s = -1 if self.mui_ten == "trai" else 1
        P0 = np.array([x + s * 215, y_dinh + 150])
        P1 = np.array([x + s * 235, y_dinh + 10])
        P2 = np.array([x + s * 66, y_dinh + 42])
        n = 28
        ss = np.linspace(0, u, n + 1)[:, None]
        pts = (1 - ss) ** 2 * P0 + 2 * (1 - ss) * ss * P1 + ss ** 2 * P2

        def ve(l, ox, oy):
            q = np.round(pts - [ox, oy]).astype(np.int32)
            cv2.polylines(l, [q], False, (20, 16, 6), 10, cv2.LINE_AA)
            cv2.polylines(l, [q], False, VANG_CHU, 6, cv2.LINE_AA)
            if u > 0.3:
                p1, p0 = pts[-1], pts[-4]
                v = p1 - p0
                v = v / (np.linalg.norm(v) + 1e-6)
                nrm = np.array([-v[1], v[0]])
                tri = np.array([p1 + v * 20, p1 - v * 10 + nrm * 16, p1 - v * 10 - nrm * 16]) - [ox, oy]
                cv2.fillConvexPoly(l, np.round(tri).astype(np.int32), (20, 16, 6), cv2.LINE_AA)
                tri2 = np.array([p1 + v * 15, p1 - v * 7 + nrm * 11, p1 - v * 7 - nrm * 11]) - [ox, oy]
                cv2.fillConvexPoly(l, np.round(tri2).astype(np.int32), VANG_CHU, cv2.LINE_AA)
        _tron_vung(frame, min(x + s * 20, x + s * 270), y_dinh - 30, max(x + s * 20, x + s * 270), y_dinh + 175, ve, a)

    def dat_nhan(self, tl, chiem, cung):
        """giữ chỗ nhãn nhà (trên đỉnh ghim) TRƯỚC khi tiện ích chọn chỗ"""
        self._hop = None
        if self.lab is None or tl < 0.5 or getattr(self, "_xy", None) is None:
            return
        x, y = self._xy
        h, w = self.lab.shape[:2]
        by = y - self.ty - h - 6
        self._hop = (x - w / 2, by, x + w / 2, by + h)
        chiem.dat(self._hop)
        cung.append(self._hop)

    def ve_nhan(self, frame, tl, chiem, cung, alpha=1.0):
        if getattr(self, "_hop", None) is None:
            self.dat_nhan(tl, chiem, cung)
        if self._hop is None:
            return
        a = ease_out(ramp(tl, 0.5, 0.3)) * alpha
        C.dan(frame, self.lab, self._hop[0], self._hop[1] + 10 * (1 - a), a)
        self._hop = None
        self._xy = None


def ve_vong_mau(frame, cam, tam, r_m, tl, nhan=None, alpha=1.0, chiem=None, nho=None, phan="ca"):
    """vòng bán kính mảnh vàng + quầng nhẹ (kiểu mẫu); nhãn ở đỉnh vòng, đỉnh bị chiếm ⇒ đáy / 2 vai, cũng chiếm ⇒ bỏ.
    phan: 'ca' | 'vong' (chỉ nét) | 'nhan' (chỉ nhãn — gọi SAU khi ghim tiện ích giữ chỗ ⇒ nhãn vòng nhường ghim)"""
    if tl < 0 or alpha <= 0.003:
        return None
    x, y = cam.chieu(tam[0], tam[1])
    u = ease_out(clamp(tl / 0.9))
    rp = r_m / cam.m_per_px() * u
    if rp < 6:
        return None
    if phan != "nhan":
        _ve_vong_net(frame, x, y, rp, alpha)
    if phan == "vong":
        return None
    return _nhan_vong(frame, x, y, rp, u, r_m, nhan, alpha, chiem, nho)


def _ve_vong_net(frame, x, y, rp, alpha):
    _tron_vung(frame, x - rp - 2, y - rp - 2, x + rp + 3, y + rp + 3,
               lambda l, ox, oy: cv2.circle(l, (int(x) - ox, int(y) - oy), int(rp), (255, 220, 80), -1, cv2.LINE_AA),
               0.06 * alpha)
    ve_phat_sang(frame, [np.array([[x + rp * math.cos(2 * math.pi * i / 180), y + rp * math.sin(2 * math.pi * i / 180)]
                                   for i in range(181)])], (255, 210, 60), 10, (255, 222, 96), 2, alpha * 0.9,
                 loi_trang=False)


def huong_trong(goc_ghim, co_tieu_de=False):
    """các hướng (độ màn hình, 0 = phải, -90 = lên) xếp theo độ xa các ghim — nhãn vòng lấy hướng ĐẦU TIÊN vừa màn hình
    ở khung đầu rồi GIỮ NGUYÊN (không nhảy)"""
    ung = [-45, -135, 45, 135, 0, 180, -90, 90]
    def diem(a):
        d = min([abs((a - g + 180) % 360 - 180) for g in goc_ghim] or [180])
        if a == -90 and co_tieu_de:
            d -= 40                     # đỉnh vòng hay vướng tiêu đề trên cùng
        if a == 90:
            d -= 30                     # đáy vòng hay vướng sub
        return d
    return sorted(ung, key=lambda a: -diem(a))


def _nhan_vong(frame, x, y, rp, u, r_m, nhan, alpha, chiem, nho):
    if nhan is None:
        nhan = ("%d m" % r_m) if r_m < 1000 else ("%g km" % (r_m / 1000.0)).replace(".", ",")
    if nhan and u > 0.7:
        im = np.asarray(nghieng(C.chu(nhan.upper(), "black", 26, fill=VANG_CHU, shadow=(0, 2, 4, 0.9), track=1)))
        hh, ww = im.shape[0] / 2, im.shape[1] / 2
        nho = nho if nho is not None else {}

        def cho(a, x_=x, y_=y, rp_=rp, ch=chiem):
            g = math.radians(a)
            cg, sg = math.cos(g), math.sin(g)
            dd = rp_ + 8 + abs(cg) * ww + abs(sg) * hh       # ngoài vòng, đúng hướng
            px, py = x_ + cg * dd, y_ + sg * dd
            r = (px - ww, py - hh, px + ww, py + hh)
            ok = not (py < 200 or py > H - 400 or r[0] < 20 or r[2] > W - 20 or (ch is not None and ch.trung(r, 4)))
            return ok, px, py, r
        cu = nho.get("_cuoi")            # (x, y, rp) của vòng lúc HẾT cảnh ⇒ hướng chọn phải vừa màn hình cả lúc đó
        if nho.get("_goc") is None:
            for a in nho.get("_goc_ds") or [-90, -45, -135, 45, 135, 0, 180, 90]:
                if cho(a)[0] and (cu is None or cho(a, cu[0], cu[1], cu[2], None)[0]):
                    nho["_goc"] = a
                    break
            else:
                return None
        ok, px, py, r = cho(nho["_goc"])
        if not ok:
            return None                 # vướng ⇒ ẩn (không nhảy sang chỗ khác)
        C.dan_giua(frame, im, px, py, alpha * clamp((u - 0.7) / 0.3))
        return r
    return None


# ---------------------------------------------------------------- đường neon + tên dọc đường

class DuongNeon:
    """{tuyen: key dia_diem, t, dai_ve (1,0), ten (chữ | true = tên kế hoạch | false), t_ten?, neo ('nha' | [lat, lon]),
    lech_m (dời chữ dọc đường từ điểm gần neo nhất, ±), lech_px (chữ cách tuyến), co (60), mau ('neon' | [r,g,b]),
    vet (true: vệt sáng chạy)}"""

    def __init__(self, d, g, nha_p):
        self.t = float(d.get("t", 0))
        self.dai_ve = float(d.get("dai_ve", 1.0))
        self.cac = [np.asarray(c, dtype=np.float64) for c in (g.get("cac_tuyen") or [g["tuyen"]]) if len(c) >= 2]
        mau = d.get("mau", "neon")
        self.mau = NEON if mau == "neon" else tuple(DN.mau(mau))
        self.loi = NEON_LOI if mau == "neon" else tuple(int(min(255, v * 0.35 + 170)) for v in self.mau)
        self.vet = d.get("vet", True)
        ten = d.get("ten", True)
        self.ten = (g.get("ten_ke_hoach") or g.get("ten") or "") if ten is True else (ten or "")
        self.t_ten = float(d.get("t_ten", self.t + 0.3 * self.dai_ve))
        self.co = int(d.get("co", 58))
        self.lech_px = float(d.get("lech_px", 40))
        neo = nha_p if d.get("neo", "nha") == "nha" else d["neo"]
        l0 = float(d.get("lech_m", 140))
        # chỗ đặt tên: neo trước, vướng (sub, tiêu đề, ghim, nhãn) ⇒ dời dọc tuyến, vẫn vướng ⇒ không hiện tên
        self.neo_ds = [x for x in (self._diem_neo(neo, l0 + o) for o in (0, 250, -250, 500, -500, 800, -800, 1200, -1200))
                       if x is not None]
        self.neo = self.neo_ds[0] if self.neo_ds else None
        self._cho = 0
        self._anh_ten = None
        self._cache = {}

    def _diem_neo(self, p, lech_m):
        """điểm trên tuyến gần p nhất, dời dọc tuyến lech_m mét → (điểm, điểm kế bên để lấy hướng)"""
        best = None
        for c in self.cac:
            d = np.hypot((c[:, 0] - p[0]) * 111320, (c[:, 1] - p[1]) * 111320 * math.cos(math.radians(p[0])))
            i = int(np.argmin(d))
            if best is None or d[i] < best[0]:
                best = (d[i], c, i)
        if best is None:
            return None
        _, c, i = best
        seg = np.hypot(np.diff(c[:, 0]) * 111320, np.diff(c[:, 1]) * 111320 * math.cos(math.radians(p[0])))
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        s = clamp(cum[i] + lech_m, 0, cum[-1])
        j = int(np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(c) - 2))
        f = (s - cum[j]) / seg[j] if seg[j] > 0 else 0.0
        a = c[j] + (c[j + 1] - c[j]) * f
        s2 = clamp(s + 25, 0, cum[-1]) if s + 25 <= cum[-1] else clamp(s - 25, 0, cum[-1])
        j2 = int(np.clip(np.searchsorted(cum, s2, side="right") - 1, 0, len(c) - 2))
        f2 = (s2 - cum[j2]) / seg[j2] if seg[j2] > 0 else 0.0
        b = c[j2] + (c[j2 + 1] - c[j2]) * f2
        return (a, b)

    def ve(self, frame, cam, t, alpha=1.0):
        if t < self.t or alpha <= 0.003 or not self.cac:
            return
        u = smooth(clamp((t - self.t) / max(0.05, self.dai_ve)))
        polys = []
        for c in self.cac:
            P = cam.chieu_mang(c)
            if not ((P[:, 0] > -400) & (P[:, 0] < W + 400) & (P[:, 1] > -400) & (P[:, 1] < H + 400)).any():
                continue
            part, _ = B.doan_theo_tien_do(P, u)
            polys.append((P, part))
        if not polys:
            return
        nhip = 0.85 + 0.15 * math.sin(2 * math.pi * (t - self.t) / 1.4)
        ve_phat_sang(frame, [p for _, p in polys], self.mau, 30, self.mau, 7, alpha * nhip)
        # vệt sáng chạy dọc tuyến (lặp lại)
        if self.vet and u >= 0.999:
            ph = ((t - self.t - self.dai_ve) % 1.7) / 1.7
            dai = max(P_.shape[0] for P_, _ in polys)
            for P, _ in polys:
                L = float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())
                if L < 80:
                    continue
                k = min(0.35, 260.0 / L)
                u1 = -k + (1 + 2 * k) * ph
                seg_ = _cat(P, max(0.0, u1 - k), min(1.0, u1))
                if len(seg_) >= 2:
                    ve_phat_sang(frame, [seg_], (255, 255, 210), 24, (255, 255, 240), 6, alpha * 0.95)
        elif u < 0.999:
            for P, part in polys:
                h_ = part[-1]
                ve_phat_sang(frame, [part[-2:] if len(part) >= 2 else part], (255, 255, 220), 26, (255, 255, 255), 8,
                             alpha)
                cv2.circle(frame, (int(h_[0]), int(h_[1])), 6, (255, 255, 240), -1, cv2.LINE_AA)

    def _dat(self, cam, neo, w, h):
        """neo → (tâm chữ, góc, các ô nhỏ dọc thân chữ) — ô dùng để thử đè (khỏi lấy khung bao chéo quá to)"""
        a_, b_ = neo
        A = np.array(cam.chieu(a_[0], a_[1]))
        Bp = np.array(cam.chieu(b_[0], b_[1]))
        v = Bp - A
        if np.linalg.norm(v) < 1e-3:
            return None
        goc = math.degrees(math.atan2(v[1], v[0]))
        if goc > 90:
            goc -= 180
        if goc < -90:
            goc += 180
        n = np.array([v[1], -v[0]]) / np.linalg.norm(v)
        if n[1] > 0:
            n = -n
        P = A + n * self.lech_px
        d = np.array([math.cos(math.radians(goc)), math.sin(math.radians(goc))])
        o = []
        for s_ in np.linspace(-w / 2, w / 2, max(3, int(w / max(20.0, h * 0.7)) + 1)):
            q = P + d * s_
            o.append((q[0] - h * 0.45, q[1] - h * 0.45, q[0] + h * 0.45, q[1] + h * 0.45))
        return P, goc, o

    def ve_ten(self, frame, cam, t, chiem, alpha=1.0):
        if not self.ten or not self.neo_ds or t < self.t_ten or alpha <= 0.003:
            return
        if self._anh_ten is None:
            self._anh_ten = chu_gradient(self.ten.upper(), "black", self.co, C.TRANG, (255, 176, 70),
                                         bong=(0, 5, 8, 0.85), glow=(255, 150, 40, 16), track=3)
        im = self._anh_ten
        w, h = im.width - 40, im.height - 40          # bỏ lề bóng / quầng
        thu = [self._cho] + [i for i in range(len(self.neo_ds)) if i != self._cho]
        chon = None
        for i in thu:
            r = self._dat(cam, self.neo_ds[i], w, h)
            if r is None:
                continue
            P, goc, o = r
            if all(30 < q[0] and q[2] < W - 30 and 150 < q[1] and q[3] < H - 30 for q in o)                     and not any(chiem.trung(q, 2) for q in o):
                chon = (i, P, goc, o)
                break
        if chon is None:
            return
        i, P, goc, o = chon
        self._cho = i
        k = clamp((t - self.t_ten) / 0.7)
        if k < 1:
            a = np.asarray(im).copy()
            ww = a.shape[1]
            x = np.arange(ww, dtype=np.float32)
            edge = -60 + (ww + 120) * ease_out(k)
            m = np.clip((edge - x) / 60.0, 0, 1)
            a[..., 3] = (a[..., 3].astype(np.float32) * m[None, :]).astype(np.uint8)
            rot = Image.fromarray(a, "RGBA").rotate(-goc, resample=Image.BICUBIC, expand=True)
        else:
            key = round(goc, 1)
            if key not in self._cache:
                self._cache = {key: im.rotate(-goc, resample=Image.BICUBIC, expand=True)}
            rot = self._cache[key]
        C.dan_giua(frame, rot, P[0], P[1], alpha)
        for q in o:
            chiem.dat(q)


# ---------------------------------------------------------------- hình dạng lô đất

class LoDat:
    """{t, tam ('nha' | [lat, lon]), rong_m (mặt tiền), sau_m, goc (độ, hướng cạnh mặt tiền: 0 = Đông, 90 = Bắc) |
    theo_duong (key dia_diem: tự song song đoạn đường gần nhất), nhan ('250m²'), t_nhan, canh: [{canh: truoc|sau|trai|phai,
    chu: '15m', t}], doan (true ⇒ hình minh hoạ, chưa có sơ đồ thật)}"""

    def __init__(self, d, tam, duong_g=None):
        self.d = d
        self.t = float(d.get("t", 0))
        self.t_nhan = float(d.get("t_nhan", self.t + 0.6))
        w, h = float(d.get("rong_m", 15)), float(d.get("sau_m", 16.7))
        f = None
        dn = None
        if duong_g is not None:
            best = None
            for c in (duong_g.get("cac_tuyen") or [duong_g.get("tuyen")]):
                c = np.asarray(c, np.float64)
                for i in range(len(c) - 1):
                    a, b = c[i], c[i + 1]
                    ax = np.array([(a[1] - tam[1]) * 111320 * math.cos(math.radians(tam[0])), (a[0] - tam[0]) * 111320])
                    bx = np.array([(b[1] - tam[1]) * 111320 * math.cos(math.radians(tam[0])), (b[0] - tam[0]) * 111320])
                    ab = bx - ax
                    L2 = float(ab @ ab)
                    if L2 <= 0:
                        continue
                    q = clamp(-(ax @ ab) / L2)
                    p = ax + ab * q
                    dd = float(np.linalg.norm(p))
                    if best is None or dd < best[0]:
                        best = (dd, ab / math.sqrt(L2), p)
            if best is not None:
                f = best[1]
                dn = -best[2] / (np.linalg.norm(best[2]) + 1e-9)       # từ đường vào lô
                if d.get("sat_duong", True):
                    # mép mặt tiền cách tim ngõ le_m (≈ nửa bề rộng ngõ), lô nằm phía có ghim
                    c_ = best[2] + dn * (h / 2 + float(d.get("le_m", 2.0)))
                    tam = _ll_cong_m(tam, c_[0], c_[1])
        if f is None:
            g = math.radians(float(d.get("goc", 0)))
            f = np.array([math.cos(g), math.sin(g)])
            dn = np.array([-f[1], f[0]])
        # góc theo (đông, bắc) mét; mặt tiền ở phía đường
        c0 = np.array([0.0, 0.0])
        self.goc_lo = [c0 - f * w / 2 - dn * h / 2, c0 + f * w / 2 - dn * h / 2, c0 + f * w / 2 + dn * h / 2,
                       c0 - f * w / 2 + dn * h / 2]        # 0-1 = mặt tiền
        self.ll = [_ll_cong_m(tam, p[0], p[1]) for p in self.goc_lo]
        self.canh = [dict(c) for c in d.get("canh", [])]
        self._chu = None

    def rect(self):
        return getattr(self, "_rect", None)

    # nhịp hiệu ứng (giây kể từ lúc lô bắt đầu hiện): quét đầy 0–0,6 · chấm góc 0,15–0,6 · gợn viền 0,6 & lúc hiện chữ
    # · ánh lướt chéo mỗi 2,4 s · viền thở. SFX: canh_bds.sfx (swoosh lúc quét, sparkle lúc chữ, pop lúc ngoặc đo)
    QUET = 0.6

    def ve(self, frame, cam, t, chiem, alpha=1.0):
        den = self.d.get("den")
        if den is not None:
            if t >= float(den):
                return
            alpha *= clamp((float(den) - t) / 0.3)
        if t < self.t or alpha <= 0.003:
            return
        tl = t - self.t
        Q = np.array([cam.chieu(p[0], p[1]) for p in self.ll], np.float64)
        w_lo = float(np.linalg.norm(Q[1] - Q[0]))
        if getattr(self, "_w0", None) is None and tl >= 0.5:
            self._w0 = w_lo              # cỡ lô lúc camera đã tới ⇒ chữ co theo khi camera lùi xa
        ti_le = clamp(w_lo / self._w0, 0.0, 1.0) if getattr(self, "_w0", None) else 1.0
        hien_chu = ti_le > 0.45 and w_lo > 45
        ctr = Q.mean(axis=0)
        # 1. khối xanh sáng quét đầy từ mặt tiền vào sâu (giống mẫu: xanh dương bão hoà, gần đặc)
        u = ease_out(clamp(tl / self.QUET))
        fr_ = Q[0] + (Q[3] - Q[0]) * u
        bk = Q[1] + (Q[2] - Q[1]) * u
        poly = np.array([Q[0], Q[1], bk, fr_])
        x0, y0, x1, y1 = _vung(frame, Q, 90)
        if x1 - x0 < 4 or y1 - y0 < 4:
            return
        reg = frame[y0:y1, x0:x1].astype(np.float32)
        mk = np.zeros(reg.shape[:2], np.uint8)
        cv2.fillPoly(mk, [np.round(poly - [x0, y0]).astype(np.int32)], 255, cv2.LINE_AA)
        hh, ww = mk.shape
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        gr = ((xx + yy) / (hh + ww))[..., None]
        col = np.array((22, 120, 255), np.float32) * (1 - gr) + np.array((70, 200, 255), np.float32) * gr
        # ánh lướt chéo (dải sáng chạy qua lô mỗi 2,4 s sau khi đầy)
        if tl > self.QUET:
            ph = ((tl - self.QUET) % 2.4) / 1.0
            if ph < 1:
                c0 = -0.25 + 1.5 * ph
                band = np.exp(-((((xx - (Q[:, 0].min() - x0)) + (yy - (Q[:, 1].min() - y0))) /
                                 max(1.0, float(np.ptp(Q[:, 0]) + np.ptp(Q[:, 1]))) - c0) / 0.07) ** 2)[..., None]
                col = col + (255 - col) * band * 0.55
        m = (mk.astype(np.float32) / 255.0 * 0.80 * alpha)[..., None]
        reg = reg * (1 - m) + col * m
        # vạch quét sáng ở mép đang lấp đầy
        if u < 0.999:
            ln = np.zeros(reg.shape[:2], np.float32)
            cv2.line(ln, tuple(np.round(fr_ - [x0, y0]).astype(int)), tuple(np.round(bk - [x0, y0]).astype(int)), 1.0, 5,
                     cv2.LINE_AA)
            ln = cv2.GaussianBlur(ln, (0, 0), 6) * 2.2 + ln
            reg = reg + (255 - reg) * np.clip(ln, 0, 1)[..., None] * alpha
        frame[y0:y1, x0:x1] = reg.clip(0, 255).astype(np.uint8)
        # 2. viền trắng + quầng xanh thở nhẹ
        vien = np.vstack([Q, Q[:1]])
        tho = 0.85 + 0.15 * math.sin(2 * math.pi * tl / 1.6)
        ve_phat_sang(frame, [vien], (60, 170, 255), 26, (255, 255, 255), 3, alpha * clamp(tl / 0.3) * tho,
                     loi_trang=False)
        # 3. gợn viền lan ra (lúc đầy + lúc hiện chữ)
        for t_g in (self.QUET, self.t_nhan - self.t):
            for kk in range(2):
                g = (tl - t_g - 0.18 * kk) / 0.8
                if 0 <= g < 1:
                    sc = 1 + 0.45 * ease_out(g)
                    Rg = ctr + (Q - ctr) * sc
                    ve_phat_sang(frame, [np.vstack([Rg, Rg[:1]])], (90, 200, 255), 12, (210, 240, 255), 2,
                                 alpha * (1 - g) ** 1.4 * 0.9, loi_trang=False)
        # 4. chấm góc bật lần lượt
        for i, q in enumerate(Q):
            g = clamp((tl - 0.15 - 0.1 * i) / 0.25)
            if g > 0:
                r_ = 8 * DN.back_out(g)
                cv2.circle(frame, (int(q[0]), int(q[1])), int(r_ + 3), (30, 110, 220), -1, cv2.LINE_AA)
                cv2.circle(frame, (int(q[0]), int(q[1])), max(1, int(r_)), (255, 255, 255), -1, cv2.LINE_AA)
        # 5. chữ diện tích xoay theo lô + lấp lánh lúc bật
        v = Q[1] - Q[0]
        goc = math.degrees(math.atan2(v[1], v[0]))
        if goc > 90:
            goc -= 180
        if goc < -90:
            goc += 180
        if abs(goc) > 50:             # cạnh mặt tiền dốc ⇒ chữ diện tích theo cạnh kia (đỡ nghiêng đầu)
            goc = goc - 90 if goc > 0 else goc + 90
        if self.d.get("nhan") and t >= self.t_nhan and hien_chu:
            if self._chu is None:
                co = int(clamp(min(w_lo, float(np.linalg.norm(Q[3] - Q[0]))) * 0.28, 30, 96))
                self._chu = chu_gradient(self.d["nhan"], "black", co, C.TRANG, (232, 246, 255), bong=(0, 4, 8, 0.85))
                self._chu_r = self._chu.rotate(-goc, resample=Image.BICUBIC, expand=True)
            k = clamp((t - self.t_nhan) / 0.35)
            C.dan_giua(frame, self._chu_r, ctr[0], ctr[1], k * alpha, max(0.05, DN.back_out(k) * ti_le))
            self._lap_lanh(frame, ctr, self._chu_r.width * ti_le, t - self.t_nhan, alpha)
        # 6. ngoặc đo kích thước
        for c in (self.canh if hien_chu else []):
            tc = float(c.get("t", self.t_nhan + 0.4))
            if t < tc:
                continue
            self._ngoac(frame, Q, c.get("canh", "truoc"), c.get("chu", ""), t - tc, alpha)
        r = (Q[:, 0].min() - 70, Q[:, 1].min() - 70, Q[:, 0].max() + 70, Q[:, 1].max() + 70)
        self._rect = r
        chiem.dat(r)

    _SAO = None

    def _lap_lanh(self, frame, ctr, rong, tl, alpha):
        """6 sao 4 cánh nháy quanh chữ diện tích trong 1,1 s đầu"""
        if tl < 0 or tl > 1.1:
            return
        if LoDat._SAO is None:
            from cta_follow import sao_4_canh
            LoDat._SAO = [np.asarray(sao_4_canh(sz, (255, 255, 255))) for sz in (26, 38, 50)]
        rng = np.random.default_rng(250)
        for i in range(6):
            g = (tl - 0.08 * i) / 0.55
            if not 0 <= g < 1:
                continue
            a_ = 2 * math.pi * (i / 6.0) + 0.4
            rr = rong * (0.42 + 0.12 * rng.random())
            p = ctr + np.array([math.cos(a_) * rr, math.sin(a_) * rr * 0.6])
            im = LoDat._SAO[i % 3]
            C.dan_giua(frame, im, p[0], p[1], alpha * math.sin(math.pi * g), 0.4 + 0.8 * math.sin(math.pi * g))

    def _ngoac(self, frame, Q, canh, chu, tl, alpha):
        i0, i1 = {"truoc": (0, 1), "phai": (1, 2), "sau": (2, 3), "trai": (3, 0)}[canh]
        a, b = Q[i0], Q[i1]
        ctr = Q.mean(axis=0)
        mid = (a + b) / 2
        out = mid - ctr
        out = out / (np.linalg.norm(out) + 1e-9)
        off = 22
        A, Bp = a + out * off, b + out * off
        u = ease_out(clamp(tl / 0.35))
        mA = (A + Bp) / 2
        A2, B2 = mA + (A - mA) * u, mA + (Bp - mA) * u
        pts = [A2 - out * 14 * u, A2, B2, B2 - out * 14 * u]
        cv2.polylines(frame, [np.round(np.array(pts)).astype(np.int32)], False, (20, 20, 20), 7, cv2.LINE_AA)
        cv2.polylines(frame, [np.round(np.array(pts)).astype(np.int32)], False, (255, 255, 255), 4, cv2.LINE_AA)
        if chu and u > 0.6:
            v = Bp - A
            goc = math.degrees(math.atan2(v[1], v[0]))
            if goc > 90:
                goc -= 180
            if goc < -90:
                goc += 180
            im = chu_gradient(chu, "black", 44, C.TRANG, (255, 255, 255), bong=(0, 3, 6, 0.85))
            im = im.rotate(-goc, resample=Image.BICUBIC, expand=True)
            p = mA + out * (off + 30)
            k = clamp((u - 0.6) / 0.4)
            C.dan_giua(frame, im, p[0], p[1], k * alpha)


# ---------------------------------------------------------------- chữ địa danh lớn

class ChuLon:
    """{t, chu: 'HỒ TÂY', tai: [lat, lon] (đã giải), goc (độ, + = nghiêng lên), co (96)}"""

    def __init__(self, d, p):
        self.t = float(d.get("t", 0))
        self.p = p
        self.goc = float(d.get("goc", -6))
        co = int(d.get("co", 96))
        self.chu = [chu_gradient(ch, "black", co, C.TRANG, (255, 168, 64), bong=(0, 6, 10, 0.8),
                                 glow=(255, 150, 40, 20)) if ch.strip() else None for ch in d["chu"].upper()]
        f = C.font("black", co)
        self.adv = [f.getlength(ch) + 4 for ch in d["chu"].upper()]
        self._xong = None

    def ve(self, frame, cam, t, chiem, alpha=1.0):
        if t < self.t or alpha <= 0.003:
            return
        tl = t - self.t
        x, y = cam.chieu(self.p[0], self.p[1])
        n = len(self.chu)
        xong = tl > 0.07 * n + 0.45
        if xong and self._xong is not None:
            im = self._xong
        else:
            Wc = int(sum(self.adv) + 80)
            Hc = int(max((c.height for c in self.chu if c is not None), default=100) + 80)
            can = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
            xx = 40
            for i, (c, ad) in enumerate(zip(self.chu, self.adv)):
                if c is not None:
                    k = clamp((tl - 0.07 * i) / 0.4)
                    if k > 0:
                        s = max(0.05, DN.back_out(k))
                        cc = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.BICUBIC) if s != 1 else c
                        al = np.asarray(cc).copy()
                        al[..., 3] = (al[..., 3].astype(np.float32) * clamp(k * 3)).astype(np.uint8)
                        cc = Image.fromarray(al, "RGBA")
                        cx, cy = xx + ad / 2, Hc / 2 - 30 * (1 - ease_out(k))
                        can.alpha_composite(cc, (int(cx - cc.width / 2), int(cy - cc.height / 2)))
                xx += ad
            im = can.rotate(self.goc, resample=Image.BICUBIC, expand=True)
            if xong:
                self._xong = im
        C.dan_giua(frame, im, x, y, alpha)
        chiem.dat((x - im.width / 2 + 40, y - im.height / 2 + 40, x + im.width / 2 - 40, y + im.height / 2 - 40))


# ---------------------------------------------------------------- biển ảnh cắm cọc

class BienAnh:
    """{t (lúc biển bật), p (đích, đã giải), anh (đường dẫn ảnh) | None ⇒ ảnh vệ tinh cận cảnh đích, nhan,
    duong (polyline lat/lon từ nhà | None), dai_ve, cot (cao cọc px, 120), rong (ảnh, 230), lech_x (px, dời biển ngang)}"""

    def __init__(self, d, nen=None):
        self.d = d
        self.p = d["p"]
        self.duong = np.asarray(d["duong"], np.float64) if d.get("duong") else None
        self.dai_ve = float(d.get("dai_ve", 1.0 if self.duong is not None else 0.0))
        self.t_bien = float(d["t"])
        self.t = self.t_bien - (self.dai_ve if self.duong is not None else 0.0)
        self.cot = float(d.get("cot", 120))
        self.lech_x = float(d.get("lech_x", 0))
        rong = int(d.get("rong", 230))
        cao = int(rong * 0.72)
        anh = None
        if d.get("anh"):
            try:
                anh = Image.open(d["anh"]).convert("RGB")
            except Exception:
                anh = None
        if anh is None and nen is not None:
            cam = B.Camera(self.p[0], self.p[1], 17.6)
            fr = cam.render(nen)
            anh = Image.fromarray(fr).crop((W // 2 - 300, H // 2 - 216, W // 2 + 300, H // 2 + 216))
        if anh is None:
            anh = Image.new("RGB", (rong, cao), (60, 70, 90))
        anh = C.cover(anh.convert("RGBA"), rong, cao)
        bd = 6
        bar = 40
        card = Image.new("RGBA", (rong + 2 * bd, cao + 2 * bd + bar), (255, 255, 255, 255))
        card.alpha_composite(anh, (bd, bd))
        ImageDraw.Draw(card).rectangle((bd, bd + cao, bd + rong - 1, bd + cao + bar - 2), fill=tuple(XANH_BIEN) + (255,))
        if d.get("nhan"):
            tx = C.chu(d["nhan"], "xbold", 26, fill=C.TRANG)
            if tx.width > rong - 16:
                tx = tx.resize((rong - 16, int(tx.height * (rong - 16) / tx.width)), Image.LANCZOS)
            card.alpha_composite(tx, (bd + (rong - tx.width) // 2, bd + cao + (bar - tx.height) // 2 - 1))
        sh, p = C.bong_do(card, blur=14, alpha=0.6)
        c2 = Image.new("RGBA", (card.width + 2 * p, card.height + 2 * p), (0, 0, 0, 0))
        c2.alpha_composite(sh, (4, 10))
        c2.alpha_composite(card, (p, p))
        self.card = c2
        self.p_card = p

    def ve_duong(self, frame, cam, t, alpha=1.0):
        if self.duong is None or t < self.t or alpha <= 0.003:
            return
        P = cam.chieu_mang(self.duong)
        u = smooth(clamp((t - self.t) / max(0.05, self.dai_ve)))
        part, head = B.doan_theo_tien_do(P, u)
        ve_net_dut(frame, part, (20, 16, 6), 7, 16, 11, alpha * 0.55)
        ve_net_dut(frame, part, VANG_CHU, 4, 16, 11, alpha)
        if u < 0.999 and head is not None:
            B.ve_cham(frame, head[0], head[1], 6, C.TRANG, alpha=alpha)

    def ve(self, frame, cam, t, chiem, alpha=1.0):
        if t < self.t_bien or alpha <= 0.003:
            return
        tl = t - self.t_bien
        x, y = cam.chieu(self.p[0], self.p[1])
        cv2.circle(frame, (int(x), int(y)), 7, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (int(x), int(y)), 7, (30, 30, 30), 2, cv2.LINE_AA)
        u = ease_out(clamp(tl / 0.2))
        top = y - self.cot * u
        xc = x + self.lech_x
        pts = np.array([[x, y], [x, top + 20], [xc, top + 20], [xc, top]]) if self.lech_x else np.array([[x, y], [x, top]])
        cv2.polylines(frame, [np.round(pts).astype(np.int32)], False, (30, 30, 30), 6, cv2.LINE_AA)
        cv2.polylines(frame, [np.round(pts).astype(np.int32)], False, (255, 255, 255), 3, cv2.LINE_AA)
        k = clamp((tl - 0.12) / 0.35)
        if k > 0:
            s = max(0.05, DN.back_out(k))
            ch = self.card.height - 2 * self.p_card
            cy = top - ch / 2 * s
            C.dan_giua(frame, self.card, xc, cy, clamp(k * 3) * alpha, s)
            w2 = (self.card.width - 2 * self.p_card) / 2
            chiem.dat((xc - w2, cy - ch / 2, xc + w2, top))


# ---------------------------------------------------------------- tiêu đề trên cùng

def _dong_mau(segs, co, key="black", bong=(0, 5, 8, 0.95)):
    """1 dòng nhiều màu trên CÙNG đường chân chữ (khe = dấu cách thật), bóng tối đổ chung cho cả dòng"""
    f = C.font(key, co)
    pad = 40
    txt = " ".join(s_ for s_, _ in segs)
    asc, desc = f.getmetrics()
    Wc, Hc = int(f.getlength(txt)) + 2 * pad, asc + desc + 2 * pad
    chu_ = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(chu_)
    x = pad
    for i, (s_, mau_) in enumerate(segs):
        d.text((x, pad), s_, font=f, fill=tuple(mau_) + (255,))
        x += f.getlength(s_ + (" " if i < len(segs) - 1 else ""))
    out = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    dx, dy, bl, al = bong
    sh = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    a = Image.new("L", (Wc, Hc), 0)
    a.paste(chu_.getchannel("A"), (int(dx), int(dy)))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(bl)).point(lambda v: int(min(255, v * al * 1.3))))
    out.alpha_composite(sh)
    out.alpha_composite(chu_)
    bb = out.getbbox()
    return out.crop(bb) if bb else out


class TieuDeTren:
    """{t, den?, dong: ['Hồ Tây chỉ cách', '≈ 130 m'], vang: ['≈ 130 m', ...], y (230), co (60)} — chữ trắng đậm bóng tối,
    cụm trong `vang` tô vàng; từng dòng trồi lên"""

    def __init__(self, d, t1_canh):
        self.t0 = float(d.get("t", 0))
        self.t1 = float(d.get("den", t1_canh))
        co = int(d.get("co", 60))
        vang = [v for v in d.get("vang", [])]
        self.dong = []
        for line in d["dong"]:
            segs = self._tach(line, vang)
            im = _dong_mau([(s_, VANG_CHU if is_v else C.TRANG) for s_, is_v in segs if s_], co)
            self.dong.append(np.asarray(im))
        self.y = float(d.get("y", 230))

    @staticmethod
    def _tach(line, vang):
        out = []
        rest = line
        while rest:
            hit = None
            for v in vang:
                i = rest.find(v)
                if i >= 0 and (hit is None or i < hit[0]):
                    hit = (i, v)
            if hit is None:
                out.append((rest.strip(), False))
                break
            i, v = hit
            if rest[:i].strip():
                out.append((rest[:i].strip(), False))
            out.append((v, True))
            rest = rest[i + len(v):]
        return out

    def rect(self):
        h = sum(d.shape[0] + 8 for d in self.dong)
        w = max(d.shape[1] for d in self.dong)
        return (W / 2 - w / 2 - 10, self.y - 10, W / 2 + w / 2 + 10, self.y + h + 10)

    def ve(self, frame, t, chiem=None, alpha=1.0):
        if t < self.t0 or t > self.t1:
            return
        out = clamp((self.t1 - t) / 0.2)
        y = self.y
        for i, d in enumerate(self.dong):
            k = ease_out(clamp((t - self.t0 - 0.1 * i) / 0.35))
            if k > 0:
                C.dan(frame, d, W / 2 - d.shape[1] / 2, y + 26 * (1 - k), k * out * alpha)
            y += d.shape[0] + 8
        if chiem is not None:
            chiem.dat(self.rect())


# ---------------------------------------------------------------- thước đo neon

class ThuocNeon:
    """{t, a: [lat, lon], b: [lat, lon], chu ('≈ 130 m')} — nét đứt trắng có 2 đầu chặn + nhãn vàng giữa"""

    def __init__(self, d):
        self.t = float(d.get("t", 0))
        self.a, self.b = d["a"], d["b"]
        self.chu = d.get("chu") or ""
        self.lab = None

    def ve(self, frame, cam, t, chiem, alpha=1.0):
        if t < self.t or alpha <= 0.003:
            return
        tl = t - self.t
        A = np.array(cam.chieu(self.a[0], self.a[1]))
        Bp = np.array(cam.chieu(self.b[0], self.b[1]))
        u = ease_out(clamp(tl / 0.5))
        E = A + (Bp - A) * u
        ve_net_dut(frame, np.array([A, E]), (20, 20, 20), 8, 14, 9, alpha * 0.6)
        ve_net_dut(frame, np.array([A, E]), (255, 255, 255), 4, 14, 9, alpha)
        v = Bp - A
        n = np.array([-v[1], v[0]]) / (np.linalg.norm(v) + 1e-9)
        for P in (A, E):
            q = np.array([P + n * 14, P - n * 14])
            cv2.polylines(frame, [np.round(q).astype(np.int32)], False, (255, 255, 255), 4, cv2.LINE_AA)
        if self.chu and u > 0.7:
            if self.lab is None:
                im = C.chu(self.chu, "black", 34, fill=(30, 22, 4))
                box = C.hop_bo((im.width + 34, im.height + 20), (im.height + 20) // 2, tuple(VANG_CHU) + (255,),
                               vien=(255, 255, 255, 255), vien_w=3)
                box.alpha_composite(im, (17, 10))
                self.lab = np.asarray(box)
            M = (A + Bp) / 2
            h0 = self.lab.shape[0]
            if np.linalg.norm(v) < self.lab.shape[1] * 1.6:     # thước ngắn ⇒ nhãn tách xuống dưới vạch, khỏi che 2 đầu
                M = M + (n if n[1] > 0 else -n) * (h0 / 2 + 18)
            k = clamp((u - 0.7) / 0.3)
            C.dan_giua(frame, self.lab, M[0], M[1], k * alpha, max(0.05, DN.back_out(k)))
            h, w = self.lab.shape[:2]
            chiem.dat((M[0] - w / 2, M[1] - h / 2, M[0] + w / 2, M[1] + h / 2))
