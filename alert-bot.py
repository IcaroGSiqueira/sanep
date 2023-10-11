######################################################################################################################################

import logging
import mysql.connector
import time
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler
from datetime import datetime
import re
import pandas as pd
import matplotlib.pyplot as plt
from telegram import InputFile
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os, csv
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("MYSQL_HOST")
usr = os.getenv("MYSQL_USER")
passw = os.getenv("MYSQL_PASSWORD")
db = os.getenv("MYSQL_DB_NAME")
telegram_token = os.getenv("TELEGRAM_TOKEN")

# Configuração do logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, filename="py_log.log", filemode="w")
logger = logging.getLogger(__name__)

def connect_database():
    # Estabelece uma conexão com o servidor MySQL
    conn = mysql.connector.connect(
        host=host,
        user=usr,
        password=passw,
        database=db
    )
    return conn


# Estados da Conversa
SENSOR, CONDICAO, VALOR = range(3)
EXCLUIR_ALERTA = range(1)

######################################################################################################################################




######################################################################################################################################

def user_exists(user_id, cursor):
    query = "SELECT * FROM telegram_users WHERE code = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    print(result)
    return result is not None


# Função para registrar um novo usuário no banco de dados
def register_user(user_id, cursor):
    query = "INSERT INTO telegram_users (code) VALUES (%s)"
    cursor.execute(query, (user_id,))


# Inicialização do Bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        conn = connect_database()

        # Instancia objetos que podem executar operações como instruções SQL
        cursor = conn.cursor()
        
        if user_exists(user_id, cursor):
            print(f'O {user_id} já está registrado.')
        else:
            register_user(user_id, cursor)
            conn.commit()
            print(f'O {user_id} foi registrado com sucesso.')

        cursor.close()
        conn.close()

        # Acessa o objeto de usuário (user) a partir de uma atualização (update) recebida pelo Bot.
        user = update.message.from_user
        # Essa é uma função ou método disponibilizado pelo objeto context.bot que permite enviar uma mensagem para um chat.
        # chat_id: identificador único para o chat ou destinatário no qual deseja-se enviar a mensagem.
        # update.effective_chat.id é usado para obter o ID do chat e 
        # normalmente representa o chat que desencadeou a atualização ou mensagem atual no bot.
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Olá, {user.first_name}! Bem-vindo ao bot. Escolha o que deseja fazer:\n\n/0 - Visualizar a última coleta de dados\n/1 - Criar alerta\n/2 - Visualizar alertas\n/3 - Excluir alerta")

    except Exception as e:
        logger.error(f"\nErro ao obter dados do MySQL: {e}\n")
        #return "Erro ao obter dados do MySQL."

######################################################################################################################################




######################################################################################################################################

