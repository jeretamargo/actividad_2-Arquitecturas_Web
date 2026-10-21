"""Genera el informe y su diagrama vectorial. Requiere reportlab."""
from pathlib import Path

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "informe-hito-2.pdf"
INK = colors.HexColor("#17354A")
TEAL = colors.HexColor("#087F8C")
PALE = colors.HexColor("#EFF6F8")
GRAY = colors.HexColor("#536674")
RULE = colors.HexColor("#CADBE2")


def fonts():
    for folder in (Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")):
        if (folder / "DejaVuSans.ttf").exists():
            pdfmetrics.registerFont(TTFont("Body", str(folder / "DejaVuSans.ttf")))
            pdfmetrics.registerFont(TTFont("BodyBold", str(folder / "DejaVuSans-Bold.ttf")))
            pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold")
            return "Body", "BodyBold"
    return "Helvetica", "Helvetica-Bold"


FONT, BOLD = fonts()
styles = getSampleStyleSheet()
styles.add(ParagraphStyle("TitleTP", fontName=BOLD, fontSize=23, leading=29, textColor=INK, spaceAfter=13))
styles.add(ParagraphStyle("LeadTP", fontName=FONT, fontSize=10.5, leading=16, textColor=GRAY, spaceAfter=12))
styles.add(ParagraphStyle("H2TP", fontName=BOLD, fontSize=12, leading=17, textColor=TEAL, spaceBefore=12, spaceAfter=7))
styles.add(ParagraphStyle("BodyTP", fontName=FONT, fontSize=9.1, leading=13.4, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle("SmallTP", fontName=FONT, fontSize=8, leading=11.5, textColor=GRAY, spaceAfter=6))
styles.add(ParagraphStyle("CellTP", fontName=FONT, fontSize=8.2, leading=12, textColor=INK))
styles.add(ParagraphStyle("HeadTP", fontName=BOLD, fontSize=8.2, leading=12, textColor=colors.white))
styles.add(ParagraphStyle("CaptionTP", fontName=FONT, fontSize=8, leading=11.5, textColor=GRAY, alignment=TA_CENTER, spaceAfter=7))


def p(text, style="BodyTP"):
    return Paragraph(text, styles[style])


def table(rows, widths):
    data = [[p(cell, "HeadTP" if i == 0 else "CellTP") for cell in row]
            for i, row in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PALE, colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, RULE),
    ]))
    return t


def diagram():
    d = Drawing(500, 415)

    def box(x, y, w, h, title, lines, dark=False):
        d.add(Rect(x, y, w, h, rx=9, ry=9,
                   fillColor=INK if dark else PALE, strokeColor=RULE, strokeWidth=0.7))
        color = colors.white if dark else INK
        d.add(String(x + w / 2, y + h - 18, title, textAnchor="middle",
                     fontName=BOLD, fontSize=10.2, fillColor=color))
        for i, line in enumerate(lines):
            d.add(String(x + w / 2, y + h - 35 - i * 12, line,
                         textAnchor="middle", fontName=FONT, fontSize=8, fillColor=color))

    def edge(points):
        for a, b in zip(points, points[1:]):
            d.add(Line(*a, *b, strokeColor=TEAL, strokeWidth=1.5))
        (x0, y0), (x1, y1) = points[-2:]
        if x0 == x1:
            delta = 1 if y1 > y0 else -1
            tip = [x1, y1, x1 - 3.5, y1 - 7 * delta, x1 + 3.5, y1 - 7 * delta]
        else:
            delta = 1 if x1 > x0 else -1
            tip = [x1, y1, x1 - 7 * delta, y1 - 3.5, x1 - 7 * delta, y1 + 3.5]
        d.add(Polygon(tip, fillColor=TEAL, strokeColor=TEAL))

    def label(x, y, text):
        d.add(String(x, y, text, fontName=FONT, fontSize=7.5, fillColor=GRAY))

    box(65, 345, 370, 55, "Navegador / componentes React", [
        "Access: memoria de JavaScript | Refresh: cookie HttpOnly",
    ])
    box(140, 265, 220, 45, "Nginx :8081", ["Entrada HTTP; conserva Host y puerto"], dark=True)
    box(0, 145, 205, 80, "Astro SSR / Node :4321", [
        "Produce HTML y recursos.",
        "React se ejecuta en el navegador.",
        "Servidor sin tokens del participante.",
    ])
    box(265, 135, 235, 100, "Gunicorn :8000 / Django", [
        "DRF + PyJWT: valida la identidad.",
        "Firma, tipo y expiración del JWT.",
        "sub -> User -> Participant.",
        "Comprueba jti revocado en refresh.",
    ])
    box(200, 15, 300, 65, "PostgreSQL :5432", [
        "Usuarios + hashes, participantes, actividades,",
        "inscripciones y RevokedToken | volumen persistente",
    ], dark=True)
    edge([(250, 345), (250, 310)])
    label(263, 328, "Páginas + API; Bearer / cookies / CSRF")
    edge([(195, 265), (195, 245), (102, 245), (102, 225)])
    label(10, 252, "/ y recursos")
    edge([(305, 265), (305, 250), (382, 250), (382, 235)])
    label(365, 259, "/api/")
    edge([(102, 145), (102, 105), (335, 105), (335, 135)])
    label(123, 111, "GET de actividades públicas (red interna)")
    edge([(440, 135), (440, 80)])
    label(449, 97, "ORM")
    return d


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self.pages)
        for state in self.pages:
            self.__dict__.update(state)
            self.setFillColor(GRAY)
            self.setFont(FONT, 8)
            self.drawRightString(A4[0] - 48, 29, f"{self._pageNumber} / {total}")
            super().showPage()
        super().save()


