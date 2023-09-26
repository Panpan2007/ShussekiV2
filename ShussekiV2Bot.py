import discord
from discord.ext import commands
import pyodbc
import asyncio

# Define intents; enable message contents
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def hello(ctx): #!hello
    await ctx.send('Hello, world!')

server = 'Insert_Server_Name'
database = 'shusseki'
username = 'sa'
password = 'xxxxxx'

#connection to SQL Server
connection = pyodbc.connect(
    f'DRIVER=ODBC Driver 17 for SQL Server;'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
)
print(connection)

# Database connection configuration
db_connection_string = (
    f'DRIVER=ODBC Driver 17 for SQL Server;'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
)

def get_data():
    connection = pyodbc.connect(db_connection_string)
    cursor = connection.cursor()

    # SQL query to retrieve data from the database
    query = "SELECT * FROM dbo.Face"  # Update
    cursor.execute(query)

    data = cursor.fetchall()
    connection.close()

    return data

@bot.command()
async def get_top5(ctx):
    # Call the function to get data from the database
    data = get_data()

    if not data:
        await ctx.send("No data found in the table.")
    else:
        # Limit the data to the top 5 rows (you can adjust as needed)
        top5_data = data[:5]
        formatted_data = "\n".join(map(str, top5_data))
        await ctx.send(f'Top 5 rows:\n```{formatted_data}```')
#-----------------------------------------------------------------------------------------------------------------------

def get_data_from_database(name):
    connection = pyodbc.connect(db_connection_string)
    cursor = connection.cursor()

    # Use a parameterized query to retrieve rows where 'name' column contains 'tang'
    query = "SELECT * FROM dbo.Face WHERE name LIKE ?"
    cursor.execute(query, f"%{name}%")  # Using % as wildcard for any characters

    data = cursor.fetchall()
    connection.close()

    return data

@bot.command()
async def get_info(ctx, name):
    # Call the function to get data from the database
    data = get_data_from_database(name)

    if not data:
        await ctx.send(f"No data found for the name '{name}'.")
    else:
        formatted_data = "\n".join(map(str, data))
        await ctx.send(f'Data for the name "{name}":\n```{formatted_data}```')

#===============================================================================================
def get_bottom_row_from_database():
    connection = pyodbc.connect(db_connection_string)
    cursor = connection.cursor()

    # Use an ORDER BY clause to sort by a date or an appropriate column in descending order
    query = "SELECT TOP 1 * FROM dbo.Face ORDER BY time DESC"
    cursor.execute(query)

    data = cursor.fetchall()
    connection.close()

    return data

@bot.command()
async def get_latest(ctx):
    # Call the function to get the bottom row from the database
    data = get_bottom_row_from_database()

    if not data:
        await ctx.send("No data found in the table.")
    else:
        formatted_data = "\n".join(map(str, data))
        await ctx.send(f'Last Person That Logged In:\n```{formatted_data}```')
#=================================================================================================
# Create a cursor for executing SQL queries
cursor = connection.cursor()

# Define the SQL query (In this case, iteration depends on database)
sql_query = """
SELECT TOP 1  face.time, Personaltable.name, Personaltable.id, Department.dep_name
FROM Face
INNER JOIN Personaltable
ON Face.enrollid = Personaltable.enrollid
INNER JOIN Department
ON Department.[dep.no] = Personaltable.[dep.no]
ORDER BY Face.time DESC
"""


# Execute the query
cursor.execute(sql_query)
# Fetch and print the results
row = cursor.fetchone()
while row:
    print(row)
    row = cursor.fetchone()

# Close the cursor and the connection (optional)
cursor.close()
connection.close()

last_data = None

async def check_database_update():
    global last_data
    await bot.wait_until_ready()
    while not bot.is_closed():
        # Create a new connection and cursor for each iteration
        connection = pyodbc.connect(db_connection_string)
        cursor = connection.cursor()
        cursor.execute(sql_query)
        new_data = cursor.fetchone()

        if new_data is not None and new_data != last_data:
            # Database data has changed, send a message
            channel = bot.get_channel(1156206842695913492)  #Channel ID copied from discord
            if channel:
                formatted_data = "\n".join(map(str, [f"Date and Time: {new_data.time}\nName: {new_data.name}\nID: {new_data.id}\nDepartment: {new_data.dep_name}"]))
                await channel.send(f"Login update!\n```{formatted_data}```")

            last_data = new_data

        # Close the cursor and the connection
        cursor.close()
        connection.close()

        await asyncio.sleep(1)  # Check for updates every 1 second


@bot.event
async def on_ready():
    print(f'Shusseki online! {bot.user.name}')
    bot.loop.create_task(check_database_update())

    bot.run('INSERT_TOKEN') #Private Info