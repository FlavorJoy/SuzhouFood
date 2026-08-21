#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV to SQL Converter - 生成完整的MySQL数据库安装脚本
读取CSV文件，生成包含数据库创建、表结构、数据导入的完整SQL脚本
"""

import csv
import os
import sys
from datetime import datetime

# ============================================
# 配置参数
# ============================================
CSV_PATH = os.getenv('CSV_PATH', 'food-original.csv')
SQL_PATH = os.getenv('SQL_PATH', 'data/food.sql')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'suzhou_food_db')
TABLE_NAME = os.getenv('TABLE_NAME', 'suzhou_food')


# ============================================
# 核心函数
# ============================================

def escape_sql_value(val):
    """转义SQL字符串值"""
    if val is None or str(val).strip() == '' or str(val).strip().upper() == 'NULL':
        return 'NULL'
    val = str(val)
    # 处理特殊字符
    escaped = val.replace('\\', '\\\\').replace("'", "''")
    return f"'{escaped}'"


def detect_column_type(column_name, sample_values):
    """
    根据字段名和样本数据推断合适的MySQL数据类型
    """
    # 根据字段名推断
    if column_name == 'id':
        return 'INT UNSIGNED NOT NULL AUTO_INCREMENT'
    elif column_name in ['rating']:
        return 'DECIMAL(3,2) DEFAULT NULL'
    elif column_name in ['name']:
        return 'VARCHAR(100) NOT NULL'
    elif column_name in ['cuisine']:
        return 'VARCHAR(50) DEFAULT NULL'
    elif column_name in ['price']:
        return 'VARCHAR(50) DEFAULT NULL'
    elif column_name in ['url']:
        return 'VARCHAR(500) DEFAULT NULL'
    elif column_name in ['hours']:
        return 'VARCHAR(200) DEFAULT NULL'
    elif column_name in ['notes']:
        return 'TEXT DEFAULT NULL'
    elif column_name in ['created_at', 'updated_at']:
        return 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'
    else:
        # 根据样本数据推断
        max_len = 0
        has_null = False
        for val in sample_values:
            if val is None or str(val).strip() == '':
                has_null = True
                continue
            max_len = max(max_len, len(str(val)))

        if max_len > 500:
            return 'TEXT DEFAULT NULL'
        elif max_len > 200:
            return f'VARCHAR({min(max_len + 50, 1000)}) DEFAULT NULL'
        else:
            return f'VARCHAR({max(50, min(max_len + 20, 255))}) DEFAULT NULL'


def generate_create_table_sql(fields, rows):
    """生成CREATE TABLE语句"""
    lines = []
    lines.append(f"CREATE TABLE `{TABLE_NAME}` (")

    # 添加字段定义
    field_defs = []

    # 主键字段
    field_defs.append("    -- 主键")
    field_defs.append("    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID'")
    field_defs.append("")
    field_defs.append("    -- 基础信息")

    # 数据字段
    for field in fields:
        sample_values = [row.get(field, '') for row in rows[:100]]  # 取前100行作为样本
        col_type = detect_column_type(field, sample_values)
        comment = field.replace('_', ' ').title()

        # 特殊字段添加注释
        if field == 'name':
            comment = '餐厅/美食名称'
        elif field == 'cuisine':
            comment = '菜系/口味分类'
        elif field == 'price':
            comment = '价格区间或人均消费'
        elif field == 'rating':
            comment = '评分（满分5.0）'
        elif field == 'url':
            comment = '高德地图链接'
        elif field == 'hours':
            comment = '营业时间'
        elif field == 'notes':
            comment = '推荐菜品/备注'

        field_defs.append(f"    `{field}` {col_type} COMMENT '{comment}'")

    # 系统字段
    field_defs.append("")
    field_defs.append("    -- 系统字段")
    field_defs.append("    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'")
    field_defs.append(
        "    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'")

    # 主键和索引
    field_defs.append("")
    field_defs.append("    -- 索引")
    field_defs.append("    PRIMARY KEY (`id`)")
    field_defs.append("    INDEX `idx_name` (`name`)")
    field_defs.append("    INDEX `idx_cuisine` (`cuisine`)")
    field_defs.append("    INDEX `idx_rating` (`rating`)")

    lines.append(",\n".join(field_defs))
    lines.append(f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='苏州美食推荐表'")

    return "\n".join(lines)


def generate_insert_sql(rows, fields):
    """生成INSERT语句（批量插入）"""
    if not rows:
        return "-- 无数据插入"

    lines = []
    lines.append("BEGIN;")
    lines.append("")

    # 使用批量插入提高效率（每50条一批）
    batch_size = 50
    fields_quoted = [f'`{f}`' for f in fields]

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        values_list = []

        for row in batch:
            values = []
            for f in fields:
                val = row.get(f, '')
                values.append(escape_sql_value(val))
            values_list.append(f"({', '.join(values)})")

        sql = f"INSERT INTO `{TABLE_NAME}` ({', '.join(fields_quoted)}) VALUES\n    {',\n    '.join(values_list)};"
        lines.append(sql)
        lines.append("")

    lines.append("COMMIT;")
    return "\n".join(lines)


def generate_validation_queries():
    """生成数据验证查询"""
    return """
