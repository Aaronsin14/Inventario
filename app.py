from flask import Flask, render_template, request, jsonify, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"  # 🔹 Necesario para login/usuarios

UPLOAD = "static/uploads"
if not os.path.exists(UPLOAD):
    os.makedirs(UPLOAD)

# -------------------------
# CONEXIÓN BASE DE DATOS
# -------------------------

DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://inventario_user:VG0AF852QrAB0xMr9lRWlyWnpybQBTNA@dpg-d6nhomh5pdvs73bin8og-a.oregon-postgres.render.com/inventario_4oa6"
conn = psycopg2.connect(DATABASE_URL, sslmode="require")

# 🔥 AGREGADO
def check_conn():
    global conn
    try:
        conn.cursor()
    except:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")

# -------------------------
# CREAR TABLAS
# -------------------------

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
        vendedor VARCHAR(50)
    )
    """)
    conn.commit()

# -------------------------
# LOGIN DE ADMIN Y VENDEDORES
# -------------------------

USUARIOS = {
    "admin": {"password": "1234", "rol": "admin"},
    "vendedor1": {"password": "1111", "rol": "vendedor"},
    "vendedor2": {"password": "2222", "rol": "vendedor"},
    "vendedor3": {"password": "3333", "rol": "vendedor"}
}

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    usuario = data.get("usuario")
    password = data.get("password")

    if usuario in USUARIOS and USUARIOS[usuario]["password"] == password:
        session["usuario"] = usuario
        session["rol"] = USUARIOS[usuario]["rol"]
        return jsonify({"rol": USUARIOS[usuario]["rol"]})
    return jsonify({"mensaje": "Usuario o contraseña incorrecta"}), 401

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
# OBTENER PRODUCTOS
# -------------------------

@app.route("/productos")
def productos():

    check_conn()

    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT id,codigo,nombre,descripcion,marca,
        cantidad,precio,precio_minimo,foto
        FROM productos
        ORDER BY id DESC
        """)
        rows = cursor.fetchall()

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

    check_conn()

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
# SUMAR STOCK
# -------------------------

@app.route("/sumar/<int:id>", methods=["POST"])
def sumar(id):

    check_conn()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE productos
            SET cantidad = cantidad + 1
            WHERE id = %s
            """,(id,))
            conn.commit()

        return jsonify({"mensaje":"sumado"})

    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({"mensaje":"error"}),500

# -------------------------
# RESTAR STOCK
# -------------------------

@app.route("/restar/<int:id>", methods=["POST"])
def restar(id):

    check_conn()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE productos
            SET cantidad = GREATEST(cantidad - 1,0)
            WHERE id = %s
            """,(id,))
            conn.commit()

        return jsonify({"mensaje":"restado"})

    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({"mensaje":"error"}),500

# -------------------------
# ELIMINAR PRODUCTO
# -------------------------

@app.route("/eliminar/<int:id>", methods=["DELETE"])
def eliminar(id):

    check_conn()

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
# VENDER PRODUCTO
# -------------------------

@app.route("/vender_producto", methods=["POST"])
def vender_producto():

    check_conn()

    try:
        data = request.get_json()

        id = int(data["id"])
        cantidad = int(data["cantidad"])
        precio_especial = float(data.get("precio") or 0)

        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT nombre,precio,cantidad
            FROM productos
            WHERE id=%s
            """,(id,))

            row = cursor.fetchone()

            if not row:
                return jsonify({"mensaje":"Producto no encontrado"}),404

            nombre_producto = row[0]
            precio_real = float(row[1])
            stock_actual = int(row[2])

            if cantidad > stock_actual:
                return jsonify({"mensaje":"Stock insuficiente"}),400

            precio_unitario = precio_especial if precio_especial > 0 else precio_real

            total_venta = precio_unitario * cantidad

            cursor.execute("""
            UPDATE productos
            SET cantidad = cantidad - %s
            WHERE id = %s
            """,(cantidad,id))

            cursor.execute("""
            INSERT INTO ventas
            (producto_id,nombre_producto,cantidad,precio_unitario,total,vendedor)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,(id,nombre_producto,cantidad,precio_unitario,total_venta,session.get("usuario")))

            conn.commit()

        return jsonify({"mensaje":"venta realizada"})

    except Exception as e:
        conn.rollback()
        print("ERROR:",e)
        return jsonify({"mensaje":"Error en la venta"}),500

# -------------------------
# HISTORIAL
# -------------------------

@app.route("/api/historial")
def api_historial():

    check_conn()

    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT nombre_producto,cantidad,precio_unitario,total,fecha,vendedor
        FROM ventas
        ORDER BY fecha DESC
        LIMIT 100
        """)
        rows = cursor.fetchall()

    historial = []

    for r in rows:
        fecha = r[4]
        historial.append({
            "producto": r[0],
            "cantidad": r[1],
            "precio_unitario": float(r[2]),
            "total": float(r[3]),
            "fecha": fecha.strftime("%Y-%m-%d %H:%M") if fecha else "",
            "vendedor": r[5]
        })

    return jsonify(historial)

# -------------------------
# 🧨 BORRAR HISTORIAL
# -------------------------

@app.route("/borrar_historial")
def borrar_historial():

    check_conn()

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

    check_conn()

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

        data = []

        for r in rows:
            data.append({
                "semana": str(r[0]),
                "total_unidades": int(r[1] or 0),
                "total_ganancias": float(r[2] or 0)
            })

        return jsonify(data)

    except Exception as e:
        print("ERROR DASHBOARD:", e)
        return jsonify([])

# -------------------------
# SERVIDOR
# -------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT",10000))

    app.run(host="0.0.0.0",port=port)