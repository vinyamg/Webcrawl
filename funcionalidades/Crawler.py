import requests
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
import warnings
import sys
import time
import tldextract
import random
from collections import deque
from urllib.parse import urlparse, urlunparse, urljoin

from . import db
from .config import (
    USER_AGENTS,
    DEFAULT_USER_AGENT,
    PROXIES_TOR,
    CAPTCHA_KEYWORDS,
    PROTECTION_KEYWORDS,
    BLOCK_KEYWORDS,
    STATUS_CODES_BLOQUEIO,
    EXTENSOES_INUTEIS,
    ACCEPT_PADRAO,
    ACCEPT_LANGUAGE_PADRAO,
    ACCEPT_ENCODING_PADRAO,
)

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def coleta(html):
    soup = BeautifulSoup(html, "html.parser")

    hrefs = {link.get("href") for link in soup.find_all("a") if link.get("href")}

    srcs = {script.get("src") for script in soup.find_all("script") if script.get("src")}

    inline_scripts = {
        script.string.strip()
        for script in soup.find_all("script")
        if script.string and script.string.strip()
    }

    css_links = {link.get("href") for link in soup.find_all("link") if link.get("href")}

    names = {
        input_tag.get("name")
        for input_tag in soup.find_all("input")
        if input_tag.get("name")
    }

    return {
        "links": list(hrefs),
        "scripts_externos": list(srcs),
        "scripts_inline": list(inline_scripts),
        "css": list(css_links),
        "post": list(names),
    }


def mesmo_dominio(url_path, url_base):
    try:
        return urlparse(url_path).netloc == urlparse(url_base).netloc
    except ValueError:
        return False


def dominio_base(url_path):
    ext = tldextract.extract(url_path)
    return f"{ext.domain}.{ext.suffix}"


def e_arquivo_js(url_path):
    return url_path.lower().split("?", 1)[0].endswith((".js", ".mjs"))


def cabecalhos_extra(url_path, referer):
    documento = not e_arquivo_js(url_path)
    extras = {
        "Accept": ACCEPT_PADRAO if documento else "*/*",
        "Sec-Fetch-Dest": "document" if documento else "script",
        "Sec-Fetch-Mode": "navigate" if documento else "no-cors",
        "Sec-Fetch-Site": "same-origin" if referer else "none",
    }
    if documento:
        extras["Upgrade-Insecure-Requests"] = "1"
        extras["Sec-Fetch-User"] = "?1"
    if referer:
        extras["Referer"] = referer
    return extras


def detectar_bloqueio(html, status_code):
    html_lower = html.lower()
    resultado = {"bloqueio": False, "captcha": False, "tipos": [], "codigo": status_code}

    for palavra in CAPTCHA_KEYWORDS:
        if palavra in html_lower:
            resultado["captcha"] = True
            resultado["tipos"].append(f"captcha:{palavra}")

    for palavra in PROTECTION_KEYWORDS:
        if palavra in html_lower:
            resultado["bloqueio"] = True
            resultado["tipos"].append(palavra)

    for palavra in BLOCK_KEYWORDS:
        if palavra in html_lower:
            resultado["bloqueio"] = True
            resultado["tipos"].append(palavra)

    return resultado


