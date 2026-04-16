# ClockLy Mobile Flutter

Base Flutter preparada para Android e iOS. Esta app no accede nunca a la base
de datos: consume la API REST compartida de ClockLy en `/api/v1`.

## Ejecutar

1. Instala Flutter en la maquina.
2. Desde esta carpeta ejecuta:

```bash
flutter create .
flutter pub get
flutter run --dart-define=CLOCKLY_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

En emulador Android, usa la IP del host si `127.0.0.1` no apunta al backend,
por ejemplo `http://10.0.2.2:8000/api/v1`.

## Estructura

- `lib/core`: configuracion, red, almacenamiento seguro y estado de app.
- `lib/models`: modelos DTO que reflejan contratos API.
- `lib/services`: llamadas API por dominio.
- `lib/repositories`: coordinacion entre servicios y persistencia local.
- `lib/screens`: pantallas de login, fichaje, historial, negocio y perfil.
- `lib/widgets`: componentes reutilizables.

## Funcionalidad inicial

- Login con token Bearer.
- Persistencia de token con `flutter_secure_storage`.
- Restauracion de sesion con `GET /auth/me`.
- Cambio de negocio con `POST /businesses/switch`.
- Estado actual de fichaje.
- Fichar entrada y salida.
- Historial basico de sesiones.
- Perfil y cierre de sesion.

## Pendiente

- Ejecutar `flutter analyze` y `flutter test` cuando el SDK este instalado.
- Generar iconos, splash screen y configuracion nativa.
- Anadir notificaciones, geolocalizacion y manejo offline controlado.
