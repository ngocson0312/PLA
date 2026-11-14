"""Đọc vị trí Google Maps và chọn CTA theo đúng các ô khách nhập."""

import copy
import re
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests


MAP_HOSTS = {
    "google.com", "www.google.com", "maps.google.com",
    "google.com.vn", "www.google.com.vn", "maps.google.com.vn",
    "maps.app.goo.gl", "goo.gl",
}
SO = r"-?\d{1,3}(?:\.\d+)?"


def cap_toa_do(value):
    match = re.fullmatch(r"\s*(" + SO + r")\s*,\s*(" + SO + r")\s*\.?\s*", value)
    if not match:
        return None
    lat, lon = map(float, match.groups())
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    raise ValueError("Tọa độ chưa hợp lệ. Sao chép lại cặp vĩ độ, kinh độ trên Google Maps.")


def tu_link(value):
    """Ưu tiên tọa độ ghim trong data trước tâm khung nhìn @lat,lon."""
    value = unquote(value)
    pins = re.findall(r"!3d(" + SO + r")!4d(" + SO + r")", value)
    if pins:
        return cap_toa_do(",".join(pins[-1]))
    query = parse_qs(urlparse(value).query)
    for key in ("q", "query", "ll"):
        if query.get(key):
            point = cap_toa_do(query[key][0])
            if point:
                return point
    match = re.search(r"@(" + SO + r"),(" + SO + r")(?:,|/|$)", value)
    return cap_toa_do(",".join(match.groups())) if match else None


def doc_vi_tri(value, tim_dia_chi):
    value = value.strip()
    if not value:
        raise ValueError("Dán vị trí đã sao chép từ Google Maps vào ô Vị trí trên Google Maps.")
    point = cap_toa_do(value)
    address = value
    if value.lower().startswith(("http://", "https://")):
        for _ in range(6):
            parsed = urlparse(value)
            if parsed.scheme != "https" or parsed.hostname not in MAP_HOSTS:
                raise ValueError("Dùng link Google Maps hoặc cặp tọa độ sao chép từ Google Maps.")
            point = tu_link(value)
            if point:
                break
            if parsed.hostname in ("maps.app.goo.gl", "goo.gl"):
                response = requests.get(value, allow_redirects=False, timeout=20)
                response.raise_for_status()
                location = response.headers.get("Location")
                if not location:
                    raise ValueError("Không mở được link Maps rút gọn. Mở Google Maps rồi sao chép tọa độ của ghim.")
                value = urljoin(value, location)
                continue
            query = parse_qs(parsed.query)
            address = (query.get("query") or query.get("q") or [""])[0]
            if not address and "/place/" in parsed.path:
                address = unquote(parsed.path.split("/place/", 1)[1].split("/", 1)[0]).replace("+", " ")
            if not address:
                raise ValueError("Link Maps chưa có vị trí. Nhấp phải đúng ghim trên Google Maps rồi chép dòng tọa độ đầu tiên.")
            break
        else:
            raise ValueError("Link Maps chuyển hướng quá nhiều. Hãy sao chép trực tiếp tọa độ của ghim.")
    if point:
        return {"lat": point[0], "lon": point[1], "chinh_xac": True}
    found = tim_dia_chi(address, n=3)
    if not found:
        raise ValueError("Không tìm thấy địa chỉ này. Mở Google Maps, nhấp phải vào nhà đất rồi sao chép tọa độ.")
    return {"lat": found[0]["lat"], "lon": found[0]["lon"], "chinh_xac": False}


def thong_tin_cta(value):
    """SĐT và phần chữ đều lấy từ ô CTA, không suy từ lời đọc."""
    phone = None
    for match in re.finditer(r"(?<!\w)\+?\d[\d .()\-]{6,}\d(?!\w)", value):
        digits = re.sub(r"\D", "", match.group())
        if 8 <= len(digits) <= 15:
            phone = match
            break
    other = value
    if phone:
        other = value[:phone.start()] + value[phone.end():]
        other = re.sub(r"(?im)\b(?:sđt|sdt|điện thoại|phone|hotline|zalo)\s*[:\-]?\s*(?=$|[\n,;|])", "", other)
    lines = [s.strip(" ,;|:-") for s in other.splitlines()]
    lines = [s for s in lines if s]
    return {
        "ten": lines[0] if lines and len(lines[0]) <= 45 else "",
        "sdt": re.sub(r"[^\d+]", "", phone.group()) if phone else "",
        "noi_dung": "\n".join(lines[1:] if lines and len(lines[0]) <= 45 else lines),
        "_van_ban": value,
    }


def ap_cta(plan, value):
    """Ghi đè lựa chọn CTA của AI bằng ô CTA đã nhập, dùng được khi chạy lại."""
    value = value.strip()
    dur = float(plan["thoi_luong"]) + float(plan.get("cai_dat", {}).get("duoi", 0.9))
    old = [t for t in plan.get("the", []) if t.get("kieu") in ("lien_he", "theo_doi")]
    start = max(0.0, dur - 6.0)
    if old and 3 <= dur - float(old[0]["tu"]) <= 10:
        start = float(old[0]["tu"])
    cards = []
    for card in plan.get("the", []):
        if card.get("kieu") in ("lien_he", "theo_doi") or float(card["tu"]) >= start:
            continue
        card = copy.deepcopy(card)
        card["den"] = min(float(card["den"]), start)
        cards.append(card)
    for scene in plan.get("canh", []):
        if scene.get("loai") == "cta":
            scene_start = float(scene["tu"])
            scene_end = float(scene.get("den") or dur)
            scene.clear()
            scene.update(loai="ban_do", tu=scene_start, den=scene_end,
                         cam=[{"t": scene_start, "tam": "nha", "zoom": 17}])
    tt = plan.setdefault("thong_tin", {})
    tt["_nguon"] = "người dùng nhập thông tin căn nhà và ô CTA"
    if value:
        contact = thong_tin_cta(value)
        tt["lien_he"] = contact
        cards.append(dict(kieu="lien_he", tu=start, den=dur, **contact))
    else:
        tt["lien_he"] = {}
        plan.setdefault("kenh", {})["ten"] = ""
        cards.append({"kieu": "theo_doi", "tu": start, "den": dur})
    plan["the"] = cards
    plan.setdefault("cai_dat", {})["cta"] = True
