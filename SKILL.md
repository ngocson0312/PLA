---
name: ban-do-tien-ich-nha-dat
description: "Dựng VIDEO BẢN ĐỒ giới thiệu NHÀ ĐẤT / BĐS dọc 9:16 từ THÔNG TIN NHÀ + 1 FILE AUDIO giọng đọc + ẢNH / CLIP NHÀ THẬT (nếu có): nền BẢN ĐỒ VỆ TINH dựng bằng code (Esri World Imagery + hình học thật OpenStreetMap) theo KIỂU MẪU đã chốt (video khách Video_Mau.mp4: nền vệ tinh tối, ghim VÀNG có tên ngay tại ghim, TÊN ĐƯỜNG NEON chạy dọc đường, tiêu đề trên cùng trắng + vàng, chữ địa danh LỚN, thước '≈ m', biển ảnh công trình, CẬN CẢNH LÔ ĐẤT zoom sát khối xanh sáng + chữ diện tích + ngoặc mặt tiền, chữ không bao giờ đè sub), camera bay nhiều điểm dừng theo lời, GHIM LÔ ĐẤT vàng (vị trí chưa chắc ⇒ vòng 'KHU VỰC LÔ ĐẤT'), VÒNG BÁN KÍNH 500 m / 1 km, TIỆN ÍCH THẬT xung quanh tự quét (khách sạn, đền chùa / di tích, công viên, hồ, trường, bệnh viện, mua sắm, metro, đại sứ quán, thể thao…) với ghim icon màu theo nhóm + nhãn tên + '≈ khoảng cách · phút đi bộ', ĐƯỜNG ĐI THẬT (OSRM ô tô / đi bộ) tự vẽ chạy từ nhà tới tiện ích, TÔ SÁNG đường phố / đại lộ / tuyến METRO quy hoạch theo hình học OSM, TÔ VÙNG hồ / công viên / phố cổ, THẺ ẢNH-CLIP NHÀ bo góc (Ken Burns, chú thích, dây nối về ghim, nhiều ảnh lần lượt), THẺ THÔNG TIN (diện tích, mặt tiền, pháp lý — từng dòng hiện đúng lúc đọc), HUY HIỆU GIÁ vàng, CTA GỌI ĐIỆN (avatar, tên, số điện thoại hiện theo nhóm số đúng lúc đọc, nút GỌI NGAY + tay bấm, không SFX), đầu đề navy, sub karaoke nguyên văn, SFX nhẹ bám hình, −14 LUFS, mã hoá 1 lần, tự kiểm. Không bịa số nhà: giá / diện tích / SĐT chỉ lấy từ lời hoặc thông tin người dùng; khoảng cách đo bản đồ luôn '≈'. Whisper nhận lời → quét tiện ích → Claude viết ke_hoach.json → DỪNG 1 lần ở cổng duyệt → dựng → tự kiểm. Trigger '/ban-do-tien-ich-nha-dat', 'làm video bản đồ nhà đất', 'video map tiện ích quanh nhà', 'video bản đồ BĐS có ảnh nhà', 'audio + ảnh nhà ra video bản đồ', 'render tiện ích xung quanh căn nhà'."
---

# ban-do-tien-ich-nha-dat — thông tin nhà + audio + ảnh/clip nhà → video BẢN ĐỒ tiện ích 9:16

> Chủ dự án 09/11/2026 (job khách hàng BĐS): *"tạo 1 skill với bản đồ map cũng như có hình ảnh ngôi nhà, input sẽ là thông
> tin nhà, file audio, ảnh hoặc video nhà thực tế nếu có … chèn video hoặc ảnh, có file audio … render chi tiết tiện ích
> xung quanh căn nhà, từ khách sạn, địa danh, đường, công cộng, metro, view ngắm … đủ nhé … nhớ là đây là video dạng bản
> đồ map nhé. chi tiết vào"*. Bản thử đầu: `F:\VIDA_TEST\PLA\Audio.mp3` + `F:\VIDA_TEST\PLA\Resources` (đất Tây Hồ).

Code chung nền với skill `ban-do-quy-hoach-bds-ve-tinh` (Camera / ô Esri / OSM / sub karaoke / CTA tay bấm) nhưng là skill
riêng: trọng tâm là **1 ngôi nhà + tiện ích quanh nó**, không phải tuyến sông/đường quy hoạch.

## ĐÃ CHỐT — không hỏi lại

1. **Toàn video là BẢN ĐỒ** (vệ tinh Esri, hình học OSM thật). Ảnh / clip nhà chỉ là THẺ đặt trên bản đồ, không phủ kín khung.
2. **Không bịa số nhà**: giá, diện tích, mặt tiền, số tầng, SĐT, tên người liên hệ chỉ lấy từ lời đọc hoặc file thông tin
   người dùng (`--info`). `run.py kiem-kh` chặn ⛔ số không có nguồn. Mục lời không nói ⇒ ĐOÁN và hỏi ở cổng duyệt.
