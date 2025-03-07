import telebot
import json
import os
import re
import unicodedata
from datetime import datetime

TOKEN = "token"
bot = telebot.TeleBot(TOKEN)

DATABASE_FILE = "tecnicos_km.json"
LOJAS_FILE = "lojas.json"

if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, "w", encoding="utf-8") as file:
        json.dump({}, file, indent=4, ensure_ascii=False)

if not os.path.exists(LOJAS_FILE):
    with open(LOJAS_FILE, "w", encoding="utf-8") as file:
        json.dump({"lojas": []}, file, indent=4, ensure_ascii=False)

def carregar_dados():
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}

def salvar_dados(dados):
    with open(DATABASE_FILE, "w", encoding="utf-8") as file:
        json.dump(dados, file, indent=4, ensure_ascii=False)

def carregar_lojas():
    try:
        with open(LOJAS_FILE, "r", encoding="utf-8") as file:
            dados_lojas = json.load(file)
            return dados_lojas.get("lojas", [])
    except Exception:
        return []

def salvar_lojas(lojas):
    with open(LOJAS_FILE, "w", encoding="utf-8") as file:
        json.dump({"lojas": lojas}, file, indent=4, ensure_ascii=False)

def normalizar_nome(nome):
    nome_normalizado = nome.strip().lower()
    nome_normalizado = unicodedata.normalize('NFD', nome_normalizado).encode('ascii', 'ignore').decode('ascii')
    nome_normalizado = re.sub(r'\s+', ' ', nome_normalizado)
    return nome_normalizado

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚗 Olá! Sou seu bot de controle de quilometragem.\n"
                          "Use `/cadastrar Nome` para se registrar.\n"
                          "Use `/loja NomeDaLoja 200.5` para registrar quilometragem.\n"
                          "Use `/abastecer` para zerar a quilometragem.\n"
                          "Use `/consultar` para ver seus km registrados.\n"
                          "Use `/historico` para ver seu histórico de registros.\n")
                          #"Use `/cadloja NomeDaLoja` para cadastrar uma nova loja.\n"#

@bot.message_handler(commands=['cadloja'])
def cadastrar_loja(message):
    try:
        partes = message.text.split(maxsplit=1)
        if len(partes) < 2:
            bot.reply_to(message, "❌ Comando inválido! Use: `/cadloja Nome da Loja`")
            return

        nome_loja = partes[1].strip('"')
        nome_loja_normalizado = normalizar_nome(nome_loja)

        lojas = carregar_lojas()

        if nome_loja_normalizado in [normalizar_nome(loja) for loja in lojas]:
            bot.reply_to(message, f"❌ A loja '{nome_loja}' já está cadastrada.")
            return

        lojas.append(nome_loja)
        salvar_lojas(lojas)

        bot.reply_to(message, f"✅ Loja '{nome_loja}' cadastrada com sucesso!")
    except Exception as e:
        bot.reply_to(message, "❌ Ocorreu um erro ao cadastrar a loja.")
        print(f"Erro no cadastro de loja: {e}")

@bot.message_handler(commands=['loja'])
def registrar_km_loja(message):
    try:
        dados = carregar_dados()
        lojas = carregar_lojas()
        tecnico_id = str(message.chat.id)

        if tecnico_id not in dados:
            bot.reply_to(message, "❌ Você precisa se cadastrar primeiro! Use: `/cadastrar Seu Nome`")
            return

        partes = message.text.split(maxsplit=1)
        if len(partes) < 2:
            bot.reply_to(message, "❌ Comando inválido! Use: `/loja NomeDaLoja 200.5`")
            return

        args = partes[1].rsplit(maxsplit=1)
        if len(args) != 2:
            bot.reply_to(message, "❌ Formato incorreto! Use: `/loja Nome da Loja 200.5`")
            return

        nome_loja_input, valor_str = args
        nome_loja_input = nome_loja_input.strip('"')

        try:
            km_rodado = float(valor_str.replace(",", "."))
        except ValueError:
            bot.reply_to(message, "❌ Valor inválido! Use números com . ou ,")
            return

        if km_rodado <= 0:
            bot.reply_to(message, "❌ O valor da quilometragem deve ser maior que zero.")
            return

        nome_loja_normalizado = normalizar_nome(nome_loja_input)
        nome_loja_formatado = None

        for loja in lojas:
            if nome_loja_normalizado == normalizar_nome(loja):
                nome_loja_formatado = loja
                break

        if not nome_loja_formatado:
            bot.reply_to(message, f"❌ A loja '{nome_loja_input}' não foi encontrada. Use `/cadloja` para cadastrá-la.")
            return

        nome_tecnico = dados[tecnico_id]["nome"]

        dados[tecnico_id].setdefault("km", 0)
        dados[tecnico_id].setdefault("historico", [])

        dados[tecnico_id]["km"] += km_rodado

        registro = {
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "km": km_rodado,
            "loja": nome_loja_formatado
        }
        dados[tecnico_id]["historico"].append(registro)
        salvar_dados(dados)

        limite = dados[tecnico_id].get("limite", 360)
        km_restante = limite - dados[tecnico_id]["km"]

        resposta = f"🚗 {nome_tecnico}, rodagem registrada para a loja '{nome_loja_formatado}'!\n"
        resposta += f"📊 Quilometragem adicionada: {km_rodado:.2f} km\n"
        resposta += f"📉 Quilometragem restante: {km_restante:.2f} km\n"

        if km_restante <= 0:
            resposta += "⚠️ Abasteça o veículo! Você atingiu o limite de km.\n"
        elif km_restante <= 40:
            resposta += "🚨 **Atenção!** Você está com menos de 40 km restantes. Planeje o abastecimento.\n"

        bot.reply_to(message, resposta)

    except Exception as e:
        bot.reply_to(message, "❌ Ocorreu um erro ao registrar a quilometragem.")
        print(f"Erro no registro de km: {e}")

