import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import os
import json
import re
import time
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree
owner_id = 899238122955636736

SKILLS_FILE = "skills.json"
ESTRATTI_FILE = "estratti.json"
STUDENTI_FILE = "studenti.json"
MATERIE_PER_PROF = {
    "899235691651825665": ["motoria"],
    "872941805602222141": ["pcto_videogames"],
    "822853281553317898": ["matematica", "fisica"],
    "771008547193618452": ["musica"],
    "802501326361460756": ["religione"],
    "850065176270209034": ["ed_sessuale"],
    "771040688976560158": ["inglese"],
    "920404746039328769": ["scienze"],
    "920402145386311751": ["filosofia"],
    "920389950950764614": ["storia"],
    "832372248115544084": ["italiano"],
    "1377912562154475562": ["arte"],
    "899238122955636736": ["test"]
}

NOMI_MATERIE = {
    "italiano": "Italiano",
    "matematica": "Matematica",
    "fisica": "Fisica",
    "inglese": "Inglese",
    "storia": "Storia",
    "scienze": "Scienze",
    "ed_sessuale": "Educazione Sessuale",
    "arte": "Arte",
    "musica": "Musica",
    "filosofia": "Filosofia",
    "motoria": "Motoria",
    "religione": "Religione",
    "condotta": "Condotta",
    "pcto_videogames": "Videogames"
}

ORDINE_MATERIE = [
    "italiano", "storia", "filosofia", "scienze", "matematica", "fisica",
    "inglese", "ed_sessuale", "arte", "musica", "motoria", "religione", "condotta"
]

VOTI_FILE = "voti.json"
CANALE_VOTI_ID = 1392595456453902417
canale_pagelle_id = 1392595613362946110
MAPPA_CLASSE_URL = "https://media.discordapp.net/attachments/1338584360500330608/1405587013205495828/3TK.png?ex=689f5e6a&is=689e0cea&hm=5d1703332b1de6396ee04cdac04c5d30685887c85226fddfae09f2743cbe68cd&=&width=1361&height=777"

# Configurazione Voice Call
VC_FILE = "vc_attive.json"
PREFIX_ESCLUDI_VC = "!"
VIVAVOCE_FILE = "vc_attive.json"

# Dizionario per tenere traccia dei vivavoce attivi in memoria
# Formato: {vc_id: {channel_id: listener_user_id}}
VIVAVOCE_ATTIVI = {}

# Sostituisci con gli ID reali del tuo server
VC_CANALI_ESCLUSI = {
    "canali": ["1334286250873589892", "1334286476678139925", "1333757061930029077","1381747156842713280"], # Esempi
    "categorie": ["948283556306767883", "920814565514698822","1363659937150013440","1333882546076909630","920813592725565520","920813926101434399","1349682159123959818","1347349068283641867","1334123695953674322"] # Esempi
}

# --- CONFIGURAZIONE TUPPER ---
TUPPER_NOMI_FILE = "tupper_nomi.json"

# File per salvare la mappatura utente -> casa
THREAD_CASE_FILE = "thread_case.json"
THREAD_CASE = {} # {user_id: thread_id} - Caricato all'avvio

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
    # Nuova regex che include anche +, ++, -, -- come voti validi
    return re.match(r"^(10 e lode|10|[1-9](\s?e mezzo)?[+-]{0,2}|\++|\-+)(pon)?$", voto) is not None
    
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

