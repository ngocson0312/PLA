# -*- coding: utf-8 -*-
"""Liệt kê SFX sẽ trộn (giây · file · mức) mà KHÔNG dựng hình — soi trước khi dựng.
python -I -X utf8 .claude\\skills\\ban-do-tien-ich-nha-dat\\scripts\\ds_sfx.py --work <thư mục work>"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import am_thanh as A  # noqa: E402


def _in(voice, ev):
    for e in ev:
        print("%6.2f  %-20s %s" % (e["t"], e["file"], e.get("muc", "")))
    print("tổng %d tiếng" % len(ev))
    raise SystemExit(0)


A.tron_sfx = _in
import dung  # noqa: E402

if __name__ == "__main__":
    sys.argv = ["dung.py"] + sys.argv[1:]
    dung.cli()
