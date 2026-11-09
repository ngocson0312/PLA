# -*- coding: utf-8 -*-
"""Lớp đồ hoạ BĐS trên bản đồ vệ tinh (toạ độ khung 1080×1920):

TRÊN BẢN ĐỒ (theo camera):
  NhaMarker    ghim vàng ngôi nhà rơi + nảy + gợn sóng vàng; vị trí chưa chắc ⇒ vòng "khu vực" vàng nét đứt xoay
  ve_vong      vòng bán kính nét đứt (500 m / 1 km…) mở rộng + nhãn pill ở đỉnh vòng
  DiemTienIch  đường đi THẬT (OSRM) vẽ chạy từ nhà → tiện ích, ghim màu nhóm bật ra, nhãn tên + "≈ khoảng cách"
  TuyenSang    tô sáng đường / tuyến metro theo hình học OSM (vẽ chạy), tên tuyến gắn vào tuyến
  VungSang     tô vùng (hồ, công viên): viền tự vẽ + phủ màu + pill tên
TRÊN MÀN HÌNH (không theo camera):
  TheAnh       thẻ ẢNH / CLIP thật của nhà (bo góc viền trắng, Ken Burns, chú thích), có dây nối về ghim nhà
  TheThongTin  thẻ navy liệt kê thông tin nhà (biểu tượng + nhãn + giá trị), từng dòng hiện đúng lúc đọc
  TheGia       huy hiệu giá vàng lớn, bật back-out + vệt sáng lướt
  TheLienHe    CTA gọi điện: avatar, tên, số điện thoại hiện theo nhóm số đúng lúc đọc, nút "GỌI NGAY" rung + tay bấm
Mọi chữ trên hình chỉ lấy từ lời đọc / thông tin nhà / dữ liệu bản đồ (khoảng cách đo ⇒ luôn "≈").
"""
import math
import os
import re
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import ban_do as B
import bieu_tuong as BT
import chung as C
import cta as CT
import diem_nhan as DN
from chung import W, H, FPS, clamp, ramp, smooth, ease_out

VIEN = (12, 18, 30)
XANH_GOI = (28, 178, 92)
VUNG_CHU = (200, 1372)            # chữ bản đồ chỉ đặt trong dải y này (trên thẻ đầu đề, dưới là sub)


def ease_io(x):
    return C.ease_in_out(x)


# ---------------------------------------------------------------- vẽ cơ bản

def ve_net(frame, P, mau, day, vien=VIEN, day_vien=2, alpha=1.0):
    """polyline nhanh (không glow) có viền tối"""
    if P is None or len(P) < 2 or alpha <= 0.003:
        return
    q = np.round(np.asarray(P)).astype(np.int32).reshape(-1, 1, 2)
    if alpha >= 0.995:
        if vien is not None:
            cv2.polylines(frame, [q], False, vien, int(day + 2 * day_vien), cv2.LINE_AA)
        cv2.polylines(frame, [q], False, tuple(int(v) for v in mau), int(day), cv2.LINE_AA)
        return
    x0, y0 = max(0, int(q[:, 0, 0].min()) - 20), max(0, int(q[:, 0, 1].min()) - 20)
    x1, y1 = min(W, int(q[:, 0, 0].max()) + 20), min(H, int(q[:, 0, 1].max()) + 20)
    if x1 <= x0 or y1 <= y0:
        return
    roi = frame[y0:y1, x0:x1]
    tmp = roi.copy()
    qq = q - np.array([[[x0, y0]]], np.int32)
    if vien is not None:
        cv2.polylines(tmp, [qq], False, vien, int(day + 2 * day_vien), cv2.LINE_AA)
    cv2.polylines(tmp, [qq], False, tuple(int(v) for v in mau), int(day), cv2.LINE_AA)
    cv2.addWeighted(roi, 1 - alpha, tmp, alpha, 0, dst=roi)


def ve_vong_dut(frame, x, y, r, mau, day=3, so=56, goc=0.0, alpha=1.0, phan=0.55):
    """vòng tròn nét đứt có viền tối"""
    if r < 4 or alpha <= 0.003:
        return
    R = int(r + day + 6)
    if R > 2600:
        return
    lay = np.zeros((2 * R, 2 * R, 4), np.uint8)
    buoc = 360.0 / so
    for i in range(so):
        g0 = goc + i * buoc
        cv2.ellipse(lay, (R, R), (int(r), int(r)), 0, g0, g0 + buoc * phan, (0, 0, 0, 150), day + 3, cv2.LINE_AA)
        cv2.ellipse(lay, (R, R), (int(r), int(r)), 0, g0, g0 + buoc * phan, tuple(int(v) for v in mau) + (255,), day,
                    cv2.LINE_AA)
    C.dan(frame, lay, x - R, y - R, alpha)


def ve_hinh_tron(frame, x, y, r, mau, a_to=0.16, alpha=1.0):
    if r < 3 or alpha <= 0.003:
        return
    R = int(r + 2)
    lay = np.zeros((2 * R, 2 * R, 4), np.uint8)
    cv2.circle(lay, (R, R), int(r), tuple(int(v) for v in mau) + (int(255 * a_to),), -1, cv2.LINE_AA)
    C.dan(frame, lay, x - R, y - R, alpha)


def dan_sprite(frame, arr, tipx, tipy, x, y, s=1.0, alpha=1.0, img=None):
    """dán sprite có điểm neo (tipx, tipy) vào (x, y), co giãn s quanh điểm neo"""
    if alpha <= 0.003 or s <= 0.02:
        return
    if abs(s - 1) > 2e-3:
        im = img if img is not None else Image.fromarray(arr)
        arr = np.asarray(im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR))
        tipx, tipy = tipx * s, tipy * s
    C.dan(frame, arr, x - tipx, y - tipy, alpha)


# ---------------------------------------------------------------- đặt nhãn (né chữ, có dây dẫn khi phải đặt xa)

def _trung(rects, r, pad, bo=None):
    x0, y0, x1, y1 = r
    for a in rects:
        if bo is not None and a is bo:
            continue
        if x0 - pad < a[2] and x1 + pad > a[0] and y0 - pad < a[3] and y1 + pad > a[1]:
            return True
    return False


