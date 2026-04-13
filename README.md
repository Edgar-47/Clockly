# ClockLy

Aplicación de escritorio para **gestionar el fichaje de entrada y salida de empleados** en restaurantes, bares y cafeterías.

El objetivo del proyecto es ofrecer una solución **local, simple y segura** para registrar horas de trabajo sin necesidad de servidores externos ni sistemas complejos.

La aplicación permite gestionar empleados, registrar fichajes y exportar los datos a Excel para su análisis o control administrativo.

---

# Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python 3.11+ | Lenguaje principal |
| CustomTkinter | Interfaz gráfica moderna |
| SQLite | Base de datos local |
| PBKDF2-SHA256 | Seguridad de contraseñas |
| OpenPyXL | Exportación a Excel |

---

# Características principales

- Interfaz moderna en **modo oscuro** diseñada para uso rápido en restaurantes  
- **Botones grandes** pensados para fichaje rápido  
- **Base de datos local SQLite** (no requiere servidor)  
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
│   │   ├── connection.py          # Conexión SQLite (context manager)
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
│   └── fichaje.sqlite3            # Base de datos (creación automática)
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

Para arrancar la aplicacion mas rapido en Windows, tambien puedes hacer doble clic en:

```bat
ejecutar_app.bat
```

---

# Primer acceso

En el primer arranque, si la base de datos está vacía, se crea automáticamente un usuario administrador.

| Campo | Valor |
|---|---|
| Usuario | admin |
| Contraseña | admin123 |

⚠️ Se recomienda **cambiar esta contraseña antes de usar la aplicación en producción**.

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
| Base de datos | `app/data/fichaje.sqlite3` |
| Exportaciones Excel | `exports/` |

SQLite es la **fuente principal de datos**.  
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

Esta aplicación está pensada para **negocios pequeños o medianos** que necesitan un sistema simple de control horario sin depender de servicios en la nube.

Ejemplos:

- Restaurantes  
- Bares  
- Cafeterías  
- Pequeños comercios
