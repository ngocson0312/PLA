# -*- coding: utf-8 -*-
"""Biểu tượng tiện ích vẽ vector bằng PIL (siêu lấy mẫu 4×, không tải ảnh ngoài) + bảng NHÓM tiện ích
(tên tiếng Việt, màu, biểu tượng, thẻ OSM để quét) + ghim tiện ích / ghim nhà / nhãn tên tiện ích.

    ICON[ten](size, mau=(255,255,255)) → ảnh RGBA vuông size×size
    ghim(nhom, co)      → sprite ghim tròn màu nhóm có biểu tượng trắng, đuôi nhọn chỉ xuống (mũi ở đáy)
    ghim_nha(co)        → ghim vàng to có hình ngôi nhà (lô đất)
    nhan_tien_ich(ten, phu, mau) → pill navy 2 dòng: tên trắng + dòng phụ màu nhóm (khoảng cách / thời gian)
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chung as C

SS = 4
_cache = {}


def _o(size):
    S = size * SS
    return Image.new("RGBA", (S, S), (0, 0, 0, 0)), S


def _thu(im, size):
    return im.resize((size, size), Image.LANCZOS)


def _c(mau):
    return tuple(int(v) for v in mau[:3]) + (255,)


# ---------------------------------------------------------------- các biểu tượng (glyph 1 màu)

def i_nha(size, mau=C.TRANG):
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.polygon([(0.50 * S, 0.10 * S), (0.92 * S, 0.48 * S), (0.08 * S, 0.48 * S)], fill=c)
    d.rectangle((0.20 * S, 0.44 * S, 0.80 * S, 0.88 * S), fill=c)
    d.rectangle((0.66 * S, 0.16 * S, 0.76 * S, 0.36 * S), fill=c)
    d.rounded_rectangle((0.42 * S, 0.60 * S, 0.58 * S, 0.88 * S), radius=0.03 * S, fill=(0, 0, 0, 0))
    return _thu(im, size)


def i_khach_san(size, mau=C.TRANG):
    """giường: đầu giường + nệm + gối"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rounded_rectangle((0.10 * S, 0.22 * S, 0.20 * S, 0.84 * S), radius=0.03 * S, fill=c)
    d.rounded_rectangle((0.10 * S, 0.56 * S, 0.92 * S, 0.70 * S), radius=0.03 * S, fill=c)
    d.rounded_rectangle((0.80 * S, 0.56 * S, 0.90 * S, 0.84 * S), radius=0.03 * S, fill=c)
    d.ellipse((0.23 * S, 0.38 * S, 0.43 * S, 0.54 * S), fill=c)
    d.rounded_rectangle((0.46 * S, 0.40 * S, 0.92 * S, 0.56 * S), radius=0.06 * S, fill=c)
    return _thu(im, size)


def i_di_tich(size, mau=C.TRANG):
    """mái đình/chùa 2 tầng cong + cột"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.polygon([(0.06 * S, 0.34 * S), (0.30 * S, 0.22 * S), (0.70 * S, 0.22 * S), (0.94 * S, 0.34 * S),
               (0.82 * S, 0.36 * S), (0.18 * S, 0.36 * S)], fill=c)
    d.polygon([(0.30 * S, 0.22 * S), (0.42 * S, 0.10 * S), (0.58 * S, 0.10 * S), (0.70 * S, 0.22 * S)], fill=c)
    d.polygon([(0.04 * S, 0.60 * S), (0.24 * S, 0.48 * S), (0.76 * S, 0.48 * S), (0.96 * S, 0.60 * S),
               (0.84 * S, 0.62 * S), (0.16 * S, 0.62 * S)], fill=c)
    d.rectangle((0.24 * S, 0.36 * S, 0.76 * S, 0.48 * S), fill=c)
    for x in (0.20, 0.40, 0.56, 0.76):
        d.rectangle((x * S, 0.62 * S, (x + 0.06) * S, 0.88 * S), fill=c)
    d.rectangle((0.12 * S, 0.86 * S, 0.88 * S, 0.92 * S), fill=c)
    return _thu(im, size)


def i_cong_vien(size, mau=C.TRANG):
    """cây: tán 3 vòng + thân"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.ellipse((0.28 * S, 0.06 * S, 0.72 * S, 0.48 * S), fill=c)
    d.ellipse((0.12 * S, 0.28 * S, 0.52 * S, 0.66 * S), fill=c)
    d.ellipse((0.48 * S, 0.28 * S, 0.88 * S, 0.66 * S), fill=c)
    d.rectangle((0.45 * S, 0.55 * S, 0.55 * S, 0.92 * S), fill=c)
    d.rectangle((0.30 * S, 0.88 * S, 0.70 * S, 0.94 * S), fill=c)
    return _thu(im, size)


