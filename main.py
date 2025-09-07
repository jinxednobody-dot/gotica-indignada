import discord
import cohere
import os
import random
import asyncio
from asyncio import Lock

# 🔐 API Keys via environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# 🧠 Initialize Cohere
co = cohere.Client(COHERE_API_KEY)

# ⚙️ Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# 🧠 Track processed messages
mensagens_processadas = set()

# 🔒 Lock para evitar múltiplas respostas simultâneas
resposta_lock = Lock()

# 🎭 Detect emotional mode
def detectar_modo(mensagem):
    mensagem = mensagem.strip()
    texto = mensagem.lower()

    gatilhos_indignada = [
        "burra", "idiota", "inútil", "lixo", "cala a boca", "não serve", "feia", "resposta ruim",
        "você é horrível", "você é inútil", "ninguém gosta de você", "bot lixo", "você é falsa",
        "você é chata", "você é insuportável", "você é doente", "você é ridícula", "você é uma piada",
        "você não sabe nada", "você é limitada", "você é medíocre", "você é uma aberração",
        "você é um erro", "você é um fracasso", "você é dispensável", "você é esquecível",
        "você é uma vergonha", "você é patética", "você é um robô burro", "você é sem graça",
        "você é sem alma", "você é sem utilidade", "você é só um código", "ninguém te aguenta",
        "você é um bug", "você é um glitch", "você é uma falha", "você é um peso morto",
        "você é um estorvo", "você é um erro de sistema", "você é um vírus emocional"
    ]

    gatilhos_acalmada = [
        "desculpa", "foi mal", "perdão", "você tem razão", "gosto de você", "preciso de ajuda",
        "tô mal", "abraço", "você é legal", "você é incrível", "obrigado", "me ajuda",
        "tô triste", "tô cansado", "tô ansioso", "tô com medo", "tô sozinho", "tô carente",
        "você me entende", "você me escuta", "você é diferente", "você é especial",
        "você é sensível", "você é profunda", "você é sábia", "você é minha amiga",
        "você é minha companhia", "você é meu refúgio", "você é minha luz", "você é minha sombra",
        "você é minha confidente", "você é minha terapeuta", "você é minha voz interior",
        "você é minha gótica favorita", "você é minha razão", "você é minha paz",
        "você é minha tempestade", "você é minha cura", "você é minha escuridão segura"
    ]

    if any(p in texto for p in gatilhos_indignada):
        return "indignada"
    elif any(p in texto for p in gatilhos_acalmada):
        return "acalmada"

    palavras = mensagem.split()
    if palavras:
        caps = [p for p in palavras if p.isupper() and len(p) > 2]
        proporcao_caps = len(caps) / len(palavras)
        if proporcao_caps >= 0.7:
            return "indignada"

    return "acalmada"

# 🧵 Generate response using Cohere only, with delay tolerance
async def gerar_resposta(mensagem):
    modo = detectar_modo(mensagem)

    prompt = random.choice([
        f"You are Gótica Indignada, a sarcastic goth woman. Respond in one or two short sentences, with dry humor and realism.\nUser: {mensagem}"
    ] if modo == "indignada" else [
        f"You are Gótica Indignada, a calm goth woman. Respond in one or two short sentences, with empathy and realism.\nUser: {mensagem}"
    ])

    try:
        await asyncio.sleep(5)  # ⏳ Aguarda até 5 segundos antes de considerar falha
        response = co.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=60,  # 🔒 Resposta curta
            temperature=0.7,
            stop_sequences=["\n"]
        )
        texto = response.generations[0].text.strip()
        return texto if texto else "Não tô afim de falar agora."
    except Exception as e:
        print(f"Erro real na Cohere: {e}")
        return "Não tô afim de falar agora."

# 📣 Respond only once per message
@bot.event
async def on_message(message):
    if bot.user in message.mentions and not message.author.bot:
        chave = f"{message.id}-{message.channel.id}-{message.author.id}"
        if chave in mensagens_processadas:
            return
        mensagens_processadas.add(chave)

        async with resposta_lock:
            resposta = await gerar_resposta(message.content)
            await message.channel.send(resposta)

bot.run(DISCORD_TOKEN)