def crawler(url, tempo, agent, tor, max_paginas=None, tentativas_bloqueio=3, resume=False, cookie=None, js_quota=5, incluir_dominios=None):
    ext = tldextract.extract(url)
    dominio = ext.domain + "." + ext.suffix

    dominios_permitidos_js = {dominio}
    if incluir_dominios:
        dominios_permitidos_js |= {d.strip().lower() for d in incluir_dominios.split(",") if d.strip()}

    ja_existe = db.existe_alvo(dominio)
    if ja_existe and not resume:
        print("Esse alvo já foi coletado. Use --analyze para revisar, ou --resume para continuar a coleta.")
        return

    conn = db.conectar(dominio)
    db.gravar_metadata(conn, url, dominio)

    user_agent = random.choice(USER_AGENTS) if agent else DEFAULT_USER_AGENT

    sessao = requests.Session()
    sessao.headers.update(
        {
            "User-Agent": user_agent,
            "Accept-Language": ACCEPT_LANGUAGE_PADRAO,
            "Accept-Encoding": ACCEPT_ENCODING_PADRAO,
            "Connection": "keep-alive",
        }
    )
    if cookie:
        for par in cookie.split(";"):
            if "=" in par:
                nome, valor = par.split("=", 1)
                sessao.cookies.set(nome.strip(), valor.strip())
    if tor:
        sessao.proxies.update(PROXIES_TOR)

    if tor:
        try:
            resp_teste = sessao.get("https://httpbin.org/ip", timeout=10)
            print("Proxy funcionando!")
            print("IP:", resp_teste.json())
        except Exception:
            print("Proxy não está funcionando")
            print("Considere ativar o serviço tor: 'sudo service tor start'")
            conn.close()
            return

        verificacao = sessao.get(url, timeout=5)
        bloqueio = detectar_bloqueio(verificacao.text, verificacao.status_code)
        if bloqueio["bloqueio"] or bloqueio["captcha"]:
            print("O servidor está bloqueando o proxy")
            conn.close()
            return

    print(f"[+] Alvo: {url}\n")

    fila_js = deque()
    fila_normal = deque()
    visitadas = set()
    enfileiradas = set()

    def normalizar(url_bruta):
        parsed = urlparse(url_bruta)
        return urlunparse(parsed._replace(query=""))

    def enfileirar_normalizada(url_bruta, referer):
        normalizada = normalizar(url_bruta)
        if normalizada in visitadas or normalizada in enfileiradas:
            return

        e_js = e_arquivo_js(normalizada)
        if e_js:
            if dominio_base(normalizada) not in dominios_permitidos_js:
                return
        else:
            if not mesmo_dominio(normalizada, url):
                return
            if normalizada.lower().endswith(EXTENSOES_INUTEIS):
                return

        enfileiradas.add(normalizada)
        (fila_js if e_js else fila_normal).append((normalizada, referer))

    if ja_existe and resume:
        visitadas = db.urls_coletadas(conn)
        for pendente, referer in db.frontier_pendente(conn):
            enfileirar_normalizada(pendente, referer)
        print(
            f"[+] Retomando: {len(visitadas)} páginas já coletadas, "
            f"{len(fila_js)} JS e {len(fila_normal)} normal pendentes na fila\n"
        )

    def fazer_requisicao_http(url_path, referer):
        extras = cabecalhos_extra(url_path, referer)
        return sessao.get(url_path, headers=extras, timeout=5)

    def resolver_absolutas(lista, url_pagina_atual):
        resolvidas = []
        for item in lista:
            if not isinstance(item, str) or not item.strip():
                continue
            if item.startswith("javascript:") or item.startswith("#"):
                continue
            resolvidas.append(urljoin(url_pagina_atual, item))
        return resolvidas

    def enfileirar(lista, referer):
        for item in lista:
            if item.startswith("mailto:"):
                continue
            enfileirar_normalizada(item, referer)

    def requisicao(url_path, referer=None):
        if e_arquivo_js(url_path):
            if dominio_base(url_path) not in dominios_permitidos_js:
                return
        elif not mesmo_dominio(url_path, url):
            return

        if db.pagina_ja_coletada(conn, url_path):
            return

        for tentativa in range(tentativas_bloqueio):
            try:
                resp = fazer_requisicao_http(url_path, referer)
            except requests.exceptions.Timeout:
                return
            except requests.exceptions.TooManyRedirects:
                return
            except requests.exceptions.RequestException:
                return

            if resp.status_code == 200:
                texto = resp.text
                if e_arquivo_js(url_path):
                    db.salvar_pagina_js(conn, url_path, texto)
                else:
                    bruto = coleta(texto)
                    resultado = {
                        "links": resolver_absolutas(bruto["links"], url_path),
                        "scripts_externos": resolver_absolutas(bruto["scripts_externos"], url_path),
                        "scripts_inline": bruto["scripts_inline"],
                        "css": resolver_absolutas(bruto["css"], url_path),
                        "post": bruto["post"],
                    }
                    db.salvar_pagina_html(conn, url_path, resultado)
                    for lista in (resultado["links"], resultado["css"], resultado["scripts_externos"]):
                        enfileirar(lista, url_path)
                if tempo:
                    time.sleep(tempo)
                return

            bloqueio = detectar_bloqueio(resp.text, resp.status_code)
            bloqueado = (bloqueio["bloqueio"] or bloqueio["captcha"]) and resp.status_code in STATUS_CODES_BLOQUEIO

            if bloqueado:
                tipo_msg = "Bloqueio" if bloqueio["bloqueio"] else "Captcha"
                espera = 10 * (tentativa + 1)
                print(f"\n[+] {tipo_msg} detectado: heurísticas {bloqueio['tipos']} | tentativa {tentativa + 1}/{tentativas_bloqueio}, esperando {espera}s\n")
                time.sleep(espera)
                continue

            return

        print(f"[!] Desisti de {url_path} após {tentativas_bloqueio} tentativas (seguindo bloqueado)")

    inicio = time.time()
    quota_ilimitada = js_quota is None or js_quota <= 0
    js_consecutivos = 0

    def deve_forcar_normal():
        if not fila_normal:
            return False
        if not fila_js:
            return True
        if quota_ilimitada:
            return False
        return js_consecutivos >= js_quota

    if not (ja_existe and resume and url in visitadas):
        requisicao(url)
    visitadas.add(url)

    try:
        while fila_js or fila_normal:
            if max_paginas is not None and len(visitadas) >= max_paginas:
                print(f"\n[+] Limite de {max_paginas} páginas atingido, encerrando coleta")
                break

            if deve_forcar_normal():
                url_normalizada, referer_atual = fila_normal.popleft()
                js_consecutivos = 0
            else:
                url_normalizada, referer_atual = fila_js.popleft()
                js_consecutivos += 1

            if url_normalizada in visitadas:
                continue

            requisicao(url_normalizada, referer_atual)
            visitadas.add(url_normalizada)
            quota_label = "∞" if quota_ilimitada else str(js_quota)
            sys.stdout.write(
                f"\rNa fila: {len(fila_js)} JS / {len(fila_normal)} normal | "
                f"Visitadas: {len(visitadas)} | seq JS: {js_consecutivos}/{quota_label}\x1b[K"
            )
            sys.stdout.flush()

        duracao = round((time.time() - inicio) / 60, 2)
        print(f"\nCrawler completo - {db.contar_paginas(conn)} páginas salvas em alvos/{dominio}.db - Tempo: {duracao}/min")

    except KeyboardInterrupt:
        duracao = round((time.time() - inicio) / 60, 2)
        print(f"\nCrawler interrompido - {db.contar_paginas(conn)} páginas já estão salvas em alvos/{dominio}.db - Tempo: {duracao}/min")
        print("Use --resume na próxima execução para continuar de onde parou.")

    finally:
        conn.close()
        sessao.close()