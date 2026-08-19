#!/usr/bin/env python3
"""
把 CSV 转成 INSERT 语句，输出到 data/food.sql，并生成 CREATE TABLE 语句。
"""

import csv
import os
import sys
from datetime import datetime

# ---------------------------------------------
# 配置
# ---------------------------------------------
CSV_PATH = os.getenv('CSV_PATH', 'food-original.csv')
SQL_PATH = os.getenv('SQL_PATH', 'data/food.sql')

print(f"读取 CSV：{CSV_PATH}")
print(f"生成 SQL：{SQL_PATH}")

# 确保输出目录存在
os.makedirs(os.path.dirname(SQL_PATH) or '.', exist_ok=True)

# ---------------------------------------------
# SQL 值安全转义
# ---------------------------------------------

def safe_escape(val, field_name=None):
    """安全转义 SQL 值，处理 None 和空值"""
    if val is None:
        return 'NULL'
    val_str = str(val).strip()
    # 把数值字段直接输出
    if field_name and field_name.lower() in ["id", "rating", "price"]:
        if val_str == '':
            return 'NULL'
        try:
            # 若包含分隔符如￥或/不应视为数值，跳过转义
            if any(ch in val_str for ch in ['￥', '/', '–']):
                raise ValueError
            float(val_str)
            return val_str
        except Exception:
            pass
    if val_str == '' or val_str.upper() == 'NULL':
        return 'NULL'
    escaped = val_str.replace('\\', '\\\\').replace("'", "''")
    return f"'{escaped}'"

# ---------------------------------------------
# 读取 CSV
# ---------------------------------------------

try:
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'latin-1']
    csv_content = None
    for enc in encodings:
        try:
            with open(CSV_PATH, newline='', encoding=enc) as csvfile:
                reader = csv.DictReader(csvfile)
                fields = reader.fieldnames
                if not fields:
                    print(f"❌ CSV 文件没有列名: {CSV_PATH}", file=sys.stderr)
                    sys.exit(1)
                fields = [f.strip() for f in fields]
                rows = []
                for row in reader:
                    if any(v and str(v).strip() for v in row.values()):
                        clean_row = {f: row.get(f, '').strip() for f in fields}
                        rows.append(clean_row)
                if not rows:
                    print(f"⚠️ 警告: CSV 文件为空或只有标题行: {CSV_PATH}", file=sys.stderr)
                print(f"✅ 使用编码: {enc}")
                print(f"✅ 读取到 {len(rows)} 条记录")
                break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"⚠️ 编码 {enc} 失败: {e}")
            continue
    else:
        print(f"❌ 无法解码 CSV 文件，尝试过的编码: {encodings}", file=sys.stderr)
        sys.exit(1)
except FileNotFoundError:
    print(f"❌ CSV 文件不存在: {CSV_PATH}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"❌ 读取 CSV 文件失败: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ---------------------------------------------
# 写入 SQL
# ---------------------------------------------

try:
    with open(SQL_PATH, 'w', encoding='utf-8') as sqlfile:
        # 写入头部注释
        sqlfile.write("-- ============================================\n")
        sqlfile.write("-- 生成自脚本：export_to_sql.py\n")
        sqlfile.write("-- 表名：suzhou_food\n")
        sqlfile.write(f"-- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sqlfile.write(f"-- 记录数：{len(rows)}\n")
        sqlfile.write("-- ============================================\n\n")

        # 创建表结构（单独写）
        sqlfile.write("CREATE TABLE IF NOT EXISTS `suzhou_food` (\n")
        sqlfile.write("  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,\n")
        sqlfile.write("  `name` TEXT,\n")
        sqlfile.write("  `cuisine` TEXT,\n")
        sqlfile.write("  `price` TEXT,\n")
        sqlfile.write("  `rating` DECIMAL(3,2),\n")
        sqlfile.write("  `url` TEXT,\n")
        sqlfile.write("  `hours` TEXT,\n")
        sqlfile.write("  `contact` TEXT,\n")
        sqlfile.write("  `reservation_needed` TEXT,\n")
        sqlfile.write("  `queue_time` TEXT,\n")
        sqlfile.write("  `tags` TEXT,\n")
        sqlfile.write("  `notes` TEXT\n")
        sqlfile.write(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n\n")

        if not rows:
            sqlfile.write("-- 无数据\n")
            print("⚠️ 没有生成任何 INSERT 语句")
        else:
            sqlfile.write("BEGIN;\n\n")
            for idx, row in enumerate(rows, 1):
                try:
                    values = []
                    for field in fields:
                        val = row.get(field, '')
                        values.append(safe_escape(val, field))
                    fields_quoted = [f'`{f}`' for f in fields]
                    sqlfile.write(f"INSERT INTO suzhou_food ({', '.join(fields_quoted)}) VALUES ({', '.join(values)});\n")
                    if idx % 100 == 0:
                        sqlfile.write("\n")
                except Exception as e:
                    print(f"⚠️ 处理第 {idx} 行时出错: {e}")
                    print(f"   行数据: {row}")
                    continue
            sqlfile.write("\nCOMMIT;\n")
    print(f"✅ SQL 生成完成！共 {len(rows)} 条记录")
    print(f"📁 输出文件: {SQL_PATH}")
except Exception as e:
    print(f"❌ 写入 SQL 文件失败: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
