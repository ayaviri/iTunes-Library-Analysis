import mysql.connector
import xml.etree.ElementTree as ET
import sys, re
from datetime import datetime

propertiesOfInterest = {"Persistent ID" : 0, "Name" : 0, "Artist" : 0, "Kind" : 0, "Total Time" : 0, "Year" : 0,
 "Date Added" : 0, "Play Count" : 0}

# connecting to the database
databaseConnection = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "t33lUBd0r",
    database = "itunes", 
    autocommit = True)

cursor = databaseConnection.cursor()

# parsing information from xml, outputs a list of tuples to insert into the database
# this will not include the three columns that must be included before the insertion 
# of the row in the database
# NOTE THAT EACH ELEMENT WILL BE OF TYPE STRING
def parseXML(filePath):
    tree = ET.parse(filePath)
    root = tree.getroot()
    libraryDictionary = list(root.find("dict"))
    for element in libraryDictionary:
        if element.tag == "date":
            currentUploadDate = re.sub("[TZ]", " ", element.text[:-1])
        if element.tag == "dict":
            trackDictionary = element
    trackDictionary = trackDictionary.findall("dict")
    newEntry = []
    for trackProperties in trackDictionary:
        currentTrack = ()
        # some track properties are longer than others, i must instead just loop through all of them 
        for i in range(int(len(trackProperties))):
            if i % 2 == 0:
                keyElement = trackProperties[i]
                valueElement = trackProperties[i + 1]
                if keyElement.text in propertiesOfInterest:
                    if keyElement.text == "Date Added":
                        currentTrack += (re.sub("[T]", " ", valueElement.text[:-1]),)
                    else: 
                        currentTrack += (valueElement.text,)
        currentTrack += (currentUploadDate,)
        newEntry += [currentTrack]
    print("number of new entries: " + str(len(newEntry)))
    print("first entry: " + str(newEntry[0]))
    return newEntry

# inserts the new entry, represented as a list of tuples(rows)
# adds the following additional rows to each entry before insertion: 
# Last_Upload_Date, Current_Upload_Date, Relative_Play_Count  
def insertEntry(newEntry): 
    for track in newEntry:
        persistentId = track[7] # this is where the primary key of the track is stored
        existenceQuery = "select exists(select * from song where Persistent_ID = %s)"
        cursor.execute(existenceQuery, (persistentId,))
        queryResult = cursor.fetchall()
        if queryResult[0] == (0,):
            # current song is a new addition to database
            dateAdded = track[5]
            lastUploadDate = dateAdded
            track += (lastUploadDate,) # setting date added to library as last upload date
            absolutePlayCount = track[6]
            relativePlayCount = absolutePlayCount
            track += (relativePlayCount,) # setting relative play count as absolute play count
            insertTrackStatement = "insert into song (Name, Artist, Kind, Total_Time, Year, Date_Added, Play_Count, Persistent_ID, Current_Upload_Date, Last_Upload_Date, Relative_Play_Count) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(insertTrackStatement, track)
        else: 
            # current song is already contained in database
            uploadDateQuery = "select Current_Upload_Date from song where Persistent_ID = %s"
            cursor.execute(uploadDateQuery, (persistentId,))
            lastUploadDate = cursor.fetchall()[0][0] # update both last and current upload dates
            lastUploadDate = datetime.strftime(lastUploadDate, "%Y-%m-%d %H:%M:%S")
            currentUploadDate = track[8]
            updateLastUploadDate = "update song set Last_Upload_Date = '%(lastUploadDate)s' where Persistent_ID = '%(persistentId)s'"
            updateCurrentUploadDate = "update song set Current_Upload_Date = '%(currentUploadDate)s' where Persistent_ID = '%(persistentId)s'"
            cursor.executemany(updateLastUploadDate, {"lastUploadDate" : lastUploadDate, "persistentId" : persistentId})
            cursor.executemany(updateCurrentUploadDate, {"currentUploadDate" : currentUploadDate, "persistentId" : persistentId})
            databaseConnection.commit()

            playCountQuery = "select Play_Count from song where Persistent_ID = %s"
            cursor.execute(playCountQuery, (persistentId,))
            oldPlayCount = cursor.fetchall()[0][0] # update both absolute and relative play counts
            absolutePlayCount = int(track[6])
            relativePlayCount = absolutePlayCount - oldPlayCount
            updateAbsolutePlayCount = "update song set Play_Count = %(absolutePlayCount)s where Persistent_ID = %(persistentId)s"
            updateRelativePlayCount = "update song set Relative_Play_Count = %(relativePlayCount)s where Persistent_ID = %(persistentId)s"
            cursor.execute(updateAbsolutePlayCount, {"absolutePlayCount" : absolutePlayCount, "persistentId" : persistentId})
            cursor.execute(updateRelativePlayCount, {"relativePlayCount" : relativePlayCount, "persistentId" : persistentId})
            databaseConnection.commit()

