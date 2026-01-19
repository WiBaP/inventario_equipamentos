from db.database import get_connection


class HistoricoService:
    
    def registrar(self, dispositivo_id, campo_alterado, valor_anterior, valor_novo, usuario_acao):
        """Registra uma alteração no histórico"""
        query = """
            INSERT INTO historico_dispositivos 
            (dispositivo_id, campo_alterado, valor_anterior, valor_novo, usuario_acao)
            VALUES (?, ?, ?, ?, ?)
        """
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                dispositivo_id,
                campo_alterado,
                valor_anterior,
                valor_novo,
                usuario_acao
            ))
            conn.commit()
            return True
    
    def listar_por_dispositivo(self, dispositivo_id):
        """Lista todo o histórico de um dispositivo específico"""
        query = """
            SELECT id, dispositivo_id, campo_alterado, valor_anterior, 
                   valor_novo, data_evento, usuario_acao
            FROM historico_dispositivos
            WHERE dispositivo_id = ?
            ORDER BY data_evento DESC
        """
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (dispositivo_id,))
            rows = cursor.fetchall()
            
            historico = []
            for r in rows:
                historico.append({
                    "id": r.id,
                    "dispositivo_id": r.dispositivo_id,
                    "campo_alterado": r.campo_alterado,
                    "valor_anterior": r.valor_anterior,
                    "valor_novo": r.valor_novo,
                    "data_evento": str(r.data_evento),
                    "usuario_acao": r.usuario_acao
                })
            
            return historico
    
    def listar_todos(self):
        """Lista todo o histórico de todos os dispositivos"""
        query = """
            SELECT id, dispositivo_id, campo_alterado, valor_anterior, 
                   valor_novo, data_evento, usuario_acao
            FROM historico_dispositivos
            ORDER BY data_evento DESC
        """
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            historico = []
            for r in rows:
                historico.append({
                    "id": r.id,
                    "dispositivo_id": r.dispositivo_id,
                    "campo_alterado": r.campo_alterado,
                    "valor_anterior": r.valor_anterior,
                    "valor_novo": r.valor_novo,
                    "data_evento": str(r.data_evento),
                    "usuario_acao": r.usuario_acao
                })
            
            return historico