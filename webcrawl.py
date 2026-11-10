import argparse
import os
from urllib.parse import urlparse

from funcionalidades.Crawler import crawler

PROXY_ESQUEMAS = ("http", "https", "socks4", "socks4a", "socks5", "socks5h")


def url_valida(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def proxy_valido(proxy: str) -> bool:
    if proxy.lower() == "tor":
        return True
    if "://" not in proxy:
        proxy = "http://" + proxy
    parsed = urlparse(proxy)
    try:
        porta = parsed.port
    except ValueError:
        return False
    return parsed.scheme in PROXY_ESQUEMAS and bool(parsed.hostname) and porta is not None


def main():
    parser = argparse.ArgumentParser(description="webCrawler - ferramenta de coleta e análise de superfície de ataque")
    parser.add_argument("--url", help="Url do alvo (precisa incluir http:// ou https://)", type=str)
    parser.add_argument("--analyze", action="store_true", help="Analisa os dados já coletados")
    parser.add_argument("--random-agent", action="store_true", help="User agent aleatório")
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Proxy a usar nas requisições. Ex: 'http://127.0.0.1:8080', "
             "'socks5h://127.0.0.1:9050', 'http://user:senha@host:3128' "
             "(sem esquema = http). Use 'tor' como atalho para o proxy tor padrão",
    )
    parser.add_argument(
        "--cert",
        type=str,
        default=None,
        help="Caminho de um certificado CA (.pem/.crt) para validar o HTTPS, "
             "útil com proxies que interceptam TLS, como Burp/ZAP (ex: '~/burp-ca.pem')",
    )
    parser.add_argument("-t", type=int, default=0, help="Tempo entre as requisições em segundos (padrão: 0)")
    parser.add_argument("--max-paginas", type=int, default=None, help="Limite máximo de páginas a coletar (padrão: sem limite)")
    parser.add_argument("--resume", action="store_true", help="Retoma uma coleta interrompida a partir dos dados já salvos")
    parser.add_argument("--cookie", type=str, default=None, help="Cookie a enviar nas requisições (ex: 'session=abc123; outro=xyz')")
    parser.add_argument("--js-quota", type=int, default=5, help="Quantos .js seguidos priorizar antes de forçar 1 página normal (0 = prioridade estrita, sem limite)")
    parser.add_argument("--incluir-dominios", type=str, default=None, help="Domínios de terceiro (separados por vírgula) a tratar como parte do alvo, para permitir buscar .js hospedado neles (ex: 'vtexassets.com,myshopify.com')")
    parser.add_argument("--robots-sitemap", action="store_true", help="Busca e coleta caminhos do robots.txt (Disallow/Allow) e URLs do sitemap.xml (inclui sitemap index) do alvo")
    args = parser.parse_args()

    if not args.url and not args.analyze:
        parser.error("Use --url <alvo> para coletar ou --analyze para analisar dados já coletados.")

    if not os.path.exists("alvos"):
        os.mkdir("alvos")

    try:
        if args.url:
            url = args.url.rstrip("/")
            if not url_valida(url):
                print(f"[!] URL inválida: '{args.url}'. Inclua o esquema, ex: https://exemplo.com")
                return

            if args.proxy and not proxy_valido(args.proxy):
                print(f"[!] Proxy inválido: '{args.proxy}'. Use o formato esquema://host:porta, ex: socks5h://127.0.0.1:9050")
                return

            cert = None
            if args.cert:
                cert = os.path.expanduser(args.cert)
                if not os.path.isfile(cert):
                    print(f"[!] Certificado não encontrado: '{args.cert}'")
                    return

            os.system("cls" if os.name == "nt" else "clear")
            crawler(url, args.t, args.random_agent, args.proxy, max_paginas=args.max_paginas, resume=args.resume, cookie=args.cookie, js_quota=args.js_quota, incluir_dominios=args.incluir_dominios, robots_sitemap=args.robots_sitemap, cert=cert)

        if args.analyze:
            from funcionalidades.shell_analyse import shell
            shell()

    except KeyboardInterrupt:
        print("Program interrupted...")
    except Exception as e:
        print(f"Erro inesperado: {e}")


if __name__ == "__main__":
    main()