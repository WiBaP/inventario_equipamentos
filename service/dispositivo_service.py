import pyodbc
from db.database import get_connection
from model.dispositivo import Dispositivo
import os
from service.historico_service import HistoricoService
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from io import BytesIO
import base64
from reportlab.lib.utils import ImageReader

class DispositivoService:

    PASTA_TERMOS = r"C:\Users\willian.pinho\Desktop\termos"

    MESES = {
    1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
    5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
    9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
    }

    def listar(self):
        query = """
            SELECT id, Hostname, SerialNumber, Fabricante, Modelo, CPU, MemoriaGB,
               UltimoUsuario, Status, OBS, Estado
            FROM dispositivos
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        dispositivos = []
        for r in rows:
            usuario = r.UltimoUsuario
            existe = False

            if usuario:
                caminho = os.path.join(self.PASTA_TERMOS, f"{usuario}.pdf")
                existe = os.path.isfile(caminho)

            dispositivos.append({
                "id": r.id,  # ✅ ADICIONA AQUI!
                "hostname": r.Hostname,
                "serialnumber": r.SerialNumber,
                "fabricante": r.Fabricante,
                "modelo": r.Modelo,
                "cpu": r.CPU,
                "memoriagb": r.MemoriaGB,
                "ultimousuario": usuario,
                "status": r.Status,
                "estado": r.Estado,
                "obs": r.OBS,
                "termo_existe": existe
            })

        return dispositivos

    # -----------------------------
    # INCLUIR
    # -----------------------------
    def incluir(self, dispositivo: Dispositivo, usuario_acao: str):
        query = """
            INSERT INTO dispositivos (
                Hostname, SerialNumber, Fabricante, Modelo, CPU, MemoriaGB,
                UltimoUsuario, Status, OBS, Estado
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        historico_service = HistoricoService()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                dispositivo.hostname,
                dispositivo.serialnumber,
                dispositivo.fabricante,
                dispositivo.modelo,
                dispositivo.cpu,
                dispositivo.memoriagb,
                dispositivo.ultimousuario,
                dispositivo.status,
                dispositivo.obs,
                dispositivo.estado
            ))

            dispositivo_id = cursor.fetchone()[0]
            conn.commit()

            # Histórico de inclusão (1 registro geral)
            historico_service.registrar(
                dispositivo_id=dispositivo_id,
                campo_alterado="INCLUSAO",
                valor_anterior=None,
                valor_novo="Dispositivo criado",
                usuario_acao=usuario_acao
            )

            return True

    # -----------------------------
    # ALTERAR (PELO ID)
    # -----------------------------
    def alterar(self, dispositivo: Dispositivo, usuario_acao: str):
        
        select_query = "SELECT * FROM dispositivos WHERE id = ?"
        update_query = """
            UPDATE dispositivos
            SET hostname = ?, MemoriaGB = ?,
                UltimoUsuario = ?, Status = ?, OBS = ?, Estado = ?
            WHERE id = ?
        """

        historico_service = HistoricoService()

        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. Estado atual
            cursor.execute(select_query, (dispositivo.id,))
            atual = cursor.fetchone()

            if not atual:
                return False

            # 1.1 Verifica se UltimoUsuario está sendo alterado
            if atual.UltimoUsuario != dispositivo.ultimousuario and dispositivo.ultimousuario:
                print(">>> Verificando conflito para usuário:", dispositivo.ultimousuario)
                
                cursor.execute("""
                    SELECT id, Hostname
                    FROM dispositivos
                    WHERE UltimoUsuario = ?
                    AND id <> ?
                    AND Status NOT IN ('Manutenção', 'Descarte')
                """, (dispositivo.ultimousuario, dispositivo.id))

                outro = cursor.fetchone()
                if outro:
                    print(">>> CONFLITO ENCONTRADO")
                    print("ID antigo:", outro[0])
                    print("Hostname antigo:", outro.Hostname)
               
                ignorar_conflito = getattr(dispositivo, "ignorar_conflito", False)

                if outro and not dispositivo.ignorar_conflito:
                    return {
                        "conflito_usuario": True,
                        "id_dispositivo": outro[0],
                        "hostname_atual": outro.Hostname,
                        "memoriagb": atual.MemoriaGB,
                        "estado": atual.Estado
                    }

            # 2. Mapeamento campo -> valor antigo / novo
            campos = {
                "Hostname": (atual.Hostname, dispositivo.hostname),
                "MemoriaGB": (atual.MemoriaGB, dispositivo.memoriagb),
                "UltimoUsuario": (atual.UltimoUsuario, dispositivo.ultimousuario),
                "Status": (atual.Status, dispositivo.status),
                "OBS": (atual.OBS, dispositivo.obs),
                "Estado": (atual.Estado, dispositivo.estado),
            }

            # 3. Registra histórico apenas do que mudou
            for campo, (valor_antigo, valor_novo) in campos.items():
                if valor_antigo != valor_novo:
                    historico_service.registrar(
                        dispositivo_id=dispositivo.id,
                        campo_alterado=campo,
                        valor_anterior=str(valor_antigo),
                        valor_novo=str(valor_novo),
                        usuario_acao=usuario_acao
                    )

            # 4. Atualiza
            cursor.execute(update_query, (
                dispositivo.hostname,
                dispositivo.memoriagb,
                dispositivo.ultimousuario,
                dispositivo.status,
                dispositivo.obs,
                dispositivo.estado,
                dispositivo.id
            ))
            conn.commit()           

            return True

    # -----------------------------
    # DELETAR (PELO HOSTNAME)
    # -----------------------------
    def deletar(self, hostname: str):
        query = "DELETE FROM dispositivos WHERE Hostname = ?"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (hostname,))
            conn.commit()
            return True

    # -----------------------------
    # PESQUISAR POR QUALQUER CAMPO
    # -----------------------------
    def pesquisar(self, termo):
        termo = f"%{termo}%"
        query = """
            SELECT id, Hostname, SerialNumber, Fabricante, Modelo, CPU, MemoriaGB,
                UltimoUsuario, Status, OBS, Estado
            FROM dispositivos
            WHERE Hostname LIKE ?
                OR SerialNumber LIKE ?
                OR Fabricante LIKE ?
                OR Modelo LIKE ?
                OR CPU LIKE ?
                OR MemoriaGB LIKE ?
                OR UltimoUsuario LIKE ?
                OR Status LIKE ?
                OR OBS LIKE ?
                OR Estado LIKE ?
        """

        params = [termo] * 10

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        dispositivos = []
        for r in rows:
            usuario = r.UltimoUsuario
            existe = False

            if usuario:
                caminho = os.path.join(self.PASTA_TERMOS, f"{usuario}.pdf")
                existe = os.path.isfile(caminho)

            dispositivos.append({
                "id": r.id,  # ✅ ADICIONA AQUI!
                "hostname": r.Hostname,
                "serialnumber": r.SerialNumber,
                "fabricante": r.Fabricante,
                "modelo": r.Modelo,
                "cpu": r.CPU,
                "memoriagb": r.MemoriaGB,
                "ultimousuario": usuario,
                "status": r.Status,
                "estado": r.Estado,
                "obs": r.OBS,
                "termo_existe": existe
            })

        return dispositivos
        
    def verificar_usuario_ad(self):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.hostname, d.ultimousuario
                FROM dispositivos d
                INNER JOIN usuarios_ad u
                    ON d.ultimousuario = u.login
                WHERE u.conta_ativa = 0
            """)
            rows = cursor.fetchall()
            resultados = [{"hostname": r[0], "ultimousuario": r[1]} for r in rows]

        return resultados

    # --------------------------
    # CONFIRMAR RETIRADA DO DISPOSITIVO
    # --------------------------
    def confirmar_retirada(self, hostname: str, usuario_acao: str):

        historico_service = HistoricoService()

        with get_connection() as conn:
            cursor = conn.cursor()

            # 1️⃣ Buscar estado atual
            cursor.execute("""
                SELECT id, status, ultimousuario
                FROM dispositivos
                WHERE hostname = ?
            """, (hostname,))
            atual = cursor.fetchone()

            if not atual:
                return {"mensagem": "Dispositivo não encontrado"}

            dispositivo_id = atual.id
            status_antigo = atual.status
            ultimousuario_antigo = atual.ultimousuario

            if not ultimousuario_antigo:
                return {"mensagem": "Nenhum termo de responsabilidade vinculado a este dispositivo"}

            # 2️⃣ Montar caminho do PDF
            termo_path = os.path.join(self.PASTA_TERMOS, f"{ultimousuario_antigo}.pdf")

            if os.path.exists(termo_path):
                try:
                    os.remove(termo_path)
                except PermissionError:
                    return {"mensagem": "Erro ao remover o termo: arquivo em uso"}

            # 3️⃣ REGISTRAR HISTÓRICO
            if status_antigo != "Disponivel":
                historico_service.registrar(
                    dispositivo_id=dispositivo_id,
                    campo_alterado="Status",
                    valor_anterior=str(status_antigo),
                    valor_novo="Disponivel",
                    usuario_acao=usuario_acao
                )

            if ultimousuario_antigo != "":
                historico_service.registrar(
                    dispositivo_id=dispositivo_id,
                    campo_alterado="UltimoUsuario",
                    valor_anterior=str(ultimousuario_antigo),
                    valor_novo="",
                    usuario_acao=usuario_acao
                )

            # 4️⃣ Atualizar dispositivo
            cursor.execute("""
                UPDATE dispositivos
                SET status = 'Disponivel',
                    ultimousuario = ''
                WHERE hostname = ?
            """, (hostname,))

            conn.commit()

        return {
            "mensagem": f"Dispositivo liberado e termo {ultimousuario_antigo}.pdf removido com sucesso"
        }


    # --------------------------
    # Gerar termo
    # --------------------------

    def buscar_usuario_com_cpf(self, usuario: str):
        """Busca dispositivo e CPF do usuário via INNER JOIN"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.*, u.cpf
                FROM dispositivos d
                INNER JOIN usuarios_ad u
                    ON d.ultimousuario = u.login
                WHERE d.ultimousuario = ?
            """, (usuario,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))

    def gerar_termo_pdf_bytes(self, dispositivo, assinatura_base64: str = None) -> BytesIO:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        print(f"🖼️ Assinatura recebida: {assinatura_base64 is not None}")  # ← LOG NOVO
        if assinatura_base64:
            print(f"📏 Tamanho da assinatura: {len(assinatura_base64)} chars")  # ← LOG NOVO
        
        # ... resto do código continua igual
        
        # Extrai dados do dispositivo
        usuario = (dispositivo.get('ultimousuario') or 
                dispositivo.get('UltimoUsuario') or 
                dispositivo.get('ultimo_usuario') or 
                'Usuário não informado')
        
        cpf = dispositivo.get('cpf', '00000000000')
        
        modelo = (dispositivo.get('modelo') or 
                dispositivo.get('Modelo') or 
                'Modelo não informado')
        
        serial = (dispositivo.get('serialnumber') or 
                dispositivo.get('SerialNumber') or 
                dispositivo.get('serial') or 
                dispositivo.get('Serial') or 
                'Serial não informado')
        
        hostname = (dispositivo.get('hostname') or 
                    dispositivo.get('Hostname') or 
                    'Hostname não informado')
        
        # Data formatada com nome do mês em português
        agora = datetime.now()
        dia = agora.day
        mes = DispositivoService.MESES[agora.month]
        ano = agora.year
        data_formatada = f"{dia} de {mes} de {ano}"
        
        # Formata CPF
        cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf
        
        # Posição inicial
        y = 800
        margem_esq = 50
        largura_util = 500
        
        # Título
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(300, y, "TERMO DE RESPONSABILIDADE DE USO")
        y -= 30
        
        # Parágrafo introdutório
        c.setFont("Helvetica", 10)
        texto1 = f"Eu, "
        c.drawString(margem_esq, y, texto1)
        largura_texto1 = c.stringWidth(texto1, "Helvetica", 10)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margem_esq + largura_texto1, y, usuario)
        largura_usuario = c.stringWidth(usuario, "Helvetica-Bold", 10)
        
        c.setFont("Helvetica", 10)
        texto2 = " portador(a) da cédula de identidade CPF: "
        c.drawString(margem_esq + largura_texto1 + largura_usuario, y, texto2)
        largura_texto2 = c.stringWidth(texto2, "Helvetica", 10)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margem_esq + largura_texto1 + largura_usuario + largura_texto2, y, cpf_formatado)
        
        y -= 15
        c.setFont("Helvetica", 10)
        c.drawString(margem_esq, y, 'e domiciliado (a) cidade de São Paulo, estado de SP, na qualidade de funcionário(a) da empresa')
        y -= 12
        c.drawString(margem_esq, y, 'Veste Estilo S.A., inscrita no CNPJ sob o nº 49.669.856/0001-43 ("VESTE"), recebo desta, neste ato,')
        y -= 12
        c.drawString(margem_esq, y, 'o equipamento a seguir identificado ("Equipamento"):')
        
        y -= 20
        
        # Informações do equipamento em negrito
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margem_esq + 10, y, f"Equipamento: Notebook")
        y -= 15
        c.drawString(margem_esq + 10, y, f"Modelo: {modelo}")
        y -= 15
        c.drawString(margem_esq + 10, y, f"Número de série: {serial}")
        y -= 15
        c.drawString(margem_esq + 10, y, f"Hostname: {hostname}")
        y -= 15
        c.drawString(margem_esq + 10, y, "Acessórios: CARREGADOR")
        
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(margem_esq, y, "Assumindo o compromisso de, a partir desta data:")
        
        y -= 15
        compromissos = [
            "Utilizar o Equipamento única e exclusivamente para execução de serviços à VESTE, em decorrência do",
            "contrato de trabalho mantido com esta;",
            "",
            "Não armazenar no Equipamento qualquer conteúdo ilícito, inapropriado, arquivos pessoais ou que não tenha",
            "relação com os serviços a serem executados;",
            "",
            "Não acessar, através do Equipamento, qualquer conteúdo ilícito ou inapropriado, ou utilizar o Equipamento",
            "em qualquer atividade ilícita;",
            "",
            "Não alterar, burlar ou desativar as configurações originais do Equipamento e, em especial, as configurações",
            "de segurança;",
            "",
            "Não instalar ou utilizar arquivos que não estejam adequadamente licenciados;",
            "",
            "Zelar pela guarda e conservação do Equipamento, comunicando à VESTE, imediatamente, qualquer dano ou",
            "falha no Equipamento;",
            "",
            "Não ceder, emprestar ou transferir o Equipamento a terceiro, ainda que este seja funcionário da VESTE;",
            "",
            "Não efetuar a troca do Equipamento entre funcionários da VESTE;",
            "",
            "Não personalizar ou alterar a aparência do Equipamento, tais como através da inserção de fotos ou adesivos;"
        ]
        
        for linha in compromissos:
            if linha == "":
                y -= 8
            else:
                c.drawString(margem_esq + 5, y, f"•  {linha}")
                y -= 12
        
        # Nova página se necessário
        if y < 100:
            c.showPage()
            y = 800
            c.setFont("Helvetica", 10)
        
        # Continua compromissos
        compromissos2 = [
            "Lavrar boletim de ocorrência em caso de perda ou extravio do Equipamento, incluídas as hipóteses de roubo",
            "e furto e apresentar uma cópia do referido boletim ao departamento Jurídico da VESTE, para apuração e",
            "adoção das medidas pertinentes;",
            "",
            "Entregar o Equipamento à VESTE, nas mesmas condições em que recebido, ressalvado o desgaste decorrente",
            "de seu uso normal, ao término do contrato de trabalho, e/ou sempre que solicitado pela VESTE, observado um",
            "prazo máximo para devolução de até 24 (vinte e quatro) horas corridas, caso não esteja de posse do",
            "Equipamento no momento da solicitação ou do encerramento do Contrato.",
            "",
            "Ressarcir à VESTE:"
        ]
        
        for linha in compromissos2:
            if linha == "":
                y -= 8
            else:
                c.drawString(margem_esq + 5, y, f"•  {linha}")
                y -= 12
        
        # Valores de ressarcimento
        valores = [
            "em caso de perda, extravio e/ou não devolução do equipamento em até 24 horas corridas, quando da",
            "rescisão do contrato de trabalho o valor de R$ 5.000,00 (Cinco Mil Reais) para o caso de notebooks Windows;",
            "",
            "em caso de perda, extravio e/ou não devolução do equipamento em até 24 horas corridas, quando da",
            "rescisão do contrato de trabalho o valor de R$ 30.000,00 (Trinta Mil Reais) para o caso de MACBOOKS ou",
            "IMAC ambos da marca Apple.",
            "",
            "em caso de dano por uso indevido do Equipamento, o valor de R$ 1.300,00 (Mil e Trezentos Reais) para o",
            "caso de notebooks Windows;",
            "",
            "em caso de dano por uso indevido do Equipamento, o valor de R$ 5.000,00 (Cinco Mil Reais) para o caso de",
            "MACBOOKS ou IMAC ambos da marca Apple;"
        ]
        
        for linha in valores:
            if y < 50:
                c.showPage()
                y = 800
                c.setFont("Helvetica", 10)
            
            if linha == "":
                y -= 8
            else:
                c.drawString(margem_esq + 20, y, f"o    {linha}")
                y -= 12
        
        # Nova página para finalização
        c.showPage()
        y = 800
        c.setFont("Helvetica", 10)
        
        finalizacao = [
            "Para tanto, AUTORIZO, desde já, o desconto do referido valor em minha folha de pagamento, na ocorrência",
            "de uma das situações aqui previstas.",
            "",
            "Por fim, declaro ter ciência de que todas as informações compartilhadas e/ou armazenadas no Equipamento",
            "são e se manterão de propriedade da VESTE, de modo que o Equipamento deverá ser devolvido à VESTE,",
            "quando solicitado por esta, ou ao final do contrato de trabalho, com todas as informações que nele tiverem",
            "sido compartilhadas ou armazenadas durante o contrato de trabalho, vedada a exclusão de tais informações,",
            "em qualquer hipótese, salvo se autorizado por escrito pela VESTE.",
            "",
            "Após ler o conteúdo deste instrumento e tomar conhecimento de todos os seus termos e disposições, estou",
            "ciente e de acordo com as responsabilidades ora assumidas.",
        ]
        
        for linha in finalizacao:
            if linha == "":
                y -= 15
            else:
                c.drawString(margem_esq, y, linha)
                y -= 12
        
        y -= 30
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margem_esq, y, f"São Paulo, {data_formatada}.")
        
        y -= 40
        
            # Adicionar assinatura digital se fornecida
        if assinatura_base64:
            try:
                print("🖼️ Tentando adicionar assinatura ao PDF...")
                
                # Decodificar base64 e criar imagem
                assinatura_bytes = base64.b64decode(assinatura_base64)
                print(f"✅ Base64 decodificado: {len(assinatura_bytes)} bytes")
                
                assinatura_img = BytesIO(assinatura_bytes)
                
                # MUDANÇA AQUI: usar ImageReader
                img_reader = ImageReader(assinatura_img)
                
                # Inserir imagem da assinatura no PDF
                c.drawImage(img_reader, margem_esq, y - 60, width=200, height=50, preserveAspectRatio=True, mask='auto')
                print("✅ Assinatura adicionada ao PDF com sucesso!")
                y -= 70
            except Exception as e:
                print(f"❌ Erro ao adicionar assinatura: {e}")
                import traceback
                traceback.print_exc()
                y -= 20
        else:
            print("⚠️ Nenhuma assinatura fornecida")
            y -= 20
        
        c.drawString(margem_esq, y, "_" * 50)
        y -= 15
        c.drawString(margem_esq, y, usuario)
        
        c.showPage()
        c.save()
        buffer.seek(0)
        
        return buffer

    def buscar_por_usuario(self, usuario: str):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM dispositivos WHERE ultimousuario = ?",
                (usuario,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        
    def salvar_termo_pdf(self, usuario: str, assinatura_base64: str):
        """Gera e salva o PDF na pasta de termos"""
        
        # Buscar dados do usuário e dispositivo
        dispositivo = self.buscar_usuario_com_cpf(usuario)
        
        if not dispositivo:
            return None
        
        # Gerar PDF
        pdf_buffer = self.gerar_termo_pdf_bytes(dispositivo, assinatura_base64)
        
        # Criar pasta se não existir
        os.makedirs(self.PASTA_TERMOS, exist_ok=True)
        
        # Nome do arquivo
        nome_arquivo = f"{usuario}.pdf"
        caminho_completo = os.path.join(self.PASTA_TERMOS, nome_arquivo)
        
        # Salvar arquivo
        with open(caminho_completo, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        return {
            "arquivo": nome_arquivo,
            "caminho": caminho_completo,
            "usuario": usuario
        }
    
