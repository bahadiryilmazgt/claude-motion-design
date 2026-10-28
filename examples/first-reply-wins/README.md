# First Reply Wins

Silent 9:16 motion piece for Instagram Reels (1080×1920, 30 fps, 45.7 s, 105 BPM).
Story: a patient sees a clinic ad, sends the same WhatsApp message to five clinics, and the first clinic to reply gets the appointment.
Message: in health tourism, reply speed = trust = patients. The beat map and scene table are in [`BRIEF.md`](BRIEF.md).

Everything is code: `film.html` (one `seek(t)` engine: CSS 3D camera, canvas light/particles/grain), `render.js` (Playwright, 6 subframes per frame blended with `tmix`), `audio.py` (music and SFX synthesized with numpy on the same beat grid, −14 LUFS).

```bash
python3 fetch_assets.py                      # Montserrat (OFL)
python3 -m http.server 8765 &                # serve the folder
node render.js probe 3 7 12 20 27 35 40 44   # stills -> probe/sheet.png
for k in 0 1 2 3; do node render.js chunk $k 4 & done; wait   # frames -> sub/
node render.js encode                        # -> out/video.mp4
python3 audio.py                             # -> out/audio.wav
ffmpeg -i out/video.mp4 -i out/audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -movflags +faststart out/first-reply-wins.mp4
```
(`render.js` needs Playwright on the Node path, e.g. `NODE_PATH=$(npm root -g)`.)

Clinic names, the patient name and every time on screen are fictional.
