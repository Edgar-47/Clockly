# ClockLy

Aplicacion web para **gestionar el fichaje de entrada y salida de empleados** en restaurantes, bares y cafeterias.

El objetivo del proyecto es ofrecer una solucion **simple y segura** para registrar horas de trabajo con PostgreSQL y despliegue en Railway.

La aplicación permite gestionar empleados, registrar fichajes y exportar los datos a Excel para su análisis o control administrativo.

---

# Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python 3.11+ | Lenguaje principal |
| FastAPI | Aplicacion web y rutas HTTP |
| PostgreSQL | Base de datos principal |
| PBKDF2-SHA256 | Seguridad de contraseñas |
| OpenPyXL | Exportación a Excel |

---

# Características principales

- Interfaz moderna en **modo oscuro** diseñada para uso rápido en restaurantes  
- **Botones grandes** pensados para fichaje rápido  
- **Base de datos PostgreSQL** preparada para Railway
- **Contraseñas protegidas con hash seguro**  
- **Gestión de empleados desde panel administrador**  
- **Exportación de fichajes a Excel (.xlsx)**  
- Compatible con **Windows 10 y Windows 11**

---

# Arquitectura del proyecto

El proyecto sigue una estructura modular separando **base de datos, lógica de negocio, interfaz y utilidades**.

```
App_Fichaje/
│
├── main.py                        # Punto de entrada de la aplicación
├── requirements.txt
│
├── app/
│   ├── config.py                  # Rutas y constantes globales
│
│   ├── database/
│   │   ├── connection.py          # Conexion PostgreSQL (context manager)
│   │   ├── schema.py              # Inicialización y esquema SQL
│   │   ├── employee_repository.py
│   │   └── time_entry_repository.py
│
│   ├── models/
│   │   ├── employee.py
│   │   └── time_entry.py
│
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── employee_service.py
│   │   ├── time_clock_service.py
│   │   └── export_service.py
│
│   ├── ui/
│   │   ├── application.py         # Controlador principal (CTk)
│   │   ├── login_view.py
│   │   ├── clock_view.py
│   │   └── admin_view.py
│
│   └── utils/
│       ├── security.py
│       └── helpers.py
│
├── app/data/
│   └── .gitkeep                   # Directorio legacy, no almacena la DB activa
│
└── exports/
    └── fichajes_YYYYMMDD_HHMMSS.xlsx
```

---

# Instalación

**Requisito:** Python 3.11 o superior.

```bash
cd App_Fichaje

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

python main.py
```

## Configuracion PostgreSQL / Railway

ClockLy usa PostgreSQL mediante `DATABASE_URL`. Para desarrollo local:

```powershell
copy .env.example .env
# Edita DATABASE_URL para apuntar a tu base PostgreSQL local
python main.py
```

Variables importantes:

| Variable | Uso |
|---|---|
| `DATABASE_URL` | URL PostgreSQL de la aplicacion |
| `TEST_DATABASE_URL` | URL PostgreSQL de tests; el nombre debe contener `test` |
| `CLOCKLY_ENV` | `development` o `production` |
| `CLOCKLY_SECRET_KEY` | Secreto de sesiones; obligatorio en produccion |
| `CLOCKLY_DEFAULT_ADMIN_USERNAME` | Usuario admin inicial |
| `CLOCKLY_DEFAULT_ADMIN_PASSWORD` | Password admin de negocio inicial; obligatorio en produccion |
| `CLOCKLY_SECURE_COOKIES` | Cookies HTTPS; por defecto activo en produccion |
| `CLOCKLY_DOCS_ENABLED` | Habilita `/docs` y `/redoc` |

Despliegue en Railway:

1. Crea un servicio PostgreSQL en Railway.
2. Conecta la app al servicio para que Railway inyecte `DATABASE_URL`.
3. Define `CLOCKLY_ENV=production`, `CLOCKLY_SECRET_KEY` y `CLOCKLY_DEFAULT_ADMIN_PASSWORD`.
4. Railway ejecutara el `Procfile`: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
5. En el primer arranque se crean las tablas y el administrador inicial.

Para arrancar la aplicacion mas rapido en Windows, tambien puedes hacer doble clic en:

```bat
ejecutar_app.bat
```

---

# Primer acceso

En el primer arranque, si la base de datos está vacía, se crea automáticamente un usuario administrador de negocio. Este usuario no tiene acceso Superadmin.

| Campo | Valor |
|---|---|
| Usuario | admin |
| Contraseña | `CLOCKLY_DEFAULT_ADMIN_PASSWORD` (`Admin123` en desarrollo) |

⚠️ Se recomienda **cambiar esta contraseña antes de usar la aplicación en producción**.

### Acceso Superadmin interno

El Superadmin está separado del login normal y se accede desde `/superadmin/login`.
No hay registro público ni siembra automática de superadmins. Para crear o recuperar
el acceso usa el comando operativo con acceso a la base de datos:

```powershell
python -m app.cli.superadmin create --email owner@example.com --name "Owner Name"
```

Si no pasas `--password`, el comando la pedirá por terminal. La contraseña mínima
para Superadmin es de 12 caracteres.

---

# Flujo de uso

### Inicio de aplicación

1. Se inicializa la base de datos si no existe  
2. Se muestra la pantalla de login  

### Empleado

- Visualiza reloj en tiempo real  
- Botón **ENTRADA** para iniciar turno  
- Botón **SALIDA** para finalizar turno  
- Posibilidad de cerrar sesión  

### Administrador

Panel con tres secciones:

**Fichajes**

Visualización completa con filtro por fecha.

**Empleados**

Crear, activar o desactivar empleados.

**Exportar**

Generación de archivo Excel con los registros.

---

# Reglas de negocio

El sistema aplica varias validaciones para evitar errores de fichaje:

- No se puede registrar **entrada si ya hay una entrada abierta**
- No se puede registrar **salida sin una entrada previa**
- Los nombres de usuario deben ser **únicos**
- Los empleados **inactivos no pueden iniciar sesión**
- Las contraseñas deben tener **mínimo 6 caracteres**

---

# Almacenamiento de datos

| Tipo de dato | Ubicación |
|---|---|
| Base de datos | PostgreSQL via `DATABASE_URL` |
| Exportaciones Excel | `exports/` |

PostgreSQL es la **fuente principal de datos**.
Los archivos Excel son únicamente exportaciones para consulta.

---

# Mejoras futuras

El proyecto está diseñado para poder ampliarse fácilmente. Algunas mejoras posibles:

- Cambio de contraseña desde el panel administrador
- Filtro de fichajes por empleado
- Cálculo automático de horas trabajadas
- Alertas por turnos excesivamente largos
- Modo kiosco (pantalla completa)
- Sistema de copias de seguridad automáticas
- Estadísticas de horas por semana o mes

---

# Uso previsto

Esta aplicación está pensada para **negocios pequeños o medianos** que necesitan un sistema simple de control horario desplegable en Railway.

Ejemplos:

- Restaurantes  
- Bares  
- Cafeterías  
- Pequeños comercios
