# TotalSecurity — PMV

Plataforma de gestión de riesgo cibernético para PYMES: evaluación de 24 controles en 6 dominios, cálculo del Índice TotalSecurity, hallazgos automáticos y plan de acción.

## Estructura

```
app.py            Rutas Flask, lógica de evaluación y base de datos SQLite
datos.py          Catálogo de controles y recomendaciones
templates/        Plantillas HTML (Jinja2)
static/css/       Estilos
static/img/       Logos
```

## Ejecutar

```bash
pip install -r requirements.txt
python app.py
```

Luego abre `http://localhost:5000`.

## Perfiles de acceso

| Perfil | Correo | Contraseña | Acceso |
|---|---|---|---|
| Administrador | `admin@totalsecurity.com` | `TotalSecurity360!` | Todo, incluido Usuarios y perfiles |
| Consultor | `consultor@totalsecurity.com` | `Consultor360!` | Empresas, evaluaciones, hallazgos y plan |
| Cliente | `cliente@totalsecurity.com` | `Cliente360!` | Solo lectura: dashboard, hallazgos y plan |

Estas contraseñas son de demostración. Cambia `SECRET_KEY` y las contraseñas antes de usar la herramienta con datos reales. Para activar el modo depuración usa `FLASK_DEBUG=1`.

## Iniciar con datos limpios

```bash
rm cybersafe360.db
python app.py
```

## Nota metodológica

El Índice TotalSecurity es una metodología propia del PMV universitario. No representa por sí mismo una certificación ISO, NIST, CIS u otro estándar.
