from . import db
from .funcoes import js, subdomain, gets, posts, help, social, arquivoTipo, extrair_modificador_tudo

def escolher_alvo():
    arquivos = db.listar_alvos()
    if not arquivos:
        print("Não possui alvos salvos, enumere um alvo primeiro com --url")
        return None

    print("\nAlvos:\n")
    for i, item in enumerate(arquivos):
        print(f"{i}. {item[:-3]}")  # remove sufixo .db
    print("\n88. Apagar os alvos | 99. Sair")

    try:
        escolha = int(input("\nQual é o seu alvo?: "))
    except ValueError:
        print("Entrada inválida, digite um número.")
        return "retry"

    if escolha == 99:
        return None

    if escolha == 88:
        confirmacao = input("Tem certeza que quer apagar TODOS os alvos? (s/n): ").strip().lower()
        if confirmacao == "s":
            db.apagar_todos_alvos()
            print("[+] Alvos apagados!")
        else:
            print("Cancelado.")
        return "retry"

    if escolha < 0 or escolha >= len(arquivos):
        print("Índice de alvo inválido.")
        return "retry"

    dominio_arquivo = arquivos[escolha][:-3]

    try:
        conn = db.conectar(dominio_arquivo)
    except Exception as e:
        print(f"Não foi possível abrir esse alvo: {e}")
        return "retry"

    if db.contar_paginas(conn) == 0:
        print("Esse alvo não tem dados coletados.")
        conn.close()
        return "retry"

    meta = db.obter_metadata(conn)
    alvo = meta.get("alvo", "")
    dominio = meta.get("dominio", dominio_arquivo)

    return conn, alvo, dominio


def shell():
    while True:
        resultado = escolher_alvo()
        if resultado is None:
            break
        if resultado == "retry":
            continue

        conn, alvo, dominio = resultado
        print(f"[+] {db.contar_paginas(conn)} páginas carregadas de {dominio}")
        print("Digite 'help' para ajuda\n")

        while True:
            try:
                comando_bruto = input("$> ").lower().strip()
                if comando_bruto == "js" or comando_bruto.startswith("js "):
                    js(conn, dominio, comando_bruto, alvo)
                    continue

                partes = comando_bruto.split()
                partes, mostrar_tudo = extrair_modificador_tudo(partes)
                comando = partes[0] if partes else ""

                if comando == "posts":
                    posts(conn, mostrar_tudo)
                elif comando == "gets":
                    gets(conn, alvo, mostrar_tudo)
                elif comando == "subdomains":
                    subdomain(conn, dominio, mostrar_tudo)
                elif comando == "social":
                    social(conn, mostrar_tudo)
                elif comando == "ext":
                    extensao = " ".join(partes[1:])
                    arquivoTipo(conn, extensao, mostrar_tudo)
                elif comando == "exit":
                    print("bye bye")
                    conn.close()
                    return
                elif comando == "help":
                    help()
                elif comando == "voltar":
                    conn.close()
                    break
                else:
                    print("Comando inválido. Digite 'help' para ver as opções, ou 'voltar' para trocar de alvo.")
            except KeyboardInterrupt:
                print("\nSaindo...")
                conn.close()
                return
            except Exception as e:
                print(f"Algo deu errado: {e}")