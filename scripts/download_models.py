"""Download the pretrained AI model into the local Hugging Face cache.

Optional – the app also downloads it on first start. Useful before a demo or
when building a Docker image, so startup doesn't wait for the ~600 MB download.
Run:  python -m scripts.download_models
"""
from app.services.classifier import get_analyzer


def main() -> None:
    analyzer = get_analyzer()
    print(f"Downloading / loading {analyzer.model_name} …")
    analyzer.load()
    print("✅ Model ready")


if __name__ == "__main__":
    main()
