from flask import Flask, render_template, request, jsonify, session
import psycopg2
import os
from functools import wraps  # ✅ NUEVO
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("dp5xiubsa"),
    api_key=os.getenv("491611916593886"),
    api_secret=os.getenv("Et9hNNN5lAPAAPJB1PwB2r2wGEo")
)

app = Flask(__name__)
app.secret_key = "mi_clave_secreta_123"

UPLOAD = "static/uploads"
if not os.path.exists(UPLOAD):
    os.makedirs(UPLOAD)

# -------------------------
# ✅ DECORADOR ADMIN
# -------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "rol" not in session or session["rol"] != "admin":
            return "No autorizado", 403
        return f(*args, **kwargs)
    return decorated_function

# -------------------------
# CONEXIÓN BASE DE DATOS
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://inventario_user:VG0AF852QrAB0xMr9lRWlyWnpybQBTNA@dpg-d6nhomh5pdvs73bin8og-a.oregon-postgres.render.com/inventario_4oa6"
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
conn.autocommit = False

# -------------------------
# CREAR TABLAS
# -------------------------
try:
    with conn.cursor() as cursor:

        # Productos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos(
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(50),
            nombre VARCHAR(100),
            descripcion TEXT,
            marca VARCHAR(100),
            cantidad INTEGER,
            precio NUMERIC,
            precio_minimo NUMERIC,
            foto TEXT
        )
        """)

        # Ventas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas(
            id SERIAL PRIMARY KEY,
            producto_id INTEGER REFERENCES productos(id),
            nombre_producto VARCHAR(100),
            cantidad INTEGER,
            precio_unitario NUMERIC,
            total NUMERIC,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Usuarios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100),
            usuario VARCHAR(50) UNIQUE,
            password VARCHAR(50),
            rol VARCHAR(20)
        )
        """)

        # Insertar usuarios solo si no existen
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO usuarios (nombre, usuario, password, rol) VALUES
            ('Administrador','admin','admin123','admin'),
            ('Vendedor 1','vendedor1','1234','vendedor'),
            ('Vendedor 2','vendedor2','1234','vendedor'),
            ('Vendedor 3','vendedor3','1234','vendedor'),
            ('Vendedor 4','vendedor4','1234','vendedor')
            """)

        conn.commit()

except Exception as e:
    conn.rollback()
    print("Error inicializando la base de datos:", e)

# -------------------------
# FIX COLUMNAS FALTANTES
# -------------------------
try:
    with conn.cursor() as cursor:
        cursor.execute("""
        ALTER TABLE ventas 
        ADD COLUMN IF NOT EXISTS usuario VARCHAR(100);
        """)
        conn.commit()
        print("✅ Columna usuario verificada correctamente")

except Exception as e:
    conn.rollback()
    print("❌ Error en fix usuario:", e)

# -------------------------
# PÁGINAS
# -------------------------
@app.route("/")
def inicio():
    return render_template("inicio.html")

@app.route("/agregar")
@admin_required
def agregar_pagina():
    return render_template("agregar.html")

@app.route("/inventario")
@admin_required
def inventario():
    # ✅ PASAR ROL AL FRONTEND
    return render_template("inventario.html", rol=session.get("rol"))

@app.route("/vender")
def vender_pagina():
    return render_template("vender.html")

@app.route("/historial")
def historial_pagina():
    return render_template("historial.html")

@app.route("/dashboard")
@admin_required
def dashboard_pagina():
    return render_template("dashboard.html")

# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.form
    usuario = data.get("usuario")
    password = data.get("password")

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT nombre, rol FROM usuarios WHERE usuario=%s AND password=%s",
                (usuario, password)
            )
            row = cursor.fetchone()
    except Exception as e:
        conn.rollback()
        print("Error en login:", e)
        return jsonify({"mensaje":"Error en la base de datos"}),500

    if row:
         session["usuario"] = row[0]
         session["rol"] = row[1]
         return jsonify({"mensaje":"ok", "rol": row[1]})
    else:
        return jsonify({"mensaje":"usuario o contraseña incorrecta"}),401

@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"mensaje":"ok"})

@app.route("/api/usuario_actual")
def usuario_actual():
    if "usuario" in session:
        return jsonify({"usuario": session["usuario"], "rol": session.get("rol")})
    return jsonify({"usuario": None, "rol": None}), 401

# -------------------------
# PRODUCTOS
# -------------------------
@app.route("/productos")
def productos():
    if "usuario" not in session:
        return jsonify([])

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id,codigo,nombre,descripcion,marca,
            cantidad,precio,precio_minimo,foto
            FROM productos
            ORDER BY id DESC
            """)
            rows = cursor.fetchall()
    except Exception as e:
        conn.rollback()
        print("Error obteniendo productos:", e)
        return jsonify([])

    productos = []
    for r in rows:
        productos.append({
            "id": r[0],
            "codigo": r[1],
            "nombre": r[2],
            "descripcion": r[3],
            "marca": r[4],
            "cantidad": r[5],
            "precio": float(r[6]) if r[6] else 0,
            "precio_minimo": float(r[7]) if r[7] else 0,
            "foto": r[8]
        })
    return jsonify(productos)

