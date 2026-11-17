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

Credenciales de demostración: `admin@totalsecurity.com` / `TotalSecurity360!`

## Iniciar con datos limpios

```bash
rm cybersafe360.db
python app.py
```

## Nota metodológica

El Índice TotalSecurity es una metodología propia del PMV universitario. No representa por sí mismo una certificación ISO, NIST, CIS u otro estándar.
