import discord
from discord.ext import commands
from discord import app_commands
import pymysql, re, datetime, json, requests


config = "./config.json"
with open(config, "r") as f:
  data = json.load(f)
  
db_host = data["DB_HOST"]
db_username = data["DB_USERNAME"]
db_name = data["DB_NAME"]
db_password = data["DB_PASS"]
server_name = data["SERVER_NAME"]
bot_token = data["DISCORD_TOKEN"]
user_token = data["USER_TOKEN"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(
    command_prefix="!",  
    case_insensitive=True,  
  intents=intents 
)

@bot.tree.command(name = "top", description = f"Get the top 10 players from {server_name}")
async def top(interaction: discord.Interaction) -> None:
  
    conn = pymysql.connect(
    host=db_host.split(":")[0],
    port=int(db_host.split(":")[1]),
    user=db_username,
    password=db_password,
    database=db_name
    )

    cur = conn.cursor()

    cur.execute("SELECT * FROM k4ranks ORDER BY points DESC LIMIT 10")

    rows = cur.fetchall()

    cur.close()
    conn.close()

    embed = discord.Embed(
        title="Top 10 Players",
        description=f"Here are the top 10 players from {server_name}:",
        color=discord.Color.blue()
    )
    i = 1
    for row in rows:
        embed.add_field(name=str(i) + ".", value=f"[{row[2]}](https://steamcommunity.com/profiles/{row[1]}) - Score: {row[4]}", inline=False)
        i += 1
    embed.set_footer(text="made with 💜 by seras")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stats", description="Get your own accounts stats")
async def stats(interaction: discord.Interaction) -> None:
  url = f"https://discord.com/api/v9/users/{interaction.user.id}/profile"
  header = {"authorization": user_token}
  res = requests.get(url, headers=header)
  parsed_data = json.loads(res.text)
  
  steam_account = None
  for account in parsed_data["connected_accounts"]:
    if account["type"] == "steam":
      steam_account = account
      break
  
  if steam_account == None:
    await interaction.response.send_message("You dont have an steam account linked to your discord account!")
  
  conn = pymysql.connect(
      host=db_host.split(":")[0],
      port=int(db_host.split(":")[1]),
      user=db_username,
      password=db_password,
      database=db_name
    )
    
  cur = conn.cursor()
    
  cur.execute(f"SELECT * FROM k4ranks WHERE `steam_id` = '{steam_account["id"]}'")
    
  rows = cur.fetchall()
    
  cur.execute(f"SELECT * FROM k4stats WHERE `steam_id` = '{steam_account["id"]}'")
    
  rows_stats = cur.fetchall()
    
  cur.close()
  conn.close()
  
  if len(rows) == 0:
    await interaction.response.send_message("Couldnt find any data related to your account")
    
  embed = discord.Embed(
        title=f"Results for your account: {steam_account["name"]}",
        color=discord.Color.blue()
      )
  embed.add_field(name="Account:", value=f"[{rows[0][2]}](https://steamcommunity.com/profiles/{rows[0][1]})", inline=False)
  embed.add_field(name="Score:", value=f"{rows[0][4]} Points")
  embed.add_field(name="Rank: ", value=rows[0][3], inline=False)
  kills = rows_stats[0][4]
  deaths = rows_stats[0][6]
  mvps = rows_stats[0][13]
  kd = round(kills / deaths, 2)
  last_seen_sql = str(rows_stats[0][3])
  datetime_obj = datetime.datetime.strptime(last_seen_sql, "%Y-%m-%d %H:%M:%S")
  unix_timestamp = datetime_obj.timestamp()
  unix_timestamp_int = int(unix_timestamp)
    
  embed.add_field(name="Kills: ", value=kills, inline=False)
  embed.add_field(name="Deaths: ", value=deaths, inline=False)
  embed.add_field(name="K/D ratio: ", value=kd, inline=False)
  embed.add_field(name="MVP's: ", value=mvps, inline=False)
  embed.add_field(name="Last seen: ", value=f"<t:{unix_timestamp_int}:R>", inline=False)
    
  embed.set_footer(text="made with 💜 by seras")
    
  await interaction.response.send_message(embed=embed)
  
  
@bot.tree.command(name="check", description="Check player by steamid64")
async def check_player(interaction: discord.Interaction, steamid64: str) -> None:
    
    if not steamid64:
      await interaction.response.send_message("Invalid steamid64")
    if not len(steamid64) == 17:
      await interaction.response.send_message("Invalid steamid64 length")
    if not re.match(r"^\d+$", steamid64):
      await interaction.response.send_message("Steamid64 only contains numbers, invalid input")
    
    conn = pymysql.connect(
      host=db_host.split(":")[0],
      port=int(db_host.split(":")[1]),
      user=db_username,
      password=db_password,
      database=db_name
    )
    
    cur = conn.cursor()
    
    cur.execute(f"SELECT * FROM k4ranks WHERE `steam_id` = '{steamid64}'")
    
    rows = cur.fetchall()
    
    cur.execute(f"SELECT * FROM k4stats WHERE `steam_id` = '{steamid64}'")
    
    rows_stats = cur.fetchall()
    
    cur.close()
    conn.close()
    if len(rows) != 0:
      embed = discord.Embed(
        title=f"Results for search: **{steamid64}**",
        color=discord.Color.blue()
      )
      embed.add_field(name="Name:", value=f"[{rows[0][2]}](https://steamcommunity.com/profiles/{rows[0][1]})", inline=False)
      embed.add_field(name="Score:", value=f"{rows[0][4]} Points")
      embed.add_field(name="Rank: ", value=rows[0][3], inline=False)
      kills = rows_stats[0][4]
      deaths = rows_stats[0][6]
      mvps = rows_stats[0][13]
      kd = round(kills / deaths, 2)
      last_seen_sql = str(rows_stats[0][3])
      datetime_obj = datetime.datetime.strptime(last_seen_sql, "%Y-%m-%d %H:%M:%S")
      unix_timestamp = datetime_obj.timestamp()
      unix_timestamp_int = int(unix_timestamp)
      
      embed.add_field(name="Kills: ", value=kills, inline=False)
      embed.add_field(name="Deaths: ", value=deaths, inline=False)
      embed.add_field(name="K/D ratio: ", value=kd, inline=False)
      embed.add_field(name="MVP's: ", value=mvps, inline=False)
      embed.add_field(name="Last seen: ", value=f"<t:{unix_timestamp_int}:R>", inline=False)
      
      embed.set_footer(text="made with 💜 by seras")
      
      await interaction.response.send_message(embed=embed)
    else:
      await interaction.response.send_message("Couldnt find that steamid64 in our database")

@bot.command()
async def synccmd(ctx):
  fmt = await ctx.bot.tree.sync()
  await ctx.send(
    f"Syncd {len(fmt)} commands to the current server"
  )
  return

token = bot_token
bot.run(token) 
