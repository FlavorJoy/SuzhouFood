#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
readme_render.py
读取 food-original.csv 并生成 README.md（覆盖写入）。
优化版：合并次要信息列，增加星级显示，提升可读性。
"""

import csv
import datetime
import sys
import os

CSV_PATH = "food-original.csv"
OUT_PATH = "README.md"


def esc(s):
    """转义表格中的特殊字符，防止破坏 Markdown 表格格式"""
    if s is None:
        return ""
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def parse_rating(s):
    """解析评分，返回浮点数，失败返回 0.0"""
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def rating_to_stars(rating):
    """
    将评分转换为星级显示
    例如: 4.5 -> "★★★★☆ 4.5"
    例如: 3.0 -> "★★★☆☆ 3.0"
    例如: 0   -> "—"
    """
    if rating is None or rating <= 0:
        return "—"
    full = int(round(rating))
    full = max(0, min(5, full))
    empty = 5 - full
    return "★" * full + "☆" * empty


def format_info_parts(row):
    """将多个信息列合并为一个"关键信息"列"""
    parts = []

    url = (row.get("url") or "").strip()
    if url:
        parts.append(f"[📍]({url})")

    hours = (row.get("hours") or "").strip()
    if hours:
        parts.append(f"🕐{hours}")

    contact = (row.get("contact") or "").strip()
    if contact:
        parts.append(f"📞{contact}")

    reservation = (row.get("reservation_needed") or "").strip().lower()
    if reservation in ("yes", "是", "需要", "true", "1"):
        parts.append("📌需预约")

    queue = (row.get("queue_time") or "").strip()
    if queue:
        parts.append(f"⏳{queue}")

    return " ".join(parts) if parts else "—"


def is_example_row(row):
    """判断是否为示例数据（跳过包含"示例"的行）"""
    name = (row.get("name") or "").strip()
    notes = (row.get("notes") or "").strip()
    # 如果名称或备注包含"示例"，认为是测试数据
    if "示例" in name or "示例" in notes:
        return True
    return False


def build_table_row(row):
    """构建单行表格数据"""
    name_raw = esc(row.get("name", ""))
    url = (row.get("url") or "").strip()

    if url:
        name = f"[{name_raw}]({url})"
    else:
        name = name_raw

    rating_val = parse_rating(row.get("rating", ""))
    stars = rating_to_stars(rating_val)

    return {
        "stars_display": f"{stars} {rating_val:.1f}" if rating_val > 0 else "—",
        "name": name,
        "cuisine": esc(row.get("cuisine", "")),
        "price": esc(row.get("price", "")),
        "info": format_info_parts(row),
        "tags": esc(row.get("tags", "")),
        "notes": esc(row.get("notes", "")),
    }


def main():
    if not os.path.exists(CSV_PATH):
        print(f"❌ 错误: {CSV_PATH} 文件不存在", file=sys.stderr)
        sys.exit(1)

    # 读取 CSV，过滤掉示例数据
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not is_example_row(row):  # 👈 跳过示例行
                rows.append(row)

    if not rows:
        print("⚠️ 警告: 没有找到有效的餐厅数据（已过滤示例数据）", file=sys.stderr)
        # 仍然生成 README，但显示空表格
    else:
        print(f"📊 读取到 {len(rows)} 家餐厅（已过滤示例数据）")

    # 按 rating 降序排序
    rows.sort(key=lambda r: parse_rating(r.get("rating", "")), reverse=True)

    # 构建输出
    lines = []
    lines.append("# 🍜 苏州美食推荐\n\n")
    lines.append(
        "> 📋 本文件由 `readme_render.py` 根据 `food-original.csv` 自动生成。\n\n"
    )
    lines.append(
        "> ✏️ 如需添加或修改餐厅，请编辑 `food-original.csv` 并提交 Pull Request。\n\n"
    )

    now_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"🕒 最后更新: {now_utc} UTC\n\n")
    lines.append(f"📊 共收录 **{len(rows)}** 家餐厅\n\n")

    lines.append(
        "| 推荐指数 | 餐厅名称 | 菜系 | 人均 | 关键信息 | 标签 |\n"
    )
    lines.append(
        "| :---: | --- | --- | :---: | --- | --- |\n"
    )

    for r in rows:
        data = build_table_row(r)
        lines.append(
            "| {} | {} | {} | {} | {} | {} |\n".format(
                data["stars_display"],
                data["name"],
                data["cuisine"],
                data["price"],
                data["info"],
                data["tags"],
            )
        )

    lines.append("\n---\n\n")
    lines.append("### 📌 图例说明\n\n")
    lines.append("| 图标 | 含义 |\n")
    lines.append("| :---: | --- |\n")
    lines.append("| 📍 | 地图/地址链接 |\n")
    lines.append("| 🕐 | 营业时间 |\n")
    lines.append("| 📞 | 联系电话 |\n")
    lines.append("| 📌 | 需要预约 |\n")
    lines.append("| ⏳ | 排队时长 |\n")
    lines.append("| ★ | 推荐指数（★越多越好） |\n")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"✅ 已生成 {OUT_PATH}")


if __name__ == "__main__":
    main()
