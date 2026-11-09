# -*- coding: utf-8 -*-
"""CTA FOLLOW cuối video — thẻ `the[].kieu = "theo_doi"` (chốt 09/11/2026: kịch bản KHÔNG đọc số điện thoại ⇒ cuối
video BẮT BUỘC là thẻ này, thay cho thẻ `lien_he`; "có button, anim bàn tay nhấn follow, xịn xò").

Thẻ navy nổi trên bản đồ (bản đồ vẫn trôi phía sau), giữa khung:
  avatar tròn (logo kênh / ghim nhà vàng) + VÒNG MÀU XOAY + huy hiệu "+" đỏ (bấm xong lật thành ✓ xanh) + sóng loang
  tên kênh (chỉ khi có kenh.ten — không bịa) · dòng chính "FOLLOW KÊNH NGAY" · dòng phụ
  NÚT FOLLOW đỏ-hồng gradient, bóng kính, vệt sáng quét, quầng thở → BÀN TAY trượt vào, nhấn (nút lún, sóng trắng,
  pháo giấy + sao lấp lánh) → nút đổi "✓ ĐÃ FOLLOW" → tay lướt xuống chip ♥ nhấn tiếp (tim bay lên) → chuông tự rung
  hàng chip: 🔔 Bật chuông · ♥ Thả tim · ↗ Chia sẻ
KHÔNG SFX (góp ý 04/11: chime CTA chói). Mọi hình vẽ vector PIL siêu lấy mẫu, không tải ảnh ngoài.

it: {kieu: "theo_doi", tu, den, t_bam? (giây nhấn FOLLOW, mặc định tu + 1,2), dong?: [dòng chính, dòng phụ],
     nut?: "FOLLOW", nut_sau?: "ĐÃ FOLLOW", chip?: [3 nhãn] | false, bam_tim?: true, y?: 470}
"""
import math
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import bieu_tuong as BT
import chung as C
import cta as CT
import diem_nhan as DN
from chung import W, clamp, ramp, smooth, ease_out

SS = 4
HONG_1, HONG_2 = (255, 84, 118), (222, 18, 70)
XAM_1, XAM_2 = (58, 72, 102), (36, 46, 70)
XANH_OK = (46, 204, 118)
DO_TIM = (255, 56, 96)
MAU_PHAO = [(255, 210, 77), (255, 84, 118), (79, 195, 247), (120, 230, 120), (190, 130, 255), (255, 255, 255)]
VONG_MAU = [(255, 210, 77), (255, 140, 60), (255, 70, 110), (190, 110, 255), (79, 195, 247), (255, 210, 77)]


# ---------------------------------------------------------------- biểu tượng vector

def _sieu(size):
    S = size * SS
    return Image.new("RGBA", (S, S), (0, 0, 0, 0)), S


def icon_tim(size, mau=C.TRANG):
    im, S = _sieu(size)
    d = ImageDraw.Draw(im)
    c = tuple(mau) + (255,)
    r = 0.25 * S
    d.ellipse((0.06 * S, 0.12 * S, 0.06 * S + 2 * r, 0.12 * S + 2 * r), fill=c)
    d.ellipse((0.94 * S - 2 * r, 0.12 * S, 0.94 * S, 0.12 * S + 2 * r), fill=c)
    d.polygon([(0.075 * S, 0.47 * S), (0.925 * S, 0.47 * S), (0.5 * S, 0.93 * S)], fill=c)
    return im.resize((size, size), Image.LANCZOS)


def icon_nguoi_cong(size, mau=C.TRANG):
    """người + dấu cộng (follow)"""
    im, S = _sieu(size)
    d = ImageDraw.Draw(im)
    c = tuple(mau) + (255,)
    d.ellipse((0.20 * S, 0.12 * S, 0.52 * S, 0.44 * S), fill=c)
    d.pieslice((0.06 * S, 0.52 * S, 0.66 * S, 1.14 * S), 180, 360, fill=c)
    cx, cy, L, w = 0.80 * S, 0.42 * S, 0.17 * S, 0.075 * S
    d.rounded_rectangle((cx - L, cy - w, cx + L, cy + w), radius=w, fill=c)
    d.rounded_rectangle((cx - w, cy - L, cx + w, cy + L), radius=w, fill=c)
    return im.resize((size, size), Image.LANCZOS)


