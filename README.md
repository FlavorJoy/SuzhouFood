# SuzhouFood 苏州美食推荐

记录一些必吃的苏州美食&amp;餐厅🍴

本 README 将由仓库根目录的 `readme_render.py` 脚本根据 `food-original.csv` 自动生成。请不要直接编辑此文件（除非你知道在做什么）。

要添加餐厅，请编辑 `food-original.csv`，在文件末尾添加一行，字段顺序为：

name,cuisine,price,rating,url,hours,contact,reservation_needed,queue_time,tags,notes

示例行已包含在 food-original.csv 中。合并 PR 后，CI（GitHub Actions）会在默认分支上运行并自动提交更新后的 README。
