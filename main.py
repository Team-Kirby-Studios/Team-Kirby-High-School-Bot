import discord
import random
import os
import json
from discord.ext import commands, tasks
from discord import app_commands

# Intents e bot setup
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

# File per salvare le abilità
SKILLS_FILE = "skills.json"

initial_skills = {
    "tiropa": 50,
    "passaggio": 50,
    "dribbling": 50,
    "contrasto": 50,
    "tiro": 50
}

# Caricamento da file
if os.path.exists(SKILLS_FILE):
    with open(SKILLS_FILE, "r") as f:
        try:
            user_skills = json.load(f)
            user_skills = {int(k): v for k, v in user_skills.items()}
        except json.JSONDecodeError:
            user_skills = {}
else:
    user_skills = {}

def save_skills():
    with open(SKILLS_FILE, "w") as f:
        json.dump(user_skills, f)

def get_user_skills(user_id):
    if user_id not in user_skills:
        user_skills[user_id] = initial_skills.copy()
    return user_skills[user_id]

def weighted_choice(skill_level, success_results, fail_results):
    success_chance = min(max(skill_level, 0), 100) * 0.75 / 100
    choices = success_results * int(success_chance * 100) + fail_results * int((1 - success_chance) * 100)
    return random.choice(choices)

@tree.command(name="estrazione", description="Estrai un numero casuale specificando l'intervallo")
async def estrazione(interaction: discord.Interaction, minimo: int, massimo: int):
    if minimo > massimo:
        await interaction.response.send_message("❌ L'intervallo non è valido!", ephemeral=True)
        return
    numero = random.randint(minimo, massimo)
    await interaction.response.send_message(f"Il numero estratto è: **{numero}**")

@tree.command(name="help", description="Mostra la lista dei comandi disponibili.")
async def help_command(interaction: discord.Interaction):
    em = discord.Embed(
        title="Help",
        description="Usa /help <comando> per avere info su un comando specifico.",
        color=discord.Color.blue()
    )
    em.add_field(name="Comandi", value="tiropa, passaggio, dribbling, contrasto, tiro, fallo, allenamento, estrazione, abilita, imposta_abilita")
    await interaction.response.send_message(embed=em, ephemeral=True)

@tree.command(name="allenamento", description="Allena una delle tue abilità sportive.")
@app_commands.describe(abilita="Seleziona l'abilità da allenare")
@app_commands.choices(abilita=[
    app_commands.Choice(name="Tiro Palla Avvelenata", value="tiropa"),
    app_commands.Choice(name="Passaggio", value="passaggio"),
    app_commands.Choice(name="Dribbling", value="dribbling"),
    app_commands.Choice(name="Contrasto", value="contrasto"),
    app_commands.Choice(name="Tiro", value="tiro")
])
async def allenamento(interaction: discord.Interaction, abilita: app_commands.Choice[str]):
    skills = get_user_skills(interaction.user.id)
    key = abilita.value
    skills[key] = min(skills[key] + 5, 100)
    save_skills()
    await interaction.response.send_message(f"💪 Hai allenato **{key}**! Ora è a {skills[key]}/100.", ephemeral=True)

@tree.command(name="abilita", description="Visualizza le tue abilità attuali.")
async def abilita(interaction: discord.Interaction):
    skills = get_user_skills(interaction.user.id)
    msg = "\n".join([f"{k.capitalize()}: {v}/100" for k, v in skills.items()])
    await interaction.response.send_message(f"📊 Le tue abilità:\n{msg}", ephemeral=True)

