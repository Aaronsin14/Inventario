const lista = document.getElementById("lista");
const buscar = document.getElementById("buscarProducto");
const usuarioSpan = document.getElementById("usuarioLogueado");

// -------------------------
// Obtener usuario logueado
// -------------------------
async function obtenerUsuario() {
    try {
        const res = await fetch("/api/usuario_actual");
        if(res.ok){
            const data = await res.json();
            usuarioSpan.textContent = data.usuario;
        } else {
            window.location.href = "/"; // Redirige a login si no hay sesión
        }
    } catch(err){
        console.error(err);
        window.location.href = "/";
    }
}

// -------------------------
// Logout
// -------------------------
async function logout(){
    await fetch("/logout");
    window.location.href = "/";
}

// -------------------------
// Cargar productos
// -------------------------
async function cargar(){
    try{
        const res = await fetch("/productos");
        const data = await res.json();

        lista.innerHTML = "";

        data.forEach(p=>{

            lista.innerHTML += `
            <div class="producto">
                <img src="${p.foto}" onerror="this.src='https://via.placeholder.com/200'">
                <h3>${p.nombre}</h3>
                <p><b>Código:</b> ${p.codigo}</p>
                <p><b>Marca:</b> ${p.marca}</p>
                <p><b>Precio:</b> $${Number(p.precio).toLocaleString()}</p>
                <p><b>Precio mínimo:</b> $${Number(p.precio_minimo).toLocaleString()}</p>
                <p><b>Stock:</b> 
                    <span class="${p.cantidad <= 0 ? 'stock-bajo' : ''}">
                        ${p.cantidad}
                    </span>
                </p>
                <input type="number" placeholder="Precio especial" id="precio${p.id}">
                <input type="number" placeholder="Cantidad" id="cantidad${p.id}" value="1" min="1" max="${p.cantidad}">
                <button onclick="vender(${p.id})">💰 Vender</button>
            </div>
            `;
        });

    } catch(err){
        console.error("Error cargando productos",err);
        lista.innerHTML="<p>Error cargando productos</p>";
    }
}

// -------------------------
// Vender producto
// -------------------------
async function vender(id){
    const cantidadInput = document.getElementById("cantidad"+id);
    const precioInput = document.getElementById("precio"+id);

    const cantidad = parseInt(cantidadInput.value) || 0;
    const precio = parseFloat(precioInput.value) || 0;

    if(cantidad <= 0){
        alert("Ingresa una cantidad válida");
        return;
    }

    try{
        const res = await fetch("/vender_producto",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body: JSON.stringify({id:id,cantidad:cantidad,precio:precio})
        });

        const data = await res.json();

        if(res.ok){
            alert(data.mensaje);
        } else {
            alert(data.mensaje || "Error en la venta");
        }

        cargar();

    } catch(err){
        console.error("Error en la venta",err);
        alert("Error al procesar la venta");
    }
}

// -------------------------
// Buscador
// -------------------------
buscar?.addEventListener("keyup",()=>{
    let texto = buscar.value.toLowerCase();
    document.querySelectorAll(".producto").forEach(p=>{
        p.style.display = p.innerText.toLowerCase().includes(texto) ? "block" : "none";
    });
});

// -------------------------
// Inicializar
// -------------------------
obtenerUsuario();
cargar();