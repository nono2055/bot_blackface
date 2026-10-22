import os

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])
LOG_CHANNEL_ID = int(os.environ["LOG_CHANNEL_ID"])

# Les 3 seuls rôles que la commande peut donner
ALLOWED_ROLE_IDS = {
    int(os.environ["ROLE_POLICIER_ID"]),
    int(os.environ["ROLE_POMPIER_ID"]),
    int(os.environ["ROLE_MEDECIN_ID"]),
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
guild_obj = discord.Object(id=GUILD_ID)


@tree.command(
    name="addrole",
    description="Choisis ton rôle whitelist (un seul possible)",
    guild=guild_obj,
)
@app_commands.describe(role="Le rôle : policier, pompier ou médecin whitelist")
async def addrole(interaction: discord.Interaction, role: discord.Role):
    member = interaction.user

    # 1. Seulement les 3 rôles autorisés
    if role.id not in ALLOWED_ROLE_IDS:
        await interaction.response.send_message(
            "❌ Tu peux seulement choisir : policier whitelist, "
            "pompier whitelist ou médecin whitelist.",
            ephemeral=True,
        )
        return

    # 2. Un seul rôle à la fois : si le membre en a déjà un des 3, refus.
    #    Quand un modo lui enlève, il peut re-choisir.
    already = [r for r in member.roles if r.id in ALLOWED_ROLE_IDS]
    if already:
        await interaction.response.send_message(
            f"❌ Tu as déjà le rôle {already[0].mention}. "
            "Un modérateur doit te l'enlever avant que tu puisses en choisir un autre.",
            ephemeral=True,
        )
        return

    # 3. Ajout du rôle
    try:
        await member.add_roles(role, reason="Commande /addrole")
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Je n'ai pas la permission de donner ce rôle "
            "(mon rôle doit être au-dessus dans la liste).",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"✅ Rôle {role.mention} ajouté !", ephemeral=True
    )

    # 4. Log : nom, ID, rôle
    channel = client.get_channel(LOG_CHANNEL_ID) or await client.fetch_channel(
        LOG_CHANNEL_ID
    )
    embed = discord.Embed(title="Rôle ajouté", color=discord.Color.green())
    embed.add_field(name="Nom", value=member.display_name, inline=True)
    embed.add_field(name="ID", value=str(member.id), inline=True)
    embed.add_field(name="Rôle choisi", value=role.name, inline=False)
    embed.timestamp = discord.utils.utcnow()
    await channel.send(embed=embed)


@client.event
async def on_ready():
    await tree.sync(guild=guild_obj)
    print(f"Connecté en tant que {client.user}")


client.run(TOKEN)
