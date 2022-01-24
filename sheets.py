from tkinter.tix import INTEGER
import httplib2
from apiclient import discovery
import pytz
from pytz import timezone
import datetime
tz = pytz.utc

def getSchedule():
    api_key = 'AIzaSyBeh_CnQNh8-_041kUcKUbPBTgBSgMcYVs' # hide as secret
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
    service = discovery.build(
        'sheets',
        'v4',
        http=httplib2.Http(),
        discoveryServiceUrl=discoveryUrl,
        developerKey=api_key)

    spreadsheetId = '1tiYLMKpJFCfbTie_yqzmJYoE9IWWd4545BW9Wviyt_U' # hide as secret
    rangeName = 'Schedule!A3:F50'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    date_chores = {}
    for row in values:
        dateStr = row[0].split(", ")[1]
        date_chores[dateStr] = row[1:len(row)]

    return date_chores

def getWeekChores(queryDate):
    # convert date to nearest-previous monday
    queryDay = int(datetime.datetime.strftime(queryDate, '%w')) # 0 = sun, 1 = mon etc
    offsetDays = 6 if queryDay == 0 else queryDay - 1
    mondayDate = queryDate - datetime.timedelta(offsetDays)
    keyStr = mondayDate.strftime('%d %B %Y')
    schedule = getSchedule()
    if keyStr in schedule:
        return schedule[keyStr]
    else:
        return None

