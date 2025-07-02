import discord
import random
import os
import json
from discord.ext import commands, tasks
from discord import app_commands
import re

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)
owner_id = ID OWNER

SKILLS_FILE = "skills.json"
ESTRATTI_FILE = "estratti.json"
STUDENTI_FILE = "studenti.json"
MATERIE_PER_PROF = {
    "ID PROF": ["materia"],
}
VOTI_FILE = "voti.json"
CANALE_VOTI_ID = ID CANALE

initial_skills = {
    "tiropa": 50,
    "passaggio": 50,
    "dribbling": 50,
    "contrasto": 50,
    "tiro": 50,
    "portiere": 50
}

if os.path.exists(SKILLS_FILE):
    with open(SKILLS_FILE, "r") as f:
        try:
            user_skills = json.load(f)
            user_skills = {int(k): v for k, v in user_skills.items()}
        except json.JSONDecodeError:
            user_skills = {}
else:
    user_skills = {}

for user_id, skills in user_skills.items():
    for abilita, valore in initial_skills.items():
        if abilita not in skills:
            skills[abilita] = valore

def save_skills():
    with open(SKILLS_FILE, "w") as f:
        json.dump(user_skills, f)

def get_user_skills(user_id):
    if user_id not in user_skills:
        user_skills[user_id] = initial_skills.copy()
    else:
        for abilita, valore in initial_skills.items():
            if abilita not in user_skills[user_id]:
                user_skills[user_id][abilita] = valore
    return user_skills[user_id]

with open(STUDENTI_FILE, "r", encoding="utf-8") as f:
    STUDENTI = json.load(f)

if os.path.exists(ESTRATTI_FILE):
    with open(ESTRATTI_FILE, "r", encoding="utf-8") as f:
        estratti_per_utente = json.load(f)
else:
    estratti_per_utente = {}

def salva_estratti():
    with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
        json.dump(estratti_per_utente, f, indent=2)

def weighted_choice(skill_level, success_results, fail_results):
    success_chance = min(max(skill_level, 0), 100) * 0.75 / 100
    choices = success_results * int(success_chance * 100) + fail_results * int((1 - success_chance) * 100)
    return random.choice(choices)

def salva_voti(voti):
    with open(VOTI_FILE, "w", encoding="utf-8") as f:
        json.dump(voti, f, indent=2)

def leggi_genere(studente_id):
    try:
        with open(STUDENTI_FILE, "r", encoding="utf-8") as f:
            studenti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Studente"  # Default se il file è vuoto o non esiste

    # Scansiona la lista e trova lo studente con l'ID corrispondente
    for studente in studenti:
        if studente["id"] == studente_id:
            return "Studentessa" if studente.get("genere") == "f" else "Studente"

    return "Studente"  # Default se l'ID non viene trovato
    
def studente_esiste(studente_id):
    try:
        with open(STUDENTI_FILE, "r", encoding="utf-8") as f:
            studenti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return False  

    return any(studente["id"] == studente_id for studente in studenti)
    
def voto_valido(voto):
    return re.match(r"^(10 e lode|10|[1-9](\s?e mezzo)?[+-]{0,2})(pon)?$", voto) is not None
    
def trova_nome_studente(studente_id):
    try:
        with open(STUDENTI_FILE, "r", encoding="utf-8") as f:
            studenti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None  

    for studente in studenti:
        if studente["id"] == studente_id:
            return studente["nome"]

    return None

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
    app_commands.Choice(name="Tiro", value="tiro"),
    app_commands.Choice(name="Portiere", value="portiere")
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
    app_commands.Choice(name="Tiro", value="tiro"),
    app_commands.Choice(name="Portiere", value="portiere")
])
async def imposta_abilita(interaction: discord.Interaction, utente: discord.Member, abilita: app_commands.Choice[str], valore: int):
    is_admin = interaction.user.guild_permissions.administrator
    is_staff = discord.utils.get(interaction.user.roles, name="Staff")
    if interaction.user.id != owner_id and not is_staff and not is_admin:
        await interaction.response.send_message("❌ Non hai il permesso per usare questo comando!", ephemeral=True)
        return
    user_skills[utente.id] = get_user_skills(utente.id)
    user_skills[utente.id][abilita.value] = min(max(valore, 0), 100)
    save_skills()
    await interaction.response.send_message(f"✅ Hai impostato {abilita.value} di {utente.mention} a {valore}/100", ephemeral=True)