3. **Số đo bản đồ luôn có "≈"** (khoảng cách đường đi OSRM, bán kính vòng). Đi bộ ghi phút (`≈ 450 m · 6 phút đi bộ`);
   **ô tô KHÔNG ghi phút** (OSRM tính đường vắng — giờ cao điểm Hà Nội sai xa), trừ khi `"thoi_gian": true`.
4. **Vị trí lô đất**: số nhà / link bản đồ ⇒ `nha.chinh_xac: true` (ghim vàng); chỉ biết tên phố ⇒ `chinh_xac: false`
   ⇒ vòng nét đứt "KHU VỰC LÔ ĐẤT" (`ban_kinh_m` ~80) và PHẢI hỏi ở cổng duyệt. Khoảng cách tiện ích đo từ điểm này.
5. **Tiện ích là dữ liệu THẬT** quét quanh nhà (`run.py tien-ich`, Photon reverse theo thẻ OSM) — không tự thêm tiện ích
   không có trên OSM. Tên lấy nguyên OSM (Claude được viết ngắn lại qua `nhan`, không đổi nghĩa).
6. **Metro / quy hoạch** chỉ vẽ tuyến CÓ trong OSM (`railway=construction|proposed|subway`), tên theo OSM, hỏi ở cổng duyệt.
7. **Mỗi nhắc tên = 1 hình**: ghim / tô sáng hiện ĐÚNG giây đọc tên (`t` = giây chữ đó trong loi_doc.txt); đường đi vẽ
   TRƯỚC đó `dai_ve` giây để ghim bật ra đúng lúc đọc.
