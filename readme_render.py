#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
readme_render.py
读取 food-original.csv 并生成 README.md（覆盖写入）。
优化版：拆分表格 + 换行处理，适配GitHub显示。
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


def format_hours(hours):
    """格式化营业时间，用<br>替代分号换行"""
    if not hours:
        return ""
    return hours.strip().replace(";", "<br>")


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
beijing_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
lines.append(f"📊 共收录 **{len(rows)}** 家餐厅 ｜ 🕒 更新于·北京时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} CST\n\n")

# ========== 核心表格（精简为7列，减少横向压缩） ==========
lines.append("## 📋 餐厅列表\n\n")
lines.append("| 名称 | 菜系 | 人均 | 推荐指数 | 营业时间 | 预约 | 标签 |\n")
lines.append("| :--- | :--- | :---: | :---: | :--- | :---: | :--- |\n")

for r in rows:
    url = (r.get("url") or "").strip()
    name_raw = esc(r.get("name", ""))
    if url:
        name = f"[{name_raw}]({url})"
    else:
        name = name_raw

    rating_val = parse_rating(r.get("rating", ""))
    stars = rating_to_stars(rating_val)
    rating_display = f"{stars} {rating_val:.1f}" if rating_val > 0 else "—"

    reservation = esc(r.get("reservation_needed", ""))
    if reservation.lower() in ("是", "yes", "需要"):
        reservation = "✅"
    elif reservation:
        reservation = "❌"
    else:
        reservation = "—"

    hours = format_hours(esc(r.get("hours", "")))

    lines.append(
        "| {} | {} | {} | {} | {} | {} | {} |\n".format(
            name,
            esc(r.get("cuisine", "")),
            esc(r.get("price", "")),
            rating_display,
            hours,
            reservation,
            esc(r.get("tags", "")),
        )
    )

# ========== 详细信息（折叠块） ==========
lines.append("\n<details>\n")
lines.append("<summary>📖 点击展开详细信息（联系方式、地址、排队、备注）</summary>\n\n")

lines.append("| 名称 | 联系方式 | 地址/链接 | 排队时长 | 备注 |\n")
lines.append("| :--- | :--- | :--- | :---: | :--- |\n")

for r in rows:
    url = (r.get("url") or "").strip()
    name_raw = esc(r.get("name", ""))
    if url:
        name = f"[{name_raw}]({url})"
    else:
        name = name_raw

    queue = esc(r.get("queue_time", ""))
    if queue:
        queue = f"⏱ {queue}"
    else:
        queue = "—"

    lines.append(
        "| {} | {} | {} | {} | {} |\n".format(
            name,
            esc(r.get("contact", "")),
            url if url else "—",
            queue,
            esc(r.get("notes", "")),
        )
    )

lines.append("\n</details>\n")

# ========== 图例 ==========
lines.append("\n---\n\n")
lines.append("### 📌 图例说明\n\n")
lines.append("| 图标 | 含义 |\n")
lines.append("| :---: | --- |\n")
lines.append("| ★★★★★ | 推荐指数（★越多越推荐） |\n")
lines.append("| ✅ | 需要预约 |\n")
lines.append("| ❌ | 无需预约 |\n")
lines.append("| ⏱ | 排队时长 |\n")
lines.append("| 📖 | 点击展开详细信息 |\n")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"✅ Wrote {OUT_PATH} ({len(rows)} entries).")
