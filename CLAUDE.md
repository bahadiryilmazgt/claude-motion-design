# Project rules for Claude

## Voice-over / TTS: always ElevenLabs

- Every voice-over, narration or TTS in this repo is generated with the **ElevenLabs API** (`https://api.elevenlabs.io`). This overrides the Cartesia mentions in `skill/motion-design/SKILL.md`; do not use another TTS provider unless the user asks.
- **Credentials**: the key is injected by the session's network proxy. Never ask for the key in chat, never write it to a file, env var, script or commit. If a client refuses to start without one, pass a dummy `xi-api-key` value; the proxy replaces it.
- If a call returns 401/403, use the secure credential form (`request_credential`, host `api.elevenlabs.io`, header `xi-api-key`) instead of asking for the key in chat.
- **Timings**: prefer `POST /v1/text-to-speech/{voice_id}/with-timestamps`. Its character alignment becomes the single timing file (`cues.json`) that drives captions and animation cues. Fall back to whisper only if the alignment is unusable.
- **Budget**: check `GET /v1/user/subscription` (`character_count` / `character_limit`) before long generations. Generate per line or scene, cache the audio under `out/` (git-ignored) and regenerate only the lines that changed.
- **Licensing**: on the free tier, ElevenLabs output requires attribution and is not licensed for commercial use. Tell the user before delivering a commercial film made on that tier.
- Mixing stays as in the skill: music ducked ~9 dB under the voice, two-pass loudnorm to -14 LUFS.

## Ev sesi

Bu depodaki tüm seslendirme ve dublaj tek, sabit bir sesle yapılır. Varsayılanlar tek yerde durur: `skill/motion-design/scripts/tts_elevenlabs.py`. Her TTS çağrısı bu betikten geçer. Kullanıcı istemedikçe değiştirme (geçici değişiklik için env: `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL_ID`, `ELEVENLABS_OUTPUT_FORMAT`).

- **Ses**: Atakan, `e9a1KJ0kRpwPORrz92UT` (Türkçe, İstanbul aksanı, kütüphane sesi; API'de ücretli plan gerekir).
- **Model**: `eleven_v4`. TTS uç noktası modeli reddederse Text to Dialogue API'yi tek input (bu ses) ile kullan; betik bunu kendisi yapar.
- **Ses ayarı gönderme**: `voice_settings` yok (stability, similarity, style, speed). Ses kendi kayıtlı ayarlarıyla okur. Eski varsayılanlar (`eleven_multilingual_v2`, stability 0.85) düz ve robotik Türkçe üretiyordu; onlara dönme.
- **Çıktı**: `mp3_44100_128`, `out/` altına (git'e girmez).
- **Metin**: Seslendirme metnini konuşma diliyle, tam cümlelerle yaz. Ekrandaki slogan parçalarını ("Peki ya mesajlar?" gibi) olduğu gibi okutma; tonlamayı bozar. Ekran metni ile seslendirme metni ayrı tutulur.
- **Kredi**: Deneme için tek kısa cümle, tek ses. Aynı metni birden çok sesle deneme.
- **Anahtar**: Betik `ELEVENLABS_API_KEY` varsa onu gönderir, yoksa anahtarı proxy ekler. Anahtarı sohbette isteme. 401/403 alırsan güvenli formu aç (`api.elevenlabs.io`, header `xi-api-key`). 402 `paid_plan_required` anahtar değil plan sorunudur; kullanıcıya söyle.
