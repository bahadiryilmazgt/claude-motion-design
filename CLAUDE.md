# Project rules for Claude

## Voice-over / TTS: always ElevenLabs

- Every voice-over, narration or TTS in this repo is generated with the **ElevenLabs API** (`https://api.elevenlabs.io`). This overrides the Cartesia mentions in `skill/motion-design/SKILL.md`; do not use another TTS provider unless the user asks.
- **Credentials**: the key is injected by the session's network proxy. Never ask for the key in chat, never write it to a file, env var, script or commit. If a client refuses to start without one, pass a dummy `xi-api-key` value; the proxy replaces it.
- If a call returns 401/403, use the secure credential form (`request_credential`, host `api.elevenlabs.io`, header `xi-api-key`) instead of asking for the key in chat.
- **Timings**: prefer `POST /v1/text-to-speech/{voice_id}/with-timestamps`. Its character alignment becomes the single timing file (`cues.json`) that drives captions and animation cues. Fall back to whisper only if the alignment is unusable.
- **Budget**: check `GET /v1/user/subscription` (`character_count` / `character_limit`) before long generations. Generate per line or scene, cache the audio under `out/` (git-ignored) and regenerate only the lines that changed.
- **Licensing**: on the free tier, ElevenLabs output requires attribution and is not licensed for commercial use. Tell the user before delivering a commercial film made on that tier.
- Mixing stays as in the skill: music ducked ~9 dB under the voice, two-pass loudnorm to -14 LUFS.