# -------------------------
# AGREGAR PRODUCTO
# -------------------------
@app.route("/agregar_producto", methods=["POST"])
@admin_required
def agregar_producto():
    try:
        codigo = request.form.get("codigo")
        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")
        marca = request.form.get("marca")
        cantidad = int(request.form.get("cantidad") or 0)
        precio = float(request.form.get("precio") or 0)
        precio_minimo = float(request.form.get("precio_minimo") or 0)

        foto = request.files.get("foto")
        ruta = ""
        if foto and foto.filename != "":
             resultado = cloudinary.uploader.upload(foto)
             ruta = resultado["secure_url"]

        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO productos
            (codigo,nombre,descripcion,marca,cantidad,precio,precio_minimo,foto)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,(codigo,nombre,descripcion,marca,cantidad,precio,precio_minimo,ruta))
            conn.commit()

        return jsonify({"mensaje":"ok"})

    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({"mensaje":"error"}),500

# -------------------------
# VENDER PRODUCTO
# -------------------------
@app.route("/vender_producto", methods=["POST"])
def vender_producto():
    try:
        if "usuario" not in session:
            return jsonify({"mensaje":"No autenticado"}),403

        data = request.get_json()
        if not data:
            return jsonify({"mensaje":"No se enviaron datos"}),400

        id = int(data.get("id", 0))
        cantidad = int(data.get("cantidad", 0))
        usuario_actual = session["usuario"]

        if id == 0 or cantidad <= 0:
            return jsonify({"mensaje":"Datos inválidos"}),400

        with conn.cursor() as cursor:
            cursor.execute("SELECT nombre,precio,cantidad FROM productos WHERE id=%s",(id,))
            row = cursor.fetchone()

            if not row:
                return jsonify({"mensaje":"Producto no encontrado"}),404

            nombre_producto, precio_real, stock_actual = row

            if cantidad > stock_actual:
                return jsonify({"mensaje":"Stock insuficiente"}),400

            try:
                precio_especial = float(data.get("precio"))
                if precio_especial <= 0:
                    precio_especial = None
            except:
                precio_especial = None

            precio_unitario = precio_especial if precio_especial else float(precio_real)
            total_venta = precio_unitario * cantidad

            cursor.execute("UPDATE productos SET cantidad = cantidad - %s WHERE id=%s",(cantidad,id))

            cursor.execute("""
                INSERT INTO ventas
                (producto_id,nombre_producto,cantidad,precio_unitario,total,usuario)
                VALUES (%s,%s,%s,%s,%s,%s)
            """,(id,nombre_producto,cantidad,precio_unitario,total_venta,usuario_actual))

            conn.commit()

        return jsonify({"mensaje":"venta realizada"})

    except Exception as e:
        conn.rollback()
        print("🔥 ERROR VENTA:", e)
        return jsonify({"mensaje":"Error en la venta"}),500

# -------------------------
# NUEVAS RUTAS ADMIN
# -------------------------
@app.route("/sumar_stock", methods=["POST"])
@admin_required
def sumar_stock():
    data = request.get_json()
    id = int(data.get("id", 0))
    cantidad = int(data.get("cantidad", 0))
    if id <= 0 or cantidad <= 0:
        return jsonify({"mensaje":"Datos inválidos"}), 400

    with conn.cursor() as cursor:
        cursor.execute("UPDATE productos SET cantidad = cantidad + %s WHERE id=%s", (cantidad, id))
        conn.commit()
    return jsonify({"mensaje":"ok"})

