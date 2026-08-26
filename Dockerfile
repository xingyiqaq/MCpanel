FROM python:3.12-slim

LABEL name="mc-panel" \
      description="MC 管理面板 - mc-web-generic" \
      version="1.0"

RUN pip install --no-cache-dir pyyaml

WORKDIR /mc-web

# 复制面板代码
COPY . /mc-web/

# 创建目录
RUN mkdir -p /panel-data /mc-data

# 复制启动脚本
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 19888

ENTRYPOINT ["/entrypoint.sh"]