def _ung_vien(x, y_dau, y_mui, nua_w, w, h):
    """các chỗ đặt nhãn w×h quanh ghim (đầu ghim ở y_dau, mũi ở y_mui, nửa bề ngang nua_w) theo thứ tự ưu tiên"""
    d = nua_w + 12
    out = []
    for k, xa in enumerate((0, 70, 150)):
        out += [(("phai", k), (x + d + xa, y_dau - h / 2)),
                (("trai", k), (x - d - xa - w, y_dau - h / 2)),
                (("tren", k), (x - w / 2, y_dau - (y_mui - y_dau) - 10 - h - xa))]
        out += [(("phai_tren", k), (x + d + xa * 0.6, y_dau - h - 40 - xa)),
                (("trai_tren", k), (x - d - xa * 0.6 - w, y_dau - h - 40 - xa)),
                (("phai_duoi", k), (x + d + xa * 0.6, y_mui + 20 + xa * 0.5)),
                (("trai_duoi", k), (x - d - xa * 0.6 - w, y_mui + 20 + xa * 0.5)),
                (("duoi", k), (x - w / 2, y_mui + 14 + xa))]
    return out


def dat_nhan(chiem, cung, x, y_dau, y_mui, nua_w, w, h, cu=None, bo=None, pad=6):
    """→ (khoá chỗ, bx, by) | None. Giữ chỗ cũ nếu chỉ va vật mới hiện sau (ghim) — chỉ đổi khi va vùng cấm / nhãn khác."""
    uv = _ung_vien(x, y_dau, y_mui, nua_w, w, h)
    # nhãn trên / dưới ghim được trượt ngang cho lọt khung (ghim sát mép)
    uv = [(k, (min(max(bx, 12.0), W - 12.0 - w) if k[0] in ("tren", "duoi") else bx, by)) for k, (bx, by) in uv]
    lo, hi = VUNG_CHU

    def hop_le(bx, by):
        return 12 <= bx and bx + w <= W - 12 and lo <= by and by + h <= hi
    if cu is not None:
        for k, (bx, by) in uv:
            if k == cu:
                if hop_le(bx, by) and not _trung(cung, (bx, by, bx + w, by + h), pad - 2, bo):
                    return k, bx, by
                break
    for k, (bx, by) in uv:
        if hop_le(bx, by) and not _trung(chiem.r, (bx, by, bx + w, by + h), pad, bo):
            return k, bx, by
    return None


def ve_day_dan(frame, ax, ay, rect, mau, alpha=1.0):
    """dây mảnh từ đầu ghim tới mép nhãn gần nhất"""
    x0, y0, x1, y1 = rect
    ex, ey = min(max(ax, x0), x1), min(max(ay, y0), y1)
    if abs(ex - ax) + abs(ey - ay) < 30:
        return
    ve_net(frame, [(ax, ay), (ex, ey)], mau, 3, VIEN, 2, alpha)
    B.ve_cham(frame, ex, ey, 5, mau, alpha=alpha)


# ---------------------------------------------------------------- ghim nhà / lô đất

class NhaMarker:
    """nha = {lat, lon, chinh_xac (mặc định True), ban_kinh_m (vòng khu vực khi chưa chắc), nhan, phu}"""

    def __init__(self, nha):
        self.p = [float(nha["lat"]), float(nha["lon"])]
        self.chinh_xac = bool(nha.get("chinh_xac", True))
        self.r_m = float(nha.get("ban_kinh_m", 80))
        mac = "VỊ TRÍ LÔ ĐẤT" if self.chinh_xac else "KHU VỰC LÔ ĐẤT"
        self.nhan = nha.get("nhan", mac)
        self.phu = nha.get("phu")
        self.sp = BT.ghim_nha(1.25)
        self.side = None

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
                a = smooth(clamp(tl / 0.5)) * alpha
                ve_hinh_tron(frame, x, y, rp, C.VANG, 0.17, a)
                ve_vong_dut(frame, x, y, rp, C.VANG, 3, so=max(18, min(72, int(rp / 9))), goc=tl * 18, alpha=a)
        DN.ve_song(frame, x, y, tl - 0.35, C.VANG, r0=14, r1=118, chu_ky=1.7, so_vong=2, day=4, alpha=alpha)
        u = clamp(tl / 0.55)
        dy = -190 * (1 - DN.bounce_out(u))
        DN._bong_elip(frame, x, y + 2, 26 * (0.4 + 0.6 * u), 8 * (0.4 + 0.6 * u), 0.5 * alpha * u)
        img, arr, tx, ty = self.sp
        dan_sprite(frame, arr, tx, ty, x, y + dy, 1.0, alpha * clamp(u * 4), img)
        top = y + dy - ty
        r = (x - tx * 0.6, top, x + tx * 0.6, y)
        self._r = r
        self._xy = (x, y + dy, tx, ty)
        chiem.dat(r)
        self._r = chiem.r[-1]
        return r

    def ve_nhan(self, frame, tl, chiem, cung, alpha=1.0):
        """nhãn 'KHU VỰC LÔ ĐẤT' — gọi SAU khi mọi ghim đã đặt (để né), TRƯỚC nhãn tiện ích (được ưu tiên chỗ)"""
        if not self.nhan or tl < 0.45 or alpha <= 0.003 or getattr(self, "_xy", None) is None:
            return
        x, y, tx, ty = self._xy
        a = ease_out(ramp(tl, 0.45, 0.3)) * alpha
        im, ar, w, h, p = BT.nhan_tien_ich(self.nhan, self.phu, C.VANG, 30)
        kq = dat_nhan(chiem, cung, x, y - ty * 0.62, y, tx * 0.6, w, h, self.side, bo=self._r)
        if kq is None:
            self.side = None
            return
        self.side, bx, by = kq
        rr = (bx, by, bx + w, by + h)
        if self.side[1] > 0 or "_" in self.side[0]:
            ve_day_dan(frame, x, y - ty * 0.62, rr, C.VANG, a)
        C.dan(frame, ar, bx - p, by - p + 10 * (1 - a), a)
        chiem.dat(rr)
        cung.append(rr)
        self._xy = None


# ---------------------------------------------------------------- vòng bán kính

