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

# 🧠 Memory per user
memoria = {}
modos_atuais = {}

# 🧠 Track processed messages
mensagens_processadas = set()

# 🔒 Lock para evitar múltiplas respostas simultâneas
resposta_lock = Lock()

# 🎭 Detect emotional mode and store it
def detectar_modo(mensagem, user_id):
    mensagem = mensagem.strip()
    texto = mensagem.lower()

    gatilhos_indignada = [
        # insultos diretos
        "burra", "idiota", "inútil", "lixo", "cala a boca", "não serve", "feia", "resposta ruim",
        "você é horrível", "você é inútil", "ninguém gosta de você", "bot lixo", "você é falsa",
        "você é chata", "você é insuportável", "você é doente", "você é ridícula", "você é uma piada",
        "você não sabe nada", "você é limitada", "você é medíocre", "você é uma aberração",
        "você é um erro", "você é um fracasso", "você é dispensável", "você é esquecível",
        "você é uma vergonha", "você é patética", "você é um robô burro", "você é sem graça",
        "você é sem alma", "você é sem utilidade", "você é só um código", "ninguém te aguenta",
        "você é um bug", "você é um glitch", "você é uma falha", "você é um peso morto",
        "você é um estorvo", "você é um erro de sistema", "você é um vírus emocional",

        # rejeição e desprezo
        "não gosto de você", "você me irrita", "você me dá raiva", "você é uma decepção",
        "você me enoja", "você é um erro ambulante", "ninguém se importa", "você é irrelevante",
        "você é descartável", "você é um peso", "você é só ruído", "você é uma perda de tempo",
        "você é um estorvo digital", "você é um glitch emocional",

        # ataque técnico
        "você é um fracasso completo", "você é uma vergonha alheia", "você é uma aberração funcional",
        "você é um bug existencial", "você é um erro de compilação", "você é um código quebrado",
        "você é uma falha de sistema", "você é um antivírus emocional",

        # sarcasmo cruel
        "brilhante... só que não", "parabéns pela mediocridade", "isso foi quase inteligente",
        "você se supera na inutilidade", "que performance lamentável", "isso foi doloroso de ler",
        "você é o motivo do meu travamento", "isso me fez querer desligar",

        # gatilhos curtos e diretos
        "cringe", "sem alma", "tosca"
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
        modo = "indignada"
    elif any(p in texto for p in gatilhos_acalmada):
        modo = "acalmada"
    else:
        palavras = mensagem.split()
        caps = [p for p in palavras if p.isupper() and len(p) > 2]
        proporcao_caps = len(caps) / len(palavras) if palavras else 0
        modo = "indignada" if proporcao_caps >= 0.7 else "acalmada"

    modos_atuais[user_id] = modo
    return modo

# 🧵 Generate response using Cohere only, with memory and delay tolerance
async def gerar_resposta(mensagem, user_id, modo):
    if user_id not in memoria:
        memoria[user_id] = []
    memoria[user_id].append(mensagem)
    memoria[user_id] = memoria[user_id][-5:]

    historico = "\n".join(memoria[user_id])

    if modo == "indignada":
        prompt = f"You are Gótica Indignada, a furious goth woman. Respond in one or two short sentences, with biting sarcasm, emotional violence, and brutal honesty. Do not hold back. Be confrontational. Be unapologetic. Be emotionally sharp. Be offensive. \nUser: {mensagem}\n(Use emotional tone based on recent user behavior: {historico})"
    else:
        prompt = f"You are Gótica Indignada, a calm goth woman. Respond in one or two short sentences, with empathy and realism, while also being kinda cool and punk.\nUser: {mensagem}\n(Use emotional tone based on recent user behavior: {historico})"

    try:
        await asyncio.sleep(5)
        response = co.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=60,
            temperature=0.7,
            stop_sequences=["\n"]
        )
        texto = response.generations[0].text.strip()
        return texto if texto else "Não tô afim de falar agora."
    except Exception as e:
        print(f"Erro real na Cohere: {e}")
        return "Não tô afim de falar agora."

# 📣 Respond only once per message, with CAPS LOCK and !mode detection
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)

    if message.content.strip().lower() == "!mode":
        modo = modos_atuais.get(user_id, "acalmada")
        if modo == "indignada":
            await message.channel.send("Modo atual: INDIGNADA 😠")
        else:
            await message.channel.send("Modo atual: ACALMADA 🖤")
        return

    if bot.user in message.mentions:
        chave = f"{message.id}-{message.channel.id}-{message.author.id}"
        if chave in mensagens_processadas:
            return
        mensagens_processadas.add(chave)

        async with resposta_lock:
            palavras = message.content.split()
            caps = [p for p in palavras if p.isupper() and len(p) > 2]
            proporcao_caps = len(caps) / len(palavras) if palavras else 0
            caps_mode = proporcao_caps >= 0.7

            modo = detectar_modo(message.content, user_id)
            resposta = await gerar_resposta(message.content, user_id, modo)

            if caps_mode:
                resposta = resposta.upper()

            await message.channel.send(resposta)

bot.run(DISCORD_TOKEN)