@app.route("/restar_stock", methods=["POST"])
@admin_required
def restar_stock():
    data = request.get_json()
    id = int(data.get("id", 0))
    cantidad = int(data.get("cantidad", 0))
    if id <= 0 or cantidad <= 0:
        return jsonify({"mensaje":"Datos inválidos"}), 400

    with conn.cursor() as cursor:
        cursor.execute("SELECT cantidad FROM productos WHERE id=%s", (id,))
        stock_actual = cursor.fetchone()[0]
        if stock_actual < cantidad:
            return jsonify({"mensaje":"Stock insuficiente"}), 400

        cursor.execute("UPDATE productos SET cantidad = cantidad - %s WHERE id=%s", (cantidad, id))
        conn.commit()
    return jsonify({"mensaje":"ok"})

@app.route("/editar_precio", methods=["POST"])
@admin_required
def editar_precio():
    data = request.get_json()
    id = int(data.get("id",0))
    precio = float(data.get("precio",0))
    if id <= 0 or precio <= 0:
        return jsonify({"mensaje":"Datos inválidos"}), 400

    with conn.cursor() as cursor:
        cursor.execute("UPDATE productos SET precio = %s WHERE id=%s", (precio, id))
        conn.commit()
    return jsonify({"mensaje":"ok"})

@app.route("/eliminar_producto", methods=["POST"])
@admin_required
def eliminar_producto():
    data = request.get_json()
    id = int(data.get("id",0))
    if id <= 0:
        return jsonify({"mensaje":"Datos inválidos"}), 400

    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM productos WHERE id=%s", (id,))
        conn.commit()
    return jsonify({"mensaje":"ok"})

# -------------------------
# HISTORIAL
# -------------------------
@app.route("/api/historial")
def api_historial():
    if "usuario" not in session:
        return jsonify([])

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT nombre_producto,cantidad,precio_unitario,total,fecha,usuario
                FROM ventas
                ORDER BY fecha DESC
                LIMIT 100
            """)
            rows = cursor.fetchall()
    except Exception as e:
        conn.rollback()
        print("Error historial:", e)
        return jsonify([])

    historial = []
    for r in rows:
        historial.append({
            "producto": r[0],
            "cantidad": r[1],
            "precio_unitario": float(r[2]),
            "total": float(r[3]),
            "fecha": r[4].strftime("%Y-%m-%d %H:%M") if r[4] else "",
            "usuario": r[5]
        })

    return jsonify(historial)

# -------------------------
# DASHBOARD
# -------------------------
@app.route("/api/dashboard")
@admin_required
def api_dashboard():
    try:
        with conn.cursor() as cursor:

            cursor.execute("SELECT COALESCE(SUM(total),0) FROM ventas")
            total_ventas = cursor.fetchone()[0]

            cursor.execute("SELECT COALESCE(SUM(cantidad),0) FROM ventas")
            total_unidades = cursor.fetchone()[0]

            cursor.execute("""
                SELECT 
                    DATE_TRUNC('week', COALESCE(fecha, CURRENT_TIMESTAMP)) as semana,
                    SUM(cantidad),
                    SUM(total)
                FROM ventas
                GROUP BY semana
                ORDER BY semana
            """)

            rows = cursor.fetchall()

        semanas = []
        unidades = []
        ganancias = []

        for r in rows:
            semanas.append(str(r[0])[:10])
            unidades.append(r[1])
            ganancias.append(float(r[2]))

        return jsonify({
            "total_ventas": float(total_ventas),
            "total_unidades": int(total_unidades),
            "semanas": semanas,
            "unidades": unidades,
            "ganancias": ganancias
        })

    except Exception as e:
        conn.rollback()
        print("Error dashboard:", e)
        return jsonify({
            "total_ventas": 0,
            "total_unidades": 0,
            "semanas": [],
            "unidades": [],
            "ganancias": []
        })

# -------------------------
# FIX FECHAS VACÍAS
# -------------------------
try:
    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE ventas
            SET fecha = CURRENT_TIMESTAMP
            WHERE fecha IS NULL;
        """)
        conn.commit()
        print("✅ Fechas corregidas correctamente")

except Exception as e:
    conn.rollback()
    print("❌ Error corrigiendo fechas:", e)

# -------------------------
# SERVIDOR
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port, debug=True)