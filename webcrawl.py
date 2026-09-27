import argparse
import os
from urllib.parse import urlparse

from funcionalidades.Crawler import crawler


def url_valida(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def main():
    parser = argparse.ArgumentParser(description="webCrawler - ferramenta de coleta e análise de superfície de ataque")
    parser.add_argument("--url", help="Url do alvo (precisa incluir http:// ou https://)", type=str)
    parser.add_argument("--analyze", action="store_true", help="Analisa os dados já coletados")
    parser.add_argument("--random-agent", action="store_true", help="User agent aleatório")
    parser.add_argument("--tor", action="store_true", help="Usa proxy tor")
    parser.add_argument("-t", type=int, default=0, help="Tempo entre as requisições em segundos (padrão: 0)")
    parser.add_argument("--max-paginas", type=int, default=None, help="Limite máximo de páginas a coletar (padrão: sem limite)")
    parser.add_argument("--resume", action="store_true", help="Retoma uma coleta interrompida a partir dos dados já salvos")
    parser.add_argument("--cookie", type=str, default=None, help="Cookie a enviar nas requisições (ex: 'session=abc123; outro=xyz')")
    parser.add_argument("--js-quota", type=int, default=5, help="Quantos .js seguidos priorizar antes de forçar 1 página normal (0 = prioridade estrita, sem limite)")
    parser.add_argument("--incluir-dominios", type=str, default=None, help="Domínios de terceiro (separados por vírgula) a tratar como parte do alvo, para permitir buscar .js hospedado neles (ex: 'vtexassets.com,myshopify.com')")
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

            os.system("cls" if os.name == "nt" else "clear")
            crawler(url, args.t, args.random_agent, args.tor, max_paginas=args.max_paginas, resume=args.resume, cookie=args.cookie, js_quota=args.js_quota, incluir_dominios=args.incluir_dominios)

        if args.analyze:
            from funcionalidades.shell_analyse import shell
            shell()

    except KeyboardInterrupt:
        print("Program interrupted...")
    except Exception as e:
        print(f"Erro inesperado: {e}")


if __name__ == "__main__":
    main()