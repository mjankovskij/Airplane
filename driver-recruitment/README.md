# Driver recruitment video (Vilnius)

33s recruitment spot for truck drivers in Vilnius, Lithuania.

## Output

- `out/drivers_vilnius.mp4` — 1920×1080 H.264 + AAC
- Female Russian voice (Microsoft Svetlana Neural), short English close
- Pay: **100 €/day with ADR**, **97 €/day without ADR**
- Phone: **+370 612 12123**

## Rebuild

```bash
pip install edge-tts pillow
# regenerate voice (see script_ru.txt / build notes), then:
python3 build_video.py
```

Requires `ffmpeg` and Noto Sans fonts.
