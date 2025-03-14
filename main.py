import discord
import random

# Definizione del bot con intents
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

@tree.command(name="casuale", description="Genera un numero casuale tra due intervalli dati")
async def casuale(interaction: discord.Interaction, minimo: int, massimo: int):
    if minimo > massimo:
        await interaction.response.send_message("❌ L'intervallo non è valido! Assicurati che il minimo sia minore del massimo.", ephemeral=True)
        return
    
    numero = random.randint(minimo, massimo)
    await interaction.response.send_message(f"🎲 Numero casuale tra {minimo} e {massimo}: **{numero}**")

@bot.event
async def on_ready():
    await tree.sync()  # Sincronizza i comandi con il server
    print(f"✅ Bot connesso come {bot.user}")

# Avvia il bot (sostituisci con il tuo token)
bot.run("IL_TUO_TOKEN")