def ve_vong(frame, cam, tam, r_m, tl, mau=C.TRANG, nhan=None, alpha=1.0):
    if tl < 0 or alpha <= 0.003:
        return None
    x, y = cam.chieu(tam[0], tam[1])
    u = ease_out(clamp(tl / 0.8))
    rp = r_m / cam.m_per_px() * u
    if rp < 6:
        return None
    ve_hinh_tron(frame, x, y, rp, mau, 0.05, alpha)
    ve_vong_dut(frame, x, y, rp, mau, 3, so=max(24, min(90, int(rp / 12))), goc=-tl * 6, alpha=alpha * 0.95)
    if nhan is None:
        nhan = ("%d M" % r_m) if r_m < 1000 else (("%.1f KM" % (r_m / 1000.0)).replace(".0 ", " ").replace(".", ","))
        nhan = nhan.replace(",0 KM", " KM")
    pill = B.nhan_pill(nhan, "xbold", 24, C.NAVY, C.VANG, pad=(16, 8))
    py = y - rp
    if py > VUNG_CHU[0] + 10 and u > 0.6:
        C.dan_giua(frame, pill, x, py, alpha * clamp((u - 0.6) / 0.3))
        return (x - pill.shape[1] / 2, py - pill.shape[0] / 2, x + pill.shape[1] / 2, py + pill.shape[0] / 2)
    return None


# ---------------------------------------------------------------- tiện ích: đường đi + ghim + nhãn

class DiemTienIch:
    """1 tiện ích trong cảnh: {p (đích), ten, nhom, chu (khoảng cách), duong [[lat, lon]…] | None, kieu, t, dai_ve,
    nhan (True/False), co}. t = lúc GHIM bật ra (đặt đúng giây đọc tên); đường đi vẽ TRƯỚC đó dai_ve giây."""

    def __init__(self, d):
        self.d = d
        self.p = d["p"]
        self.g = BT.nhom(d.get("nhom"))
        self.mau = tuple(DN.mau(d["mau"]) if d.get("mau") else self.g["mau"])
        self.duong = np.asarray(d["duong"], dtype=np.float64) if d.get("duong") else None
        self.dai_ve = float(d.get("dai_ve", 1.0 if self.duong is not None else 0.0))
        self.t_ghim = float(d["t"])
        self.t = self.t_ghim - (self.dai_ve if self.duong is not None else 0.0)
        self.co = float(d.get("co", 0.95))
        self.sp = BT.ghim(d.get("nhom"), self.co, mau=self.mau)
        icon_phu = {"di_bo": "di_bo", "o_to": "o_to"}.get(d.get("kieu"))
        self.lab = BT.nhan_tien_ich(d["ten"], d.get("chu"), self.mau, int(d.get("co_chu", 25)), icon_phu) \
            if d.get("nhan", True) and d.get("ten") else None
        self.side = None

    def ve_duong(self, frame, cam, t, alpha=1.0):
        if self.duong is None or t < self.t or alpha <= 0.003:
            return
        P = cam.chieu_mang(self.duong)
        u = smooth(clamp((t - self.t) / max(0.05, self.dai_ve)))
        part, head = B.doan_theo_tien_do(P, u)
        ve_net(frame, part, self.mau, 7, VIEN, 2, alpha)
        if u < 0.999 and head is not None:
            B.ve_cham(frame, head[0], head[1], 8, C.TRANG, alpha=alpha)
        elif alpha > 0.5:
            DN.ve_dong_chay(frame, P, t - self.t - self.dai_ve, toc=95, dash=12, gap=38, mau_=C.TRANG, day=3)

    def ve_ghim(self, frame, cam, t, chiem, alpha=1.0):
        self._xy = None
        tl = t - self.t_ghim
        if tl < 0 or alpha <= 0.003:
            return
        x, y = cam.chieu(self.p[0], self.p[1])
        if not (-60 < x < W + 60 and -60 < y < H + 60):
            return
        DN.ve_song(frame, x, y, tl, self.mau, r0=8, r1=58, chu_ky=1.5, so_vong=1, day=3, alpha=alpha * 0.9, lap=False)
        s = 0.3 + 0.7 * DN.back_out(clamp(tl / 0.32))
        img, arr, tx, ty = self.sp
        dan_sprite(frame, arr, tx, ty, x, y, s, alpha * clamp(tl / 0.1), img)
        chiem.dat((x - tx * 0.55, y - ty, x + tx * 0.55, y))
        self._r = chiem.r[-1]
        self._xy = (x, y, tx, ty)

    def ve_nhan(self, frame, cam, t, chiem, cung, alpha=1.0):
        tl = t - self.t_ghim - 0.12
        if self.lab is None or tl < 0 or alpha <= 0.003 or getattr(self, "_xy", None) is None:
            return
        x, y, tx, ty = self._xy
        im, ar, w, h, p = self.lab
        kq = dat_nhan(chiem, cung, x, y - ty * 0.62, y, tx * 0.55, w, h, self.side, bo=self._r)
        if kq is None:
            self.side = None
            return
        self.side, bx, by = kq
        a = ease_out(clamp(tl / 0.28)) * alpha
        rr = (bx, by, bx + w, by + h)
        if self.side[1] > 0 or "_" in self.side[0]:
            ve_day_dan(frame, x, y - ty * 0.62, rr, self.mau, a)
        dx = {"phai": -14, "trai": 14}.get(self.side[0], 0) * (1 - a)
        C.dan(frame, ar, bx - p + dx, by - p, a)
        chiem.dat(rr)
        cung.append(rr)


# ---------------------------------------------------------------- tô sáng tuyến (đường, metro)

