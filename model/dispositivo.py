class Dispositivo:
    def __init__(self, hostname, serialnumber, fabricante, modelo, cpu, memoriagb,
                 ultimousuario, status, obs, estado, id=None, ignorar_conflito=False):
        self.id = id
        self.hostname = hostname
        self.serialnumber = serialnumber
        self.fabricante = fabricante
        self.modelo = modelo
        self.cpu = cpu
        self.memoriagb = memoriagb
        self.ultimousuario = ultimousuario
        self.status = status
        self.obs = obs
        self.estado = estado
        self.ignorar_conflito = ignorar_conflito