@bot.message_handler(commands=['consultar'])
def consultar_km(message):
    dados = carregar_dados()
    tecnico_id = str(message.chat.id)

    if tecnico_id not in dados:
        bot.reply_to(message, "❌ Você precisa se cadastrar primeiro! Use: `/cadastrar Seu Nome`")
        return

    nome_tecnico = dados[tecnico_id]["nome"]
    km_atual = dados[tecnico_id].get("km", 0)
    limite = dados[tecnico_id].get("limite", 360)
    km_restante = limite - km_atual

    resposta = f"📋 {nome_tecnico}, aqui estão seus dados:\n"
    resposta += f"🚗 Quilometragem atual: {km_atual:.2f} km\n"
    resposta += f"📉 Quilometragem restante: {km_restante:.2f} km\n"

    if km_restante <= 0:
        resposta += "⚠️ Abasteça o veículo! Você atingiu o limite de km.\n"
    elif km_restante <= 40:
        resposta += "🚨 **Atenção!** Você está com menos de 40 km restantes. Planeje o abastecimento.\n"

    bot.reply_to(message, resposta)

@bot.message_handler(commands=['historico'])
def ver_historico(message):
    try:
        dados = carregar_dados()
        tecnico_id = str(message.chat.id)

        if tecnico_id not in dados:
            bot.reply_to(message, "❌ Você precisa se cadastrar primeiro! Use: `/cadastrar Seu Nome`")
            return

        historico = dados[tecnico_id].get("historico", [])

        if not historico:
            bot.reply_to(message, "📌 Você ainda não tem registros de quilometragem.")
            return

        resposta = "📜 Histórico de quilometragem:\n"
        for reg in historico:
            if reg["loja"] == "⛽ ABASTECIMENTO":
                resposta += f"📅 {reg['data']} - {reg['loja']}\n"
            else:
                resposta += f"📅 {reg['data']} - 🚗 {reg['km']} km na loja {reg['loja']}\n"

        bot.reply_to(message, resposta)
    except Exception as e:
        bot.reply_to(message, "❌ Ocorreu um erro ao exibir o histórico.")
        print(f"Erro no histórico: {e}")

@bot.message_handler(commands=['abastecer'])
def abastecer(message):
    try:
        dados = carregar_dados()
        tecnico_id = str(message.chat.id)

        if tecnico_id not in dados:
            bot.reply_to(message, "❌ Você precisa se cadastrar primeiro! Use: `/cadastrar Seu Nome`")
            return

        nome_tecnico = dados[tecnico_id]["nome"]
        historico = dados[tecnico_id].get("historico", [])

        registros_lojas = [reg for reg in historico if reg["loja"] != "⛽ ABASTECIMENTO"]
        ultimo_abastecimento = next((reg for reg in reversed(historico) if reg["loja"] == "⛽ ABASTECIMENTO"), None)

        resposta = "📋 Relatório de lojas visitadas desde o último abastecimento:\n"
        if ultimo_abastecimento:
            resposta += f"📅 Último abastecimento: {ultimo_abastecimento['data']}\n\n"

        if registros_lojas:
            total_km = 0
            for reg in registros_lojas:
                resposta += f"🏪 {reg['loja']}: {reg['km']} km\n"
                total_km += reg['km']
            resposta += f"📊 Total percorrido: {total_km:.2f} km\n\n"
        else:
            resposta += "📌 Nenhuma loja foi registrada desde o último abastecimento.\n\n"

        dados[tecnico_id]["km"] = 0
        dados[tecnico_id]["historico"] = []

        registro = {
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "km": 0,
            "loja": "⛽ ABASTECIMENTO"
        }
        dados[tecnico_id]["historico"].append(registro)
        salvar_dados(dados)

        resposta += "⛽ Quilometragem zerada com sucesso! O histórico foi resetado."
        bot.reply_to(message, resposta)
    except Exception as e:
        bot.reply_to(message, "❌ Ocorreu um erro ao zerar a quilometragem.")
        print(f"Erro no abastecimento: {e}")

bot.polling()
