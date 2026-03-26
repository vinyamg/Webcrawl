from colorama import Fore
import re
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from urllib.parse import urlparse


class sensive:
    tokens_header = r'token:.*'
    token_json = r'"token":"[^"]+"'
    token_acess = r'"access_token": "[^"]+"'
    authorization = r'Authorization:.*'
    twitter_token = r'[1-9][0-9]+-[0-9a-zA-Z]{40}'
    facebook_token = r'EAACEdEose0cBA[0-9A-Za-z]+'
    google_api = r'AIza[0-9A-Za-z-_]{35}'
    google_oauth = r'[0-9a-zA-Z-_]{24}'
    github_token = r'^ghp_[a-zA-Z0-9]{36}$'
    github_oauth = r'^gho_[a-zA-Z0-9]{36}$'
    github_server_acess_token = r'^ghu_[a-zA-Z0-9]{36}$'
    stripe_key_standart = r'sk_live_[0-9a-zA-Z]{24}'
    stripe_key_private = r'rk_live_[0-9a-zA-Z]{99}'
    openai_user_api = r'sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}'
    paypal = r'access_token,production$[0-9a-z]{161[0-9a,]{32}'
    patterns = {
        #"token_header": r'token:.*',
        "token_json": r'"token":"[^"]+"',
        "access_token": r'"access_token": "[^"]+"',
        #"authorization": r'Authorization:.*',
        "twitter_token": r'[1-9][0-9]+-[0-9a-zA-Z]{40}',
        "facebook_token": r'EAACEdEose0cBA[0-9A-Za-z]+',
        "google_api": r'AIza[0-9A-Za-z-_]{35}',
        "google_oauth": r'([A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,})',
        "github_token": r'^ghp_[a-zA-Z0-9]{36}$',
        "github_oauth": r'^gho_[a-zA-Z0-9]{36}$',
        "github_server_access_token": r'^ghu_[a-zA-Z0-9]{36}$',
        "stripe_key_standard": r'sk_live_[0-9a-zA-Z]{24}',
        "stripe_key_private": r'rk_live_[0-9a-zA-Z]{99}',
        "openai_api_key": r'sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}',
        "paypal_token": r'access_token,production\$[0-9a-z]{161}[0-9a-z]{32}'
    }


def social(chaves, dados):
    encontrados = set()
    for url in chaves:
        if not url.endswith(".js") or not url.endswith(".mjs"):
            links = dados[url]["links"]
            for redes in links:
                if "www.facebook.com" in redes or "www.pinterest.com" in redes or "www.youtube.com/c/" in redes or "twitter.com" in redes:
                    encontrados.add(redes)
    for i in encontrados:
        print(f"[+] {i}")
def help():
    print("Comandos válidos:\n")
    print("gets - Mostra todos os endpoints com parametros GET")
    print("Posts - Mostra todos os endpoints com parametros POST")
    print("subdomains - Mostra todos os subdominios descobertos")
    print("social - Mostra todas as redes sociais encontradas")
    print("js <comando>\n  - search")
    print()
def subdomain(chaves, dados, dominio):
    encontrados = set()  # <-- agora é global

    for url in chaves:
        if not (url.endswith(".js") or url.endswith(".mjs")):
            continue

        links = dados[url]["links"]

        for subdominio in links:
            parsed = urlparse(subdominio)
            base = f"{parsed.scheme}://{parsed.netloc}"

            if re.search(fr"\.{dominio}$", parsed.netloc):
                encontrados.add(base)

    for item in encontrados:
        print(f"- {item}")
def gets(chaves, dados, alvo):
    validos = set()
    for url in chaves:
        if not (url.endswith(".js") or url.endswith(".mjs")):
            links = dados[url]["links"]
            for parametros in links:
                if parametros and "?" in parametros and parametros.startswith(alvo):
                    validos.add(parametros)
    for i in validos:
        print(f"- {i}")
