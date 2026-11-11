"""
image_handler.py
Multimodal input processor – handles food photo and grocery label images.
Extracts text via OCR (pytesseract) and passes results to the nutrition agent.
"""

import os
import io
import base64
from typing import Optional, Tuple

# Optional heavy imports – handled gracefully if not installed
try:
    from PIL import Image, ImageEnhance, ImageFilter
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

try:
    import pytesseract
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
MAX_FILE_SIZE_MB   = 10


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(img: "Image.Image") -> "Image.Image":
    """
    Enhance image quality for better OCR accuracy:
    - Convert to RGB
    - Increase contrast
    - Sharpen
    - Convert to grayscale for OCR
    """
    img = img.convert("RGB")
    # Enhance contrast
    img = ImageEnhance.Contrast(img).enhance(2.0)
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    # Convert to grayscale for OCR
    img = img.convert("L")
    return img


def extract_text_from_image(image_bytes: bytes) -> Tuple[str, str]:
    """
    Extract text from image bytes.
    Returns (extracted_text, status_message).
    """
    if not _PIL_AVAILABLE:
        return "", "Pillow is not installed. Install it with: pip install Pillow"

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return "", f"Could not open image: {e}"

    if not _TESSERACT_AVAILABLE:
        # Return image metadata without OCR
        width, height = img.size
        mode = img.mode
        return (
            f"[Image metadata only – pytesseract not installed]\n"
            f"Image size: {width}x{height} pixels\n"
            f"Mode: {mode}\n"
            f"Please install Tesseract OCR and pytesseract for full text extraction.",
            "warning"
        )

    try:
        processed = preprocess_image(img)
        text = pytesseract.image_to_string(processed, config="--psm 3")
        text = text.strip()
        if not text:
            return "[No text found in image]", "warning"
        return text, "ok"
    except Exception as e:
        return f"[OCR Error: {e}]", "error"


def encode_image_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string for browser display."""
    return base64.b64encode(image_bytes).decode("utf-8")


def detect_image_type(image_bytes: bytes) -> str:
    """Detect whether image is likely a food photo or nutrition label."""
    text, _ = extract_text_from_image(image_bytes)
    label_keywords = [
        "calories", "nutrition facts", "serving size", "total fat",
        "saturated fat", "sodium", "carbohydrate", "protein", "ingredients",
        "daily value", "cholesterol", "sugars", "fiber", "vitamin",
    ]
    text_lower = text.lower()
    matches = sum(1 for kw in label_keywords if kw in text_lower)
    if matches >= 3:
        return "nutrition_label"
    if matches >= 1:
        return "partial_label"
    return "food_photo"


def describe_image_context(image_bytes: bytes) -> str:
    """
    Build a descriptive context string from an image to pass to the agent.
    Combines OCR text with image type detection.
    """
    extracted_text, status = extract_text_from_image(image_bytes)
    image_type = detect_image_type(image_bytes)

    context_parts = [f"[Image type detected: {image_type.replace('_', ' ').title()}]"]

    if extracted_text and status == "ok":
        context_parts.append(f"\nExtracted text:\n{extracted_text}")
    elif extracted_text:
        context_parts.append(f"\n{extracted_text}")
    else:
        context_parts.append("\n[No readable text could be extracted from this image]")
        if image_type == "food_photo":
            context_parts.append(
                "\n[This appears to be a food photo without readable labels. "
                "Please describe the food item for a nutritional analysis.]"
            )

    return "\n".join(context_parts)
