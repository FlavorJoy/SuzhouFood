#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
readme_render.py
读取 food-original.csv 并生成 README.md（覆盖写入）。
美观版：保持11列，增加星级、图标，提升可读性。
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
    return str(s).replace("|", "\\|").strip()


def parse_rating(s):
    try:
        return float(s)
    except Exception:
        return 0.0


def rating_to_stars(rating):
    """将评分转换为星级显示"""
    if rating is None or rating <= 0:
        return "—"
    full = int(round(rating))
    full = max(0, min(5, full))
    return "★" * full + "☆" * (5 - full)


def is_example_row(row):
    """判断是否为示例数据"""
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

# 标题和说明
lines.append("# 🍜 苏州美食推荐\n\n")
lines.append("> 📋 本文件由 `readme_render.py` 根据 `food-original.csv` 自动生成\n\n")
lines.append("> ✏️ 如需添加或修改餐厅，请编辑 `food-original.csv` 并提交 Pull Request\n\n")
lines.append(f"📊 共收录 **{len(rows)}** 家餐厅 ｜ 🕒 更新时间：{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")

# 表头（加粗、带图标）
lines.append("| 名称 | 菜系 | 人均 | 推荐指数 | 地址/链接 | 营业时间 | 联系方式 | 预约 | 排队 | 标签 | 备注 |\n")
lines.append("| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :---: | :---: | :--- | :--- |\n")

for r in rows:
    url = (r.get("url") or "").strip()
    name_raw = esc(r.get("name", ""))
    if url:
        name = f"[{name_raw}]({url})"
    else:
        name = name_raw

    # 推荐指数：星级 + 数值
    rating_val = parse_rating(r.get("rating", ""))
    stars = rating_to_stars(rating_val)
    rating_display = f"{stars} {rating_val:.1f}" if rating_val > 0 else "—"

    # 预约：加个图标
    reservation = esc(r.get("reservation_needed", ""))
    if reservation.lower() in ("是", "yes", "需要"):
        reservation = "✅ 是"
    elif reservation:
        reservation = "❌ 否"

    # 排队：加个图标
    queue = esc(r.get("queue_time", ""))
    if queue and queue != "":
        queue = f"⏱ {queue}"

    lines.append(
        "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |\n".format(
            name,
            esc(r.get("cuisine", "")),
            esc(r.get("price", "")),
            rating_display,
            f"🔗 [链接]({url})" if url else "",
            esc(r.get("hours", "")),
            esc(r.get("contact", "")),
            reservation,
            queue,
            esc(r.get("tags", "")),
            esc(r.get("notes", "")),
        )
    )

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
