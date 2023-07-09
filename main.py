import discord
from gpt_index import SimpleDirectoryReader, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os
import requests

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BOT_API_KEY = os.getenv("BOT_API_KEY")

# os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def construct_index(directory_path):
    max_input_size = 4096
    num_outputs = 512
    max_chunk_overlap = 20
    chunk_size_limit = 600

    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)

    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=num_outputs))

    documents = SimpleDirectoryReader(directory_path).load_data()

    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)

    index.save_to_disk('index.json')

    return index

def chatbot(input_text):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    response = index.query(input_text, response_mode="compact")
    return response.response

# GETS THE CLIENT OBJECT FROM DISCORD.PY. CLIENT IS SYNONYMOUS WITH BOT.
bot = discord.Client(intents=discord.Intents.all())

# EVENT LISTENER FOR WHEN THE BOT HAS SWITCHED FROM OFFLINE TO ONLINE.
@bot.event
async def on_ready():
	# CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
	guild_count = 0

	# LOOPS THROUGH ALL THE GUILD / SERVERS THAT THE BOT IS ASSOCIATED WITH.
	for guild in bot.guilds:
		# PRINT THE SERVER'S ID AND NAME.s
		print(f"- {guild.id} (name: {guild.name})")

		# INCREMENTS THE GUILD COUNTER.
		guild_count = guild_count + 1

	# PRINTS HOW MANY GUILDS / SERVERS THE BOT IS IN.
	print("SampleDiscordBot is in " + str(guild_count) + " guilds.")


index = construct_index("docs")

# EVENT LISTENER FOR WHEN A NEW MESSAGE IS SENT TO A CHANNEL.
@bot.event
async def on_message(message):
	print(message.author.id)
	# if message.channel.type in discord.enums._EnumValue_ChannelType:
	if str(message.channel.type) == 'private':
		if str(message.author.id) == '427531259325972480':
			#Answer to only this user as the admin
			# !ecodocs commmand
			if message.content.startswith("!ecodocs"):
				documents = []
				for path in os.listdir("docs"):
					# check if current path is a file
					if os.path.isfile(os.path.join("docs", path)):
						documents.append(path)
				await message.channel.send(documents)
			elif message.content.startswith("!add-ecodocs"):
				#Adding a doc/s to the list
				attachments = message.attachments
				if(len(attachments)> 0):
					for attachment in attachments:
						attachment_url = attachment.url
						filename = attachment_url.split('/')[-1]
						file_request = requests.get(attachment_url)
						with open('docs/'+filename, 'wb') as f:
							f.write(file_request.content)
							await message.channel.send(filename+": Saved")
				else:
					await message.channel.send("You sent no document")
			elif message.content.startswith("!delete-ecodocs"):
				#Deleting a doc from the list
				file_name = message.content.replace("!delete-ecodocs ", "")
				file_path = ""
				if ".pdf" in file_name:
					file_path = "docs/"+file_name
				else:
					file_path = "docs/"+file_name+".pdf"

				if os.path.isfile(file_path):
					os.remove(file_path)
					await message.channel.send(f"{file_path} deleted.")
				else:
					await message.channel.send(f"{file_path} not found.")
			elif message.content.startswith("!train-ecodocs"):
				await message.channel.send("Starting training...")
				construct_index("docs")
				await message.channel.send("Training completed.")
	# CHECKS IF THE MESSAGE THAT WAS SENT IS EQUAL TO "HELLO".
	if message.content.startswith("!ecogpt"):
		text = message.content
		botmessage = await message.channel.send("processing...")
		await botmessage.edit(content = "{} {}".format(chatbot(text.replace("!ecogpt", "")), message.author.mention))
	

# EXECUTES THE BOT WITH THE SPECIFIED TOKEN. TOKEN HAS BEEN REMOVED AND USED JUST AS AN EXAMPLE.
bot.run(BOT_API_KEY)