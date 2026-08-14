#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
readme_render.py
读取 food-original.csv 并生成 README.md（覆盖写入）。
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

if not os.path.exists(CSV_PATH):
    print(f"ERROR: {CSV_PATH} not found.", file=sys.stderr)
    sys.exit(1)

rows = []
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# 按 rating 降序排序（无法解析为数值的视为 0）
rows.sort(key=lambda r: parse_rating(r.get("rating", "")), reverse=True)

lines = []
lines.append("# 苏州美食推荐（自动生成）\n\n")
lines.append("本文件由 `readme_render.py` 根据 `food-original.csv` 自动生成。\n\n")
lines.append("如果要添加/修改餐厅，请编辑 `food-original.csv` 并提交 PR。\n\n")
lines.append("更新时间：{} UTC\n\n".format(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
lines.append("| 名称 | 菜系 | 人均/价格区间 | 推荐指数 | 地址/链接 | 营业时间 | 联系方式 | 是否需预约 | 排队时长 | 标签 | 备注 |\n")
lines.append("| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |\n")

for r in rows:
    url = (r.get("url") or "").strip()
    name_raw = esc(r.get("name", ""))
    if url:
        name = f"[{name_raw}]({url})"
    else:
        name = name_raw
    lines.append(
        "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |\n".format(
            name,
            esc(r.get("cuisine", "")),
            esc(r.get("price", "")),
            esc(r.get("rating", "")),
            url if url else "",
            esc(r.get("hours", "")),
            esc(r.get("contact", "")),
            esc(r.get("reservation_needed", "")),
            esc(r.get("queue_time", "")),
            esc(r.get("tags", "")),
            esc(r.get("notes", "")),
        )
    )

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"Wrote {OUT_PATH} ({len(rows)} entries).")
