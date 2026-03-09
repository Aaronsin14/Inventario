from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

ARCHIVO = "inventario.json"
UPLOAD = "static/uploads"

if not os.path.exists(UPLOAD):
    os.makedirs(UPLOAD)

def leer():
    if not os.path.exists(ARCHIVO):
        return []

    with open(ARCHIVO,"r") as f:
        return json.load(f)

def guardar(data):
    with open(ARCHIVO,"w") as f:
        json.dump(data,f,indent=4)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/productos")
def productos():
    return jsonify(leer())

@app.route("/agregar", methods=["POST"])
def agregar():

    data = leer()

    codigo = request.form["codigo"]
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    marca = request.form["marca"]
    cantidad = int(request.form["cantidad"])
    foto = request.files["foto"]

    ruta = ""

    if foto and foto.filename != "":
        ruta = os.path.join(UPLOAD,foto.filename)
        foto.save(ruta)

    producto = {
        "id": len(data)+1,
        "codigo": codigo,
        "nombre": nombre,
        "descripcion": descripcion,
        "marca": marca,
        "cantidad": cantidad,
        "foto": ruta
    }

    data.append(producto)

    guardar(data)

    return jsonify({"mensaje":"ok"})


@app.route("/sumar/<int:id>", methods=["POST"])
def sumar(id):

    data = leer()

    for p in data:
        if p["id"] == id:
            p["cantidad"] += 1

    guardar(data)

    return jsonify({"mensaje":"sumado"})


@app.route("/restar/<int:id>", methods=["POST"])
def restar(id):

    data = leer()

    for p in data:
        if p["id"] == id and p["cantidad"] > 0:
            p["cantidad"] -= 1

    guardar(data)

    return jsonify({"mensaje":"restado"})


@app.route("/eliminar/<int:id>", methods=["DELETE"])
def eliminar(id):

    data = leer()

    data = [p for p in data if p["id"] != id]

    guardar(data)

    return jsonify({"mensaje":"eliminado"})


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)