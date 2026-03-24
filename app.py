from flask import Flask, render_template, request, jsonify, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "mi_clave_secreta_123"  # Para sesiones

UPLOAD = "static/uploads"
if not os.path.exists(UPLOAD):
    os.makedirs(UPLOAD)

# -------------------------
# CONEXIÓN BASE DE DATOS
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://inventario_user:VG0AF852QrAB0xMr9lRWlyWnpybQBTNA@dpg-d6nhomh5pdvs73bin8og-a.oregon-postgres.render.com/inventario_4oa6"
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
conn.autocommit = False  # Mantenemos transacciones para INSERT/UPDATE/DELETE

# -------------------------
# CREAR TABLAS
# -------------------------
try:
    with conn.cursor() as cursor:
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
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas(
            id SERIAL PRIMARY KEY,
            producto_id INTEGER REFERENCES productos(id),
            nombre_producto VARCHAR(100),
            cantidad INTEGER,
            precio_unitario NUMERIC,
            total NUMERIC,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario VARCHAR(100)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100),
            usuario VARCHAR(50) UNIQUE,
            password VARCHAR(50),
            rol VARCHAR(20)
        )
        """)
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
# PAGINAS
# -------------------------
@app.route("/")
def inicio():
    return render_template("inicio.html")

@app.route("/agregar")
def agregar_pagina():
    return render_template("agregar.html")

@app.route("/inventario")
def inventario():
    return render_template("inventario.html")

@app.route("/vender")
def vender_pagina():
    return render_template("vender.html")

@app.route("/historial")
def historial_pagina():
    return render_template("historial.html")

@app.route("/dashboard")
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
        return jsonify({"mensaje":"ok"})
    else:
        return jsonify({"mensaje":"usuario o contraseña incorrecta"}),401

@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"mensaje":"ok"})

@app.route("/api/usuario_actual")
def usuario_actual():
    if "usuario" in session:
        return jsonify({"usuario": session["usuario"]})
    return jsonify({"usuario": None}), 401

# -------------------------
# OBTENER PRODUCTOS
# -------------------------
@app.route("/productos")
def productos():
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
            nombre_foto = foto.filename
            ruta = "/static/uploads/" + nombre_foto
            foto.save(os.path.join(UPLOAD, nombre_foto))

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
# SUMAR / RESTAR / ELIMINAR
# -------------------------
@app.route("/sumar/<int:id>", methods=["POST"])
def sumar(id):
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE productos SET cantidad = cantidad + 1 WHERE id = %s",(id,))
            conn.commit()
        return jsonify({"mensaje":"sumado"})
    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({"mensaje":"error"}),500

@app.route("/restar/<int:id>", methods=["POST"])
def restar(id):
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE productos SET cantidad = GREATEST(cantidad - 1,0) WHERE id = %s",(id,))
            conn.commit()
        return jsonify({"mensaje":"restado"})
    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({"mensaje":"error"}),500

@app.route("/eliminar/<int:id>", methods=["DELETE"])
def eliminar(id):
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM productos WHERE id=%s",(id,))
            conn.commit()
        return jsonify({"mensaje":"eliminado"})
    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({"mensaje":"error"}),500

# -------------------------
# VENDER PRODUCTO (con usuario)
# -------------------------
@app.route("/vender_producto", methods=["POST"])
def vender_producto():
    try:
        if "usuario" not in session:
            return jsonify({"mensaje":"No autenticado"}),403

        data = request.get_json()
        id = int(data["id"])
        cantidad = int(data["cantidad"])
        precio_especial = float(data.get("precio") or 0)
        usuario_actual = session["usuario"]

        with conn.cursor() as cursor:
            cursor.execute("SELECT nombre,precio,cantidad FROM productos WHERE id=%s",(id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"mensaje":"Producto no encontrado"}),404

            nombre_producto, precio_real, stock_actual = row
            if cantidad > stock_actual:
                return jsonify({"mensaje":"Stock insuficiente"}),400

            precio_unitario = precio_especial if precio_especial>0 else float(precio_real)
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
        print("ERROR:",e)
        return jsonify({"mensaje":"Error en la venta"}),500

# -------------------------
# HISTORIAL CON USUARIO
# -------------------------
@app.route("/api/historial")
def api_historial():
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
        fecha = r[4]
        historial.append({
            "producto": r[0],
            "cantidad": r[1],
            "precio_unitario": float(r[2]),
            "total": float(r[3]),
            "fecha": fecha.strftime("%Y-%m-%d %H:%M") if fecha else "",
            "usuario": r[5]
        })
    return jsonify(historial)

# -------------------------
# BORRAR HISTORIAL
# -------------------------
@app.route("/borrar_historial")
def borrar_historial():
    try:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE ventas RESTART IDENTITY CASCADE;")
            conn.commit()
        return "Historial eliminado 🔥"
    except Exception as e:
        conn.rollback()
        print(e)
        return "Error"

# -------------------------
# DASHBOARD
# -------------------------
@app.route("/api/dashboard")
def api_dashboard():
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT 
            DATE(COALESCE(fecha, CURRENT_TIMESTAMP)) as dia,
            SUM(cantidad) as unidades,
            SUM(total) as ganancias
            FROM ventas
            GROUP BY dia
            ORDER BY dia DESC
            LIMIT 30
            """)
            rows = cursor.fetchall()
    except Exception as e:
        conn.rollback()
        print("ERROR DASHBOARD:", e)
        return jsonify([])

    data = []
    for r in rows:
        data.append({
            "semana": str(r[0]),
            "total_unidades": int(r[1] or 0),
            "total_ganancias": float(r[2] or 0)
        })
    return jsonify(data)

# -------------------------
# SERVIDOR
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port, debug=True)