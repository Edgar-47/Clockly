# ClockLy Mobile Flutter

Cliente Flutter preparado para Android, iOS y web. La app no accede nunca a la
base de datos: consume la API REST compartida de ClockLy en `/api/v1`.

## Ejecutar

1. Instala Flutter en la maquina.
2. Desde `mobile_flutter/clockly_flutter_aplication` ejecuta:

```bash
flutter pub get
flutter run --dart-define=CLOCKLY_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

En emulador Android, usa la IP del host si `127.0.0.1` no apunta al backend,
por ejemplo `http://10.0.2.2:8000/api/v1`.

## Build web preparado

```bash
flutter build web --dart-define=CLOCKLY_API_BASE_URL=https://your-production-domain.example/api/v1
```

No uses la URL de ejemplo en producción: sustitúyela por el dominio real el día
del lanzamiento.

## Estructura

- `lib/core`: configuración, red, almacenamiento seguro, rutas y tema.
- `lib/data`: datasources y modelos DTO alineados con `/api/v1`.
- `lib/domain`: entidades de negocio.
- `lib/features`: pantallas, providers y flujos de producto.
- `lib/shared`: widgets reutilizables.

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

- Ejecutar `flutter analyze` y `flutter test` cuando el SDK esté instalado.
- Sustituir iconos/splash nativos por los assets finales de marca.
- Añadir notificaciones, geolocalización y manejo offline controlado.
