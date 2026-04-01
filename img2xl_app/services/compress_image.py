from __future__ import unicode_literals
from PIL import Image
import io

def compress_image(content):
    try:
        img = Image.open(io.BytesIO(content))

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail((768, 768))

        output = io.BytesIO()
        img.save(output, format='JPEG', quality=70)

        return output.getvalue()

    except Exception as e:
        print("Preprocess error:", e)
        return content
