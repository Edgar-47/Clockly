# ClockLy API v1

Base URL local: `http://127.0.0.1:8000/api/v1`

## Autenticacion

Flutter usa `Authorization: Bearer <token>`. La web tambien puede usar la cookie
HttpOnly `clockly_access_token`.

### POST `/auth/login`

Request:

```json
{
  "identifier": "12345678A",
  "password": "clave123"
}
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": {},
  "businesses": [],
  "active_business_id": "uuid",
  "active_business_role": "employee",
  "permissions": ["attendance:self"]
}
```

### POST `/auth/logout`

Limpia la cookie API y devuelve `{ "ok": true }`.

### GET `/auth/me`

Devuelve la sesion API actual, negocio activo, negocios disponibles y permisos.

## Negocios

- `GET /businesses`
- `POST /businesses`
- `PUT /businesses/{id}`
- `DELETE /businesses/{id}`
- `POST /businesses/switch`

`DELETE` es soft delete: marca `businesses.is_active = false` y deshabilita
membresias.

## Empleados

- `GET /employees`
- `POST /employees`
- `GET /employees/{id}`
- `PUT /employees/{id}`
- `DELETE /employees/{id}`

`DELETE` deshabilita la membresia del usuario en el negocio activo, no borra el
usuario global.

## Fichajes

- `GET /attendance`
- `POST /attendance/clock-in`
- `POST /attendance/clock-out`
- `GET /attendance/history`

Los empleados fichan sobre su propio usuario. Los roles con `attendance:manage`
pueden operar sobre `employee_id` explicito.

## Dashboard Y Permisos

- `GET /dashboard/summary`
- `GET /roles/permissions`

## Errores

Todas las respuestas de error propias de la API siguen este formato:

```json
{
  "error": {
    "code": "permission_denied",
    "message": "No tienes permisos para realizar esta accion.",
    "details": {}
  }
}
```

Codigos comunes:

- `unauthorized`
- `invalid_credentials`
- `permission_denied`
- `business_required`
- `not_found`
- `validation_error`
