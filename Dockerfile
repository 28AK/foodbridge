# FoodBridge – container for Hugging Face Spaces (also runs on any Docker host)
FROM python:3.11-slim

# OpenCV runtime dependency
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs containers as user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    PYTHONUNBUFFERED=1
WORKDIR /home/user/app

# requirements.txt points pip at the CPU-only PyTorch index (no ~2.5 GB of GPU libraries)
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Bake the AI model into the image so startup doesn't wait for a ~600 MB download
ARG AI_MODEL=openai/clip-vit-base-patch16
RUN python -c "from transformers import CLIPModel, CLIPProcessor; \
CLIPModel.from_pretrained('${AI_MODEL}'); CLIPProcessor.from_pretrained('${AI_MODEL}')"
# Use only the baked-in copy at runtime
ENV HF_HUB_OFFLINE=1

COPY --chown=user . .

EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
