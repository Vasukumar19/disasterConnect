async function loadPeers() {
  const r = await fetch("/api/peers");
  const data = await r.json();
  const ul = document.getElementById("peers");
  ul.innerHTML = "";
  Object.keys(data).forEach(p => {
    const li = document.createElement("li");
    li.textContent = p;
    ul.appendChild(li);
  });
}

async function send() {
  const type = document.getElementById("type").value;
  const text = document.getElementById("msg").value;
  await fetch("/api/send", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({type, text})
  });
}

setInterval(loadPeers, 3000);
loadPeers();