def i_ho(size, mau=C.TRANG):
    """mặt nước: 3 làn sóng"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    wd = int(0.09 * S)
    for k, y in enumerate((0.30, 0.52, 0.74)):
        pts = [(x * S, (y + 0.07 * math.sin(x * 2 * math.pi * 1.6 + k)) * S) for x in np.linspace(0.08, 0.92, 40)]
        d.line(pts, fill=c, width=wd, joint="curve")
        for p in (pts[0], pts[-1]):
            d.ellipse((p[0] - wd / 2, p[1] - wd / 2, p[0] + wd / 2, p[1] + wd / 2), fill=c)
    return _thu(im, size)


def i_view(size, mau=C.TRANG):
    """con mắt (view ngắm)"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    top = [(x * S, (0.5 - 0.30 * math.sin(math.pi * (x - 0.06) / 0.88)) * S) for x in np.linspace(0.06, 0.94, 40)]
    bot = [(x * S, (0.5 + 0.30 * math.sin(math.pi * (x - 0.06) / 0.88)) * S) for x in np.linspace(0.94, 0.06, 40)]
    d.polygon(top + bot, fill=c)
    d.ellipse((0.34 * S, 0.34 * S, 0.66 * S, 0.66 * S), fill=(0, 0, 0, 0))
    d.ellipse((0.42 * S, 0.42 * S, 0.58 * S, 0.58 * S), fill=c)
    return _thu(im, size)


def i_truong(size, mau=C.TRANG):
    """mũ tốt nghiệp"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.polygon([(0.50 * S, 0.16 * S), (0.96 * S, 0.38 * S), (0.50 * S, 0.60 * S), (0.04 * S, 0.38 * S)], fill=c)
    d.polygon([(0.24 * S, 0.50 * S), (0.76 * S, 0.50 * S), (0.76 * S, 0.74 * S), (0.50 * S, 0.84 * S),
               (0.24 * S, 0.74 * S)], fill=c)
    d.line([(0.84 * S, 0.42 * S), (0.84 * S, 0.74 * S)], fill=c, width=int(0.05 * S))
    d.ellipse((0.79 * S, 0.72 * S, 0.89 * S, 0.84 * S), fill=c)
    return _thu(im, size)


def i_benh_vien(size, mau=C.TRANG):
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rounded_rectangle((0.38 * S, 0.10 * S, 0.62 * S, 0.90 * S), radius=0.04 * S, fill=c)
    d.rounded_rectangle((0.10 * S, 0.38 * S, 0.90 * S, 0.62 * S), radius=0.04 * S, fill=c)
    return _thu(im, size)


def i_mua_sam(size, mau=C.TRANG):
    """túi mua sắm"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rounded_rectangle((0.14 * S, 0.34 * S, 0.86 * S, 0.92 * S), radius=0.06 * S, fill=c)
    d.arc((0.30 * S, 0.08 * S, 0.70 * S, 0.56 * S), 180, 360, fill=c, width=int(0.08 * S))
    d.ellipse((0.30 * S, 0.44 * S, 0.38 * S, 0.52 * S), fill=(0, 0, 0, 0))
    d.ellipse((0.62 * S, 0.44 * S, 0.70 * S, 0.52 * S), fill=(0, 0, 0, 0))
    return _thu(im, size)


