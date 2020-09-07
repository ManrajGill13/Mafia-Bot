import discord, random, config, re
from objects import State, Player, Game
from discord.ext import commands
from discord.utils import find, get

client = commands.Bot(config.prefix)

games = list()
players = list()

# Get the game with the right server ID a command was sent from
def get_game(server_id):
	for game in games:
		if server_id == game.server_id:
			return game

	return -1

# Create an embed with a default red colour
def create_embed(msg):
	display = discord.Embed(
		description = msg,
		color = discord.Colour.red()
	)

	return display

@client.event
async def on_ready():
    print('Ready to go!')

@client.command()
async def rules(ctx):
    with open(config.rules) as f:
        await ctx.send(f.read())

@client.command()
async def createchannels(ctx):
	channels_created = True
	for channel in ctx.guild.channels: # check if channels with game names already exist
		if channel.name == "mafia-general" or channel.name == "mafioso" or channel.name == "medics" or channel.name == "detectives":
			channels_created = False

	if channels_created: # if they don't exist, make channels and handle permissions
		overwrites = {
	        ctx.message.guild.default_role: discord.PermissionOverwrite(read_messages = False),
	    }

		await ctx.guild.create_text_channel('mafia-general') # create a mafia general channel
		mafia_general = find(lambda x: x.name == 'mafia-general', ctx.guild.text_channels)
		if mafia_general and mafia_general.permissions_for(ctx.guild.me).send_messages:
			await mafia_general.send(embed = create_embed("**Use this channel for general purpose commands such as making/joining/leaving games and voting**"))

		await ctx.guild.create_text_channel('mafioso', overwrites = overwrites) # create a channel for the mafia
		mafioso = find(lambda x: x.name == 'mafioso', ctx.guild.text_channels)
		if mafioso and mafioso.permissions_for(ctx.guild.me).send_messages:
			await mafioso.send(embed = create_embed("**Talk to your fellow mafia members here and vote on who to kill**"))

		await ctx.guild.create_text_channel('medics', overwrites = overwrites) # create a channel for medics
		medics = find(lambda x: x.name == 'medics', ctx.guild.text_channels)
		if medics and medics.permissions_for(ctx.guild.me).send_messages:
			await medics.send(embed = create_embed("**Choose who to save here**"))

		await ctx.guild.create_text_channel('detectives', overwrites = overwrites) # create a channel for detectives
		detectives = find(lambda x: x.name == 'detectives', ctx.guild.text_channels)
		if detectives and detectives.permissions_for(ctx.guild.me).send_messages:
			await detectives.send(embed = create_embed("**Choose who you wish to inspect here**"))
	else: # otherwise let users know that channels already exist
		await ctx.send(embed = create_embed("**A channel by the name of mafia-general, mafioso, medics, or detectives already exists on this server**"))

# Create a game and add to list of games
@client.command()
async def creategame(ctx):
	channels_created = False
	for channel in ctx.guild.channels: # check if channels with game names already exist
		if channel.name == "mafia-general" or channel.name == "mafioso" or channel.name == "medics" or channel.name == "detectives":
			channels_created = True

	if get_game(ctx.guild.id) == -1: # if no game in server yet
		game = Game(ctx.guild.id)

		if channels_created:
			game.state = State.started
			games.append(game)

			display = create_embed("**A new game of Mafia has been created by " + ctx.message.author.mention + " use m!join to join.**")
			display.set_author(
				name = "Mafia Bot", 
				icon_url = "https://i.imgur.com/mwmT47i.png")
			display.set_image(url = "https://i.imgur.com/zTSJolW.png")
			display.set_footer(text = "When you're ready type m!setup to start, use m!help if you get lost.")
		else:
			display = create_embed("**You need to make text channels for the game first, use m!createchannels**")
	else: # if game exists in server already
		display = create_embed("**There is already a game in progress in this server.**")

	await ctx.send(embed = display)

# Join a game if one exists in the start phase on the server
@client.command()
async def join(ctx):
	game = get_game(ctx.guild.id)

	if game == -1:
		display = create_embed("**There is no game in this server yet, use m!creategame to make one.**")
	elif not game.state == State.started:
		display = create_embed("**A game has already begun**")
	elif game.get_player(ctx.message.author.id): # check if player is in player_atlas
		display = create_embed("**You're already a part of the game.**")
	else:
		display = create_embed("**" + ctx.message.author.mention + " has joined the game.**")
		for i in range(0, 5):
			game.player_atlas["none"].append(Player(ctx.message.author.id)) # add player to player_atlas with no role

	await ctx.send(embed = display)

