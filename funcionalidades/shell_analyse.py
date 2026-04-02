import json
import tldextract
from .funcoes import js, subdomain, gets, posts, help, social, arquivoTipo
import os
def shell():
    while True:
        try:
            arquivos = os.listdir("alvos")
            if not arquivos:
                print("Não possui alvos salvos, enumere um alvo primeiro com --url")
                break
            print("\nAlvos:\n")
            for i, item in enumerate(arquivos):
                print(f"{i}. {item[:-5]}")
            print("\n88. Apagar os alvos | 99. Sair")
            alvo = int(input("\nQual é o seu alvo?: "))
            if alvo == 99:
                break
            if alvo == 88:
                for i in arquivos:
                    os.remove(f"alvos/{i}")
                print("[+] Alvos apagados!")
                break
            with open(f"alvos/{arquivos[alvo]}", "rb") as arq:
                dados = json.load(arq)
        except Exception as e:
            print(f"Algo deu errado, alvo inválido, comando incorreto, etc\n\n{e}")
            break

        chaves = list(dados.keys())
        alvo = chaves[0]
        ext = tldextract.extract(alvo)
        subdominio = ext.subdomain
        dominio = ext.domain + '.' + ext.suffix
        print("Digite 'help' para ajuda\n")
        while True:
            try:
                comando = input("$> ").lower()
                if comando == "posts":
                    posts(chaves, dados)
                elif comando == "gets":
                    gets(chaves, dados, alvo)
                elif comando == "subdomains":
                    subdomain(chaves, dados, dominio)
                elif comando.startswith("js"):
                    js(chaves, dados, dominio, comando, alvo)
                elif comando == "social":
                    social(chaves, dados)
                elif comando.startswith("ext"):
                    arquivoTipo(chaves, dados, comando)
                elif comando == "exit":
                    print("bye bye")
                    break
                elif comando == "help":
                    help()
                else:
                    print("Comando inválido.")
            except Exception as e:
                print(e)
                print("Algo deu errado.")


