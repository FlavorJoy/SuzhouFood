# 贡献指南 - 添加/更新美食条目

欢迎贡献苏州美食推荐！请按照下面步骤提交餐厅信息：

1. 在仓库根目录打开 `food-original.csv`。
2. 在文件末尾添加一行，字段按顺序为：
   name,cuisine,price,rating,url,hours,notes
3. 填写示例：
   示例餐厅,本地苏帮菜,¥50-100,4.5,https://example.com,周一-周日 11:00-21:00,示例说明
4. 提交新分支并打开 PR。
5. PR 被合并到默认分支（main/master）后，GitHub Actions 会自动运行 `readme_render.py` 并提交生成的 `README.md`。

> **附加说明**：在 PR 合并后，自动化脚本 `export_to_sql.py` 亦会执行，将 `food-original.csv` 转换为 `data/food.sql`。此 SQL 文件包含 `suzhou_food` 表的 INSERT 语句，可直接用于创建数据库或备份。

本仓库使用 CSV 做单一数据源，README 与 SQL 为自动生成产物，请确保 CSV 的字段顺序和列名不被更改。