@tree.command(name="tiropa", description="Tira in Palla Avvelenata!")
async def tiropa(interaction: discord.Interaction, utente: discord.Member):
    skills_attaccante = get_user_skills(interaction.user.id)
    skills_difensore = get_user_skills(utente.id)

    att_stat = max(min(skills_attaccante["tiropa"], 100), 50)
    def_stat = max(min(skills_difensore["tiropa"], 100), 50)

    scaling = (att_stat - def_stat) / 50  # varia da -1 a +1

    colpito_chance = 0.5 + scaling * 0.2  # da 0.3 a 0.7
    bloccata_chance = 0.35 - scaling * 0.2  # da 0.15 a 0.55

    colpito_chance = max(0.3, min(colpito_chance, 0.7))
    bloccata_chance = max(0.15, min(bloccata_chance, 0.55))

    mancato_bonus = (100 - att_stat) / 100 * 0.1  # da 0 a 0.05
    mancato_chance = max(0.05, 1.0 - (colpito_chance + bloccata_chance) + mancato_bonus)

    total = colpito_chance + bloccata_chance + mancato_chance
    colpito_chance /= total
    bloccata_chance /= total
    mancato_chance /= total

    risultati = (
    ["Colpito"] * int(colpito_chance * 100) +
    ["Bloccata"] * int(bloccata_chance * 100) +
    ["Schivata/Bersaglio Mancato"] * int(mancato_chance * 100)
    )

    risultato = random.choice(risultati)
    await interaction.response.send_message(
        f"🏐 {interaction.user.mention} ha lanciato la palla contro {utente.mention}: **{risultato}!**"
    )

@tree.command(name="passaggio", description="Passa la palla a un compagno!")
async def passaggio(interaction: discord.Interaction, utente: discord.Member):
    skills = get_user_skills(interaction.user.id)
    result = weighted_choice(skills["passaggio"], ['Palla passata'] * 4, ['Passaggio intercettato'])
    await interaction.response.send_message(f"👟 {interaction.user.mention} prova a passare la palla a {utente.mention}: **{result}!**")

@tree.command(name="dribbling", description="Prova a dribblare un avversario!")
async def dribbling(interaction: discord.Interaction, utente: discord.Member):
    skill_att = get_user_skills(interaction.user.id)
    skill_def = get_user_skills(utente.id)
    
    stats_att = max(min(skill_att["dribbling"], 100), 50)
    stats_def = max(min(skill_def["contrasto"], 100), 50)
    
    scaling = (stats_att - stats_def) / 50
    
    superato_chance = min(0.75, max(0.15, 0.4 + scaling * 0.35))
    nonsuperato_chance = min(0.7, max(0.10, 0.5 - scaling * 0.35))
    subito_chance = min(0.25, max(0.05, 0.05 + scaling * 0.2))
    commesso_chance = min(0.05, max(0.01, 0.01 - scaling * 0.05))
    
    totale = superato_chance + nonsuperato_chance + subito_chance + commesso_chance
    if totale > 1:
        scale = 1 / totale
        superato_chance *= scale
        nonsuperato_chance *= scale
        subito_chance *= scale
        commesso_chance *= scale
        
    eventi = ["Avversario superato", "Dribbling non riuscito", "Fallo subito", "Fallo commesso"]
    pesi = [superato_chance, nonsuperato_chance, subito_chance, commesso_chance]
    
    result = random.choices(eventi, weights=pesi, k=1)[0]
    await interaction.response.send_message(f"⚡ {interaction.user.mention} tenta un dribbling contro {utente.mention}: **{result}!**")

@tree.command(name="contrasto", description="Prova a contrastare un avversario!")
async def contrasto(interaction: discord.Interaction, utente: discord.Member):
    skill_def = get_user_skills(interaction.user.id)
    skill_att = get_user_skills(utente.id)
    
    stats_att = max(min(skill_att["dribbling"], 100), 50)
    stats_def = max(min(skill_def["contrasto"], 100), 50)
    
    scaling = (stats_def - stats_att) / 50
    
    riuscito_chance = min(0.75, max(0.15, 0.4 + scaling * 0.35))
    nonriuscito_chance = min(0.6, max(0.10, 0.45 - scaling * 0.35))
    subito_chance = min(0.05, max(0.01, 0.01 + scaling * 0.05))
    commesso_chance = min(0.2, max(0.05, 0.1 - scaling * 0.1))
    
    totale = riuscito_chance + nonriuscito_chance + subito_chance + commesso_chance
    if totale > 1:
        scale = 1 / totale
        riuscito_chance *= scale
        nonriuscito_chance *= scale
        subito_chance *= scale
        commesso_chance *= scale
        
    eventi = ["Contrasto riuscito", "Contrasto non riuscito", "Fallo subito", "Fallo commesso"]
    pesi = [riuscito_chance, nonriuscito_chance, subito_chance, commesso_chance]
    
    result = random.choices(eventi, weights=pesi, k=1)[0]
    await interaction.response.send_message(f"🛡️ {interaction.user.mention} prova a contrastare {utente.mention}: **{result}!**")