class TuyenSang:
    """{tuyen: key, t, mau, kieu: duong|metro, ten (chữ | true = tên OSM | false), dai_ve, day}"""

    def __init__(self, d, g):
        self.t = float(d.get("t", 0))
        self.kieu = d.get("kieu", "duong")
        self.mau = DN.mau(d.get("mau"), 0) if d.get("mau") else (C.VANG if self.kieu == "duong" else (64, 156, 255))
        self.cac = [np.asarray(c, dtype=np.float64) for c in (g.get("cac_tuyen") or [g["tuyen"]]) if len(c) >= 2]
        self.dai = [C.dai_tuyen_m(c.tolist()) for c in self.cac]
        self.dai_ve = float(d.get("dai_ve", 1.2))
        self.day = int(d.get("day", 7 if self.kieu == "duong" else 8))
        ten = d.get("ten", True)
        self.ten = (g.get("ten_ke_hoach") or g.get("ten") or "") if ten is True else (ten or "")

    def ve(self, frame, cam, t, alpha=1.0):
        """vẽ tuyến (chạy theo tiến độ); nhớ chuỗi hiện rõ nhất để ve_ten gắn tên"""
        self._best = None
        if t < self.t or alpha <= 0.003:
            return
        u = smooth(clamp((t - self.t) / max(0.05, self.dai_ve)))
        self._u = u
        best = None
        for c in self.cac:
            P = cam.chieu_mang(c)
            m = (P[:, 0] > -60) & (P[:, 0] < W + 60) & (P[:, 1] > VUNG_CHU[0]) & (P[:, 1] < VUNG_CHU[1])
            m_rong = (P[:, 0] > -600) & (P[:, 0] < W + 600) & (P[:, 1] > -600) & (P[:, 1] < H + 600)
            if not m_rong.any():
                continue
            part, head = B.doan_theo_tien_do(P, u)
            if self.kieu == "metro":
                ve_net(frame, part, (255, 255, 255), self.day + 4, VIEN, 2, alpha)
                ve_net(frame, part, self.mau, self.day, None, 0, alpha)
                if u >= 0.999 and alpha > 0.5:
                    DN.ve_dong_chay(frame, P, t - self.t - self.dai_ve, toc=70, dash=16, gap=34, mau_=(255, 255, 255), day=3)
            else:
                ve_net(frame, part, self.mau, self.day, VIEN, 2, alpha)
            dai_px = float(np.linalg.norm(np.diff(P[m], axis=0), axis=1).sum()) if m.sum() > 1 else 0.0
            if best is None or dai_px > best[0]:
                best = (dai_px, P, head)
        if best is not None and u < 0.999 and best[2] is not None:
            B.ve_cham(frame, best[2][0], best[2][1], 7, C.TRANG, alpha=alpha)
        self._best = best

    def ve_ten(self, frame, t, chiem, alpha=1.0):
        best = getattr(self, "_best", None)
        if self.ten and best is not None and best[0] > 60 and self._u >= 0.35:
            DN.ve_ten_tuyen(frame, best[1], self.ten, self.mau, chiem, t - self.t - 0.35 * self.dai_ve,
                            neo=(W * 0.5, H * 0.42), alpha=alpha)


class VungSang:
    """{vung: key, t, mau, nhan (chữ | true = tên OSM | false), diem_nhan [lat, lon]}"""

    def __init__(self, d, g):
        self.t = float(d.get("t", 0))
        self.mau = DN.mau(d.get("mau"), 3) if d.get("mau") else (70, 180, 255)
        self.rings = [np.asarray(v, dtype=np.float64) for v in g.get("vong") or [] if len(v) >= 3]
        nh = d.get("nhan", True)
        self.nhan = (g.get("ten_ke_hoach") or g.get("ten") or "") if nh is True else (nh or "")
        self.p_nhan = d.get("diem_nhan") or g.get("diem")
        self.a_to = float(d.get("a_to", 0.30))

    def ve(self, frame, cam, t, alpha=1.0):
        if t < self.t or alpha <= 0.003 or not self.rings:
            return
        px = [cam.chieu_mang(r) for r in self.rings]
        af = smooth(ramp(t, self.t + 0.3, 0.5)) * alpha
        if af > 0:
            B.ve_vung(frame, px, self.mau, alpha_to=self.a_to, vien=None, day_vien=0, alpha=af)
        uo = smooth(ramp(t, self.t, 0.8))
        for r_ in px:
            if alpha > 0.5:
                DN.ve_vien_chay(frame, r_, uo, self.mau, 4)

    def ve_nhan(self, frame, cam, t, chiem, alpha=1.0):
        if t < self.t or alpha <= 0.003 or not self.rings:
            return
        if self.nhan and self.p_nhan:
            x, y = cam.chieu(self.p_nhan[0], self.p_nhan[1])
            if 60 < x < W - 60 and VUNG_CHU[0] < y < VUNG_CHU[1]:
                DN.ve_song(frame, x, y, t - self.t - 0.2, self.mau, r0=14, r1=100, chu_ky=1.6, lap=False, alpha=alpha)
                chiem.dat(DN.ve_pop(frame, DN.pill_cham(self.nhan, self.mau, 30), x, y, t - self.t - 0.35, alpha))


# ================================================================ thẻ trên màn hình

