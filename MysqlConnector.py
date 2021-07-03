# @Benjamin Holmes
# @CS7700 Project
# @Summer 2020
# @Wright State

# This program implements the speedrun database described in my project proposal,
# and implements a number of transactions - inputting runners and fields, changing the status
# of runners, and maintaining a 'top 10' table for each game and version.

# We're going to implement this in MYSQL. The first step is to
# download the necessary libraries and start the connector
import mysql.connector as mysql
from mysql.connector import Error
from mysql.connector import errorcode
import datetime
import time

# This function will create the speedrunning database and associated tables.
def startRunDatabase():
    # This try/catch loop is added so we wipe the table and start fresh every time. If this was a real, persistent database, I would of course
    # blank this out!

    # The password is blanked out, because running MYSQL locally on this machine required the use of my system password! Add in your own to follow along
    cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password')
    mycursor = cnx.cursor()
    try:
        mycursor.execute("DROP DATABASE speedruns")
    except:
        pass
    mycursor.execute("CREATE DATABASE speedruns")

    # Now that we'cre created the database, connect to it and start up the cursor.
    cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
    mycursor = cnx.cursor()

    # Here we create the tables
    mycursor.execute("create table Players("
                     "user_name varchar(100) PRIMARY KEY, "
                     "is_referee BOOLEAN NOT NULL,"
                     "created_at TIMESTAMP NOT NULL)")
    # There should only be one "game + version" combo. We might have a different run for "Super Mario Bros. 1.0" and "Super Mario Bros. 1.2"
    mycursor.execute("create table Games(game_id int AUTO_INCREMENT PRIMARY KEY, "
                     "game_name varchar(100) NOT NULL, "
                     "game_version DECIMAL(4,2) NOT NULL, "
                     "UNIQUE KEY game_plus_version(game_name, game_version))")
    mycursor.execute("create table Categories(category_id int AUTO_INCREMENT PRIMARY KEY, "
                     "game_id int, "
                     "category varchar(100) NOT NULL, "
                     "FOREIGN KEY(game_id) REFERENCES Games(game_id) ON DELETE CASCADE, "
                     "UNIQUE KEY game_plus_category(game_id, category))")
    mycursor.execute("create table Runs(run_id int AUTO_INCREMENT PRIMARY KEY, "
                     "date_of_run DATETIME NOT NULL, "
                     "time_of_run TIME NOT NULL, "
                     "game_id int, "
                     "player_name varchar(100), "
                     "category_id int, "
                     "signed_by_ref boolean,"
                     "referee_name varchar(100),"
                     "run_logged TIMESTAMP NOT NULL,"
                     "FOREIGN KEY(game_id) REFERENCES Games(game_id) ON DELETE CASCADE, "
                     "FOREIGN KEY(player_name) REFERENCES Players(user_name) ON DELETE CASCADE, "
                     "FOREIGN KEY(referee_name) REFERENCES Players(user_name),"
                     "FOREIGN KEY(category_id) REFERENCES Categories(category_id) ON DELETE CASCADE,"
                     "UNIQUE KEY run_data(player_name, game_id, category_id, date_of_run, time_of_run))")
# Now it's time to start adding functions!

##
# First, creation and deletion
##

# Let's have one for adding players
def addPlayer(name):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        mycursor.execute("""insert into Players(user_name, created_at, is_referee) values(%s, %s, %s)""", (name, timestamp, False))
        print("Player Added Succesfully")
        cnx.commit()
    except mysql.Error as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# And one for deleting players