def icon_chia_se(size, mau=C.TRANG):
    """3 nút nối nhau (chia sẻ)"""
    im, S = _sieu(size)
    d = ImageDraw.Draw(im)
    c = tuple(mau) + (255,)
    p = [(0.74 * S, 0.20 * S), (0.26 * S, 0.50 * S), (0.74 * S, 0.80 * S)]
    d.line([p[0], p[1], p[2]], fill=c, width=int(0.07 * S))
    r = 0.13 * S
    for x, y in p:
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)
    return im.resize((size, size), Image.LANCZOS)


def icon_cong(size, mau=C.TRANG):
    im, S = _sieu(size)
    d = ImageDraw.Draw(im)
    c = tuple(mau) + (255,)
    L, w = 0.30 * S, 0.075 * S
    d.rounded_rectangle((S / 2 - L, S / 2 - w, S / 2 + L, S / 2 + w), radius=w, fill=c)
    d.rounded_rectangle((S / 2 - w, S / 2 - L, S / 2 + w, S / 2 + L), radius=w, fill=c)
    return im.resize((size, size), Image.LANCZOS)


def sao_4_canh(size, mau=C.VANG):
    im, S = _sieu(size)
    d = ImageDraw.Draw(im)
    c = tuple(mau) + (255,)
    m, k = S / 2, 0.11 * S
    d.polygon([(m, 0), (m + k, m - k), (S, m), (m + k, m + k), (m, S), (m - k, m + k), (0, m), (m - k, m - k)], fill=c)
    im = im.resize((size, size), Image.LANCZOS)
    glow = im.filter(ImageFilter.GaussianBlur(size / 10))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(im)
    return out


# ---------------------------------------------------------------- khối dựng sẵn

