const lista = document.getElementById("lista")
const buscar = document.getElementById("buscar")

async function cargar(){

const res = await fetch("/productos")
const data = await res.json()

lista.innerHTML=""

data.forEach(p=>{

let stock = p.cantidad <=5 ? "stock-bajo" : ""

lista.innerHTML += `

<div class="producto">

<img src="${p.foto}" onerror="this.src='https://via.placeholder.com/300'">

<div class="producto-info">

<h3>${p.nombre}</h3>

<p><b>Código:</b> ${p.codigo}</p>

<p><b>Marca:</b> ${p.marca}</p>

<p>${p.descripcion}</p>

<p class="stock ${stock}">Stock: ${p.cantidad}</p>

<button onclick="sumar(${p.id})">➕</button>

<button onclick="restar(${p.id})">➖</button>

<button onclick="eliminar(${p.id})">🗑</button>

</div>

</div>

`

})

}

document.getElementById("form").addEventListener("submit", async e=>{

e.preventDefault()

const form = new FormData(e.target)

await fetch("/agregar",{

method:"POST",
body:form

})

e.target.reset()

cargar()

})

async function sumar(id){

await fetch("/sumar/"+id,{
method:"POST"
})

cargar()

}

async function restar(id){

await fetch("/restar/"+id,{
method:"POST"
})

cargar()

}

async function eliminar(id){

await fetch("/eliminar/"+id,{
method:"DELETE"
})

cargar()

}

buscar.addEventListener("keyup",()=>{

let texto = buscar.value.toLowerCase()

document.querySelectorAll(".producto").forEach(p=>{

p.style.display = p.innerText.toLowerCase().includes(texto)
? "block" : "none"

})

})

cargar()