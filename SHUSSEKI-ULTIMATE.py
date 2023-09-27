import discord
from discord.ext import commands
import pyodbc
import asyncio
import io
from PIL import Image
import json
import base64
from PIL import Image
from io import BytesIO
import requests

# Define intents and enable message content
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix='!', intents=intents)

server = 'LAPTOP-GJVJTCRT'
database = 'shusseki'
username = 'sa'
password = 'XXXX'

# Create a connection to SQL Server
connection = pyodbc.connect(
    f'DRIVER=ODBC Driver 17 for SQL Server;'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
)
print(connection)

def process_image_and_insert(enrollid, server, database, username, password):
    # Define the URL and JSON data
    url = "http://10.1.1.41:5000/admin/push"
    payload = {
        "cmd": "getuserinfo",
        "enrollid": enrollid,
        "sn": "ZXRB22001001",
        "backupnum": 50
    }

    api_token = "shusseki"

    filename = "response.json"  # Define a default filename

    try:
        # Send a POST request with the JSON data and the authentication token
        headers = {"Authorization": f"Bearer {api_token}"}
        response = requests.post(url, json=payload, headers=headers)

        # Check the response status code
        if response.status_code == 200:
            print("Request was successful")

            print(f"Saving response content to {filename}...")
            with open(filename, 'w') as file:
                file.write(response.text)
            print(f"Response content saved to {filename}")
        else:
            print(f"Request failed with status code {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    with open(filename, 'r') as json_file:
        data = json.load(json_file)

    # Decode the base64-encoded image data
    response_data = data.get('record', "")
    image_data = base64.b64decode(response_data)
    image = Image.open(BytesIO(image_data))
    image.save("face.png")

# Create a cursor for executing SQL queries
cursor = connection.cursor()

last_data = None

@bot.event
async def check_database_update():
    global last_data
    while not bot.is_closed():
        # Define the SQL query inside the loop to fetch data on each iteration
        sql_query = """
        SELECT TOP 1 face.time, Personaltable.name, Personaltable.id, Department.dep_name, Personaltable.enrollid
        FROM Face
        INNER JOIN Personaltable ON Face.enrollid = Personaltable.enrollid
        INNER JOIN Department ON Department.[dep.no] = Personaltable.[dep.no]
        ORDER BY face.time DESC
        """
        cursor.execute(sql_query)

        new_data = cursor.fetchone()

        if new_data is not None and new_data != last_data:
            # Database data has changed, send a message
            channel = bot.get_channel(1156206842695913492)  # Replace with your channel ID
            if channel:
                formatted_data = "\n".join(
                    map(str,[f"Date and Time: {new_data.time}\nName: {new_data.name}\nID: {new_data.id}\nDepartment: {new_data.dep_name}"])
                )
                process_image_and_insert(new_data.enrollid, server, database, username, password)
                image_file = discord.File("face.png")  # Create a discord.File
                await channel.send(
                        f"Login update!\n```{formatted_data}```",
                        file=image_file,  # Send the image as a file
                    )

            last_data = new_data

        await asyncio.sleep(5)  # Check for updates every 1 second


@bot.event
async def on_ready():
    print(f'Shusseki online! {bot.user.name}')
    bot.loop.create_task(check_database_update()) 



#===================================================================================================
bot.run('YOUR_TOKEN_HERE')
