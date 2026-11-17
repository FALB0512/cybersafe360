from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path
from datetime import date
from functools import wraps

app = Flask(__name__)
app.secret_key = "cybersafe360-demo-secret-key"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "cybersafe360.db"

DEMO_USER = {
    "email": "admin@totalsecurity.com",
    "password": "TotalSecurity360!",
    "name": "Administrador TotalSecurity",
    "role": "Consultor"
}

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


def get_db():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        razon_social TEXT NOT NULL,
        nit TEXT,
        sector TEXT,
        empleados INTEGER,
        contacto TEXT,
        correo TEXT,
        estado TEXT DEFAULT 'Activo'
    );

    CREATE TABLE IF NOT EXISTS evaluaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        puntaje INTEGER NOT NULL,
        nivel TEXT NOT NULL,
        responsable TEXT,
        observacion TEXT,
        FOREIGN KEY (empresa_id) REFERENCES empresas(id)
    );

    CREATE TABLE IF NOT EXISTS controles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dominio TEXT NOT NULL,
        pregunta TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS respuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evaluacion_id INTEGER NOT NULL,
        control_id INTEGER NOT NULL,
        resultado INTEGER NOT NULL,
        observacion TEXT,
        FOREIGN KEY (evaluacion_id) REFERENCES evaluaciones(id),
        FOREIGN KEY (control_id) REFERENCES controles(id)
    );

    CREATE TABLE IF NOT EXISTS hallazgos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER NOT NULL,
        codigo TEXT NOT NULL,
        titulo TEXT NOT NULL,
        descripcion TEXT,
        probabilidad INTEGER NOT NULL,
        impacto INTEGER NOT NULL,
        riesgo INTEGER NOT NULL,
        criticidad TEXT NOT NULL,
        recomendacion TEXT,
        estado TEXT DEFAULT 'Pendiente',
        control_id INTEGER,
        evaluacion_id INTEGER,
        FOREIGN KEY (empresa_id) REFERENCES empresas(id),
        FOREIGN KEY (control_id) REFERENCES controles(id),
        FOREIGN KEY (evaluacion_id) REFERENCES evaluaciones(id)
    );

    CREATE TABLE IF NOT EXISTS planes_accion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hallazgo_id INTEGER NOT NULL,
        actividad TEXT NOT NULL,
        responsable TEXT,
        fecha_limite TEXT,
        avance INTEGER DEFAULT 0,
        estado TEXT DEFAULT 'Pendiente',
        FOREIGN KEY (hallazgo_id) REFERENCES hallazgos(id)
    );
    """)

    # Add potentially missing columns on previous DBs
    for table, column, ddl in [
        ("evaluaciones", "observacion", "ALTER TABLE evaluaciones ADD COLUMN observacion TEXT"),
        ("hallazgos", "control_id", "ALTER TABLE hallazgos ADD COLUMN control_id INTEGER"),
        ("hallazgos", "evaluacion_id", "ALTER TABLE hallazgos ADD COLUMN evaluacion_id INTEGER"),
    ]:
        cols = [r["name"] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            cur.execute(ddl)

    if cur.execute("SELECT COUNT(*) FROM controles").fetchone()[0] == 0:
        cur.executemany("INSERT INTO controles (dominio, pregunta, activo) VALUES (?, ?, 1)", CONTROLES_BASE)

    if cur.execute("SELECT COUNT(*) FROM empresas").fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO empresas (razon_social, nit, sector, empleados, contacto, correo, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Ingeniería Andina SAS", "901.555.321-7", "Ingeniería y construcción",
            85, "Laura Martínez", "laura@ingenieriaandina.test", "Activo"
        ))
        empresa_id = cur.lastrowid

        evaluaciones = [
            (empresa_id, "2026-05-15", 48, "Alto", "Administrador TotalSecurity", "Evaluación histórica de demostración"),
            (empresa_id, "2026-06-15", 53, "Alto", "Administrador TotalSecurity", "Evaluación histórica de demostración"),
            (empresa_id, "2026-07-15", 58, "Alto", "Administrador TotalSecurity", "Evaluación histórica de demostración"),
            (empresa_id, "2026-08-15", 63, "Medio", "Administrador TotalSecurity", "Evaluación histórica de demostración"),
        ]
        cur.executemany("""
        INSERT INTO evaluaciones (empresa_id, fecha, puntaje, nivel, responsable, observacion)
        VALUES (?, ?, ?, ?, ?, ?)
        """, evaluaciones)

        hallazgos = [
            ("CYB-001", "MFA incompleto en cuentas administrativas",
             "Se identificaron cuentas privilegiadas protegidas únicamente con contraseña.",
             4, 4, 16, "Crítico",
             "Habilitar MFA para el 100% de las cuentas administrativas.", "En progreso"),
            ("CYB-002", "Copias de seguridad sin prueba de restauración",
             "Existen respaldos, pero no se evidencia prueba periódica de recuperación.",
             3, 4, 12, "Crítico",
             "Definir y ejecutar pruebas trimestrales de restauración.", "Pendiente"),
            ("CYB-003", "Usuarios antiguos activos",
             "Se encontraron cuentas asociadas a personal que ya no requiere acceso.",
             3, 3, 9, "Alto",
             "Depurar usuarios y formalizar procedimiento de retiro.", "En progreso"),
            ("CYB-004", "Capacitación insuficiente frente a phishing",
             "No existe un ciclo periódico de sensibilización y simulación.",
             3, 3, 9, "Alto",
             "Implementar campaña trimestral de cultura de ciberseguridad.", "Pendiente"),
            ("CYB-005", "Procedimiento de incidentes no formalizado",
             "La organización no cuenta con flujo documentado de reporte y escalamiento.",
             2, 3, 6, "Medio",
             "Documentar roles, canales y tiempos de respuesta.", "Pendiente"),
        ]
        hallazgo_ids = []
        for h in hallazgos:
            cur.execute("""
            INSERT INTO hallazgos
            (empresa_id, codigo, titulo, descripcion, probabilidad, impacto, riesgo,
             criticidad, recomendacion, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (empresa_id, *h))
            hallazgo_ids.append(cur.lastrowid)

        planes = [
            (hallazgo_ids[0], "Activar MFA en cuentas privilegiadas", "Administrador TI", "2026-08-31", 60, "En progreso"),
            (hallazgo_ids[1], "Realizar prueba documentada de restauración", "Infraestructura", "2026-09-10", 20, "En progreso"),
            (hallazgo_ids[2], "Depurar cuentas y revisar privilegios", "Administrador TI", "2026-08-25", 70, "En progreso"),
            (hallazgo_ids[3], "Ejecutar campaña de phishing simulado", "Talento Humano / TI", "2026-09-20", 35, "En progreso"),
            (hallazgo_ids[4], "Aprobar procedimiento de gestión de incidentes", "Gerencia / TI", "2026-09-30", 15, "Pendiente"),
        ]
        cur.executemany("""
        INSERT INTO planes_accion
        (hallazgo_id, actividad, responsable, fecha_limite, avance, estado)
        VALUES (?, ?, ?, ?, ?, ?)
        """, planes)

    conn.commit()
    conn.close()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def nivel_desde_puntaje(puntaje):
    if puntaje <= 39:
        return "Crítico"
    elif puntaje <= 59:
        return "Alto"
    elif puntaje <= 79:
        return "Medio"
    elif puntaje <= 89:
        return "Aceptable"
    return "Fortalecido"