@tree.command(name="tiro", description="Prova a tirare in porta!")
async def tiro(interaction: discord.Interaction, utente: discord.Member):
    skills_att = get_user_skills(interaction.user.id)
    skills_por = get_user_skills(utente.id)
    
    stat_att = max(min(skills_att["tiro"], 100), 50)
    stat_por = max(min(skills_por["portiere"], 100), 50)
    palo_chance = 0.05
    
    scaling = (stat_att - stat_por) / 50

    gol_chance = min(0.75, max(0.35, 0.55 + scaling * 0.2))
    parata_chance = min(0.55, max(0.15, 0.35 - scaling * 0.2))

    errore_bonus = (100 - stat_att) / 100 * 0.25

    fuori_chance = min(0.3, max(0.05, errore_bonus))

    totale = gol_chance + parata_chance + fuori_chance + palo_chance
    if totale > 1:
        scale = 1 / totale
        gol_chance *= scale
        parata_chance *= scale
        fuori_chance *= scale
        palo_chance *= scale

    eventi = ["Gol", "Parata", "Tiro Fuori", "Palo/Traversa"]
    pesi = [gol_chance, parata_chance, fuori_chance, palo_chance]

    result = random.choices(eventi, weights=pesi, k=1)[0]

    await interaction.response.send_message(
        f"⚽ {interaction.user.mention} ha tirato in porta: **{result}!** (Portiere: {utente.mention})"
    )

@tree.command(name="fallo", description="Decidi se un fallo è da cartellino. Solo per Roleplay Staff.")
async def fallo(interaction: discord.Interaction):
    is_admin = interaction.user.guild_permissions.administrator
    role = discord.utils.get(interaction.user.roles, name="Roleplay Staff")
    if interaction.user.id != owner_id and role is None and not is_admin:
        await interaction.response.send_message("❌ Non hai il permesso per usare questo comando!", ephemeral=True)
        return
    fallo_responses = ['No Cartellino', 'Giallo', 'Rosso']
    await interaction.response.send_message(f"🟥🟨 Fallo: {random.choice(fallo_responses)}")

@tree.command(name="sorteggio", description="Estrai studenti in modo casuale per materia")
@app_commands.describe(materia="Materia da cui estrarre", quanti="Numero di studenti da sorteggiare")
@app_commands.choices(
    materia=[
        app_commands.Choice(name="Motoria", value="motoria"),
        app_commands.Choice(name="PCTO Videogames", value="pcto_videogames"),
        app_commands.Choice(name="Matematica", value="matematica"),
        app_commands.Choice(name="Fisica", value="fisica"),
        app_commands.Choice(name="Musica", value="musica"),
        app_commands.Choice(name="Religione", value="religione"),
        app_commands.Choice(name="Ed. sessuale", value="ed_sessuale"),
        app_commands.Choice(name="Inglese", value="inglese"),
        app_commands.Choice(name="Scienze", value="scienze"),
        app_commands.Choice(name="Filosofia", value="filosofia"),
        app_commands.Choice(name="Storia", value="storia"),
        app_commands.Choice(name="Italiano", value="italiano"),
        app_commands.Choice(name="Test", value="test")
    ]
)
async def sorteggio(interaction: discord.Interaction, materia: app_commands.Choice[str], quanti: int):
    user_id = str(interaction.user.id)
    materia_nome = materia.value

    if interaction.user.id != owner_id and user_id not in MATERIE_PER_PROF:
        await interaction.response.send_message("Non hai il permesso per usare questo comando.", ephemeral=True)
        return

    materie_autorizzate = MATERIE_PER_PROF.get(user_id, [])
    if interaction.user.id != owner_id and materia_nome not in materie_autorizzate:
        await interaction.response.send_message(f"Non insegni la materia **{materia_nome}**.", ephemeral=True)
        return

    try:
        with open("estratti.json", "r") as f:
            estratti_per_utente = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        estratti_per_utente = {}

    with open("studenti.json", "r", encoding="utf-8") as f:
        studenti = json.load(f)

    studenti_ids = [str(s["id"]) for s in studenti]

    estratti_per_utente.setdefault(user_id, {}).setdefault(materia_nome, [])

    # Se non ci sono abbastanza studenti da estrarre, resetta la lista degli estratti
    rimanenti = list(set(studenti_ids) - set(estratti_per_utente[user_id][materia_nome]))
    if len(rimanenti) < quanti:
        estratti_per_utente[user_id][materia_nome].clear()
        rimanenti = list(set(studenti_ids) - set(estratti_per_utente[user_id][materia_nome]))

    scelti = random.sample(rimanenti, quanti)
    estratti_per_utente[user_id][materia_nome].extend(scelti)

    # Salva gli estratti aggiornati
    with open("estratti.json", "w", encoding="utf-8") as f:
        json.dump(estratti_per_utente, f, indent=2)

    menzioni = [f"<@{uid}>" for uid in scelti]
    await interaction.response.send_message(
        f"Gli studenti sorteggiati sono:\n" + "\n".join(menzioni)
    )