def i_metro(size, mau=C.TRANG):
    """đầu tàu metro: thân bo + 2 cửa kính + 2 đèn + ray"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rounded_rectangle((0.20 * S, 0.06 * S, 0.80 * S, 0.76 * S), radius=0.14 * S, fill=c)
    d.rounded_rectangle((0.28 * S, 0.16 * S, 0.72 * S, 0.42 * S), radius=0.04 * S, fill=(0, 0, 0, 0))
    d.ellipse((0.28 * S, 0.54 * S, 0.38 * S, 0.64 * S), fill=(0, 0, 0, 0))
    d.ellipse((0.62 * S, 0.54 * S, 0.72 * S, 0.64 * S), fill=(0, 0, 0, 0))
    wd = int(0.07 * S)
    d.line([(0.32 * S, 0.76 * S), (0.18 * S, 0.94 * S)], fill=c, width=wd)
    d.line([(0.68 * S, 0.76 * S), (0.82 * S, 0.94 * S)], fill=c, width=wd)
    d.line([(0.25 * S, 0.86 * S), (0.75 * S, 0.86 * S)], fill=c, width=int(0.05 * S))
    return _thu(im, size)


def i_xe_buyt(size, mau=C.TRANG):
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rounded_rectangle((0.14 * S, 0.08 * S, 0.86 * S, 0.80 * S), radius=0.10 * S, fill=c)
    d.rectangle((0.22 * S, 0.20 * S, 0.78 * S, 0.46 * S), fill=(0, 0, 0, 0))
    d.ellipse((0.22 * S, 0.58 * S, 0.34 * S, 0.70 * S), fill=(0, 0, 0, 0))
    d.ellipse((0.66 * S, 0.58 * S, 0.78 * S, 0.70 * S), fill=(0, 0, 0, 0))
    d.rounded_rectangle((0.20 * S, 0.78 * S, 0.34 * S, 0.94 * S), radius=0.03 * S, fill=c)
    d.rounded_rectangle((0.66 * S, 0.78 * S, 0.80 * S, 0.94 * S), radius=0.03 * S, fill=c)
    return _thu(im, size)


def i_san_bay(size, mau=C.TRANG):
    """máy bay nhìn từ trên, mũi hướng lên phải"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    body = [(0.50, 0.04), (0.56, 0.12), (0.56, 0.40), (0.94, 0.60), (0.94, 0.68), (0.56, 0.56), (0.56, 0.80),
            (0.68, 0.90), (0.68, 0.96), (0.50, 0.91), (0.32, 0.96), (0.32, 0.90), (0.44, 0.80), (0.44, 0.56),
            (0.06, 0.68), (0.06, 0.60), (0.44, 0.40), (0.44, 0.12)]
    pts = []
    for x, y in body:
        x0, y0 = x - 0.5, y - 0.5
        a = math.radians(40)
        pts.append(((0.5 + x0 * math.cos(a) - y0 * math.sin(a)) * S, (0.5 + x0 * math.sin(a) + y0 * math.cos(a)) * S))
    d.polygon(pts, fill=c)
    return _thu(im, size)


def i_dai_su_quan(size, mau=C.TRANG):
    """cờ"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rectangle((0.18 * S, 0.08 * S, 0.26 * S, 0.94 * S), fill=c)
    pts = [(0.26 * S, 0.10 * S)]
    pts += [(x * S, (0.12 + 0.05 * math.sin((x - 0.26) * 9)) * S) for x in np.linspace(0.26, 0.86, 20)]
    pts += [(x * S, (0.52 + 0.05 * math.sin((x - 0.26) * 9)) * S) for x in np.linspace(0.86, 0.26, 20)]
    d.polygon(pts, fill=c)
    return _thu(im, size)


def i_the_thao(size, mau=C.TRANG):
    """tạ đôi"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rectangle((0.20 * S, 0.45 * S, 0.80 * S, 0.55 * S), fill=c)
    for x0, x1, h in ((0.08, 0.18, 0.22), (0.20, 0.30, 0.32), (0.70, 0.80, 0.32), (0.82, 0.92, 0.22)):
        d.rounded_rectangle((x0 * S, (0.5 - h) * S, x1 * S, (0.5 + h) * S), radius=0.03 * S, fill=c)
    return _thu(im, size)


def i_ngan_hang(size, mau=C.TRANG):
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.polygon([(0.50 * S, 0.06 * S), (0.94 * S, 0.30 * S), (0.06 * S, 0.30 * S)], fill=c)
    for x in (0.16, 0.36, 0.56, 0.76):
        d.rectangle((x * S, 0.36 * S, (x + 0.09) * S, 0.80 * S), fill=c)
    d.rectangle((0.08 * S, 0.84 * S, 0.92 * S, 0.94 * S), fill=c)
    return _thu(im, size)


