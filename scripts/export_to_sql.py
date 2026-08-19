#!/usr/bin/env python3
"""
把 CSV 转成 INSERT 语句，输出到 data/food.sql
"""

import csv
import os
import sys
from datetime import datetime

CSV_PATH = os.getenv('CSV_PATH', 'data/food.csv')
SQL_PATH = os.getenv('SQL_PATH', 'data/food.sql')

print(f"读取 CSV：{CSV_PATH}")
print(f"生成 SQL：{SQL_PATH}")

# 确保输出目录存在
os.makedirs(os.path.dirname(SQL_PATH) or '.', exist_ok=True)

def safe_escape(val, field_name=None):
    """安全转义 SQL 值，处理 None 和空值"""
    if val is None:
        return 'NULL'
    
    val_str = str(val).strip()
    
    # 如果字段是数值类型，不添加引号
    if field_name and field_name.lower() in ['id', 'rating', 'price', 'cost', 'score']:
        if val_str == '':
            return 'NULL'
        # 检查是否是有效数字
        try:
            float(val_str)
            return val_str
        except ValueError:
            # 不是数字，按字符串处理
            pass
    
    # 空字符串或 'NULL' 字符串转为 SQL NULL
    if val_str == '' or val_str.upper() == 'NULL':
        return 'NULL'
    
    # 转义单引号和反斜杠
    escaped = val_str.replace('\\', '\\\\').replace("'", "''")
    return f"'{escaped}'"

try:
    # 检测文件编码
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'latin-1']
    csv_content = None
    
    for encoding in encodings:
        try:
            with open(CSV_PATH, newline='', encoding=encoding) as csvfile:
                reader = csv.DictReader(csvfile)
                fields = reader.fieldnames
                
                if not fields:
                    print(f"❌ CSV 文件没有列名: {CSV_PATH}", file=sys.stderr)
                    sys.exit(1)
                
                # 清理字段名
                fields = [f.strip() for f in fields]
                
                # 读取所有行，过滤空行
                rows = []
                for row in reader:
                    # 检查是否有任何非空值
                    if any(v and str(v).strip() for v in row.values()):
                        # 确保所有字段都存在
                        clean_row = {f: row.get(f, '').strip() for f in fields}
                        rows.append(clean_row)
                
                if not rows:
                    print(f"⚠️ 警告: CSV 文件为空或只有标题行: {CSV_PATH}", file=sys.stderr)
                
                print(f"✅ 使用编码: {encoding}")
                print(f"✅ 读取到 {len(rows)} 条记录")
                break
                
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"⚠️ 编码 {encoding} 失败: {e}")
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

# 生成 SQL
try:
    with open(SQL_PATH, 'w', encoding='utf-8') as sqlfile:
        # 写入头部
        sqlfile.write("-- ============================================\n")
        sqlfile.write("-- 生成自脚本：export_to_sql.py\n")
        sqlfile.write("-- 表名：suzhou_food\n")
        sqlfile.write(f"-- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sqlfile.write(f"-- 记录数：{len(rows)}\n")
        sqlfile.write("-- ============================================\n\n")
        
        if not rows:
            sqlfile.write("-- 无数据\n")
            print("⚠️ 没有生成任何 INSERT 语句")
        else:
            # 开始事务
            sqlfile.write("BEGIN;\n\n")
            
            # 生成 INSERT 语句
            for idx, row in enumerate(rows, 1):
                try:
                    # 处理每个字段
                    values = []
                    for f in fields:
                        val = row.get(f, '')
                        escaped_val = safe_escape(val, f)
                        values.append(escaped_val)
                    
                    # 使用反引号包裹字段名（MySQL 兼容）
                    fields_quoted = [f'`{f}`' for f in fields]
                    sqlfile.write(f"INSERT INTO suzhou_food ({', '.join(fields_quoted)}) VALUES ({', '.join(values)});\n")
                    
                    # 每 100 条加一个空行，提高可读性
                    if idx % 100 == 0:
                        sqlfile.write("\n")
                        
                except Exception as e:
                    print(f"⚠️ 处理第 {idx} 行时出错: {e}")
                    print(f"   行数据: {row}")
                    # 跳过错误行
                    continue
            
            # 提交事务
            sqlfile.write("\nCOMMIT;\n")
            
    print(f"✅ SQL 生成完成！共 {len(rows)} 条记录")
    print(f"📁 输出文件: {SQL_PATH}")
    
except Exception as e:
    print(f"❌ 写入 SQL 文件失败: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)