@tree.command(name="usciti", description="Mostra gli studenti già estratti per una materia")
@app_commands.describe(materia="Materia da controllare", admin="Mostra gli estratti di tutti i professori (solo admin)")
@app_commands.choices(
    materia=[
        app_commands.Choice(name="Motoria", value="motoria"),
        app_commands.Choice(name="PCTO Videogames", value="pcto_videogames"),
        app_commands.Choice(name="Matematica", value="matematica"),
        app_commands.Choice(name="Fisica", value="fisica"),
        app_commands.Choice(name="Musica", value="musica"),
        app_commands.Choice(name="Religione", value="religione"),
        app_commands.Choice(name="Ed. sessuale", value="ed_sessuale"),
        app_commands.Choice(name="Inglese", value="inglese"),
        app_commands.Choice(name="Scienze", value="scienze"),
        app_commands.Choice(name="Filosofia", value="filosofia"),
        app_commands.Choice(name="Storia", value="storia"),
        app_commands.Choice(name="Italiano", value="italiano"),
        app_commands.Choice(name="Test", value="test")
    ]
)
async def usciti(interaction: discord.Interaction, materia: app_commands.Choice[str], admin: bool = False):
    user_id = str(interaction.user.id)
    materia_nome = materia.value

    if admin and interaction.user.id != owner_id:
        await interaction.response.send_message("Solo l'admin può usare questa opzione.", ephemeral=True)
        return

    try:
        with open("estratti.json", "r") as f:
            estratti_per_utente = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        estratti_per_utente = {}

    tutti_studenti_ids = [s["id"] for s in STUDENTI]
    embeds = []

    if admin:
        for prof_id, materie in estratti_per_utente.items():
            if materia_nome not in materie:
                continue

            ids_estratti = materie[materia_nome]
            ids_mancanti = [id_ for id_ in tutti_studenti_ids if id_ not in ids_estratti]

            menzioni_estratti = [f"<@{s['id']}>" for s in STUDENTI if s["id"] in ids_estratti]
            menzioni_mancanti = [f"<@{id_}>" for id_ in ids_mancanti]

            embed = discord.Embed(
                title=f"📚 Estrazioni per {materia.name}",
                description=f"Docente: <@{prof_id}>",
                color=discord.Color.blue()
            )
            if menzioni_estratti:
                embed.add_field(
                    name=f"✅ {len(menzioni_estratti)} Estratti",
                    value="\n".join(menzioni_estratti),
                    inline=False
                )
            if menzioni_mancanti:
                embed.add_field(
                    name=f"🕓 {len(menzioni_mancanti)} Mancanti",
                    value="\n".join(menzioni_mancanti),
                    inline=False
                )
            embeds.append(embed)

    else:
        if user_id not in estratti_per_utente or materia_nome not in estratti_per_utente[user_id]:
            await interaction.response.send_message("Nessuno studente è stato ancora estratto per questa materia.", ephemeral=True)
            return

        ids_estratti = estratti_per_utente[user_id][materia_nome]
        ids_mancanti = [id_ for id_ in tutti_studenti_ids if id_ not in ids_estratti]

        menzioni_estratti = [f"<@{s['id']}>" for s in STUDENTI if s["id"] in ids_estratti]
        menzioni_mancanti = [f"<@{id_}>" for id_ in ids_mancanti]

        embed = discord.Embed(
            title=f"📚 Estrazioni per {materia.name}",
            color=discord.Color.green()
        )
        embed.add_field(
            name=f"✅ {len(menzioni_estratti)} Estratti",
            value="\n".join(menzioni_estratti) or "Nessuno",
            inline=False
        )
        embed.add_field(
            name=f"🕓 {len(menzioni_mancanti)} Mancanti",
            value="\n".join(menzioni_mancanti) or "Nessuno",
            inline=False
        )
        embeds.append(embed)

    if not embeds:
        await interaction.response.send_message("Nessuno studente è stato ancora estratto per questa materia.", ephemeral=True)
    else:
        for embed in embeds:
            await interaction.followup.send(embed=embed, ephemeral=True) if interaction.response.is_done() else await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="aggiungi_studente", description="Aggiunge uno studente agli estratti (es. se si offre volontario)")
