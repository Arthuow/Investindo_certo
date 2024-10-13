import MetaTrader5 as mt5
import datetime


################# FAZER CONEXÃO COM METATRADER ######################
def inicializando_MetaTrader():
    login = 1016433950
    password = "@Rt20421125"
    server = "ClearInvestimentos-CLEAR"

    # Inicializar o MetaTrader 5
    if not mt5.initialize():
        print("Falha ao inicializar o MetaTrader 5")
        mt5.shutdown()
        return False

    # Fazer login na conta com as credenciais fornecidas
    if not mt5.login(login, password, server):
        print(f"Falha ao fazer login na conta {login}")
        mt5.shutdown()
        return False
    else:
        print(f"Conectado à conta {login}")
        return True
def cotacao_tempo_real(ativo):
    try:
        ativo = ativo.replace(".SA", "")

        cotacao = pesquisar_ativo(ativo)  # Suponho que 'pesquisar_ativo' retorna o valor
        if cotacao is not None and hasattr(cotacao, 'last'):
            return cotacao.last
        else:
            print(f"Erro: Cotação não disponível para o ativo {ativo}.")
            return None  # Ou você pode definir um valor padrão como 0
    except Exception as e:
        print(f"Erro ao obter cotação do ativo {ativo}: {e}")
        return None
def pesquisar_ativo(ativo):
    # Verificar se o ativo está disponível
    ativo_info = mt5.symbol_info(ativo)
    if ativo_info is None:
        print(f"Ativo {ativo} não encontrado, encerrando...")
        return None, None, None, None, None

    if not ativo_info.visible:
        print(f"Ativo {ativo} não está visível. Habilitando...")
        if not mt5.symbol_select(ativo, True):
            print(f"Falha ao habilitar {ativo}, encerrando...")
            return None, None, None, None, None

    # Obter a cotação do ativo
    cotacao = mt5.symbol_info_tick(ativo)
    if cotacao:
        print(f"Símbolo: {ativo}")
        print(f"Bid: {cotacao.bid}")
        print(f"Ask: {cotacao.ask}")
        print(f"Último preço: {cotacao.last}")
        print(f"Data/Hora: {datetime.datetime.fromtimestamp(cotacao.time)}")
        return cotacao.last
    else:
        print(f"Falha ao obter a cotação de {ativo}")
        return None, None, None, None, None

# Agora a chamada deve ser feita assim:
    cotacao_last = pesquisar_ativo(ativo)
    return cotacao_last