def i_ca_phe(size, mau=C.TRANG):
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rounded_rectangle((0.12 * S, 0.40 * S, 0.70 * S, 0.88 * S), radius=0.10 * S, fill=c)
    d.ellipse((0.58 * S, 0.48 * S, 0.90 * S, 0.76 * S), outline=c, width=int(0.07 * S))
    for x in (0.26, 0.42, 0.58):
        d.arc((x * S, 0.08 * S, (x + 0.10) * S, 0.34 * S), 90, 270, fill=c, width=int(0.05 * S))
    return _thu(im, size)


def i_toa_nha(size, mau=C.TRANG):
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rectangle((0.20 * S, 0.08 * S, 0.80 * S, 0.94 * S), fill=c)
    for r in range(4):
        for k in range(3):
            x, y = 0.28 + k * 0.17, 0.16 + r * 0.17
            d.rectangle((x * S, y * S, (x + 0.10) * S, (y + 0.10) * S), fill=(0, 0, 0, 0))
    return _thu(im, size)


def i_duong(size, mau=C.TRANG):
    """con đường thu về chân trời + vạch giữa"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.polygon([(0.36 * S, 0.06 * S), (0.64 * S, 0.06 * S), (0.96 * S, 0.94 * S), (0.04 * S, 0.94 * S)], fill=c)
    for y0, y1 in ((0.14, 0.28), (0.40, 0.56), (0.70, 0.90)):
        w0, w1 = 0.02 + 0.02 * y0, 0.02 + 0.02 * y1
        d.polygon([((0.5 - w0) * S, y0 * S), ((0.5 + w0) * S, y0 * S), ((0.5 + w1) * S, y1 * S),
                   ((0.5 - w1) * S, y1 * S)], fill=(0, 0, 0, 0))
    return _thu(im, size)


def i_o_to(size, mau=C.TRANG):
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.polygon([(0.22 * S, 0.30 * S), (0.78 * S, 0.30 * S), (0.88 * S, 0.50 * S), (0.12 * S, 0.50 * S)], fill=c)
    d.rounded_rectangle((0.06 * S, 0.46 * S, 0.94 * S, 0.74 * S), radius=0.07 * S, fill=c)
    d.polygon([(0.28 * S, 0.36 * S), (0.72 * S, 0.36 * S), (0.78 * S, 0.47 * S), (0.22 * S, 0.47 * S)], fill=(0, 0, 0, 0))
    d.ellipse((0.16 * S, 0.66 * S, 0.34 * S, 0.84 * S), fill=c)
    d.ellipse((0.66 * S, 0.66 * S, 0.84 * S, 0.84 * S), fill=c)
    return _thu(im, size)


def i_di_bo(size, mau=C.TRANG):
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    wd = int(0.10 * S)
    d.ellipse((0.44 * S, 0.04 * S, 0.62 * S, 0.22 * S), fill=c)
    d.line([(0.52 * S, 0.28 * S), (0.46 * S, 0.58 * S)], fill=c, width=wd, joint="curve")
    d.line([(0.46 * S, 0.58 * S), (0.30 * S, 0.92 * S)], fill=c, width=wd)
    d.line([(0.46 * S, 0.58 * S), (0.64 * S, 0.74 * S), (0.66 * S, 0.94 * S)], fill=c, width=wd, joint="curve")
    d.line([(0.26 * S, 0.46 * S), (0.36 * S, 0.34 * S), (0.52 * S, 0.30 * S), (0.66 * S, 0.44 * S), (0.76 * S, 0.50 * S)],
           fill=c, width=int(0.08 * S), joint="curve")
    return _thu(im, size)


def i_dien_tich(size, mau=C.TRANG):
    """ô vuông có 4 góc mũi tên (diện tích)"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    wd = int(0.08 * S)
    d.rectangle((0.24 * S, 0.24 * S, 0.76 * S, 0.76 * S), outline=c, width=wd)
    for sx, sy in ((0.06, 0.06), (0.94, 0.06), (0.06, 0.94), (0.94, 0.94)):
        dx = 1 if sx < 0.5 else -1
        dy = 1 if sy < 0.5 else -1
        d.polygon([(sx * S, sy * S), ((sx + dx * 0.20) * S, sy * S), (sx * S, (sy + dy * 0.20) * S)], fill=c)
    return _thu(im, size)


