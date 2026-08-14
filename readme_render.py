#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
readme_render.py
读取 food-original.csv 并生成 README.md（覆盖写入）。
美观版：使用HTML表格防止被压缩，保持11列。
"""

import csv
import datetime
import sys
import os

CSV_PATH = "food-original.csv"
OUT_PATH = "README.md"


def esc(s):
    if s is None:
        return ""
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def parse_rating(s):
    try:
        return float(s)
    except Exception:
        return 0.0


def rating_to_stars(rating):
    if rating is None or rating <= 0:
        return "—"
    full = int(round(rating))
    full = max(0, min(5, full))
    return "★" * full + "☆" * (5 - full)


def is_example_row(row):
    name = (row.get("name") or "").strip()
    notes = (row.get("notes") or "").strip()
    if "示例" in name or "示例" in notes:
        return True
    return False


if not os.path.exists(CSV_PATH):
    print(f"ERROR: {CSV_PATH} not found.", file=sys.stderr)
    sys.exit(1)

rows = []
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if not is_example_row(row):
            rows.append(row)

rows.sort(key=lambda r: parse_rating(r.get("rating", "")), reverse=True)

lines = []

# 标题
lines.append("# 🍜 苏州美食推荐\n\n")
lines.append("> 📋 本文件由 `readme_render.py` 根据 `food-original.csv` 自动生成\n\n")
lines.append("> ✏️ 如需添加或修改餐厅，请编辑 `food-original.csv` 并提交 Pull Request\n\n")
lines.append(f"📊 共收录 **{len(rows)}** 家餐厅 ｜ 🕒 更新时间：{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")

# ⭐ 使用 HTML 表格，每列设置最小宽度防止被压缩
lines.append("""
<div style="overflow-x: auto;">

<table>
  <thead>
    <tr>
      <th style="min-width: 120px; text-align: left;">名称</th>
      <th style="min-width: 80px; text-align: left;">菜系</th>
      <th style="min-width: 80px; text-align: center;">人均</th>
      <th style="min-width: 130px; text-align: center;">推荐指数</th>
      <th style="min-width: 100px; text-align: left;">地址/链接</th>
      <th style="min-width: 180px; text-align: left;">营业时间</th>
      <th style="min-width: 120px; text-align: left;">联系方式</th>
      <th style="min-width: 70px; text-align: center;">预约</th>
      <th style="min-width: 80px; text-align: center;">排队</th>
      <th style="min-width: 80px; text-align: left;">标签</th>
      <th style="min-width: 150px; text-align: left;">备注</th>
    </tr>
  </thead>
  <tbody>
""")

for r in rows:
    url = (r.get("url") or "").strip()
    name_raw = esc(r.get("name", ""))
    if url:
        name = f'<a href="{url}">{name_raw}</a>'
    else:
        name = name_raw

    rating_val = parse_rating(r.get("rating", ""))
    stars = rating_to_stars(rating_val)
    rating_display = f"{stars} {rating_val:.1f}" if rating_val > 0 else "—"

    reservation = esc(r.get("reservation_needed", ""))
    if reservation.lower() in ("是", "yes", "需要"):
        reservation = "✅ 是"
    elif reservation:
        reservation = "❌ 否"

    queue = esc(r.get("queue_time", ""))
    if queue and queue != "":
        queue = f"⏱ {queue}"

    # 营业时间处理：保留换行，用 <br> 替代
    hours = esc(r.get("hours", ""))
    hours = hours.replace(";", ";<br>")

    lines.append(f"""
    <tr>
      <td style="min-width: 120px;">{name}</td>
      <td style="min-width: 80px;">{esc(r.get('cuisine', ''))}</td>
      <td style="min-width: 80px; text-align: center;">{esc(r.get('price', ''))}</td>
      <td style="min-width: 130px; text-align: center; white-space: nowrap;">{rating_display}</td>
      <td style="min-width: 100px;">{"🔗 <a href=\"" + url + "\">链接</a>" if url else ""}</td>
      <td style="min-width: 180px;">{hours}</td>
      <td style="min-width: 120px;">{esc(r.get('contact', ''))}</td>
      <td style="min-width: 70px; text-align: center;">{reservation}</td>
      <td style="min-width: 80px; text-align: center;">{queue}</td>
      <td style="min-width: 80px;">{esc(r.get('tags', ''))}</td>
      <td style="min-width: 150px;">{esc(r.get('notes', ''))}</td>
    </tr>
""")

lines.append("""
  </tbody>
</table>

</div>
""")

# 图例
lines.append("\n---\n\n")
lines.append("### 📌 图例说明\n\n")
lines.append("| 图标 | 含义 |\n")
lines.append("| :---: | --- |\n")
lines.append("| ★ | 推荐指数（★越多越推荐） |\n")
lines.append("| 🔗 | 地址/地图链接 |\n")
lines.append("| ✅ ❌ | 是否需要预约 |\n")
lines.append("| ⏱ | 排队时长 |\n")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"✅ Wrote {OUT_PATH} ({len(rows)} entries).")
