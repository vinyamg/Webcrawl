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
import random


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
    # NAME <input name="">
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


def crawler(url, tempo, agent, tor):
    ext = tldextract.extract(url)
    dominio = ext.domain + '.' + ext.suffix
    if os.path.exists(f"alvos/{dominio}.json"):
        print("Esse alvo já foi coletado, use --analyze")
        return
    user_agents = [
        # Windows - Chrome / Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.184 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/121.0.2277.128 Safari/537.36",
        # macOS - Safari / Chrome
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.184 Safari/537.36",
        # Linux - Chrome / Firefox
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.224 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Android - Chrome
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
        # iPhone - Safari / Chrome
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.71 Mobile/15E148 Safari/604.1",
        # iPad
        "Mozilla/5.0 (iPad; CPU OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.7 Mobile/15E148 Safari/604.1",
        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Edge moderno
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36 Edg/122.0.2365.66"
    ]
    proxiesTor = {
        "http": "socks5h://127.0.0.1:9050",
        "https": "socks5h://127.0.0.1:9050"
    }
    if agent:
        headers = {
            "User-Agent": random.choice(user_agents)
        }
    else:
        headers = {
            "User-Agent": "webCrawler/Tool"
        }

    urls_completa = []
    dados_gerais = {}
    if tor:
        try:
            response = requests.get(
                "https://httpbin.org/ip",
                proxies=proxiesTor,
                timeout=10
            )
            print("Proxy funcionando!")
            print("IP:", response.json())
        except Exception as e:
            print("Proxy não está funcionando")
            print("Considere ativar o serviço tor: 'sudo service tor start'")
            return
    print(f"[+] Alvo: {url}\n")
    def requisicao(url_path):
        if url_path.startswith(url):
            try:
                if tor:
                    requisicao = requests.get(url_path, headers=headers, proxies=proxiesTor, timeout=5)
                else:
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
                elif requisicao.status_code == 429:
                    print("\nRate Limited excedido, esperando 10s, caso não resolva, considere o -t\n")
                    time.sleep(10)
            except requests.exceptions.Timeout:
                pass
            except requests.exceptions.TooManyRedirects:
                pass
            except requests.exceptions.RequestException as e:
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
    if tor:
        verificacao = requests.get(url, headers=headers, timeout=5, proxies=proxiesTor)
        if verificacao.status_code == 403:
            print("🚫 Bloqueado (provável Tor)")
            return
        elif verificacao.status_code == 503:
            print("⚠️ Possível bloqueio / proteção")
            return
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
                sys.stdout.write(f"\rRestantes: {len(vezes)}/{total} > {i.ljust(180)}")
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