async def barra0(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Estabelece uma conexão com o servidor MySQL
        conn = connect_database()

        # Instancia objetos que podem executar operações como instruções SQL
        cursor = conn.cursor()        
        
        # Executa uma consulta SELECT
        cursor.execute("SELECT CAST(sanep.sensor_data.data AS FLOAT) as Valor, sanep.sensors.name as Origem, sanep.sensor_data.created_at as Data FROM sanep.sensor_data LEFT JOIN sanep.sensors ON sanep.sensor_data.sensor_id = sanep.sensors.id WHERE sanep.sensors.type_id = 1 ORDER BY sanep.sensor_data.created_at DESC LIMIT 1")
        # Retorna os resultados
        temperatura = cursor.fetchall()

        # Executa uma consulta SELECT
        cursor.execute("SELECT CAST(sanep.sensor_data.data AS FLOAT) as Valor, sanep.sensors.name as Origem, sanep.sensor_data.created_at as Data FROM sanep.sensor_data LEFT JOIN sanep.sensors ON sanep.sensor_data.sensor_id = sanep.sensors.id WHERE sanep.sensors.type_id = 2 ORDER BY sanep.sensor_data.created_at DESC LIMIT 1")
        # Retorna os resultados
        umidade = cursor.fetchall()

        # Executa uma consulta SELECT
        cursor.execute("SELECT CAST(sanep.sensor_data.data AS FLOAT) as Valor, sanep.sensors.name as Origem, sanep.sensor_data.created_at as Data FROM sanep.sensor_data LEFT JOIN sanep.sensors ON sanep.sensor_data.sensor_id = sanep.sensors.id WHERE sanep.sensors.type_id = 6 ORDER BY sanep.sensor_data.created_at DESC LIMIT 1")
        # Retorna os resultados
        vento = cursor.fetchall()

        cursor.close()
        conn.close()
        
        print(f"\n{temperatura}\n")
        print(f"\n{umidade}\n")
        print(f"\n{vento}\n")
        
        data_hora_original = str(temperatura[0][2])
        data_hora = datetime.strptime(data_hora_original, ('%Y-%m-%d %H:%M:%S'))
        data_formatada = data_hora.strftime('%d-%m-%Y')
        hora_formatada = data_hora.strftime('%H:%M')
        
        mensagem = f"{data_formatada} às {hora_formatada}\n\nTemperatura: {temperatura[0][0]}°C\nUmidade: {umidade[0][0]}%\nVento: {vento[0][0]} km/h"
        print(mensagem)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{mensagem}")

    except Exception as e:
        logger.error(f"\nErro ao obter dados do MySQL: {e}\n")
        #return "Erro ao obter dados do MySQL."

######################################################################################################################################




######################################################################################################################################

def salva_regra(sensor_sem_barra, condicao_sem_barra, valor_sem_barra):

    sensor_dict = {
        'TEMPERATURA':'2d0ffdf5-928d-4439-85a0-0351b8b7eadc',
        'UMIDADE':'9795f012-4a4b-41fa-b402-6121ef9998be',
        'VENTO':'91094aed-14df-4671-8af9-f40dd1480fed'
    }

    try:
        # Estabelece uma conexão com o servidor MySQL
        conn = connect_database()
        
        # Instancia objetos que podem executar operações como instruções SQL
        cursor = conn.cursor()

        # Define a instrução SQL de inserção
        inserir_dados = "INSERT INTO rules (sensor_id, `condition`, value) VALUES (%s, %s, %s)"

        # Valores a serem inseridos
        dados = (sensor_dict[sensor_sem_barra], condicao_sem_barra, valor_sem_barra)
        
        # Executa a instrução INSERT
        cursor.execute(inserir_dados, dados)
        
        # Confirma a inserção no banco de dados
        conn.commit()
        print("Inserção bem-sucedida!")

    except Exception as e:
        # Em caso de erro, desfazer a operação e exibir uma mensagem de erro
        conn.rollback()
        print(f"\nErro ao gravar dados no MySQL: {e}\n")
        logger.error(f"\nErro ao gravar dados no MySQL: {e}\n")
        #return "Erro ao gravar dados no MySQL."

    finally:
        cursor.close()
        conn.close()


async def barra1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Adicionar alerta para qual sensor?\n\n/TEMPERATURA\n/UMIDADE\n/VENTO")
    return SENSOR


async def receber_sensor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sensor = update.message.text
    if sensor == '/TEMPERATURA' or sensor == '/UMIDADE' or sensor == '/VENTO':
        context.user_data['sensor'] = sensor
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Qual será a condição?\n\n/IGUAL\n/MENOR_QUE\n/MAIOR_QUE")
        return CONDICAO
    else:   
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Desculpe, não entendi esse comando.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Adicionar alerta para qual sensor?\n\n/TEMPERATURA\n/UMIDADE\n/VENTO")
        return SENSOR


async def receber_condicao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    condicao = update.message.text
    if condicao == '/IGUAL' or condicao == '/MENOR_QUE' or condicao == '/MAIOR_QUE':
        context.user_data['condicao'] = condicao
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Digite o valor de referência.\nPor exemplo: /23.")
        return VALOR
    else:   
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Desculpe, não entendi esse comando.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Qual será a condição?\n\n/IGUAL\n/MENOR_QUE\n/MAIOR_QUE")
        return CONDICAO


async def receber_valor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = update.message.text
    if re.match(r'^/\d+', valor):
        sensor = context.user_data['sensor']  # Recupera o sensor da memória do bot
        condicao = context.user_data['condicao']  # Recupera a condição da memória do bot
        
        print(f"{sensor} - {condicao} - {valor}")
        
        sensor_sem_barra = sensor.lstrip('/')
        print(sensor_sem_barra)

        condicao_sem_barra = condicao.lstrip('/')
        print(condicao_sem_barra)

        valor_sem_barra = valor.lstrip('/')
        print(valor_sem_barra)

        salva_regra(sensor_sem_barra, condicao_sem_barra, valor_sem_barra)

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Alerta criado!")
        return ConversationHandler.END # Encerra a conversa
    else:   
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Desculpe, não entendi esse comando.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Digite o valor de referência.\nPor exemplo: /23.")
        return VALOR

######################################################################################################################################




######################################################################################################################################

def save_dataframe_as_pdf(df, pdf_filename, title):
    # Cria um objeto SimpleDocTemplate para o PDF passando o nome do arquivo PDF de destino como argumento.
    # pagesize: define o tamanho da página.
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)

    # Lista para armazenar os elementos a serem adicionados ao PDF
    elements = []

    # columns: fornece acesso aos nomes das colunas (rótulos das colunas) do DataFrame.
    # tolist(): converte o atributo columns em uma lista de strings
    header = df.columns.tolist()

    # Divide o DataFrame em partes para evitar quebras de página no meio de uma tabela
    chunk_size = 30  # Número de linhas por página (ajustar conforme necessário)
    # Cria uma lista chamada chunks que contém partições (fragmentos) do DataFrame df.
    # Esses fragmentos ou partições são criados de forma que cada um contenha no máximo 30 linhas do DataFrame original.
    # range(0, len(df), chunk_size) cria um iterável que gera os índices iniciais de cada fragmento.
    # Ele começa em 0 e avança em incrementos de chunk_size até o comprimento total do DataFrame.
    # df[i:i + chunk_size] é a fatia do DataFrame que corresponde a cada fragmento.
    # O i é o índice inicial e i + chunk_size é o índice final (não inclusivo) da fatia.
    # Isso cria um novo DataFrame que contém um pedaço do DataFrame original, começando no índice i e indo até o índice i + chunk_size.
    chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

    # Estilo para o título da tabela
    title_style = ParagraphStyle(name='TitleStyle', fontSize=12, alignment=1, fontName='Helvetica-Bold', spaceAfter=18)
    title_text = Paragraph(title.upper(), title_style)

    for chunk in chunks:
        table_data = [header] + chunk.values.tolist()
        # Table é usado para criar tabelas em documentos PDF.
        table = Table(table_data, repeatRows=1)

        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), (0.8, 0.8, 0.8)),
            ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), (0.95, 0.95, 0.95)),
            ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),
        ])

        table.setStyle(table_style)
        
        elements.append(title_text)
        elements.append(table)
        elements.append(PageBreak())

    # Constrói o PDF
    doc.build(elements)