def i_mat_tien(size, mau=C.TRANG):
    """mũi tên 2 đầu ↔ trên vạch"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rectangle((0.16 * S, 0.44 * S, 0.84 * S, 0.56 * S), fill=c)
    d.polygon([(0.04 * S, 0.50 * S), (0.26 * S, 0.30 * S), (0.26 * S, 0.70 * S)], fill=c)
    d.polygon([(0.96 * S, 0.50 * S), (0.74 * S, 0.30 * S), (0.74 * S, 0.70 * S)], fill=c)
    d.rectangle((0.04 * S, 0.76 * S, 0.96 * S, 0.84 * S), fill=c)
    return _thu(im, size)


def i_so_do(size, mau=C.TRANG):
    """giấy tờ có dấu tích (pháp lý / sổ đỏ)"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.rounded_rectangle((0.16 * S, 0.06 * S, 0.84 * S, 0.94 * S), radius=0.06 * S, fill=c)
    for y in (0.20, 0.32, 0.44):
        d.rectangle((0.28 * S, y * S, 0.72 * S, (y + 0.05) * S), fill=(0, 0, 0, 0))
    pts = [(0.30 * S, 0.68 * S), (0.44 * S, 0.80 * S), (0.70 * S, 0.56 * S)]
    d.line(pts, fill=(0, 0, 0, 0), width=int(0.08 * S), joint="curve")
    return _thu(im, size)