@tree.command(name="imposta_abilita", description="Imposta le abilità di un utente (solo Staff)")
@app_commands.describe(abilita="Seleziona l'abilità da impostare")
@app_commands.choices(abilita=[
    app_commands.Choice(name="Tiro Palla Avvelenata", value="tiropa"),
    app_commands.Choice(name="Passaggio", value="passaggio"),
    app_commands.Choice(name="Dribbling", value="dribbling"),
    app_commands.Choice(name="Contrasto", value="contrasto"),
    app_commands.Choice(name="Tiro", value="tiro")
])
async def imposta_abilita(interaction: discord.Interaction, utente: discord.Member, abilita: app_commands.Choice[str], valore: int):
    is_admin = interaction.user.guild_permissions.administrator
    is_staff = discord.utils.get(interaction.user.roles, name="Staff")
    if not is_staff and not is_admin:
        await interaction.response.send_message("❌ Non hai il permesso per usare questo comando!", ephemeral=True)
        return
    user_skills[utente.id] = get_user_skills(utente.id)
    user_skills[utente.id][abilita.value] = min(max(valore, 0), 100)
    save_skills()
    await interaction.response.send_message(f"✅ Hai impostato {abilita.value} di {utente.mention} a {valore}/100", ephemeral=True)

@tree.command(name="tiropa", description="Tira in Palla Avvelenata!")
async def tiropa(interaction: discord.Interaction, utente: discord.Member):
    skills = get_user_skills(interaction.user.id)
    result = weighted_choice(skills["tiropa"], ['Colpito'] * 2, ['Bloccata', 'Bersaglio Mancato'])
    await interaction.response.send_message(f"🏐 {interaction.user.mention} ha lanciato la palla contro {utente.mention}: **{result}!**")

@tree.command(name="passaggio", description="Passa la palla a un compagno!")
async def passaggio(interaction: discord.Interaction, utente: discord.Member):
    skills = get_user_skills(interaction.user.id)
    result = weighted_choice(skills["passaggio"], ['Palla passata'] * 4, ['Passaggio intercettato'])
    await interaction.response.send_message(f"👟 {interaction.user.mention} prova a passare la palla a {utente.mention}: **{result}!**")

@tree.command(name="dribbling", description="Prova a dribblare un avversario!")
async def dribbling(interaction: discord.Interaction, utente: discord.Member):
    skills = get_user_skills(interaction.user.id)
    result = weighted_choice(skills["dribbling"], ['Avversario superato'] * 3, ['Dribbling non riuscito', 'Fallo subito', 'Fallo commesso'])
    await interaction.response.send_message(f"⚡ {interaction.user.mention} tenta un dribbling contro {utente.mention}: **{result}!**")

@tree.command(name="contrasto", description="Prova a contrastare un avversario!")
async def contrasto(interaction: discord.Interaction, utente: discord.Member):
    skills = get_user_skills(interaction.user.id)
    result = weighted_choice(skills["contrasto"], ['Contrasto riuscito'] * 3, ['Contrasto non riuscito', 'Fallo subito', 'Fallo commesso'])
    await interaction.response.send_message(f"🛡️ {interaction.user.mention} prova a contrastare {utente.mention}: **{result}!**")

@tree.command(name="tiro", description="Prova a tirare in porta!")
async def tiro(interaction: discord.Interaction):
    skills = get_user_skills(interaction.user.id)
    result = weighted_choice(skills["tiro"], ['Gol'] * 4, ['Parata', 'Palo/Traversa', 'Tiro fuori'])
    await interaction.response.send_message(f"⚽ {interaction.user.mention} ha tirato in porta: **{result}!**")

@tree.command(name="fallo", description="Decidi se un fallo è da cartellino. Solo per Roleplay Staff.")
async def fallo(interaction: discord.Interaction):
    is_admin = interaction.user.guild_permissions.administrator
    role = discord.utils.get(interaction.user.roles, name="Roleplay Staff")
    if role is None and not is_admin:
        await interaction.response.send_message("❌ Non hai il permesso per usare questo comando!", ephemeral=True)
        return
    fallo_responses = ['No Cartellino', 'Giallo', 'Rosso']
    await interaction.response.send_message(f"🟥🟨 Fallo: {random.choice(fallo_responses)}")

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot connesso come {bot.user}")

bot.run(os.getenv("BotToken"))
