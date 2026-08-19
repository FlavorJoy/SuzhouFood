FROM python:3.10-slim

# 安装依赖
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# 运行脚本
CMD ["python", "scripts/readme_render.py"]
