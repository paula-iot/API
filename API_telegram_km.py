import telebot
import json
import os
from datetime import datetime

# Token do bot
TOKEN = "token-tonken"  #gerado pelo fatherbot
bot = telebot.TeleBot(TOKEN)

# Nome do arquivo onde armazenamos os dados dos técnicos
DATABASE_FILE = "tecnicos_km.json"

# Verifica se o arquivo existe, senão cria um vazio
if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, "w") as file:
        json.dump({}, file)

# Carregar os dados do arquivo JSON
def carregar_dados():
    try:
        with open(DATABASE_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return {}

# Salvar os dados no arquivo JSON
def salvar_dados(dados):
    try:
        with open(DATABASE_FILE, "w") as file:
            json.dump(dados, file, indent=4)
    except Exception as e:
        print(f"Erro ao salvar dados: {e}")

# cmd /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚗 Olá! Sou seu bot de controle de quilometragem.\n"
                          "Use `/cadastrar Nome` para se registrar.\n"
                          "Use `/km 200` para registrar rodagem.\n"
                          "Use `/consultar` para ver seus km registrados.\n"
                          "Use `/historico` para ver seu histórico de registros.")

# cmd /cadastrar
@bot.message_handler(commands=['cadastrar'])
def cadastrar_tecnico(message):
    try:
        dados = carregar_dados()
        tecnico_id = str(message.chat.id)
        nome = " ".join(message.text.split()[1:])  # Pega o nome após o cmd

        if not nome:
            bot.reply_to(message, "❌ Erro ao cadastrar. Use: `/cadastrar Seu Nome`")
            return

        # Verifica se o técnico já está cadastrado
        if tecnico_id in dados:
            bot.reply_to(message, f"⚠️ Você já está cadastrado como {dados[tecnico_id]['nome']}.")
            return

        # Cadastra o técnico
        dados[tecnico_id] = {"nome": nome, "km": 0, "historico": []}  # Inicializa o campo "historico"
        salvar_dados(dados)

        bot.reply_to(message, f"✅ Técnico {nome} cadastrado com sucesso!")

    except Exception as e:
        bot.reply_to(message, "❌ Ocorreu um erro ao cadastrar o técnico.")
        print(f"Erro no cadastro: {e}")

# cmd /km
@bot.message_handler(commands=['km'])
def registrar_km(message):
    try:
        dados = carregar_dados()
        tecnico_id = str(message.chat.id)

        # Verifica se o cmd foi usado corretamente
        if len(message.text.split()) < 2:
            bot.reply_to(message, "❌ Comando inválido! Use: `/km 200.5` para registrar a quilometragem.")
            return

        # Tenta converter o valor para float
        try:
            km_rodado = float(message.text.split()[1])
        except ValueError:
            bot.reply_to(message, "❌ Valor inválido! Use: `/km 200.5` para registrar a quilometragem.")
            return

        # Verifica se o técnico está cadastrado
        if tecnico_id not in dados:
            bot.reply_to(message, "❌ Você precisa se cadastrar primeiro! Use: `/cadastrar Seu Nome`")
            return

        # Pega o nome do técnico salvo
        nome_tecnico = dados[tecnico_id]["nome"]

        # Adiciona os quilômetros corretamente
        dados[tecnico_id]["km"] += km_rodado

        # Adiciona o registro ao histórico
        if "historico" not in dados[tecnico_id]:  # Verifica se o campo "historico" existe
            dados[tecnico_id]["historico"] = []  # Inicializa o campo "historico" se não existir

        registro = {
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "km": km_rodado
        }
        dados[tecnico_id]["historico"].append(registro)

        salvar_dados(dados)

        km_restante = 360.0 - dados[tecnico_id]["km"]

        if km_restante <= 0:
            bot.reply_to(message, f"⚠️ {nome_tecnico}, abasteça o veículo! Você atingiu 360.00 km.")
        else:
            bot.reply_to(message, f"✅ {nome_tecnico}, rodagem registrada! Você ainda pode rodar {km_restante:.2f} km.")

    except Exception as e:
        bot.reply_to(message, "❌ Ocorreu um erro ao registrar a quilometragem.")
        print(f"Erro no registro de km: {e}")

# cmd /consultar
@bot.message_handler(commands=['consultar'])
def consultar_km(message):
    try:
        dados = carregar_dados()
        tecnico_id = str(message.chat.id)

        if tecnico_id in dados:
            nome = dados[tecnico_id]["nome"]
            bot.reply_to(message, f"🔍 {nome}, você já rodou {dados[tecnico_id]['km']} km.")
        else:
            bot.reply_to(message, "⚠️ Você ainda não está cadastrado! Use `/cadastrar Seu Nome` primeiro.")
    except Exception as e:
        bot.reply_to(message, "❌ Ocorreu um erro ao consultar a quilometragem.")
        print(f"Erro na consulta: {e}")

# cmd /historico
@bot.message_handler(commands=['historico'])
def historico_km(message):
    try:
        dados = carregar_dados()
        tecnico_id = str(message.chat.id)

        if tecnico_id in dados:
            nome = dados[tecnico_id]["nome"]
            historico = dados[tecnico_id]["historico"]

            if not historico:
                bot.reply_to(message, f"📜 {nome}, você ainda não registrou nenhuma quilometragem.")
            else:
                resposta = f"📜 Histórico de {nome}:\n"
                for registro in historico:
                    resposta += f"📅 {registro['data']} - {registro['km']} km\n"
                bot.reply_to(message, resposta)
        else:
            bot.reply_to(message, "⚠️ Você ainda não está cadastrado! Use `/cadastrar Seu Nome` primeiro.")
    except Exception as e:
        bot.reply_to(message, "❌ Ocorreu um erro ao consultar o histórico.")
        print(f"Erro no histórico: {e}")

bot.polling()

# Criado por paulasrmn
