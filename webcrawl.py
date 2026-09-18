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
            crawler(url, args.t, args.random_agent, args.tor, max_paginas=args.max_paginas, resume=args.resume)

        if args.analyze:
            from funcionalidades.shell_analyse import shell
            shell()

    except KeyboardInterrupt:
        print("Program interrupted...")
    except Exception as e:
        print(f"Erro inesperado: {e}")


if __name__ == "__main__":
    main()