async def barra2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Estabelece uma conexão com o servidor MySQL
        conn = connect_database()
        
        # Instancia objetos que podem executar operações como instruções SQL
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, sensor_id, `condition`, value FROM rules")
        lista_original = cursor.fetchall()

        cursor.close()
        conn.close()

        print(f"\n{lista_original}\n")

        sensor_dict = {
            'TEMPERATURA':'2d0ffdf5-928d-4439-85a0-0351b8b7eadc',
            'UMIDADE':'9795f012-4a4b-41fa-b402-6121ef9998be',
            'VENTO':'91094aed-14df-4671-8af9-f40dd1480fed'
        }
        
        # Função para substituir ID por NOME dos sensores
        def substituir_id_nome(item):
            novo_item = list(item)
            if novo_item[1] == sensor_dict['TEMPERATURA']:
                novo_item[1] = 'TEMPERATURA'
            elif novo_item[1] == sensor_dict['UMIDADE']:
                novo_item[1] = 'UMIDADE'
            elif novo_item[1] == sensor_dict['VENTO']:
                novo_item[1] = 'VENTO'
            return tuple(novo_item)

        lista_transformada = [substituir_id_nome(item) for item in lista_original]
        
        # Define os nomes das colunas
        nomes_colunas = ['ID', 'Sensor', 'Condição', 'Valor']

        tabela = pd.DataFrame(lista_transformada, columns=nomes_colunas)

        mensagem = tabela.to_string(index=False)
        print(mensagem)

        save_dataframe_as_pdf(tabela, 'alertas.pdf', 'Tabela de Alertas')

        pdf_path = '/home/icaro/matheus/alertas.pdf'

        # Envia o PDF
        await context.bot.send_document(chat_id=update.effective_chat.id, document=InputFile(open(pdf_path, 'rb')))

    except Exception as e:
        logger.error(f"\nErro ao visualizar alertas: {e}\n")
        #return "Erro ao visualizar alertas."

