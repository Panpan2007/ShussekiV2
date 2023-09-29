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
password = 'ris17460'

db_connection_string = (
    f'DRIVER=ODBC Driver 17 for SQL Server;'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};')

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
update_task = None  # To store the database update task
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
                    map(str, [f"Date and Time: {new_data.time}\nName: {new_data.name}\nID: {new_data.id}\nDepartment: {new_data.dep_name}"])
                )
                process_image_and_insert(new_data.enrollid, server, database, username, password)
                image_file = discord.File("face.png")  # Create a discord.File
                await channel.send(
                    f"Login update!\n```{formatted_data}```",
                    file=image_file,  # Send the image as a file
                )

            last_data = new_data

        await asyncio.sleep(3)  # Check for updates every 5 seconds

# Command to start the database update task
@bot.command()
async def start_realtime(ctx):
    global update_task
    if update_task is None:
        update_task = bot.loop.create_task(check_database_update())
        await ctx.send('Real-time update task started.')
    else:
        await ctx.send('Real-time update task is already running.')

# Command to stop the database update task
@bot.command()
async def stop_realtime(ctx):
    global update_task
    if update_task:
        try:
            update_task.cancel()
            await update_task
        except asyncio.CancelledError:
            pass
        update_task = None
        await ctx.send('Real-time update task stopped.')
    else:
        await ctx.send('Real-time update task is not running.')



# Run your bot


def get_data_link():
    connection = pyodbc.connect(db_connection_string)
    cursor = connection.cursor()

    # Your SQL query to retrieve data from the database
    query = """
    SELECT TOP 1 Picture.[picture], face.time, Personaltable.name, Personaltable.id, Department.dep_name, Picture.enrollid
    FROM Face
    INNER JOIN Personaltable ON Face.enrollid = Personaltable.enrollid
    INNER JOIN Department ON Department.[dep.no] = Personaltable.[dep.no]
    INNER JOIN Picture ON Face.enrollid = Picture.enrollid
    ORDER BY face.time DESC, Picture.[picture] Asc
    """ # Update the query as needed
    cursor.execute(query)

    data = cursor.fetchall()
    connection.close()

    return data

# Command to display data in Discord
@bot.command()
async def show_nen(ctx):
    # Call the function to get 'time' and 'name' columns from the database
    data = get_data_link()

    if not data:
        await ctx.send("No data found in the table.")
    else:
        # Format and send the data as a Discord message
        formatted_data = "\n".join([f"Date and Time: {row.time}\nName: {row.name}\nID: {row.id}\nDepartment: {row.dep_name}"for row in data])
        await ctx.send(f'Time and Name:\n```{formatted_data}```')

def get_time_name_data():
    connection = pyodbc.connect(db_connection_string)
    cursor = connection.cursor()

    # Specify the columns you want to select
    query = "SELECT time, name FROM dbo.Face "  # Select only 'time' and 'name'
    cursor.execute(query)

    data = cursor.fetchall()
    connection.close()

    return data

@bot.command()
async def get_time_name_all(ctx):
    # Call the function to get 'time' and 'name' columns from the database
    data = get_time_name_data()

    if not data:
        await ctx.send("No data found in the table.")
    else:
        # Format and send the data as a Discord message
        formatted_data = "\n".join([f"Time: {row.time}, Name: {row.name}" for row in data])
        await ctx.send(f'Time and Name:\n```{formatted_data}```')

# ... specific name
def get_time_name(name):
    connection = pyodbc.connect(db_connection_string)
    cursor = connection.cursor()

    # Use a parameterized query to retrieve rows where 'name' column matches the provided name
    query = "SELECT time, name FROM dbo.Face WHERE name LIKE ?"
    cursor.execute(query, f"%{name}%")  # Using % as a wildcard for any characters

    data = cursor.fetchall()
    connection.close()

    return data

@bot.command()
async def get_timename(ctx, name):

    # Call the function to get 'time' and 'name' columns from the database for the specified name
    data = get_time_name(name)

    if not data:
        await ctx.send(f"No data found for the name '{name}'.")
    else:
        # Format and send the data as a Discord message
        formatted_data = "\n".join([f"Date and Time: {row.time}, Name: {row.name}" for row in data])
        await ctx.send(f'Time and Name for "{name}":\n```{formatted_data}```')

@bot.command()
async def commands(ctx):
     await ctx.send('Available Commands as of right now: \n !get_timename(Put name here) \n !get_time_name_all(Gets all of time and name) \n !start_realtime(starts realtime data output) \n !stop_realtime(stops realtime data output)')
#===================================================================================================



bot.run('MTE1MDYyNjExNjY2MzUwODk5Mg.GKW-sK.OMUSUKln-od3xPYi1Hp3Kx4azpMEOl_JBw9RR4')