#!/usr/bin/env python3
"""Build a truck-driver recruitment video with Russian/English VO overlays."""

from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "out"
TRUCK = ASSETS / "truck.jpg"
VOICE = OUT / "voice.mp3"
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

W, H = 1920, 1080
FPS = 30


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.ImageFont,
    fill=(255, 255, 255, 255),
    stroke_fill=(0, 0, 0, 180),
    stroke_width: int = 2,
) -> int:
    tw, th = measure(draw, text, font)
    x = (W - tw) // 2
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
    return th


def make_overlay(lines: list[tuple[str, str, int]]) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    # Soft bottom panel
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    for i in range(460):
        a = int(185 * (i / 459) ** 1.25)
        y = H - 460 + i
        pd.line([(0, y), (W, y)], fill=(6, 10, 16, a))
    # Top vignette strip
    for i in range(160):
        a = int(90 * (1 - i / 159))
        pd.line([(0, i), (W, i)], fill=(6, 10, 16, a))
    layer = Image.alpha_composite(layer, panel)
    draw = ImageDraw.Draw(layer)

    # Brand chip
    draw.rounded_rectangle((70, 56, 560, 118), radius=10, fill=(196, 22, 28, 235))
    brand_font = load_font(FONT_BOLD, 34)
    draw.text((96, 72), "ВАКАНСИЯ · VILNIUS", font=brand_font, fill=(255, 255, 255, 255))

    y = 500
    for role, text, size in lines:
        if role == "title":
            font = load_font(FONT_BOLD, size)
            color = (255, 255, 255, 255)
            stroke = 3
            y += 6
        elif role == "accent":
            font = load_font(FONT_BOLD, size)
            color = (255, 214, 64, 255)
            stroke = 2
        elif role == "phone":
            font = load_font(FONT_BOLD, size)
            color = (255, 255, 255, 255)
            tw, th = measure(draw, text, font)
            px, py = (W - tw) // 2 - 40, y - 20
            draw.rounded_rectangle(
                (px, py, px + tw + 80, py + th + 40),
                radius=18,
                fill=(196, 22, 28, 240),
            )
            draw.text(((W - tw) // 2, y), text, font=font, fill=color)
            y += th + 52
            continue
        elif role == "small":
            font = load_font(FONT_REG, size)
            color = (220, 228, 236, 245)
            stroke = 1
        else:
            font = load_font(FONT_REG, size)
            color = (235, 240, 245, 255)
            stroke = 2

        th = draw_centered_text(draw, text, y, font, fill=color, stroke_width=stroke)
        y += th + (24 if role == "title" else 16)

    return layer


SCENES = [
    (
        "01_hire",
        [
            ("title", "ИЩЕМ ВОДИТЕЛЕЙ", 92),
            ("body", "Помогаем с трудоустройством", 48),
            ("small", "Вильнюс, Литва · Vilnius, Lithuania", 36),
        ],
    ),
    (
        "02_pay",
        [
            ("title", "ОПЛАТА ЗА ДЕНЬ", 78),
            ("accent", "100 €  ·  с ADR", 72),
            ("accent", "97 €  ·  без ADR", 72),
            ("small", "Стабильные выплаты · ежедневно", 34),
        ],
    ),
    (
        "03_fleet",
        [
            ("title", "СОВРЕМЕННЫЙ АВТОПАРК", 70),
            ("body", "Scania · комфорт · надёжная работа", 46),
            ("small", "Помощь с оформлением и ADR", 34),
        ],
    ),
    (
        "04_call",
        [
            ("title", "ЗВОНИТЕ СЕЙЧАС", 78),
            ("phone", "+370 612 12123", 72),
            ("small", "Looking for drivers · Vilnius, Lithuania", 34),
            ("body", "Русский / English", 42),
        ],
    ),
]


def prepare_base_still() -> Path:
    """Crop truck photo to exact 1920x1080 cover."""
    img = Image.open(TRUCK).convert("RGB")
    src_w, src_h = img.size
    target_ratio = W / H
    if src_w / src_h > target_ratio:
        new_h = src_h
        new_w = int(src_h * target_ratio)
    else:
        new_w = src_w
        new_h = int(src_w / target_ratio)
    left = (src_w - new_w) // 2
    top = (src_h - new_h) // 2
    base = img.crop((left, top, left + new_w, top + new_h)).resize((W, H), Image.Resampling.LANCZOS)
    # Slight contrast lift so red cab pops
    base = ImageEnhance.Contrast(base).enhance(1.08)
    base = ImageEnhance.Color(base).enhance(1.05)
    path = OUT / "base_1080.jpg"
    base.save(path, quality=95)
    return path


def voice_duration() -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(VOICE),
        ],
        text=True,
    ).strip()
    return float(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    duration = voice_duration() + 0.35
    frames = int(duration * FPS)
    print(f"duration={duration:.2f}s frames={frames}")

    base = prepare_base_still()
    overlay_paths = []
    for name, lines in SCENES:
        ov = make_overlay(lines)
        p = OUT / f"overlay_{name}.png"
        ov.save(p)
        overlay_paths.append(p)
        print(f"wrote {p.name}")

    # Scene timing aligned with VO
    # 0-7.2 hire, 7.2-14.5 pay, 14.5-21.5 fleet, 21.5-end call
    # Ken Burns via zoompan on larger canvas
    # Scale base up then crop with moving window
    video_out = OUT / "drivers_vilnius.mp4"

    # Build filter: zoompan then overlay each text layer with fade enable
    # zoompan needs input sized; use scale then zoompan
    zframes = frames
    filter_complex = (
        f"[0:v]scale=2304:1296,zoompan="
        f"z='min(1.18,1.05+0.13*on/{zframes})':"
        f"x='(iw-iw/zoom)*0.15+((iw-iw/zoom)*0.70)*on/{zframes}':"
        f"y='(ih-ih/zoom)*0.30':"
        f"d=1:s={W}x{H}:fps={FPS}[bg];"
        # overlays
        f"[bg][1:v]overlay=0:0:enable='between(t,0,7.2)':"
        f"format=auto:alpha=premultiplied[v1];"
        f"[v1][2:v]overlay=0:0:enable='between(t,7.2,14.5)':"
        f"format=auto:alpha=premultiplied[v2];"
        f"[v2][3:v]overlay=0:0:enable='between(t,14.5,21.5)':"
        f"format=auto:alpha=premultiplied[v3];"
        f"[v3][4:v]overlay=0:0:enable='gte(t,21.5)':"
        f"format=auto:alpha=premultiplied[vout]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(base),
        "-loop",
        "1",
        "-i",
        str(overlay_paths[0]),
        "-loop",
        "1",
        "-i",
        str(overlay_paths[1]),
        "-loop",
        "1",
        "-i",
        str(overlay_paths[2]),
        "-loop",
        "1",
        "-i",
        str(overlay_paths[3]),
        "-i",
        str(VOICE),
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        "5:a",
        "-t",
        f"{duration:.3f}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(video_out),
    ]
    print("encoding...")
    subprocess.run(cmd, check=True)
    print(f"DONE {video_out}")


if __name__ == "__main__":
    main()