######################################################################################################################################




######################################################################################################################################

async def barra3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Digite o ID do alerta que deseja excluir.\nPor exemplo: /23.")
    return EXCLUIR_ALERTA


async def excluir_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_delete = update.message.text
    if re.match(r'^/\d+', id_delete):
        print(f"\n{id_delete}\n")
        try:
            # Estabelece uma conexão com o servidor MySQL
            conn = connect_database()
            
            # Instancia objetos que podem executar operações como instruções SQL
            cursor = conn.cursor()

            # Define a instrução SQL de exclusão
            delete_query = "DELETE FROM rules WHERE id = %s"

            id_delete_sem_barra = id_delete.lstrip('/')
            #print(id_delete_sem_barra)
            
            cursor.execute(delete_query, (id_delete_sem_barra,))
        
            # Confirma a exclusão no banco de dados
            conn.commit()

            if cursor.rowcount == 1:
                #print(f"Alerta excluído com sucesso!")
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Alerta excluído!")
                return ConversationHandler.END # Encerra a conversa
            else:
                #print(f"Nenhum alerta com ID = {id_delete} foi encontrado.")
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Nenhum alerta com ID = {id_delete_sem_barra} foi encontrado.")
                return ConversationHandler.END # Encerra a conversa

        except mysql.connector.Error as error:
            #print(f"\nErro ao excluir alerta no MySQL: {error}\n")
            logger.error(f"\nErro ao excluir alerta no MySQL: {error}\n")
            #return "Erro ao excluir alerta no MySQL."

        finally:
            cursor.close()
            conn.close()

    else:   
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Desculpe, não entendi esse comando.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Para excluir um alerta, digite /3 novamente.")
        return ConversationHandler.END # Encerra a conversa

######################################################################################################################################




######################################################################################################################################