def criticidad_desde_riesgo(riesgo):
    if riesgo >= 12:
        return "Crítico"
    elif riesgo >= 8:
        return "Alto"
    elif riesgo >= 4:
        return "Medio"
    return "Bajo"


@app.route("/")
def inicio():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if email == DEMO_USER["email"] and password == DEMO_USER["password"]:
            session["user"] = DEMO_USER
            return redirect(url_for("dashboard"))
        flash("Correo o contraseña incorrectos.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    empresa = conn.execute("SELECT * FROM empresas ORDER BY id LIMIT 1").fetchone()
    evaluaciones = conn.execute("""
        SELECT * FROM evaluaciones WHERE empresa_id=? ORDER BY fecha, id
    """, (empresa["id"],)).fetchall()
    ultima = evaluaciones[-1] if evaluaciones else None

    counts = {}
    for crit in ("Crítico", "Alto", "Medio"):
        counts[crit] = conn.execute("""
            SELECT COUNT(*) c FROM hallazgos
            WHERE empresa_id=? AND criticidad=? AND estado!='Cerrado'
        """, (empresa["id"], crit)).fetchone()["c"]

    promedio_avance = conn.execute("SELECT COALESCE(AVG(avance),0) a FROM planes_accion").fetchone()["a"]
    nsm_total = conn.execute("""
        SELECT COUNT(*) c FROM hallazgos
        WHERE empresa_id=? AND criticidad IN ('Crítico','Alto')
    """, (empresa["id"],)).fetchone()["c"]
    nsm_mitigados = conn.execute("""
        SELECT COUNT(*) c FROM hallazgos
        WHERE empresa_id=? AND criticidad IN ('Crítico','Alto') AND estado='Cerrado'
    """, (empresa["id"],)).fetchone()["c"]

    dominios = []
    if ultima:
        rows = conn.execute("""
            SELECT c.dominio,
                   ROUND(100.0 * SUM(r.resultado) / (COUNT(*) * 2), 0) AS pct
            FROM respuestas r
            JOIN controles c ON c.id=r.control_id
            WHERE r.evaluacion_id=?
            GROUP BY c.dominio
            ORDER BY c.id
        """, (ultima["id"],)).fetchall()
        dominios = [(r["dominio"], int(r["pct"])) for r in rows]

    if not dominios:
        dominios = [
            ("Identidad y accesos", 52),
            ("Protección de información", 71),
            ("Equipos y red", 66),
            ("Correo y servicios digitales", 58),
            ("Gestión organizacional", 61),
            ("Cultura de ciberseguridad", 72),
        ]

    conn.close()
    return render_template(
        "dashboard.html", empresa=empresa, evaluaciones=evaluaciones, ultima=ultima,
        criticos=counts["Crítico"], altos=counts["Alto"], medios=counts["Medio"],
        promedio_avance=round(promedio_avance),
        dominios=dominios, nsm_total=nsm_total, nsm_mitigados=nsm_mitigados
    )


@app.route("/empresas")
@login_required
def empresas():
    conn = get_db()
    data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
    conn.close()
    return render_template("empresas.html", empresas=data)


@app.route("/empresas/nueva", methods=["POST"])
@login_required
def nueva_empresa():
    conn = get_db()
    conn.execute("""
        INSERT INTO empresas (razon_social, nit, sector, empleados, contacto, correo, estado)
        VALUES (?, ?, ?, ?, ?, ?, 'Activo')
    """, (
        request.form["razon_social"], request.form.get("nit"), request.form.get("sector"),
        request.form.get("empleados") or 0, request.form.get("contacto"), request.form.get("correo")
    ))
    conn.commit()
    conn.close()
    flash("Empresa registrada correctamente.", "success")
    return redirect(url_for("empresas"))


@app.route("/evaluaciones")
@login_required
def evaluaciones():
    conn = get_db()
    data = conn.execute("""
        SELECT e.*, em.razon_social
        FROM evaluaciones e JOIN empresas em ON em.id=e.empresa_id
        ORDER BY e.fecha DESC, e.id DESC
    """).fetchall()
    empresas_data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
    conn.close()
    return render_template("evaluaciones.html", evaluaciones=data, empresas=empresas_data)


@app.route("/evaluaciones/nueva")
@login_required
def nueva_evaluacion_form():
    conn = get_db()
    empresas_data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
    controles = conn.execute("SELECT * FROM controles WHERE activo=1 ORDER BY id").fetchall()
    conn.close()

    agrupados = {}
    for c in controles:
        agrupados.setdefault(c["dominio"], []).append(c)
    return render_template("evaluacion_form.html", empresas=empresas_data, grupos=agrupados)


@app.route("/evaluaciones/guardar", methods=["POST"])
@login_required
def guardar_evaluacion():
    empresa_id = int(request.form["empresa_id"])
    fecha_eval = request.form.get("fecha") or date.today().isoformat()

    conn = get_db()
    controles = conn.execute("SELECT * FROM controles WHERE activo=1 ORDER BY id").fetchall()

    total = 0
    maximo = len(controles) * 2
    respuestas = []

    for c in controles:
        key = f"control_{c['id']}"
        resultado = int(request.form.get(key, 0))
        total += resultado
        respuestas.append((c["id"], resultado, request.form.get(f"obs_{c['id']}", "").strip()))

    puntaje = round((total / maximo) * 100) if maximo else 0
    nivel = nivel_desde_puntaje(puntaje)

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO evaluaciones (empresa_id, fecha, puntaje, nivel, responsable, observacion)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (empresa_id, fecha_eval, puntaje, nivel, session["user"]["name"],
          "Puntaje calculado automáticamente a partir de controles"))
    evaluacion_id = cur.lastrowid

    for control_id, resultado, observacion in respuestas:
        cur.execute("""
            INSERT INTO respuestas (evaluacion_id, control_id, resultado, observacion)
            VALUES (?, ?, ?, ?)
        """, (evaluacion_id, control_id, resultado, observacion))

        # Si no cumple, crear hallazgo sugerido automáticamente.
        if resultado == 0:
            control = next(c for c in controles if c["id"] == control_id)
            next_num = cur.execute("SELECT COUNT(*) + 1 n FROM hallazgos").fetchone()["n"]
            codigo = f"CYB-{next_num:03d}"

            # Priorización base: el consultor luego puede ajustar.
            prob, impacto = 3, 3
            riesgo = prob * impacto
            criticidad = criticidad_desde_riesgo(riesgo)

            cur.execute("""
                INSERT INTO hallazgos
                (empresa_id, codigo, titulo, descripcion, probabilidad, impacto, riesgo,
                 criticidad, recomendacion, estado, control_id, evaluacion_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?, ?)
            """, (
                empresa_id, codigo,
                f"Control no implementado: {control['pregunta'][:85]}",
                f"Durante la evaluación se registró 'No cumple' para el control del dominio {control['dominio']}. "
                + (f"Observación: {observacion}" if observacion else ""),
                prob, impacto, riesgo, criticidad,
                RECOMENDACIONES_CONTROLES.get(
                    control["pregunta"],
                    "Definir una acción correctiva, responsable y fecha de implementación."
                ),
                control_id, evaluacion_id
            ))

    conn.commit()
    conn.close()

    flash(f"Evaluación completada. Índice TotalSecurity: {puntaje}/100 · Nivel {nivel}.", "success")
    return redirect(url_for("resultado_evaluacion", evaluacion_id=evaluacion_id))


