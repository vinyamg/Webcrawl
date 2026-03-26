import requests
from bs4 import BeautifulSoup
import json
from bs4 import XMLParsedAsHTMLWarning
import warnings
import sys
import time
import tldextract
import os
from urllib.parse import urlparse, urlunparse


def coleta(html):
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    soup = BeautifulSoup(html, 'html.parser')

    # Links <a>
    hrefs = {
        link.get('href')
        for link in soup.find_all('a')
        if link.get('href')
    }

    # Scripts externos <script src="">
    srcs = {
        script.get('src')
        for script in soup.find_all('script')
        if script.get('src')
    }

    # Scripts inline <script>...</script>
    inline_scripts = {
        script.string.strip()
        for script in soup.find_all('script')
        if script.string and script.string.strip()
    }

    # CSS <link href="">
    css_links = {
        link.get('href')
        for link in soup.find_all('link')
        if link.get('href')
    }
    names = {
        input_tag.get('name')
        for input_tag in soup.find_all('input')
        if input_tag.get('name')
    }

    return {
        "links": list(hrefs),
        "scripts_externos": list(srcs),
        "scripts_inline": list(inline_scripts),
        "css": list(css_links),
        "post": list(names)
    }


def crawler(url, tempo):
    ext = tldextract.extract(url)
    dominio = ext.domain + '.' + ext.suffix
    if os.path.exists(f"alvos/{dominio}.json"):
        print("Esse alvo já foi coletado, use --analyze")
        return
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; itel W6501) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Mobile Safari/537.36"
    }
    urls_completa = []
    dados_gerais = {}

    def requisicao(url_path):
        if url_path.startswith(url):
            try:
                requisicao = requests.get(url_path, headers=headers, timeout=5)
                if requisicao.status_code == 200:
                    requisicao = requisicao.text
                    if url_path.endswith(".js") or url_path.endswith(".mjs"):
                        dados_gerais[url_path] = requisicao
                    else:
                        resultado = coleta(requisicao)
                        dados_gerais[url_path] = resultado
                        for i in [resultado["links"], resultado["css"], resultado["scripts_externos"]]:
                            divisao(i)
                            time.sleep(tempo)
            except requests.exceptions.Timeout:
                pass
        else:
            pass

    def divisao(dados):  # codigo onde divide url e diretorio
        for dado in dados:
            if isinstance(dado, str):
                if dado.startswith("/") or dado.startswith("//") or dado.startswith('./'):
                    if dado.startswith("//") or dado.startswith('./'):
                        urls_completa.append(url + dado[1:])
                    else:
                        urls_completa.append(url + dado)
                elif dado.startswith("https") or dado.startswith("http"):
                    urls_completa.append(dado)
                else:
                    pass
            else:
                pass
        urls_completa[:] = list(dict.fromkeys(urls_completa))
    inicio = time.time()
    requisicao(url) #principal
    urls_visitadas = [url]
    vezes = []
    extensoes_inuteis = (
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".bmp", ".tiff", ".heic",
        ".mp4", ".mkv", ".mov", ".avi", ".webm", ".mp3", ".wav", ".ogg", ".flac",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar", ".7z", ".tar", ".gz", ".iso",
        ".woff", ".woff2", ".ttf", ".otf", ".eot",
        ".exe", ".bin", ".apk", ".dmg", ".msi", ".dll", ".css", ".xml"
    )
    try:
        for i in urls_completa:
            parsed = urlparse(i)
            i = urlunparse(parsed._replace(query=""))
            if i in urls_visitadas or not i.startswith(url) or i.endswith(extensoes_inuteis):
                vezes.append(i)
                pass
            else:
                vezes.append(i)
                total = len(urls_completa)
                requisicao(i)
                urls_visitadas.append(i)
                sys.stdout.write(f"\rRestantes: {len(vezes)}/{total} > {i.ljust(200)}")
                sys.stdout.flush()

        with open(f"alvos/{dominio}.json", "w", encoding="utf-8") as f:
            json.dump(dados_gerais, f, ensure_ascii=False, indent=4)
            final = time.time()
            tempo = round((final - inicio) / 60, 2)
            print(f"\nCrawler completo, informações salvas - Tempo: {tempo}/min")
    except KeyboardInterrupt:
        with open(f"alvos/{dominio}.json", "w", encoding="utf-8") as f:
            json.dump(dados_gerais, f, ensure_ascii=False, indent=4)
            final = time.time()
            tempo = round((final - inicio) / 60, 2)
            print(f"\nCrawler terminado, informações salvas - Tempo: {tempo}/min")