async def alerta_regra(context: ContextTypes.DEFAULT_TYPE):
    try:
        # Estabelece uma conexão com o servidor MySQL
        conn = connect_database()
        
        # Instancia objetos que podem executar operações como instruções SQL
        cursor = conn.cursor()

        cursor.execute("SELECT id, sensor_id, `condition`, value FROM rules")
        rows = cursor.fetchall()
        
        # Executa uma consulta SELECT
        cursor.execute("SELECT CAST(sanep.sensor_data.data AS FLOAT) as Valor, sanep.sensors.name as Origem, sanep.sensor_data.created_at as Data FROM sanep.sensor_data LEFT JOIN sanep.sensors ON sanep.sensor_data.sensor_id = sanep.sensors.id WHERE sanep.sensors.type_id = 1 ORDER BY sanep.sensor_data.created_at DESC LIMIT 1")
        # Retorna os resultados
        temperatura = cursor.fetchall()

        # Executa uma consulta SELECT
        cursor.execute("SELECT CAST(sanep.sensor_data.data AS FLOAT) as Valor, sanep.sensors.name as Origem, sanep.sensor_data.created_at as Data FROM sanep.sensor_data LEFT JOIN sanep.sensors ON sanep.sensor_data.sensor_id = sanep.sensors.id WHERE sanep.sensors.type_id = 2 ORDER BY sanep.sensor_data.created_at DESC LIMIT 1")
        # Retorna os resultados
        umidade = cursor.fetchall()

        # Executa uma consulta SELECT
        cursor.execute("SELECT CAST(sanep.sensor_data.data AS FLOAT) as Valor, sanep.sensors.name as Origem, sanep.sensor_data.created_at as Data FROM sanep.sensor_data LEFT JOIN sanep.sensors ON sanep.sensor_data.sensor_id = sanep.sensors.id WHERE sanep.sensors.type_id = 6 ORDER BY sanep.sensor_data.created_at DESC LIMIT 1")
        # Retorna os resultados
        vento = cursor.fetchall()

        cursor.execute("SELECT code FROM telegram_users WHERE active = 1")
        telegram_users = cursor.fetchall()

        cursor.close()
        conn.close()
        
        print(f"\n{rows}\n")
        print(f"\n{temperatura}\n")
        print(f"\n{umidade}\n")
        print(f"\n{vento}\n")
        print(f"\n{telegram_users}\n")

        sensor_dict = {
            '2d0ffdf5-928d-4439-85a0-0351b8b7eadc':'TEMPERATURA',
            '9795f012-4a4b-41fa-b402-6121ef9998be':'UMIDADE',
            '91094aed-14df-4671-8af9-f40dd1480fed':'VENTO'
        }

        for row in rows:
            if temperatura[0][1].upper() == sensor_dict[row[1]]:
                if row[2] == 'IGUAL':
                    if temperatura[0][0] == row[3]:
                        for i in telegram_users:
                            user_id = i[0]
                            #print(f"Alerta acionado!\nTemperatura está igual a {row[3]}°C.")
                            mensagem = f"Alerta acionado!\n\nTemperatura está igual a {row[3]}°C."
                            await context.bot.send_message(chat_id=user_id, text=f"{mensagem}")
                elif row[2] == 'MENOR_QUE':
                    if temperatura[0][0] < row[3]:
                        for i in telegram_users:
                            user_id = i[0]
                            #print(f"Alerta acionado!\nTemperatura está abaixo dos {row[3]}°C.\nTemperatura no momento é de {temperatura[0][0]}°C.")
                            mensagem = f"Alerta acionado!\n\nTemperatura está abaixo dos {row[3]}°C.\nTemperatura no momento é de {temperatura[0][0]}°C."
                            await context.bot.send_message(chat_id=user_id, text=f"{mensagem}")
                elif row[2] == 'MAIOR_QUE':
                    if temperatura[0][0] > row[3]:
                        for i in telegram_users:
                            user_id = i[0]
                            #print(f"Alerta acionado!\nTemperatura está acima dos {row[3]}°C.\nTemperatura no momento é de {temperatura[0][0]}°C.")
                            mensagem = f"Alerta acionado!\n\nTemperatura está acima dos {row[3]}°C.\nTemperatura no momento é de {temperatura[0][0]}°C."
                            await context.bot.send_message(chat_id=user_id, text=f"{mensagem}")

            elif umidade[0][1].upper() == sensor_dict[row[1]]:
                if row[2] == 'IGUAL':
                    if umidade[0][0] == row[3]:
                        for i in telegram_users:
                            user_id = i[0]
                            #print(f"Alerta acionado!\nUmidade está igual a {row[3]}%.")
                            mensagem = f"Alerta acionado!\n\nUmidade está igual a {row[3]}%."
                            await context.bot.send_message(chat_id=user_id, text=f"{mensagem}")
                elif row[2] == 'MENOR_QUE':
                    if umidade[0][0] < row[3]:
                        for i in telegram_users:
                            user_id = i[0]
                            #print(f"Alerta acionado!\nUmidade está abaixo dos {row[3]}%.\nUmidade no momento é de {umidade[0][0]}%.")
                            mensagem = f"Alerta acionado!\n\nUmidade está abaixo dos {row[3]}%.\nUmidade no momento é de {umidade[0][0]}%."
                            await context.bot.send_message(chat_id=user_id, text=f"{mensagem}")
                elif row[2] == 'MAIOR_QUE':
                    if umidade[0][0] > row[3]:
                        for i in telegram_users:
                            user_id = i[0]
                            #print(f"Alerta acionado!\nUmidade está acima dos {row[3]}%.\nUmidade no momento é de {umidade[0][0]}%.")
                            mensagem = f"Alerta acionado!\n\nUmidade está acima dos {row[3]}%.\nUmidade no momento é de {umidade[0][0]}%."
                            await context.bot.send_message(chat_id=user_id, text=f"{mensagem}")

            elif vento[0][1].upper() == sensor_dict[row[1]]:
                if row[2] == 'IGUAL':
                    if vento[0][0] == row[3]:
                        for i in telegram_users:
                            user_id = i[0]
                            #print(f"Alerta acionado!\nVento está igual a {row[3]} km/h.")
                            mensagem = f"Alerta acionado!\n\nVento está igual a {row[3]} km/h."
                            await context.bot.send_message(chat_id=user_id, text=f"{mensagem}")
                elif row[2] == 'MENOR_QUE':
                    if vento[0][0] < row[3]:
                        for i in telegram_users:
                            user_id = i[0]
                            #print(f"Alerta acionado!\nVento está abaixo dos {row[3]} km/h.\nVento no momento é de {vento[0][0]} km/h.")
                            mensagem = f"Alerta acionado!\n\nVento está abaixo dos {row[3]} km/h.\nVento no momento é de {vento[0][0]} km/h."
                            await context.bot.send_message(chat_id=user_id, text=f"{mensagem}")
                elif row[2] == 'MAIOR_QUE':
                    if vento[0][0] > row[3]:
                        for i in telegram_users:
                            user_id = i[0]
                            #print(f"Alerta acionado!\nVento está acima dos {row[3]} km/h.\nVento no momento é de {vento[0][0]} km/h.")
                            mensagem = f"Alerta acionado!\n\nVento está acima dos {row[3]} km/h.\nVento no momento é de {vento[0][0]} km/h."
                            await context.bot.send_message(chat_id=user_id, text=f"{mensagem}")

    except Exception as e:
        logger.error(f"\nErro ao verificar o alerta: {e}\n")
        #return "Erro ao verificar o alerta."

