# AGENTS.md

Guidelines for automated changes in `clockly-mobile`.

- This repo is Flutter mobile only. Do not add backend code or direct database
  access here.
- Consume ClockLy Platform through `/api/v1` using `CLOCKLY_API_BASE_URL`.
- Keep API contract changes coordinated with `clockly-platform/docs/contracts`.
- Do not commit `.env`, build output, `.dart_tool`, IDE folders or generated
  caches.
- Android and iOS are the supported MVP targets. Re-add web/desktop platforms
  only if there is a product decision to support them.
- Prefer small feature changes inside `lib/features/*` and shared widgets in
  `lib/shared/*`.
- Before finishing, run when the Flutter SDK is available:

```bash
flutter analyze
flutter test
```

If Flutter is unavailable, state that clearly in the handoff.
