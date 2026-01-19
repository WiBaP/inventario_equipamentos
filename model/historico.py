class Historico:
    def __init__(self, dispositivo_id, campo_alterado, valor_anterior, valor_novo, 
                 usuario_acao, id=None, data_evento=None):
        self.id = id
        self.dispositivo_id = dispositivo_id
        self.campo_alterado = campo_alterado
        self.valor_anterior = valor_anterior
        self.valor_novo = valor_novo
        self.data_evento = data_evento
        self.usuario_acao = usuario_acao