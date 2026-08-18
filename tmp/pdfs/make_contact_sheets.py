from pathlib import Path

from PIL import Image, ImageDraw


files = sorted(Path("tmp/pdfs/rendered").glob("page-*.png"))
for sheet_number, start in enumerate(range(0, len(files), 5), 1):
    group = files[start:start + 5]
    images = [Image.open(path).convert("RGB") for path in group]
    thumb_width = 350
    thumb_height = int(images[0].height * thumb_width / images[0].width)
    canvas = Image.new("RGB", (thumb_width * len(images), thumb_height + 30), (225, 230, 238))
    draw = ImageDraw.Draw(canvas)
    for index, image in enumerate(images):
        resized = image.resize((thumb_width, thumb_height))
        canvas.paste(resized, (index * thumb_width, 30))
        draw.text((index * thumb_width + 8, 8), f"Page {start + index + 1}", fill=(20, 30, 50))
    canvas.save(f"tmp/pdfs/contact-{sheet_number}.png")
