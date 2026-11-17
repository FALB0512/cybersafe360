# TotalSecurity — PMV v4

Versión universitaria funcional de una plataforma de gestión de riesgo cibernético para PYMES.

## Mejoras v4

- Corrige la barra “Finalizar diagnóstico” para que no tape controles durante la evaluación.
- Mantiene 24 controles distribuidos en 6 dominios.
- Calcula automáticamente el Índice TotalSecurity y el nivel de riesgo.
- Calcula resultados por dominio.
- Los controles “No cumple” generan hallazgos automáticamente.
- Cada control incumplido ahora genera una recomendación específica, no genérica.
- Los hallazgos muestran si fueron generados desde una evaluación.
- Se agregó lectura ejecutiva automática del resultado para apoyar la sustentación.
- Cierre de hallazgos y actualización de la North Star Metric.

## Credenciales

Correo: `admin@totalsecurity.com`  
Contraseña: `TotalSecurity360!`

## Ejecutar en GitHub Codespaces

```bash
pip install -r requirements.txt
python app.py
```

Luego abre el puerto 5000.

## Para iniciar limpio

```bash
rm cybersafe360.db
python app.py
```

## Nota metodológica

El Índice TotalSecurity es una metodología propia del PMV universitario. No representa por sí mismo una certificación ISO, NIST, CIS u otro estándar.
