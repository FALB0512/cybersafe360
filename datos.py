"""Catálogo de controles y recomendaciones de CyberSafe/TotalSecurity."""

CONTROLES_BASE = [
    ("Identidad y accesos", "¿Se utiliza autenticación multifactor (MFA) en las cuentas administrativas?"),
    ("Identidad y accesos", "¿Existe una política formal de contraseñas?"),
    ("Identidad y accesos", "¿Se eliminan o deshabilitan oportunamente las cuentas de exempleados?"),
    ("Identidad y accesos", "¿Se revisan periódicamente los privilegios de acceso?"),

    ("Protección de información", "¿La organización realiza copias de seguridad periódicas?"),
    ("Protección de información", "¿Se realizan pruebas de restauración de copias de seguridad?"),
    ("Protección de información", "¿La información sensible se encuentra clasificada?"),
    ("Protección de información", "¿Los permisos sobre información sensible se revisan periódicamente?"),

    ("Equipos y red", "¿Los equipos reciben actualizaciones y parches de seguridad de forma periódica?"),
    ("Equipos y red", "¿Los equipos cuentan con protección antimalware o EDR?"),
    ("Equipos y red", "¿La organización utiliza firewall para proteger sus redes?"),
    ("Equipos y red", "¿Se controla el acceso a las redes inalámbricas corporativas?"),

    ("Correo y servicios digitales", "¿Las cuentas de correo corporativo utilizan MFA?"),
    ("Correo y servicios digitales", "¿Existen filtros o controles contra phishing y correo malicioso?"),
    ("Correo y servicios digitales", "¿Se revisan configuraciones de seguridad de servicios en la nube?"),
    ("Correo y servicios digitales", "¿Existe un proceso para reportar correos sospechosos?"),

    ("Gestión organizacional", "¿Existe una política de seguridad de la información aprobada?"),
    ("Gestión organizacional", "¿Se han definido responsables de ciberseguridad o seguridad de la información?"),
    ("Gestión organizacional", "¿Existe un procedimiento formal de gestión de incidentes?"),
    ("Gestión organizacional", "¿Se realiza una revisión periódica de riesgos de seguridad?"),

    ("Cultura de ciberseguridad", "¿Los colaboradores reciben capacitación periódica en ciberseguridad?"),
    ("Cultura de ciberseguridad", "¿Se realizan campañas o simulaciones de phishing?"),
    ("Cultura de ciberseguridad", "¿Los usuarios conocen buenas prácticas sobre contraseñas y MFA?"),
    ("Cultura de ciberseguridad", "¿Los colaboradores saben cómo reportar un incidente de seguridad?")

]

RECOMENDACIONES_CONTROLES = {
    "¿Se utiliza autenticación multifactor (MFA) en las cuentas administrativas?":
        "Habilitar MFA para el 100% de las cuentas administrativas y privilegiadas, priorizando aplicaciones críticas y servicios en la nube.",
    "¿Existe una política formal de contraseñas?":
        "Definir, aprobar y comunicar una política de contraseñas que contemple longitud mínima, bloqueo, reutilización y uso de gestores de contraseñas.",
    "¿Se eliminan o deshabilitan oportunamente las cuentas de exempleados?":
        "Implementar un procedimiento formal de retiro que deshabilite cuentas y revoque accesos inmediatamente al finalizar la relación laboral.",
    "¿Se revisan periódicamente los privilegios de acceso?":
        "Realizar revisiones periódicas de privilegios bajo el principio de mínimo privilegio y documentar las aprobaciones de acceso.",
    "¿La organización realiza copias de seguridad periódicas?":
        "Establecer un esquema de copias de seguridad con frecuencia definida, responsables, retención y monitoreo de ejecuciones fallidas.",
    "¿Se realizan pruebas de restauración de copias de seguridad?":
        "Programar y documentar pruebas periódicas de restauración para verificar que los respaldos puedan recuperarse dentro de los tiempos requeridos.",
    "¿La información sensible se encuentra clasificada?":
        "Definir una política de clasificación de información y aplicar niveles de sensibilidad, responsables y reglas de manejo para cada categoría.",
    "¿Los permisos sobre información sensible se revisan periódicamente?":
        "Revisar periódicamente permisos y grupos de acceso sobre información sensible, eliminando accesos innecesarios o desactualizados.",
    "¿Los equipos reciben actualizaciones y parches de seguridad de forma periódica?":
        "Implementar un proceso de gestión de parches con inventario, criticidad, tiempos máximos de instalación y verificación de cumplimiento.",
    "¿Los equipos cuentan con protección antimalware o EDR?":
        "Implementar y mantener protección antimalware/EDR administrada, con actualizaciones automáticas y monitoreo de alertas.",
    "¿La organización utiliza firewall para proteger sus redes?":
        "Implementar o fortalecer firewall perimetral y reglas de filtrado, documentando servicios expuestos y revisando periódicamente las reglas.",
    "¿Se controla el acceso a las redes inalámbricas corporativas?":
        "Separar redes corporativas e invitados, usar cifrado robusto y gestionar credenciales de acceso de forma controlada.",
    "¿Las cuentas de correo corporativo utilizan MFA?":
        "Habilitar MFA para todas las cuentas de correo corporativo, priorizando usuarios con acceso a información sensible o funciones administrativas.",
    "¿Existen filtros o controles contra phishing y correo malicioso?":
        "Configurar filtros antiphishing, antispam y análisis de adjuntos/enlaces, complementados con campañas de sensibilización.",
    "¿Se revisan configuraciones de seguridad de servicios en la nube?":
        "Realizar revisiones periódicas de configuración segura, permisos, MFA, registros y exposición de servicios en la nube.",
    "¿Existe un proceso para reportar correos sospechosos?":
        "Definir un canal simple y visible para reportar correos sospechosos, con responsables y tiempos de análisis establecidos.",
    "¿Existe una política de seguridad de la información aprobada?":
        "Documentar, aprobar y comunicar una política de seguridad de la información alineada con los riesgos y responsabilidades de la organización.",
    "¿Se han definido responsables de ciberseguridad o seguridad de la información?":
        "Asignar formalmente responsables, roles y responsabilidades para la gestión de ciberseguridad y seguridad de la información.",
    "¿Existe un procedimiento formal de gestión de incidentes?":
        "Diseñar y aprobar un procedimiento de gestión de incidentes con etapas de detección, reporte, contención, recuperación y lecciones aprendidas.",
    "¿Se realiza una revisión periódica de riesgos de seguridad?":
        "Establecer revisiones periódicas de riesgos con responsables, criterios de valoración, planes de tratamiento y seguimiento.",
    "¿Los colaboradores reciben capacitación periódica en ciberseguridad?":
        "Implementar un programa periódico de formación en ciberseguridad adaptado a los riesgos y roles de los colaboradores.",
    "¿Se realizan campañas o simulaciones de phishing?":
        "Ejecutar simulaciones de phishing periódicas y utilizar los resultados para dirigir refuerzos formativos a los grupos con mayor exposición.",
    "¿Los usuarios conocen buenas prácticas sobre contraseñas y MFA?":
        "Reforzar prácticas de contraseñas seguras, gestores de contraseñas y MFA mediante capacitación y comunicaciones periódicas.",
    "¿Los colaboradores saben cómo reportar un incidente de seguridad?":
        "Definir y divulgar un canal de reporte de incidentes, indicando qué reportar, a quién, cómo y en qué plazo."
}