# Leave a game if one exists in the setup phase on the server
@client.command()
async def leave(ctx):
	game = get_game(ctx.guild.id)

	if game == -1:
		display = create_embed("**There is no game in this server yet, use m!creategame to make one.**")
	elif not game.state == State.started:
		display = create_embed("**A game has already begun, no one can leave until it is finished.**")
	elif not game.get_player(ctx.message.author.id): # check if player is not in palyer_atlas
		display = create_embed("**You can't leave a game you haven't joined.**")
	else:
		display = create_embed("**" + ctx.message.author.mention + " has left the game.**")
		game.player_atlas["none"].remove(game.get_player(ctx.message.author.id)) # remove player from player_atlas

	await ctx.send(embed = display)

# Show list of players
@client.command()
async def players(ctx):
	game = get_game(ctx.guild.id)

	if game == -1:
		display = create_embed("**There is no game in this server yet, use m!creategame to make one.**")
	elif game.state == State.started and len(game.player_atlas["none"]) < 1:
		display = create_embed("**No players have joined yet**")
	else:
		display = create_embed("**:detective:Players(" + str(len(game.player_atlas["none"])) + "): ** \n>>> ")

		# list out players
		for player in game.player_atlas["none"]:
			display.description = display.description + "**" + client.get_user(player.ID).mention + ":white_check_mark:**\n"

	await ctx.send(embed = display)

