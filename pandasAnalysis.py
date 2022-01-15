import xml.etree.ElementTree as ET # in order to parse xml 
import pandas as pd

columnsOfInterest = {"Name" : 0, "Artist" : 0, "Kind" : 0, "Total Time" : 0, "Year" : 0,
 "Date Added" : 0, "Play Count" : 0, }

# obtains a list of dictionaries where each dictionary is a track
def obtainTracklist(filePath):
    tree = ET.parse(filePath)
    root = tree.getroot()
    libraryDictionary = list(root.find("dict"))
    for element in libraryDictionary:
        if element.tag == "dict":
            trackDictionary = element
    listOfDictionaries = []
    # iterating through each track
    for track in trackDictionary:
        if track.tag == "dict":
            currentTrack = {}
            for i in range(int(len(track) / 2)):
                keyElement = track[2 * i]
                valueElement = track[(2 * i) + 1]
                if keyElement.text in columnsOfInterest:
                    if valueElement.tag == "integer":
                        currentTrack[keyElement.text] = int(valueElement.text)
                    else:
                        currentTrack[keyElement.text] = valueElement.text
            listOfDictionaries += [currentTrack]
    return listOfDictionaries

def topSongs(n, dataframe):
    print("Your top " + str(n) + " songs by Play Count")
    print(dataframe.filter(items = ["Artist", "Name", "Play Count"]).sort_values(by = "Play Count", ascending = False).head(n).set_index("Name"))

def topArtistsByPlayCount(n, dataframe):
    print("Your top " + str(n) + " artists by Play Count")
    print(dataframe.filter(items = ["Artist", "Play Count"]).groupby("Artist").sum().sort_values(by = ["Play Count"], ascending = False).head(n))

def topArtistsByPlayTime(n, dataframe):
    print("Your top " + str(n) + " artists by Play time")
    totalMilliSeconds = dataframe["Play Count"] * dataframe["Total Time"]
    totalMinutes = totalMilliSeconds.apply(lambda milliseconds : milliseconds / (1000 * 60))
    totalHours = totalMinutes.apply(lambda minutes : minutes / 60)
    totalDays = totalHours.apply(lambda hours : hours / 24)
    dataframe["Play Time (Milliseconds)"] = totalMilliSeconds
    dataframe["Play Time (Minutes)"] = totalMinutes
    dataframe["Play Time (Hours)"] = totalHours
    dataframe["Play Time (Days)"] = totalDays
    print(dataframe.filter(items = ["Artist", "Play Time (Milliseconds)", "Play Time (Minutes)", "Play Time (Hours)", "Play Time (Days)"]).groupby("Artist").sum().sort_values(by = ["Play Time (Minutes)"], ascending = False).head(n))

def totalTimeListened(dataframe):
    totalMilliseconds = dataframe.filter(items = ["Total Time"]).sum().iat[0]
    totalSeconds = totalMilliseconds / 1000
    totalMinutes = totalSeconds / 60
    totalHours = totalMinutes / 60
    totalDays = totalHours / 24
    print("Minutes Listened: " + str(totalMinutes) + ", Hours Listened: " + str(totalHours) + ", Days Listened: " + str(totalDays))
    
def main():
    n = int(input("Enter the number of elements: "))
    pd.set_option("display.max_rows", None)
    tracklist = obtainTracklist("wrapped/122021.xml")
    dataframe = pd.DataFrame(tracklist)
    topSongs(n, dataframe)
    print()
    topArtistsByPlayCount(n, dataframe)
    print()
    topArtistsByPlayTime(n, dataframe)
    print()
    totalTimeListened(dataframe)

main()

    

