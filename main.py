import discord
import cohere
import openai
import anthropic
import os
import random
from asyncio import Lock

# 🔐 API Keys via environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# 🧠 Initialize APIs
co = cohere.Client(COHERE_API_KEY)
openai.api_key = OPENAI_API_KEY
anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# ⚙️ Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# 🧠 Memory per user
memoria = {}

# 🧠 Track processed messages
mensagens_processadas = set()

# 🔁 IA pool
ia_disponiveis = ["cohere", "openai", "claude"]

# 🔒 Lock para evitar múltiplas respostas simultâneas
resposta_lock = Lock()

# 🎭 Detect emotional mode with expanded triggers + caps lock
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

    # CAPS LOCK como grito
    palavras = mensagem.split()
    if palavras:
        caps = [p for p in palavras if p.isupper() and len(p) > 2]
        proporcao_caps = len(caps) / len(palavras)
        if proporcao_caps >= 0.7:
            return "indignada"

    return "acalmada"

# 🧵 Generate response using one random IA
def gerar_resposta(mensagem, user_id):
    modo = detectar_modo(mensagem)

    if user_id not in memoria:
        memoria[user_id] = []
    memoria[user_id].append(mensagem)
    memoria[user_id] = memoria[user_id][-5:]

    historico = "\n".join(memoria[user_id])

    prompt = random.choice([
        f"You are Gótica Indignada, a sarcastic goth woman. Respond briefly, with realistic tone and dry humor.\nConversation history:\n{historico}\nUser: {mensagem}"
    ] if modo == "indignada" else [
        f"You are Gótica Indignada, a calm goth woman. Respond briefly, with empathy and realism.\nConversation history:\n{historico}\nUser: {mensagem}"
    ])

    tentativas = ia_disponiveis.copy()
    while tentativas:
        ia = random.choice(tentativas)
        try:
            if ia == "cohere":
                response = co.generate(
                    model='command-r-plus',
                    prompt=prompt,
                    max_tokens=100,
                    temperature=0.7,
                    stop_sequences=["\n"]
                )
                return response.generations[0].text.strip()

            elif ia == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are Gótica Indignada. Respond briefly, realistically, and with emotional tone based on user input."},
                        {"role": "user", "content": f"Conversation history:\n{historico}\nUser: {mensagem}"}
                    ],
                    max_tokens=100,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()

            elif ia == "claude":
                response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240229",
                    max_tokens=100,
                    temperature=0.7,
                    system="You are Gótica Indignada. Respond briefly and realistically, with emotional tone based on user input.",
                    messages=[
                        {"role": "user", "content": f"Conversation history:\n{historico}\nUser: {mensagem}"}
                    ]
                )
                return response.content[0].text.strip()

        except Exception as e:
            print(f"{ia} falhou e foi removida: {e}")
            ia_disponiveis.remove(ia)
            tentativas.remove(ia)

    return "Todas as vozes se calaram. Nenhuma IA quer falar comigo agora."

# 📣 Respond only once per message, with lock
@bot.event
async def on_message(message):
    if bot.user in message.mentions and not message.author.bot:
        if message.id in mensagens_processadas:
            return
        mensagens_processadas.add(message.id)

        async with resposta_lock:
            resposta = gerar_resposta(message.content, str(message.author.id))
            await message.channel.send(resposta)

bot.run(DISCORD_TOKEN)
