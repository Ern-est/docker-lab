FROM ubuntu:24.04

WORKDIR /app

COPY app.txt .

CMD ["sleep", "300"]