@app_commands.describe(
    materia="Materia di riferimento",
    studente="Studente da aggiungere (menziona)",
    prof="(Solo owner) Seleziona un prof al posto del quale agire"
)
@app_commands.choices(materia=[
    app_commands.Choice(name="Motoria", value="motoria"),
    app_commands.Choice(name="PCTO Videogames", value="pcto_videogames"),
    app_commands.Choice(name="Matematica", value="matematica"),
    app_commands.Choice(name="Fisica", value="fisica"),
    app_commands.Choice(name="Musica", value="musica"),
    app_commands.Choice(name="Religione", value="religione"),
    app_commands.Choice(name="Ed. sessuale", value="ed_sessuale"),
    app_commands.Choice(name="Inglese", value="inglese"),
    app_commands.Choice(name="Scienze", value="scienze"),
    app_commands.Choice(name="Filosofia", value="filosofia"),
    app_commands.Choice(name="Storia", value="storia"),
    app_commands.Choice(name="Italiano", value="italiano"),
    app_commands.Choice(name="Test", value="test")
])
async def aggiungi_studente(
    interaction: discord.Interaction,
    materia: app_commands.Choice[str],
    studente: discord.Member,
    prof: discord.Member | None = None
):
    user_id = str(interaction.user.id)
    target_id = str(prof.id) if interaction.user.id == owner_id and prof else user_id
    materia_nome = materia.value
    studente_id = str(studente.id)

    if interaction.user.id != owner_id and user_id not in MATERIE_PER_PROF:
        await interaction.response.send_message("Non hai il permesso per usare questo comando.", ephemeral=True)
        return

    materie_autorizzate = MATERIE_PER_PROF.get(target_id, [])
    if interaction.user.id != owner_id and materia_nome not in materie_autorizzate:
        await interaction.response.send_message(f"Non insegni la materia **{materia_nome}**.", ephemeral=True)
        return

    if os.path.exists(ESTRATTI_FILE):
        with open(ESTRATTI_FILE, "r", encoding="utf-8") as f:
            estratti_per_utente = json.load(f)
    else:
        estratti_per_utente = {}

    estratti_per_utente.setdefault(target_id, {}).setdefault(materia_nome, [])
    if studente_id in estratti_per_utente[target_id][materia_nome]:
        await interaction.response.send_message(f"{studente.mention} è già presente negli estratti per **{materia.name}**.", ephemeral=True)
        return

    estratti_per_utente[target_id][materia_nome].append(studente_id)

    with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
        json.dump(estratti_per_utente, f, indent=2)

    await interaction.response.send_message(f"{studente.mention} è stato aggiunto agli estratti di **{materia.name}**.", ephemeral=True)

