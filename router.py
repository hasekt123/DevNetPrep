"""
Router - Load Balancer
Port: 8000

Požadavky:
- Ratio 1:3 load balancing (JS:Python) => z každých 4 requestů:
  1x pošleme na JS server (8002), 3x na Python server (8001)
- Router musí podporovat všechny HTTP metody (GET/POST/PUT/...)
- Router má jen přeposílat (proxy) požadavek na jeden ze serverů
- Hlavičku X-Server-ID nastavují cílové servery, router ji nemá "vymýšlet"
"""

from flask import Flask, request, Response
import requests

app = Flask(__name__)

PY_SERVER = "http://localhost:8001"
JS_SERVER = "http://localhost:8002"

# Počítadlo requestů – podle něj děláme poměr 1:3.
# Sekvence serverů pro 4 requesty: [JS, PY, PY, PY] a pak znovu.
counter = 0


def pick_target_base_url() -> str:
    """
    Vybere cílový server podle ratio 1:3 (JS:Python).

    Proč takhle:
    - nejjednodušší deterministic load balancing
    - pro každý request zvýšíme counter
    - counter % 4:
        0 -> JS
        1 -> PY
        2 -> PY
        3 -> PY
    """
    global counter
    choice = counter % 4
    counter += 1
    return JS_SERVER if choice == 0 else PY_SERVER


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy(path):
    """
    Catch-all route:
    - chytí /drinks, /drinks/1, cokoliv…
    - a přepošle to na vybraný backend server

    Důležité body proxy:
    1) zachovat HTTP metodu (GET/POST/PUT/...)
    2) zachovat query string (?a=1)
    3) přeposlat body (JSON)
    4) přeposlat hlavičky (ale některé je lepší filtrovat)
    5) vrátit status code i body odpovědi
    """
    target_base = pick_target_base_url()

    # poskládáme cílovou URL (včetně cesty)
    target_url = f"{target_base}/{path}"

    # query string (např. ?x=5) chceme zachovat
    if request.query_string:
        target_url += "?" + request.query_string.decode("utf-8")

    # Předáme hlavičky dál, ale některé se do proxy přenosu nehodí.
    # Host typicky přepíše requests sám, Content-Length taky.
    forward_headers = {k: v for k, v in request.headers.items()
                       if k.lower() not in ["host", "content-length"]}

    # Data těla:
    # - pro JSON/POST/PUT je to request.get_data()
    body = request.get_data()

    # Tohle je hlavní proxy call: requests.request umí libovolnou metodu
    backend_resp = requests.request(
        method=request.method,
        url=target_url,
        headers=forward_headers,
        data=body,
        allow_redirects=False,
    )

    # Vrátíme odpověď tak, aby klient viděl to, co poslal backend.
    # backend už posílá X-Server-ID, takže ho zachováme.
    excluded = {"transfer-encoding", "connection", "keep-alive", "proxy-authenticate",
                "proxy-authorization", "te", "trailers", "upgrade"}

    resp_headers = [(k, v) for k, v in backend_resp.headers.items()
                    if k.lower() not in excluded]

    return Response(
        response=backend_resp.content,
        status=backend_resp.status_code,
        headers=resp_headers
    )


if __name__ == "__main__":
    app.run(port=8000, debug=True)