-- ============================================
-- 5. 数据验证查询（可选）
-- ============================================

-- 查看导入记录数
SELECT COUNT(*) AS total_records FROM `{TABLE_NAME}`;

-- 按菜系统计
SELECT 
    `cuisine`,
    COUNT(*) AS count,
    ROUND(AVG(`rating`), 2) AS avg_rating
FROM `{TABLE_NAME}`
WHERE `cuisine` IS NOT NULL
GROUP BY `cuisine`
ORDER BY count DESC;

-- 高评分推荐（4.8分以上）
SELECT `name`, `cuisine`, `rating`, `price`, `notes`
FROM `{TABLE_NAME}`
WHERE `rating` >= 4.8
ORDER BY `rating` DESC;

-- 按价格区间分类
SELECT 
    CASE 
        WHEN `price` REGEXP '^¥[0-9]+$' AND CAST(REPLACE(`price`, '¥', '') AS UNSIGNED) < 30 THEN '¥30以下'
        WHEN `price` REGEXP '^¥[0-9]+$' AND CAST(REPLACE(`price`, '¥', '') AS UNSIGNED) BETWEEN 30 AND 60 THEN '¥30-60'
        WHEN `price` REGEXP '^¥[0-9]+$' AND CAST(REPLACE(`price`, '¥', '') AS UNSIGNED) BETWEEN 60 AND 100 THEN '¥60-100'
        WHEN `price` REGEXP '^¥[0-9]+$' AND CAST(REPLACE(`price`, '¥', '') AS UNSIGNED) > 100 THEN '¥100以上'
        ELSE '价格待定'
    END AS price_range,
    COUNT(*) AS count
FROM `{TABLE_NAME}`
GROUP BY price_range
ORDER BY price_range;
""".format(TABLE_NAME=TABLE_NAME)


def generate_views():
    """生成常用视图"""
    return """
-- ============================================
-- 6. 创建视图（方便常用查询）
-- ============================================

-- 创建高分美食视图
CREATE OR REPLACE VIEW `v_high_rating_food` AS
SELECT 
    `id`, `name`, `cuisine`, `price`, `rating`, `notes`
FROM `{TABLE_NAME}`
WHERE `rating` >= 4.5
ORDER BY `rating` DESC;

-- 创建按菜系分组统计视图
CREATE OR REPLACE VIEW `v_cuisine_stats` AS
SELECT 
    `cuisine`,
    COUNT(*) AS total_count,
    ROUND(AVG(`rating`), 2) AS avg_rating,
    MAX(`rating`) AS max_rating,
    MIN(`rating`) AS min_rating
FROM `{TABLE_NAME}`
WHERE `cuisine` IS NOT NULL
GROUP BY `cuisine`
ORDER BY total_count DESC;
""".format(TABLE_NAME=TABLE_NAME)


def generate_stored_procedures():
    """生成存储过程"""
    return """
-- ============================================
-- 7. 创建存储过程（方便数据管理）
-- ============================================

DELIMITER //

-- 按评分范围查询美食
CREATE PROCEDURE `sp_get_food_by_rating`(
    IN min_rating DECIMAL(3,2),
    IN max_rating DECIMAL(3,2)
)
BEGIN
    SELECT `name`, `cuisine`, `price`, `rating`, `notes`
    FROM `{TABLE_NAME}`
    WHERE `rating` BETWEEN min_rating AND max_rating
    ORDER BY `rating` DESC;
END //

-- 按菜系查询美食
CREATE PROCEDURE `sp_get_food_by_cuisine`(
    IN cuisine_name VARCHAR(50)
)
BEGIN
    SELECT `name`, `price`, `rating`, `notes`
    FROM `{TABLE_NAME}`
    WHERE `cuisine` = cuisine_name
    ORDER BY `rating` DESC;
END //

-- 搜索美食（支持名称和备注模糊搜索）
CREATE PROCEDURE `sp_search_food`(
    IN keyword VARCHAR(100)
)
BEGIN
    SELECT `name`, `cuisine`, `price`, `rating`, `notes`
    FROM `{TABLE_NAME}`
    WHERE `name` LIKE CONCAT('%', keyword, '%')
       OR `notes` LIKE CONCAT('%', keyword, '%')
    ORDER BY `rating` DESC;
END //

DELIMITER ;
""".format(TABLE_NAME=TABLE_NAME)


def generate_completion_message():
    """生成安装完成信息"""
    return """