# Lock the game so no more players may leave or join and setup roles for each player
@client.command()
async def setup(ctx):
	game = get_game(ctx.guild.id)

	if game == -1:
		display = create_embed("**There is no game in this server yet, use m!creategame to make one.**")
	elif not game.state == State.started:
		display = create_embed("**A game has already begun**")
	elif len(game.player_atlas["none"]) < 5: # Make sure there are at least 6 players before a game may begin
		display = create_embed("**There aren't enough players in this game yet, use m!join to join.**")
	else:
		display = create_embed("**The game is ready to begin, no more players will be allowed to join until this one is finished.\n\n" + 
			":detective:Players(" + str(len(game.player_atlas["none"])) + "): ** \n>>> ")

		# list out players
		for player in game.player_atlas["none"]:
			display.description = display.description + "**" + client.get_user(player.ID).mention + ":white_check_mark:**\n"
		display.set_footer(text = "Information about your role has been sent to your DM.")

		# split players into mafia
		for i in range(0, len(game.player_atlas["none"])//5):
			temp = random.choice(game.player_atlas["none"])
			game.player_atlas["none"].remove(temp)
			game.player_atlas["mafiosi"].append(temp)

			mafioso = find(lambda x: x.name == 'mafioso', ctx.guild.text_channels)
			await mafioso.set_permissions(ctx.guild.get_member(temp.ID), read_messages = True)
			await mafioso.set_permissions(ctx.guild.get_member(temp.ID), send_messages = True)

		# choose a medic from players
		temp = random.choice(game.player_atlas["none"])
		game.player_atlas["none"].remove(temp)
		game.player_atlas["medics"].append(temp)
		medics = find(lambda x: x.name == 'medics', ctx.guild.text_channels)
		await medics.set_permissions(ctx.guild.get_member(temp.ID), read_messages = True)
		await medics.set_permissions(ctx.guild.get_member(temp.ID), send_messages = True)

		# choose a detective from players
		temp = random.choice(game.player_atlas["none"])
		game.player_atlas["none"].remove(temp)
		game.player_atlas["detectives"].append(temp)
		detectives = find(lambda x: x.name == 'mafioso', ctx.guild.text_channels)
		await detectives.set_permissions(ctx.guild.get_member(temp.ID), read_messages = True)
		await detectives.set_permissions(ctx.guild.get_member(temp.ID), send_messages = True)

		game.player_atlas["citizens"] = game.player_atlas["none"]

		for player in game.player_atlas["mafiosi"]: # send mafioso their instructions
			player.role = "mafioso"
			mafia_display = create_embed("**You're a *FIENDISH MAFIA MEMBER!***\n\nYou may privately snicker and plot " + 
				"with your fellow mafiosi (make sure you keep it down).\nEach night you must collectively decide on one " + 
				"unfortunate soul to kill.\n\n**You win when there are the same amount of citizens as mafiosi left.\n\n**")

			if len(game.player_atlas["mafiosi"]) > 1: # tell mafia member who their fellow mafiosi are
				mafia_display.description = mafia_display.description + "Your particular mafia includes the following members: \n>>> "
				for mafioso in game.player_atlas["Mafiosi"]:
					mafia_display.description = mafia_display.description + "**" + mafioso.mention + ":white_check_mark:**\n"

			mafia_display.set_author(name = "Mafia Bot", 
				icon_url = "https://i.imgur.com/mwmT47i.png")
			await client.get_user(player.ID).send(embed = mafia_display)

		for player in game.player_atlas["medics"]: # send medic their instructions
			player.role = "medic"
			medic_string = random.choice([ # choose from a list of random medics, these do nothing yet
					"**You're a RELUCTANT MEDIC!**\n\nYour parents always nagged you to be a doctor and now look at where it left you... Medic morals make you want to help/save others (especially in these circumstances) and you definitely didn't suffer through Med-school to go out like this.",
					"**You're an EX-HOBO MEDIC!**\n\nYou always knew browsing through that Med Training Handbook you found under the bridge was going to come in handy. Now you help this small town with your not-really-certified medical skills.",
					"**You're an ALCOHOLIC MEDIC!**\n\n You had to get through medical school somehow, and drowning the stress away with alcohol kept you sane enough to get your degree. Even if that now means you're an alcoholic. The town provides you with your favourite drinks so you kind of have to save them to indirectly save the booze, and you're sure that the Mafia is going to keep all the booze to themselves if they win.",
					"**You're a WITCH DOCTOR MEDIC!**\n\nWho needs medschool when Mother Earth produces such wonderful healing herbs? It's not like the town can afford a \"real\" doctor anyways, so instead they have you. You don't have much aside from this town so you really have to keep it out of the hands of the Mafia regardless. It's for the town's well being, sure, but mainly for your livelihood.",
					"**You're a MEDIC**You've gone through the grueling years of medical school and have settled down in this town. You really like the place and the people here need you so you feel the need to protect them from the Mafia."
				])

			medic_display = create_embed(medic_string + "\nEach night you must decide on one person's life to save from the " +
					"Mafia's unpredictable schemes.\n\n**You win when all the mafiosi are dead.**")
			medic_display.set_author(name = "Mafia Bot", 
				icon_url = "https://i.imgur.com/mwmT47i.png")
			await client.get_user(player.ID).send(embed = medic_display)

		for player in game.player_atlas["detectives"]: # send detectives their instructions
			player.role = "detective"
			detective_display = create_embed("**You're a *SKILLFUL DETECTIVE***\n\nThe years you've spent working in your " + 
				"field have given you the ability to effortlessly determine someone's goals upon inspection.\nEach night you may " +
				"use this skill to inpect a single player and learn their roles.\n\n**You win when all the mafiosi are dead.**")

			detective_display.set_author(name = "Mafia Bot", 
				icon_url = "https://i.imgur.com/mwmT47i.png")
			await client.get_user(player.ID).send(embed = detective_display)
		
		for player in game.player_atlas["citizens"]: # send citizens their instructions
			player.role = "citizen"
			citizen_display = create_embed("**You're a *POWERLESS CITIZEN!***\n\nYou have no special abilities and must " + 
				"live the next few days of your life with great caution.\nUse your mundanity to figure out who the " + 
				"mafiosi are and vote on players in the day time to lynch them.\n\n**You win when all the mafiosi are dead.**")

			citizen_display.set_author(name = "Mafia Bot", 
			icon_url = "https://i.imgur.com/mwmT47i.png")
			await client.get_user(player.ID).send(embed = citizen_display)

	await ctx.send(embed = display)

	display = create_embed("It's night time\n\nThe Mafia may use m!kill @user\nMedics may use m!protect @user\nDetectives may use m!inspect")
	await ctx.send(embed = display)

	game.state = State.night

# Allow Mafia to choose who to kill
@client.command()
async def kill(ctx, arg1):
	game = get_game(ctx.guild.id)
	player_ID = int(re.sub('[<|!|@|>]', '', arg1))
	player = game.get_player(player_ID)

	if game.can_act(ctx.message.author.id, "mafia"):
		if player == None:
			display = create_embed("**This player is not in the game.**")
		elif player.is_protected:
			display = create_embed("**Nice try.**")
		else:
			display = create_embed("**" + client.get_user(player_ID).name + "? Consider it done.**")
			kill(player)
			player.has_acted = True
	else:
		display = create_embed("**You're better than that.**")

	await ctx.send(embed = display)

# Allow Medics to choose who to protect
@client.command()
async def protect(ctx, arg1):
	game = get_game(ctx.guild.id)
	player_ID = int(re.sub('[<|!|@|>]', '', arg1))
	player = game.get_player(player_ID)

	if game.can_act(ctx.message.author.id, "medic"):
		if player == None:
			display = create_embed("**No such player exists.**")
		else:
			display = create_embed("**You rush to" + client.get_user(player_ID).name + "'s aid**")
			player.has_acted = True
	else:
		display = create_embed("**You're not really up for it.**")

	await ctx.send(embed = display)

# Allow Detectives to choose who to inspect
@client.command()
async def inspect(ctx, arg1):
	game = get_game(ctx.guild.id)
	player_ID = int(re.sub('[<|!|@|>]', '', arg1))
	player = game.get_player(player_ID)

	if game.can_act(ctx.message.author.id, "detective"):
		if player == None:
			display = create_embed("**No such player exists.**")
		else:
			display = create_embed("**" + client.get_user(player_ID).name + " is a " + player.role + "**")
			player.has_acted = True
	else:
		display = create_embed("**You wish you knew how.**")

	await ctx.send(embed = display)

client.run(config.token)
