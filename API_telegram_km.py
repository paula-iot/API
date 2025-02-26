import telebot
import json
import os

# token 
TOKEN = "7698066035:AAEAxYpj7g4Bz9T1dtzWaFgkYdO-oRCajIg"
bot = telebot.TeleBot(TOKEN)

# nome do arquivo onde armazenamos os dados dos técnicos
DATABASE_FILE = "tecnicos_km.json"

# verifica se o arquivo existe, senão cria um vazio
if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, "w") as file:
        json.dump({}, file)

# carregar os dados do arquivo JSON
def carregar_dados():
    with open(DATABASE_FILE, "r") as file:
        return json.load(file)

# salvar os dados no arquivo JSON
def salvar_dados(dados):
    with open(DATABASE_FILE, "w") as file:
        json.dump(dados, file, indent=4)  

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚗 Olá! Sou seu bot de controle de quilometragem.\n"
                          "Use `/cadastrar Nome` para se registrar.\n"
                          "Use `/km 200` para registrar rodagem.\n"
                          "Use `/consultar` para ver seus km registrados.")

@bot.message_handler(commands=['cadastrar']) #cadastrar
def cadastrar_tecnico(message):
    try:
        dados = carregar_dados()
        tecnico_id = str(message.chat.id)
        nome = " ".join(message.text.split()[1:])  # "/cadastrar"

        if not nome:
            bot.reply_to(message, "❌ Erro ao cadastrar. Use: `/cadastrar Seu Nome`")
            return

        dados[tecnico_id] = {"nome": nome, "km": 0}
        salvar_dados(dados)

        bot.reply_to(message, f"✅ Técnico {nome} cadastrado com sucesso!")

    except Exception as e:
        bot.reply_to(message, "❌ Ocorreu um erro ao cadastrar o técnico.")
        print(f"Erro no cadastro: {e}") 

@bot.message_handler(commands=['km']) #registra km
def registrar_km(message):
    try:
        dados = carregar_dados()
        tecnico_id = str(message.chat.id)
        km_rodado = float(message.text.split()[1]) 

        # verifica se o técnico está cadastrado
        if tecnico_id not in dados:
            bot.reply_to(message, "❌ Você precisa se cadastrar primeiro! Use: `/cadastrar Seu Nome`")
            return
        
        if not isinstance(dados[tecnico_id], dict):
            bot.reply_to(message, "❌ Erro nos seus dados! Tente se cadastrar novamente com `/cadastrar Seu Nome`")
            return
    
        nome_tecnico = dados[tecnico_id]["nome"]

        if "km" not in dados[tecnico_id] or not isinstance(dados[tecnico_id]["km"], (int, float)):
            dados[tecnico_id]["km"] = 0.0 

        dados[tecnico_id]["km"] += km_rodado
        salvar_dados(dados)

        km_restante = 360.0 - dados[tecnico_id]["km"]

        if km_restante <= 0:
            dados[tecnico_id]["km"] = 0.0
            salvar_dados(dados)
            bot.reply_to(message, f"⚠️ {nome_tecnico}, abasteça o veículo! Você atingiu 360.00 km.")
        else:
            bot.reply_to(message, f"✅ {nome_tecnico}, rodagem registrada! Você ainda pode rodar {km_restante:.2f} km.")

    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Comando inválido! Use: `/km 200.5` para registrar a quilometragem.")

@bot.message_handler(commands=['consultar'])
def consultar_km(message):
    dados = carregar_dados()
    tecnico_id = str(message.chat.id)

    if tecnico_id in dados:
        nome = dados[tecnico_id]["nome"]
        bot.reply_to(message, f"🔍 {nome}, você já rodou {dados[tecnico_id]['km']} km.")
    else:
        bot.reply_to(message, "⚠️ Você ainda não está cadastrado! Use `/cadastrar Seu Nome` primeiro.")

bot.polling()

#createad by paulasrmn