@app.route("/evaluaciones/<int:evaluacion_id>/resultado")
@login_required
def resultado_evaluacion(evaluacion_id):
    conn = get_db()
    evaluacion = conn.execute("""
        SELECT e.*, em.razon_social
        FROM evaluaciones e JOIN empresas em ON em.id=e.empresa_id
        WHERE e.id=?
    """, (evaluacion_id,)).fetchone()

    dominios = conn.execute("""
        SELECT c.dominio,
               COUNT(*) total_controles,
               SUM(r.resultado) puntos,
               ROUND(100.0 * SUM(r.resultado) / (COUNT(*) * 2), 0) pct
        FROM respuestas r
        JOIN controles c ON c.id=r.control_id
        WHERE r.evaluacion_id=?
        GROUP BY c.dominio
        ORDER BY MIN(c.id)
    """, (evaluacion_id,)).fetchall()

    no_cumple = conn.execute("""
        SELECT c.dominio, c.pregunta, r.observacion
        FROM respuestas r
        JOIN controles c ON c.id=r.control_id
        WHERE r.evaluacion_id=? AND r.resultado=0
        ORDER BY c.id
    """, (evaluacion_id,)).fetchall()

    conn.close()
    return render_template("evaluacion_resultado.html", evaluacion=evaluacion, dominios=dominios, no_cumple=no_cumple)


