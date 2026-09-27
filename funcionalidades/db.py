import os
import sqlite3
import time

PASTA_ALVOS = "alvos"

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (
    chave TEXT PRIMARY KEY,
    valor TEXT
);

CREATE TABLE IF NOT EXISTS paginas (
    url TEXT PRIMARY KEY,
    tipo TEXT NOT NULL CHECK(tipo IN ('html', 'js')),
    js_codigo TEXT,
    coletado_em REAL
);

CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_origem TEXT NOT NULL REFERENCES paginas(url),
    href TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_links_origem ON links(url_origem);
CREATE INDEX IF NOT EXISTS idx_links_href ON links(href);

CREATE TABLE IF NOT EXISTS scripts_externos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_origem TEXT NOT NULL REFERENCES paginas(url),
    src TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scripts_ext_origem ON scripts_externos(url_origem);
CREATE INDEX IF NOT EXISTS idx_scripts_ext_src ON scripts_externos(src);

CREATE TABLE IF NOT EXISTS scripts_inline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_origem TEXT NOT NULL REFERENCES paginas(url),
    codigo TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scripts_inline_origem ON scripts_inline(url_origem);

CREATE TABLE IF NOT EXISTS css (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_origem TEXT NOT NULL REFERENCES paginas(url),
    href TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_css_origem ON css(url_origem);
CREATE INDEX IF NOT EXISTS idx_css_href ON css(href);

CREATE TABLE IF NOT EXISTS post_params (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_origem TEXT NOT NULL REFERENCES paginas(url),
    nome TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_post_origem ON post_params(url_origem);
"""


def caminho_db(dominio: str) -> str:
    return os.path.join(PASTA_ALVOS, f"{dominio}.db")


def existe_alvo(dominio: str) -> bool:
    return os.path.exists(caminho_db(dominio))


def conectar(dominio: str) -> sqlite3.Connection:
    if not os.path.exists(PASTA_ALVOS):
        os.mkdir(PASTA_ALVOS)
    conn = sqlite3.connect(caminho_db(dominio))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    return conn


def gravar_metadata(conn: sqlite3.Connection, alvo: str, dominio: str) -> None:
    agora = str(time.time())
    conn.executemany(
        """
        INSERT INTO metadata (chave, valor) VALUES (?, ?)
        ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
        """,
        [("alvo", alvo), ("dominio", dominio), ("ultima_execucao", agora)],
    )
    conn.execute(
        """
        INSERT INTO metadata (chave, valor) VALUES ('iniciado_em', ?)
        ON CONFLICT(chave) DO NOTHING
        """,
        (agora,),
    )
    conn.commit()


def obter_metadata(conn: sqlite3.Connection) -> dict:
    return dict(conn.execute("SELECT chave, valor FROM metadata").fetchall())


def pagina_ja_coletada(conn: sqlite3.Connection, url: str) -> bool:
    cur = conn.execute("SELECT 1 FROM paginas WHERE url = ?", (url,))
    return cur.fetchone() is not None


def urls_coletadas(conn: sqlite3.Connection) -> set:
    return {row[0] for row in conn.execute("SELECT url FROM paginas").fetchall()}


def contar_paginas(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM paginas").fetchone()[0]


def salvar_pagina_html(conn: sqlite3.Connection, url: str, resultado: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO paginas (url, tipo, js_codigo, coletado_em) VALUES (?, 'html', NULL, ?)",
        (url, time.time()),
    )
    # se a URL já existia (ex.: --resume reprocessando), limpa os filhos antes de reinserir
    for tabela in ("links", "scripts_externos", "scripts_inline", "css", "post_params"):
        conn.execute(f"DELETE FROM {tabela} WHERE url_origem = ?", (url,))

    conn.executemany("INSERT INTO links (url_origem, href) VALUES (?, ?)", [(url, h) for h in resultado["links"]])
    conn.executemany(
        "INSERT INTO scripts_externos (url_origem, src) VALUES (?, ?)",
        [(url, s) for s in resultado["scripts_externos"]],
    )
    conn.executemany(
        "INSERT INTO scripts_inline (url_origem, codigo) VALUES (?, ?)",
        [(url, c) for c in resultado["scripts_inline"]],
    )
    conn.executemany("INSERT INTO css (url_origem, href) VALUES (?, ?)", [(url, c) for c in resultado["css"]])
    conn.executemany(
        "INSERT INTO post_params (url_origem, nome) VALUES (?, ?)", [(url, n) for n in resultado["post"]]
    )
    conn.commit()


def salvar_pagina_js(conn: sqlite3.Connection, url: str, codigo: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO paginas (url, tipo, js_codigo, coletado_em) VALUES (?, 'js', ?, ?)",
        (url, codigo, time.time()),
    )
    conn.commit()


def frontier_pendente(conn: sqlite3.Connection) -> list:
    descobertas = {}
    for href, origem in conn.execute("SELECT href, url_origem FROM links").fetchall():
        descobertas.setdefault(href, origem)
    for src, origem in conn.execute("SELECT src, url_origem FROM scripts_externos").fetchall():
        descobertas.setdefault(src, origem)
    for href, origem in conn.execute("SELECT href, url_origem FROM css").fetchall():
        descobertas.setdefault(href, origem)

    coletadas = urls_coletadas(conn)
    return [(u, origem) for u, origem in descobertas.items() if u not in coletadas]


def salvar_descobertas_js(conn: sqlite3.Connection, descobertas: list) -> int:
    novos = 0
    for origem, url_js in descobertas:
        ja_existe = conn.execute(
            "SELECT 1 FROM scripts_externos WHERE url_origem = ? AND src = ?", (origem, url_js)
        ).fetchone()
        if ja_existe:
            continue
        conn.execute("INSERT INTO scripts_externos (url_origem, src) VALUES (?, ?)", (origem, url_js))
        novos += 1
    conn.commit()
    return novos


def listar_alvos() -> list:
    if not os.path.exists(PASTA_ALVOS):
        return []
    return sorted(f for f in os.listdir(PASTA_ALVOS) if f.endswith(".db"))


def apagar_todos_alvos() -> None:
    for f in listar_alvos():
        try:
            os.remove(os.path.join(PASTA_ALVOS, f))
        except OSError:
            pass
        # remove também os arquivos auxiliares do modo WAL, se existirem
        for sufixo in ("-wal", "-shm"):
            aux = os.path.join(PASTA_ALVOS, f + sufixo)
            if os.path.exists(aux):
                os.remove(aux)