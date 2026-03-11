from flask import Flask, render_template, request, jsonify
import psycopg2
import os

app = Flask(__name__)

UPLOAD = "static/uploads"

if not os.path.exists(UPLOAD):
    os.makedirs(UPLOAD)

# -------------------------
# CONEXIÓN BASE DE DATOS
# -------------------------

DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://inventario_user:VG0AF852QrAB0xMr9lRWlyWnpybQBTNA@dpg-d6nhomh5pdvs73bin8og-a.oregon-postgres.render.com/inventario_4oa6"

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
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

# -------------------------
# PAGINAS
# -------------------------

@app.route("/")
def inicio():
    return render_template("inicio.html")

@app.route("/agregar")
def agregar():
    return render_template("agregar.html")

@app.route("/inventario")
def inventario():
    return render_template("inventario.html")

@app.route("/vender")
def vender():
    return render_template("vender.html")

@app.route("/historial")
def historial():
    return render_template("historial.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# -------------------------
# OBTENER PRODUCTOS
# -------------------------

@app.route("/productos")
def productos():

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
# EDITAR PRECIO
# -------------------------

@app.route("/editar_precio/<int:id>", methods=["POST"])
def editar_precio(id):

    try:

        data = request.get_json()
        precio = float(data["precio"])

        with conn.cursor() as cursor:

            cursor.execute("""
            UPDATE productos
            SET precio=%s
            WHERE id=%s
            """,(precio,id))

            conn.commit()

        return jsonify({"mensaje":"Precio actualizado"})

    except Exception as e:

        conn.rollback()
        print(e)

        return jsonify({"mensaje":"Error"}),500

# -------------------------
# SUMAR STOCK
# -------------------------

@app.route("/sumar/<int:id>", methods=["POST"])
def sumar(id):

    with conn.cursor() as cursor:

        cursor.execute("""
        UPDATE productos
        SET cantidad=cantidad+1
        WHERE id=%s
        """,(id,))

        conn.commit()

    return jsonify({"mensaje":"ok"})

# -------------------------
# RESTAR STOCK
# -------------------------

@app.route("/restar/<int:id>", methods=["POST"])
def restar(id):

    with conn.cursor() as cursor:

        cursor.execute("""
        UPDATE productos
        SET cantidad=GREATEST(cantidad-1,0)
        WHERE id=%s
        """,(id,))

        conn.commit()

    return jsonify({"mensaje":"ok"})

# -------------------------
# ELIMINAR PRODUCTO
# -------------------------

@app.route("/eliminar/<int:id>", methods=["DELETE"])
def eliminar(id):

    with conn.cursor() as cursor:

        cursor.execute("DELETE FROM productos WHERE id=%s",(id,))
        conn.commit()

    return jsonify({"mensaje":"eliminado"})

# -------------------------
# VENDER PRODUCTO
# -------------------------

@app.route("/vender_producto", methods=["POST"])
def vender_producto():

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

            nombre = row[0]
            precio_real = float(row[1])
            stock = int(row[2])

            if cantidad > stock:
                return jsonify({"mensaje":"Stock insuficiente"}),400

            precio_final = precio_especial if precio_especial>0 else precio_real

            total = precio_final*cantidad

            cursor.execute("""
            UPDATE productos
            SET cantidad=cantidad-%s
            WHERE id=%s
            """,(cantidad,id))

            cursor.execute("""
            INSERT INTO ventas
            (producto_id,nombre_producto,cantidad,precio_unitario,total)
            VALUES (%s,%s,%s,%s,%s)
            """,(id,nombre,cantidad,precio_final,total))

            conn.commit()

        return jsonify({"mensaje":"Venta realizada"})

    except Exception as e:

        conn.rollback()
        print(e)

        return jsonify({"mensaje":"Error"}),500

# -------------------------
# HISTORIAL
# -------------------------

@app.route("/api/historial")
def api_historial():

    with conn.cursor() as cursor:

        cursor.execute("""
        SELECT nombre_producto,cantidad,precio_unitario,total,fecha
        FROM ventas
        ORDER BY fecha DESC
        """)

        rows = cursor.fetchall()

    historial = []

    for r in rows:

        historial.append({
            "producto": r[0],
            "cantidad": r[1],
            "precio_unitario": float(r[2]),
            "total": float(r[3]),
            "fecha": r[4].strftime("%Y-%m-%d %H:%M") if r[4] else ""
        })

    return jsonify(historial)

# -------------------------
# DASHBOARD
# -------------------------

@app.route("/api/dashboard")
def api_dashboard():

    with conn.cursor() as cursor:

        cursor.execute("""
        SELECT DATE_TRUNC('week',fecha),
        SUM(cantidad),
        SUM(total)
        FROM ventas
        WHERE fecha IS NOT NULL
        GROUP BY 1
        ORDER BY 1 DESC
        """)

        rows = cursor.fetchall()

    data=[]

    for r in rows:

        data.append({
            "semana": r[0].strftime("%Y-%m-%d"),
            "total_unidades": int(r[1]),
            "total_ganancias": float(r[2])
        })

    return jsonify(data)

# -------------------------
# SERVIDOR
# -------------------------

if __name__=="__main__":

    port=int(os.environ.get("PORT",10000))

    app.run(host="0.0.0.0",port=port)