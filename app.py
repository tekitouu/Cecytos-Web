from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from config import Config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Clave secreta indispensable para que funcionen las sesiones
app.secret_key = 'leopardos_asistech_key'

mysql = MySQL(app)

@app.route("/")
def index():
    cur = mysql.connection.cursor()
    # Hacemos un JOIN para traer el nombre del usuario que reportó la incidencia
    query = """
        SELECT p.id_problema, p.titulo, p.descripcion, p.estado, 
               DATE_FORMAT(p.fecha_reporte, '%d-%m %H:%M'), u.nombre 
        FROM problema p
        INNER JOIN usuario u ON p.id_usuario = u.id_usuario
        ORDER BY p.fecha_reporte DESC
    """
    cur.execute(query)
    problemas = cur.fetchall()
    cur.close()
    return render_template("index.html", problemas=problemas)

@app.route("/post/<int:id>")
def post(id):
    cur = mysql.connection.cursor()
    query = """
        SELECT p.id_problema, p.titulo, p.descripcion, p.estado, p.fecha_reporte, u.nombre, u.correo
        FROM problema p
        INNER JOIN usuario u ON p.id_usuario = u.id_usuario
        WHERE p.id_problema = %s
    """
    cur.execute(query, (id,))
    problema = cur.fetchone()
    cur.close()
    return render_template("post.html", problema=problema)

@app.route("/create", methods=["GET", "POST"])
def create():
    # Seguridad básica: Si no se ha logueado, directo al login
    if not session.get('user_id'):
        flash("Debes iniciar sesión para reportar una incidencia.", "danger")
        return redirect(url_for('login'))

    if request.method == "POST":
        titulo = request.form["titulo"]
        descripcion = request.form["contenido"] # Recibe del textarea del HTML
        id_usuario = session['user_id']
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cur = mysql.connection.cursor()
        # Insertamos usando las columnas reales de tu tabla 'problema'
        cur.execute(
            "INSERT INTO problema (id_usuario, titulo, descripcion, estado, fecha_reporte) VALUES (%s, %s, %s, 'Pendiente', %s)",
            (id_usuario, titulo, descripcion, fecha_actual)
        )
        mysql.connection.commit()
        cur.close()
        
        flash("¡Incidencia registrada en el sistema exitosamente!", "success")
        return redirect(url_for("index"))

    return render_template("create.html")

@app.route("/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")
        
        cur = mysql.connection.cursor()
        # Buscamos en tu tabla real de usuarios
        cur.execute("SELECT id_usuario, nombre, contraseña, rol FROM usuario WHERE correo = %s", (correo,))
        user = cur.fetchone()
        cur.close()
        
        # Validamos en texto plano como lo tienes en tu base de datos
        if user and user[2] == password:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_role'] = user[3]
            
            flash(f"¡Bienvenido de nuevo, {user[1]}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Credenciales incorrectas. Intenta nuevamente.", "danger")
            return redirect(url_for("login"))
            
    return render_template("auth/login.html")

@app.route("/auth/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)