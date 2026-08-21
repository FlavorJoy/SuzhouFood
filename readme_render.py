#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
README Renderer - 从CSV生成美观的README.md
支持完整的数据展示，包含统计信息、图表和交互式筛选
"""

import csv
import datetime
import sys
import os
import re
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

# ============================================
# 配置参数
# ============================================
CSV_PATH = os.getenv('CSV_PATH', 'food-original.csv')
OUT_PATH = os.getenv('README_PATH', 'README.md')
MAX_TOP_RATED = int(os.getenv('MAX_TOP_RATED', '5'))


# ============================================
# 工具函数
# ============================================

def esc(s: Optional[str]) -> str:
    """转义Markdown特殊字符"""
    if s is None:
        return ""
    s = str(s)
    # 替换表格分隔符
    s = s.replace("|", "\\|")
    # 替换换行符为空格
    s = s.replace("\n", " ").replace("\r", "")
    # 替换HTML标签
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    return s.strip()


def parse_rating(s: Optional[str]) -> float:
    """解析评分"""
    if s is None:
        return 0.0
    try:
        return float(str(s).strip())
    except (ValueError, TypeError):
        return 0.0


def rating_to_stars(rating: Optional[float]) -> str:
    """将评分转换为星级显示"""
    if rating is None or rating <= 0:
        return "—"
    full = int(round(rating))
    full = max(0, min(5, full))
    return "★" * full + "☆" * (5 - full)


def parse_price(price_str: Optional[str]) -> Optional[float]:
    """解析价格，提取数值"""
    if not price_str:
        return None
    price_str = str(price_str).strip()
    # 提取数字
    numbers = re.findall(r'[\d.]+', price_str)
    if not numbers:
        return None
    # 取第一个数字
    return float(numbers[0])


def get_price_range(price_str: Optional[str]) -> str:
    """获取价格区间分类"""
    if not price_str:
        return "价格待定"
    price_str = str(price_str).strip()

    # 提取所有数字
    numbers = re.findall(r'[\d.]+', price_str)
    if not numbers:
        return "价格待定"

    # 取平均值（如果有范围）
    nums = [float(n) for n in numbers]
    avg_price = sum(nums) / len(nums)

    if avg_price < 30:
        return "¥30以下"
    elif avg_price < 60:
        return "¥30-60"
    elif avg_price < 100:
        return "¥60-100"
    else:
        return "¥100以上"


def is_example_row(row: Dict[str, str]) -> bool:
    """判断是否为示例行"""
    name = (row.get("name") or "").strip()
    notes = (row.get("notes") or "").strip()
    return "示例" in name or "示例" in notes


def format_hours(hours: Optional[str]) -> str:
    """格式化营业时间，用<br>替代分号换行"""
    if not hours or hours.strip().upper() == 'NULL':
        return ""
    return hours.strip().replace(";", "<br>")


def get_cuisine_stats(rows: List[Dict]) -> List[Tuple[str, int]]:
    """统计菜系数据"""
    stats = defaultdict(int)
    for r in rows:
        cuisine = (r.get("cuisine") or "").strip()
        if cuisine:
            stats[cuisine] += 1
    return sorted(stats.items(), key=lambda x: x[1], reverse=True)


def get_top_rated(rows: List[Dict], limit: int = 5) -> List[Dict]:
    """获取评分最高的餐厅"""
    sorted_rows = sorted(
        rows,
        key=lambda r: parse_rating(r.get("rating", "")),
        reverse=True
    )
    return sorted_rows[:limit]


def get_queue_time_avg(rows: List[Dict]) -> float:
    """计算平均排队时间（CSV中已无此列，返回0）"""
    # CSV中已删除 queue_time 列
    return 0.0


def get_current_beijing_time() -> datetime.datetime:
    """获取当前北京时间（使用推荐的时区感知方法）"""
    try:
        # Python 3.11+ 推荐方式
        from datetime import UTC
        return datetime.datetime.now(UTC) + datetime.timedelta(hours=8)
    except ImportError:
        # Python 3.10 及以下兼容方式
        try:
            from datetime import timezone
            return datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=8)
        except ImportError:
            # 最后的兼容方案
            return datetime.datetime.utcnow() + datetime.timedelta(hours=8)


def generate_progress_bar(percentage: float, width: int = 20) -> str:
    """生成进度条"""
    filled = int(percentage / 100 * width)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def generate_statistics(rows: List[Dict]) -> Dict[str, Any]:
    """生成统计信息"""
    total = len(rows)
    ratings = [parse_rating(r.get("rating", "")) for r in rows]
    avg_rating = sum(ratings) / total if total > 0 else 0.0

    # 菜系统计
    cuisine_stats = get_cuisine_stats(rows)

    # 价格分布
    price_dist = defaultdict(int)
    for r in rows:
        price_range = get_price_range(r.get("price", ""))
        price_dist[price_range] += 1

    # 高分餐厅
    top_rated = get_top_rated(rows, MAX_TOP_RATED)

    # 平均排队时间（已删除该列）
    avg_queue = 0.0

    return {
        'total': total,
        'avg_rating': avg_rating,
        'cuisine_stats': cuisine_stats,
        'price_dist': price_dist,
        'top_rated': top_rated,
        'avg_queue': avg_queue,
        'max_rating': max(ratings) if ratings else 0.0,
        'min_rating': min(ratings) if ratings else 0.0,
    }


def generate_stats_markdown(stats: Dict[str, Any]) -> List[str]:
    """生成统计信息的Markdown"""
    lines = []

    # 统计卡片
    lines.append("## 📊 数据统计\n\n")
    lines.append("| 指标 | 数值 |\n")
    lines.append("| :--- | ---: |\n")
    lines.append(f"| 📝 餐厅总数 | **{stats['total']}** 家 |\n")
    lines.append(f"| ⭐ 平均评分 | **{stats['avg_rating']:.2f}** / 5.0 |\n")
    if stats['total'] > 0:
        lines.append(f"| 🔼 最高评分 | **{stats['max_rating']:.1f}** / 5.0 |\n")
        lines.append(f"| 🔽 最低评分 | **{stats['min_rating']:.1f}** / 5.0 |\n")
    lines.append("\n")

    # 菜系统计
    if stats['cuisine_stats']:
        lines.append("### 🍽️ 菜系分布\n\n")
        lines.append("| 菜系 | 数量 | 占比 |\n")
        lines.append("| :--- | ---: | ---: |\n")
        for cuisine, count in stats['cuisine_stats']:
            percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
            bar = generate_progress_bar(percentage)
            lines.append(f"| {cuisine} | {count} | {percentage:.1f}% {bar} |\n")
        lines.append("\n")

    # 价格分布
    if any(stats['price_dist'].values()):
        lines.append("### 💰 价格分布\n\n")
        lines.append("| 价格区间 | 数量 | 占比 |\n")
        lines.append("| :--- | ---: | ---: |\n")
        price_order = ["¥30以下", "¥30-60", "¥60-100", "¥100以上", "价格待定"]
        for price_range in price_order:
            count = stats['price_dist'].get(price_range, 0)
            if count > 0:
                percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
                bar = generate_progress_bar(percentage)
                lines.append(f"| {price_range} | {count} | {percentage:.1f}% {bar} |\n")
        lines.append("\n")

    # 高分推荐
    if stats['top_rated']:
        lines.append(f"### 🏆 高分推荐（Top {MAX_TOP_RATED}）\n\n")
        lines.append("| 排名 | 名称 | 菜系 | 评分 | 价格 |\n")
        lines.append("| :---: | :--- | :--- | :---: | :--- |\n")
        for idx, r in enumerate(stats['top_rated'], 1):
            name = esc(r.get("name", ""))
            cuisine = esc(r.get("cuisine", ""))
            rating = parse_rating(r.get("rating", ""))
            price = esc(r.get("price", ""))
            stars = rating_to_stars(rating)
            lines.append(f"| {idx} | {name} | {cuisine} | {stars} {rating:.1f} | {price} |\n")
        lines.append("\n")

    return lines


def generate_main_table(rows: List[Dict]) -> List[str]:
    """生成主表格（精简版）"""
    lines = []
    lines.append("## 📋 餐厅列表\n\n")
    lines.append("| 名称 | 菜系 | 人均 | 推荐指数 | 营业时间 |\n")
    lines.append("| :--- | :--- | :---: | :---: | :--- |\n")

    for r in rows:
        url = (r.get("url") or "").strip()
        name_raw = esc(r.get("name", ""))
        name = f"[{name_raw}]({url})" if url else name_raw

        rating_val = parse_rating(r.get("rating", ""))
        stars = rating_to_stars(rating_val)
        rating_display = f"{stars} {rating_val:.1f}" if rating_val > 0 else "—"

        hours = format_hours(esc(r.get("hours", "")))

        lines.append(
            f"| {name} | {esc(r.get('cuisine', ''))} | "
            f"{esc(r.get('price', ''))} | {rating_display} | "
            f"{hours} |\n"
        )

    return lines


def generate_detail_table(rows: List[Dict]) -> List[str]:
    """生成详细信息表格（折叠）"""
    lines = []
    lines.append("\n<details>\n")
    lines.append("<summary>📖 点击展开详细信息（备注/推荐菜）</summary>\n\n")

    lines.append("| 名称 | 备注/推荐菜 |\n")
    lines.append("| :--- | :--- |\n")

    for r in rows:
        url = (r.get("url") or "").strip()
        name_raw = esc(r.get("name", ""))
        name = f"[{name_raw}]({url})" if url else name_raw

        notes = esc(r.get("notes", "")) or "—"

        lines.append(f"| {name} | {notes} |\n")

    lines.append("\n</details>\n")
    return lines


def generate_search_guide() -> List[str]:
    """生成搜索和使用指南"""
    lines = []
    lines.append("## 🔍 如何使用\n\n")
    lines.append("### 方式一：直接浏览\n")
    lines.append("1. 浏览下方的餐厅列表\n")
    lines.append("2. 点击餐厅名称可查看高德地图详情\n")
    lines.append("3. 点击 📖 展开查看详细信息\n\n")

    lines.append("### 方式二：数据库查询\n")
    lines.append("如需进行复杂查询，可以使用生成的SQL文件导入数据库：\n\n")
    lines.append("```bash\n")
    lines.append(f"mysql -u root -p < food.sql\n")
    lines.append("```\n\n")

    lines.append("### 方式三：关键词搜索\n")
    lines.append("在浏览器中使用 `Ctrl+F` 搜索关键词（如：\"烧烤\"、\"火锅\"、\"湘菜\"）\n\n")

    return lines


def generate_legend() -> List[str]:
    """生成图例"""
    lines = []
    lines.append("\n---\n\n")
    lines.append("## 📌 图例说明\n\n")
    lines.append("| 图标 | 含义 |\n")
    lines.append("| :---: | --- |\n")
    lines.append("| ★★★★★ | 推荐指数（★越多越推荐） |\n")
    lines.append("| 📖 | 点击展开详细信息 |\n")
    lines.append("| 📊 | 数据统计 |\n")
    lines.append("| 🏆 | 高分推荐 |\n")
    return lines


def generate_footer() -> List[str]:
    """生成页脚"""
    lines = []
    lines.append("\n---\n\n")
    lines.append("## 📝 贡献指南\n\n")
    lines.append("1. Fork 本仓库\n")
    lines.append("2. 编辑 `food-original.csv` 文件\n")
    lines.append("3. 运行 `python readme_render.py` 更新 README\n")
    lines.append("4. 运行 `python export_to_sql.py` 更新 SQL 文件\n")
    lines.append("5. 提交 Pull Request\n\n")

    lines.append("### CSV格式说明\n\n")
    lines.append("| 字段 | 说明 | 示例 |\n")
    lines.append("| :--- | :--- | :--- |\n")
    lines.append("| name | 餐厅名称 | 哑巴生煎(临顿路店) |\n")
    lines.append("| cuisine | 菜系 | 苏菜 |\n")
    lines.append("| price | 人均价格 | ¥28/人 |\n")
    lines.append("| rating | 评分(0-5) | 4.7 |\n")
    lines.append("| url | 高德地图链接 | https://surl.amap.com/xxx |\n")
    lines.append("| hours | 营业时间 | 6:30-19:30 |\n")
    lines.append("| notes | 备注/推荐菜 | 生煎 牛肉粉丝汤 |\n")

    return lines


def read_csv_data(csv_path: str) -> List[Dict]:
    """读取CSV数据"""
    rows = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not is_example_row(row):
                    rows.append(row)
    except FileNotFoundError:
        print(f"❌ 错误: {csv_path} 文件不存在", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 读取CSV文件错误: {e}", file=sys.stderr)
        sys.exit(1)

    return rows


def main():
    """主函数"""
    print("=" * 60)
    print("📝 README生成工具")
    print("=" * 60)
    print(f"📂 CSV文件: {CSV_PATH}")
    print(f"📄 README文件: {OUT_PATH}")
    print("=" * 60)

    # 读取CSV
    rows = read_csv_data(CSV_PATH)

    if not rows:
        print("⚠️ 警告: 没有有效数据（可能只有示例行）")

    # 按评分排序
    rows.sort(key=lambda r: parse_rating(r.get("rating", "")), reverse=True)

    print(f"✅ 读取成功: {len(rows)} 条有效记录")

    # 生成统计数据
    stats = generate_statistics(rows)

    # 生成README内容
    lines = []

    # 标题和头部
    lines.append("# 🍜 苏州美食推荐\n\n")
    lines.append("> 📋 本文件由 `readme_render.py` 根据 `food-original.csv` 自动生成\n\n")
    lines.append("> ✏️ 如需添加或修改餐厅，请编辑 `food-original.csv` 并提交 Pull Request\n\n")

    # 更新时间
    beijing_time = get_current_beijing_time()
    lines.append(
        f"📊 共收录 **{len(rows)}** 家餐厅 ｜ "
        f"🕒 更新于·北京时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')} CST\n\n"
    )

    # 目录
    lines.append("## 📑 目录\n\n")
    lines.append("- [📊 数据统计](#-数据统计)\n")
    lines.append("- [📋 餐厅列表](#-餐厅列表)\n")
    lines.append("- [📖 详细信息](#-点击展开详细信息备注推荐菜)\n")
    lines.append("- [🔍 如何使用](#-如何使用)\n")
    lines.append("- [📌 图例说明](#-图例说明)\n")
    lines.append("- [📝 贡献指南](#-贡献指南)\n\n")

    # 统计信息
    lines.extend(generate_stats_markdown(stats))

    # 主表格
    lines.extend(generate_main_table(rows))

    # 详细信息（折叠）
    lines.extend(generate_detail_table(rows))

    # 使用指南
    lines.extend(generate_search_guide())

    # 图例
    lines.extend(generate_legend())

    # 页脚
    lines.extend(generate_footer())

    # 写入文件
    try:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"✅ README生成成功: {OUT_PATH} ({len(rows)} 条记录)")
    except Exception as e:
        print(f"❌ 写入README文件错误: {e}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)

    # 打印统计摘要
    print("\n📊 统计摘要:")
    print(f"  - 餐厅总数: {stats['total']}")
    print(f"  - 平均评分: {stats['avg_rating']:.2f}")
    print(f"  - 最高评分: {stats['max_rating']:.1f}")
    print(f"  - 最低评分: {stats['min_rating']:.1f}")
    print(f"  - 菜系种类: {len(stats['cuisine_stats'])} 种")

    # 打印菜系分布
    if stats['cuisine_stats']:
        print("\n  🍽️ 菜系分布:")
        for cuisine, count in stats['cuisine_stats'][:5]:
            print(f"    - {cuisine}: {count} 家")
        if len(stats['cuisine_stats']) > 5:
            print(f"    ... 还有 {len(stats['cuisine_stats']) - 5} 种菜系")

    print("\n💡 提示: 可以使用 `python export_to_sql.py` 生成数据库安装脚本")


if __name__ == "__main__":
    main()