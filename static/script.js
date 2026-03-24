const lista = document.getElementById("lista")
const buscar = document.getElementById("buscar")

async function cargar(){

    if(!lista) return

    const res = await fetch("/productos")
    const data = await res.json()

    lista.innerHTML=""

    data.forEach(p=>{

        let stock = p.cantidad <=5 ? "stock-bajo" : ""

        let precio = Number(p.precio || 0).toLocaleString()
        let precio_minimo = Number(p.precio_minimo || 0).toLocaleString()

        lista.innerHTML += `
        <div class="producto">
            <img src="${p.foto}" onerror="this.src='https://via.placeholder.com/300'">
            <div class="producto-info">
                <h3>${p.nombre}</h3>
                <p><b>Código:</b> ${p.codigo}</p>
                <p><b>Marca:</b> ${p.marca}</p>
                <p>${p.descripcion || ""}</p>
                <p>
                    <b>Precio:</b> $${precio}
                    ${rol === 'admin' ? `<button onclick="editarPrecio(${p.id}, ${p.precio})">✏️</button>` : ""}
                </p>
                <p><b>Precio mínimo:</b> $${precio_minimo}</p>
                <p class="stock ${stock}">Stock: ${p.cantidad}</p>
                ${rol === 'admin' ? `
                    <button onclick="sumar(${p.id})">➕</button>
                    <button onclick="restar(${p.id})">➖</button>
                    <button onclick="eliminar(${p.id})">🗑</button>
                ` : ""}
            </div>
        </div>
        `
    })
}

// SUMAR STOCK
async function sumar(id){
    let cantidad = prompt("Ingrese cantidad a sumar:")
    if(!cantidad) return
    await fetch("/sumar_stock",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({id:id, cantidad:parseInt(cantidad)})
    })
    cargar()
}

// RESTAR STOCK
async function restar(id){
    let cantidad = prompt("Ingrese cantidad a restar:")
    if(!cantidad) return
    await fetch("/restar_stock",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({id:id, cantidad:parseInt(cantidad)})
    })
    cargar()
}

// ELIMINAR PRODUCTO
async function eliminar(id){
    if(!confirm("¿Eliminar producto?")) return
    await fetch("/eliminar_producto",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({id:id})
    })
    cargar()
}

// EDITAR PRECIO
async function editarPrecio(id, precioActual){
    let nuevo = prompt("Nuevo precio:", precioActual)
    if(!nuevo) return
    await fetch("/editar_precio",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({id:id, precio:parseFloat(nuevo)})
    })
    cargar()
}

// FILTRO DE BÚSQUEDA
buscar?.addEventListener("keyup",()=>{
    let texto = buscar.value.toLowerCase()
    document.querySelectorAll(".producto").forEach(p=>{
        p.style.display = p.innerText.toLowerCase().includes(texto) ? "block" : "none"
    })
})

// CARGAR PRODUCTOS AL INICIO
cargar()