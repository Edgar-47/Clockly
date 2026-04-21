# ClockLy Mobile

Flutter mobile app for ClockLy. This app does not connect to the database
directly; it consumes the ClockLy Platform API under `/api/v1`.

## Stack

- Flutter/Dart
- Riverpod for state management
- GoRouter for navigation
- `http` for API calls
- `flutter_secure_storage` for token storage
- Android and iOS platform targets

## Structure

```text
clockly-mobile/
  android/           # Android app target
  ios/               # iOS app target
  assets/brand/      # ClockLy brand assets
  lib/
    core/            # config, routing, network, theme, storage
    data/            # datasources and API models
    domain/          # entities
    features/        # screens and providers by product area
    shared/          # reusable widgets/extensions
  test/
```

## Run locally

Start `clockly-platform` first on port 8000.

```bash
flutter pub get
flutter run --dart-define=CLOCKLY_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Android emulator usually needs the host alias:

```bash
flutter run --dart-define=CLOCKLY_API_BASE_URL=http://10.0.2.2:8000/api/v1
```

## Production builds

Use HTTPS:

```bash
flutter build apk --release --dart-define=CLOCKLY_API_BASE_URL=https://your-domain.example/api/v1
flutter build ios --release --dart-define=CLOCKLY_API_BASE_URL=https://your-domain.example/api/v1
```

Release builds fail fast if `CLOCKLY_API_BASE_URL` does not use HTTPS.

## Configuration

`.env.example` documents the expected API base URL, but Flutter does not load it
automatically. Pass values with `--dart-define`.

| Value | Purpose |
| --- | --- |
| `CLOCKLY_API_BASE_URL` | Base URL for ClockLy Platform API v1 |

## Backend connection

The app expects ClockLy Platform endpoints documented in
`clockly-platform/docs/contracts/api_v1.md`, especially:

- `POST /auth/login`
- `GET /auth/me`
- `POST /businesses/switch`
- `GET /attendance`
- `POST /attendance/clock-in`
- `POST /attendance/clock-out`
- `GET /attendance/history`

## Checks

```bash
flutter analyze
flutter test
```

Before store distribution, replace Android debug signing, configure iOS signing
and review package identifiers with the final company account.
