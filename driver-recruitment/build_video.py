#!/usr/bin/env python3
"""High-motion recruitment video: morphing approach shots + animated overlays + VO."""

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
VOICE = OUT / "voice.mp3"
GEN = Path("/opt/cursor/artifacts/assets")
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

W, H = 1920, 1080
FPS = 30

# Approach sequence: far → near (truck drives toward camera)
KEYFRAMES = [
    ASSETS / "truck.jpg",
    GEN / "truck_move_00.jpg",
    GEN / "truck_move_01.jpg",
    GEN / "truck_move_02.jpg",
    GEN / "truck_move_03.jpg",
]


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_centered_text(draw, text, y, font, fill=(255, 255, 255, 255), stroke=2) -> int:
    tw, th = measure(draw, text, font)
    draw.text(
        ((W - tw) // 2, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke,
        stroke_fill=(0, 0, 0, 180),
    )
    return th


def make_overlay(lines: list[tuple[str, str, int]]) -> np.ndarray:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    for i in range(460):
        a = int(185 * (i / 459) ** 1.25)
        pd.line([(0, H - 460 + i), (W, H - 460 + i)], fill=(6, 10, 16, a))
    for i in range(160):
        a = int(90 * (1 - i / 159))
        pd.line([(0, i), (W, i)], fill=(6, 10, 16, a))
    layer = Image.alpha_composite(layer, panel)
    draw = ImageDraw.Draw(layer)

    draw.rounded_rectangle((70, 56, 560, 118), radius=10, fill=(196, 22, 28, 235))
    draw.text((96, 72), "ВАКАНСИЯ · VILNIUS", font=load_font(FONT_BOLD, 34), fill=(255, 255, 255, 255))

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
            tw, th = measure(draw, text, font)
            px, py = (W - tw) // 2 - 40, y - 20
            draw.rounded_rectangle((px, py, px + tw + 80, py + th + 40), radius=18, fill=(196, 22, 28, 240))
            draw.text(((W - tw) // 2, y), text, font=font, fill=(255, 255, 255, 255))
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
        th = draw_centered_text(draw, text, y, font, fill=color, stroke=stroke)
        y += th + (24 if role == "title" else 16)

    return cv2.cvtColor(np.array(layer), cv2.COLOR_RGBA2BGRA)


SCENES = [
    (0.0, 7.2, [("title", "ИЩЕМ ВОДИТЕЛЕЙ", 92), ("body", "Помогаем с трудоустройством", 48), ("small", "Вильнюс, Литва · Vilnius, Lithuania", 36)]),
    (7.2, 14.5, [("title", "ОПЛАТА ЗА ДЕНЬ", 78), ("accent", "100 €  ·  с ADR", 72), ("accent", "97 €  ·  без ADR", 72), ("small", "Стабильные выплаты · ежедневно", 34)]),
    (14.5, 21.5, [("title", "СОВРЕМЕННЫЙ АВТОПАРК", 70), ("body", "Scania · комфорт · надёжная работа", 46), ("small", "Помощь с оформлением и ADR", 34)]),
    (21.5, 99.0, [("title", "ЗВОНИТЕ СЕЙЧАС", 78), ("phone", "+370 612 12123", 72), ("small", "Looking for drivers · Vilnius, Lithuania", 34), ("body", "Русский / English", 42)]),
]


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def cover_resize(path: Path, out_w: int = W, out_h: int = H) -> np.ndarray:
    bgr = cv2.imread(str(path))
    if bgr is None:
        raise FileNotFoundError(path)
    h, w = bgr.shape[:2]
    scale = max(out_w / w, out_h / h)
    nw, nh = int(w * scale), int(h * scale)
    resized = cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    x0 = (nw - out_w) // 2
    y0 = (nh - out_h) // 2
    crop = resized[y0 : y0 + out_h, x0 : x0 + out_w]
    # Mild grade
    pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    pil = ImageEnhance.Contrast(pil).enhance(1.08)
    pil = ImageEnhance.Color(pil).enhance(1.06)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def zoom_frame(img: np.ndarray, z: float, xn: float, yn: float, shake_t: float) -> np.ndarray:
    """Crop from a larger padded version for zoom headroom."""
    h, w = img.shape[:2]
    # Work on 1.5x padded canvas so we can zoom out and in
    pad = cv2.resize(img, (int(w * 1.55), int(h * 1.55)), interpolation=cv2.INTER_LINEAR)
    ph, pw = pad.shape[:2]
    crop_w = pw / z
    crop_h = ph / z
    rumble_x = math.sin(shake_t * 17.0) * 5.0 + math.sin(shake_t * 29.0) * 2.5
    rumble_y = math.sin(shake_t * 23.0) * 6.0 + math.sin(shake_t * 37.0) * 3.0
    max_x = pw - crop_w
    max_y = ph - crop_h
    x = xn * max_x + rumble_x
    y = yn * max_y + rumble_y
    x = max(0.0, min(max_x, x))
    y = max(0.0, min(max_y, y))
    x0, y0 = int(x), int(y)
    x1, y1 = x0 + int(crop_w), y0 + int(crop_h)
    patch = pad[y0:y1, x0:x1]
    return cv2.resize(patch, (W, H), interpolation=cv2.INTER_LINEAR)


def alpha_overlay(bg: np.ndarray, ov: np.ndarray, y_off: int, a_scale: float) -> np.ndarray:
    out = bg.copy()
    oh = ov.shape[0]
    if y_off >= H or y_off <= -oh:
        return out
    y0 = max(0, y_off)
    y1 = min(H, y_off + oh)
    oy0 = max(0, -y_off)
    oy1 = oy0 + (y1 - y0)
    layer = ov[oy0:oy1].astype(np.float32)
    a = (layer[:, :, 3:4] / 255.0) * max(0.0, min(1.0, a_scale))
    roi = out[y0:y1].astype(np.float32)
    out[y0:y1] = (layer[:, :, :3] * a + roi * (1.0 - a)).astype(np.uint8)
    return out


def blend(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    t = ease_in_out(t)
    return cv2.addWeighted(a, 1.0 - t, b, t, 0)


def voice_duration() -> float:
    return float(
        subprocess.check_output(
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
    )


def keyframe_at(t: float, duration: float, frames: list[np.ndarray]) -> np.ndarray:
    """Map time → continuous morph across approach keyframes + per-segment zoom."""
    # Spend time across N-1 segments
    n = len(frames)
    # Hold last frame a bit longer for CTA
    progress = min(0.999, t / max(0.001, duration * 0.92))
    # Non-linear: accelerate approach mid-video
    progress = ease_in_out(progress)
    seg_f = progress * (n - 1)
    i0 = int(seg_f)
    i1 = min(n - 1, i0 + 1)
    local = seg_f - i0

    # Within each morph, also push zoom on both ends
    z0 = 1.08 + 0.18 * local
    z1 = 1.12 + 0.22 * local
    # Bias toward truck (right-center)
    xn = 0.35 + 0.25 * math.sin(progress * math.pi)
    yn = 0.32 + 0.08 * local

    a = zoom_frame(frames[i0], z0, xn, yn, t)
    b = zoom_frame(frames[i1], z1, xn + 0.05, yn + 0.02, t)
    base = blend(a, b, local)

    # Extra forward punch: slight scale pulse
    punch = 1.0 + 0.015 * math.sin(t * 2.4)
    if punch != 1.0:
        nh, nw = int(H / punch), int(W / punch)
        y0 = (H - nh) // 2
        x0 = (W - nw) // 2
        crop = base[y0 : y0 + nh, x0 : x0 + nw]
        base = cv2.resize(crop, (W, H), interpolation=cv2.INTER_LINEAR)

    # Directional motion blur when morphing fast
    speed = abs(local - 0.5) * 2  # peak mid-morph? actually higher near transitions
    speed = (0.35 + abs(math.sin(progress * math.pi * (n - 1))) * 0.65)
    k = int(1 + round(speed * 9))
    if k % 2 == 0:
        k += 1
    if k >= 3:
        base = cv2.GaussianBlur(base, (k, 1), 0)
    return base


def render(duration: float) -> Path:
    frames_dir = OUT / "frames"
    if frames_dir.exists():
        for p in frames_dir.glob("*.jpg"):
            p.unlink()
    frames_dir.mkdir(parents=True, exist_ok=True)

    print("loading keyframes...")
    kfs = [cover_resize(p) for p in KEYFRAMES]
    for i, p in enumerate(KEYFRAMES):
        print(f"  {i}: {p.name} ok")
        cv2.imwrite(str(OUT / f"kf_{i:02d}.jpg"), kfs[i])

    overlays = [(s, e, make_overlay(lines)) for s, e, lines in SCENES]

    total = int(duration * FPS)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.72)) ** 2)
    r_term = np.clip(r - 0.5, 0, 1) ** 2

    for i in range(total):
        t = i / FPS
        frame = keyframe_at(t, duration, kfs)

        # Scene overlay
        scene = overlays[-1]
        for s in overlays:
            if s[0] <= t < s[1]:
                scene = s
                break
        start, end, ov = scene
        local = (t - start) / max(0.001, (min(end, duration) - start))
        fade = ease_out_cubic(min(1.0, local * 3.0))
        slide = int((1.0 - fade) * 100)
        fade_out = 1.0 if end > duration - 0.5 else ease_out_cubic(min(1.0, max(0.0, (end - t) / 0.3)))
        frame = alpha_overlay(frame, ov, slide, fade * fade_out)

        strength = 0.20 + 0.05 * math.sin(t * 2.0)
        vignette = np.clip(1.0 - strength * r_term, 0.58, 1.0)
        frame = (frame.astype(np.float32) * vignette[:, :, None]).astype(np.uint8)

        cv2.imwrite(str(frames_dir / f"frame_{i:05d}.jpg"), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if i % 60 == 0:
            print(f"frame {i}/{total}", flush=True)

    return frames_dir


def mux(frames_dir: Path) -> Path:
    video_path = OUT / "drivers_vilnius.mp4"
    subprocess.run(
        [
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
            "17",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(video_path),
        ],
        check=True,
    )
    return video_path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Copy generated assets into repo for reproducibility
    gen_dir = ASSETS / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)
    for name in ["truck_move_00.jpg", "truck_move_01.jpg", "truck_move_02.jpg", "truck_move_03.jpg"]:
        src = GEN / name
        if src.exists():
            dst = gen_dir / name
            dst.write_bytes(src.read_bytes())

    # Prefer local copies if present
    global KEYFRAMES
    local = [
        ASSETS / "truck.jpg",
        gen_dir / "truck_move_00.jpg",
        gen_dir / "truck_move_01.jpg",
        gen_dir / "truck_move_02.jpg",
        gen_dir / "truck_move_03.jpg",
    ]
    if all(p.exists() for p in local):
        KEYFRAMES = local

    duration = voice_duration() + 0.2
    print(f"duration={duration:.2f}s")
    frames_dir = render(duration)
    path = mux(frames_dir)
    print(f"DONE {path}")


if __name__ == "__main__":
    main()