def _bo_goc(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    return np.asarray(m).astype(np.float32)[..., None] / 255.0


class TheAnh:
    """{anh: file | [file…] (ảnh hoặc clip), tu, den, vi_tri: giua|phai|trai|tren, rong, cao, chu: str | [str…],
    doi (giây mỗi ảnh), noi_nha (dây nối về ghim nhà, mặc định khi vi_tri != giua), phu_toi (làm tối bản đồ, 0–0.7),
    y (tâm dọc)} — ảnh giữ nguyên, chỉ cắt khung vừa thẻ + zoom chậm 1,00 → 1,08."""

    def __init__(self, it, tim_file):
        self.t0, self.t1 = float(it["tu"]), float(it["den"])
        files = it["anh"] if isinstance(it["anh"], list) else [it["anh"]]
        self.vt = it.get("vi_tri", "giua")
        rong = int(it.get("rong", {"giua": 880, "tren": 880}.get(self.vt, 500)))
        src0 = self._doc(tim_file(files[0]), None)
        ar = src0["ar"]
        cao = int(it.get("cao", max(int(rong * 0.62), min(int(rong / ar), int(rong * 1.18)))))
        self.w, self.h = rong, cao
        self.nguon = [self._doc(tim_file(f), (rong, cao)) for f in files]
        n = len(self.nguon)
        self.doi = float(it.get("doi", (self.t1 - self.t0) / n))
        chu = it.get("chu")
        if chu is None:
            chu = [os.path.splitext(os.path.basename(f))[0] for f in files]
        if isinstance(chu, str):
            chu = [chu] * n
        self.chu = [self._nhan(c) if c else None for c in chu] + [None] * n
        self.phu_toi = float(it.get("phu_toi", 0.45 if self.vt == "giua" else 0.0))
        self.noi_nha = bool(it.get("noi_nha", self.vt != "giua"))
        self.vien, self.R = 7, 30
        self.mask = _bo_goc(self.w, self.h, self.R - 4)
        # khung tĩnh: bóng + viền trắng
        k = C.hop_bo((self.w + 2 * self.vien, self.h + 2 * self.vien), self.R, (255, 255, 255, 255))
        sh, p = C.bong_do(k, blur=22, alpha=0.6)
        fr = Image.new("RGBA", (k.width + 2 * p, k.height + 2 * p), (0, 0, 0, 0))
        fr.alpha_composite(sh, (0, 12))
        fr.alpha_composite(k, (p, p))
        self.khung = np.array(fr)
        self.ox, self.oy = p + self.vien, p + self.vien
        cx = {"giua": W / 2, "tren": W / 2, "phai": W - 40 - self.w / 2, "trai": 40 + self.w / 2}.get(self.vt, W / 2)
        cy = float(it.get("y", {"giua": 770, "tren": 640}.get(self.vt, 640)))
        self.cx, self.cy = float(it.get("x", cx)), cy

    def _doc(self, path, box):
        ext = os.path.splitext(path)[1].lower()
        if ext in (".mp4", ".mov", ".m4v", ".mkv", ".webm"):
            info = C.probe(path)
            ar = info["w"] / max(1, info["h"])
            if box is None:
                return {"ar": ar}
            bw, bh = int(box[0] * 1.1), int(box[1] * 1.1)
            n = int(max(1.0, info["duration"]) * FPS)
            vf = "fps=%d,scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d" % (FPS, bw, bh, bw, bh)
            r = subprocess.run([C.ffbin("ffmpeg"), "-v", "error", "-i", path, "-an", "-vf", vf, "-frames:v", str(min(n, 900)),
                                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
            k = len(r.stdout) // (bw * bh * 3)
            return {"ar": ar, "clip": np.frombuffer(r.stdout[:k * bw * bh * 3], np.uint8).reshape(k, bh, bw, 3)}
        im = Image.open(path)
        try:
            from PIL import ImageOps
            im = ImageOps.exif_transpose(im)
        except Exception:
            pass
        im = im.convert("RGB")
        ar = im.width / im.height
        if box is None:
            return {"ar": ar}
        bw, bh = int(box[0] * 1.1), int(box[1] * 1.1)
        return {"ar": ar, "anh": np.asarray(C.cover(im, bw, bh))}

    def _nhan(self, text):
        t = C.chu(text.upper(), "xbold", 30, fill=C.TRANG, track=1)
        w, h = t.width + 56, t.height + 26
        box = C.hop_bo((w, h), h // 2, tuple(C.NAVY) + (240,), vien=tuple(C.VANG) + (255,), vien_w=2)
        box.alpha_composite(t, (28, 13))
        sh, p = C.bong_do(box, blur=10, alpha=0.55)
        out = Image.new("RGBA", (w + 2 * p, h + 2 * p), (0, 0, 0, 0))
        out.alpha_composite(sh, (0, 5))
        out.alpha_composite(box, (p, p))
        return np.asarray(out)

    def _khung_anh(self, k, tl_k):
        src = self.nguon[k]
        if "clip" in src:
            cl = src["clip"]
            img = cl[min(len(cl) - 1, max(0, int(tl_k * FPS)))] if len(cl) else np.zeros((self.h, self.w, 3), np.uint8)
        else:
            img = src["anh"]
        bh, bw = img.shape[:2]
        s = 1.0 + 0.08 * smooth(clamp(tl_k / max(1.0, self.doi + 0.6)))
        cw, ch = bw / s, bh / s
        x0, y0 = (bw - cw) / 2, (bh - ch) / 2
        M = np.float32([[self.w / cw, 0, -x0 * self.w / cw], [0, self.h / ch, -y0 * self.h / ch]])
        return cv2.warpAffine(img, M, (self.w, self.h), flags=cv2.INTER_AREA if self.w < cw else cv2.INTER_LINEAR)

    def the(self, t):
        """→ (ảnh RGBA thẻ, chú thích) ở giây t"""
        tl = t - self.t0
        n = len(self.nguon)
        k = min(n - 1, max(0, int(tl / self.doi)))
        tk = tl - k * self.doi
        anh = self._khung_anh(k, tk).astype(np.float32)
        if k + 1 < n and tk > self.doi - 0.3:
            w = smooth((tk - (self.doi - 0.3)) / 0.3)
            anh = anh * (1 - w) + self._khung_anh(k + 1, tk - self.doi).astype(np.float32) * w
        out = self.khung.copy()
        reg = out[self.oy:self.oy + self.h, self.ox:self.ox + self.w]
        reg[..., :3] = (reg[..., :3].astype(np.float32) * (1 - self.mask) + anh * self.mask).astype(np.uint8)
        nh = self.chu[k]
        if k + 1 < n and tk > self.doi - 0.3 and smooth((tk - (self.doi - 0.3)) / 0.3) > 0.5:
            nh = self.chu[k + 1]
        return out, nh

    def ve(self, frame, t, nha_xy=None):
        if t < self.t0 - 0.02 or t > self.t1:
            return None
        tl = t - self.t0
        a_in = clamp(tl / 0.18)
        a = min(a_in, clamp((self.t1 - t) / 0.25))
        if self.phu_toi > 0:
            k = self.phu_toi * a
            frame[:] = (frame.astype(np.float32) * (1 - k)).astype(np.uint8)
        card, nh = self.the(t)
        s = 0.55 + 0.45 * DN.back_out(clamp(tl / 0.42))
        cx, cy = self.cx, self.cy
        if self.noi_nha and nha_xy is not None:
            bx, by = cx, cy + self.h / 2 + 4
            if nha_xy[1] < cy:
                by = cy - self.h / 2 - 4
            u = smooth(clamp((tl - 0.2) / 0.35))
            ex, ey = bx + (nha_xy[0] - bx) * u, by + (nha_xy[1] - by) * u
            ve_net(frame, [(bx, by), (ex, ey)], C.VANG, 3, VIEN, 2, a)
            B.ve_cham(frame, ex, ey, 7, C.VANG, alpha=a)
            # thẻ bung ra từ phía ghim nhà
            cx = nha_xy[0] + (cx - nha_xy[0]) * min(1.0, 0.35 + 0.65 * ease_out(clamp(tl / 0.42)))
            cy = nha_xy[1] + (cy - nha_xy[1]) * min(1.0, 0.35 + 0.65 * ease_out(clamp(tl / 0.42)))
        C.dan_giua(frame, card, cx, cy, a, s)
        if nh is not None:
            v = ease_out(ramp(tl, 0.3, 0.3))
            C.dan_giua(frame, nh, cx, cy + (self.h / 2 - 8) * s + 10 * (1 - v), a * v)
        return (cx - self.w / 2, cy - self.h / 2, cx + self.w / 2, cy + self.h / 2 + 40)

    def sfx(self):
        return [{"t": self.t0, "file": "camera-shutter.mp3", "muc": "nhe"}]


class TheThongTin:
    """{tu, den, tieu_de, dong: [{icon, nhan, gia_tri, t}], day (đáy thẻ, mặc định 1365) | y (đỉnh)}"""

    def __init__(self, it):
        self.t0, self.t1 = float(it["tu"]), float(it["den"])
        self.w = int(it.get("rong", 940))
        self.tit = C.chu(it["tieu_de"].upper(), "xbold", 34, fill=C.VANG, track=2) if it.get("tieu_de") else None
        self.dong = []
        D_ = 92
        for d in it.get("dong", []):
            ic = Image.new("RGBA", (D_, D_), (0, 0, 0, 0))
            ImageDraw.Draw(ic).ellipse((0, 0, D_ - 1, D_ - 1), fill=tuple(C.VANG) + (255,))
            g = BT.icon(d.get("icon", "vi_tri"), 54, C.NAVY)
            ic.alpha_composite(g, ((D_ - g.width) // 2, (D_ - g.height) // 2))
            nh = C.chu(d.get("nhan", "").upper(), "bold", 26, fill=(176, 194, 222), track=2) if d.get("nhan") else None
            co = 54
            gt = C.chu(d.get("gia_tri", ""), "black", co, fill=C.TRANG)
            while gt.width > self.w - 60 - D_ - 30 and co > 30:
                co -= 3
                gt = C.chu(d.get("gia_tri", ""), "black", co, fill=C.TRANG)
            txt = C.xep_doc([x for x in (nh, gt) if x is not None], gap=0, align="left")
            row = Image.new("RGBA", (self.w - 60, max(D_ + 6, txt.height + 6)), (0, 0, 0, 0))
            row.alpha_composite(ic, (0, (row.height - D_) // 2))
            row.alpha_composite(txt, (D_ + 26, (row.height - txt.height) // 2))
            self.dong.append((float(d.get("t", self.t0)), np.asarray(row), row.height))
        gap = 16
        h = 34 + (self.tit.height + 22 if self.tit is not None else 0) + sum(r[2] for r in self.dong) + gap * max(0, len(self.dong) - 1) + 30
        box = C.hop_bo((self.w, h), 28, tuple(C.NAVY) + (236,), vien=tuple(C.NAVY_VIEN) + (255,), vien_w=2)
        d_ = ImageDraw.Draw(box)
        d_.rounded_rectangle((40, 0, self.w - 40, 7), radius=3, fill=tuple(C.VANG) + (255,))
        y = 34
        if self.tit is not None:
            box.alpha_composite(self.tit, (34, y))
            y += self.tit.height + 22
        self.y_dong = []
        for _, _, rh in self.dong:
            self.y_dong.append(y)
            y += rh + gap
        sh, p = C.bong_do(box, blur=20, alpha=0.55)
        out = Image.new("RGBA", (self.w + 2 * p, h + 2 * p), (0, 0, 0, 0))
        out.alpha_composite(sh, (0, 10))
        out.alpha_composite(box, (p, p))
        self.nen, self.p, self.h = np.asarray(out), p, h
        self.x = (W - self.w) / 2
        self.y = float(it["y"]) if it.get("y") is not None else float(it.get("day", 1365)) - h

    def rect(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def ve(self, frame, t):
        if t < self.t0 - 0.02 or t > self.t1:
            return None
        tl = t - self.t0
        a = min(ease_out(clamp(tl / 0.3)), clamp((self.t1 - t) / 0.25))
        dy = 40 * (1 - ease_out(clamp(tl / 0.35)))
        C.dan(frame, self.nen, self.x - self.p, self.y - self.p + dy, a)
        for (td, row, rh), yd in zip(self.dong, self.y_dong):
            v = ease_out(ramp(t, td, 0.3))
            if v <= 0:
                continue
            C.dan(frame, row, self.x + 30 - 30 * (1 - v), self.y + yd + dy, a * v)
        return self.rect()

    def sfx(self):
        return [{"t": d[0], "file": "pop-2.mp3", "muc": "nhe"} for d in self.dong]


class TheGia:
    """{tu, den, nhan ('GIÁ CHÀO'), gia ('NHỈNH 80 TỶ'), y (tâm)}"""

    def __init__(self, it):
        self.t0, self.t1 = float(it["tu"]), float(it["den"])
        nhan = C.chu((it.get("nhan") or "GIÁ").upper(), "xbold", 34, fill=C.NAVY, track=4)
        gia = C.chu(it["gia"].upper(), "black", 92, fill=C.NAVY, track=1)
        while gia.width > 760:
            gia = C.chu(it["gia"].upper(), "black", int(gia.height * 0.86), fill=C.NAVY, track=1)
        ic = BT.icon("gia", 74, C.NAVY)
        w = max(nhan.width, gia.width) + ic.width + 150
        h = nhan.height + gia.height + 66
        S = 2
        g = np.zeros((h * S, w * S, 4), np.uint8)
        yy = np.linspace(0, 1, h * S)[:, None]
        top, bot = np.array([255, 226, 120]), np.array([236, 168, 40])
        g[..., :3] = (top * (1 - yy[..., None]) + bot * yy[..., None]).astype(np.uint8)[:, :1, :].repeat(w * S, 1)
        m = Image.new("L", (w * S, h * S), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w * S - 1, h * S - 1), radius=34 * S, fill=255)
        g[..., 3] = np.asarray(m)
        box = Image.fromarray(g).resize((w, h), Image.LANCZOS)
        ImageDraw.Draw(box).rounded_rectangle((5, 5, w - 6, h - 6), radius=30, outline=(255, 248, 210, 255), width=3)
        box.alpha_composite(ic, (40, (h - ic.height) // 2))
        xt = 40 + ic.width + 34
        box.alpha_composite(nhan, (xt, 26))
        box.alpha_composite(gia, (xt, 26 + nhan.height + 10))
        self.mask = np.asarray(box.getchannel("A")).astype(np.float32) / 255.0
        self.box = np.asarray(box)
        sh, p = C.bong_do(box, blur=26, alpha=0.65)
        out = Image.new("RGBA", (w + 2 * p, h + 2 * p), (0, 0, 0, 0))
        out.alpha_composite(sh, (0, 14))
        self.bong, self.p = np.asarray(out), p
        self.w, self.h = w, h
        self.cy = float(it.get("y", 860))

    def ve(self, frame, t):
        if t < self.t0 - 0.02 or t > self.t1:
            return None
        tl = t - self.t0
        a = min(clamp(tl / 0.12), clamp((self.t1 - t) / 0.25))
        s = 0.3 + 0.7 * DN.back_out(clamp(tl / 0.45))
        card = self.box.copy()
        u = (tl - 0.5) / 0.7
        if 0 < u < 1:
            xs = -0.3 * self.w + u * 1.6 * self.w
            yy, xx = np.mgrid[0:self.h, 0:self.w]
            band = np.clip(1 - np.abs((xx + yy * 0.45) - xs) / 46.0, 0, 1) * self.mask * 0.65
            card = card.astype(np.float32)
            card[..., :3] = card[..., :3] * (1 - band[..., None]) + 255 * band[..., None]
            card = card.astype(np.uint8)
        C.dan_giua(frame, self.bong, W / 2, self.cy + 14, a * 0.9, s)
        C.dan_giua(frame, card, W / 2, self.cy, a, s)
        return (W / 2 - self.w / 2, self.cy - self.h / 2, W / 2 + self.w / 2, self.cy + self.h / 2)

    def sfx(self):
        return [{"t": self.t0 + 0.05, "file": "ka-ching.mp3", "muc": "chinh"}]


SDT_CO, SDT_TRACK, SDT_GAP = 86, 3, 20   # cỡ số, cách chữ số, cách nhóm (px)


def chia_so_hien(so, ep=None):
    """Cách nhóm HIỆN số điện thoại (chốt 09/11/2026): 10 số → 4-3-3 (0904 282 858), 11 số → 4-3-4, 8 số → 4-4,
    còn lại 4 + nhóm 3 (dư gộp vào nhóm cuối). `ep` = chuỗi mẫu ('0904 282 858') nếu muốn ép cách khác."""
    if ep:
        nh = [len(re.sub(r"\D", "", x)) for x in str(ep).split()]
        if sum(nh) == len(so) and all(nh):
            return nh
    n = len(so)
    if n <= 4:
        return [n] if n else []
    if n == 8:
        return [4, 4]
    nh = [4] + [3] * ((n - 4) // 3)
    du = (n - 4) % 3
    if du:
        nh[-1] += du
    return nh


class TheLienHe:
    """CTA gọi điện (không SFX): {tu, den, ten, sdt, sdt_tu [giây mỗi nhóm số], nhan ('LIÊN HỆ NGAY'),
    dong_cuoi (chữ lấy từ lời), t_bam (giây tay bấm), y (đỉnh thẻ)}"""

    def __init__(self, it):
        self.t0, self.t1 = float(it["tu"]), float(it["den"])
        self.it = it
        D_ = 170
        av = Image.new("RGBA", (D_ + 14, D_ + 14), (0, 0, 0, 0))
        dv = ImageDraw.Draw(av)
        dv.ellipse((0, 0, D_ + 13, D_ + 13), fill=(255, 255, 255, 255))
        dv.ellipse((7, 7, D_ + 6, D_ + 6), fill=tuple(C.VANG) + (255,))
        g = BT.icon("nguoi", 104, C.NAVY)
        av.alpha_composite(g, ((D_ + 14 - g.width) // 2, (D_ + 14 - g.height) // 2 + 8))
        self.av = av
        self.nhan = np.asarray(C.chu((it.get("nhan") or "LIÊN HỆ NGAY").upper(), "xbold", 34, fill=(200, 214, 236), track=4))
        self.ten = np.asarray(C.chu(it["ten"].upper(), "black", 74, fill=C.VANG, shadow=(0, 4, 6, 0.5), track=2)) \
            if it.get("ten") else None
        # số điện thoại: HIỆN theo nhóm 4-3-3 (góp ý 09/11: nhóm theo lời đọc "0904 28 28 58" cách nhau quá) — từng chữ số
        # bật đúng lúc đọc; `sdt` giữ cách nhóm THEO LỜI (khớp sdt_tu), `sdt_hien` (tuỳ chọn) ép cách nhóm hiện
        nhom_doc = it["sdt"].split()
        tu_doc = [float(x) for x in (it.get("sdt_tu") or [])] + [None] * len(nhom_doc)
        self.t_so = []
        for g, s_ in enumerate(nhom_doc):
            for k, ch in enumerate(re.sub(r"\D", "", s_)):
                self.t_so.append(None if tu_doc[g] is None else tu_doc[g] + 0.07 * k)
        so = re.sub(r"\D", "", it["sdt"])
        self.nhom_hien = chia_so_hien(so, it.get("sdt_hien"))
        f = C.font("black", SDT_CO)
        self.so_anh, self.so_o = {}, {}
        for ch in set(so):
            self.so_anh[ch] = np.asarray(C.chu(ch, "black", SDT_CO, fill=C.TRANG, shadow=(0, 4, 6, 0.5)))
            self.so_o[ch] = f.getlength(ch) + SDT_TRACK
        self.so = so
        self.sdt = [self.so_anh[ch] for ch in so]
        self.ic_dt = np.asarray(BT.icon("dien_thoai", 64, C.VANG))
        gl = BT.icon("dien_thoai", 58, C.TRANG)
        self.nut, self.x_ic = CT._nut(XANH_GOI, "GỌI NGAY", rong=600, cao=132, cho_icon=58)
        self.gl = gl
        self.dong_cuoi = None
        if it.get("dong_cuoi"):
            t = C.chu(it["dong_cuoi"], "semi", 34, fill=(220, 230, 245))
            ic = BT.icon("vi_tri", 40, C.VANG)
            row = Image.new("RGBA", (ic.width + 12 + t.width, max(ic.height, t.height)), (0, 0, 0, 0))
            row.alpha_composite(ic, (0, (row.height - ic.height) // 2))
            row.alpha_composite(t, (ic.width + 12, (row.height - t.height) // 2))
            self.dong_cuoi = np.asarray(row)
        glow = Image.new("RGBA", (600 + 80, 132 + 80), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle((40, 40, 639, 171), radius=66, fill=(90, 230, 140, 255))
        self.glow = np.asarray(glow.filter(ImageFilter.GaussianBlur(18)))
        self.tay = CT.ban_tay(250)
        # bố cục
        y = float(it.get("y", 470))
        self.y_av = y + 40
        y = self.y_av + D_ / 2 + 40
        self.y_nhan = y + self.nhan.shape[0] / 2
        y += self.nhan.shape[0] + 14
        self.y_ten = None
        if self.ten is not None:
            self.y_ten = y + self.ten.shape[0] / 2
            y += self.ten.shape[0] + 26
        hs = max(s.shape[0] for s in self.sdt)
        self.y_sdt = y + hs / 2
        y += hs + 40
        self.y_nut = y + 66
        y += 132 + 30
        self.y_cuoi = None
        if self.dong_cuoi is not None:
            self.y_cuoi = y + self.dong_cuoi.shape[0] / 2
            y += self.dong_cuoi.shape[0] + 26
        ch = int(y - self.y_av + 10)
        the = C.hop_bo((960, ch), 38, tuple(C.NAVY) + (236,), vien=tuple(C.NAVY_VIEN) + (255,), vien_w=3)
        ImageDraw.Draw(the).rounded_rectangle((44, 0, 916, 8), radius=4, fill=tuple(C.VANG) + (255,))
        sh, p = C.bong_do(the, blur=26, alpha=0.6)
        t2 = Image.new("RGBA", (the.width + 2 * p, the.height + 2 * p), (0, 0, 0, 0))
        t2.alpha_composite(sh, (0, 12))
        t2.alpha_composite(the, (p, p))
        self.the, self.p_the = np.asarray(t2), p
        self.t_bam = float(it.get("t_bam", self.t0 + 4.0)) - self.t0

    def rect(self):
        return (60, self.y_av, W - 60, self.y_av + self.the.shape[0] - 2 * self.p_the)

    def ve(self, frame, t):
        if t < self.t0 - 0.02 or t > self.t1:
            return None
        tl = t - self.t0
        a = ease_out(ramp(tl, 0.0, 0.35))
        dy = 70 * (1 - a)
        C.dan(frame, self.the, (W - self.the.shape[1]) / 2, self.y_av - self.p_the + dy, a)
        u = ramp(tl, 0.12, 0.4)
        if u > 0:
            DN.ve_song(frame, W / 2, self.y_av + dy, tl - 0.6, C.VANG, r0=92, r1=140, chu_ky=1.6, so_vong=2, day=3, alpha=0.7)
            C.dan_giua(frame, self.av, W / 2, self.y_av + dy, clamp(u * 3), max(0.05, DN.back_out(u)))
        v = ease_out(ramp(tl, 0.25, 0.3))
        C.dan_giua(frame, self.nhan, W / 2, self.y_nhan + dy + 16 * (1 - v), v)
        if self.y_ten is not None:
            v = ease_out(ramp(tl, 0.35, 0.3))
            C.dan_giua(frame, self.ten, W / 2, self.y_ten + dy + 16 * (1 - v), v)
        # số điện thoại: nhóm hiện 4-3-3 sát nhau, từng chữ số bật đúng lúc đọc
        o = [self.so_o[ch] for ch in self.so]
        tong = self.ic_dt.shape[1] + 22 + sum(o) - SDT_TRACK + SDT_GAP * (len(self.nhom_hien) - 1)
        x = (W - tong) / 2
        t_dau = next((x_ for x_ in self.t_so if x_ is not None), self.t0 + 0.5) - self.t0
        vi = ease_out(ramp(tl, t_dau - 0.1, 0.3))
        if vi > 0:
            C.dan_giua(frame, self.ic_dt, x + self.ic_dt.shape[1] / 2, self.y_sdt + dy, vi, max(0.05, DN.back_out(vi)))
        x += self.ic_dt.shape[1] + 22
        i = 0
        for g, n in enumerate(self.nhom_hien):
            if g:
                x += SDT_GAP
            for _ in range(n):
                ch = self.so[i]
                tk = (self.t_so[i] - self.t0) if self.t_so[i] is not None else 0.5 + 0.12 * i
                v = ramp(tl, tk, 0.18)
                if v > 0:
                    w_ = o[i] - SDT_TRACK
                    C.dan_giua(frame, self.so_anh[ch], x + w_ / 2, self.y_sdt + dy, clamp(v * 2), max(0.05, DN.back_out(v)))
                x += o[i]
                i += 1
        # nút GỌI NGAY: hiện sau số đầu, ống nghe rung, tay bấm ở t_bam
        vn = ramp(tl, t_dau + 0.2, 0.35)
        if vn > 0:
            cy = self.y_nut + dy
            nhan_ = 1.0
            if self.t_bam <= tl < self.t_bam + 0.2:
                nhan_ = 1 - 0.06 * math.sin(math.pi * (tl - self.t_bam) / 0.2)
            s = max(0.05, DN.back_out(vn)) * nhan_
            nhip = 0.5 + 0.5 * math.sin(2 * math.pi * tl / 0.9)
            C.dan_giua(frame, self.glow, W / 2, cy, clamp(vn) * (0.35 + 0.35 * nhip))
            C.dan_giua(frame, self.nut, W / 2, cy, clamp(vn * 3), s)
            goc = 16 * math.sin(2 * math.pi * tl / 0.18) * (0.5 + 0.5 * math.sin(2 * math.pi * tl / 1.6) > 0.55)
            g = self.gl.rotate(goc, resample=Image.BICUBIC) if goc else self.gl
            xc = W / 2 + (self.x_ic - self.nut.width / 2) * s
            C.dan_giua(frame, g, xc, cy, clamp(vn * 3), s)
            if self.t_bam <= tl < self.t_bam + 0.7:
                DN.ve_song(frame, W / 2 + 120, cy + 34, tl - self.t_bam, C.TRANG, r0=18, r1=150, chu_ky=0.7, so_vong=1,
                           day=5, lap=False)
            if self.t_bam - 0.45 <= tl <= self.t_bam + 0.9:
                dx, dy_t = W / 2 + 120, cy + 34
                if tl < self.t_bam - 0.05:
                    k = ease_out((tl - self.t_bam + 0.45) / 0.4)
                    ox, oy, at = 300 * (1 - k), 440 * (1 - k), clamp((tl - self.t_bam + 0.45) / 0.15)
                elif tl < self.t_bam + 0.45:
                    ox, oy, at = 0.0, 0.0, 1.0
                else:
                    k = smooth((tl - self.t_bam - 0.45) / 0.4)
                    ox, oy, at = 170 * k, 280 * k, 1 - k
                sc = 1.0
                if self.t_bam - 0.05 <= tl < self.t_bam + 0.2:
                    sc = 1 - 0.08 * math.sin(math.pi * (tl - self.t_bam + 0.05) / 0.25)
                C.dan_giua(frame, self.tay, dx + ox, dy_t + oy, at, sc)
        if self.y_cuoi is not None:
            tc = float(self.it.get("dong_cuoi_tu", self.t0 + 1.0)) - self.t0
            v = ease_out(ramp(tl, tc, 0.35))
            C.dan_giua(frame, self.dong_cuoi, W / 2, self.y_cuoi + dy + 14 * (1 - v), v)
        return self.rect()

    def sfx(self):
        return []


# thẻ CTA FOLLOW (kịch bản không đọc SĐT) — module riêng, đưa vào đây để dung.LOAI_THE tìm thấy
from cta_follow import TheTheoDoi  # noqa: E402,F401
