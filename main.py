import discord
import random
import os
from discord.ext import commands

# Definizione del bot con intents
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

@tree.command(name="estrazione", description="Estrai un numero casuale specificando l'intervallo")
async def estrazione(interaction: discord.Interaction, minimo: int, massimo: int):
    if minimo > massimo:
        await interaction.response.send_message("❌ L'intervallo non è valido! Assicurati che il minimo sia minore del massimo.", ephemeral=True)
        return

    numero = random.randint(minimo, massimo)
    await interaction.response.send_message(f"Il numero estratto è: **{numero}**")

@bot.event
async def on_ready():
    await tree.sync()  # Sincronizza i comandi con il server
    print(f"✅ Bot connesso come {bot.user}")

# Avvia il bot (sostituisci con il tuo token)
token = os.getenv("BotToken")
bot.run(token)
