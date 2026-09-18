import requests
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
import warnings
import sys
import time
import tldextract
import random
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


def crawler(url, tempo, agent, tor, max_paginas=None, tentativas_bloqueio=3, resume=False):
    ext = tldextract.extract(url)
    dominio = ext.domain + "." + ext.suffix

    ja_existe = db.existe_alvo(dominio)
    if ja_existe and not resume:
        print("Esse alvo já foi coletado. Use --analyze para revisar, ou --resume para continuar a coleta.")
        return

    conn = db.conectar(dominio)
    db.gravar_metadata(conn, url, dominio)

    if agent:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
    else:
        headers = {"User-Agent": DEFAULT_USER_AGENT}

    if tor:
        try:
            resp_teste = requests.get("https://httpbin.org/ip", proxies=PROXIES_TOR, timeout=10)
            print("Proxy funcionando!")
            print("IP:", resp_teste.json())
        except Exception:
            print("Proxy não está funcionando")
            print("Considere ativar o serviço tor: 'sudo service tor start'")
            conn.close()
            return

        verificacao = requests.get(url, headers=headers, timeout=5, proxies=PROXIES_TOR)
        bloqueio = detectar_bloqueio(verificacao.text, verificacao.status_code)
        if bloqueio["bloqueio"] or bloqueio["captcha"]:
            print("O servidor está bloqueando o proxy")
            conn.close()
            return

    print(f"[+] Alvo: {url}\n")

    # --- estado do crawl -----------------------------------------------
    urls_completa = []
    visitadas = set()

    if ja_existe and resume:
        visitadas = db.urls_coletadas(conn)
        pendentes = db.frontier_pendente(conn)
        urls_completa.extend(pendentes)
        print(f"[+] Retomando: {len(visitadas)} páginas já coletadas, {len(pendentes)} pendentes na fila\n")
    # ---------------------------------------------------------------------

    def fazer_requisicao_http(url_path):
        if tor:
            return requests.get(url_path, headers=headers, proxies=PROXIES_TOR, timeout=5)
        return requests.get(url_path, headers=headers, timeout=5)

    def resolver_absolutas(lista, url_pagina_atual):
        resolvidas = []
        for item in lista:
            if not isinstance(item, str) or not item.strip():
                continue
            if item.startswith("javascript:") or item.startswith("#"):
                continue
            resolvidas.append(urljoin(url_pagina_atual, item))
        return resolvidas

    def enfileirar(lista):
        for item in lista:
            if item.startswith("mailto:"):
                continue
            urls_completa.append(item)

    def requisicao(url_path):
        if not mesmo_dominio(url_path, url):
            return
        if db.pagina_ja_coletada(conn, url_path):
            return

        for tentativa in range(tentativas_bloqueio):
            try:
                resp = fazer_requisicao_http(url_path)
            except requests.exceptions.Timeout:
                return
            except requests.exceptions.TooManyRedirects:
                return
            except requests.exceptions.RequestException:
                return

            if resp.status_code == 200:
                texto = resp.text
                if url_path.endswith(".js") or url_path.endswith(".mjs"):
                    db.salvar_pagina_js(conn, url_path, texto)
                else:
                    bruto = coleta(texto)
                    resultado = {
                        "links": resolver_absolutas(bruto["links"], url_path),
                        "scripts_externos": resolver_absolutas(bruto["scripts_externos"], url_path),
                        "scripts_inline": bruto["scripts_inline"],  # não são URLs, não precisam de resolução
                        "css": resolver_absolutas(bruto["css"], url_path),
                        "post": bruto["post"],
                    }
                    db.salvar_pagina_html(conn, url_path, resultado)
                    for lista in (resultado["links"], resultado["css"], resultado["scripts_externos"]):
                        enfileirar(lista)
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

            return  # status não-200 e não identificado como bloqueio: desiste dessa URL

        print(f"[!] Desisti de {url_path} após {tentativas_bloqueio} tentativas (seguindo bloqueado)")

    inicio = time.time()

    if not (ja_existe and resume and url in visitadas):
        requisicao(url)
    visitadas.add(url)

    try:
        indice = 0
        while indice < len(urls_completa):
            if max_paginas is not None and len(visitadas) >= max_paginas:
                print(f"\n[+] Limite de {max_paginas} páginas atingido, encerrando coleta")
                break

            bruta = urls_completa[indice]
            indice += 1

            parsed = urlparse(bruta)
            url_normalizada = urlunparse(parsed._replace(query=""))

            if (
                url_normalizada in visitadas
                or not mesmo_dominio(url_normalizada, url)
                or url_normalizada.lower().endswith(EXTENSOES_INUTEIS)
            ):
                continue

            requisicao(url_normalizada)
            visitadas.add(url_normalizada)
            sys.stdout.write(f"\rDescobertas: {len(urls_completa)} | Visitadas: {len(visitadas)}")
            sys.stdout.flush()

        duracao = round((time.time() - inicio) / 60, 2)
        print(f"\nCrawler completo - {db.contar_paginas(conn)} páginas salvas em alvos/{dominio}.db - Tempo: {duracao}/min")

    except KeyboardInterrupt:
        duracao = round((time.time() - inicio) / 60, 2)
        print(f"\nCrawler interrompido - {db.contar_paginas(conn)} páginas já estão salvas em alvos/{dominio}.db - Tempo: {duracao}/min")
        print("Use --resume na próxima execução para continuar de onde parou.")

    finally:
        conn.close()