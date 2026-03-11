from flask import Flask, render_template, request, jsonify
import psycopg2
import os

app = Flask(__name__)

UPLOAD = "static/uploads"

if not os.path.exists(UPLOAD):
    os.makedirs(UPLOAD)

# obtener url de base de datos desde render
DATABASE_URL = os.getenv("DATABASE_URL")

# conexión segura para render
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cursor = conn.cursor()

# crear tabla si no existe
cursor.execute("""
CREATE TABLE IF NOT EXISTS productos(
id SERIAL PRIMARY KEY,
codigo VARCHAR(50),
nombre VARCHAR(100),
descripcion TEXT,
marca VARCHAR(100),
cantidad INTEGER,
foto TEXT
)
""")
conn.commit()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/productos")
def productos():

    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
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
            "foto": r[6]
        })

    return jsonify(productos)


@app.route("/agregar", methods=["POST"])
def agregar():

    codigo = request.form["codigo"]
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    marca = request.form["marca"]
    cantidad = int(request.form["cantidad"])
    foto = request.files["foto"]

    ruta = ""

    if foto and foto.filename != "":
        ruta = os.path.join(UPLOAD, foto.filename)
        foto.save(ruta)

    cursor.execute("""
    INSERT INTO productos
    (codigo,nombre,descripcion,marca,cantidad,foto)
    VALUES (%s,%s,%s,%s,%s,%s)
    """,(codigo,nombre,descripcion,marca,cantidad,ruta))

    conn.commit()

    return jsonify({"mensaje":"ok"})


@app.route("/sumar/<int:id>", methods=["POST"])
def sumar(id):

    cursor.execute("""
    UPDATE productos
    SET cantidad = cantidad + 1
    WHERE id = %s
    """,(id,))

    conn.commit()

    return jsonify({"mensaje":"sumado"})


@app.route("/restar/<int:id>", methods=["POST"])
def restar(id):

    cursor.execute("""
    UPDATE productos
    SET cantidad = GREATEST(cantidad - 1,0)
    WHERE id = %s
    """,(id,))

    conn.commit()

    return jsonify({"mensaje":"restado"})


@app.route("/eliminar/<int:id>", methods=["DELETE"])
def eliminar(id):

    cursor.execute("DELETE FROM productos WHERE id = %s",(id,))
    conn.commit()

    return jsonify({"mensaje":"eliminado"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)