8. **CTA gọi điện không SFX** (góp ý cũ: chime cuối chói). **Số điện thoại HIỆN theo nhóm 4-3-3** (`0904 282 858`, chốt
   09/11/2026: nhóm theo lời đọc "0904 28 28 58" cách nhau quá) — nhóm sát nhau (cách 20 px), từng CHỮ SỐ bật đúng giây đọc
   (`sdt_tu` vẫn ghi theo nhóm LỜI ĐỌC). 11 số → 4-3-4, 8 số → 4-4; ép cách khác bằng `sdt_hien`.
   **Lời KHÔNG đọc số điện thoại ⇒ cuối video BẮT BUỘC thẻ `theo_doi`** (chốt 09/11/2026, "CTA có button, anim bàn tay
   nhấn FOLLOW, xịn xò"): avatar vòng màu xoay + huy hiệu "+" → nút FOLLOW gradient hồng có vệt sáng quét → tay nhấn
   (sóng trắng, pháo giấy, sao lấp lánh) → "✓ ĐÃ FOLLOW" → tay nhấn chip ♥ (tim bay) → chuông tự rung. Không SFX.
   `kiem-kh` báo ⛔ nếu video không có CTA nào (`cai_dat.cta: false` để tắt khi người dùng bảo).
9. Sub karaoke nguyên văn (Montserrat, chữ đang đọc vàng, y 1545); `sua_chu` chỉ sửa lỗi nhận dạng (tên phố, chính tả).
10. Nguồn ảnh luôn ghi đáy khung: `Ảnh: Esri World Imagery · Dữ liệu: © OpenStreetMap contributors · Đường đi: OSRM`.
11. −14 LUFS / −1 dBTP, mã hoá hình 1 lần (x264 bt709), video kéo 0,9 s sau tiếng cuối, ra `<audio>_BDTI.mp4` (không ghi đè:
    `_BDTI_2.mp4`…).
12. **Phong cách MẪU là mặc định cho job khách BĐS** (`cai_dat.phong_cach: "mau"`, chốt 09/11/2026 theo video khách gửi
    `F:\VIDA_TEST\PLA\Video_Mau.mp4` — "chi tiết hình dạng hơn"): nền vệ tinh tối + viền tối (`nen_sang` 0,66), ghim VÀNG
    giọt nước + nhãn vàng nghiêng ngay trên/dưới ghim, mũi tên vẽ tay chỉ ghim nhà, TÊN ĐƯỜNG NEON xanh chanh chạy dọc
    thân đường (`neon`), tiêu đề trên cùng 2 dòng trắng + VÀNG (`tieu_de_tren`, thay hook navy), chữ địa danh LỚN nảy từng
    chữ (`chu_lon`, vd "HỒ TÂY"), BIỂN ẢNH cắm cọc (`bien_anh`), thước neon nét đứt (`thuoc`), vòng mảnh vàng phát sáng,
    LÔ ĐẤT CẬN CẢNH khối xanh sáng (`lo_dat`). Lời khách cụ thể (hồ cách ? m, tên đường, công trình gần) ⇒ mỗi thứ 1 hình
    riêng có số đo "≈".
13. **Ghim chỉ có khi tên nằm NGAY tại ghim** (góp ý 09/11/2026 "chỉ có icon địa điểm khi đúng địa điểm đó"): nhãn chỉ được
    ngay trên hoặc ngay dưới ghim; không chỗ ⇒ ẨN CẢ GHIM — và phải BỎ ghim đó khỏi kế hoạch (SFX tính trước khi dựng hình
    nên ghim ẩn vẫn kêu pop). Không bao giờ để icon trơ hay nhãn lệch xa ghim.
14. **Chữ trên bản đồ không bao giờ đè sub / tiêu đề / thẻ** (góp ý "đè text lên sub kìa"): tên đường thử lần lượt các điểm
    neo dọc đường (lệch 0, ±250, ±500, ±800, ±1200 m), không điểm nào sạch ⇒ ẩn tên. Nhãn vòng "500 M" chọn hướng 1 lần
    (vừa màn hình cả lúc đầu lẫn lúc HẾT cảnh) rồi đứng yên, vướng ⇒ ẩn, không nhảy.
15. **Cận cảnh lô đất phải "xịn"** (góp ý kèm ảnh mẫu lô xanh "200m²": "map zoom lại, hiệu ứng các thứ có vào, SFX các kiểu
    nữa phải đủ"): camera zoom ~21,2 (lô ~250 px), `nen_sang` 0,92, nền tự làm nét khi zoom > 19,2; lô quét đầy xanh từ mặt
    tiền vào + vạch quét sáng, ánh lướt chéo mỗi 2,4 s, viền trắng + quầng xanh thở, gợn viền lan, chấm góc bật, chữ diện
    tích to xoay theo lô + sao lấp lánh, ngoặc đo cạnh ("15m") đúng giây đọc. SFX: swoosh lúc quét, sparkle lúc chữ, pop
    lúc ngoặc. Hình lô không có sơ đồ sổ đỏ = ĐOÁN (`doan: true`) ⇒ hỏi ở cổng duyệt.

## Cần gì

- 1 file audio giọng đọc (mp3/m4a/wav). Thư mục ảnh / clip nhà (tuỳ chọn, `--res`). File thông tin nhà (tuỳ chọn, `--info`
  .txt/.md/.json: giá, diện tích, mặt tiền, pháp lý, địa chỉ / link bản đồ, tên + SĐT liên hệ).
- Mạng (chạy ngoài sandbox): Photon, OSM API, Overpass (overpass-api.de, hay 502 ⇒ tự thử lại 4 lần), OSRM
  (router.project-osrm.org ô tô, routing.openstreetmap.de đi bộ), ô ảnh Esri. Cache ở `~/.cache/ban-do-tien-ich-nha-dat`
  và dùng chung ô ảnh / OSM với `~/.cache/ban-do-quy-hoach-bds-ve-tinh`.
- Thư viện: `requirements.txt` (faster-whisper, opencv, pillow, requests, numpy). Whisper large-v3 (~3 GB lần đầu).

## Cách Claude chạy (trả lời tiếng Việt có dấu)

Mọi lệnh: `python -I -X utf8 .claude\skills\ban-do-tien-ich-nha-dat\scripts\run.py <lệnh> …` (work = `<audio>_bdti_work`).

1. `quet --audio <file> [--res <thư mục>] [--info <file>]` → `loi_doc.txt` (chữ@giây), `so_lieu.txt`, `tai_nguyen.jpg`
   (ảnh + khung giữa mỗi clip, tên file + cỡ), `thong_tin_nha.txt`, khung `ke_hoach.json`. **Claude MỞ tai_nguyen.jpg.**
2. Điền `nha` (toạ độ: `run.py tim "<địa chỉ / tên phố>"`; giao 2 phố thì lấy giữa, ghi `_vi_sao` ĐOÁN), `khu_vuc`,
   `thong_tin` (từ lời / file), `tien_ich {ban_kinh_m 1500, toi_da 6, nhom?}`.
3. `tien-ich --work <dir>` → `tien_ich.json/.txt/.jpg`: mỗi tiện ích có id (`khach_san_2`, `ho_6`…), tên OSM, đường đi thật,
   chữ khoảng cách. **Claude mở tien_ich.jpg + đọc tien_ich.txt**, chọn tiện ích khớp NGHĨA lời (vd "người nước ngoài" ⇒ đại
   sứ quán + trường quốc tế + khách sạn căn hộ dịch vụ + siêu thị nhập khẩu).
4. Khai `dia_diem` cho thứ không phải tiện ích quét: đường phố, đại lộ, metro, hồ lớn, phố cổ, sân bay… rồi `dia-diem`.
   Đọc kỹ tên OSM trả về (sai đối tượng ⇒ sửa `osm` / `ten_osm_re`).
5. Viết `canh` (cảnh `ban_do`, phủ kín 0 → hết, mỗi cụm ý 1 cảnh 2,5–6 s) + `the` (ảnh / thông tin / giá / liên hệ) +
   `hook` + `sua_chu`. Mẫu đầy đủ: `references/vi-du-tay-ho-mau.json` (kiểu mẫu, mặc định cho khách BĐS) — kiểu cũ `references/vi-du-tay-ho.json`.
6. `kiem-kh` (sửa hết ⛔; ⚠ số trong nhãn bản đồ phải là tên OSM / số đo) → `duyet` → **MỞ duyet.jpg** (và xem_truoc_*.jpg
   nghi ngờ: nhãn mất, đè nhau, ghim lệch) → sửa đến khi sạch → `ds_sfx.py --work <dir>` soi SFX → **CỔNG DUYỆT** (1 lần, hỏi D1–D7, chờ trả lời).
7. `dung --work <dir>` (chạy nền, ~10–15 phút cho 66 s) → `kiem --work <dir>` → **MỞ soat_canh.jpg + soat_sub_*.jpg**.
8. Giao: đường dẫn mp4, độ dài, khổ, LUFS, bảng đồ hoạ, mục còn ĐOÁN.

## CỔNG DUYỆT (lần nào cũng hỏi, có đề xuất mặc định)

- **D1 Vị trí lô đất** (nếu ĐOÁN): xin số nhà / link Google Maps; mặc định giữ vòng "KHU VỰC LÔ ĐẤT".
- **D2 Liên hệ**: tên (Whisper hay sai tên riêng) + SĐT; mặc định giữ như lời.
- **D3 Metro / quy hoạch**: tuyến nào giữ (liệt kê tuyến OSM + khoảng cách); mặc định giữ hết tuyến trong ~3 km.
- **D4 Âm thanh**: SFX nhẹ có/không, nhạc nền (file của người dùng); nhắc kho SFX chưa rõ giấy phép nếu giao thương mại.
- **D5 Nhãn nhạy cảm**: tiện ích không tên / khoảng cách lệch lời ("vài bước chân" mà 850 m) — giữ số thật hay bỏ.
- **D6 Logo / tên kênh** góc trên phải; mặc định không có.
- **D7 Kiểu mẫu** (khi `phong_cach: "mau"`): hình lô ĐOÁN (xin sơ đồ sổ đỏ / các góc lô; mặc định chữ nhật mặt tiền × diện
  tích/mặt tiền, song song ngõ trước nhà); biển ảnh không có ảnh thật (mặc định ảnh vệ tinh cận cảnh); số đo hồ / công trình
  đường chim bay hay đi bộ (mặc định chim bay "≈ 130 m"); tiêu đề lấy từ lời khách giữ nguyên chữ.

## ke_hoach.json — các khối

| Khối | Ý nghĩa |
|---|---|
| `thong_tin` | thông tin nhà; `_nguon` bắt đầu "file…" / "người dùng…" ⇒ số trong đó được phép lên hình |
| `nha` | `{lat, lon, chinh_xac, ban_kinh_m, _vi_sao}` |
| `tien_ich` | `{ban_kinh_m, toi_da, nhom?}` cho lệnh quét |
| `hook` | `{tu, den, dong1, dong2, dong3?, fade}` hộp navy y≈202 (đừng chồng thẻ ảnh đầu) |
| `dia_diem.<key>` | `{ten, loai: diem\|vung\|tuyen, osm: "W…/R…/N…"}` hoặc đường theo tên `{ten, ten_osm_re: "^(Phố \|Đường )?Xuân Diệu$", quanh: [lat, lon], ban_kinh_m, the: highway\|railway}` |
| `canh[]` | `loai: "ban_do"` (xem dưới); các loại cũ `tinh / diem / to_vung / thuoc_do / bay_tuyen / ban_do_tong / cta` vẫn dùng được |
| `the[]` | thẻ màn hình, giây tuyệt đối (xem dưới) |
| `sua_chu` | `{"cụm sai": "cụm đúng"}` cho sub |
| `cai_dat` | `sfx`, `sfx_bo [file]`, `sfx_them_tay [{t, file, muc}]`, `nhac`, `hoa_tan 0.25`, `cap_tu [cặp từ không tách sub]`, `phong_cach: "mau"`, `nen_sang 0.66`, `nen_bao_hoa 0.78`, `nen_vien 0.42` … |

**Khoá kiểu mẫu trong cảnh `ban_do`** (`scripts/lop_mau.py`; mẫu đầy đủ `references/vi-du-tay-ho-mau.json`):
- `nen_sang` (độ sáng nền cảnh, cận lô 0,92), `net` (độ làm nét khi zoom > 19,2, mặc định 0,9).
- `nha: {t, nhan: "VỊ TRÍ ĐẤT", mui_ten: "trai" | "phai" | true}`.
- `neon: [{tuyen, t, dai_ve, ten: "ĐƯỜNG QUẢNG AN" | true | false, neo: "nha" | [lat, lon], lech_m, lech_px (+ = phía trên;
  2 đường song song ⇒ trái dấu + neo so le), co 48–60}]` — tuyến phải có trong `dia_diem`.
- `lo_dat: {t, theo_duong: key dia_diem, rong_m, sau_m, nhan: "250m²", t_nhan, canh: [{canh: truoc|sau|trai|phai, chu: "15m",
  t}], doan: true, den (giây tắt dần), le_m 2.0}` — chữ phải có trong lời.
- `chu_lon: [{t, chu: "HỒ TÂY", tai: [lat, lon] (đặt TRONG vùng, xa nhãn khác), co 86, goc -6}]`.
- `bien_anh: [{diem, t, chu, anh? (không có ⇒ ảnh vệ tinh z17,6), rong 300, cot 150}]`.
- `thuoc: [{a: "nha", b: id, t, chu? (tự "≈ … m")}]`.
- `tieu_de_tren: [{t, den?, dong: ["Hồ Tây chỉ cách", "≈ 130 M"], vang: [1], y 230, co 60}]` — dòng có số đo phải có "≈".

**Cảnh `ban_do`**:
```json
{"loai": "ban_do", "tu": 11.4, "den": 15.46, "_loi": "…",
 "cam": [{"t": 11.4, "tam": "nha", "zoom": 16.0},
         {"t": 11.45, "dai": 1.3, "vua": ["nha", "dai_su_quan_1", "truong_3"], "le": 0.16, "theo_duong": false},
         {"t": 27.75, "dai": 1.4, "tam": "noi_bai", "zoom": 11.0, "lech_y": 200}],
 "troi": 0.015,
 "nha": true | {"t": 1.55, "phu": "Thổ cư · 250 m²"} | {"nhan": false},
 "vong": [{"r_m": 500, "t": 11.8}],
 "tien_ich": [{"id": "ho_6", "t": 16.36, "duong": true, "nhan": "Hồ Tây", "dai_ve": 1.0},
              {"id": "phu_tay_ho", "t": 25.36, "kieu": "o_to", "nhom": "di_tich", "nhan": "Phủ Tây Hồ"}],
 "tuyen_sang": [{"tuyen": "xuan_dieu", "t": 9.8, "kieu": "duong|metro", "mau": "vang", "ten": "Phố Xuân Diệu" | true | false, "dai_ve": 1.2}],
 "vung_sang": [{"vung": "ho_tay", "t": 16.14, "mau": "xanh", "nhan": false}],
 "toi": [[45.1, 0.0], [45.5, 0.4]],
 "dau_de": [{"t": 11.96, "tieu_de": "Thủ phủ cộng đồng quốc tế"}],
 "dia_danh": false}
```
- `cam`: điểm dừng đầu = camera đứng sẵn; mỗi điểm sau bay tới trong `dai` giây bắt đầu ở `t`. `tam` = "nha" | id tiện ích |
  key dia_diem; `vua` = khung vừa các thứ đó (kèm đường đi nếu `theo_duong`); `lech_y` (+ = điểm nằm cao hơn giữa khung —
  chừa chỗ cho thẻ thông tin ở đáy). `troi` = zoom trôi chậm khi đứng.
- `tien_ich[].id` = id trong tien_ich.json (đã có đường đi) hoặc key dia_diem (đường đi OSRM tự tính, `kieu` o_to/di_bo,
  >1,2 km tự là ô tô). `t` = giây GHIM bật (đúng chữ đọc tên). `duong: false` ⇒ chỉ ghim + nhãn (cảnh nhiều tiện ích).
- Màu: `vang cam ngoc xanh hong do trang navy` hoặc `[r,g,b]`. Nhóm tiện ích & màu ghim: `scripts/bieu_tuong.py` → `NHOM`.

**Thẻ `the[]`** (giây tuyệt đối, ảnh tìm trong Resources):
- `anh`: `{tu, den, anh: "a.jpg" | ["a.jpg", "b.mp4"…], chu: "…" | [...], vi_tri: giua|phai|trai|tren, rong, cao, y, phu_toi,
  noi_nha}` — ảnh nhỏ (≤ 600 px) đừng để thẻ rộng quá 1,5× ảnh; ảnh ngang cho thẻ ngang (`rong 640, cao 480`); mỗi ảnh ≥ 1,2 s.
- `thong_tin`: `{tu, den, tieu_de, dong: [{icon, nhan, gia_tri, t}], day | y}` — icon: dien_tich, mat_tien, so_do, gia,
  nha, vi_tri, duong, o_to, di_bo, dien_thoai, nguoi, toa_nha…
- `gia`: `{tu, den, nhan: "Giá chào", gia: "Nhỉnh 80 tỷ", y}` — ka-ching.
- `lien_he`: `{tu, den, ten, sdt: "0904 28 28 58" (cách nhóm THEO LỜI ĐỌC), sdt_tu: [giây mỗi nhóm lời], sdt_hien?
  ("0904 282 858" — bỏ trống = tự 4-3-3), nhan, t_bam, dong_cuoi, dong_cuoi_tu, y}`.
- `theo_doi` (lời không có SĐT): `{tu, den (= hết video), t_bam? (giây nhấn FOLLOW — đặt ĐÚNG chữ "follow / theo dõi" nếu
  lời có, mặc định tu + 1,2), dong?: ["FOLLOW KÊNH NGAY", "để xem thêm nhiều căn nhà đẹp"], nut?: "FOLLOW",
  nut_sau?: "ĐÃ FOLLOW", chip?: ["Bật chuông", "Thả tim", "Chia sẻ"] | false, bam_tim?: true, y?: 470}` — cần ≥ 3,3 s để
  tay nhấn cả FOLLOW lẫn ♥ (ngắn hơn ⇒ chỉ nhấn FOLLOW). Logo/tên kênh lấy từ `kenh` (không có thì ghim nhà vàng, không tên).
  Code: `scripts/cta_follow.py`; clip thử: `F:\VIDA_TEST\PLA\thu_CTA_follow.mp4`.

## Lớp đồ hoạ (scripts/lop_bds.py, canh_bds.py — khung 1080×1920)

| Lớp | Hình |
|---|---|
| `NhaMarker` | ghim vàng có hình nhà rơi + nảy, gợn sóng vàng lặp, vòng khu vực nét đứt xoay (khi ĐOÁN), nhãn navy viền vàng |
| `ve_vong` | vòng bán kính trắng nét đứt mở rộng + pill vàng "500 M" |
| `DiemTienIch` | đường đi vẽ chạy (đầu chấm trắng, xong thì vạch trắng chảy) → ghim icon màu nhóm bật back-out + gợn → nhãn navy thanh màu: TÊN IN HOA + icon đi bộ/ô tô + "≈ …" |
| `TuyenSang` | đường: nét màu viền tối vẽ chạy; metro: nét màu viền trắng + vạch trắng chạy; tên gắn vào tuyến (pill chấm màu + dây) |
| `VungSang` | phủ màu + viền tự vẽ quanh vùng (+ pill tên tuỳ chọn) |
| `TheAnh` | thẻ ảnh/clip viền trắng bo góc, bóng, zoom chậm 1,00→1,08, hoà 0,3 s giữa các ảnh, chú thích pill navy, dây vàng nối về ghim nhà |
| `TheThongTin` | hộp navy vạch vàng, mỗi dòng: tròn vàng icon + NHÃN nhỏ + giá trị Montserrat Black 54, hiện đúng `t` |
| `TheGia` | huy hiệu gradient vàng, icon thẻ giá, bật back-out + vệt sáng lướt |
| `TheLienHe` | thẻ navy: avatar vàng gợn sóng, "GỌI NGAY CHO EM", TÊN vàng, ☎ số từng nhóm, nút xanh GỌI NGAY rung ống nghe + tay bấm (`cta.ban_tay`) |
| Nhãn | `dat_nhan`: 8 hướng × 3 khoảng cách, né sub / đầu đề / thẻ / nhãn khác, giữ chỗ cũ (không nhảy), xa ⇒ dây dẫn mảnh |

Lớp kiểu mẫu (`scripts/lop_mau.py`): `GhimVang` (ghim tiện ích + nhãn sát ghim), `NhaGhimVang` (ghim nhà rơi nảy + sóng +
mũi tên vẽ tay), `ve_vong_mau`, `DuongNeon` (lõi + quầng thở + vệt sáng chạy, tên hiện dần dọc đường), `LoDat`, `ChuLon`,
`BienAnh`, `TieuDeTren`, `ThuocNeon`, `nen_toi`.

SFX (tự, lọc trùng < 0,35 s cùng file và < 0,12 s mọi tiếng): whoosh khi camera bay xa, ding khi ghim nhà rơi, swoosh nhẹ khi
vẽ đường / tên neon / vòng, pop rất nhẹ mỗi ghim, pop-2 mỗi vùng / chữ lớn, quick-swoosh mỗi tiêu đề trên cùng / thước,
camera-shutter ở biển ảnh và thẻ ảnh, lô đất swoosh + sparkle + pop, pop-2 mỗi dòng thông tin, ka-ching ở giá; mức
`chinh +4 / nhe +1 / rat_nhe −5 dB` so với giọng tại chỗ. Bản Tây Hồ kiểu mẫu: 48 tiếng / 66 s. Liệt kê SFX không cần dựng:
`scripts/ds_sfx.py --work <dir>`.

## Bẫy đã gặp (đừng lặp lại)

- **Nhãn tiện ích tự va ghim của chính nó** (nhãn cách ghim 34 px < nửa ghim + lề) ⇒ mọi nhãn bị ẩn. Đã sửa: bỏ qua hộp ghim
  của chính nó (`bo=`), nhãn trên/dưới được trượt ngang cho lọt khung.
- Ghim bật SAU khi đường vẽ xong ⇒ trễ lời, có cảnh ghim chỉ hiện 0,2 s. Đã chốt: `t` = giây ghim, đường vẽ trước.
- Nhãn nhà vẽ sau tên đường ⇒ che tên đường. Thứ tự đúng: nét → ghim → nhãn nhà → nhãn tiện ích → tên tuyến/vùng.
- Đường nhiều chuỗi (Âu Cơ 50 way, Võ Chí Công 97 way) ⇒ mỗi chuỗi 1 chấm đầu trắng = rác. Chỉ chuỗi hiện rõ nhất có chấm.
- `W1217914839` "Ranh giới khu phố cổ" là ĐƯỜNG ranh (không khép) ⇒ dùng relation `R20663236` "Khu phố cổ" làm vùng.
- Overpass hay 502 ⇒ chạy lại `dia-diem` (cache theo câu hỏi, chỗ đã có không tải lại).
- Tên metro OSM có lỗi gõ ("sô 14") ⇒ `ten_osm_re` khớp đúng chuỗi OSM; nhãn hiện viết lại "Tuyến số 14".
- Ảnh khách gửi nhỏ (408×544) ⇒ thẻ ảnh giữa ≤ 600×800, thẻ phụ ~430 rộng, kẻo vỡ hạt.
- Ảnh ngang trong thẻ dọc bị cắt mất 45 % ⇒ đặt ảnh ngang ở thẻ ngang riêng.
- Vùng hồ khổng lồ (Hồ Tây) làm `vua` lùi quá xa ⇒ khung theo TIỆN ÍCH `ho_6` (đích là mép hồ gần nhà), không theo vùng hồ.
- Âm `muc` "nhe" (+1 dB) cho pop lặp 5–6 lần quá ồn ⇒ thêm mức `rat_nhe`.
- PowerShell in tiếng Việt lỗi cp1252 ⇒ luôn `python -I -X utf8`.
- Bản thử ra −14,8 LUFS: đỉnh SFX cao (mix TP −0,4 dBFS) ⇒ loudnorm tự bỏ chế độ tuyến tính, ra nhỏ hơn đích. Đã sửa
  `am_thanh.master`: khi đỉnh + độ tăng > TP − 0,2 thì dùng `volume` + `alimiter` (level tắt) rồi bù phần lệch 1 lần.
  Muốn trộn lại tiếng mà không dựng lại hình: `dung.py --chi-tieng … --out <file tạm>`.
- Camera `vua` có tiện ích hồ (`ho_6` Hồ Tây) ⇒ `bbox_cua` từng lấy `lat/lon` = TÂM hồ (giữa Hồ Tây) ⇒ khung lùi xa, cụm nhà
  dồn sát mép phải. Đã sửa: khung theo `dich` (mép hồ gần nhà, chỗ vẽ ghim).
- Người dùng gửi vị trí thật SAU cổng duyệt ⇒ id trong `tien_ich.json` ĐỔI THỨ TỰ khi quét lại (`khach_san_2` cũ ≠ mới) ⇒
  phải chọn lại id trong mọi `canh[].tien_ich` / `vua`, đo lại khoảng cách tới phố trong lời; sao lưu `*_vitri_doan.*`.
- 5 ghim trong 1 khung, 2 ghim cùng phía (Somerset 58° + Lion Mall 88°) ⇒ ghim bật sau chiếm chỗ, nhãn ghim trước bị ẨN.
  Mở `xem_truoc` ở giây SAU ghim cuối; thiếu nhãn ⇒ bỏ / đổi tiện ích sang phía trống (≤ 4 ghim/khung là vừa).
- Whisper tách "250m" và "vuông" ra 2 cụm sub (lặng 0,2 s giữa) ⇒ chấp nhận được; muốn liền thì sửa trong `sua_chu`.
- **Cận cảnh mờ bệt**: `Z_MAX` 18 ⇒ zoom 20+ phóng ô 4–8 lần. Esri có ô z19 nét ở nội thành; z20/z21 trả ảnh XÁM "Map data
  not yet available" (~2,5 KB, vẫn HTTP 200) ⇒ `ban_do.Z_MAX = 19`, ô xám bị đánh dấu `.trong` và bỏ qua.
- NumPy 2 bỏ `ndarray.ptp()` ⇒ dùng `np.ptp(a)`.
- Nhãn vòng chọn hướng xa ghim nhất (180°) nhưng camera trôi làm vòng to ra ⇒ nhãn ra ngoài màn hình rồi mất. Đã sửa: thử
  danh sách hướng, nhận hướng vừa màn hình cả ở khung đầu lẫn camera lúc HẾT cảnh (`_cuoi`).
- Ghim bị ẩn (không chỗ cho nhãn) vẫn có tiếng pop ⇒ bỏ hẳn tiện ích đó khỏi `tien_ich` / `vua` (vd `truong_3` QSI).
- 2 đường song song (Đặng Thai Mai – Quảng An) tên đè nhau ⇒ neo so le + `lech_px` trái dấu.
- Chữ diện tích theo cạnh mặt tiền dốc (> 50°) nghiêng đầu khó đọc ⇒ tự đổi sang cạnh kia.
- Camera lùi xa sau cận lô ⇒ chữ "250m²" lơ lửng to đùng ⇒ `den` (tắt dần) + chữ co theo zoom, lô < 45 px ẩn chữ.
- Hồ lớn: chữ "HỒ TÂY" đặt ở tâm hình học bị cắt mép khung ⇒ đặt `tai` gần bờ phía nhà (trong vùng), zoom cảnh ~18.

## Skill này được bồi thêm sau mỗi lần chạy thật

| Ngày | Lần chạy | Góp ý / thay đổi |
|---|---|---|
| 09/11/2026 | Bản thử `F:\VIDA_TEST\PLA\Audio.mp3` (đất 250 m² Xuân Diệu – Đặng Thai Mai, Tây Hồ, 6 ảnh Resources) | Tạo skill. Cổng duyệt: người dùng chọn "Dựng theo mặc định" (vị trí ĐOÁN giữ vòng khu vực, tên Lê Anh, giữ 4 tuyến metro 2/5/10/14, SFX tạm, giữ nhãn CÔNG VIÊN, không logo). Kết quả `F:\VIDA_TEST\PLA\Audio_BDTI.mp4`: 66,20 s, 1080×1920 30 fps, 11 cảnh bản đồ + 7 thẻ, −14,0 LUFS / đỉnh −3,1 dBFS, dựng ~264 s. Kế hoạch mẫu lưu `references/vi-du-tay-ho.json`. |
| 09/11/2026 | Góp ý bản thử | "Số cách nhau quá, 4 số đầu, 3 số sau, 3 số cuối" ⇒ thẻ gọi điện hiện số 4-3-3 sát nhau, từng chữ số bật theo lời (`lop_bds.chia_so_hien`). Dựng lại `Audio_BDTI_ban2.mp4`. |
| 09/11/2026 | Người dùng gửi ghim Google Maps (21.0651638, 105.8234162 — lệch chỗ đoán ~450 m) | `nha.chinh_xac: true` ⇒ ghim vàng thay vòng khu vực; quét lại tiện ích (Hồ Tây ≈ 370 m đi bộ), cảnh 500 m đổi bộ ghim (ĐSQ Ai Cập, ĐSQ Ca-dắc-xtan, QSI School, Somerset); sửa `bbox_cua` theo `dich`. Dựng `Audio_BDTI_ban3.mp4`. |
| 09/11/2026 | Góp ý: "nhiều kịch bản không đọc điện thoại thì cuối là CTA có button, anim bàn tay nhấn FOLLOW, xịn xò" | Thêm thẻ `theo_doi` (`cta_follow.py`), `kiem-kh` ⛔ khi thiếu CTA cuối; thêm mốc xem trước cho thẻ. |
| 09/11/2026 | Khách chê bản 3 "chưa oki", gửi `F:\VIDA_TEST\PLA\Video_Mau.mp4` + góp ý "Hồ Tây cách ? m / đường Đặng Thai Mai / đường Quảng An / gần Nhà hát Cánh Buồm / nơi định vị đẳng cấp sống, khách châu Âu, căn hộ dịch vụ luôn thiếu phòng" | Thêm KIỂU MẪU (`lop_mau.py`, `phong_cach: "mau"`): ghim vàng, tên đường neon, tiêu đề trắng+vàng, chữ HỒ TÂY lớn, thước "≈ 130 m", biển ảnh Nhà hát, lô đất cận cảnh. Góp ý giữa chừng: "đè text lên sub" ⇒ tên đường dời neo / ẩn; "chỉ có icon khi đúng địa điểm" ⇒ nhãn chỉ sát ghim, không chỗ ẩn cả ghim; "map zoom lại, hiệu ứng, SFX phải đủ, xịn" (ảnh mẫu lô xanh 200m²) ⇒ Z_MAX 19 + bỏ ô xám, zoom 21,2, làm nét, lô đủ hiệu ứng, 48 SFX, `ds_sfx.py`. Cổng duyệt: "Dựng theo mặc định". Ra `F:\VIDA_TEST\PLA\Audio_BDTI_ban4.mp4`: 66,20 s, 1080×1920 30 fps, −14,0 LUFS / đỉnh −3,1 dBFS, dựng ~6 phút. Kế hoạch mẫu `references/vi-du-tay-ho-mau.json`. |
