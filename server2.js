/**
 * Server 2 - Node.js Express REST API pro správu nápojového lístku
 * Port: 8002
 *
 * Požadavky:
 * - GET  /drinks
 * - GET  /drinks/:id
 * - POST /drinks        (ignoruje id z body, generuje vlastní)
 * - PUT  /drinks/:id
 * - Každá odpověď musí mít hlavičku: X-Server-ID: 2
 */

const express = require("express");
const fs = require("fs");
const path = require("path");

const app = express();
app.use(express.json());

const DB_FILE = path.join(__dirname, "db.json");

// -------------------------
// Pomocné funkce pro DB
// -------------------------

function loadData() {
    // Načteme celý JSON soubor do JS objektu
    return JSON.parse(fs.readFileSync(DB_FILE, "utf-8"));
}

function saveData(data) {
    // Zapíšeme celý objekt zpátky (null,2 = hezké odsazení)
    fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2), "utf-8");
}

// Middleware: proběhne před každým endpointem a nastaví hlavičku.
// Díky tomu nemusíme X-Server-ID psát ručně do každé route.
app.use((req, res, next) => {
    res.set("X-Server-ID", "2");
    next();
});

// -------------------------
// REST API endpointy
// -------------------------

app.get("/drinks", (req, res) => {
    const data = loadData();
    return res.status(200).json({ drinks: data.drinks });
});

app.get("/drinks/:id", (req, res) => {
    const data = loadData();
    const id = Number(req.params.id);

    const drink = data.drinks.find((d) => d.id === id);
    if (!drink) return res.status(404).json({ error: "Not found" });

    return res.status(200).json(drink);
});

app.post("/drinks", (req, res) => {
    const data = loadData();
    const body = req.body; // bez sanitizace (jak chceš)

    // Generování id stejně jako v Python serveru
    const maxId = data.drinks.reduce((m, d) => Math.max(m, d.id), 0);
    const newId = maxId + 1;

    body.id = newId; // ignoruje id z body a přepíše ho

    data.drinks.push(body);
    saveData(data);

    return res.status(201).json(body);
});

app.put("/drinks/:id", (req, res) => {
    const data = loadData();
    const id = Number(req.params.id);
    const body = req.body;

    const index = data.drinks.findIndex((d) => d.id === id);
    if (index === -1) return res.status(404).json({ error: "Not found" });

    // id se nesmí změnit -> přepíšeme ho na správné
    body.id = id;

    // "replace" logika: celou položku nahradíme
    data.drinks[index] = body;
    saveData(data);

    return res.status(200).json(body);
});

app.listen(8002, () => {
    console.log("Server 2 (JS) běží na portu 8002");
});