@tree.command(name="rimuovi_studente", description="Rimuove uno studente dagli estratti di una materia")
@app_commands.describe(
    materia="Seleziona la materia",
    studente="Studente da rimuovere (menziona)",
    prof="(Solo owner) Seleziona un prof al posto del quale agire"
)
@app_commands.choices(materia=[
    app_commands.Choice(name="Motoria", value="motoria"),
    app_commands.Choice(name="PCTO Videogames", value="pcto_videogames"),
    app_commands.Choice(name="Matematica", value="matematica"),
    app_commands.Choice(name="Fisica", value="fisica"),
    app_commands.Choice(name="Musica", value="musica"),
    app_commands.Choice(name="Religione", value="religione"),
    app_commands.Choice(name="Ed. sessuale", value="sessuale"),
    app_commands.Choice(name="Inglese", value="inglese"),
    app_commands.Choice(name="Scienze", value="scienze"),
    app_commands.Choice(name="Filosofia", value="filosofia"),
    app_commands.Choice(name="Storia", value="storia"),
    app_commands.Choice(name="Italiano", value="italiano"),
    app_commands.Choice(name="Test", value="test"),
])
async def rimuovi_studente(
    interaction: discord.Interaction,
    materia: app_commands.Choice[str],
    studente: discord.Member,
    prof: discord.Member | None = None
):
    # Ricarica da file estratti.json all'inizio del comando
    try:
        with open("estratti.json", "r", encoding="utf-8") as f:
            estratti_per_utente = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        estratti_per_utente = {}

    user_id = str(interaction.user.id)
    target_id = str(prof.id) if interaction.user.id == owner_id and prof else user_id
    materia_nome = materia.value
    studente_id = str(studente.id)

    if interaction.user.id != owner_id and user_id not in MATERIE_PER_PROF:
        await interaction.response.send_message("Non hai il permesso per usare questo comando.", ephemeral=True)
        return

    materie_autorizzate = MATERIE_PER_PROF.get(target_id, [])
    if interaction.user.id != owner_id and materia_nome not in materie_autorizzate:
        await interaction.response.send_message(f"Non insegni la materia **{materia_nome}**.", ephemeral=True)
        return

    if target_id not in estratti_per_utente or materia_nome not in estratti_per_utente[target_id] or studente_id not in estratti_per_utente[target_id][materia_nome]:
        await interaction.response.send_message("Questo studente non è presente negli estratti.", ephemeral=True)
        return

    estratti_per_utente[target_id][materia_nome].remove(studente_id)

    # Salva subito su file
    with open("estratti.json", "w", encoding="utf-8") as f:
        json.dump(estratti_per_utente, f, indent=2)

    await interaction.response.send_message(f"{studente.mention} è stato rimosso dagli estratti di **{materia.name}**.", ephemeral=True)