# --- FUNZIONI DI UTILITÀ VC ---
def load_vc():
    """Carica le VC attive dal file."""
    if os.path.exists(VC_FILE):
        try:
            with open(VC_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_vc(vc_data):
    """Salva le VC attive nel file."""
    with open(VC_FILE, "w", encoding="utf-8") as f:
        json.dump(vc_data, f, indent=2, ensure_ascii=False)

def genera_vc_id(creatore_id):
    """Genera un ID univoco per la VC."""
    return f"vc_{creatore_id}_{int(time.time())}"

# --- GESTIONE THREAD_CASE (CASA DEGLI UTENTI) ---
def carica_thread_case():
    """Carica la mappatura utente->casa dal file."""
    global THREAD_CASE
    if os.path.exists(THREAD_CASE_FILE):
        try:
            with open(THREAD_CASE_FILE, "r", encoding="utf-8") as f:
                THREAD_CASE = json.load(f)
        except json.JSONDecodeError:
            THREAD_CASE = {}

def salva_thread_case():
    """Salva la mappatura utente->casa su file."""
    with open(THREAD_CASE_FILE, "w", encoding="utf-8") as f:
        json.dump(THREAD_CASE, f, indent=2, ensure_ascii=False)

# --- FUNZIONI DI UTILITÀ PER SELF-MUTE (Persistent) ---
def is_user_self_muted(vc_data_entry, user_id):
    """Controlla se un utente è auto-mutato nella VC (stato persistente)."""
    muted_users = vc_data_entry.get("self_muted_persistent", [])
    return user_id in muted_users

def toggle_self_mute_persistent(vc_data_entry, user_id):
    """Attiva/disattiva il self-mute persistente per un utente nella VC."""
    if "self_muted_persistent" not in vc_data_entry:
        vc_data_entry["self_muted_persistent"] = []
    
    muted_list = vc_data_entry["self_muted_persistent"]
    
    if user_id in muted_list:
        # Già mutato, lo smutiamo
        muted_list.remove(user_id)
       # Rimuovi la chiave se la lista è vuota
        if not muted_list:
            del vc_data_entry["self_muted_persistent"]
        return "unmuted"
    else:
        # Lo mutiamo
        muted_list.append(user_id)
        return "muted"

# --- FUNZIONI DI UTILITÀ PER TUPPER ---
def load_tupper_nomi():
    """Carica la mappatura nome_tupper -> user_id dal file."""
    if os.path.exists(TUPPER_NOMI_FILE):
        try:
            with open(TUPPER_NOMI_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_tupper_nomi(data):
    """Salva la mappatura nome_tupper -> user_id su file."""
    with open(TUPPER_NOMI_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user_id_from_tupper(message_author_name, message_content):
    """
    Cerca di ottenere l'ID utente da un messaggio di tupper.
    Controlla il nome del webhook e il contenuto del messaggio.
    """
    tupper_data = load_tupper_nomi()
    
    # 1. Controlla se il nome del webhook contiene un nome associato
    for nome_tupper, info in tupper_data.items():
        user_id = info["user_id"]
        # Confronto case-insensitive e parziale per maggiore tolleranza
        if nome_tupper.lower() in message_author_name.lower():
            return user_id
            
    # 2. Controlla se il contenuto del messaggio inizia con un nome associato
    # (stile Tupperbox: "NomeTupper: testo" o "[NomeTupper] testo")
    for nome_tupper, info in tupper_data.items():
        user_id = info["user_id"]
        if message_content.lower().startswith(f"{nome_tupper.lower()}:") or \
           message_content.lower().startswith(f"[{nome_tupper.lower()}]"):
            return user_id
            
    return None

def should_ignore_user_message(author_id, message_content):
    """
    Controlla se un messaggio da un utente normale deve essere ignorato
    perché inizia con un prefisso di un tupper associato a quell'utente.
    Adattata per prefissi che vanno direttamente al contenuto, come 'prefisso.testo'.
    """
    user_id = str(author_id)
    tupper_data = load_tupper_nomi()
    
    # Cerca se l'utente ha tupper associati
    for nome_tupper, info in tupper_data.items():
        if info["user_id"] == user_id:
            prefisso = info["prefisso"]
            # Controlla se il messaggio inizia con il prefisso del tupper
            # Modificato per gestire prefissi senza ':' o '[ ]'
            if message_content.startswith(f"{prefisso}"):
                # Opzionale: per evitare falsi positivi (es. prefisso "na" e messaggio "nahi"),
                # si potrebbe aggiungere un controllo sul carattere successivo,
                # ma per ora assumiamo che il prefisso sia unico e seguito dal contenuto.
                return True
    return False

def canale_escluso(channel: discord.TextChannel | discord.Thread) -> bool:
    """Controlla se un canale/thread è nella blacklist."""
    # Controllo diretto sull'ID del canale/thread
    if str(channel.id) in VC_CANALI_ESCLUSI["canali"]:
        return True
    
    # Se è un thread, controlla anche il canale genitore
    if isinstance(channel, discord.Thread):
        if str(channel.parent_id) in VC_CANALI_ESCLUSI["canali"]:
            return True

    # Controllo su categorie (funziona anche per thread)
    if hasattr(channel, 'category_id') and str(channel.category_id) in VC_CANALI_ESCLUSI["categorie"]:
        return True

    return False

# --- CLASSE PER I BOTTONI DI ACCETTAZIONE/RIFIUTO ---
class VCAcceptView(discord.ui.View):
    """View per i bottoni di accettazione/rifiuto della chiamata."""
    def __init__(self, vc_id: str, canale_creazione_id: str):
        super().__init__(timeout=120)
        self.vc_id = vc_id
        self.canale_creazione_id = canale_creazione_id

    @discord.ui.button(label="✅ Accetta", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        vc_data = load_vc()
        vc = vc_data.get(self.vc_id)

        user_id = str(interaction.user.id)
        if user_id not in vc["invitati"] and user_id != vc["creatore"]:
            await interaction.followup.send("❌ Non sei stato invitato a questa chiamata.", ephemeral=True)
            return

        if user_id not in vc["partecipanti"]:
            vc["partecipanti"].append(user_id)
            # NOTA: Non salviamo più automaticamente il canale corrente come casa qui
            # L'utente deve averla già impostata con /imposta_casa
            
            # Invia messaggio temporaneo nel canale
            canale = interaction.guild.get_channel(int(self.canale_creazione_id))
            if canale:
                msg_temp = await canale.send(f"✅ {interaction.user.mention} ha **accettato** la chiamata.")
                await msg_temp.delete(delay=5.0) 

            # Se la VC diventa attiva
            if len(vc["partecipanti"]) >= 2 and vc["stato"] == "in_attesa":
                vc["stato"] = "attiva"
                if canale:
                    msg_attiva = await canale.send(
                        f"📞 **Chiamata ora attiva!**\n"
                        f"Partecipanti: {', '.join([f'<@{uid}>' for uid in vc['partecipanti']])}"
                    )
                    await msg_attiva.delete(delay=10.0) # Messaggio attivazione visibile 10 secondi

        save_vc(vc_data)
        await interaction.followup.send("✅ Hai accettato la chiamata!", ephemeral=True)

    @discord.ui.button(label="❌ Rifiuta", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True) # Risposta immediata all'utente
        vc_data = load_vc()
        vc = vc_data.get(self.vc_id)
        if not vc:
            await interaction.followup.send("❌ Questa chiamata non è più valida.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        if user_id not in vc["invitati"] and user_id != vc["creatore"]:
            await interaction.followup.send("❌ Non sei stato invitato a questa chiamata.", ephemeral=True)
            return

        # Invia messaggio temporaneo nel canale
        canale = interaction.guild.get_channel(int(self.canale_creazione_id))
        if canale:
            msg_temp = await canale.send(f"📞 {interaction.user.mention} ha **rifiutato** la chiamata.")
            await msg_temp.delete(delay=5.0) # Cancella dopo 5 secondi
        
        # Conferma visibile solo all'utente
        await interaction.followup.send("❌ Hai rifiutato la chiamata.", ephemeral=True)

# --- FUNZIONI DI UTILITÀ PER VIVAVOCE ---
def load_vivavoce():
    """Carica le configurazioni dei vivavoce dal file."""
    global VIVAVOCE_ATTIVI
    if os.path.exists(VIVAVOCE_FILE):
        try:
            with open(VIVAVOCE_FILE, "r", encoding="utf-8") as f:
                # Il file salva {vc_id: {channel_id: user_id}}
                # Ma in memoria vogliamo lo stesso per velocità
                data = json.load(f)
                VIVAVOCE_ATTIVI = data
        except (json.JSONDecodeError, KeyError):
            VIVAVOCE_ATTIVI = {}

def save_vivavoce():
    """Salva le configurazioni dei vivavoce su file."""
    with open(VIVAVOCE_FILE, "w", encoding="utf-8") as f:
        json.dump(VIVAVOCE_ATTIVI, f, indent=2, ensure_ascii=False)

def get_vivavoce_channels_for_vc(vc_id):
    """Ottiene i canali in vivavoce per una specifica VC."""
    return VIVAVOCE_ATTIVI.get(vc_id, {})

def set_vivavoce_channel(vc_id, channel_id, user_id):
    """Imposta un canale come 'in vivavoce' per un utente in una VC."""
    if vc_id not in VIVAVOCE_ATTIVI:
        VIVAVOCE_ATTIVI[vc_id] = {}
    VIVAVOCE_ATTIVI[vc_id][str(channel_id)] = str(user_id)
    save_vivavoce()

def remove_vivavoce_channel(vc_id, channel_id):
    """Rimuove un canale dalla lista dei vivavoce per una VC."""
    if vc_id in VIVAVOCE_ATTIVI and str(channel_id) in VIVAVOCE_ATTIVI[vc_id]:
        del VIVAVOCE_ATTIVI[vc_id][str(channel_id)]
        # Se la VC non ha più canali in vivavoce, rimuovila
        if not VIVAVOCE_ATTIVI[vc_id]:
            del VIVAVOCE_ATTIVI[vc_id]
        save_vivavoce()

def is_channel_in_vivavoce(channel_id):
    """Controlla se un canale è attivo in qualche vivavoce."""
    str_channel_id = str(channel_id)
    for vc_channels in VIVAVOCE_ATTIVI.values():
        if str_channel_id in vc_channels:
            return True
    return False

def get_vc_and_listener_for_channel(channel_id):
    """Ottiene la VC e l'utente ascoltatore per un canale in vivavoce."""
    str_channel_id = str(channel_id)
    for vc_id, channels in VIVAVOCE_ATTIVI.items():
        if str_channel_id in channels:
            return vc_id, channels[str_channel_id]
    return None, None
    
    
# --- FUNZIONI DI UTILITÀ PER VIVAVOCE ---
def get_vc_info_and_listener_for_channel(channel_id: int | str):
    """
    Cerca se un canale è in vivavoce per qualche VC attiva.
    Restituisce (vc_info, listener_user_id) se trovato, altrimenti (None, None).
    """
    vc_data = load_vc()
    str_channel_id = str(channel_id)
    
    for vc_id, vc_info in vc_data.items():
        if vc_info.get("stato") == "attiva":
            vivavoce_channels = vc_info.get("vivavoce_channels", {})
            listener_user_id = vivavoce_channels.get(str_channel_id)
            # Verifica che l'ascoltatore sia ancora nella VC
            if listener_user_id and listener_user_id in vc_info.get("partecipanti", []):
                return vc_info, listener_user_id
    return None, None

def set_vivavoce_channel_in_vc_data(vc_id: str, channel_id: str, user_id: str):
    """Imposta un canale come 'in vivavoce' per un utente in una VC, salvando su vc_attive.json."""
    vc_data = load_vc()
    if vc_id in vc_data:
        if "vivavoce_channels" not in vc_data[vc_id]:
            vc_data[vc_id]["vivavoce_channels"] = {}
        vc_data[vc_id]["vivavoce_channels"][channel_id] = user_id
        save_vc(vc_data)
        return True
    return False

def remove_vivavoce_channel_from_vc_data(vc_id: str, channel_id: str):
    """Rimuove un canale dalla lista dei vivavoce per una VC, salvando su vc_attive.json."""
    vc_data = load_vc()
    if vc_id in vc_data:
        vivavoce_channels = vc_data[vc_id].get("vivavoce_channels", {})
        if channel_id in vivavoce_channels:
            del vivavoce_channels[channel_id]
            # Se non ci sono più canali, rimuovi la chiave
            if not vivavoce_channels:
                vc_data[vc_id].pop("vivavoce_channels", None)
            else:
                vc_data[vc_id]["vivavoce_channels"] = vivavoce_channels
            save_vc(vc_data)
            return True
    return False
    
    

# ----------- COMANDI ------------

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

    scaling = (att_stat - def_stat) / 50

    colpito_chance = 0.5 + scaling * 0.2
    bloccata_chance = 0.35 - scaling * 0.2

    colpito_chance = max(0.3, min(colpito_chance, 0.7))
    bloccata_chance = max(0.15, min(bloccata_chance, 0.55))

    mancato_bonus = (110 - att_stat) / 100 * 0.2
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

    if risultato == "Schivata/Bersaglio Mancato":
        schivata_chance = max(0.3, min((def_stat - att_stat) / 50, 0.7))
        mancato_chance = max(0.3, min(mancato_bonus, 0.7))
        sub_result = random.choices(["Schivata", "Bersaglio Mancato"], weights=[schivata_chance, mancato_chance], k=1)[0]
        result_message = f"{sub_result}"
    else:
        result_message = risultato

    await interaction.response.send_message(
        f"🏐 {interaction.user.mention} ha lanciato la palla contro {utente.mention}:\n"
        f"# **{result_message}!**"
    )

@tree.command(name="passaggio", description="Passa la palla a un compagno!")
async def passaggio(interaction: discord.Interaction, utente: discord.Member):
    skills = get_user_skills(interaction.user.id)
    result = weighted_choice(skills["passaggio"], ['Palla passata'] * 4, ['Passaggio intercettato'])
    await interaction.response.send_message(
        f"👟 {interaction.user.mention} prova a passare la palla a {utente.mention}:\n"
        f"# **{result}!**"
    )

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
    await interaction.response.send_message(
        f"⚡ {interaction.user.mention} tenta un dribbling contro {utente.mention}:\n"
        f"# **{result}!**"
    )

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
    await interaction.response.send_message(
            f"🛡️ {interaction.user.mention} prova a contrastare {utente.mention}:\n" 
            f"# **{result}!**"
        )

@tree.command(name="tiro", description="Prova a tirare in porta!")
@app_commands.describe(
    utente="Il portiere da sfidare",
    tipo="Tipo di tiro (opzionale, default: Normale)"
)
@app_commands.choices(tipo=[
    app_commands.Choice(name="Potenza", value="potenza"),
    app_commands.Choice(name="Precisione", value="precisione"),
    app_commands.Choice(name="Pallonetto", value="pallonetto")
])
async def tiro(interaction: discord.Interaction, utente: discord.Member, tipo: app_commands.Choice[str] = None):

    tipo_tiro_value = tipo.value if tipo else "normale"
    
    skills_att = get_user_skills(interaction.user.id)
    skills_por = get_user_skills(utente.id)
    
    stat_att = max(min(skills_att["tiro"], 100), 50)
    stat_por = max(min(skills_por["portiere"], 100), 50)
    base_palo_chance = 0.05
    
    scaling = (stat_att - stat_por) / 50

    base_gol_chance = min(0.65, max(0.35, 0.45 + scaling * 0.2))
    base_parata_chance = min(0.6, max(0.2, 0.35 - scaling * 0.25))

    errore_bonus = (110 - stat_att) / 100 * 0.8

    base_fuori_chance = min(0.4, max(0.05, errore_bonus))
    
    # --- APPLICA MODIFICATORI PER TIPO DI TIRO ---
    if tipo_tiro_value == "potenza":
        gol_chance = min(0.75, max(0.35, 0.35 + scaling * 0.4))
        parata_chance = min(0.3, max(0.1, 0.25 - scaling * 0.2))
        fuori_chance = min(0.65, max(0.05,(110 - stat_att) / 100 * 1.2))
        palo_chance = base_palo_chance * (1.0 - (stat_att - 50) * 0.005)

    elif tipo_tiro_value == "precisione":
        gol_chance = min(0.85, max(0.35, 0.5 + scaling * 0.7))
        parata_chance = min(0.35, max(0.1, 0.25 - scaling * 0.7))
        fuori_chance = min(0.5, max(0.05,(110 - stat_att) / 100 * 0.7))
        palo_chance = base_palo_chance * (1.0 - (stat_att - 50) * 0.007)

    elif tipo_tiro_value == "pallonetto":
        gol_chance = min(0.7, max(0.2, 0.3 + scaling * 0.8))
        parata_chance = min(0.6, max(0.3, 0.25 - scaling * 0.5))
        fuori_chance = min(0.3, max(0.05, errore_bonus))
        palo_chance = base_palo_chance * (1.0 - (stat_att - 50) * 0.009)
        
    else:
        # Usa i valori base
        gol_chance = base_gol_chance
        parata_chance = base_parata_chance
        fuori_chance = base_fuori_chance
        palo_chance = base_palo_chance

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
        
    # --- GESTIONE ESITI ---
    if result == "Palo/Traversa":
        # 66% Palo, 34% Traversa
        sub_result = random.choices(["Palo", "Traversa"], weights=[0.66, 0.34], k=1)[0]
        result_message = f"{sub_result}"
    elif result == "Parata":
        diff_skill = (stat_att - stat_por) / 50
        
        normalized_diff = max(-1.0, min(1.0, diff_skill))

        bloccata_chance = 0.325 - normalized_diff * 0.125
        corta_chance = 0.085 + normalized_diff * 0.065
        fuori_chance = max(0.35, 1.0 - (bloccata_chance + corta_chance))

        totale_parata = bloccata_chance + corta_chance + fuori_chance
        if totale_parata > 1:
            scale_parata = 1 / totale_parata
            bloccata_chance *= scale_parata
            corta_chance *= scale_parata
            fuori_chance *= scale_parata
            
        # Scegli il sottotipo di parata
        sub_result_parata = random.choices(
            ["Bloccata", "Respinta Corta", "Palla Fuori"], 
            weights=[bloccata_chance, corta_chance, fuori_chance], 
            k=1
        )[0]
        
        # --- GESTIONE PALLA FUORI (ANGOLO O RIMESSA) ---
        if sub_result_parata == "Palla Fuori":
            corn_or_throw_in = random.choices(["Calcio d'Angolo", "Rimessa Laterale"], weights=[0.5, 0.5], k=1)[0]
            result_message = f"Parata: {corn_or_throw_in}"
        else:
            result_message = f"Parata: {sub_result_parata}"
        
    else:
        result_message = result

    if tipo:
        await interaction.response.send_message(
            f"⚽ {interaction.user.mention} ha tirato in porta (**{tipo.name}**):\n"
            f"# {result_message}!\n" 
            f"(Portiere: {utente.mention})"
        )
    else:    
        await interaction.response.send_message(
            f"⚽ {interaction.user.mention} ha tirato in porta:\n"
            f"# {result_message}!\n"
            f"(Portiere: {utente.mention})"
        )

@tree.command(name="fallo", description="Decidi se un fallo è da cartellino. Solo per Roleplay Staff.")
async def fallo(interaction: discord.Interaction):
    is_admin = interaction.user.guild_permissions.administrator
    role = discord.utils.get(interaction.user.roles, name="Roleplay Staff")
    if interaction.user.id != owner_id and role is None and not is_admin:
        await interaction.response.send_message("❌ Non hai il permesso per usare questo comando!", ephemeral=True)
        return
    fallo_responses = ['No Cartellino', 'Cartellino Giallo', 'Cartellino Rosso']
    await interaction.response.send_message(f"🟥🟨 Fallo: **{random.choice(fallo_responses)}**")

# --- COMANDO: /crossbar_challenge ---
@tree.command(name="crossbar_challenge", description="Metti alla prova la tua precisione! Tira contro la traversa.")
async def crossbar_challenge(interaction: discord.Interaction):
    """Prova a colpire la traversa!"""
    skills_att = get_user_skills(interaction.user.id)
    
    # Usa la skill "tiro" dell'utente
    stat_att = max(min(skills_att["tiro"], 100), 50)
    scaling = (stat_att - 50) / 50

    traversa_chance = min(0.25, max(0.03, scaling * 0.25))
    gol_chance = min(0.6, max(0.35, 0.4 + scaling * 0.2))
    palo_chance = 0.05
    fuori_chance = 1 - (traversa_chance + gol_chance + palo_chance)

    risultati = ["Traversa", "Gol", "Palo", "Tiro Fuori"]
    weights = [traversa_chance, gol_chance, palo_chance, fuori_chance]
    
    # Estrai il risultato
    result = random.choices(risultati, weights=weights, k=1)[0]

    await interaction.response.send_message(
        f"🎯 **Crossbar Challenge per {interaction.user.mention}!**\n"
        f"# **{result}!**"
    )

@tree.command(name="sorteggio", description="Estrai studenti in modo casuale per la tua materia.")
@app_commands.describe(
    materia="(Solo per il prof di Matematica e Fisica)",
    quanti="Numero di studenti da sorteggiare"
)
@app_commands.choices(materia=[
    app_commands.Choice(name="Matematica", value="matematica"),
    app_commands.Choice(name="Fisica", value="fisica")
])
async def sorteggio(interaction: discord.Interaction, quanti: int, materia: app_commands.Choice[str] = None):
    user_id = str(interaction.user.id)

    # Owner → sempre "test"
    if interaction.user.id == owner_id:
        materia_nome = "test"

    else:
        materie_prof = MATERIE_PER_PROF.get(user_id, [])

        if not materie_prof:
            await interaction.response.send_message("❌ Non hai il permesso per usare questo comando.", ephemeral=True)
            return

        if len(materie_prof) == 1:
            if materia:
                await interaction.response.send_message("❌ Non devi selezionare una materia: ne insegni solo una.", ephemeral=True)
                return
            materia_nome = materie_prof[0]

        elif set(materie_prof) == {"matematica", "fisica"}:
            if not materia:
                await interaction.response.send_message("❌ Devi selezionare **Matematica** o **Fisica** perché insegni entrambe.", ephemeral=True)
                return
            materia_nome = materia.value

    # Carica studenti
    try:
        with open("studenti.json", "r", encoding="utf-8") as f:
            studenti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Errore nel caricamento degli studenti.", ephemeral=True)
        return

    studenti_ids = [str(s["id"]) for s in studenti]

    # Carica estratti
    try:
        with open("estratti.json", "r", encoding="utf-8") as f:
            estratti_per_utente = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        estratti_per_utente = {}

    estratti_per_utente.setdefault(user_id, {}).setdefault(materia_nome, [])

    rimanenti = list(set(studenti_ids) - set(estratti_per_utente[user_id][materia_nome]))
    if len(rimanenti) < quanti:
        estratti_per_utente[user_id][materia_nome].clear()
        rimanenti = list(set(studenti_ids) - set(estratti_per_utente[user_id][materia_nome]))

    scelti = random.sample(rimanenti, quanti)
    estratti_per_utente[user_id][materia_nome].extend(scelti)

    with open("estratti.json", "w", encoding="utf-8") as f:
        json.dump(estratti_per_utente, f, indent=2)

    nome_materia = NOMI_MATERIE.get(materia_nome, materia_nome.capitalize())
    menzioni = [f"<@{uid}>" for uid in scelti]
    await interaction.response.send_message(
        f"Gli studenti sorteggiati per **{nome_materia}** sono:\n" + "\n".join(menzioni)
    )

@tree.command(name="usciti", description="Mostra gli studenti già estratti per una materia.")
@app_commands.describe(
    materia="(Solo per il prof di Matematica e Fisica)",
    admin="Mostra gli estratti di tutti i professori per tutte le materie (solo owner)"
)
@app_commands.choices(materia=[
    app_commands.Choice(name="Matematica", value="matematica"),
    app_commands.Choice(name="Fisica", value="fisica")
])
async def usciti(interaction: discord.Interaction, materia: app_commands.Choice[str] = None, admin: bool = False):
    user_id = str(interaction.user.id)

    # Carica dati
    try:
        with open("estratti.json", "r", encoding="utf-8") as f:
            estratti_per_utente = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        estratti_per_utente = {}

    try:
        with open("studenti.json", "r", encoding="utf-8") as f:
            studenti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Errore nel caricamento degli studenti.", ephemeral=True)
        return

    tutti_studenti_ids = [s["id"] for s in studenti]
    embeds = []

    if admin:
        if interaction.user.id != owner_id:
            await interaction.response.send_message("❌ Solo l'owner può usare l'opzione admin.", ephemeral=True)
            return

        for prof_id, materie in estratti_per_utente.items():
            for materia_key, ids_estratti in materie.items():
                nome_materia = NOMI_MATERIE.get(materia_key, materia_key.capitalize())
                ids_mancanti = [id_ for id_ in tutti_studenti_ids if id_ not in ids_estratti]

                menzioni_estratti = [f"<@{s['id']}>" for s in studenti if s["id"] in ids_estratti]
                menzioni_mancanti = [f"<@{id_}>" for id_ in ids_mancanti]

                embed = discord.Embed(
                    title=f"📚 Estrazioni per {nome_materia}",
                    description=f"Docente: <@{prof_id}>",
                    color=discord.Color.blue()
                )
                if menzioni_estratti:
                    embed.add_field(name=f"✅ {len(menzioni_estratti)} Estratti", value="\n".join(menzioni_estratti), inline=False)
                if menzioni_mancanti:
                    embed.add_field(name=f"🕓 {len(menzioni_mancanti)} Mancanti", value="\n".join(menzioni_mancanti), inline=False)
                embeds.append(embed)

    else:
        # Logica normale (owner → test, prof → dedotta o selezionata)
        if interaction.user.id == owner_id:
            materia_nome = "test"
        else:
            materie_prof = MATERIE_PER_PROF.get(user_id, [])
            if not materie_prof:
                await interaction.response.send_message("❌ Non hai il permesso per usare questo comando.", ephemeral=True)
                return

            if len(materie_prof) == 1:
                if materia:
                    await interaction.response.send_message("❌ Non devi selezionare una materia: ne insegni solo una.", ephemeral=True)
                    return
                materia_nome = materie_prof[0]

            elif set(materie_prof) == {"matematica", "fisica"}:
                if not materia:
                    await interaction.response.send_message("❌ Devi selezionare **Matematica** o **Fisica** perché insegni entrambe.", ephemeral=True)
                    return
                materia_nome = materia.value

        if user_id not in estratti_per_utente or materia_nome not in estratti_per_utente[user_id]:
            await interaction.response.send_message("❌ Nessuno studente è stato ancora estratto per questa materia.", ephemeral=True)
            return

        nome_materia = NOMI_MATERIE.get(materia_nome, materia_nome.capitalize())
        ids_estratti = estratti_per_utente[user_id][materia_nome]
        ids_mancanti = [id_ for id_ in tutti_studenti_ids if id_ not in ids_estratti]

        menzioni_estratti = [f"<@{s['id']}>" for s in studenti if s["id"] in ids_estratti]
        menzioni_mancanti = [f"<@{id_}>" for id_ in ids_mancanti]

        embed = discord.Embed(
            title=f"📚 Estrazioni per {nome_materia}",
            color=discord.Color.green()
        )
        embed.add_field(name=f"✅ {len(menzioni_estratti)} Estratti", value="\n".join(menzioni_estratti) or "Nessuno", inline=False)
        embed.add_field(name=f"🕓 {len(menzioni_mancanti)} Mancanti", value="\n".join(menzioni_mancanti) or "Nessuno", inline=False)
        embeds.append(embed)

    if not embeds:
        await interaction.response.send_message("❌ Nessuno studente è stato ancora estratto.", ephemeral=True)
    else:
        for embed in embeds:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="aggiungi_studente", description="Aggiunge uno studente agli estratti (es. se si offre volontario)")
@app_commands.describe(
    materia="(Solo se il prof ha Matematica e Fisica)",
    studente="Studente da aggiungere (menziona)",
    prof="(Solo owner) Seleziona un prof al posto del quale agire"
)
@app_commands.choices(materia=[
    app_commands.Choice(name="Matematica", value="matematica"),
    app_commands.Choice(name="Fisica", value="fisica")
])
async def aggiungi_studente(
    interaction: discord.Interaction,
    studente: discord.Member,
    materia: app_commands.Choice[str] = None,
    prof: discord.Member | None = None
):
    user_id = str(interaction.user.id)
    studente_id = str(studente.id)

    # Solo l'owner può usare l'opzione prof
    if prof and interaction.user.id != owner_id:
        await interaction.response.send_message("❌ Solo l'owner può usare l'opzione 'prof'.", ephemeral=True)
        return

    # Determina il prof target
    target_id = str(prof.id) if prof else user_id

    # Verifica che il prof sia valido
    materie_prof = MATERIE_PER_PROF.get(target_id)
    if not materie_prof:
        await interaction.response.send_message("❌ Il prof selezionato non ha materie assegnate.", ephemeral=True)
        return

    # Determina la materia
    if len(materie_prof) == 1:
        if materia:
            await interaction.response.send_message("❌ Non devi selezionare una materia: il prof insegna solo una materia.", ephemeral=True)
            return
        materia_nome = materie_prof[0]

    elif set(materie_prof) == {"matematica", "fisica"}:
        if not materia:
            await interaction.response.send_message("❌ Devi selezionare **Matematica** o **Fisica** perché il prof insegna entrambe.", ephemeral=True)
            return
        materia_nome = materia.value

    # Carica estratti
    if os.path.exists(ESTRATTI_FILE):
        with open(ESTRATTI_FILE, "r", encoding="utf-8") as f:
            estratti_per_utente = json.load(f)
    else:
        estratti_per_utente = {}

    estratti_per_utente.setdefault(target_id, {}).setdefault(materia_nome, [])

    if studente_id in estratti_per_utente[target_id][materia_nome]:
        nome_materia = NOMI_MATERIE.get(materia_nome, materia_nome.capitalize())
        await interaction.response.send_message(
            f"{studente.mention} è già presente negli estratti per **{nome_materia}**.", ephemeral=True
        )
        return

    estratti_per_utente[target_id][materia_nome].append(studente_id)

    with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
        json.dump(estratti_per_utente, f, indent=2)

    nome_materia = NOMI_MATERIE.get(materia_nome, materia_nome.capitalize())
    await interaction.response.send_message(
        f"{studente.mention} è stato aggiunto agli estratti di **{nome_materia}**.", ephemeral=True
    )

@tree.command(name="rimuovi_studente", description="Rimuove uno studente dagli estratti di una materia")
@app_commands.describe(
    materia="(Solo se il prof ha Matematica e Fisica)",
    studente="Studente da rimuovere (menziona)",
    prof="(Solo owner) Seleziona un prof al posto del quale agire"
)
@app_commands.choices(materia=[
    app_commands.Choice(name="Matematica", value="matematica"),
    app_commands.Choice(name="Fisica", value="fisica")
])
async def rimuovi_studente(
    interaction: discord.Interaction,
    studente: discord.Member,
    materia: app_commands.Choice[str] = None,
    prof: discord.Member | None = None
):
    user_id = str(interaction.user.id)
    studente_id = str(studente.id)

    # Solo l'owner può usare l'opzione prof
    if prof and interaction.user.id != owner_id:
        await interaction.response.send_message("❌ Solo l'owner può usare l'opzione 'prof'.", ephemeral=True)
        return

    # Determina il prof target
    target_id = str(prof.id) if prof else user_id

    # Verifica che il prof sia valido
    materie_prof = MATERIE_PER_PROF.get(target_id)
    if not materie_prof:
        await interaction.response.send_message("❌ Il prof selezionato non ha materie assegnate.", ephemeral=True)
        return

    # Determina la materia
    if len(materie_prof) == 1:
        if materia:
            await interaction.response.send_message("❌ Non devi selezionare una materia: il prof insegna solo una materia.", ephemeral=True)
            return
        materia_nome = materie_prof[0]

    elif set(materie_prof) == {"matematica", "fisica"}:
        if not materia:
            await interaction.response.send_message("❌ Devi selezionare **Matematica** o **Fisica** perché il prof insegna entrambe.", ephemeral=True)
            return
        materia_nome = materia.value

    else:
        await interaction.response.send_message("❌ Questo comando è riservato ai prof con una sola materia o a chi insegna Matematica/Fisica.", ephemeral=True)
        return

    # Carica estratti
    try:
        with open(ESTRATTI_FILE, "r", encoding="utf-8") as f:
            estratti_per_utente = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        estratti_per_utente = {}

    if target_id not in estratti_per_utente or materia_nome not in estratti_per_utente[target_id]:
        await interaction.response.send_message("❌ Nessuno studente è stato ancora estratto per questa materia.", ephemeral=True)
        return

    if studente_id not in estratti_per_utente[target_id][materia_nome]:
        await interaction.response.send_message("❌ Questo studente non è presente negli estratti.", ephemeral=True)
        return

    estratti_per_utente[target_id][materia_nome].remove(studente_id)

    with open(ESTRATTI_FILE, "w", encoding="utf-8") as f:
        json.dump(estratti_per_utente, f, indent=2)

    nome_materia = NOMI_MATERIE.get(materia_nome, materia_nome.capitalize())
    await interaction.response.send_message(
        f"{studente.mention} è stato rimosso dagli estratti di **{nome_materia}**.", ephemeral=True
    )

@tree.command(name="voti", description="Mostra i voti che hai ricevuto e le materie mancanti.")
@app_commands.describe(materia="(Opzionale) Filtra per una materia specifica")
@app_commands.choices(materia=[
    app_commands.Choice(name="Matematica", value="matematica"),
    app_commands.Choice(name="Fisica", value="fisica"),
    app_commands.Choice(name="Musica", value="musica"),
    app_commands.Choice(name="Educazione Sessuale", value="ed_sessuale"),
    app_commands.Choice(name="Inglese", value="inglese"),
    app_commands.Choice(name="Scienze", value="scienze"),
    app_commands.Choice(name="Storia", value="storia"),
    app_commands.Choice(name="Italiano", value="italiano"),
    app_commands.Choice(name="Arte", value="arte")
])
async def voti(interaction: discord.Interaction, materia: app_commands.Choice[str] = None):
    user_id = str(interaction.user.id)

    FIGLI_PER_GENITORE = {
        "477766915096313867": ["Balloon Boy"],
        "833442585078005811": ["Chica"],
        "1186449740485890158": ["Glamrock Freddy"],
        "922092338317258802": ["Nia"],
        "899238122955636736": ["Pneuma"],
        "742745224006074490": ["Spinni", "Storo"],
        "1021504899680313426": ["Zeke"],
        "899235691651825665": ["Pneuma"]
    }

    materie_mappate = {
        "matematica": "Matematica",
        "fisica": "Fisica",
        "musica": "Musica",
        "ed_sessuale": "Educazione Sessuale",
        "inglese": "Inglese",
        "scienze": "Scienze",
        "storia": "Storia",
        "italiano": "Italiano",
        "arte": "Arte"
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

    genitore_extra = {"477766915096313867", "899235691651825665"}
    is_genitore = any(role.name == "Genitore" for role in interaction.user.roles) or user_id in genitore_extra

    if is_genitore:
        nomi_figli = FIGLI_PER_GENITORE.get(user_id)
        if not nomi_figli:
            await interaction.response.send_message("❌ Non sei associato ad alcuno studente registrato.", ephemeral=True)
            return

        await interaction.response.send_message("👨‍👧‍👦 Ecco i voti dei tuoi figli:", ephemeral=True)

        for nome_studente in nomi_figli:
            voti_studente = voti.get(nome_studente, {})
            embed = discord.Embed(title=f"📚 Voti di {nome_studente}", color=discord.Color.blue())

            if materia:
                materia_key = materia.value
                voti_materia = voti_studente.get(materia_key, [])
                if not voti_materia:
                    embed.add_field(name="❌ Nessun voto", value=f"Nessun voto trovato in {materie_mappate[materia_key]}.", inline=False)
                else:
                    dettagli = []
                    for v in voti_materia:
                        riga = f"Voto: **{v['voto']}**"
                        if v.get("argomento"):
                            riga += f"\nArgomento: **{v['argomento']}**"
                        if v.get("commento"):
                            riga += f"\nCommento: **{v['commento']}**"
                        dettagli.append(riga)
                    embed.add_field(name=f"📘 {materie_mappate[materia_key]}", value="\n".join(dettagli), inline=False)
            else:
                materie_con_voti = set(voti_studente.keys())
                materie_possibili = set(materie_mappate.keys())
                materie_mancanti = materie_possibili - materie_con_voti

                if materie_con_voti:
                    voti_text = "\n".join(
                        f"**{materie_mappate[m]}** → {', '.join(f"**{v['voto']}**" for v in voti_studente[m])}"
                        for m in materie_con_voti
                    )
                    embed.add_field(name="✅ Voti ricevuti", value=voti_text, inline=False)

                if materie_mancanti:
                    mancanti_text = "\n".join(materie_mappate[m] for m in materie_mancanti)
                    embed.add_field(name="🕓 Materie senza voti", value=mancanti_text, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)

    else:
        studente = next((s for s in studenti if s["id"] == user_id), None)
        if not studente:
            await interaction.response.send_message("❌ Non sei registrato nel file studenti.json.", ephemeral=True)
            return

        nome_studente = studente["nome"]
        voti_studente = voti.get(nome_studente, {})
        embed = discord.Embed(title="📚 I tuoi voti", color=discord.Color.blue())

        if materia:
            materia_key = materia.value
            voti_materia = voti_studente.get(materia_key, [])
            if not voti_materia:
                embed.add_field(name="❌ Nessun voto", value=f"Nessun voto trovato in {materie_mappate[materia_key]}.", inline=False)
            else:
                dettagli = []
                for v in voti_materia:
                    riga = f"Voto: **{v['voto']}**"
                    if v.get("argomento"):
                        riga += f"\nArgomento: **{v['argomento']}**"
                    if v.get("commento"):
                        riga += f"\nCommento: **{v['commento']}**"
                    dettagli.append(riga)
                embed.add_field(name=f"📘 {materie_mappate[materia_key]}", value="\n".join(dettagli), inline=False)
        else:
            materie_con_voti = set(voti_studente.keys())
            materie_possibili = set(materie_mappate.keys())
            materie_mancanti = materie_possibili - materie_con_voti

            if materie_con_voti:
                voti_text = "\n".join(
                    f"**{materie_mappate[m]}** → {', '.join(f"**{v['voto']}**" for v in voti_studente[m])}"
                    for m in materie_con_voti
                )
                embed.add_field(name="✅ Voti ricevuti", value=voti_text, inline=False)

            if materie_mancanti:
                mancanti_text = "\n".join(materie_mappate[m] for m in materie_mancanti)
                embed.add_field(name="🕓 Materie senza voti", value=mancanti_text, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
    
@tree.command(name="assegna_voto", description="Assegna un voto a uno studente.")
@app_commands.describe(
    studente="Studente da valutare",
    materia="(Solo se il prof ha Matematica e Fisica)",
    voto="Voto da assegnare",
    argomento="Argomento (opzionale)",
    commento="Commento (opzionale)",
    prof="(Solo owner) Seleziona un prof al posto del quale assegnare il voto"
)
@app_commands.choices(
    materia=[
        app_commands.Choice(name="Matematica", value="matematica"),
        app_commands.Choice(name="Fisica", value="fisica")
    ]
)
async def assegna_voto(
    interaction: discord.Interaction,
    studente: discord.Member,
    voto: str,
    materia: app_commands.Choice[str] = None,
    argomento: str = None,
    commento: str = None,
    prof: discord.Member | None = None
):
    user_id = str(interaction.user.id)
    studente_id = str(studente.id)

    # Solo l'owner può usare l'opzione prof
    if prof and interaction.user.id != owner_id:
        await interaction.response.send_message("❌ Solo l'owner può usare l'opzione 'prof'.", ephemeral=True)
        return

    # Determina il prof target
    target_id = str(prof.id) if prof else user_id

    # Verifica che il prof sia valido
    materie_prof = MATERIE_PER_PROF.get(target_id)
    if not materie_prof:
        await interaction.response.send_message("❌ Il prof selezionato non ha materie assegnate.", ephemeral=True)
        return

    # Determina la materia
    if len(materie_prof) == 1:
        if materia:
            await interaction.response.send_message("❌ Non devi selezionare una materia: il prof insegna solo una materia.", ephemeral=True)
            return
        materia_nome = materie_prof[0]

    elif set(materie_prof) == {"matematica", "fisica"}:
        if not materia:
            await interaction.response.send_message("❌ Devi selezionare **Matematica** o **Fisica** perché il prof insegna entrambe.", ephemeral=True)
            return
        materia_nome = materia.value

    # Verifica che il voto sia valido
    if not voto_valido(voto):
        await interaction.response.send_message("❌ Formato voto non valido!", ephemeral=True)
        return

    # Trova il nome dello studente
    nome_studente = trova_nome_studente(studente_id)
    if not nome_studente:
        await interaction.response.send_message("❌ Questo studente non è registrato nel file studenti.json.", ephemeral=True)
        return

    # Carica voti
    try:
        with open("voti.json", "r", encoding="utf-8") as f:
            voti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        voti = {}

    voti.setdefault(nome_studente, {}).setdefault(materia_nome, []).append({
        "voto": voto,
        "argomento": argomento,
        "commento": commento
    })

    with open("voti.json", "w", encoding="utf-8") as f:
        json.dump(voti, f, indent=2)

    # Determina il genere dello studente
    genere = leggi_genere(studente_id)
    nome_materia = NOMI_MATERIE.get(materia_nome, materia_nome.capitalize())

    canale_voti = interaction.guild.get_channel(CANALE_VOTI_ID) or interaction.guild.get_thread(CANALE_VOTI_ID)
    if canale_voti is None:
        await interaction.response.send_message("❌ Errore: Il canale voti non è stato trovato.", ephemeral=True)
        return

    embed = discord.Embed(title="📢 Valutazione aggiornata!", color=discord.Color.green())
    embed.add_field(name=f"{genere}:", value=f"<@{studente_id}>", inline=False)
    embed.add_field(name="Materia:", value=f"**{nome_materia}**", inline=False)
    embed.add_field(name="Voto:", value=f"**{voto}**", inline=False)
    embed.add_field(name="Insegnante:", value=f"<@{target_id}>", inline=False)

    if argomento:
        embed.add_field(name="Argomento:", value=argomento, inline=False)
    if commento:
        embed.add_field(name="Commento:", value=commento, inline=False)

    await canale_voti.send(embed=embed)
    await interaction.response.send_message(
        f"✅ Nuovo voto **{voto}** registrato per **{nome_studente}** in **{nome_materia}**.",
        ephemeral=True
    )

@tree.command(name="valutati", description="Mostra gli studenti che hanno ricevuto voti e i relativi voti.")
@app_commands.describe(
    materia="(Solo se il prof ha Matematica e Fisica)",
    studente="(Opzionale) Mostra solo i voti di uno studente specifico",
    prof="(Solo owner) Seleziona un prof al posto del quale visualizzare"
)
@app_commands.choices(
    materia=[
        app_commands.Choice(name="Matematica", value="matematica"),
        app_commands.Choice(name="Fisica", value="fisica")
    ]
)
async def valutati(
    interaction: discord.Interaction,
    materia: app_commands.Choice[str] = None,
    studente: discord.Member = None,
    prof: discord.Member | None = None
):
    user_id = str(interaction.user.id)

    if prof and interaction.user.id != owner_id:
        await interaction.response.send_message("❌ Solo l'owner può usare l'opzione 'prof'.", ephemeral=True)
        return

    target_id = str(prof.id) if prof else user_id
    materie_prof = MATERIE_PER_PROF.get(target_id)

    if not materie_prof:
        await interaction.response.send_message("❌ Il prof selezionato non ha materie assegnate.", ephemeral=True)
        return

    if len(materie_prof) == 1:
        if materia:
            await interaction.response.send_message("❌ Non devi selezionare una materia: il prof insegna solo una materia.", ephemeral=True)
            return
        materia_key = materie_prof[0]

    elif set(materie_prof) == {"matematica", "fisica"}:
        if not materia:
            await interaction.response.send_message("❌ Devi selezionare **Matematica** o **Fisica** perché il prof insegna entrambe.", ephemeral=True)
            return
        materia_key = materia.value

    try:
        with open("voti.json", "r", encoding="utf-8") as f:
            voti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Nessun voto registrato.", ephemeral=True)
        return

    try:
        with open(STUDENTI_FILE, "r", encoding="utf-8") as f:
            studenti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Errore nel caricamento degli studenti.", ephemeral=True)
        return

    studenti_da_mostrare = []
    if studente:
        nome_studente = trova_nome_studente(str(studente.id))
        if not nome_studente:
            await interaction.response.send_message("❌ Studente non trovato nel file studenti.json.", ephemeral=True)
            return
        studenti_da_mostrare = [nome_studente]
    else:
        studenti_da_mostrare = list(voti.keys())

    embed = discord.Embed(
        title=f"📊 Voti in {NOMI_MATERIE.get(materia_key, materia_key.capitalize())}",
        color=discord.Color.blue()
    )

    studenti_trovati = False

    if studente:  # Dettagli completi per uno studente
        nome_studente = trova_nome_studente(str(studente.id))
        materie_voti = voti.get(nome_studente, {})
        studente_id = str(studente.id)
        genere = leggi_genere(studente_id)
        tag_studente = f"<@{studente_id}>"

        voti_materia = materie_voti.get(materia_key, [])
        if voti_materia:
            studenti_trovati = True
            dettagli = []
            for v in voti_materia:
                riga = f"Voto: **{v['voto']}**"
                if v.get("argomento"):
                    riga += f"\nArgomento: **{v['argomento']}**"
                if v.get("commento"):
                    riga += f"\nCommento: **{v['commento']}**"
                dettagli.append(riga)
            embed.add_field(name=genere, value=f"{tag_studente}\n" + "\n".join(dettagli), inline=False)

    else:  # Sintesi compatta per tutti
        righe = []
        for nome_studente in studenti_da_mostrare:
            materie_voti = voti.get(nome_studente, {})
            studente_id = next((s["id"] for s in studenti if s["nome"] == nome_studente), None)
            tag_studente = f"<@{studente_id}>" if studente_id else nome_studente
            voti_materia = materie_voti.get(materia_key, [])
            if voti_materia:
                studenti_trovati = True
                voti_sintetici = ", ".join(f"**{v['voto']}**" for v in voti_materia)
                righe.append(f"{tag_studente}: {voti_sintetici}")

        if righe:
            embed.add_field(name="Studenti valutati", value="\n".join(righe), inline=False)

    if not studenti_trovati:
        await interaction.response.send_message("❌ Nessuno studente ha ricevuto voti in questa materia.", ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="imposta_pagella", description="Inserisci un voto da pagella per uno studente.")
@app_commands.describe(
    studente="Studente da valutare",
    materia="Materia della valutazione",
    voto="Voto da inserire (es. 6, 7, Buono, Ottimo...)"
)
@app_commands.choices(materia=[
    app_commands.Choice(name="Italiano", value="italiano"),
    app_commands.Choice(name="Matematica", value="matematica"),
    app_commands.Choice(name="Fisica", value="fisica"),
    app_commands.Choice(name="Inglese", value="inglese"),
    app_commands.Choice(name="Storia", value="storia"),
    app_commands.Choice(name="Scienze", value="scienze"),
    app_commands.Choice(name="Ed. Sessuale", value="ed_sessuale"),
    app_commands.Choice(name="Arte", value="arte"),
    app_commands.Choice(name="Musica", value="musica"),
    app_commands.Choice(name="Filosofia", value="filosofia"),
    app_commands.Choice(name="Motoria", value="motoria"),
    app_commands.Choice(name="Religione", value="religione"),
    app_commands.Choice(name="Condotta", value="condotta")
])
async def imposta_pagella(interaction: discord.Interaction, studente: discord.Member, materia: app_commands.Choice[str], voto: str):
    user_id = str(interaction.user.id)
    materia_nome = materia.value
    studente_id = str(studente.id)

    # Gestione speciale per "condotta"
    if materia_nome == "condotta":
        ruolo_capo = discord.utils.get(interaction.user.roles, name="Capo Professore")
        if interaction.user.id != owner_id and ruolo_capo is None:
            await interaction.response.send_message("❌ Solo la Capo Prof.ssa o l'owner può inserire il voto di condotta.", ephemeral=True)
            return
    else:
        # Verifica permessi normali
        ruolo_capo = discord.utils.get(interaction.user.roles, name="Capo Professore")
        if interaction.user.id != owner_id and (user_id not in MATERIE_PER_PROF or materia_nome not in MATERIE_PER_PROF[user_id]) and ruolo_capo is None:
            await interaction.response.send_message("❌ Non puoi inserire voti per questa materia.", ephemeral=True)
            return

    # Trova il nome dello studente
    nome_studente = trova_nome_studente(studente_id)
    if not nome_studente:
        await interaction.response.send_message("❌ Questo studente non è registrato.", ephemeral=True)
        return

    # Carica o crea il file pagelle.json
    try:
        with open("pagelle.json", "r", encoding="utf-8") as f:
            pagelle = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pagelle = {}

    pagelle.setdefault(nome_studente, {})[materia_nome] = voto

    with open("pagelle.json", "w", encoding="utf-8") as f:
        json.dump(pagelle, f, indent=2)

    await interaction.response.send_message(
        f"✅ Hai inserito **{voto}** in **{materia.name}** per **{nome_studente}**.", ephemeral=True
    )

@tree.command(name="pagella_test", description="Mostra l'anteprima della pagella di uno studente con media calcolata.")
@app_commands.describe(studente="Studente di cui visualizzare la pagella", mostra="(Opzionale) Scegli se mostrare la pagella a tutti")
async def pagella_test(interaction: discord.Interaction, studente: discord.Member, mostra: bool = False):
    user_id = str(interaction.user.id)
    studente_id = str(studente.id)

    # Solo prof o owner possono usare questo comando
    ruolo_capo = discord.utils.get(interaction.user.roles, name="Capo Professore")
    if interaction.user.id != owner_id and ruolo_capo is None:
        await interaction.response.send_message("❌ Solo la capo prof.ssa può vedere l'anteprima della pagella.", ephemeral=True)
        return

    nome_studente = trova_nome_studente(studente_id)
    if not nome_studente:
        await interaction.response.send_message("❌ Studente non trovato.", ephemeral=True)
        return

    try:
        with open("pagelle.json", "r", encoding="utf-8") as f:
            pagelle = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Nessuna pagella trovata.", ephemeral=True)
        return

    voti_studente = pagelle.get(nome_studente)
    if not voti_studente:
        await interaction.response.send_message("❌ Nessuna pagella trovata per questo studente.", ephemeral=True)
        return

    # Calcolo media numerica (esclude religione e condotta)
    materie_escluse = {"religione", "condotta"}
    voti_numerici = []
    for materia, voto in voti_studente.items():
        if materia in materie_escluse:
            continue
        try:
            voti_numerici.append(float(voto))
        except ValueError:
            continue  # Ignora voti non numerici

    media = round(sum(voti_numerici) / len(voti_numerici), 2) if voti_numerici else "N/A"

    embed = discord.Embed(title=f"📄 Anteprima Pagella di {nome_studente}", color=discord.Color.gold())
    for materia_key in ORDINE_MATERIE:
        nome_materia = NOMI_MATERIE.get(materia_key, materia_key.capitalize())
        voto = voti_studente.get(materia_key, "N/A")
        embed.add_field(name=nome_materia, value=str(voto), inline=True)

    embed.add_field(name="📊 Media", value=str(media), inline=False)

    if mostra:
        await interaction.response.send_message(embed=embed, ephemeral=False)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="conferma_pagella", description="Conferma la pagella di uno studente e calcola il voto finale.")
@app_commands.describe(
    studente="Studente di cui confermare la pagella",
    voto_finale="Voto finale (es. 6, 7, 8...)",
    esito="Esito finale (es. PROMOSSO/A)"
)
async def conferma_pagella(interaction: discord.Interaction, studente: discord.Member, voto_finale: str, esito: str):
    user_id = str(interaction.user.id)
    studente_id = str(studente.id)

    # Solo owner o capo prof.ssa (motoria)
    prof_motoria_id = next((uid for uid, materie in MATERIE_PER_PROF.items() if "motoria" in materie), None)
    if user_id != str(owner_id) and user_id != prof_motoria_id:
        await interaction.response.send_message("❌ Solo l'owner o la capo prof.ssa può confermare una pagella.", ephemeral=True)
        return

    nome_studente = trova_nome_studente(studente_id)
    if not nome_studente:
        await interaction.response.send_message("❌ Studente non trovato.", ephemeral=True)
        return

    try:
        with open("pagelle.json", "r", encoding="utf-8") as f:
            pagelle = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Nessuna pagella trovata.", ephemeral=True)
        return

    voti_studente = pagelle.get(nome_studente)
    if not voti_studente:
        await interaction.response.send_message("❌ Nessuna pagella trovata per questo studente.", ephemeral=True)
        return

    # Calcolo media numerica (esclude religione e condotta)
    materie_escluse = {"religione", "condotta"}
    voti_numerici = []
    for materia, voto in voti_studente.items():
        if materia in materie_escluse:
            continue
        try:
            voti_numerici.append(float(voto))
        except ValueError:
            continue  # Ignora voti non numerici

    media = round(sum(voti_numerici) / len(voti_numerici), 2) if voti_numerici else "N/A"

    # Costruzione embed
    embed = discord.Embed(
        title=f"📄 Pagella di {nome_studente}",
        color=discord.Color.gold()
    )
    for materia, voto in voti_studente.items():
        nome_materia = NOMI_MATERIE.get(materia, materia.capitalize())
        embed.add_field(name=nome_materia, value=voto, inline=True)


    embed.add_field(name="📊 Media", value=str(media), inline=False)
    embed.add_field(name="🏅 Voto Finale", value=voto_finale, inline=True)
    embed.add_field(name="📘 Esito", value=esito, inline=True)

    canale_pagelle = interaction.guild.get_channel(canale_pagelle_id) or interaction.guild.get_thread(canale_pagelle_id)
    if canale_pagelle:
        await canale_pagelle.send(embed=embed)
        await interaction.response.send_message("✅ Pagella confermata e pubblicata!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Canale pagelle non trovato.", ephemeral=True)

    # Rimuove voti da voti.json
    try:
        with open("voti.json", "r", encoding="utf-8") as f:
            voti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        voti = {}

    if nome_studente in voti:
        del voti[nome_studente]
        with open("voti.json", "w", encoding="utf-8") as f:
            json.dump(voti, f, indent=2)

    # (Facoltativo) Salva la pagella confermata
    try:
        with open("pagelle_confermate.json", "r", encoding="utf-8") as f:
            archivio = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        archivio = {}

    archivio[nome_studente] = {
        "voti": voti_studente,
        "media": media,
        "voto_finale": voto_finale,
        "esito": esito
    }

    with open("pagelle_confermate.json", "w", encoding="utf-8") as f:
        json.dump(archivio, f, indent=2)

    # Rimuove la pagella temporanea
    del pagelle[nome_studente]
    with open("pagelle.json", "w", encoding="utf-8") as f:
        json.dump(pagelle, f, indent=2)
        
@tree.command(name="pagella", description="Mostra la pagella confermata dello studente.")
@app_commands.describe(mostra="(Opzionale) Scegli se mostrare la pagella a tutti")
async def pagella(interaction: discord.Interaction, mostra: bool = False):
    user_id = str(interaction.user.id)

    FIGLI_PER_GENITORE = {
        "477766915096313867": ["Balloon Boy"],
        "833442585078005811": ["Chica"],
        "1186449740485890158": ["Glamrock Freddy"],
        "922092338317258802": ["Nia"],
        "899238122955636736": ["Pneuma"],
        "742745224006074490": ["Spinni", "Storo"],
        "1021504899680313426": ["Zeke"],
        "899235691651825665": ["Pneuma"]
    }

    try:
        with open("pagelle_confermate.json", "r", encoding="utf-8") as f:
            pagelle = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Nessuna pagella confermata trovata.", ephemeral=True)
        return

    try:
        with open(STUDENTI_FILE, "r", encoding="utf-8") as f:
            studenti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Errore nel caricamento degli studenti.", ephemeral=True)
        return

    genitore_extra = {"477766915096313867", "899235691651825665"}
    is_genitore = any(role.name == "Genitore" for role in interaction.user.roles) or user_id in genitore_extra

    if is_genitore:
        nomi_figli = FIGLI_PER_GENITORE.get(user_id)
        if not nomi_figli:
            await interaction.response.send_message("❌ Non sei associato ad alcuno studente registrato.", ephemeral=True)
            return

        await interaction.response.send_message("📘 Ecco le pagelle confermate dei tuoi figli:", ephemeral=True)

        for nome_studente in nomi_figli:
            pagella_studente = pagelle.get(nome_studente)
            if not pagella_studente:
                await interaction.followup.send(f"❌ Nessuna pagella confermata per **{nome_studente}**.", ephemeral=True)
                continue

            embed = discord.Embed(
                title=f"📄 Pagella di {nome_studente}",
                color=discord.Color.gold()
            )
            for materia, voto in pagella_studente["voti"].items():
                nome_materia = NOMI_MATERIE.get(materia, materia.capitalize())
                embed.add_field(name=nome_materia, value=voto, inline=True)

            embed.add_field(name="📊 Media", value=str(pagella_studente["media"]), inline=False)
            embed.add_field(name="🏅 Voto Finale", value=pagella_studente["voto_finale"], inline=True)
            embed.add_field(name="📘 Esito", value=pagella_studente["esito"], inline=True)

            await interaction.followup.send(embed=embed, ephemeral=not mostra)

    else:
        studente = next((s for s in studenti if s["id"] == user_id), None)
        if not studente:
            await interaction.response.send_message("❌ Non sei registrato nel file studenti.json.", ephemeral=True)
            return

        nome_studente = studente["nome"]
        pagella_studente = pagelle.get(nome_studente)
        if not pagella_studente:
            await interaction.response.send_message("❌ Nessuna pagella confermata trovata per te.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=not mostra)

        embed = discord.Embed(
            title=f"📄 La tua pagella",
            color=discord.Color.gold()
        )
        for materia, voto in pagella_studente["voti"].items():
            nome_materia = NOMI_MATERIE.get(materia, materia.capitalize())
            embed.add_field(name=nome_materia, value=voto, inline=True)

        embed.add_field(name="📊 Media", value=str(pagella_studente["media"]), inline=False)
        embed.add_field(name="🏅 Voto Finale", value=pagella_studente["voto_finale"], inline=True)
        embed.add_field(name="📘 Esito", value=pagella_studente["esito"], inline=True)

        await interaction.followup.send(embed=embed, ephemeral=not mostra)
        
@tree.command(name="appello", description="Mostra l'appello numerato degli studenti con tag, genere e totale.")
async def appello(interaction: discord.Interaction):
    try:
        with open(STUDENTI_FILE, "r", encoding="utf-8") as f:
            studenti = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await interaction.response.send_message("❌ Errore nel caricamento degli studenti.", ephemeral=True)
        return

    if not studenti:
        await interaction.response.send_message("❌ Nessuno studente trovato.", ephemeral=True)
        return

    studenti_ordinati = sorted(studenti, key=lambda s: s.get("nome", "").lower())
    righe = []

    for i, studente in enumerate(studenti_ordinati, start=1):
        studente_id = studente.get("id")
        genere_raw = studente.get("genere", "m").lower()
        genere = "M" if genere_raw == "m" else "F"
        tag_studente = f"<@{studente_id}>"
        riga = f"{i}. {tag_studente} ({genere})"
        righe.append(riga)

    righe.append(f"\n👥 Totale studenti: **{len(studenti_ordinati)}**")

    embed = discord.Embed(
        title="📋 Appello studenti",
        description="\n".join(righe),
        color=discord.Color.teal()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)
    
@tree.command(name="posti_classe", description="Mostra i posti in aula.")
async def posti_classe(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Mappa dei posti in aula",
        description="Ecco dove si trovano gli studenti in classe!",
        color=discord.Color.orange()
    )
    embed.set_image(url=MAPPA_CLASSE_URL)

    await interaction.response.send_message(embed=embed, ephemeral=True) 
    
@tree.command(name="orario", description="Mostra l'orario della classe 3TK come immagine.")
async def orario(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📘 Orario settimanale — Classe 3TK",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://files.catbox.moe/mlwius.png")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- COMANDI VC ---
@tree.command(name="vc_create", description="Crea una chiamata testuale con altri utenti.")
@app_commands.describe(
    partecipanti="Utenti da invitare (es. @user1 @user2)",
    motivo="Motivo della chiamata (opzionale)"
)
async def vc_create(interaction: discord.Interaction, partecipanti: str, motivo: str = "Nessun motivo"):
    user_ids = re.findall(r"<@!?(\d+)>", partecipanti)
    
    carica_thread_case()
    
    if not user_ids:
        await interaction.response.send_message("❌ Menziona almeno un utente da invitare.", ephemeral=True)
        return

    vc_id = genera_vc_id(interaction.user.id)
    vc_data = load_vc()
    vc_data[vc_id] = {
        "creatore": str(interaction.user.id),
        "partecipanti": [str(interaction.user.id)],
        "stato": "in_attesa",
        "motivo": motivo,
        "canale_creazione": str(interaction.channel.id),
        "invitati": user_ids
    }
    save_vc(vc_data)

    embed = discord.Embed(
        title="📞 Nuova Chiamata in Arrivo!",
        description=(
            f"**Creatore:** {interaction.user.mention}\n"
            f"**Motivo:** {motivo}\n\n"
            f"**Invitati:** {', '.join([f'<@{uid}>' for uid in user_ids])}\n\n"
            f"_Clicca uno dei bottoni qui sotto per partecipare._"
        ),
        color=discord.Color.blue()
    )

    view = VCAcceptView(vc_id, str(interaction.channel.id))
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="imposta_casa", description="Imposta il thread/canale corrente come la tua 'casa' per le VC.")
async def imposta_casa(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    channel_id = str(interaction.channel.id)
    carica_thread_case()
    
    THREAD_CASE[user_id] = channel_id
    salva_thread_case()
    
    await interaction.response.send_message(
        f"✅ Il canale/thread {interaction.channel.mention} è stato impostato come la tua 'casa' per le chiamate!",
        ephemeral=True
    )

@tree.command(name="vc_end", description="Termina una chiamata attiva (solo il creatore).")
async def vc_end(interaction: discord.Interaction):
    """Termina una chiamata attiva (solo il creatore)."""
    user_id = str(interaction.user.id)
    vc_data = load_vc()
    
    # Cerca una VC attiva creata dall'utente
    vc_to_end = None
    vc_id_to_end = None
    for vc_id, data in vc_data.items():
        if data["creatore"] == user_id and data["stato"] == "attiva":
            vc_to_end = data
            vc_id_to_end = vc_id
            break
    
    if not vc_to_end:
        await interaction.response.send_message(
            "❌ Non hai nessuna chiamata attiva creata da te da terminare.",
            ephemeral=True
        )
        return

    # Termina la VC
    vc_to_end["stato"] = "terminata"
    motivo = vc_to_end.get("motivo", "Nessun motivo")
    save_vc(vc_data)

    # Notifica tutti i partecipanti nei loro thread casa
    notifica_msg = f"📞 La chiamata è stata **terminata** da {interaction.user.mention}."
    embed_notifica = discord.Embed(
        title="📞 Chiamata Terminata",
        description=notifica_msg,
        color=discord.Color.red()
    )

    # Invia il messaggio di terminazione nel canale di creazione e cancellalo dopo
    canale_creazione = interaction.guild.get_channel(int(vc_to_end["canale_creazione"]))
    if canale_creazione:
        msg_terminata = await canale_creazione.send(embed=embed_notifica)
        await msg_terminata.delete(delay=10.0)

    # 2. Invia messaggio NEI THREAD CASA dei partecipanti (che si cancella subito o dopo poco)
    notifica_msg = f"📞 La chiamata è stata terminata."
    for participant_id in vc_to_end["partecipanti"]:
        try:
            thread_id = THREAD_CASE.get(participant_id)
            if thread_id:
                thread = await bot.fetch_channel(int(thread_id))
                if thread:
                    # Invia un messaggio normale e cancellalo subito (o dopo 1-2 secondi)
                    msg_notifica = await thread.send(notifica_msg)
                    await msg_notifica.delete(delay=2.0) # Si cancella rapidamente
            # Se non c'è thread casa, non inviamo nulla (o possiamo inviare in DM, ma per ora lo saltiamo)
        except Exception as e:
            print(f"Errore nell'inviare notifica di termine a {participant_id}: {e}")

    await interaction.response.send_message(
        f"✅ Hai terminato la chiamata. Tutti i partecipanti sono stati avvisati.",
        ephemeral=True
    )

@tree.command(name="vc_add", description="Aggiungi utenti a una chiamata attiva (solo il creatore).")
@app_commands.describe(
    utenti="Uno o più utenti da aggiungere (es. @user1 @user2)"
)
async def vc_add(interaction: discord.Interaction, utenti: str):
    """Aggiunge nuovi utenti a una VC attiva (solo il creatore)."""
    user_id = str(interaction.user.id)
    vc_data = load_vc()
    carica_thread_case()
    
    # Cerca una VC attiva creata dall'utente
    active_vc = None
    target_vc_id = None
    for vc_id, data in vc_data.items():
        if data["creatore"] == user_id and data["stato"] == "attiva":
            active_vc = data
            target_vc_id = vc_id
            break
    
    if not active_vc:
        await interaction.response.send_message(
            "❌ Non hai nessuna chiamata attiva creata da te a cui aggiungere utenti.",
            ephemeral=True
        )
        return

    # Estrai gli ID degli utenti da aggiungere
    user_ids_to_add = re.findall(r"<@!?(\d+)>", utenti)
    
    if not user_ids_to_add:
        await interaction.response.send_message(
            "❌ Menziona almeno un utente da aggiungere.",
            ephemeral=True
        )
        return

    # Aggiungi gli utenti alla lista degli invitati (se non ci sono già)
    nuovi_inviti = []
    for uid in user_ids_to_add:
        if uid not in active_vc["invitati"]:
            active_vc["invitati"].append(uid)
            nuovi_inviti.append(uid)
    
    if not nuovi_inviti:
        await interaction.response.send_message(
            "⚠️ Tutti gli utenti menzionati erano già invitati alla chiamata.",
            ephemeral=True
        )
        return

    save_vc(vc_data)

    # Crea l'embed di invito
    motivo = active_vc.get("motivo", "Nessun motivo")
    embed = discord.Embed(
        title="📞 Nuovo Invito a Chiamata Attiva!",
        description=(
            f"**Creatore:** {interaction.user.mention}\n"
            f"**Motivo:** {motivo}\n\n"
            f"**Nuovi invitati:** {', '.join([f'<@{uid}>' for uid in nuovi_inviti])}\n\n"
            f"_Clicca uno dei bottoni qui sotto per partecipare._"
        ),
        color=discord.Color.purple()
    )

    # Invia l'embed con i bottoni nel canale corrente (dove è stato usato il comando)
    view = VCAcceptView(target_vc_id, str(interaction.channel.id))
    await interaction.response.send_message(
        embed=embed,
        view=view
    )

# --- COMANDO: /vc_leave (Aggiornato - Notifica temporanea nei thread) ---
@tree.command(name="vc_leave", description="Esci volontariamente da una chiamata attiva.")
async def vc_leave(interaction: discord.Interaction):
    """Permette a un partecipante di uscire da una VC attiva."""
    user_id = str(interaction.user.id)
    vc_data = load_vc()
    
    # Cerca una VC attiva in cui l'utente è partecipante
    active_vc = None
    target_vc_id = None
    for vc_id, data in vc_data.items():
        if data["stato"] == "attiva" and user_id in data["partecipanti"]:
            active_vc = data
            target_vc_id = vc_id
            break
    
    if not active_vc:
        await interaction.response.send_message(
            "❌ Non sei in nessuna chiamata attiva da cui poter uscire.",
            ephemeral=True
        )
        return

    # Rimuovi l'utente dai partecipanti
    if user_id in active_vc["partecipanti"]:
        active_vc["partecipanti"].remove(user_id)
    
    motivo = active_vc.get("motivo", "Nessun motivo")
    
    # Salva i dati aggiornati
    save_vc(vc_data)

    # Notifica tutti i partecipanti rimasti nei loro thread casa (messaggio temporaneo)
    notifica_msg = f"🚪 **{interaction.user.display_name}** ha **lasciato** la chiamata."

    for participant_id in active_vc["partecipanti"]:
        try:
            thread_id = THREAD_CASE.get(participant_id)
            if thread_id:
                thread = await bot.fetch_channel(int(thread_id))
                if thread:
                    # Invia messaggio e cancellalo dopo 3 secondi
                    msg_notifica = await thread.send(notifica_msg)
                    await msg_notifica.delete(delay=3.0)
            # Se non c'è thread casa, non facciamo nulla (o si potrebbe inviare in DM, ma lo saltiamo)
        except Exception as e:
            print(f"Errore nell'inviare notifica di uscita a {participant_id}: {e}")

    await interaction.response.send_message(
        f"✅ Hai lasciato la chiamata. Gli altri partecipanti sono stati avvisati.",
        ephemeral=True
    )

# --- COMANDO: /vc_join (Aggiornato - Richiesta auto-cancellante) ---
@tree.command(name="vc_join", description="Richiedi di unirti a una chiamata attiva.")
@app_commands.describe(creatore="Il creatore della chiamata a cui vuoi unirti")
async def vc_join(interaction: discord.Interaction, creatore: discord.Member):
    """Richiedi di unirti a una VC attiva taggando il creatore."""
    user_id = str(interaction.user.id)
    creatore_id = str(creatore.id)
    vc_data = load_vc()
    carica_thread_case()
    
    # Cerca la VC attiva creata da quel creatore
    target_vc = None
    target_vc_id = None
    
    for cid, data in vc_data.items():
        if data["creatore"] == creatore_id and data["stato"] == "attiva":
            target_vc = data
            target_vc_id = cid
            break
        
    if not target_vc:
        await interaction.response.send_message(
            f"❌ {creatore.mention} non ha nessuna chiamata attiva a cui unirti.",
            ephemeral=True
        )
        return

    # Controlla se l'utente è già nella VC
    if user_id in target_vc["partecipanti"]:
        await interaction.response.send_message(
            "❌ Sei già in questa chiamata!",
            ephemeral=True
        )
        return

    # Controlla se l'utente è già stato invitato
    if user_id in target_vc["invitati"]:
        await interaction.response.send_message(
            "❌ Sei già stato invitato a questa chiamata. Usa i bottoni dell'invito per accettare.",
            ephemeral=True
        )
        return

    # Invia richiesta nel canale di creazione della VC
    canale_creazione_id = target_vc["canale_creazione"]
    motivo = target_vc.get("motivo", "Nessun motivo")
    
    try:
        canale_creazione = interaction.guild.get_channel(int(canale_creazione_id))
        if canale_creazione:
            embed_richiesta = discord.Embed(
                title="📞 Richiesta di Partecipazione",
                description=(
                    f"L'utente {interaction.user.mention} ha richiesto di unirsi alla tua chiamata attiva.\n"
                    f"**Motivo:** {motivo}\n\n"
                    f"Usa `/vc_add {interaction.user.mention}` in questo canale per accettare la richiesta."
                ),
                color=discord.Color.gold()
            )
            # Invia la richiesta e salva il messaggio per cancellarlo
            msg_richiesta = await canale_creazione.send(embed=embed_richiesta)
            # Cancella il messaggio dopo 15 secondi
            await msg_richiesta.delete(delay=15.0)
            
            # Risposta visibile solo a chi ha usato il comando
            await interaction.response.send_message(
                f"✅ Richiesta inviata a {creatore.mention} nel canale della chiamata.",
                ephemeral=True
            )
        else:
            raise Exception("Canale di creazione non trovato")
    except:
        await interaction.response.send_message(
            "❌ Impossibile inviare la richiesta nel canale di creazione.",
            ephemeral=True
        )

# --- COMANDO: /vc_mute (Self-Mute Persistente) ---
@tree.command(name="vc_mute", description="Muta o smuta te stesso nella VC attiva.")
async def vc_mute(interaction: discord.Interaction):
    """Muta o smuta se stesso nella VC attiva (stato persistente fino a smute)."""
    user_id = str(interaction.user.id)
    vc_data = load_vc()
    
    # Cerca una VC attiva in cui l'utente è partecipante
    active_vc = None
    target_vc_id = None
    for vc_id, data in vc_data.items():
        if data["stato"] == "attiva" and user_id in data["partecipanti"]:
            active_vc = data
            target_vc_id = vc_id
            break
    
    if not active_vc:
        await interaction.response.send_message(
            "❌ Non sei in nessuna chiamata attiva.",
            ephemeral=True
        )
        return

    # Toggle del self-mute persistente
    action = toggle_self_mute_persistent(active_vc, user_id)
    save_vc(vc_data)
    
    if action == "muted":
        await interaction.response.send_message(
            "🔇 Ti sei mutato nella chiamata. I tuoi messaggi non verranno inoltrati fino a quando non ti smuti.",
            ephemeral=True
        )
    else: # "unmuted"
        await interaction.response.send_message(
            "🔊 Ti sei smutato nella chiamata. I tuoi messaggi verranno di nuovo inoltrati.",
            ephemeral=True
        )

# --- COMANDO: /vc_associa_tupper (Aggiornato con prefisso) ---
@tree.command(name="vc_associa_tupper", description="Associa un nome di tupper e il suo prefisso al tuo account.")
@app_commands.describe(
    nome="Il nome esatto (o parte del nome) del tupper",
    prefisso="Il prefisso usato da Tupperbox per questo tupper"
)
async def vc_associa_tupper(interaction: discord.Interaction, nome: str, prefisso: str):
    """Associa un nome di tupper e il suo prefisso all'account dell'utente."""
    user_id = str(interaction.user.id)
    tupper_data = load_tupper_nomi()
    
    # Controllo se il nome è già associato a qualcun altro
    if nome in tupper_data and tupper_data[nome].get("user_id") != user_id:
        utente_esistente = f"<@{tupper_data[nome]['user_id']}>"
        await interaction.response.send_message(
            f"❌ Il nome '{nome}' è già associato a {utente_esistente}.",
            ephemeral=True
        )
        return
        
    # Associa il nome e il prefisso all'utente
    tupper_data[nome] = {
        "user_id": user_id,
        "prefisso": prefisso
    }
    save_tupper_nomi(tupper_data)
    
    await interaction.response.send_message(
        f"✅ Il tupper '{nome}' con prefisso '{prefisso}' è stato associato al tuo account per le VC.",
        ephemeral=True
    )

# --- EVENTO: on_message per inoltro automatico ---
@bot.event
async def on_message(message: discord.Message):
    """Gestisce l'inoltro automatico dei messaggi durante una VC attiva (con embed)."""
    # 1. Evita che il bot risponda a se stesso e processa i comandi
    if message.author == bot.user:
        await bot.process_commands(message)
        return

    # 2. --- GESTIONE TUPPER: Ignora messaggi utente con prefisso ---
    # Se il messaggio è di un utente normale e inizia con un prefisso tupper associato,
    # lo ignoriamo perché Tupperbox lo sta processando
    if not isinstance(message.author, discord.User):
        if should_ignore_user_message(message.author.id, message.content):
            # Messaggio con prefisso tupper, lo ignoriamo
            await bot.process_commands(message)
            return

    # 3. --- GESTIONE TUPPER: Riconoscimento webhook ---
    # Determina l'ID utente reale, anche se il messaggio è di un webhook (tupper)
    user_id = None
    if isinstance(message.author, discord.User):
        # Potrebbe essere un messaggio di un tupper
        user_id = get_user_id_from_tupper(message.author.name, message.content)
    
    # Se non è un webhook o non è un tupper riconosciuto, usa l'ID dell'autore normale
    if not user_id:
        user_id = str(message.author.id)

    # --- 4. LOGICA VC ESISTENTE (con supporto Vivavoce) ---
    vc_data = load_vc()
    active_vc = None
    
    # --- 4a. PRIMO: Controlla se l'utente è in una VC attiva (logica normale) ---
    for vc_id, data in vc_data.items():
        if data["stato"] == "attiva" and user_id in data["partecipanti"]:
            active_vc = data
            # print(f"[DEBUG VC NORMALE] Utente {user_id} trovato in VC attiva {vc_id}")
            break

    # --- 4b. SECONDO: Se non è in VC, controlla se il messaggio è da un canale in VIVAVOCE ---
    if not active_vc:
        # Cerca se il canale del messaggio è in vivavoce per qualche VC attiva
        vc_info_from_vivavoce, listener_user_id = get_vc_info_and_listener_for_channel(message.channel.id)
        if vc_info_from_vivavoce:
            # print(f"[DEBUG VIVAVOCE] Canale {message.channel.id} è in vivavoce per VC, ascoltatore {listener_user_id}")
            active_vc = vc_info_from_vivavoce
            # ATTENZIONE: user_id rimane l'originale (quello che ha scritto)
            # L'embed userà comunque message.author (l'originale) per nome/avatar
            # Quindi il mittente nell'embed sarà corretto

    # 5. CONTROLLA SE L'UTENTE È SELF-MUTATO (persistente)
    # Nota: per i messaggi da vivavoce, questo controllo si applica all'utente che ha attivato il vivavoce
    if active_vc and is_user_self_muted(active_vc, user_id):
        # L'utente è mutato, non inoltriamo il messaggio
        await bot.process_commands(message)
        return # Esce dalla funzione, non inoltra il messaggio

    # 6. CONTROLLA SE IL MESSAGGIO DEVE ESSERE INOLTRATO
    if (active_vc and 
        not message.content.startswith(PREFIX_ESCLUDI_VC)):

        # 7. Crea l'embed per il messaggio inoltrato - SENZA timestamp
        embed_vc = discord.Embed(
            description=message.content,
            color=discord.Color.blurple()
        )
        
        # Usa il nome e l'avatar del webhook (tupper) o dell'utente normale
        # NOTA: Per il vivavoce, l'utente originale è message.author, quindi l'embed lo mostra correttamente
        if isinstance(message.author, discord.User):
            # Messaggio da tupper/webhook
            embed_vc.set_author(
                name=message.author.name, # Nome del tupper
                icon_url=message.author.display_avatar.url # Avatar del tupper
            )
        else:
            # Messaggio da utente normale (o da vivavoce)
            embed_vc.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url
            )

        # 8. --- LOGICA MIGLIORATA PER INOLTRO ---
        # a. Controlla se il canale corrente è escluso
        if canale_escluso(message.channel):
            # print(f"[DEBUG] Canale {message.channel.id} è escluso, nessun inoltro.") # Opzionale per debug
            pass # Non inoltrare se il messaggio viene da un canale escluso
        else:
            # b. Raggruppa partecipanti per thread_id e invia un solo messaggio per thread
            partecipanti_per_thread = {}
            for participant_id in active_vc["partecipanti"]:
                if participant_id != user_id: # Non inviare al mittente
                    thread_id = THREAD_CASE.get(participant_id)
                    if thread_id:
                        if thread_id not in partecipanti_per_thread:
                            partecipanti_per_thread[thread_id] = []
                        partecipanti_per_thread[thread_id].append(participant_id)
                    # Nota: i partecipanti senza casa vengono ignorati (nessun fallback)

            # c. Invia un SOLO messaggio per ogni thread unico
            for thread_id, participant_ids in partecipanti_per_thread.items():
                # *** NUOVO CONTROLLO: Evita di inviare il messaggio nel canale di origine ***
                # Se il thread di destinazione è lo stesso canale dove è stato scritto il messaggio originale,
                # e il mittente è anche nel thread di destinazione, non inviare (evita auto-inoltro visivo)
                if str(message.channel.id) == str(thread_id):
                    # print(f"[DEBUG] Thread {thread_id} è il canale di origine, skip auto-inoltro.") # Opzionale
                    continue # Salta l'invio a questo thread specifico
                
                try:
                    thread = await bot.fetch_channel(int(thread_id))
                    if thread:
                        # d. Controlla se il thread di destinazione è escluso
                        if not canale_escluso(thread):
                            await thread.send(embed=embed_vc)
                            # print(f"[DEBUG] Messaggio inviato a thread {thread_id} per {len(participant_ids)} partecipanti.") # Opzionale
                        # else:
                            # print(f"[DEBUG] Thread {thread_id} è escluso, nessun invio.") # Opzionale
                except Exception as e:
                    print(f"[ERRORE] Impossibile inviare messaggio al thread {thread_id}: {e}")

    # 9. Importante: processa i comandi anche per i messaggi normali
    await bot.process_commands(message)

# --- COMANDO: /vc_vivavoce ---
@tree.command(name="vc_vivavoce", description="Attiva/disattiva il vivavoce per un canale nella VC.")
@app_commands.describe(canale="Il canale da mettere in vivavoce (default: il canale corrente)")
async def vc_vivavoce(interaction: discord.Interaction, canale: discord.TextChannel = None):
    """Attiva o disattiva il vivavoce per un canale."""
    user_id = str(interaction.user.id)
    
    # Determina il canale target
    target_channel = canale if canale else interaction.channel
    target_channel_id = str(target_channel.id)
    
    # Verifica che l'utente sia in una VC attiva
    vc_data = load_vc()
    active_vc = None
    target_vc_id = None
    for vc_id, data in vc_data.items():
        if data["stato"] == "attiva" and user_id in data["partecipanti"]:
            active_vc = data
            target_vc_id = vc_id
            break
    
    if not active_vc:
        await interaction.response.send_message(
            "❌ Non sei in nessuna chiamata attiva dove attivare il vivavoce.",
            ephemeral=True
        )
        return

    # Controlla se il canale è già in vivavoce per questa VC
    vivavoce_channels = active_vc.get("vivavoce_channels", {})
    
    if target_channel_id in vivavoce_channels:
        # Disattiva il vivavoce
        if remove_vivavoce_channel_from_vc_data(target_vc_id, target_channel_id):
            await interaction.response.send_message(
                f"🔇 Vivavoce disattivato per il canale {target_channel.mention} nella chiamata.",
                ephemeral=True
            )
        else:
             await interaction.response.send_message(
                "❌ Errore durante la disattivazione del vivavoce.",
                ephemeral=True
            )
    else:
        # Attiva il vivavoce
        if set_vivavoce_channel_in_vc_data(target_vc_id, target_channel_id, user_id):
            await interaction.response.send_message(
                f"🎙️ Vivavoce attivato! Ora i messaggi da {target_channel.mention} verranno inoltrati nella chiamata. Chiunque scriva lì sarà sentito come se fosse tu.",
                ephemeral=True
            )
        else:
             await interaction.response.send_message(
                "❌ Errore durante l'attivazione del vivavoce.",
                ephemeral=True
            )


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await tree.sync()
    print(f"✅ Bot connesso come {bot.user}")
        
bot.run("TOKEN")