def _pill(rong, cao, c1, c2):
    """viên thuốc gradient dọc c1→c2, bóng kính nửa trên, viền trong sáng — khử răng cưa bằng siêu lấy mẫu"""
    s = 3
    Wd, Hd = rong * s, cao * s
    g = np.linspace(0, 1, Hd, dtype=np.float32)[:, None, None]
    col = np.array(c1, np.float32)[None, None, :] * (1 - g) + np.array(c2, np.float32)[None, None, :] * g
    rgb = np.repeat(col, Wd, axis=1)
    m = Image.new("L", (Wd, Hd), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, Wd - 1, Hd - 1), radius=Hd // 2, fill=255)
    im = Image.fromarray(np.dstack([rgb.clip(0, 255).astype(np.uint8), np.asarray(m)]), "RGBA")
    hl = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle((int(0.03 * Wd), int(0.07 * Hd), int(0.97 * Wd), int(0.50 * Hd)),
                                         radius=Hd // 4, fill=(255, 255, 255, 52))
    im.alpha_composite(hl)
    vi = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    ImageDraw.Draw(vi).rounded_rectangle((2, 2, Wd - 3, Hd - 3), radius=Hd // 2 - 2, outline=(255, 255, 255, 70),
                                         width=2 * s)
    im.alpha_composite(vi)
    return im.resize((rong, cao), Image.LANCZOS)


def _nut(rong, cao, c1, c2, icon, chu, co=56):
    box = _pill(rong, cao, c1, c2)
    t = C.chu(chu, "black", co, fill=C.TRANG, shadow=(0, 3, 4, 0.35), track=3)
    gap = 22
    x = (rong - (icon.width + gap + t.width)) // 2
    box.alpha_composite(icon, (x, (cao - icon.height) // 2))
    box.alpha_composite(t, (x + icon.width + gap, (cao - t.height) // 2))
    return box


def _vong_mau(r_ngoai, day):
    """vòng gradient nón nhiều màu (kiểu viền story) — xoay mỗi khung"""
    s = 3
    n = int(2 * (r_ngoai + 3) * s)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = n / 2.0
    r = np.hypot(xx - c, yy - c) / s
    ang = ((np.degrees(np.arctan2(yy - c, xx - c)) + 360.0) % 360.0) / 360.0
    st = np.array(VONG_MAU, np.float32)
    seg = ang * (len(st) - 1)
    i = np.clip(np.floor(seg).astype(int), 0, len(st) - 2)
    f = (seg - i)[..., None]
    rgb = st[i] * (1 - f) + st[i + 1] * f
    a = (((r <= r_ngoai) & (r >= r_ngoai - day)) * 255).astype(np.uint8)
    im = Image.fromarray(np.dstack([rgb.astype(np.uint8), a]), "RGBA")
    return im.resize((n // s, n // s), Image.LANCZOS)


def _chip(nhan, rong_icon, nen=(255, 255, 255, 34), vien=(255, 255, 255, 110), mau_chu=C.TRANG):
    """chip kính bo tròn, chừa chỗ icon bên trái (icon vẽ riêng để rung / bật) → (ảnh, x tâm icon)"""
    t = C.chu(nhan, "semi", 28, fill=mau_chu)
    w, h = 24 + rong_icon + 12 + t.width + 28, 80
    box = C.hop_bo((w, h), h // 2, nen, vien=vien, vien_w=2)
    box.alpha_composite(t, (24 + rong_icon + 12, (h - t.height) // 2))
    return box, 24 + rong_icon / 2


def _xoay_np(img, goc):
    return img.rotate(goc, resample=Image.BICUBIC) if abs(goc) > 0.05 else img


# ---------------------------------------------------------------- thẻ

class TheTheoDoi:
    def __init__(self, it, kenh=None, tim_file=None):
        kenh = kenh or {}
        self.it = it
        self.t0, self.t1 = float(it["tu"]), float(it["den"])
        dai = self.t1 - self.t0
        self.tb = float(it["t_bam"]) - self.t0 if it.get("t_bam") is not None else min(1.2, max(0.6, dai - 1.0))
        bam_tim = it.get("bam_tim", True) and it.get("chip", True) is not False
        self.th = self.tb + 1.0 if (bam_tim and dai - self.tb >= 2.3) else None
        self.t_chuong = (self.th if self.th is not None else self.tb) + 0.55
        # avatar
        D_ = 176
        self.D = D_
        logo = None
        if kenh.get("logo") and tim_file:
            try:
                logo = C.cover(Image.open(tim_file(kenh["logo"])).convert("RGBA"), D_, D_)
            except (SystemExit, Exception):
                logo = None
        if logo is None:
            logo = Image.new("RGBA", (D_, D_), tuple(C.VANG) + (255,))
            g = BT.icon("nha", 100, C.NAVY)
            logo.alpha_composite(g, ((D_ - g.width) // 2, (D_ - g.height) // 2 + 2))
        mk = Image.new("L", (D_ * SS, D_ * SS), 0)
        ImageDraw.Draw(mk).ellipse((0, 0, D_ * SS - 1, D_ * SS - 1), fill=255)
        logo.putalpha(mk.resize((D_, D_), Image.LANCZOS))
        av = Image.new("RGBA", (D_ + 12, D_ + 12), (0, 0, 0, 0))
        m2 = Image.new("L", ((D_ + 12) * SS, (D_ + 12) * SS), 0)
        ImageDraw.Draw(m2).ellipse((0, 0, (D_ + 12) * SS - 1, (D_ + 12) * SS - 1), fill=255)
        av.paste((255, 255, 255, 255), (0, 0), m2.resize((D_ + 12, D_ + 12), Image.LANCZOS))
        av.alpha_composite(logo, (6, 6))
        sh, p = C.bong_do(av, blur=14, alpha=0.55)
        a2 = Image.new("RGBA", (av.width + 2 * p, av.height + 2 * p), (0, 0, 0, 0))
        a2.alpha_composite(sh, (0, 8))
        a2.alpha_composite(av, (p, p))
        self.avatar = a2
        self.vong = _vong_mau(D_ // 2 + 22, 9)
        # huy hiệu + / ✓ trên avatar
        self.hh_cong = self._huy_hieu(HONG_2, icon_cong(34))
        self.hh_ok = self._huy_hieu(XANH_OK, CT.icon_tick(34))
        # chữ
        ten = (kenh.get("ten") or "").strip()
        dong = it.get("dong") or ["FOLLOW KÊNH NGAY", "để xem thêm nhiều căn nhà đẹp"]
        self.ten = np.asarray(C.chu(ten.upper(), "black", 44, fill=C.VANG, shadow=(0, 3, 5, 0.5), track=2)) if ten else None
        self.dong1 = np.asarray(C.chu(dong[0].upper(), "black", 64, fill=C.TRANG, shadow=(0, 4, 6, 0.5), track=1))
        self.dong2 = np.asarray(C.chu(dong[1], "semi", 34, fill=(208, 220, 240))) if len(dong) > 1 and dong[1] else None
        # nút
        self.nut_do = np.asarray(_nut(640, 136, HONG_1, HONG_2, icon_nguoi_cong(66), it.get("nut") or "FOLLOW"))
        self.nut_ok = np.asarray(_nut(640, 136, XAM_1, XAM_2, CT.icon_tick(54, XANH_OK), it.get("nut_sau") or "ĐÃ FOLLOW",
                                      co=50))
        h_, w_ = self.nut_do.shape[:2]
        yg, xg = np.mgrid[0:h_, 0:w_].astype(np.float32)
        self._xy = xg + 0.45 * yg
        glow = Image.new("RGBA", (640 + 100, 136 + 100), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle((50, 50, 689, 185), radius=68, fill=tuple(HONG_1) + (255,))
        self.glow = np.asarray(glow.filter(ImageFilter.GaussianBlur(22)))
        # chip
        self.chips = []
        nh = it.get("chip")
        if nh is not False:
            nh = nh or ["Bật chuông", "Thả tim", "Chia sẻ"]
            loai = ["chuong", "tim", "chia_se"]
            for k, n_ in zip(loai, nh):
                base, x_ic = _chip(n_, 44)
                on = None
                if k == "tim":
                    on, _ = _chip(n_, 44, nen=tuple(DO_TIM) + (235,), vien=(255, 190, 205, 255))
                if k == "chuong":
                    on, _ = _chip(n_, 44, nen=(255, 210, 77, 60), vien=tuple(C.VANG) + (255,), mau_chu=C.VANG)
                self.chips.append({"k": k, "base": base, "on": on, "x_ic": x_ic, "w": base.width})
            self.ic_chuong = CT.icon_chuong(44, C.TRANG)
            self.ic_chuong_on = CT.icon_chuong(44, C.VANG)
            self.ic_tim = icon_tim(42, C.TRANG)
            self.ic_chia = icon_chia_se(40, C.TRANG)
        self.tim_bay = [icon_tim(s_, c_) for s_, c_ in ((58, DO_TIM), (48, (255, 120, 150)), (40, (255, 255, 255)))]
        self.sao = sao_4_canh(56)
        self.tay = CT.ban_tay(250)
        # bố cục
        y = float(it.get("y", 470))
        self.y_av = y + 40
        y = self.y_av + D_ / 2 + 52
        self.y_ten = None
        if self.ten is not None:
            self.y_ten = y + self.ten.shape[0] / 2
            y += self.ten.shape[0] + 16
        self.y_d1 = y + self.dong1.shape[0] / 2
        y += self.dong1.shape[0] + 12
        self.y_d2 = None
        if self.dong2 is not None:
            self.y_d2 = y + self.dong2.shape[0] / 2
            y += self.dong2.shape[0] + 30
        self.y_nut = y + 68
        y += 136 + 30
        self.y_chip = None
        if self.chips:
            self.y_chip = y + 40
            y += 80 + 34
            gap = 16
            tong = sum(c["w"] for c in self.chips) + gap * (len(self.chips) - 1)
            x = (W - tong) / 2
            for c in self.chips:
                c["cx"] = x + c["w"] / 2
                x += c["w"] + gap
        else:
            y += 6
        ch = int(y - self.y_av + 6)
        the = C.hop_bo((960, ch), 38, tuple(C.NAVY) + (236,), vien=tuple(C.NAVY_VIEN) + (255,), vien_w=3)
        ImageDraw.Draw(the).rounded_rectangle((44, 0, 916, 8), radius=4, fill=tuple(C.VANG) + (255,))
        sh, p = C.bong_do(the, blur=26, alpha=0.6)
        t2 = Image.new("RGBA", (the.width + 2 * p, the.height + 2 * p), (0, 0, 0, 0))
        t2.alpha_composite(sh, (0, 12))
        t2.alpha_composite(the, (p, p))
        self.the, self.p_the = np.asarray(t2), p
        self.y_day = self.y_av + ch
        # điểm bấm
        self.p_nut = (W / 2 + 200, self.y_nut + 26)
        tim = next((c for c in self.chips if c["k"] == "tim"), None)
        self.p_tim = (tim["cx"] - tim["w"] / 2 + tim["x_ic"] + 14, self.y_chip + 10) if tim else None
        if self.p_tim is None:
            self.th = None
        # pháo giấy (cố định theo hạt giống ⇒ dựng lại ra y hệt)
        rd = random.Random(20261109)
        self.phao = []
        for _ in range(30):
            ang = math.radians(rd.uniform(195, 345)) if rd.random() < 0.8 else math.radians(rd.uniform(0, 360))
            v = rd.uniform(520, 1080)
            self.phao.append({"x0": W / 2 + rd.uniform(-230, 230), "vx": v * math.cos(ang), "vy": v * math.sin(ang),
                              "w": rd.uniform(10, 18), "r": rd.uniform(0.35, 0.65), "quay": rd.uniform(-14, 14),
                              "g0": rd.uniform(0, 6.28), "mau": rd.choice(MAU_PHAO), "song": rd.uniform(0.85, 1.25)})
        self.bay = []
        for i in range(8):
            self.bay.append({"tre": 0.07 * i, "dx": rd.uniform(-60, 60), "len": rd.uniform(360, 560),
                             "lac": rd.uniform(18, 40), "f": rd.uniform(1.6, 2.6), "k": i % 3, "s": rd.uniform(0.75, 1.1)})
        self.cho_sao = [(-300, -78, 0.10), (310, -70, 0.22), (-250, 74, 0.34), (280, 80, 0.16)]

    # ---------------------------------------------------------------- tiện ích vẽ
    @staticmethod
    def _huy_hieu(mau, icon):
        D_ = 58
        im = Image.new("RGBA", (D_ * SS, D_ * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((0, 0, D_ * SS - 1, D_ * SS - 1), fill=(255, 255, 255, 255))
        d.ellipse((5 * SS, 5 * SS, (D_ - 5) * SS - 1, (D_ - 5) * SS - 1), fill=tuple(mau) + (255,))
        im = im.resize((D_, D_), Image.LANCZOS)
        im.alpha_composite(icon, ((D_ - icon.width) // 2, (D_ - icon.height) // 2))
        return im

    def _quet_sang(self, arr, pha):
        w = arr.shape[1]
        pos = -0.25 * w + 1.55 * w * pha
        band = np.exp(-((self._xy - pos) / 30.0) ** 2) * 0.55
        a = arr.astype(np.float32)
        m = band[..., None] * (a[..., 3:4] / 255.0)
        a[..., :3] += (255.0 - a[..., :3]) * m
        return a.astype(np.uint8)

    def _bam(self, tl):
        """vị trí + độ trong + tỉ lệ bàn tay (None = không hiện)"""
        tb, th = self.tb, self.th
        P1 = self.p_nut
        if tl < tb - 0.5:
            return None
        if tl < tb - 0.08:
            k = ease_out((tl - (tb - 0.5)) / 0.42)
            x, y, a = P1[0] + 330 * (1 - k), P1[1] + 500 * (1 - k), clamp((tl - (tb - 0.5)) / 0.15)
        elif th is None:
            if tl < tb + 0.45:
                x, y, a = P1[0], P1[1], 1.0
            elif tl < tb + 0.85:
                k = smooth((tl - tb - 0.45) / 0.4)
                x, y, a = P1[0] + 220 * k, P1[1] + 380 * k, 1 - k
            else:
                return None
        else:
            P2 = self.p_tim
            if tl < tb + 0.42:
                x, y, a = P1[0], P1[1], 1.0
            elif tl < th - 0.08:
                k = smooth((tl - tb - 0.42) / (th - 0.08 - tb - 0.42))
                x = P1[0] + (P2[0] - P1[0]) * k + 70 * math.sin(math.pi * k)
                y = P1[1] + (P2[1] - P1[1]) * k + 30 * math.sin(math.pi * k)
                a = 1.0
            elif tl < th + 0.45:
                x, y, a = P2[0], P2[1], 1.0
            elif tl < th + 0.85:
                k = smooth((tl - th - 0.45) / 0.4)
                x, y, a = P2[0] + 240 * k, P2[1] + 400 * k, 1 - k
            else:
                return None
        sc = 1.0
        for tp in (tb, th):
            if tp is not None and tp - 0.06 <= tl < tp + 0.2:
                sc = 1 - 0.09 * math.sin(math.pi * (tl - tp + 0.06) / 0.26)
        return x, y, a, sc

    # ---------------------------------------------------------------- API thẻ
    def rect(self):
        return (60, self.y_av - self.D / 2 - 30, W - 60, self.y_day)

    def sfx(self):
        return []          # CTA không SFX (góp ý 04/11/2026)

    def ve(self, frame, t):
        if t < self.t0 - 0.02 or t > self.t1:
            return None
        tl = t - self.t0
        tb, th = self.tb, self.th
        a = ease_out(ramp(tl, 0.0, 0.35))
        dy = 80 * (1 - a)
        C.dan(frame, self.the, (W - self.the.shape[1]) / 2, self.y_av - self.p_the + dy, a)
        # avatar: vòng màu xoay + sóng + huy hiệu
        u = ramp(tl, 0.10, 0.42)
        if u > 0:
            cy = self.y_av + dy
            DN.ve_song(frame, W / 2, cy, tl - 0.5, C.VANG, r0=self.D / 2 + 20, r1=self.D / 2 + 70, chu_ky=1.5,
                       so_vong=2, day=3, alpha=0.55)
            s = max(0.05, DN.back_out(u))
            C.dan_giua(frame, _xoay_np(self.vong, -tl * 140.0), W / 2, cy, clamp(u * 3), s)
            C.dan_giua(frame, self.avatar, W / 2, cy, clamp(u * 3), s)
            v = ramp(tl, 0.42, 0.3)
            if v > 0:
                hx, hy = W / 2, cy + self.D / 2 + 2
                lat = ramp(tl, tb + 0.08, 0.26)
                if lat <= 0:
                    C.dan_giua(frame, self.hh_cong, hx, hy, clamp(v * 3), max(0.05, DN.back_out(v)))
                else:
                    sx = abs(math.cos(math.pi * lat))
                    hh = self.hh_cong if lat < 0.5 else self.hh_ok
                    im = hh.resize((max(1, int(hh.width * sx)), hh.height), Image.BICUBIC)
                    C.dan_giua(frame, im, hx, hy, 1.0, 1.0 + 0.18 * math.sin(math.pi * lat))
        # chữ
        if self.y_ten is not None:
            v = ease_out(ramp(tl, 0.22, 0.3))
            C.dan_giua(frame, self.ten, W / 2, self.y_ten + dy + 18 * (1 - v), v)
        v = ease_out(ramp(tl, 0.28, 0.3))
        C.dan_giua(frame, self.dong1, W / 2, self.y_d1 + dy + 18 * (1 - v), v)
        if self.y_d2 is not None:
            v = ease_out(ramp(tl, 0.36, 0.3))
            C.dan_giua(frame, self.dong2, W / 2, self.y_d2 + dy + 18 * (1 - v), v)
        # nút FOLLOW → ĐÃ FOLLOW
        v = ramp(tl, 0.40, 0.35)
        cy = self.y_nut + dy
        if v > 0:
            nhan = 1.0
            if tb <= tl < tb + 0.22:
                nhan = 1 - 0.07 * math.sin(math.pi * (tl - tb) / 0.22)
            tho = 1.0 + (0.025 * math.sin(2 * math.pi * tl / 0.9) if 0.75 < tl < tb - 0.5 else 0.0)
            s = max(0.05, DN.back_out(v)) * nhan * tho
            doi = clamp((tl - tb - 0.10) / 0.14)
            if doi < 1:
                nhip = 0.5 + 0.5 * math.sin(2 * math.pi * tl / 0.8)
                C.dan_giua(frame, self.glow, W / 2, cy, clamp(v) * (0.40 + 0.40 * nhip) * (1 - doi))
                nut = self.nut_do
                if 0.6 < tl < tb + 0.1:
                    nut = self._quet_sang(nut, ((tl - 0.6) % 1.3) / 1.3)
                C.dan_giua(frame, nut, W / 2, cy, clamp(v * 3) * (1 - doi), s)
            if doi > 0:
                C.dan_giua(frame, self.nut_ok, W / 2, cy, doi, s * (0.9 + 0.1 * DN.back_out(doi)))
        # hàng chip
        if self.chips:
            yc = self.y_chip + dy
            for i, c in enumerate(self.chips):
                v = ramp(tl, 0.52 + 0.08 * i, 0.3)
                if v <= 0:
                    continue
                s = max(0.05, DN.back_out(v))
                bat = 0.0
                if c["k"] == "tim" and th is not None:
                    bat = clamp((tl - th - 0.02) / 0.12)
                if c["k"] == "chuong":
                    bat = clamp((tl - self.t_chuong) / 0.15)
                C.dan_giua(frame, c["base"], c["cx"], yc, clamp(v * 3) * (1 - bat), s)
                if bat > 0 and c["on"] is not None:
                    nay = 1.0
                    if c["k"] == "tim":
                        nay = 1 + 0.10 * math.sin(math.pi * clamp((tl - th) / 0.3))
                    C.dan_giua(frame, c["on"], c["cx"], yc, bat, s * nay)
                ix = c["cx"] - c["w"] / 2 * s + c["x_ic"] * s
                if c["k"] == "chuong":
                    goc = 0.0
                    k = tl - self.t_chuong
                    if 0 <= k < 1.0:
                        goc = 26 * math.sin(2 * math.pi * k / 0.17) * math.exp(-k * 2.6)
                    ic = self.ic_chuong_on if bat > 0.5 else self.ic_chuong
                    ic = ic.rotate(goc, center=(22, 4), resample=Image.BICUBIC) if goc else ic
                    C.dan_giua(frame, ic, ix, yc, clamp(v * 3), s)
                    if 0 <= k < 0.9:
                        DN.ve_song(frame, ix, yc, k, C.VANG, r0=18, r1=70, chu_ky=0.9, so_vong=1, day=3, lap=False)
                elif c["k"] == "tim":
                    pop = 1.0
                    if th is not None and th <= tl < th + 0.3:
                        pop = 1 + 0.45 * math.sin(math.pi * (tl - th) / 0.3)
                    C.dan_giua(frame, self.ic_tim, ix, yc, clamp(v * 3), s * pop)
                else:
                    C.dan_giua(frame, self.ic_chia, ix, yc, clamp(v * 3), s)
        # hiệu ứng nhấn FOLLOW: sóng trắng + pháo giấy + sao lấp lánh
        k = tl - tb
        if 0 <= k < 0.7:
            DN.ve_song(frame, self.p_nut[0], self.p_nut[1] + dy, k, C.TRANG, r0=16, r1=170, chu_ky=0.7, so_vong=1,
                       day=6, lap=False)
        if 0.04 <= k < 1.6:
            self._phao(frame, k - 0.04, cy)
        if 0.08 <= k:
            for ox, oy, tre in self.cho_sao:
                q = k - 0.08 - tre
                if q < 0:
                    continue
                if q < 0.7:
                    sc = math.sin(math.pi * q / 0.7)
                else:
                    sc = 0.35 + 0.25 * math.sin(2 * math.pi * (q - 0.7) / 1.4 + tre * 9)
                    if q > 6:
                        continue
                if sc > 0.02:
                    C.dan_giua(frame, _xoay_np(self.sao, q * 90), W / 2 + ox, cy + oy, min(1.0, sc * 1.4), sc)
        # tim bay lên khi nhấn ♥
        if th is not None and tl >= th:
            self._tim_bay(frame, tl - th, self.p_tim[0] - 14, self.y_chip + dy)
        # bàn tay (trên cùng)
        b = self._bam(tl)
        if b is not None:
            x, y, al, sc = b
            for tp, P in ((tb, self.p_nut), (th, self.p_tim)):
                if tp is not None and 0 <= tl - tp < 0.55 and tp != tb:
                    DN.ve_song(frame, P[0], P[1] + dy, tl - tp, C.TRANG, r0=14, r1=110, chu_ky=0.55, so_vong=1,
                               day=5, lap=False)
            C.dan_giua(frame, self.tay, x, y + dy, al, sc)
        return None

    def _phao(self, frame, k, cy):
        g = 1700.0
        for p in self.phao:
            q = k / p["song"]
            if q >= 1:
                continue
            x = p["x0"] + p["vx"] * k * (1 - 0.35 * k)
            y = cy + p["vy"] * k + 0.5 * g * k * k
            co = 1.0 if q < 0.65 else 1 - (q - 0.65) / 0.35
            w = p["w"] * co
            h = w * p["r"] * (0.35 + 0.65 * abs(math.cos(p["g0"] + k * 9)))
            ang = p["g0"] + p["quay"] * k
            ca, sa = math.cos(ang), math.sin(ang)
            pts = np.array([[x + ca * dx_ - sa * dy_, y + sa * dx_ + ca * dy_]
                            for dx_, dy_ in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))],
                           np.int32)
            if w > 0.8:
                cv2.fillConvexPoly(frame, pts, tuple(int(v) for v in p["mau"]), lineType=cv2.LINE_AA)

    def _tim_bay(self, frame, k, x0, y0):
        for b in self.bay:
            q = (k - b["tre"]) / 1.5
            if q < 0 or q >= 1:
                continue
            y = y0 - b["len"] * ease_out(q)
            x = x0 + b["dx"] * q + b["lac"] * math.sin(2 * math.pi * b["f"] * q)
            s = b["s"] * (0.5 + 0.6 * min(1.0, q * 4))
            al = 1.0 if q < 0.55 else 1 - (q - 0.55) / 0.45
            C.dan_giua(frame, self.tim_bay[b["k"]], x, y, al, s)