-- ============================================
-- 安装完成
-- ============================================
SELECT '✅ 苏州美食数据库安装完成！' AS status;
SELECT '📊 使用说明：' AS info;
SELECT '  - 查看所有数据: SELECT * FROM {TABLE_NAME};' AS tips;
SELECT '  - 查看高分美食: SELECT * FROM v_high_rating_food;' AS tips;
SELECT '  - 按菜系统计: SELECT * FROM v_cuisine_stats;' AS tips;
SELECT '  - 按评分查询: CALL sp_get_food_by_rating(4.5, 5.0);' AS tips;
SELECT '  - 按菜系查询: CALL sp_get_food_by_cuisine(''湘菜'');' AS tips;
SELECT '  - 搜索美食: CALL sp_search_food(''牛肉'');' AS tips;
""".format(TABLE_NAME=TABLE_NAME)


def read_csv(csv_path):
    """读取CSV文件"""
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            fields = reader.fieldnames

            if not fields:
                print("❌ CSV文件没有表头", file=sys.stderr)
                sys.exit(1)

            rows = list(reader)
            return fields, rows

    except FileNotFoundError:
        print(f"❌ CSV文件不存在: {csv_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 读取CSV文件错误: {e}", file=sys.stderr)
        sys.exit(1)


def write_sql(sql_path, fields, rows, total_count):
    """生成完整的SQL脚本"""
    # 确保输出目录存在
    os.makedirs(os.path.dirname(sql_path) or '.', exist_ok=True)

    with open(sql_path, 'w', encoding='utf-8') as sqlfile:
        # 文件头
        sqlfile.write("-- ============================================\n")
        sqlfile.write("-- 苏州美食数据库 - 完整安装脚本\n")
        sqlfile.write(f"-- Generated by: {os.path.basename(__file__)}\n")
        sqlfile.write(f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sqlfile.write(f"-- Total records: {total_count}\n")
        sqlfile.write(f"-- Database: {DATABASE_NAME}\n")
        sqlfile.write("-- ============================================\n\n")

        # 1. 创建数据库
        sqlfile.write("-- ============================================\n")
        sqlfile.write("-- 1. 创建数据库（如果不存在）\n")
        sqlfile.write("-- ============================================\n")
        sqlfile.write(f"CREATE DATABASE IF NOT EXISTS `{DATABASE_NAME}` \n")
        sqlfile.write("    CHARACTER SET utf8mb4 \n")
        sqlfile.write("    COLLATE utf8mb4_unicode_ci;\n\n")
        sqlfile.write(f"USE `{DATABASE_NAME}`;\n\n")

        # 2. 删除已存在的表
        sqlfile.write("-- ============================================\n")
        sqlfile.write("-- 2. 删除已存在的表（谨慎操作，如需保留数据请注释掉）\n")
        sqlfile.write("-- ============================================\n")
        sqlfile.write(f"DROP TABLE IF EXISTS `{TABLE_NAME}`;\n\n")

        # 3. 创建表
        sqlfile.write("-- ============================================\n")
        sqlfile.write("-- 3. 创建表结构\n")
        sqlfile.write("-- ============================================\n")
        sqlfile.write(generate_create_table_sql(fields, rows))
        sqlfile.write("\n\n")

        # 4. 导入数据
        sqlfile.write("-- ============================================\n")
        sqlfile.write("-- 4. 导入数据\n")
        sqlfile.write("-- ============================================\n")
        sqlfile.write(generate_insert_sql(rows, fields))
        sqlfile.write("\n\n")

        # 5. 验证查询
        sqlfile.write(generate_validation_queries())
        sqlfile.write("\n\n")

        # 6. 视图
        sqlfile.write(generate_views())
        sqlfile.write("\n\n")

        # 7. 存储过程
        sqlfile.write(generate_stored_procedures())
        sqlfile.write("\n\n")

        # 8. 完成信息
        sqlfile.write(generate_completion_message())


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 苏州美食数据库 - SQL生成工具")
    print("=" * 60)
    print(f"📂 CSV文件: {CSV_PATH}")
    print(f"📄 SQL文件: {SQL_PATH}")
    print(f"🗄️  数据库名: {DATABASE_NAME}")
    print(f"📋 表名: {TABLE_NAME}")
    print("=" * 60)

    # 读取CSV
    fields, rows = read_csv(CSV_PATH)

    # 过滤示例行
    rows = [r for r in rows if not ("示例" in (r.get('name') or '') or "示例" in (r.get('notes') or ''))]

    if not rows:
        print("⚠️ 警告: CSV文件为空或只有示例行")

    total_count = len(rows)
    print(f"✅ 读取成功: {total_count} 条记录, {len(fields)} 个字段")
    print(f"📋 字段: {', '.join(fields)}")

    # 生成SQL
    write_sql(SQL_PATH, fields, rows, total_count)

    print(f"✅ SQL生成成功: {SQL_PATH}")
    print(f"📊 记录数: {total_count}")
    print("=" * 60)
    print("💡 使用方法:")
    print(f"   mysql -u root -p < {SQL_PATH}")
    print("   或在MySQL客户端执行: source " + SQL_PATH)
    print("=" * 60)


if __name__ == "__main__":
    main()