def removePlayer(name):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = "SELECT * FROM Players WHERE user_name = %s"
        adr = (name,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        print(myresult)
        if len(myresult) == 0:
            raise Exception('Could not find player with name for deletion: {}'.format(name))
        sql = "DELETE FROM Players WHERE user_name = %s"
        adr = (name,)
        mycursor.execute(sql,adr)
        # After we remove the player, we've gotta make sure we un-verify any runs that player is the ref for
        sql = "SELECT run_id FROM Runs WHERE referee_name = %s"
        adr = (name,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        for x in myresult:
            runid = x[0]
            unverifyRunWithId(runid)
        print("Player Deleted Succesfully")
        cnx.commit()
    except (mysql.Error, Exception) as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# One for adding refs...
def makeRef(name):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        # Let's make sure this person has an entry in Players first
        sql = "SELECT user_name from Players WHERE user_name = %s"
        adr = (name,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # If this isn't a player yet, add them now!
        if len(myresult) == 0:
            addPlayer(name)
            cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
            cnx.autocommit = False
            mycursor = cnx.cursor()
            mycursor.execute(sql,adr)
            myresult = mycursor.fetchall()
        name = myresult[0][0]
        sql = "Update Players SET is_referee = %s WHERE user_name = %s"
        adr = (True, name,)
        mycursor.execute(sql,adr)
        print("Ref Added Succesfully")
        cnx.commit()
    except mysql.Error as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# And one for deleting refs
def removeRef(name):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = "select user_name from Players WHERE user_name = %s"
        adr = (name,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            raise Exception('Could not find referee with name: {}'.format(name))
        else:
            name = myresult[0][0]
        sql = "Update Players SET is_referee = %s WHERE user_name = %s"
        adr = (False, name,)
        mycursor.execute(sql,adr)
        # We also want to eliminate any runs where this player was the ref
        sql = "SELECT run_id FROM Runs WHERE referee_name = %s"
        adr = (name,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        for x in myresult:
            runid = x[0]
            unverifyRunWithId(runid)
        print("Ref Deleted Succesfully")
        cnx.commit()
    except (mysql.Error, Exception) as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# One for adding games...
def addGame(game, version):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = "INSERT INTO Games (game_name, game_version) VALUES (%s, %s)"
        adr = (game, version,)
        mycursor.execute(sql,adr)
        print("Game Added Succesfully")
        cnx.commit()
    except mysql.Error as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# ...and for deleting games
def removeGame(game, version):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = "select game_id from Games WHERE game_name = %s and game_version = %s"
        adr = (game, version,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            raise Exception('Could not find game and version: {0} {1}'.format(game, version))

        sql = "DELETE FROM Games WHERE game_name = %s AND game_version = %s"
        adr = (game,version,)
        mycursor.execute(sql,adr)
        print("Game Deleted Succesfully")
        cnx.commit()
    except (mysql.Error, Exception) as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# One for adding categories...
def addCategory(game, version, category):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = "SELECT game_id from Games WHERE game_name = %s AND game_version = %s"
        adr = (game,version,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # If this isn't a game yet, add it now!
        if len(myresult) == 0:
            addGame(game, version)
            cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
            cnx.autocommit = False
            mycursor = cnx.cursor()
            mycursor.execute(sql,adr)
            myresult = mycursor.fetchall()
        id = myresult[0][0]
        sql = "INSERT INTO Categories (game_id, category) VALUES (%s, %s)"
        adr = (id, category,)
        mycursor.execute(sql,adr)
        print("Category Added Succesfully")
        cnx.commit()
    except mysql.Error as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# ...and for deleting categories
def removeCategory(game, version, category):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = "SELECT game_id from Games WHERE game_name = %s AND game_version = %s"
        adr = (game,version,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            raise Exception('Could not find game/version combo: {0}, {1}'.format(game, version))
        id = myresult[0][0]
        sql = "SELECT category_id from Categories WHERE game_id = %s AND category = %s"
        adr = (id, category,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            raise Exception('Could not find game/version/category combo: {0}, {1}, {2}'.format(game, version, category))
        sql = "DELETE FROM Categories WHERE game_id = %s AND category = %s"
        adr = (id,category,)
        mycursor.execute(sql,adr)
        print("Game Deleted Succesfully")
        cnx.commit()
    except (mysql.Error, Exception) as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# One for adding runs...
def addRun(player, game, version, category, hours, minutes, seconds, day, month, year):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = "SELECT game_id from Games WHERE game_name = %s AND game_version = %s"
        adr = (game,version,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # If this isn't a game yet, do NOT add - throw an error!
        if len(myresult) == 0:
            raise Exception('Could not find game/version combo: {0}, {1}'.format(game, version))
        gameid = myresult[0][0]
        sql = "SELECT category_id from Categories WHERE game_id = %s and category = %s"
        adr = (gameid, category)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # We'll also error out if we can't find the category
        if len(myresult) == 0:
            raise Exception('Could not find game/category: {0}, {1}'.format(game, category))
        categoryid = myresult[0][0]
        sql = "SELECT user_name from Players WHERE user_name = %s"
        adr = (player,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # Likewise, we'll throw an exception if we can't find the player
        if len(myresult) == 0:
            raise Exception('Could not find player: {0}'.format(player))
        playername = myresult[0][0]

        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

        # We'll make the time object here from the HMS provided
        timeOfRun = datetime.time(hours,minutes,seconds)
        dateOfRun = datetime.datetime(year, month, day)


        sql = "INSERT INTO Runs (date_of_run, time_of_run, game_id, player_name, category_id, signed_by_ref, run_logged) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        adr = (dateOfRun, timeOfRun, gameid, playername, categoryid, False, timestamp, )
        mycursor.execute(sql,adr)
        print("Run Added Succesfully")
        cnx.commit()
    except mysql.Error as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# ...and for deleting runs
def removeRun(player, game, version, category, hours, minutes, seconds, day, month, year):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        timeOfRun = datetime.time(hours,minutes,seconds)
        dateOfRun = datetime.datetime(year, month, day)
        timeOfRun = datetime.timedelta(hours=timeOfRun.hour, minutes=timeOfRun.minute, seconds=timeOfRun.second)

        sql = "SELECT game_id from Games WHERE game_name = %s AND game_version = %s"
        adr = (game,version,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # If this isn't a game yet, do NOT add - throw an error!
        if len(myresult) == 0:
            raise Exception('Could not find game/version combo: {0}, {1}'.format(game, version))
        gameid = myresult[0][0]
        sql = "SELECT category_id from Categories WHERE game_id = %s and category = %s"
        adr = (gameid, category)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # We'll also error out if we can't find the category
        if len(myresult) == 0:
            raise Exception('Could not find game/category: {0}, {1}'.format(game, category))
        categoryid = myresult[0][0]

        sql = "SELECT run_id from Runs WHERE player_name = %s AND game_id = %s AND category_id = %s AND date_of_run = %s AND time_of_run = %s"
        adr = (player, gameid, categoryid, dateOfRun, timeOfRun,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            raise Exception('Could not find this run!: {0}, {1}'.format(game, version))
        runid = myresult[0][0]
        sql = "DELETE FROM Runs WHERE run_id = %s"
        adr = (runid,)
        mycursor.execute(sql,adr)
        print("Run Deleted Succesfully")
        cnx.commit()
    except (mysql.Error, Exception) as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

def verifyRun(player, game, version, category, hours, minutes, seconds, day, month, year, referee):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()

        # First, a simple check - no verifying your own runs!
        if referee == player:
            raise Exception('Sorry, no verifying your own runs!: {0}, {1}'.format(game, version))

        sql = "SELECT is_referee FROM Players WHERE user_name = %s"
        adr = (referee,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            raise Exception('Could not find referee!: {}'.format(referee))
        isref = myresult[0][0]
        if not isref:
            raise Exception('Player is not ref!: ()'.format(referee))

        timeOfRun = datetime.time(hours,minutes,seconds)
        dateOfRun = datetime.datetime(year, month, day)
        timeOfRun = datetime.timedelta(hours=timeOfRun.hour, minutes=timeOfRun.minute, seconds=timeOfRun.second)
        sql = "SELECT game_id from Games WHERE game_name = %s AND game_version = %s"
        adr = (game,version,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # If this isn't a game yet, do NOT add - throw an error!
        if len(myresult) == 0:
            raise Exception('Could not find game/version combo: {0}, {1}'.format(game, version))
        gameid = myresult[0][0]
        sql = "SELECT category_id from Categories WHERE game_id = %s and category = %s"
        adr = (gameid, category,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # We'll also error out if we can't find the category
        if len(myresult) == 0:
            raise Exception('Could not find game/category: {0}, {1}'.format(game, category))
        categoryid = myresult[0][0]

        sql = "SELECT run_id from Runs WHERE player_name = %s AND game_id = %s AND category_id = %s AND date_of_run = %s AND time_of_run = %s"
        adr = (player, gameid, categoryid, dateOfRun, timeOfRun,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            raise Exception('Could not find this run!: {0}, {1}'.format(game, version))
        runid = myresult[0][0]
        sql = "UPDATE Runs Set signed_by_ref = %s, referee_name = %s WHERE run_id = %s"
        adr = (True, referee, runid, )
        mycursor.execute(sql,adr)
        print("Run Verified Succesfully")
        cnx.commit()
    except (mysql.Error, Exception) as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

def unverifyRun(player, game, version, category, hours, minutes, seconds, day, month, year):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        timeOfRun = datetime.time(hours,minutes,seconds)
        dateOfRun = datetime.datetime(year, month, day)
        timeOfRun = datetime.timedelta(hours=timeOfRun.hour, minutes=timeOfRun.minute, seconds=timeOfRun.second)
        sql = "SELECT game_id from Games WHERE game_name = %s AND game_version = %s"
        adr = (game,version,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # If this isn't a game yet, do NOT add - throw an error!
        if len(myresult) == 0:
            raise Exception('Could not find game/version combo: {0}, {1}'.format(game, version))
        gameid = myresult[0][0]
        sql = "SELECT category_id from Categories WHERE game_id = %s and category = %s"
        adr = (gameid, category,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        # We'll also error out if we can't find the category
        if len(myresult) == 0:
            raise Exception('Could not find game/category: {0}, {1}'.format(game, category))
        categoryid = myresult[0][0]

        sql = "SELECT run_id from Runs WHERE player_name = %s AND game_id = %s AND category_id = %s AND date_of_run = %s AND time_of_run = %s"
        adr = (player, gameid, categoryid, dateOfRun, timeOfRun,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            raise Exception('Could not find this run!: {0}, {1}'.format(game, version))
        runid = myresult[0][0]
        sql = "UPDATE Runs Set signed_by_ref = %s, referee_name = NULL WHERE run_id = %s"
        adr = (False, runid, )
        mycursor.execute(sql,adr)
        print("Run Un-Verified Succesfully")
        cnx.commit()
    except (mysql.Error, Exception) as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# This is for ease when I'm doing updates (like when a player is deleted)
def unverifyRunWithId(runId):
    try:
        # Now that we've created the database, connect to it and start up the cursor.
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = "SELECT run_id from Runs WHERE run_id = %s"
        adr = (runId,)
        mycursor.execute(sql,adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            raise Exception('Could not find this run!')
        runid = myresult[0][0]
        sql = "UPDATE Runs Set signed_by_ref = %s, referee_name = NULL WHERE run_id = %s"
        adr = (False, runid, )
        mycursor.execute(sql,adr)
        print("Run Un-Verified Succesfully")
        cnx.commit()
    except (mysql.Error, Exception) as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# We also want to be able to display the leaderboards
def displayAllLeaderboards():
    try:
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        mycursor.execute("SELECT DISTINCT game_id FROM Runs")
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            print("************")
            print('LEADERBOARDS ARE EMPTY! WHY NOT ADD SOME RUNS!?')
            print("************")
        for row in myresult:
            gameid = row[0]
            sql = ("SELECT game_name, game_version FROM Games WHERE game_id = %s")
            adr = (gameid,)
            mycursor.execute(sql, adr)
            gameresults = mycursor.fetchall()
            if len(gameresults) == 0:
                raise Exception ("ERROR IN GAME IDS - Database in error!")
            gname = gameresults[0][0]
            gversion = gameresults[0][1]
            sql = ("SELECT category, category_id FROM Categories WHERE game_id = %s")
            mycursor.execute(sql, adr)
            categoryresults = mycursor.fetchall()
            # There might be a game with no categories - we don't want to throw an error, it just won't display anything.
            for category in categoryresults:
                cat = category[0]
                catid = category[1]
                print('\n*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
                print('LEADERBOARD FOR \n')
                print('{} - Version: {} - Category: {}'.format(gname, gversion, cat))
                sql = ("SELECT time_of_run, date_of_run, player_name, referee_name FROM Runs WHERE game_id = %s AND category_id = %s AND signed_by_ref = %s ORDER BY time_of_run ASC LIMIT 3")
                adr = (gameid, catid, True,)
                mycursor.execute(sql, adr)
                leaderboardResults = mycursor.fetchall()
                if len(leaderboardResults) == 0:
                    print("************")
                    print('LEADERBOARDS ARE EMPTY! WHY NOT ADD SOME RUNS!?')
                    print("************")
                for boardResult in leaderboardResults:
                    time = boardResult[0]
                    date = boardResult[1].date()
                    runner = boardResult[2]
                    ref = boardResult[3]
                    print("{} BY RUNNER {} ON {} AND APPROVED BY {}".format(time, runner, date, ref))
        print('\n*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')

        mycursor.execute("SELECT * FROM Runs ORDER BY time_of_run ASC LIMIT 3")
        myresult = mycursor.fetchall()
        id = myresult[0][0]
        sql = ("SELECT * FROM Runs WHERE game_id = %s")
        adr = (id,)
        mycursor.execute(sql, adr)
        myresult = mycursor.fetchall()
        for x in myresult:
            print(x)
    except mysql.Error as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# This is for output of the leaderboards - the top 3 times - for all games
def displayLeaderboardForGame(game):
    try:
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = ("SELECT DISTINCT game_id FROM Games WHERE game_name = %s")
        adr = (game,)
        mycursor.execute(sql, adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            print("************")
            print('LEADERBOARDS ARE EMPTY! WHY NOT ADD SOME RUNS!?')
            print("************")
        for row in myresult:
            gameid = row[0]
            sql = ("SELECT game_name, game_version FROM Games WHERE game_id = %s")
            adr = (gameid,)
            mycursor.execute(sql, adr)
            gameresults = mycursor.fetchall()
            if len(gameresults) == 0:
                raise Exception ("ERROR IN GAME IDS - Database in error!")
            gname = gameresults[0][0]
            gversion = gameresults[0][1]
            sql = ("SELECT category FROM Categories WHERE game_id = %s")
            mycursor.execute(sql, adr)
            categoryresults = mycursor.fetchall()
            # There might be a game with no categories - we don't want to throw an error, it just won't display anything.
            for category in categoryresults:
                cat = category[0]
                print('\n*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
                print('LEADERBOARD FOR \n')
                print('{} - Version: {} - Category: {}'.format(gname, gversion, cat))
                sql = ("SELECT time_of_run, date_of_run, player_name, referee_name FROM Runs WHERE game_id = %s AND signed_by_ref = %s ORDER BY time_of_run ASC LIMIT 3")
                adr = (gameid, True,)
                mycursor.execute(sql, adr)
                leaderboardResults = mycursor.fetchall()
                for boardResult in leaderboardResults:
                    time = boardResult[0]
                    date = boardResult[1].date()
                    runner = boardResult[2]
                    ref = boardResult[3]
                    print("{} BY RUNNER {} ON {} AND APPROVED BY {}".format(time, runner, date, ref))
        print('\n*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')

        mycursor.execute("SELECT * FROM Runs ORDER BY time_of_run ASC LIMIT 3")
        myresult = mycursor.fetchall()
        id = myresult[0][0]
        sql = ("SELECT * FROM Runs WHERE game_id = %s")
        adr = (id,)
        mycursor.execute(sql, adr)
        myresult = mycursor.fetchall()
        for x in myresult:
            print(x)
    except mysql.Error as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# This is for output of the leaderboards - the top 3 times - per a particular game/version
def displayLeaderboardForGameAndVersion(game, version):
    try:
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = ("SELECT DISTINCT game_id FROM Games WHERE game_name = %s AND game_version = %s")
        adr = (game, version,)
        mycursor.execute(sql, adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            print("************")
            print('LEADERBOARDS ARE EMPTY! WHY NOT ADD SOME RUNS!?')
            print("************")
        for row in myresult:
            gameid = row[0]
            sql = ("SELECT game_name, game_version FROM Games WHERE game_id = %s")
            adr = (gameid,)
            mycursor.execute(sql, adr)
            gameresults = mycursor.fetchall()
            if len(gameresults) == 0:
                raise Exception ("ERROR IN GAME IDS - Database in error!")
            gname = gameresults[0][0]
            gversion = gameresults[0][1]
            sql = ("SELECT category FROM Categories WHERE game_id = %s")
            mycursor.execute(sql, adr)
            categoryresults = mycursor.fetchall()
            # There might be a game with no categories - we don't want to throw an error, it just won't display anything.
            for category in categoryresults:
                cat = category[0]
                print('\n*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
                print('LEADERBOARD FOR')
                print('{} - Version: {} - Category: {}'.format(gname, gversion, cat))
                print()
                sql = ("SELECT time_of_run, date_of_run, player_name, referee_name FROM Runs WHERE game_id = %s AND signed_by_ref = %s ORDER BY time_of_run ASC LIMIT 3")
                adr = (gameid, True,)
                mycursor.execute(sql, adr)
                leaderboardResults = mycursor.fetchall()
                for boardResult in leaderboardResults:
                    time = boardResult[0]
                    date = boardResult[1].date()
                    runner = boardResult[2]
                    ref = boardResult[3]
                    print("{} BY RUNNER {} ON {} AND APPROVED BY {}".format(time, runner, date, ref))
        print('\n*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')

        mycursor.execute("SELECT * FROM Runs ORDER BY time_of_run ASC LIMIT 3")
        myresult = mycursor.fetchall()
        id = myresult[0][0]
        sql = ("SELECT * FROM Runs WHERE game_id = %s")
        adr = (id,)
        mycursor.execute(sql, adr)
        myresult = mycursor.fetchall()
        for x in myresult:
            print(x)
    except mysql.Error as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")

# This is for output of the leaderboards - the top 3 times - per a particular game/version AND category
def displayLeaderboardForGameAndVersionAndCategory(game, version, category):
    try:
        cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database='speedruns')
        cnx.autocommit = False
        mycursor = cnx.cursor()
        sql = ("SELECT DISTINCT game_id FROM Games WHERE game_name = %s AND game_version = %s")
        adr = (game, version,)
        mycursor.execute(sql, adr)
        myresult = mycursor.fetchall()
        if len(myresult) == 0:
            print("************")
            print('LEADERBOARDS ARE EMPTY! WHY NOT ADD SOME RUNS!?')
            print("************")
        for row in myresult:
            gameid = row[0]
            sql = ("SELECT game_name, game_version FROM Games WHERE game_id = %s")
            adr = (gameid,)
            mycursor.execute(sql, adr)
            gameresults = mycursor.fetchall()
            if len(gameresults) == 0:
                raise Exception ("ERROR IN GAME IDS - Database in error!")
            gname = gameresults[0][0]
            gversion = gameresults[0][1]
            sql = ("SELECT category, category_id FROM Categories WHERE game_id = %s and category = %s")
            adr = (gameid, category)
            mycursor.execute(sql, adr)
            categoryresults = mycursor.fetchall()
            if len(categoryresults) == 0:
                print("************")
                print('LEADERBOARDS FOR {} - {} - {} ARE EMPTY! WHY NOT ADD SOME RUNS!?'.format(gname, gversion, category))
                print("************")
            # There might be a game with no categories - we don't want to throw an error, it just won't display anything.
            for category in categoryresults:
                cat = category[0]
                catid = category[1]
                print('\n*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
                print('LEADERBOARD FOR')
                print('{} - Version: {} - Category: {}'.format(gname, gversion, cat))
                print()
                sql = ("SELECT time_of_run, date_of_run, player_name, referee_name FROM Runs WHERE game_id = %s AND signed_by_ref = %s AND category_id = %s ORDER BY time_of_run ASC LIMIT 3")
                adr = (gameid, True, catid,)
                mycursor.execute(sql, adr)
                leaderboardResults = mycursor.fetchall()
                for boardResult in leaderboardResults:
                    time = boardResult[0]
                    date = boardResult[1].date()
                    runner = boardResult[2]
                    ref = boardResult[3]
                    print("{} BY RUNNER {} ON {} AND APPROVED BY {}".format(time, runner, date, ref))
        print('\n*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')

        mycursor.execute("SELECT * FROM Runs ORDER BY time_of_run ASC LIMIT 3")
        myresult = mycursor.fetchall()
        id = myresult[0][0]
        sql = ("SELECT * FROM Runs WHERE game_id = %s")
        adr = (id,)
        mycursor.execute(sql, adr)
        myresult = mycursor.fetchall()
        for x in myresult:
            print(x)
    except mysql.Error as error:
        print("Failed to update record to database rollback: {}".format(error))
        # reverting changes because of exception
        cnx.rollback()
    finally:
        # closing database connection.
        if (cnx.is_connected()):
            mycursor.close()
            cnx.close()
            print("connection is closed")


startRunDatabase()
#########
# Now is the time to start adding in transactions. We'll start with an empty database
########

cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database = 'speedruns')
mycursor = cnx.cursor()

print("PLAYERS")
mycursor.execute("select * from Players")
myresult = mycursor.fetchall()
field_names = [i[0] for i in mycursor.description]
print(field_names)
for x in myresult:
  print(x)

print("GAMES")
mycursor.execute("select * from Games")
myresult = mycursor.fetchall()
field_names = [i[0] for i in mycursor.description]
print(field_names)
for x in myresult:
  print(x)

print("CATEGORIES")
mycursor.execute("select * from Categories")
field_names = [i[0] for i in mycursor.description]
print(field_names)
myresult = mycursor.fetchall()
for x in myresult:
  print(x)

print("RUNS")
mycursor.execute("select * from Runs")
field_names = [i[0] for i in mycursor.description]
print(field_names)
myresult = mycursor.fetchall()
for x in myresult:
  print(x)

# Then we'll add in some players...
addPlayer('Bacterx1')
addPlayer('Player1')
addPlayer('Player2')
addPlayer('Player3')
addPlayer('Player4')
addPlayer('Player5')
addPlayer('Player6')

# Make a few of them refs...
makeRef('Bacterx1')
makeRef('Player1')
makeRef('Player5')

# And remove one.
removePlayer('Player4')

# Let's not let me be a ref.
removeRef('Bacterx1')

# And try to do some things that will cause errors
removePlayer('NewPlayer')
addPlayer('Bacterx1')

# Now we'll add games
addGame('Donkey Kong', 1.2)
addGame('Super Mario', 1.2)
addGame('Donkey Kong', 1.2)
addGame('Donkey Kong', 1.0)
addGame('Donkey Kong', 1.1)
addGame('F-Zero', 1.1)

# Take out some, including one that doesnt' exist...
removeGame('Donkey Kong', 1.0)
removeGame('Fairie Tale', 2.3)

# And add in some categories.
addCategory('Donkey Kong', 1.2, 'Any %')
addCategory('Donkey Kong', 1.1, 'Any %')
addCategory('Donkey Kong', 1.2, '100%')
addCategory('Donkey Kong', 1.2, 'No Glitches')
addCategory('Super Mario', 1.2, 'Any %')
addCategory('F-Zero', 1.1, 'Any %')

# Let's cause some category errors!
addCategory('Donkey Kong', 1.2, 'Any %')
removeCategory('Fairie Tale', 2.3, 'Any %')
removeCategory('Donkey Kong', 1.2, 'Fake %')
removeCategory('Donkey Kong', 1.2, 'No Glitches')

# Finally, we'll add some runs
addRun('Bacterx1', 'Donkey Kong', 1.2, 'Any %', 1, 12, 24, 14, 6, 2020)
addRun('Player2', 'Donkey Kong', 1.2, 'Any %', 0, 56, 24, 14, 6, 2020)
addRun('Player6', 'Donkey Kong', 1.2, 'Any %', 0, 55, 24, 14, 6, 2020)
addRun('Player5', 'Donkey Kong', 1.2, '100%', 0, 22, 24, 14, 6, 2020)
addRun('Player5', 'Donkey Kong', 1.2, '100%', 0, 21, 24, 14, 6, 2020)
addRun('Bacterx1', 'Donkey Kong', 1.2, 'Any %', 0, 53, 24, 14, 6, 2020)
addRun('Bacterx1', 'Donkey Kong', 1.1, 'Any %', 1, 12, 24, 14, 6, 2020)
addRun('Player5', 'Super Mario', 1.2, 'Any %', 0, 15, 3, 2, 5, 1998)
addRun('Bacterx1', 'F-zero', 1.1, 'Any %', 1, 2, 3, 1, 1, 2020)

# Remove some... (and cause some errors)
removeRun('Player5', 'Donkey Kong', 1.2, '100%', 0, 21, 24, 14, 6, 2020)

removeRun('Player5', 'Donkey Kong', 1.2, '100%', 0, 21, 24, 14, 6, 2020)
removeRun('Player5', 'Donkey Kong', 1.3, '100%', 0, 21, 24, 14, 6, 2020)
removeRun('Player5', 'Donkey Kong', 1.2, 'Fake%', 0, 21, 24, 14, 6, 2020)
addRun('Bacterx1', 'F-zero', 1.1, 'Any %', 1, 2, 3, 1, 1, 2020)

# Verify some...
verifyRun('Bacterx1', 'Donkey Kong', 1.2, 'Any %', 1, 12, 24, 14, 6, 2020, 'Player5')
verifyRun('Player2', 'Donkey Kong', 1.2, 'Any %', 0, 56, 24, 14, 6, 2020, 'Player5')
verifyRun('Player6', 'Donkey Kong', 1.2, 'Any %', 0, 55, 24, 14, 6, 2020, 'Player5')
verifyRun('Bacterx1', 'Donkey Kong', 1.2, 'Any %', 0, 53, 24, 14, 6, 2020, 'Player5')
verifyRun('Bacterx1', 'Donkey Kong', 1.1, 'Any %', 1, 12, 24, 14, 6, 2020, 'Player1')
verifyRun('Player5', 'Donkey Kong', 1.2, '100%', 0, 22, 24, 14, 6, 2020, 'Player1')

verifyRun('Bacterx1', 'F-zero', 1.1, 'Any %', 1, 2, 3, 1, 1, 2020, 'Player5')
verifyRun('Player5', 'Super Mario', 1.2, 'Any %', 0, 15, 3, 2, 5, 1998, 'Player1')

# These are errors - can't verify yourself, can't verify if you're not a ref!
verifyRun('Player5', 'Donkey Kong', 1.2, '100%', 0, 22, 24, 14, 6, 2020, 'Player5')
verifyRun('Player5', 'Donkey Kong', 1.2, '100%', 0, 22, 24, 14, 6, 2020, 'Bacterx1')

# And that's that! We'll display them all!
cnx = mysql.connect(user='root', password=FakePassw0rd, host='127.0.0.1', auth_plugin='mysql_native_password', database = 'speedruns')
mycursor = cnx.cursor()

print("PLAYERS")
mycursor.execute("select * from Players")
myresult = mycursor.fetchall()
field_names = [i[0] for i in mycursor.description]
print(field_names)
for x in myresult:
  print(x)

print("REFS")
mycursor.execute("select * from Players WHERE is_referee = True")
myresult = mycursor.fetchall()
field_names = [i[0] for i in mycursor.description]
print(field_names)
for x in myresult:
  print(x)

print("GAMES")
mycursor.execute("select * from Games")
myresult = mycursor.fetchall()
field_names = [i[0] for i in mycursor.description]
print(field_names)
for x in myresult:
  print(x)

print("CATEGORIES")
mycursor.execute("select * from Categories")
field_names = [i[0] for i in mycursor.description]
print(field_names)
myresult = mycursor.fetchall()
for x in myresult:
  print(x)

print("RUNS")
mycursor.execute("select * from Runs")
field_names = [i[0] for i in mycursor.description]
print(field_names)
myresult = mycursor.fetchall()
for x in myresult:
  print(x)
