from PIL import Image, ImageDraw

def create_tray_icon():
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, 62, 62), fill="#4f46e5", outline="#3730a3", width=2)
    nodes = [(32, 13), (15, 47), (49, 47)]
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            draw.line([a, b], fill=(255, 255, 255, 140), width=2)
    for x, y in nodes:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="white")
    return img

if __name__ == "__main__":
    icon = create_tray_icon()
    icon.save(
    "llm_switcher.ico",
    sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
    )