def getRelativeStatistics(n):
    print("Relative Statistics:")
    elapsedTime = __getRelativeTimeElapsed()
    print("Time elapsed since last upload: " + str(elapsedTime.days) + " days")
    topSongs = __getRelativeTopSongs(n)
    print("Your top " + str(n) + " songs by play count")
    for song in topSongs: 
        print("Name: " + str(song[0]) + ", Artist: " + str(song[1]) + ", Play Count: " + str(song[2]))
    topArtistsByPlayCount = __getRelativeTopArtistsByPlayCount(n)
    for artist in topArtistsByPlayCount:
        print("Artist: " + str(artist[0]) + ", Play Count: " + str(artist[1]))
    topArtistsByPlayTime = __getRelativeTopArtistsByPlayTime(n)
    for artist in topArtistsByPlayTime:
        print("Artist: " + str(artist[0]) + ", Play Time (Minutes): " + str(artist[1]))
    timeListened = __getRelativeTimeListened()
    print("Minutes of music listened to since last upload: " + str(timeListened) + " minutes")
    
# returns a timedelta object with described the time elapsed between the current upload and the previous upload
def __getRelativeTimeElapsed():
    currentTimestampQuery = "select Current_Upload_Date from song order by Current_Upload_Date desc limit 1"
    cursor.execute(currentTimestampQuery)
    currentTimestamp = cursor.fetchall()[0][0]
    lastUploadTimestampQuery = "select Last_Upload_Date from song order by Last_Upload_Date asc limit 1"
    cursor.execute(lastUploadTimestampQuery)
    lastUploadTimestamp = cursor.fetchall()[0][0]
    elapsedTime = currentTimestamp - lastUploadTimestamp
    return elapsedTime

# returns a list of the top n songs, each represented by the following tuple: (name, artist, playcount)
def __getRelativeTopSongs(n):
    topSongsQuery = "select Name, Artist, Relative_Play_Count from song order by Relative_Play_Count desc limit %s"
    cursor.execute(topSongsQuery, (n,))
    topSongs = cursor.fetchall()
    return topSongs

# returns a list of the top n artists by play count, each represented by the following tuple: (artist, playcount)
def __getRelativeTopArtistsByPlayCount(n):
    topArtistsQuery = "select Artist, sum(Relative_Play_Count) as Relative_Play_Count from song group by Artist order by Relative_Play_Count desc limit %s"
    cursor.execute(topArtistsQuery, (n,))
    topArtists = cursor.fetchall()
    return topArtists

# returns a list of the top n artists by play time, each represented by the following tuple: (artist, playtime (minutes))
def __getRelativeTopArtistsByPlayTime(n):
    topArtistsQuery = "select Artist, sum((Relative_Play_Count * Total_Time) / 60000) as Minutes_Listened from song group by Artist order by Minutes_Listened desc limit %s"
    cursor.execute(topArtistsQuery, (n,))
    topArtists = cursor.fetchall()
    return topArtists

# returns the total number of minutes listened to between the last and current uploads
def __getRelativeTimeListened():
    timeQuery = "select sum((Relative_Play_Count * Total_Time) / 60000) as Minutes_Listened from song"
    cursor.execute(timeQuery)
    timeListened = int(cursor.fetchall()[0][0])
    return timeListened

def getAbsoluteStatistics(n):
    print("Absolute Statistics:")
    elapsedTime = __getAbsoluteTimeElapsed()
    print("Absolute time elapsed: " + str(elapsedTime.days) + " days")
    topSongs = __getRelativeTopSongs(n)
    print("Your top " + str(n) + " songs by play count")
    for song in topSongs: 
        print("Name: " + str(song[0]) + ", Artist: " + str(song[1]) + ", Play Count: " + str(song[2]))
    topArtistsByPlayCount = __getRelativeTopArtistsByPlayCount(n)
    for artist in topArtistsByPlayCount:
        print("Artist: " + str(artist[0]) + ", Play Count: " + str(artist[1]))
    topArtistsByPlayTime = __getRelativeTopArtistsByPlayTime(n)
    for artist in topArtistsByPlayTime:
        print("Artist: " + str(artist[0]) + ", Play Time (Minutes): " + str(artist[1]))
    timeListened = __getRelativeTimeListened()
    print("Minutes of music listened to since last upload: " + str(timeListened) + " minutes")

def __getAbsoluteTimeElapsed():
    currentTimestampQuery = "select Current_Upload_Date from song order by Current_Upload_Date desc limit 1"
    cursor.execute(currentTimestampQuery)
    currentTimestamp = cursor.fetchall()[0][0]
    creationTimestampQuery = "select Date_Added from song order by Date_Added asc limit 1"
    cursor.execute(creationTimestampQuery)
    creationTimestamp = cursor.fetchall()[0][0]
    elapsedTime = currentTimestamp - creationTimestamp 
    return elapsedTime

def __getRelativeTopSongs():
    # TODO: get the top five songs by play time
    print("hello world")

# for example, run python main.py 122221.xml
def main():
    filePath = sys.argv[1]
    newEntry = parseXML("wrapped/" + str(filePath))
    insertEntry(newEntry)
    n = int(input("Enter the number of results you would like to retrieve: "))
    # relative information
    getRelativeStatistics(n)
    # absolute information
    getAbsoluteStatistics(n)
    cursor.close()
    databaseConnection.close()

main()