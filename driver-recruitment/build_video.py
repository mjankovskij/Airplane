#!/usr/bin/env python3
"""Build a high-motion truck-driver recruitment video from a still + VO."""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

import cv2
import numpy as np
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
# Extra resolution so aggressive zooms stay sharp
SRC_W, SRC_H = 2880, 1620


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


def make_overlay(lines: list[tuple[str, str, int]]) -> np.ndarray:
    """Return BGRA overlay (numpy)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    for i in range(460):
        a = int(185 * (i / 459) ** 1.25)
        y = H - 460 + i
        pd.line([(0, y), (W, y)], fill=(6, 10, 16, a))
    for i in range(160):
        a = int(90 * (1 - i / 159))
        pd.line([(0, i), (W, i)], fill=(6, 10, 16, a))
    layer = Image.alpha_composite(layer, panel)
    draw = ImageDraw.Draw(layer)

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

    rgba = np.array(layer)
    # PIL RGBA -> OpenCV BGRA
    return cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)


SCENES = [
    (
        0.0,
        7.2,
        [
            ("title", "ИЩЕМ ВОДИТЕЛЕЙ", 92),
            ("body", "Помогаем с трудоустройством", 48),
            ("small", "Вильнюс, Литва · Vilnius, Lithuania", 36),
        ],
        # camera: strong push-in toward truck (right-center)
        {"z0": 1.05, "z1": 1.55, "x0": 0.22, "x1": 0.62, "y0": 0.28, "y1": 0.38},
    ),
    (
        7.2,
        14.5,
        [
            ("title", "ОПЛАТА ЗА ДЕНЬ", 78),
            ("accent", "100 €  ·  с ADR", 72),
            ("accent", "97 €  ·  без ADR", 72),
            ("small", "Стабильные выплаты · ежедневно", 34),
        ],
        # whip-ish: pull slightly then pan across truck
        {"z0": 1.35, "z1": 1.70, "x0": 0.70, "x1": 0.25, "y0": 0.40, "y1": 0.32},
    ),
    (
        14.5,
        21.5,
        [
            ("title", "СОВРЕМЕННЫЙ АВТОПАРК", 70),
            ("body", "Scania · комфорт · надёжная работа", 46),
            ("small", "Помощь с оформлением и ADR", 34),
        ],
        # dive into grille / cab
        {"z0": 1.40, "z1": 1.95, "x0": 0.45, "x1": 0.58, "y0": 0.35, "y1": 0.42},
    ),
    (
        21.5,
        99.0,
        [
            ("title", "ЗВОНИТЕ СЕЙЧАС", 78),
            ("phone", "+370 612 12123", 72),
            ("small", "Looking for drivers · Vilnius, Lithuania", 34),
            ("body", "Русский / English", 42),
        ],
        # pull back revealing full truck + road
        {"z0": 1.85, "z1": 1.20, "x0": 0.55, "x1": 0.40, "y0": 0.42, "y1": 0.30},
    ),
]


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def prepare_source() -> np.ndarray:
    img = Image.open(TRUCK).convert("RGB")
    src_w, src_h = img.size
    target_ratio = SRC_W / SRC_H
    if src_w / src_h > target_ratio:
        new_h = src_h
        new_w = int(src_h * target_ratio)
    else:
        new_w = src_w
        new_h = int(src_w / target_ratio)
    left = (src_w - new_w) // 2
    top = (src_h - new_h) // 2
    base = img.crop((left, top, left + new_w, top + new_h)).resize(
        (SRC_W, SRC_H), Image.Resampling.LANCZOS
    )
    base = ImageEnhance.Contrast(base).enhance(1.10)
    base = ImageEnhance.Color(base).enhance(1.08)
    rgb = np.array(base)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    path = OUT / "base_hires.jpg"
    cv2.imwrite(str(path), bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return bgr


def camera_crop(src: np.ndarray, cam: dict, local_t: float, global_t: float) -> np.ndarray:
    """Crop/zoom with road vibration + slight sway for real motion feel."""
    p = ease_in_out(local_t)
    z = cam["z0"] + (cam["z1"] - cam["z0"]) * p
    xn = cam["x0"] + (cam["x1"] - cam["x0"]) * p
    yn = cam["y0"] + (cam["y1"] - cam["y0"]) * p

    # Road rumble + gentle sway (truck-on-road feel)
    rumble_y = math.sin(global_t * 26.0) * 4.5 + math.sin(global_t * 41.0) * 2.2
    rumble_x = math.sin(global_t * 13.5) * 3.0
    sway = math.sin(global_t * 1.7) * 8.0

    crop_w = SRC_W / z
    crop_h = SRC_H / z
    max_x = SRC_W - crop_w
    max_y = SRC_H - crop_h
    x = xn * max_x + rumble_x + sway
    y = yn * max_y + rumble_y
    x = max(0.0, min(max_x, x))
    y = max(0.0, min(max_y, y))

    x0, y0 = int(x), int(y)
    x1, y1 = int(x + crop_w), int(y + crop_h)
    # Keep exact size
    if x1 - x0 < int(crop_w):
        x1 = x0 + int(crop_w)
    if y1 - y0 < int(crop_h):
        y1 = y0 + int(crop_h)
    x1 = min(SRC_W, x1)
    y1 = min(SRC_H, y1)
    patch = src[y0:y1, x0:x1]
    frame = cv2.resize(patch, (W, H), interpolation=cv2.INTER_LINEAR)

    # Directional motion blur along pan direction (stronger when camera moves fast)
    dx = abs(cam["x1"] - cam["x0"])
    dz = abs(cam["z1"] - cam["z0"])
    speed = dx * 18 + dz * 10
    k = int(max(1, min(15, round(speed))))
    if k % 2 == 0:
        k += 1
    if k >= 3:
        frame = cv2.GaussianBlur(frame, (k, 1), 0)

    return frame


def alpha_overlay(bg_bgr: np.ndarray, overlay_bgra: np.ndarray, y_off: int, alpha_scale: float) -> np.ndarray:
    """Composite BGRA overlay onto BGR with vertical offset + fade."""
    out = bg_bgr.copy()
    oh, ow = overlay_bgra.shape[:2]
    if y_off >= H or y_off <= -oh:
        return out

    y0 = max(0, y_off)
    y1 = min(H, y_off + oh)
    oy0 = max(0, -y_off)
    oy1 = oy0 + (y1 - y0)

    ov = overlay_bgra[oy0:oy1, :, :].astype(np.float32)
    a = (ov[:, :, 3:4] / 255.0) * max(0.0, min(1.0, alpha_scale))
    rgb = ov[:, :, :3]
    roi = out[y0:y1, :, :].astype(np.float32)
    out[y0:y1, :, :] = (rgb * a + roi * (1.0 - a)).astype(np.uint8)
    return out


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


def render_frames(src: np.ndarray, duration: float) -> Path:
    frames_dir = OUT / "frames"
    if frames_dir.exists():
        for p in frames_dir.glob("*.jpg"):
            p.unlink()
    frames_dir.mkdir(parents=True, exist_ok=True)

    overlays = []
    for start, end, lines, cam in SCENES:
        overlays.append((start, end, make_overlay(lines), cam))

    total = int(duration * FPS)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    r_term = np.clip(r - 0.55, 0, 1) ** 2

    for i in range(total):
        t = i / FPS
        # Active scene
        scene = overlays[-1]
        for s in overlays:
            if s[0] <= t < s[1]:
                scene = s
                break
        start, end, ov, cam = scene
        local = (t - start) / max(0.001, (end - start))
        # For last scene, end is 99 — clamp using duration
        if end > duration:
            local = (t - start) / max(0.001, (duration - start))

        frame = camera_crop(src, cam, local, t)

        # Text slide-up + fade-in each scene
        fade = ease_out_cubic(min(1.0, local * 3.2))
        slide = int((1.0 - fade) * 90)
        # Fade out near scene end (except last)
        if end < duration - 0.5:
            fade_out = ease_out_cubic(min(1.0, max(0.0, (end - t) / 0.35)))
        else:
            fade_out = 1.0
        alpha = fade * fade_out
        frame = alpha_overlay(frame, ov, slide, alpha)

        # Soft vignette pulse
        strength = 0.22 + 0.04 * math.sin(t * 2.2)
        vignette = np.clip(1.0 - strength * r_term, 0.55, 1.0)
        frame = (frame.astype(np.float32) * vignette[:, :, None]).astype(np.uint8)

        out_path = frames_dir / f"frame_{i:05d}.jpg"
        cv2.imwrite(str(out_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if i % 60 == 0:
            print(f"frame {i}/{total}", flush=True)

    return frames_dir


def mux(frames_dir: Path, duration: float) -> Path:
    video_path = OUT / "drivers_vilnius.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frames_dir / "frame_%05d.jpg"),
        "-i",
        str(VOICE),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(video_path),
    ]
    subprocess.run(cmd, check=True)
    return video_path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    duration = voice_duration() + 0.25
    print(f"duration={duration:.2f}s")
    src = prepare_source()
    frames_dir = render_frames(src, duration)
    path = mux(frames_dir, duration)
    print(f"DONE {path}")


if __name__ == "__main__":
    main()
