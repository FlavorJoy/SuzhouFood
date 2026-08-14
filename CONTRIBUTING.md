# 贡献指南 - 添加/更新美食条目

欢迎贡献苏州美食推荐！请按照下面步骤提交餐厅信息：

1. 在仓库根目录打开 `food-original.csv`。
2. 在文件末尾添加一行，字段按顺序为：
   name,cuisine,price,rating,url,hours,contact,reservation_needed,queue_time,tags,notes
3. 填写示例：
   示例餐厅,本地苏帮菜,¥50-100,4.5,https://example.com,周一-周日 11:00-21:00,0512-12345678,否,10-20分钟,平价小吃,示例说明
4. 提交新分支并打开 PR。
5. PR 被合并到默认分支（main/master）后，GitHub Actions 会自动运行 `readme_render.py` 并提交生成的 `README.md`。

本仓库使用 CSV 做单一数据源，README 为自动生成产物，请确保 CSV 的字段顺序和列名不被更改。
