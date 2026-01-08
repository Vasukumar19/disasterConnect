const express = require("express");
const app = express();
app.use(express.json());
app.use(express.static("public"));

const PY = "http://localhost:9000";

app.get("/api/peers", async (req, res) => {
  const r = await fetch(`${PY}/peers`);
  res.json(await r.json());
});

app.post("/api/send", async (req, res) => {
  const r = await fetch(`${PY}/send`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(req.body)
  });
  res.json(await r.json());
});

app.listen(3000, () => console.log("UI at http://localhost:3000"));
