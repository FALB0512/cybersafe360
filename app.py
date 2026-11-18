from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import csv
import io
import os
import sqlite3
from pathlib import Path
from datetime import date
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambiar-en-produccion")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "cybersafe360.db"

ROLES = {
    "admin": "Administrador",
    "consultor": "Consultor",
    "cliente": "Cliente",
}
EDITORES = ("admin", "consultor")

USUARIOS_SEMILLA = [
    ("Administrador TotalSecurity", "admin@totalsecurity.com", "TotalSecurity360!", "admin"),
    ("Consultor TotalSecurity", "consultor@totalsecurity.com", "Consultor360!", "consultor"),
    ("Cliente Ingeniería Andina", "cliente@totalsecurity.com", "Cliente360!", "cliente"),
]

from datos import CONTROLES_BASE, RECOMENDACIONES_CONTROLES


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
        ("hallazgos", "observacion_verificacion", "ALTER TABLE hallazgos ADD COLUMN observacion_verificacion TEXT"),
        ("hallazgos", "cumplimiento", "ALTER TABLE hallazgos ADD COLUMN cumplimiento TEXT"),
    ]:
        cols = [r["name"] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            cur.execute(ddl)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        rol TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    )
    """)
    if cur.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO usuarios (nombre, correo, password_hash, rol) VALUES (?, ?, ?, ?)",
            [(n, c, generate_password_hash(pw), r) for n, c, pw, r in USUARIOS_SEMILLA]
        )

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

    cur.execute("""
        UPDATE hallazgos SET estado='Cerrado', cumplimiento='Cumplió a cabalidad',
            observacion_verificacion='Corregido según la evaluación más reciente de la empresa.'
        WHERE estado!='Cerrado' AND control_id IS NOT NULL AND EXISTS (
            SELECT 1 FROM evaluaciones e JOIN respuestas r ON r.evaluacion_id=e.id
            WHERE e.id = (SELECT e2.id FROM evaluaciones e2 WHERE e2.empresa_id=hallazgos.empresa_id
                          ORDER BY e2.fecha DESC, e2.id DESC LIMIT 1)
              AND r.control_id=hallazgos.control_id AND r.resultado>0)
    """)
    for ev_id, puntaje in cur.execute("SELECT id, puntaje FROM evaluaciones").fetchall():
        cur.execute("UPDATE evaluaciones SET nivel=? WHERE id=?", (nivel_desde_puntaje(puntaje), ev_id))

    conn.commit()
    conn.close()


def roles_required(*roles):
    def decorador(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                return redirect(url_for("login"))
            if roles and user["rol"] not in roles:
                flash("Tu perfil no tiene acceso a esta sección.", "danger")
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)
        return wrapper
    return decorador


def login_required(fn):
    return roles_required()(fn)


@app.context_processor
def permisos():
    rol = session.get("user", {}).get("rol")
    return {"puede_editar": rol in EDITORES, "es_admin": rol == "admin"}


def nivel_desde_puntaje(puntaje):
    if puntaje <= 39:
        return "Crítico"
    elif puntaje <= 59:
        return "Bajo"
    elif puntaje <= 74:
        return "Medio"
    elif puntaje <= 89:
        return "Alto"
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
        conn = get_db()
        u = conn.execute("SELECT * FROM usuarios WHERE correo=? AND activo=1", (email,)).fetchone()
        conn.close()
        if u and check_password_hash(u["password_hash"], password):
            session["user"] = {
                "id": u["id"], "name": u["nombre"], "email": u["correo"],
                "rol": u["rol"], "role": ROLES[u["rol"]],
            }
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
    empresa_id = request.args.get("empresa", type=int)
    empresa = conn.execute("SELECT * FROM empresas WHERE id=?", (empresa_id,)).fetchone() if empresa_id else None
    if not empresa:
        empresa = conn.execute("SELECT * FROM empresas ORDER BY id LIMIT 1").fetchone()
    empresas_data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
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

    promedio_avance = conn.execute("""
        SELECT COALESCE(AVG(p.avance),0) a FROM planes_accion p
        JOIN hallazgos h ON h.id=p.hallazgo_id WHERE h.empresa_id=?
    """, (empresa["id"],)).fetchone()["a"]
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
        dominios = [(d, 0) for d in dict.fromkeys(dom for dom, _ in CONTROLES_BASE)]

    conn.close()
    return render_template(
        "dashboard.html", empresa=empresa, evaluaciones=evaluaciones, ultima=ultima,
        criticos=counts["Crítico"], altos=counts["Alto"], medios=counts["Medio"],
        promedio_avance=round(promedio_avance),
        dominios=dominios, nsm_total=nsm_total, nsm_mitigados=nsm_mitigados,
        empresas=empresas_data
    )


@app.route("/empresas")
@roles_required(*EDITORES)
def empresas():
    conn = get_db()
    data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
    conn.close()
    return render_template("empresas.html", empresas=data)


@app.route("/empresas/<int:empresa_id>")
@roles_required(*EDITORES)
def empresa_panel(empresa_id):
    conn = get_db()
    empresa = conn.execute("SELECT * FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    if not empresa:
        conn.close()
        flash("La empresa no existe.", "danger")
        return redirect(url_for("empresas"))
    evaluaciones = conn.execute(
        "SELECT * FROM evaluaciones WHERE empresa_id=? ORDER BY fecha DESC, id DESC", (empresa_id,)
    ).fetchall()
    hallazgos_emp = conn.execute("""
        SELECT * FROM hallazgos WHERE empresa_id=?
        ORDER BY CASE criticidad WHEN 'Crítico' THEN 1 WHEN 'Alto' THEN 2 WHEN 'Medio' THEN 3 ELSE 4 END, id DESC
    """, (empresa_id,)).fetchall()
    planes_emp = conn.execute("""
        SELECT p.*, h.codigo, h.titulo
        FROM planes_accion p JOIN hallazgos h ON h.id=p.hallazgo_id
        WHERE h.empresa_id=? ORDER BY p.fecha_limite
    """, (empresa_id,)).fetchall()
    conn.close()

    abiertos = {c: sum(1 for h in hallazgos_emp if h["criticidad"] == c and h["estado"] != "Cerrado")
                for c in ("Crítico", "Alto", "Medio")}
    avance = round(sum(p["avance"] for p in planes_emp) / len(planes_emp)) if planes_emp else 0
    historial = []
    for i, ev in enumerate(evaluaciones):
        anterior = evaluaciones[i + 1] if i + 1 < len(evaluaciones) else None
        historial.append({"ev": ev, "delta": (ev["puntaje"] - anterior["puntaje"]) if anterior else None})
    return render_template(
        "empresa.html", empresa=empresa, ultima=evaluaciones[0] if evaluaciones else None,
        evaluaciones=evaluaciones, historial=historial, hallazgos=hallazgos_emp, planes=planes_emp,
        abiertos=abiertos, avance=avance,
        grafico_fechas=[e["fecha"] for e in reversed(evaluaciones)],
        grafico_valores=[e["puntaje"] for e in reversed(evaluaciones)]
    )


@app.route("/empresas/<int:empresa_id>/eliminar", methods=["POST"])
@roles_required(*EDITORES)
def eliminar_empresa(empresa_id):
    conn = get_db()
    conn.execute("DELETE FROM planes_accion WHERE hallazgo_id IN (SELECT id FROM hallazgos WHERE empresa_id=?)", (empresa_id,))
    conn.execute("DELETE FROM hallazgos WHERE empresa_id=?", (empresa_id,))
    conn.execute("DELETE FROM respuestas WHERE evaluacion_id IN (SELECT id FROM evaluaciones WHERE empresa_id=?)", (empresa_id,))
    conn.execute("DELETE FROM evaluaciones WHERE empresa_id=?", (empresa_id,))
    conn.execute("DELETE FROM empresas WHERE id=?", (empresa_id,))
    conn.commit()
    conn.close()
    flash("Empresa eliminada junto con sus evaluaciones, hallazgos y plan de acción.", "success")
    return redirect(url_for("empresas"))


def datos_informe(empresa_id):
    conn = get_db()
    empresa = conn.execute("SELECT * FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    if not empresa:
        conn.close()
        return None
    hallazgos_data = conn.execute("""
        SELECT h.*, c.dominio FROM hallazgos h
        LEFT JOIN controles c ON c.id=h.control_id
        WHERE h.empresa_id=?
        ORDER BY CASE h.criticidad WHEN 'Crítico' THEN 1 WHEN 'Alto' THEN 2 WHEN 'Medio' THEN 3 ELSE 4 END, h.id
    """, (empresa_id,)).fetchall()
    planes_data = conn.execute("""
        SELECT p.*, h.id AS hallazgo_ref, h.codigo FROM planes_accion p
        JOIN hallazgos h ON h.id=p.hallazgo_id
        WHERE h.empresa_id=? ORDER BY h.id, p.id
    """, (empresa_id,)).fetchall()
    ultima = conn.execute(
        "SELECT * FROM evaluaciones WHERE empresa_id=? ORDER BY fecha DESC, id DESC LIMIT 1", (empresa_id,)
    ).fetchone()
    conn.close()
    planes_por_h = {}
    for pl in planes_data:
        planes_por_h.setdefault(pl["hallazgo_ref"], []).append(pl)
    return empresa, hallazgos_data, planes_por_h, planes_data, ultima


@app.route("/empresas/<int:empresa_id>/informe")
@roles_required(*EDITORES)
def informe_empresa(empresa_id):
    datos = datos_informe(empresa_id)
    if not datos:
        flash("La empresa no existe.", "danger")
        return redirect(url_for("empresas"))
    empresa, hallazgos_data, planes_por_h, planes_data, ultima = datos
    return render_template(
        "informe.html", empresa=empresa, hallazgos=hallazgos_data, planes_por_h=planes_por_h,
        planes=planes_data, ultima=ultima, hoy=date.today().isoformat()
    )


@app.route("/empresas/<int:empresa_id>/informe.csv")
@roles_required(*EDITORES)
def informe_csv(empresa_id):
    datos = datos_informe(empresa_id)
    if not datos:
        flash("La empresa no existe.", "danger")
        return redirect(url_for("empresas"))
    empresa, hallazgos_data, planes_por_h, _, _ = datos
    salida = io.StringIO()
    escritor = csv.writer(salida, delimiter=";")
    escritor.writerow([
        "Empresa", "Código", "Dominio", "Hallazgo", "Descripción", "Probabilidad", "Impacto", "Riesgo",
        "Criticidad", "Estado", "Recomendación", "Cumplimiento", "Observación de verificación",
        "Acción", "Responsable", "Fecha límite", "Avance %"
    ])
    for h in hallazgos_data:
        base = [empresa["razon_social"], h["codigo"], h["dominio"] or "", h["titulo"], h["descripcion"] or "",
                h["probabilidad"], h["impacto"], h["riesgo"], h["criticidad"], h["estado"],
                h["recomendacion"] or "", h["cumplimiento"] or "Sin verificar", h["observacion_verificacion"] or ""]
        acciones = planes_por_h.get(h["id"], [])
        if not acciones:
            escritor.writerow(base + ["Sin acción registrada", "", "", ""])
        for pl in acciones:
            escritor.writerow(base + [pl["actividad"], pl["responsable"] or "", pl["fecha_limite"] or "", pl["avance"]])
    contenido = "\ufeff" + salida.getvalue()
    return Response(
        contenido, mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=informe_empresa_{empresa_id}.csv"}
    )

@app.route("/empresas/nueva", methods=["POST"])
@roles_required(*EDITORES)
def nueva_empresa():
    if not request.form.get("razon_social", "").strip():
        flash("La razón social de la empresa es obligatoria.", "danger")
        return redirect(url_for("empresas"))
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
@roles_required(*EDITORES)
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
@roles_required(*EDITORES)
def nueva_evaluacion_form():
    conn = get_db()
    empresas_data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
    controles = conn.execute("SELECT * FROM controles WHERE activo=1 ORDER BY id").fetchall()
    conn.close()

    agrupados = {}
    for c in controles:
        agrupados.setdefault(c["dominio"], []).append(c)
    return render_template(
        "evaluacion_form.html", empresas=empresas_data, grupos=agrupados,
        evaluacion=None, respuestas={}, action=url_for("guardar_evaluacion")
    )


@app.route("/historial")
@roles_required(*EDITORES)
def historial():
    empresa_id = request.args.get("empresa", type=int)
    conn = get_db()
    empresas_data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
    empresa = conn.execute("SELECT * FROM empresas WHERE id=?", (empresa_id,)).fetchone() if empresa_id else None
    if not empresa and empresas_data:
        empresa = empresas_data[0]
    evaluaciones_emp = []
    if empresa:
        evaluaciones_emp = conn.execute(
            "SELECT * FROM evaluaciones WHERE empresa_id=? ORDER BY fecha DESC, id DESC", (empresa["id"],)
        ).fetchall()

    dominios_por_eval = {}
    for ev in evaluaciones_emp[:2]:
        filas = conn.execute("""
            SELECT c.dominio, ROUND(100.0 * SUM(r.resultado) / (COUNT(*) * 2), 0) AS pct
            FROM respuestas r JOIN controles c ON c.id=r.control_id
            WHERE r.evaluacion_id=? GROUP BY c.dominio
        """, (ev["id"],)).fetchall()
        dominios_por_eval[ev["id"]] = {f["dominio"]: int(f["pct"]) for f in filas}
    conn.close()

    historial_items = []
    for i, ev in enumerate(evaluaciones_emp):
        anterior = evaluaciones_emp[i + 1] if i + 1 < len(evaluaciones_emp) else None
        historial_items.append({"ev": ev, "delta": (ev["puntaje"] - anterior["puntaje"]) if anterior else None})

    comparacion = None
    if len(evaluaciones_emp) >= 2:
        actual, anterior = evaluaciones_emp[0], evaluaciones_emp[1]
        delta = actual["puntaje"] - anterior["puntaje"]
        dom_act = dominios_por_eval[actual["id"]]
        dom_ant = dominios_por_eval[anterior["id"]]
        dominios = [
            (d, dom_ant.get(d, 0), dom_act.get(d, 0), dom_act.get(d, 0) - dom_ant.get(d, 0))
            for d in dict.fromkeys(dom for dom, _ in CONTROLES_BASE)
        ]
        comparacion = {
            "actual": actual, "anterior": anterior, "delta": delta,
            "veredicto": "Mejoró" if delta > 0 else ("Empeoró" if delta < 0 else "Sin cambio"),
            "dominios": dominios,
            "desde_inicio": evaluaciones_emp[0]["puntaje"] - evaluaciones_emp[-1]["puntaje"],
            "primera": evaluaciones_emp[-1],
        }

    return render_template(
        "historial.html", empresas=empresas_data, empresa=empresa, historial=historial_items,
        comparacion=comparacion,
        grafico_fechas=[e["fecha"] for e in reversed(evaluaciones_emp)],
        grafico_valores=[e["puntaje"] for e in reversed(evaluaciones_emp)],
        empresa_id=empresa["id"] if empresa else None
    )

def validar_evaluacion(form, controles, exige_empresa):
    """Devuelve el mensaje de error con el dominio y control que faltan, o None si está completa."""
    errores = []
    if exige_empresa and not form.get("empresa_id"):
        errores.append("Selecciona la empresa a evaluar.")
    if not form.get("fecha"):
        errores.append("Ingresa la fecha de la evaluación.")
    faltan = {}
    contador = {}
    for c in controles:
        contador[c["dominio"]] = contador.get(c["dominio"], 0) + 1
        if f"control_{c['id']}" not in form:
            faltan.setdefault(c["dominio"], []).append(str(contador[c["dominio"]]))
    if faltan:
        detalle = "; ".join(f"{dom} (control {', '.join(nums)})" for dom, nums in faltan.items())
        errores.append("Faltan respuestas por marcar en: " + detalle + ".")
    return " ".join(errores) if errores else None


def sincronizar_hallazgos(cur, empresa_id, evaluacion_id, respuestas, controles_por_id, hoy):
    """La evaluación más reciente define qué hallazgos siguen abiertos en la empresa."""
    abiertos = {
        r["control_id"]: r["id"] for r in cur.execute(
            "SELECT id, control_id FROM hallazgos WHERE empresa_id=? AND control_id IS NOT NULL AND estado!='Cerrado'",
            (empresa_id,)).fetchall()
    }
    for control_id, resultado, observacion in respuestas:
        abierto = abiertos.get(control_id)
        if resultado == 0 and abierto is None:
            control = controles_por_id[control_id]
            next_num = cur.execute("SELECT COUNT(*) + 1 n FROM hallazgos").fetchone()["n"]
            prob, impacto = 3, 3
            riesgo = prob * impacto
            cur.execute("""
                INSERT INTO hallazgos
                (empresa_id, codigo, titulo, descripcion, probabilidad, impacto, riesgo,
                 criticidad, recomendacion, estado, control_id, evaluacion_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?, ?)
            """, (
                empresa_id, f"CYB-{next_num:03d}",
                f"Control no implementado: {control['pregunta'][:85]}",
                f"Durante la evaluación del {hoy} se registró 'No cumple' para el control del dominio {control['dominio']}. "
                + (f"Observación: {observacion}" if observacion else ""),
                prob, impacto, riesgo, criticidad_desde_riesgo(riesgo),
                RECOMENDACIONES_CONTROLES.get(
                    control["pregunta"],
                    "Definir una acción correctiva, responsable y fecha de implementación."
                ),
                control_id, evaluacion_id
            ))
        elif resultado > 0 and abierto is not None:
            cur.execute("""
                UPDATE hallazgos SET estado='Cerrado', cumplimiento='Cumplió a cabalidad',
                observacion_verificacion=? WHERE id=?
            """, (f"Corregido en la evaluación del {hoy}.", abierto))


@app.route("/evaluaciones/<int:evaluacion_id>/editar")
@roles_required(*EDITORES)
def editar_evaluacion(evaluacion_id):
    conn = get_db()
    ev = conn.execute("SELECT * FROM evaluaciones WHERE id=?", (evaluacion_id,)).fetchone()
    if not ev:
        conn.close()
        flash("La evaluación no existe.", "danger")
        return redirect(url_for("evaluaciones"))
    empresas_data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
    controles = conn.execute("SELECT * FROM controles WHERE activo=1 ORDER BY id").fetchall()
    filas = conn.execute(
        "SELECT control_id, resultado, observacion FROM respuestas WHERE evaluacion_id=?", (evaluacion_id,)
    ).fetchall()
    conn.close()

    agrupados = {}
    for c in controles:
        agrupados.setdefault(c["dominio"], []).append(c)
    respuestas = {f["control_id"]: {"resultado": f["resultado"], "observacion": f["observacion"] or ""} for f in filas}
    return render_template(
        "evaluacion_form.html", empresas=empresas_data, grupos=agrupados, evaluacion=ev,
        respuestas=respuestas, action=url_for("actualizar_evaluacion", evaluacion_id=evaluacion_id)
    )


@app.route("/evaluaciones/<int:evaluacion_id>/actualizar", methods=["POST"])
@roles_required(*EDITORES)
def actualizar_evaluacion(evaluacion_id):
    conn = get_db()
    ev = conn.execute("SELECT * FROM evaluaciones WHERE id=?", (evaluacion_id,)).fetchone()
    if not ev:
        conn.close()
        flash("La evaluación no existe.", "danger")
        return redirect(url_for("evaluaciones"))

    controles = conn.execute("SELECT * FROM controles WHERE activo=1 ORDER BY id").fetchall()
    error = validar_evaluacion(request.form, controles, exige_empresa=False)
    if error:
        conn.close()
        flash(error, "danger")
        return redirect(url_for("editar_evaluacion", evaluacion_id=evaluacion_id))
    fecha_eval = request.form["fecha"]
    total = 0
    respuestas = []
    for c in controles:
        resultado = int(request.form[f"control_{c['id']}"])
        total += resultado
        respuestas.append((c["id"], resultado, request.form.get(f"obs_{c['id']}", "").strip()))

    puntaje = round((total / (len(respuestas) * 2)) * 100)
    nivel = nivel_desde_puntaje(puntaje)
    hoy = date.today().isoformat()
    cur = conn.cursor()
    cur.execute("DELETE FROM respuestas WHERE evaluacion_id=?", (evaluacion_id,))
    cur.execute("""
        UPDATE evaluaciones SET fecha=?, puntaje=?, nivel=?, observacion=? WHERE id=?
    """, (fecha_eval, puntaje, nivel, f"Editada el {hoy} por {session['user']['name']}", evaluacion_id))
    for control_id, resultado, observacion in respuestas:
        cur.execute("""
            INSERT INTO respuestas (evaluacion_id, control_id, resultado, observacion)
            VALUES (?, ?, ?, ?)
        """, (evaluacion_id, control_id, resultado, observacion))

    controles_por_id = {c["id"]: c for c in controles}
    sincronizar_hallazgos(cur, ev["empresa_id"], evaluacion_id, respuestas, controles_por_id, hoy)

    conn.commit()
    conn.close()
    flash(f"Evaluación actualizada. Índice TotalSecurity: {puntaje}/100 · Nivel {nivel}.", "success")
    return redirect(url_for("resultado_evaluacion", evaluacion_id=evaluacion_id))


@app.route("/evaluaciones/guardar", methods=["POST"])
@roles_required(*EDITORES)
def guardar_evaluacion():
    conn = get_db()
    controles = conn.execute("SELECT * FROM controles WHERE activo=1 ORDER BY id").fetchall()
    error = validar_evaluacion(request.form, controles, exige_empresa=True)
    if error:
        conn.close()
        flash(error, "danger")
        return redirect(url_for("nueva_evaluacion_form"))
    empresa_id = int(request.form["empresa_id"])
    fecha_eval = request.form["fecha"]

    total = 0
    respuestas = []
    for c in controles:
        resultado = int(request.form[f"control_{c['id']}"])
        total += resultado
        respuestas.append((c["id"], resultado, request.form.get(f"obs_{c['id']}", "").strip()))

    no_respondidos = len(controles) - len(respuestas)
    maximo = len(respuestas) * 2
    puntaje = round((total / maximo) * 100)
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


    controles_por_id = {c["id"]: c for c in controles}
    sincronizar_hallazgos(cur, empresa_id, evaluacion_id, respuestas, controles_por_id, date.today().isoformat())
    conn.commit()
    conn.close()

    aviso = f" {no_respondidos} control(es) sin responder no fueron considerados." if no_respondidos else ""
    flash(f"Evaluación completada. Índice TotalSecurity: {puntaje}/100 · Nivel {nivel}.{aviso}", "success")
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
    empresa_id = request.args.get("empresa", type=int)
    conn = get_db()
    data = conn.execute("""
        SELECT h.*, em.razon_social
        FROM hallazgos h JOIN empresas em ON em.id=h.empresa_id
        WHERE (? IS NULL OR h.empresa_id=?)
        ORDER BY CASE h.criticidad WHEN 'Crítico' THEN 1 WHEN 'Alto' THEN 2 WHEN 'Medio' THEN 3 ELSE 4 END, h.id DESC
    """, (empresa_id, empresa_id)).fetchall()
    empresas_data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
    conn.close()
    return render_template("hallazgos.html", hallazgos=data, empresas=empresas_data, empresa_id=empresa_id,
                           cumplimientos=CUMPLIMIENTOS)


@app.route("/hallazgos/nuevo", methods=["POST"])
@roles_required(*EDITORES)
def nuevo_hallazgo():
    if not request.form.get("titulo", "").strip():
        flash("El título del hallazgo es obligatorio.", "danger")
        return redirect(url_for("hallazgos"))
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


CUMPLIMIENTOS = ("Cumplió a cabalidad", "Cumplimiento parcial", "No cumplió")


@app.route("/hallazgos/<int:hallazgo_id>/verificar", methods=["POST"])
@roles_required(*EDITORES)
def verificar_hallazgo(hallazgo_id):
    observacion = request.form.get("observacion", "").strip()
    cumplimiento = request.form.get("cumplimiento", "")
    if cumplimiento not in CUMPLIMIENTOS:
        cumplimiento = None
    cerrar = request.form.get("accion") == "cerrar"
    conn = get_db()
    conn.execute(
        "UPDATE hallazgos SET observacion_verificacion=?, cumplimiento=? WHERE id=?",
        (observacion, cumplimiento, hallazgo_id)
    )
    if cerrar:
        conn.execute("UPDATE hallazgos SET estado='Cerrado' WHERE id=?", (hallazgo_id,))
    conn.commit()
    conn.close()
    flash("Verificación guardada." + (" Hallazgo cerrado." if cerrar else ""), "success")
    empresa_id = request.form.get("empresa", type=int)
    return redirect(url_for("hallazgos", empresa=empresa_id) if empresa_id else url_for("hallazgos"))


@app.route("/hallazgos/<int:hallazgo_id>/cerrar", methods=["POST"])
@roles_required(*EDITORES)
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
    empresa_id = request.args.get("empresa", type=int)
    conn = get_db()
    data = conn.execute("""
        SELECT p.*, h.codigo, h.titulo, h.criticidad, h.estado AS hallazgo_estado, em.razon_social
        FROM planes_accion p
        JOIN hallazgos h ON h.id=p.hallazgo_id
        JOIN empresas em ON em.id=h.empresa_id
        WHERE (? IS NULL OR h.empresa_id=?)
        ORDER BY p.fecha_limite
    """, (empresa_id, empresa_id)).fetchall()
    hallazgos_data = conn.execute("""
        SELECT h.id, h.codigo, h.titulo, em.razon_social
        FROM hallazgos h JOIN empresas em ON em.id=h.empresa_id
        WHERE h.estado!='Cerrado'
        ORDER BY h.id DESC
    """).fetchall()
    empresas_data = conn.execute("SELECT * FROM empresas ORDER BY razon_social").fetchall()
    conn.close()
    return render_template("planes.html", planes=data, hallazgos=hallazgos_data, empresas=empresas_data, empresa_id=empresa_id)


@app.route("/planes/nuevo", methods=["POST"])
@roles_required(*EDITORES)
def nuevo_plan():
    if not request.form.get("actividad", "").strip():
        flash("La actividad del plan es obligatoria.", "danger")
        return redirect(url_for("planes"))
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
@roles_required(*EDITORES)
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


@app.route("/usuarios")
@roles_required("admin")
def usuarios():
    conn = get_db()
    data = conn.execute("SELECT id, nombre, correo, rol, activo FROM usuarios ORDER BY nombre").fetchall()
    conn.close()
    return render_template("usuarios.html", usuarios=data, roles=ROLES)


@app.route("/usuarios/nuevo", methods=["POST"])
@roles_required("admin")
def nuevo_usuario():
    nombre = request.form.get("nombre", "").strip()
    correo = request.form.get("correo", "").strip().lower()
    password = request.form.get("password", "")
    rol = request.form.get("rol", "")
    if not (nombre and correo and len(password) >= 8 and rol in ROLES):
        flash("Revisa los datos: contraseña de mínimo 8 caracteres y perfil válido.", "danger")
        return redirect(url_for("usuarios"))

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO usuarios (nombre, correo, password_hash, rol) VALUES (?, ?, ?, ?)",
            (nombre, correo, generate_password_hash(password), rol)
        )
        conn.commit()
        flash("Usuario creado correctamente.", "success")
    except sqlite3.IntegrityError:
        flash("Ya existe un usuario con ese correo.", "danger")
    finally:
        conn.close()
    return redirect(url_for("usuarios"))


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.environ.get("FLASK_DEBUG") == "1")
