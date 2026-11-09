# ban-do-tien-ich-nha-dat

Skill Claude Code: **thông tin nhà + 1 file audio + ảnh/clip nhà → video BẢN ĐỒ VỆ TINH dọc 9:16** giới thiệu 1 căn nhà / lô
đất, theo KIỂU MẪU đã chốt (ghim vàng có tên, tên đường neon, tiêu đề trắng + vàng, cận cảnh lô đất khối xanh, tiện ích thật
quanh nhà, sub karaoke, SFX, −14 LUFS). Hướng dẫn đầy đủ cho Claude: [SKILL.md](SKILL.md).

## Cài trên máy mới (vd máy nhà)

1. Cần: Python 3.10+, git, ffmpeg + ffprobe **bản full** trong PATH (`ffmpeg -filters` có `subtitles` và `loudnorm`).
2. Clone thẳng vào thư mục skill của dự án (Claude Code đọc skill ở `<dự án>\.claude\skills\<tên>\SKILL.md`):

   - Nếu `.claude\skills` của dự án là junction vào repo `SON_VIDEO_AI\skills` (như máy công ty):

     ```bash
     git clone https://github.com/ngocson0312/PLA.git "D:\____TTT_____\SON_AI_VIDEO\SON_VIDEO_AI\skills\ban-do-tien-ich-nha-dat"
     ```

   - Nếu không có junction:

     ```bash
     git clone https://github.com/ngocson0312/PLA.git "D:\____TTT_____\SON_AI_VIDEO\.claude\skills\ban-do-tien-ich-nha-dat"
     ```

3. Cài thư viện (phải có `-I` vì script chạy bằng `python -I`):

   ```bash
   python -I -m pip install -r "D:\____TTT_____\SON_AI_VIDEO\.claude\skills\ban-do-tien-ich-nha-dat\requirements.txt"
   ```

4. Lần chạy đầu: Whisper tải mô hình large-v3 (~3 GB, chạy CPU nên lâu); ô ảnh vệ tinh / OSM tải lại vào
   `~/.cache/ban-do-tien-ich-nha-dat` và `~/.cache/ban-do-quy-hoach-bds-ve-tinh` (cần mạng).

## Chạy

Mọi lệnh chạy từ thư mục dự án: `python -I -X utf8 .claude\skills\ban-do-tien-ich-nha-dat\scripts\run.py <lệnh> …`

`quet --audio <file> [--res <ảnh>] [--info <file>]` → `tien-ich` → `dia-diem` → (Claude viết `ke_hoach.json`, mẫu
`references/vi-du-tay-ho-mau.json`) → `kiem-kh` → `duyet` → `scripts\ds_sfx.py --work <dir>` → CỔNG DUYỆT → `dung` → `kiem`.

Nói với Claude: *"Làm video bản đồ nhà đất từ audio `<file>` với Resources `<thư mục ảnh>`"*.

## Đồng bộ máy nhà ↔ máy công ty

- Trước khi làm: `git pull` trong thư mục skill.
- Sửa xong (khi muốn mang sang máy kia): `git add -A`, `git commit -m "…"`, `git push`.
- Dữ liệu job (audio, ảnh khách, thư mục `*_bdti_work`, video ra) **không** nằm trong repo — chép riêng nếu cần làm tiếp
  job dở (vd `F:\VIDA_TEST\PLA`).

## Giấy phép tài nguyên

- Phông trong `assets/fonts`: SIL OFL (xem `OFL-*.txt`).
- SFX trong `assets/sfx`: kho sưu tầm, **chưa rõ giấy phép** (xem `assets/sfx/CREDITS.md`) — video thương mại nên thay bằng
  SFX CC0 / đã mua, giữ nguyên tên file.
