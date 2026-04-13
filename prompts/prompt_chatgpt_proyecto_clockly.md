# Prompt para explicar el proyecto ClockLy a ChatGPT

Quiero que actues como un arquitecto senior de software y me ayudes a continuar el desarrollo de este proyecto.

## Contexto general

Estoy desarrollando una aplicacion de escritorio llamada **ClockLy** para gestionar el fichaje de entrada y salida de empleados en restaurantes, bares, cafeterias o pequenos comercios.

La idea principal es tener una solucion local, simple y segura, sin depender de servidores externos. La aplicacion debe permitir:

- Registrar empleados.
- Iniciar sesion por DNI y contrasena.
- Fichar entrada.
- Fichar salida.
- Ver quien esta fichado en este momento.
- Consultar registros de asistencia.
- Exportar los datos a Excel.
- Gestionar empleados desde un panel administrador.

## Tecnologias actuales

El proyecto usa:

- Python 3.11 o superior.
- CustomTkinter para la interfaz grafica.
- SQLite como base de datos local.
- PBKDF2-SHA256 para proteger contrasenas.
- OpenPyXL para exportar a Excel.

Dependencias principales:

```txt
customtkinter==5.2.2
openpyxl==3.1.5
```

## Estructura aproximada del proyecto

```txt
App_Fichaje/
  main.py
  requirements.txt
  README.md

  app/
    config.py

    database/
      connection.py
      schema.py
      employee_repository.py
      attendance_session_repository.py
      time_entry_repository.py

    models/
      employee.py
      attendance_session.py
      attendance_status.py
      time_entry.py

    services/
      auth_service.py
      employee_service.py
      time_clock_service.py
      export_service.py

    ui/
      application.py
      login_view.py
      attendance_view.py
      active_employees_sidebar.py
      admin_dashboard_view.py
      theme.py

      # Pantallas antiguas que pueden estar obsoletas:
      admin_view.py
      clock_view.py
      clock_kiosk_view.py

    utils/
      security.py
      helpers.py

  app/data/
    fichaje.sqlite3

  exports/
    fichajes_YYYYMMDD_HHMMSS.xlsx
```

## Estado actual de la aplicacion

La aplicacion arranca desde `main.py`, que crea `TimeClockApplication`.

`TimeClockApplication`:

- Inicializa la base de datos.
- Crea los servicios principales:
  - `AuthService`
  - `EmployeeService`
  - `TimeClockService`
  - `ExportService`
- Muestra primero el login.
- Si entra un admin, muestra `AdminDashboardView`.
- Si entra un empleado, muestra `AttendanceView`.

El login actual usa DNI y contrasena.

El panel de empleado (`AttendanceView`) permite:

- Ver el nombre y DNI del empleado.
- Ver si esta fichado o sin fichar.
- Fichar entrada.
- Fichar salida.
- Ver un temporizador del turno activo.
- Volver al inicio para que otro empleado pueda iniciar sesion.
- Ver un panel lateral con empleados actualmente fichados.

El panel administrador (`AdminDashboardView`) permite:

- Ver empleados registrados.
- Crear empleados nuevos.
- Activar o desactivar empleados.
- Ver registros de asistencia.
- Ver metricas basicas:
  - empleados activos
  - empleados fichados ahora
  - sesiones de hoy
- Exportar registros a Excel.

## Modelo de datos actual

La base de datos tiene tablas modernas y tablas legacy.

Tablas modernas:

- `users`
- `attendance_sessions`

Tablas legacy o de compatibilidad:

- `employees`
- `time_entries`

Problema importante:

Actualmente conviven dos modelos de asistencia:

1. `time_entries`: guarda eventos sueltos de entrada/salida.
2. `attendance_sessions`: guarda sesiones completas con:
   - entrada
   - salida
   - estado activo
   - duracion total

El flujo nuevo parece estar orientado a `attendance_sessions`, pero la exportacion actual todavia usa `time_entries`.

Quiero avanzar hacia un modelo mas limpio donde `attendance_sessions` sea la fuente principal para informes, panel admin y exportaciones.

## Reglas de negocio actuales

- Un empleado inactivo no puede iniciar sesion.
- Solo empleados con rol `employee` pueden fichar.
- Los admins no fichan asistencia.
- No deberia existir mas de una sesion activa por usuario.
- La tabla `attendance_sessions` tiene un indice unico parcial para impedir varias sesiones activas por usuario.
- El DNI debe ser unico.
- La contrasena debe tener minimo 6 caracteres.
- Se crea un administrador por defecto si no existe.

Admin por defecto:

```txt
Usuario/DNI: admin
Contrasena: Admin123
```

## Cosas detectadas a revisar

- El README puede estar desactualizado respecto al estado real del proyecto.
- La exportacion Excel deberia pasar de `time_entries` a `attendance_sessions`.
- Hay pantallas antiguas posiblemente no usadas:
  - `admin_view.py`
  - `clock_view.py`
  - `clock_kiosk_view.py`
- Hay archivos sueltos de pruebas MongoDB que probablemente no pertenecen al proyecto:
  - `playground-1.mongodb.js`
  - `playground-2.mongodb.js`
  - `playground-3.mongodb.js`
  - `playground-4.mongodb.js`
  - `use('SoftDevDB');.js`
- El proyecto esta dentro de OneDrive y SQLite puede dar problemas de `disk I/O error` con archivos journal o bases temporales.
- No hay tests automatizados todavia.

## Objetivo que quiero conseguir ahora

Quiero que me ayudes a decidir e implementar los siguientes pasos para evolucionar el proyecto de forma ordenada.

Prioridades recomendadas:

1. Consolidar el modelo de datos usando `attendance_sessions` como fuente principal.
2. Actualizar la exportacion Excel para exportar sesiones completas:
   - empleado
   - DNI
   - entrada
   - salida
   - duracion
   - estado
   - notas
3. Anadir filtros en el panel administrador:
   - fecha desde
   - fecha hasta
   - empleado
   - estado abierto/cerrado
4. Anadir cambio o restablecimiento de contrasena desde admin.
5. Anadir tests automatizados de servicios y repositorios.
6. Limpiar codigo legacy que ya no se use.
7. Actualizar README.
8. Pensar en funcionalidades futuras:
   - resumen de horas por empleado
   - alertas de turnos largos
   - cierre manual de turnos abiertos
   - copia de seguridad automatica
   - modo kiosco pantalla completa

## Como quiero que me respondas

Primero analiza la arquitectura actual y dime si estas de acuerdo con las prioridades.

Despues proponme una checklist concreta de implementacion.

Cuando te pida codigo, quiero que:

- Mantengas el estilo actual del proyecto.
- No reescribas todo desde cero.
- Hagas cambios pequenos y seguros.
- Expliques que archivos tocar.
- Incluyas pruebas o smoke tests cuando sea posible.
- Evites romper compatibilidad con bases existentes.

Empieza proponiendo el primer cambio tecnico que deberia hacer y por que.