def decorate_page(c, doc):
    c.saveState()
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.line(48, 797, A4[0] - 48, 797)
    c.setFillColor(GRAY)
    c.setFont(FONT, 8)
    c.drawString(48, 809, "UNTDF / ARQUITECTURAS WEB / HITO 2")
    c.drawString(48, 29, "Autenticación y ejecución reproducible · evaluación local")
    c.restoreState()


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    drawing = diagram()
    svg = renderSVG.drawToString(drawing)
    svg = svg.replace("font-family: BodyBold;", "font-family: 'DejaVu Sans', sans-serif; font-weight: bold;")
    svg = svg.replace("font-family: Body;", "font-family: 'DejaVu Sans', sans-serif;")
    svg = svg.replace("<title>...</title>", "<title>Componentes del sistema de inscripciones - Hito 2</title>")
    svg = svg.replace("<desc>...</desc>", "<desc>Nginx recibe las solicitudes, Astro produce la interfaz, Django valida la identidad y PostgreSQL persiste los datos.</desc>")
    (ROOT / "docs" / "diagrama-componentes.svg").write_text(svg, encoding="utf-8")
    story = []

    def add(text, style="BodyTP"):
        story.append(p(text, style))

    def h(text):
        add(text, "H2TP")

    # 1: componentes, comunicaciones y persistencia.
    add("Sistema de inscripciones", "TitleTP")
    add("Arquitectura, autenticación JWT y reproducción de la entrega", "LeadTP")
    add("El Hito 2 incorpora identidad autenticada al sistema del Hito 1. Se mantienen Django, PostgreSQL y Docker Compose. El frontend activo usa Astro para renderizar páginas y componentes React para login, sesión e inscripciones. El entorno de entrega agrega Nginx y Gunicorn.")
    story.append(drawing)
    add("Diagrama del entorno de entrega. Las flechas indican solicitudes; las respuestas vuelven por el mismo recorrido.", "CaptionTP")
    h("Entrada, datos e identidad")
    add("<b>Nginx</b> publica sólo el puerto local 8081: envía <b>/api/</b> a Django y las demás rutas a Astro. Astro consulta actividades públicas al backend por la red interna de Compose. Los tokens del participante se manejan en el navegador, no durante ese renderizado del servidor.")
    add("<b>Django</b> valida identidad y reglas del dominio. <b>PostgreSQL</b> conserva usuarios y hashes de contraseña, participantes, actividades, inscripciones y revocaciones. El volumen <b>postgres_data</b> conserva esos datos al recrear contenedores.")

    # 2: flujo de autenticación y autorización.
    story.append(PageBreak())
    add("Autenticación y autorización", "TitleTP")
    add("PyJWT genera y valida los JWT con HS256. No se utiliza SimpleJWT. Los JWT están firmados: sus claims son legibles y no se usan para guardar contraseñas.")
    story.append(table([
        ["Token", "Contenido y duración", "Ubicación y uso"],
        ["Access", "sub, username, type=access, iat, exp.<br/><b>10 minutos.</b>", "Sólo memoria del frontend.<br/>Authorization: Bearer &lt;token&gt;"],
        ["Refresh", "sub, type=refresh, jti único, iat, exp.<br/><b>7 días.</b>", "Cookie refresh_token: HttpOnly, SameSite=Lax, Path=/api/v2/auth/."],
    ], [66, 212, 221]))
    h("1. Login")
    add("El cliente envía username y password a <b>POST /api/v2/auth/login/</b>. Django llama a <b>authenticate()</b>, comprueba que el usuario tenga participante y emite ambos tokens. El access vuelve en JSON; el refresh se instala como cookie HttpOnly. Una contraseña incorrecta devuelve <b>401</b>; un usuario válido sin participante recibe <b>403</b>.")
    h("2. Operaciones del participante")
    add("En las rutas <b>/api/v2/me/</b>, AccessTokenAuthentication comprueba firma, algoritmo permitido, claims obligatorios, expiración y type=access. Busca un usuario activo usando sub; luego obtiene <b>request.user.participant</b>. La identidad no se toma de un UUID elegido por el cliente. Un access faltante, vencido o inválido devuelve <b>401</b>; la ausencia de participante, <b>403</b>.")
    h("3. Renovación")
    add("<b>POST /api/v2/auth/refresh/</b> recibe la cookie y valida firma, expiración, type=refresh y jti. Rechaza identificadores presentes en <b>RevokedToken</b> y comprueba usuario activo y participante. Si corresponde, entrega un nuevo access. El refresh mantiene su vencimiento original; no se rota. Un refresh ausente, inválido, vencido o revocado devuelve <b>401</b>.")
    h("4. Logout")
    add("<b>POST /api/v2/auth/logout/</b> registra el jti del refresh válido, elimina su cookie y devuelve <b>204</b>. Si ya no hay un refresh válido, también responde 204. El frontend descarta el access y limpia la información privada. La revocación queda persistida en PostgreSQL.")
    h("CSRF y cookies")
    add("Antes de los tres POST de autenticación, el cliente consulta <b>GET /api/v2/auth/csrf/</b>, conserva las cookies y envía el valor csrf_token en <b>X-CSRFToken</b>. Una verificación CSRF fallida devuelve 403. El navegador accede al mismo origen mediante Nginx; conservar Host y el puerto externo evita rechazos de origen. La evaluación usa HTTP local, por eso Secure está desactivado.")

    # 3: decisiones, contrato y límites explícitos.
    story.append(PageBreak())
    add("Decisiones y límites", "TitleTP")
    h("Conservación del Hito 1")
    story.append(table([
        ["Operación v2", "Comportamiento"],
        ["GET activities/ y activities/{id}/", "Consulta pública de actividades y cupos. Detalle inexistente: 404."],
        ["GET me/enrollments/", "Sólo las inscripciones del participante autenticado."],
        ["PUT me/enrollments/create/{id}/", "201 al crear; 200 si ya existe; 409 sin cupo; 404 si no existe la actividad. No se envía participante."],
        ["DELETE me/enrollments/delete/{id}/", "204 al cancelar o si ya estaba cancelada; 404 si no existe la actividad."],
    ], [210, 289]))
    h("Access breve y refresh HttpOnly")
    add("El access se conserva en una variable del módulo de autenticación; no se escribe en localStorage, sessionStorage ni cookies. Al recargar o cambiar de página Astro se pierde esa memoria y se recupera un access por refresh. Ante un 401 protegido, el cliente intenta renovar y reintenta una vez. Comparte las renovaciones simultáneas y evita restaurar una sesión desde respuestas anteriores al logout.")
    add("HttpOnly evita que JavaScript lea el refresh, pero no impide que un script malicioso haga peticiones dentro de una sesión. CSRF y la prevención de XSS siguen siendo necesarios. La cookie se restringe a las rutas de autenticación.")
    h("Qué pasa con un access emitido después del logout")
    add("<b>El logout revoca el refresh presentado, no el access.</b> Si alguien conserva una copia del access, puede utilizarla hasta su expiración original, mientras el usuario siga activo y tenga participante. Por ejemplo: un access emitido a las 10:00 vence a las 10:10; un logout a las 10:03 no elimina los 7 minutos restantes. La corta duración limita esa ventana.")
    h("Límites de la implementación")
    add("<b>Sesiones:</b> no hay rotación del refresh, detección de reutilización ni cierre global de sesiones. El logout afecta a su jti. No hay limpieza automática de revocaciones vencidas ni limitación de intentos de login.")
    add("<b>API heredada:</b> /api/v1/ permanece accesible con el comportamiento anterior y sin JWT. La interfaz actual usa v2. Esta permanencia impide afirmar que todas las rutas están protegidas; se conserva como una limitación explícita del alcance.")
    add("<b>Concurrencia:</b> cupo e idempotencia se comprueban para operaciones secuenciales. La unicidad actividad-participante evita filas duplicadas, pero el conteo y la creación no están bloqueados en una transacción: solicitudes simultáneas pueden superar el cupo o generar un error en una carrera por la misma inscripción.")
    add("<b>Evaluación local:</b> HTTP sin TLS, clave Django/JWT fija en código y cuentas públicas de prueba. No se presenta como una configuración segura para Internet. Las etiquetas de imágenes y algunos rangos Python tampoco garantizan builds idénticos bit a bit en fechas distintas.")

    # 4: reproducción, cuentas y evidencia verificable.
    story.append(PageBreak())
    add("Ejecución y comprobación", "TitleTP")
    add('Repositorio: <link href="https://github.com/jeretamargo/actividad_2-Arquitecturas_Web" color="#087F8C">github.com/jeretamargo/actividad_2-Arquitecturas_Web</link>. El <b>README de la raíz</b> contiene los comandos completos, requisitos, puertos y resolución del entorno local. No depende de archivos .env privados ni de una base preexistente.')
    h("Desde una copia limpia")
    story.append(table([
        ["Paso", "Acción"],
        ["1. Configuración", "Clonar el repositorio. Copiar .env.example como .env: DB_NAME, DB_USER y DB_PASSWORD públicos de evaluación."],
        ["2. Construcción", "Usar compose.yaml + compose.prod.yaml y el nombre de proyecto hito2. Construir backend y frontend e iniciar PostgreSQL."],
        ["3. Esquema y datos", "En backend: manage.py migrate, seed_activities y seed_users, en ese orden. No ejecutar makemigrations para instalar."],
        ["4. Arranque", "Iniciar todos los servicios y abrir http://127.0.0.1:8081/. Nginx comunica con Astro y Gunicorn; sólo Nginx publica un puerto."],
    ], [108, 391]))
    h("Usuarios exclusivamente locales de evaluación")
    story.append(table([
        ["Usuario", "Contraseña", "Participante", "Inscripciones"],
        ["maria", "MariaTP2026!", "María López", "2"],
        ["jorge", "JorgeTP2026!", "Jorge Fernández", "1"],
    ], [68, 139, 180, 112]))
    story.append(Spacer(1, 8))
    add("<b>seed_activities</b> restaura 4 actividades, 5 participantes y 8 inscripciones; elimina datos de dominio ajenos al escenario. <b>seed_users</b> crea o restaura las dos cuentas sin duplicarlas ni modificar inscripciones: conserva el hash si la contraseña coincide y restaura contraseña/estado activo si cambiaron. Ante cuentas administrativas o vínculos incompatibles, revierte toda la operación.")
    add("Las migraciones versionadas incluyen la relación User-Participant (0004) y RevokedToken (0005). PostgreSQL almacena el esquema, los datos y las revocaciones en un volumen. Detener con down lo conserva; down -v lo elimina. Desarrollo usa Astro :4321 y Django :8000, sin Nginx ni Gunicorn; no sustituye la prueba del entorno de entrega.")
    h("Evidencia de verificación local")
    add("<b>Backend:</b> 6 pruebas aprobadas en una base de tests: listado público, método HTTP, bootstrap, login con CSRF, cookie HttpOnly, identidad autenticada, repetición de semillas, restauración de credenciales y rollback por conflicto. La comprobación de migraciones no detectó cambios pendientes.")
    add("<b>Integración HTTP real:</b> instalación con volumen PostgreSQL nuevo y 24 comprobaciones por Nginx: páginas SSR, login correcto/incorrecto, falta de access, CSRF, inscripciones propias, cupo 409, PUT y DELETE repetidos, refresh, borrado de cookie, revocación y vigencia del access después del logout. Las pruebas se realizaron en un entorno separado de la base de desarrollo.")
    add("<b>Frontend:</b> build de producción correcto y pruebas del módulo de autenticación con respuestas simuladas. Estas últimas verifican lógica del cliente; no se presentan como prueba de concurrencia ni sustituyen las comprobaciones HTTP reales.")

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=48, rightMargin=48,
                            topMargin=61, bottomMargin=49,
                            title="Hito 2 - Autenticación y ejecución reproducible",
                            author="Arquitecturas Web - UNTDF", subject="Informe del sistema de inscripciones")
    doc.build(story, canvasmaker=NumberedCanvas, onFirstPage=decorate_page, onLaterPages=decorate_page)
    print(OUT)


if __name__ == "__main__":
    build()
