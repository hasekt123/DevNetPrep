"""
Server 1 - Python Flask REST API pro správu nápojového lístku
Port: 8001

Požadavky (z PDF):
- GET  /drinks           -> vrátí všechny záznamy
- GET  /drinks/<id>      -> vrátí záznam podle ID
- POST /drinks           -> vytvoří nový záznam (ignoruje id v body, generuje svoje)
- PUT  /drinks/<id>      -> upraví existující záznam
- Každá odpověď musí mít hlavičku: X-Server-ID: 1
"""

from flask import Flask, jsonify, request, make_response
import json
from pathlib import Path

app = Flask(__name__)

# db.json je naše "mini databáze" – reálně je to jen soubor s JSONem
DB_FILE = Path("db.json")


# -------------------------
# Pomocné funkce pro DB
# -------------------------

def load_data() -> dict:
    """
    Načtení celé DB do paměti (Python dict).
    Proč to děláme:
    - db.json je malý, takže ho můžeme celý načíst.
    - V reálné DB bys dotazoval SQL, tady jen čteme soubor.
    """
    with DB_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict) -> None:
    """
    Uložení celé DB zpátky do souboru.
    ensure_ascii=False = zachová diakritiku normálně.
    indent=2 = hezké formátování souboru.
    """
    with DB_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_server_header(payload, status_code=200):
    """
    Zadání chce hlavičku X-Server-ID v KAŽDÉ odpovědi.
    Flask standardně vrací JSON přes jsonify(), ale hlavičky se nastavují na response objektu.
    Proto uděláme response přes make_response() a přidáme hlavičku.
    """
    resp = make_response(jsonify(payload), status_code)
    resp.headers["X-Server-ID"] = "1"
    return resp


# -------------------------
# REST API endpointy
# -------------------------

@app.get("/drinks")
def get_all_drinks():
    """
    GET /drinks
    Vrací všechny drinky.

    Vracím {"drinks": [...]} aby to bylo přehledné a kompatibilní s tvým db.json.
    """
    data = load_data()
    return add_server_header({"drinks": data["drinks"]}, 200)


@app.get("/drinks/<int:drink_id>")
def get_drink_by_id(drink_id: int):
    """
    GET /drinks/<id>
    Najdeme drink podle ID.

    - projdeme seznam data["drinks"]
    - pokud najdeme id, vrátíme celý objekt drinku
    - pokud ne, vrátíme 404
    """
    data = load_data()

    for d in data["drinks"]:
        if d.get("id") == drink_id:
            return add_server_header(d, 200)

    return add_server_header({"error": "Not found"}, 404)


@app.post("/drinks")
def create_drink():
    """
    POST /drinks
    Vytvoří nový záznam.

    Požadavek ze zadání:
    - ignorovat id v těle požadavku
    - server generuje vlastní id

    Jak generujeme id:
    - vezmeme max existující id (nebo 0 když je seznam prázdný)
    - nové id = max + 1
    """
    data = load_data()
    body = request.get_json(force=True)  # force=True: vezme JSON i když klient nedá správný header (užitečné při testování)

    new_id = max((d["id"] for d in data["drinks"]), default=0) + 1

    # "bez sanitizace" = bereme, co přišlo (name/category/price/available),
    # jen přepíšeme id na naše generované.
    body["id"] = new_id

    data["drinks"].append(body)
    save_data(data)

    return add_server_header(body, 201)


@app.put("/drinks/<int:drink_id>")
def update_drink(drink_id: int):
    """
    PUT /drinks/<id>
    Upravit existující záznam.

    Praktická logika:
    - najdeme drink podle id
    - vezmeme body
    - ignorujeme id v body (nesmí změnit primární klíč)
    - přepíšeme záznam novými hodnotami
    - uložíme db.json
    - vrátíme aktualizovaný objekt

    Pozn.: bez sanitizace = nekontrolujeme typy ani povinné klíče.
    """
    data = load_data()
    body = request.get_json(force=True)

    for i, d in enumerate(data["drinks"]):
        if d.get("id") == drink_id:
            # zachováme původní id
            body["id"] = drink_id

            # Tady děláme "replace" (celou položku nahradíme).
            # Alternativa by byla "patch" (měnit jen klíče, které přišly).
            data["drinks"][i] = body

            save_data(data)
            return add_server_header(body, 200)

    return add_server_header({"error": "Not found"}, 404)


if __name__ == "__main__":
    # debug=True: při vývoji se to auto-restartuje při změně souboru
    app.run(port=8001, debug=True)
