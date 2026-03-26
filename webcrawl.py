import argparse
from funcionalidades.Crawler import crawler
import os

parser = argparse.ArgumentParser()
parser.add_argument("--url", help="Yrl do alvo", type=str)
parser.add_argument("--analyze", action="store_true", help="Analisa os dados")
parser.add_argument("-t", type=int, help="Tempo entre as requisições em /s", default=None)
args = parser.parse_args()

try:
    if not args.url and not args.analyze:
        raise 1
    else:
        if args.url:
            url = args.url
            tempo = args.t
            if url.endswith("/"):
                url = url[:-1]
            os.system("cls" if os.name == "nt" else "clear")
            if not tempo:
                tempo = 0
            crawler(url, tempo)
        if args.analyze:
            from funcionalidades.shell_analyse import shell
            shell()

except KeyboardInterrupt:
    print('Program interrupted...')
except BaseException as e:
    print(e)