@app.route("/hallazgos")
@login_required
def hallazgos():
    conn = get_db()
    data = conn.execute("""
        SELECT h.*, em.razon_social
        FROM hallazgos h JOIN empresas em ON em.id=h.empresa_id
        ORDER BY CASE h.criticidad WHEN 'Crítico' THEN 1 WHEN 'Alto' THEN 2 WHEN 'Medio' THEN 3 ELSE 4 END, h.id DESC
    """).fetchall()
    empresas_data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
    conn.close()
    return render_template("hallazgos.html", hallazgos=data, empresas=empresas_data)


@app.route("/hallazgos/nuevo", methods=["POST"])
@login_required
def nuevo_hallazgo():
    prob = int(request.form["probabilidad"])
    impact = int(request.form["impacto"])
    riesgo = prob * impact
    criticidad = criticidad_desde_riesgo(riesgo)

    conn = get_db()
    next_num = conn.execute("SELECT COUNT(*) + 1 n FROM hallazgos").fetchone()["n"]
    codigo = f"CYB-{next_num:03d}"
    conn.execute("""
        INSERT INTO hallazgos
        (empresa_id, codigo, titulo, descripcion, probabilidad, impacto, riesgo,
         criticidad, recomendacion, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente')
    """, (
        request.form["empresa_id"], codigo, request.form["titulo"], request.form.get("descripcion"),
        prob, impact, riesgo, criticidad, request.form.get("recomendacion")
    ))
    conn.commit()
    conn.close()
    flash(f"Hallazgo {codigo} creado con criticidad {criticidad}.", "success")
    return redirect(url_for("hallazgos"))