def posts(chaves, dados):
    for url in chaves:
        if not (url.endswith(".js") or url.endswith(".mjs")):
            parametros = dados[url]["post"]
            if parametros:
                print(url)
                print(f"{parametros}\n")

def js(chaves, dados, dominio, comando, alvo):
    def codigo_js():
        codigo_final = ""
        for url in tqdm(chaves, desc="Especionando código"):
            if url.endswith(".js") or url.endswith(".mjs"):
                codigo_final += dados[url] + "\n"
            else:
               codigo_final += "".join(i + "\n" for i in dados[url]["scripts_inline"])
        return codigo_final

    def endpoints(valores):
        urls = []
        paths = []
        for i in valores:
            if (i.startswith("https") or i.startswith("http")) and len(i) > 7:
                urls.append(i)
            elif (i.startswith("/") or i.startswith("//") or i.startswith("./") or i.startswith("\\")) and len(i) > 3 and not i.startswith(r"\u"):
                paths.append(i)
            else:
                pass
        return list(set(urls)), list(set(paths))
    def tokens(valores):
        for dados in tqdm(valores, desc="Analisando em busca de tokens"):
            for nome, regex in sensive.patterns.items():
                matches = re.findall(regex, dados)
                if matches:
                    for m in matches:
                        print(f"[+] {nome}: {m}")

    def mostrarDados(info, tipo):
        def tipos(valor):
            if "api" in valor or "admin" in valor or "account" in valor or "login" in valor or "supabase.co" in valor or "firebase" in valor or "firestore" in valor or "amazonaws.com" in valor:
                return Fore.YELLOW + valor + Fore.RESET
            if "?" in valor or "googleapis.com" in valor:
                return Fore.BLUE + valor + Fore.RESET
            else:
                return valor

        fora_escopo = []
        escopo = []

        instrucoes = {
            "branco": "Branco: Informação",
            "azul": Fore.BLUE + "Azul: Informação baixa" + Fore.RESET,
            "amarelo": Fore.YELLOW + "Amarelo: Superficie de ataque" + Fore.RESET,
            "vermelho": Fore.RED + "Vermelho: informação grave!!" + Fore.RESET
        }
        print(instrucoes["branco"] + "\n" + instrucoes["azul"] + "\n" + instrucoes["amarelo"] + "\n" + instrucoes[
            "vermelho"] + "\n")
        if tipo == 1:  # tipo 1 = Urls
            for i in info:
                if dominio in i:
                    tipo = tipos(i)
                    escopo.append(tipo)
                else:
                    fora_escopo.append(i)
            print("No escopo:\n")
            for i in escopo:
                print(f"[+] {i}")
            print("\nFora do escopo:\n")
            for i in fora_escopo:
                print(f"[+] {i}")
        else:
            for i in info:
                tipo = tipos(i)
                print(f"[+] {tipo}")
    codigo = codigo_js()
    acao = comando[3:]
    if acao == "search":
        regex = r'"(.*?)"'
        regex2 = r"'(.*?)'"
        valoresAspasDuplas = re.findall(regex, codigo)
        valoresAspasSimples = re.findall(regex2, codigo)
        print("1. Endpoints 2. Tecnologias 3. Tokens\n99. Sair")
        while True:
            procura = int(input("O que você deseja procurar?: "))
            match (procura):
                case 1:
                    urls, paths = endpoints(valoresAspasDuplas)
                    urls2, paths2 = endpoints(valoresAspasSimples)
                    print("Caminhos encontrados:\n")
                    mostrarDados(paths, 2)
                    mostrarDados(paths2, 2)
                    print("\nurls encontradas:\n")
                    mostrarDados(urls, 1)
                    mostrarDados(urls2, 1)
                case 3:
                    tokens(valoresAspasSimples)
                    tokens(valoresAspasDuplas)
                case 99:
                    print("Saindo...")
                    break
                case _:
                    print("Opção inválida")
    else:
        print(codigo)