# Sử dụng Python 3.12 slim để nhẹ image
FROM python:3.12-slim

# Sao chép công cụ uv trực tiếp từ image chính thức của Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Thư mục làm việc trong container
WORKDIR /app

# Cài đặt thư viện hệ thống cần thiết cho PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Sao chép file cấu hình
COPY pyproject.toml uv.lock ./

# Cài đặt toàn bộ thư viện (không cài dev dependencies để image nhẹ hơn)
RUN uv sync --frozen --no-dev

# Đưa môi trường ảo vào PATH để không cần gõ "uv run" nữa
ENV PATH="/app/.venv/bin:$PATH"

# Sao chép toàn bộ mã nguồn
COPY . .

# Mở cổng 8000
EXPOSE 8000

# Khởi chạy Uvicorn thay vì file python thường
# Đảm bảo có --host 0.0.0.0 để kết nối được từ bên ngoài
# Bỏ --reload đi vì đây là môi trường đóng gói (Production-like)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]