@app.route("/hallazgos/<int:hallazgo_id>/cerrar", methods=["POST"])
@login_required
def cerrar_hallazgo(hallazgo_id):
    conn = get_db()
    conn.execute("UPDATE hallazgos SET estado='Cerrado' WHERE id=?", (hallazgo_id,))
    conn.commit()
    conn.close()
    flash("Hallazgo marcado como cerrado. La North Star Metric se actualizará en el dashboard.", "success")
    return redirect(url_for("hallazgos"))


@app.route("/planes")
@login_required
def planes():
    conn = get_db()
    data = conn.execute("""
        SELECT p.*, h.codigo, h.titulo, h.criticidad, h.estado AS hallazgo_estado, em.razon_social
        FROM planes_accion p
        JOIN hallazgos h ON h.id=p.hallazgo_id
        JOIN empresas em ON em.id=h.empresa_id
        ORDER BY p.fecha_limite
    """).fetchall()
    hallazgos_data = conn.execute("""
        SELECT h.id, h.codigo, h.titulo, em.razon_social
        FROM hallazgos h JOIN empresas em ON em.id=h.empresa_id
        WHERE h.estado!='Cerrado'
        ORDER BY h.id DESC
    """).fetchall()
    conn.close()
    return render_template("planes.html", planes=data, hallazgos=hallazgos_data)


@app.route("/planes/nuevo", methods=["POST"])
@login_required
def nuevo_plan():
    avance = max(0, min(100, int(request.form.get("avance") or 0)))
    estado = "Completado" if avance == 100 else ("En progreso" if avance > 0 else "Pendiente")
    conn = get_db()
    conn.execute("""
        INSERT INTO planes_accion (hallazgo_id, actividad, responsable, fecha_limite, avance, estado)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        request.form["hallazgo_id"], request.form["actividad"], request.form.get("responsable"),
        request.form.get("fecha_limite"), avance, estado
    ))
    conn.commit()
    conn.close()
    flash("Plan de acción registrado.", "success")
    return redirect(url_for("planes"))


@app.route("/planes/<int:plan_id>/avance", methods=["POST"])
@login_required
def actualizar_avance(plan_id):
    avance = max(0, min(100, int(request.form["avance"])))
    estado = "Completado" if avance == 100 else ("En progreso" if avance > 0 else "Pendiente")

    conn = get_db()
    plan = conn.execute("SELECT * FROM planes_accion WHERE id=?", (plan_id,)).fetchone()
    conn.execute("UPDATE planes_accion SET avance=?, estado=? WHERE id=?", (avance, estado, plan_id))
    if avance == 100 and request.form.get("cerrar_hallazgo") == "1":
        conn.execute("UPDATE hallazgos SET estado='Cerrado' WHERE id=?", (plan["hallazgo_id"],))
    conn.commit()
    conn.close()
    flash("Avance actualizado.", "success")
    return redirect(url_for("planes"))


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