@tree.command(name="voti", description="Mostra i voti che hai ricevuto e le materie mancanti.")
async def voti(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    # Mappa genitore -> lista di nomi degli studenti (figli)
    FIGLI_PER_GENITORE = {
        "ID GENITORE": ["NOME STUDENTE"]
    }

    try:
        with open("voti.json", "r", encoding="utf-8") as f:
            voti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Errore nel caricamento dei voti.", ephemeral=True)
        return

    try:
        with open(STUDENTI_FILE, "r", encoding="utf-8") as f:
            studenti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Errore nel caricamento degli studenti.", ephemeral=True)
        return
    genitore_extra = {"ID GENITORE"}
    is_genitore = any(role.name == "Genitore" for role in interaction.user.roles) or user_id in genitore_extra

    materie_mappate = {
        "matematica": "Matematica",
        "fisica": "Fisica",
        "musica": "Musica",
        "ed_sessuale": "Educazione Sessuale",
        "inglese": "Inglese",
        "scienze": "Scienze",
        "storia": "Storia",
        "italiano": "Italiano"
    }

    if is_genitore:
        nomi_figli = FIGLI_PER_GENITORE.get(user_id)
        if not nomi_figli:
            await interaction.response.send_message("❌ Non sei associato ad alcuno studente registrato.", ephemeral=True)
            return

        # Prima risposta, obbligatoria e unica
        await interaction.response.send_message("👨‍👧‍👦 Ecco i voti dei tuoi figli:", ephemeral=True)

        for nome_studente in nomi_figli:
            voti_studente = voti.get(nome_studente, {})
            materie_con_voti = set(voti_studente.keys())
            materie_possibili = set(materie_mappate.keys())
            materie_mancanti = materie_possibili - materie_con_voti

            titolo = f"📚 Voti di {nome_studente}"
            embed = discord.Embed(
                title=titolo,
                description="Ecco le materie in cui sono stati ricevuti voti e quelle ancora senza:",
                color=discord.Color.blue()
            )

            if materie_con_voti:
                voti_text = "\n".join(
                    f"**{materie_mappate[m]}** → {', '.join(v['voto'] for v in voti_studente[m])}"
                    for m in materie_con_voti
                )
                embed.add_field(name="✅ Voti ricevuti", value=voti_text, inline=False)

            if materie_mancanti:
                materie_mancanti_text = "\n".join(materie_mappate[m] for m in materie_mancanti)
                embed.add_field(name="🕓 Materie senza voti", value=materie_mancanti_text, inline=False)

            # Tutte le risposte successive vanno con followup
            await interaction.followup.send(embed=embed, ephemeral=True)

    else:
        # Utente normale, cerca il proprio nome
        studente = next((s for s in studenti if s["id"] == user_id), None)
        if not studente:
            await interaction.response.send_message("❌ Non sei registrato nel file studenti.json.", ephemeral=True)
            return

        nome_studente = studente["nome"]
        voti_studente = voti.get(nome_studente, {})
        materie_con_voti = set(voti_studente.keys())
        materie_possibili = set(materie_mappate.keys())
        materie_mancanti = materie_possibili - materie_con_voti

        embed = discord.Embed(
            title="📚 I tuoi voti",
            description="Ecco le materie in cui hai ricevuto voti e quelle in cui manca ancora un voto:",
            color=discord.Color.blue()
        )

        if materie_con_voti:
            voti_text = "\n".join(
                f"**{materie_mappate[m]}** → {', '.join(v['voto'] for v in voti_studente[m])}"
                for m in materie_con_voti
            )
            embed.add_field(name="✅ Voti ricevuti", value=voti_text, inline=False)

        if materie_mancanti:
            materie_mancanti_text = "\n".join(materie_mappate[m] for m in materie_mancanti)
            embed.add_field(name="🕓 Materie senza voti", value=materie_mancanti_text, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
    
@tree.command(name="assegna_voto", description="Assegna un voto a uno studente.")
@app_commands.describe(studente="Studente da valutare", materia="Materia", voto="Voto da assegnare", argomento="Argomento (opzionale)", commento="Commento (opzionale)")
@app_commands.choices(
    materia=[
        app_commands.Choice(name="Matematica", value="matematica"),
        app_commands.Choice(name="Fisica", value="fisica"),
        app_commands.Choice(name="Musica", value="musica"),
        app_commands.Choice(name="Educazione Sessuale", value="ed_sessuale"),
        app_commands.Choice(name="Inglese", value="inglese"),
        app_commands.Choice(name="Scienze", value="scienze"),
        app_commands.Choice(name="Storia", value="storia"),
        app_commands.Choice(name="Italiano", value="italiano")
    ]
)
async def assegna_voto(interaction: discord.Interaction, studente: discord.Member, materia: app_commands.Choice[str], voto: str, argomento: str = None, commento: str = None):
    user_id = str(interaction.user.id)
    studente_id = str(studente.id)
    materia_nome = materia.value  

    # **Trova il nome dello studente**
    nome_studente = trova_nome_studente(studente_id)
    if not nome_studente:
        await interaction.response.send_message("❌ Errore: Questo studente non è registrato nel file studenti.json.", ephemeral=True)
        return

    # **Verifica permessi del prof o dell'owner**
    if interaction.user.id != owner_id and (user_id not in MATERIE_PER_PROF or materia_nome not in MATERIE_PER_PROF[user_id]):
        await interaction.response.send_message("❌ Non puoi assegnare voti per questa materia.", ephemeral=True)
        return

    # **Verifica che il voto sia valido**
    if not voto_valido(voto):  # Usa la funzione invece della regex diretta
        await interaction.response.send_message("❌ Formato voto non valido!", ephemeral=True)
        return

    try:
        with open("voti.json", "r", encoding="utf-8") as f:
            voti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        voti = {}

    # **Ora salviamo i voti sotto il nome dello studente!**
    voti.setdefault(nome_studente, {}).setdefault(materia_nome, []).append({"voto": voto, "argomento": argomento, "commento": commento})  

    with open("voti.json", "w", encoding="utf-8") as f:
        json.dump(voti, f, indent=2)

    # **Determina il genere dello studente**
    genere = leggi_genere(studente_id)

    canale_voti = interaction.guild.get_channel(CANALE_VOTI_ID)
    if canale_voti is None:
        await interaction.response.send_message("❌ Errore: Il canale voti non è stato trovato.", ephemeral=True)
        return

    embed = discord.Embed(title="📢 Valutazione aggiornata!", color=discord.Color.green())
    embed.add_field(name=f"{genere}:", value=f"<@{studente_id}>", inline=False)  
    embed.add_field(name="Materia:", value=f"**{materia.name}**", inline=False)
    embed.add_field(name="Voto:", value=f"**{voto}**", inline=False)
    embed.add_field(name="Insegnante:", value=f"<@{user_id}>", inline=False)  

    if argomento:
        embed.add_field(name="Argomento:", value=argomento, inline=False)
    if commento:
        embed.add_field(name="Commento:", value=commento, inline=False)

    await canale_voti.send(embed=embed)
    await interaction.response.send_message(f"✅ Nuovo voto **{voto}** registrato per **{nome_studente}** in **{materia.name}**.", ephemeral=True)
    
@tree.command(name="valutati", description="Mostra gli studenti che hanno ricevuto voti e i relativi voti.")
@app_commands.describe(materia="Materia da filtrare (obbligatoria)")
@app_commands.choices(
    materia=[
        app_commands.Choice(name="Matematica", value="matematica"),
        app_commands.Choice(name="Fisica", value="fisica"),
        app_commands.Choice(name="Musica", value="musica"),
        app_commands.Choice(name="Educazione Sessuale", value="ed_sessuale"),
        app_commands.Choice(name="Inglese", value="inglese"),
        app_commands.Choice(name="Scienze", value="scienze"),
        app_commands.Choice(name="Storia", value="storia"),
        app_commands.Choice(name="Italiano", value="italiano"),
        app_commands.Choice(name="Tutte le materie", value="Tutte")
    ]
)
async def valutati(interaction: discord.Interaction, materia: app_commands.Choice[str]):
    user_id = str(interaction.user.id)
    materie_mappate = {
    "matematica": "Matematica",
    "fisica": "Fisica",
    "musica": "Musica",
    "ed_sessuale": "Educazione Sessuale",
    "inglese": "Inglese",
    "scienze": "Scienze",
    "storia": "Storia",
    "italiano": "Italiano"
    }

    # **Identifica la capo professoressa (motoria)**
    prof_motoria_id = next((uid for uid, materie in MATERIE_PER_PROF.items() if "motoria" in materie), None)

    # **Verifica permessi**
    if user_id not in MATERIE_PER_PROF and user_id != owner_id:
        await interaction.response.send_message("❌ Non sei un prof.", ephemeral=True)
        return

    if materia.value == "Tutte":
        if interaction.user.id != owner_id and user_id != prof_motoria_id:
            await interaction.response.send_message("❌ Solo l'owner e la capo professoressa possono vedere tutti i voti.", ephemeral=True)
            return
    else:
        # **Se il prof sta cercando una materia specifica, verifica se la insegna**
        if user_id not in MATERIE_PER_PROF or materia.value not in MATERIE_PER_PROF[user_id]:
            await interaction.response.send_message("❌ Non insegni questa materia.", ephemeral=True)
            return

    try:
        with open("voti.json", "r", encoding="utf-8") as f:
            voti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Nessun voto registrato.", ephemeral=True)
        return

    embed = discord.Embed(title=f"📊 Voti in {materia.name}", color=discord.Color.blue())
    studenti_trovati = False

    # **Trova gli studenti e taggali**
    with open(STUDENTI_FILE, "r", encoding="utf-8") as f:
        studenti = json.load(f)

    for nome_studente, materie_voti in voti.items():
        studenti_trovati = True
        studente_id = next((s["id"] for s in studenti if s["nome"] == nome_studente), None)
        genere = leggi_genere(studente_id)  # Recupera il genere dello studente
        tag_studente = f"<@{studente_id}>" if studente_id else nome_studente  

        if materia.value == "Tutte":
            voti_lista = [f"**{materie_mappate[m]}**: {', '.join(v['voto'] for v in materie_voti[m])}" for m in materie_voti.keys()]
        else:
            voti_lista = [f"**{v['voto']}**" for v in materie_voti.get(materia.value, [])]

        voti_text = f"{tag_studente} ({', '.join(voti_lista)})" if voti_lista else f"{tag_studente} (❌ Nessun voto)"
        embed.add_field(name=genere, value=voti_text, inline=False)


    if not studenti_trovati:
        await interaction.response.send_message(f"❌ Nessuno studente ha ricevuto voti in **{materia.name}**.", ephemeral=True)
        return

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await tree.sync()
    print(f"✅ Bot connesso come {bot.user}")
        
bot.run("TOKEN")