def i_gia(size, mau=C.TRANG):
    """thẻ giá (tag)"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.polygon([(0.10 * S, 0.44 * S), (0.44 * S, 0.10 * S), (0.90 * S, 0.10 * S), (0.90 * S, 0.56 * S), (0.56 * S, 0.90 * S)],
              fill=c)
    d.ellipse((0.66 * S, 0.22 * S, 0.80 * S, 0.36 * S), fill=(0, 0, 0, 0))
    return _thu(im, size)


def i_dien_thoai(size, mau=C.TRANG):
    """ống nghe điện thoại"""
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    # đường viền theo icon "call" của Material Icons (Apache 2.0), hệ 24×24, lấy mẫu các đoạn Bézier
    P0 = (6.62, 10.79)
    doan = [("C", (8.06, 13.62), (10.38, 15.93), (13.21, 17.38)), ("L", (15.41, 15.18)),
            ("C", (15.68, 14.91), (16.08, 14.82), (16.43, 14.94)), ("C", (17.55, 15.31), (18.76, 15.51), (20.0, 15.51)),
            ("C", (20.55, 15.51), (21.0, 15.96), (21.0, 16.51)), ("L", (21.0, 20.0)),
            ("C", (21.0, 20.55), (20.55, 21.0), (20.0, 21.0)), ("C", (10.61, 21.0), (3.0, 13.39), (3.0, 4.0)),
            ("C", (3.0, 3.45), (3.45, 3.0), (4.0, 3.0)), ("L", (7.5, 3.0)),
            ("C", (8.05, 3.0), (8.5, 3.45), (8.5, 4.0)), ("C", (8.5, 5.25), (8.7, 6.45), (9.07, 7.57)),
            ("C", (9.18, 7.92), (9.10, 8.31), (8.82, 8.59)), ("L", P0)]
    pts, cur = [P0], P0
    for seg in doan:
        if seg[0] == "L":
            cur = seg[1]
            pts.append(cur)
            continue
        a, b, e = seg[1], seg[2], seg[3]
        for u in np.linspace(0, 1, 14)[1:]:
            v = 1 - u
            pts.append((v ** 3 * cur[0] + 3 * v * v * u * a[0] + 3 * v * u * u * b[0] + u ** 3 * e[0],
                        v ** 3 * cur[1] + 3 * v * v * u * a[1] + 3 * v * u * u * b[1] + u ** 3 * e[1]))
        cur = e
    k = S / 24.0
    d.polygon([((x - 12) * k * 1.08 + S / 2, (y - 12) * k * 1.08 + S / 2) for x, y in pts], fill=_c(mau))
    return _thu(im, size)


def i_nguoi(size, mau=C.TRANG):
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    d.ellipse((0.30 * S, 0.06 * S, 0.70 * S, 0.46 * S), fill=c)
    d.pieslice((0.10 * S, 0.52 * S, 0.90 * S, 1.30 * S), 180, 360, fill=c)
    return _thu(im, size)


def i_vi_tri(size, mau=C.TRANG):
    im, S = _o(size)
    d = ImageDraw.Draw(im)
    c = _c(mau)
    cx, cy, r = 0.5 * S, 0.38 * S, 0.30 * S
    d.polygon([(cx - r * 0.86, cy + r * 0.5), (cx + r * 0.86, cy + r * 0.5), (cx, 0.96 * S)], fill=c)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
    d.ellipse((cx - r * 0.42, cy - r * 0.42, cx + r * 0.42, cy + r * 0.42), fill=(0, 0, 0, 0))
    return _thu(im, size)


ICON = {"nha": i_nha, "khach_san": i_khach_san, "di_tich": i_di_tich, "cong_vien": i_cong_vien, "ho": i_ho,
        "view": i_view, "truong": i_truong, "benh_vien": i_benh_vien, "mua_sam": i_mua_sam, "metro": i_metro,
        "xe_buyt": i_xe_buyt, "san_bay": i_san_bay, "dai_su_quan": i_dai_su_quan, "the_thao": i_the_thao,
        "ngan_hang": i_ngan_hang, "ca_phe": i_ca_phe, "toa_nha": i_toa_nha, "duong": i_duong, "o_to": i_o_to,
        "di_bo": i_di_bo, "dien_tich": i_dien_tich, "mat_tien": i_mat_tien, "so_do": i_so_do, "gia": i_gia,
        "dien_thoai": i_dien_thoai, "nguoi": i_nguoi, "vi_tri": i_vi_tri}


def icon(ten, size, mau=C.TRANG):
    k = ("ic", ten, int(size), tuple(mau))
    if k not in _cache:
        f = ICON.get(ten) or ICON["vi_tri"]
        _cache[k] = f(int(size), mau)
    return _cache[k]


# ---------------------------------------------------------------- nhóm tiện ích

# osm = thẻ lọc Photon reverse (key:value hoặc key) — dùng ở tien_ich.py; mac_dinh = quét khi không chỉ định nhóm
NHOM = {
    "khach_san":   {"ten": "Khách sạn", "icon": "khach_san", "mau": (150, 108, 255), "mac_dinh": True,
                    "osm": ["tourism:hotel"]},
    "di_tich":     {"ten": "Đền · chùa · di tích", "icon": "di_tich", "mau": (236, 86, 56), "mac_dinh": True,
                    "osm": ["amenity:place_of_worship", "historic", "tourism:attraction"]},
    "cong_vien":   {"ten": "Công viên", "icon": "cong_vien", "mau": (64, 186, 88), "mac_dinh": True,
                    "osm": ["leisure:park", "leisure:garden"]},
    "ho":          {"ten": "Hồ · mặt nước", "icon": "ho", "mau": (52, 168, 238), "mac_dinh": True,
                    "osm": ["natural:water", "water:lake"]},
    "truong":      {"ten": "Trường học", "icon": "truong", "mau": (246, 184, 34), "mac_dinh": True,
                    "osm": ["amenity:school", "amenity:university", "amenity:college", "amenity:kindergarten"]},
    "benh_vien":   {"ten": "Bệnh viện · phòng khám", "icon": "benh_vien", "mau": (232, 56, 68), "mac_dinh": True,
                    "osm": ["amenity:hospital", "amenity:clinic"]},
    "mua_sam":     {"ten": "Mua sắm", "icon": "mua_sam", "mau": (238, 96, 168), "mac_dinh": True,
                    "osm": ["shop:mall", "shop:supermarket", "shop:department_store", "amenity:marketplace"]},
    "metro":       {"ten": "Ga metro · đường sắt", "icon": "metro", "mau": (36, 106, 228), "mac_dinh": True,
                    "osm": ["railway:station", "railway:halt", "public_transport:station"]},
    "dai_su_quan": {"ten": "Đại sứ quán", "icon": "dai_su_quan", "mau": (70, 90, 170), "mac_dinh": True,
                    "osm": ["amenity:embassy", "office:diplomatic"]},
    "the_thao":    {"ten": "Thể thao", "icon": "the_thao", "mau": (0, 176, 166), "mac_dinh": True,
                    "osm": ["leisure:sports_centre", "leisure:fitness_centre", "leisure:golf_course",
                            "leisure:swimming_pool", "leisure:stadium"]},
    "xe_buyt":     {"ten": "Xe buýt", "icon": "xe_buyt", "mau": (84, 146, 236), "mac_dinh": False,
                    "osm": ["highway:bus_stop"]},
    "ngan_hang":   {"ten": "Ngân hàng", "icon": "ngan_hang", "mau": (118, 128, 150), "mac_dinh": False,
                    "osm": ["amenity:bank"]},
    "ca_phe":      {"ten": "Cà phê · nhà hàng", "icon": "ca_phe", "mau": (176, 112, 64), "mac_dinh": False,
                    "osm": ["amenity:cafe", "amenity:restaurant"]},
    "hanh_chinh":  {"ten": "Cơ quan", "icon": "toa_nha", "mau": (100, 112, 134), "mac_dinh": False,
                    "osm": ["amenity:townhall", "office:government"]},
    "san_bay":     {"ten": "Sân bay", "icon": "san_bay", "mau": (36, 106, 228), "mac_dinh": False,
                    "osm": ["aeroway:aerodrome"]},
    # nhóm không quét (đặt tay qua dia_diem): đường, phố cổ, trung tâm…
    "duong":       {"ten": "Đường", "icon": "duong", "mau": (255, 196, 64), "mac_dinh": False, "osm": []},
    "trung_tam":   {"ten": "Trung tâm", "icon": "toa_nha", "mau": (255, 140, 60), "mac_dinh": False, "osm": []},
    "view":        {"ten": "View", "icon": "view", "mau": (52, 168, 238), "mac_dinh": False, "osm": []},
}


def nhom(k):
    return NHOM.get(k) or NHOM["trung_tam"]


# ---------------------------------------------------------------- ghim + nhãn

def ghim(nhom_key, co=1.0, mau=None, ten_icon=None):
    """ghim tròn: vòng trắng + nền màu nhóm + biểu tượng trắng, đuôi nhọn; mũi ở giữa đáy ảnh.
    → (ảnh RGBA PIL, mảng, mũi_x, mũi_y)"""
    g = nhom(nhom_key)
    mau = tuple(mau or g["mau"])
    ten_icon = ten_icon or g["icon"]
    k = ("ghim", nhom_key, round(co, 2), mau, ten_icon)
    if k in _cache:
        return _cache[k]
    D = int(64 * co)
    S = SS
    w, h = D + 24, int(D * 1.42) + 20
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, r = w * S / 2, (D / 2 + 6) * S, D / 2 * S
    tip = (cx, (h - 6) * S)
    d.polygon([(cx - r * 0.62, cy + r * 0.62), (cx + r * 0.62, cy + r * 0.62), tip], fill=(255, 255, 255, 255))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 255))
    r2 = r - 4.5 * S * co
    d.polygon([(cx - r2 * 0.55, cy + r2 * 0.70), (cx + r2 * 0.55, cy + r2 * 0.70), (cx, tip[1] - 7 * S * co)],
              fill=mau + (255,))
    d.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=mau + (255,))
    # bóng sáng nhẹ nửa trên
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse((cx - r2 * 0.86, cy - r2 * 0.92, cx + r2 * 0.86, cy + r2 * 0.10), fill=(255, 255, 255, 40))
    im.alpha_composite(hl)
    im = im.resize((w, h), Image.LANCZOS)
    gl = icon(ten_icon, int(D * 0.56), C.TRANG)
    im.alpha_composite(gl, (int(w / 2 - gl.width / 2), int(D / 2 + 6 - gl.height / 2)))
    sh, p = C.bong_do(im, blur=7, alpha=0.6)
    out = Image.new("RGBA", (w + 2 * p, h + 2 * p), (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 5))
    out.alpha_composite(im, (p, p))
    res = (out, np.asarray(out), p + w / 2, p + h - 6)
    _cache[k] = res
    return res


def ghim_nha(co=1.0):
    """ghim vàng to có ngôi nhà (lô đất) — viền navy"""
    return ghim("nha_", co, mau=C.VANG, ten_icon="nha")


def nhan_tien_ich(ten, phu=None, mau=C.VANG, co=26, icon_phu=None):
    """pill navy bo tròn: tên trắng IN HOA (+ dòng phụ màu nhóm, có biểu tượng nhỏ đi bộ / ô tô). → (PIL, mảng, w, h)"""
    k = ("nti", ten, phu, tuple(mau), co, icon_phu)
    if k in _cache:
        return _cache[k]
    parts = [C.chu(ten.upper(), "xbold", co, fill=C.TRANG, track=1)]
    if phu:
        tp = C.chu(phu, "bold", int(co * 0.80), fill=tuple(mau))
        if icon_phu:
            ic = icon(icon_phu, int(co * 0.86), tuple(mau))
            row = Image.new("RGBA", (ic.width + 8 + tp.width, max(ic.height, tp.height)), (0, 0, 0, 0))
            row.alpha_composite(ic, (0, (row.height - ic.height) // 2))
            row.alpha_composite(tp, (ic.width + 8, (row.height - tp.height) // 2))
            tp = row
        parts.append(tp)
    txt = C.xep_doc(parts, gap=3, align="left")
    w, h = txt.width + 44, txt.height + 22
    box = C.hop_bo((w, h), min(22, h // 2), tuple(C.NAVY) + (238,), vien=tuple(C.NAVY_VIEN) + (255,), vien_w=2)
    ImageDraw.Draw(box).rounded_rectangle((0, 0, 9, h - 1), radius=5, fill=tuple(mau) + (255,))
    box.alpha_composite(txt, (26, 11))
    sh, p = C.bong_do(box, blur=9, alpha=0.5)
    out = Image.new("RGBA", (w + 2 * p, h + 2 * p), (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 4))
    out.alpha_composite(box, (p, p))
    res = (out, np.asarray(out), w, h, p)
    _cache[k] = res
    return res


def chip(nhom_key, co=24):
    """chip chú giải: chấm tròn màu nhóm có biểu tượng + tên nhóm (dùng ở cảnh tổng quan)"""
    g = nhom(nhom_key)
    k = ("chip", nhom_key, co)
    if k in _cache:
        return _cache[k]
    D = int(co * 1.5)
    t = C.chu(g["ten"], "bold", co, fill=C.TRANG)
    w, h = D + 12 + t.width + 26, D + 14
    box = C.hop_bo((w, h), h // 2, tuple(C.NAVY) + (225,), vien=tuple(C.NAVY_VIEN) + (255,), vien_w=2)
    d = ImageDraw.Draw(box)
    d.ellipse((7, 7, 7 + D, 7 + D), fill=tuple(g["mau"]) + (255,))
    gl = icon(g["icon"], int(D * 0.62), C.TRANG)
    box.alpha_composite(gl, (7 + (D - gl.width) // 2, 7 + (D - gl.height) // 2))
    box.alpha_composite(t, (7 + D + 12, (h - t.height) // 2))
    _cache[k] = (box, np.asarray(box), w, h)
    return _cache[k]


def to_mau(out_path):
    """tờ thử mọi biểu tượng + ghim (soát bằng mắt)"""
    keys = list(ICON)
    cols = 7
    rows = (len(keys) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 150, rows * 150 + 260), (40, 60, 80, 255))
    d = ImageDraw.Draw(sheet)
    for i, k in enumerate(keys):
        x, y = (i % cols) * 150, (i // cols) * 150
        d.rounded_rectangle((x + 20, y + 10, x + 130, y + 120), radius=20, fill=(20, 40, 70, 255))
        sheet.alpha_composite(icon(k, 80), (x + 35, y + 25))
        d.text((x + 10, y + 124), k, font=C.font("semi", 16), fill=(255, 255, 255))
    x = 10
    for k in list(NHOM)[:12]:
        im = ghim(k)[0]
        sheet.alpha_composite(im, (x, rows * 150 + 20))
        x += im.width - 10
    sheet.alpha_composite(ghim_nha(1.4)[0], (x + 10, rows * 150 + 10))
    sheet.alpha_composite(nhan_tien_ich("Phủ Tây Hồ", "≈ 1,2 km · 4 phút", (236, 86, 56), icon_phu="o_to")[0],
                          (20, rows * 150 + 150))
    sheet.convert("RGB").save(out_path, quality=92)


if __name__ == "__main__":
    import sys
    to_mau(sys.argv[1] if len(sys.argv) > 1 else "bieu_tuong_mau.jpg")
