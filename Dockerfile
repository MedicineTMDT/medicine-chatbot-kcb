# Sử dụng Python 3.12 slim để nhẹ image
FROM python:3.12-slim

# Sao chép công cụ uv trực tiếp từ image chính thức của Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Thư mục làm việc trong container
WORKDIR /app

# Cài đặt thư viện hệ thống cần thiết cho PostgreSQL và xử lý file
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Sao chép file cấu hình thư viện
COPY pyproject.toml uv.lock ./

# Cài đặt toàn bộ thư viện (không cài dev dependencies)
RUN uv sync --frozen --no-dev

# Đưa môi trường ảo vào PATH để chạy lệnh python trực tiếp
ENV PATH="/app/.venv/bin:$PATH"

# Sao chép toàn bộ mã nguồn
COPY . .

# Mặc định khởi chạy (có thể ghi đè khi chạy lệnh docker run)
CMD ["python", "run_workflow.py"]