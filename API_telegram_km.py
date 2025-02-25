import telebot
import json
import os

# Substitua pelo seu TOKEN do BotFather
TOKEN = "TOKEN-TOKEN-TOKEN"
bot = telebot.TeleBot(TOKEN)

# Nome do arquivo onde armazenamos os dados dos técnicos
DATABASE_FILE = "tecnicos_km.json"

# Verifica se o arquivo existe, senão cria um vazio
if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, "w") as file:
        json.dump({}, file)

# Função para carregar os dados do arquivo JSON
def carregar_dados():
    with open(DATABASE_FILE, "r") as file:
        return json.load(file)

# Função para salvar os dados no arquivo JSON
def salvar_dados(dados):
    with open(DATABASE_FILE, "w") as file:
        json.dump(dados, file)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚗 Olá! Sou seu bot de controle de quilometragem. Envie `/km 200` para registrar sua rodagem.")

@bot.message_handler(commands=['km'])
def registrar_km(message):
    try:
        dados = carregar_dados()
        tecnico_id = str(message.chat.id)
        km_rodado = int(message.text.split()[1])  # captura o valor enviado (ex: "/km 200")

        if tecnico_id in dados:
            dados[tecnico_id] += km_rodado
        else:
            dados[tecnico_id] = km_rodado

        salvar_dados(dados)                     
                                    #tanque
        km_restante = 360 - dados[tecnico_id]

        if km_restante <= 0:
            dados[tecnico_id] = 0  # reseta após abastecimento
            salvar_dados(dados)
            bot.reply_to(message, "⚠️ Abasteça o veículo! Você atingiu o limite de 360 km.")
        else:
            bot.reply_to(message, f"✅ Rodagem registrada! Você ainda pode rodar {km_restante} km antes do abastecimento.")

    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Comando inválido! Use: `/km 200` para registrar a quilometragem.")
#Created by Paula Sarmanho

bot.polling()
