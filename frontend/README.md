# Frontend

This directory contains the Flutter application shell for فهمان.

The first release targets a single host device shared by both teams. Flutter
will render the Arabic RTL experience, preload question media, display the
timer, submit game commands, and restore an active match after interruption.

The backend remains authoritative for question allocation, game state,
lifelines, turns, and points.

## Included milestone

- RTL Arabic theme and responsive navigation
- Google Sign-In 7.x integration and secure token storage
- A reviewable demo mode that needs no credentials
- Backend-powered eligible-category selection
- Team setup and match creation
- Manual or random eligible-category selection for 3–7 categories
- Responsive game board with real question opening and Double Points timing
- Text, image, audio, and video question presentation
- Authoritative media readiness, play limits, timer, reveal, lifelines, and scoring

## Run locally

The project is verified with Flutter 3.35.3 and Dart 3.9.2. Android, iOS, and
web platform folders have been generated. Run from this directory:

```powershell
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/v1
```

For real Google sign-in, configure each platform following the
`google_sign_in` package instructions and provide the appropriate client IDs:

```powershell
flutter run `
  --dart-define=API_BASE_URL=https://YOUR-RAILWAY-DOMAIN/v1 `
  --dart-define=GOOGLE_SERVER_CLIENT_ID=YOUR-WEB-OAUTH-CLIENT-ID
```