######################################################################################################################################




######################################################################################################################################

if __name__ == '__main__':
    # Isso cria uma instância de um construtor de aplicativos.
    # O ApplicationBuilder é uma classe usada para configurar e construir o bot.
    # build(): finaliza a configuração do aplicativo e cria uma instância do bot com base nas configurações definidas anteriormente. 
    application = ApplicationBuilder().token(telegram_token).build()
    
    # Adicionando o comando "/start"
    # Registra um manipulador (handler) para o comando /start.
    # CommandHandler("start", start) especifica que quando o comando /start for enviado, a função start será chamada para processá-lo.
    application.add_handler(CommandHandler('start', start))
    
    # Adicionando uma opção no Menu
    # Permite definir manipuladores (handlers) para diferentes tipos de mensagens recebidas pelo Bot.
    application.add_handler(CommandHandler('0', barra0))

    # O Filtro significa que o manipulador será acionado apenas quando o bot 
    # receber mensagens de texto normais dos usuários e também mensagens que sejam comandos de bot.
    application.add_handler(ConversationHandler(entry_points=[CommandHandler('1', barra1)],
                                                states={SENSOR: [MessageHandler(filters.TEXT & filters.COMMAND, receber_sensor)],
                                                        CONDICAO: [MessageHandler(filters.TEXT & filters.COMMAND, receber_condicao)],
                                                        VALOR: [MessageHandler(filters.TEXT & filters.COMMAND, receber_valor)],},
                                                fallbacks=[],
                                                ))
    
    application.add_handler(CommandHandler('2', barra2))
    
    
    application.add_handler(ConversationHandler(entry_points=[CommandHandler('3', barra3)],
                                                states={EXCLUIR_ALERTA: [MessageHandler(filters.TEXT & filters.COMMAND, excluir_alerta)],},
                                                fallbacks=[],
                                                ))
    
    # Configuração do envio de alertas a cada 10 minutos
    # Permite agendar tarefas (jobs) para serem executadas em horários específicos ou periodicamente no bot.
    # Executa uma função de envio de alerta de forma repetitiva (em intervalos regulares).
    # first=0: Hora em que o trabalho deve ser executado. Este parâmetro será interpretado dependendo do seu tipo.
    # int ou float será interpretado como “daqui a alguns segundos” em que o trabalho deverá ser executado. 
    application.job_queue.run_repeating(alerta_regra, interval=600, first=0)
    
    # Inicia a verificação periódica do servidor do Telegram em busca de novas atualizações.
    # Quando uma nova atualização é recebida, ela será processada e encaminhada para os manipuladores.
    application.run_polling()

######################################################################################################################################