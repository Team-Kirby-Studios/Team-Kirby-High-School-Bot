import discord
import random
import os
from discord.ext import commands, tasks

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

# Comando /help
@tree.command(name="help", description="Mostra la lista dei comandi disponibili.")
async def help_command(interaction: discord.Interaction):
    em = discord.Embed(
        title="Help",
        description="Usa /help <comando> per avere info su un comando specifico.",
        color=discord.Color.blue()
    )
    em.add_field(name="Comandi", value="tiropa, passaggio, dribbling, contrasto, tiro, fallo, estrazione")
    await interaction.response.send_message(embed=em, ephemeral=True)

# Funzione per creare un comando randomico
def create_random_command(name, description, responses):
    @tree.command(name=name, description=description)
    async def random_command(interaction: discord.Interaction):
        await interaction.response.send_message(f"{random.choice(responses)}")

# Creazione dei comandi sportivi
create_random_command("tiropa", "Tira in Palla Avvelenata!", ['Colpito', 'Bloccata', 'Bersaglio Mancato'])
create_random_command("passaggio", "Passa la palla a un compagno!", ['Palla passata', 'Passaggio intercettato'])
create_random_command("dribbling", "Prova a dribblare un avversario!", ['Avversario superato', 'Dribbling non riuscito', 'Fallo subito', 'Fallo commesso'])
create_random_command("contrasto", "Prova a contrastare un avversario!", ['Contrasto riuscito', 'Contrasto non riuscito', 'Fallo commesso', 'Fallo subito'])
create_random_command("tiro", "Prova a tirare in porta!", ['Gol', 'Parata', 'Palo/Traversa', 'Tiro fuori'])

# Comando fallo con restrizione di ruolo
@tree.command(name="fallo", description="Decidi se un fallo è da cartellino. Solo per Roleplay Staff.")
async def fallo(interaction: discord.Interaction):
    role = discord.utils.get(interaction.user.roles, name="Roleplay Staff")
    if role is None:
        await interaction.response.send_message("❌ Non hai il permesso per usare questo comando!", ephemeral=True)
        return

    fallo_responses = ['No Cartellino', 'Giallo', 'Rosso']
    await interaction.response.send_message(f"{random.choice(fallo_responses)}")

@bot.event
async def on_ready():
    await tree.sync()  # Sincronizza i comandi con il server
    print(f"✅ Bot connesso come {bot.user}")

# Avvia il bot (sostituisci con il tuo token)
token = os.getenv("BotToken")
bot.run(token)
