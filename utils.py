from datetime import datetime
import re
from config import hour24, journalsFilesFormat, journalsFilesExtension, journalsFolder, journalsPrefix
import requests
import hashlib
from os.path import basename

bootTime = datetime.now()

def getJournalPath():
  dateTimeObj = datetime.now()

  if (journalsPrefix == "none"):
    return journalsFolder + "/" + dateTimeObj.strftime(journalsFilesFormat) + journalsFilesExtension
  else:
    return journalsFolder + "/" + journalsPrefix + dateTimeObj.strftime(journalsFilesFormat) + journalsFilesExtension

def getAnnotationPath(uri):
  return 'annotations/' + getURIHash(uri) + journalsFilesExtension

def getCurrentTime():
  dateTimeObj = datetime.now()

  if(hour24 == "true"):
    return dateTimeObj.strftime("%H:%M") 
  else:
    return dateTimeObj.strftime("%I:%M %p")

def getTimestamp():
  dateTimeObj = datetime.now()
  
  if(hour24 == "true"):
    return dateTimeObj.strftime("%Y-%m-%d %H:%M") 
  else:
    return dateTimeObj.strftime("%Y-%m-%d %I:%M %p")

def getUptime():
  seconds = date_diff_in_seconds(datetime.now(), bootTime)

  minutes, seconds = divmod(seconds, 60)
  hours, minutes = divmod(minutes, 60)
  days, hours = divmod(hours, 24)
  return (days, hours, minutes, seconds)

def date_diff_in_seconds(dt2, dt1):
    timedelta = dt2 - dt1
    return timedelta.days * 24 * 3600 + timedelta.seconds

def containsURL(s):
    #return search("(?P<url>https?://[^\\s]+)", s).group("url")
    url = re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', s)
    if url:
      return url.group()
    else:
      return False
    
# def getWebPageTitle(url, title_re=re.compile(r'<title>(.*?)</title>', re.UNICODE )):    
def getWebPageTitle(url, title_re=re.compile(r'title[^>]*>([^<]+)<\/title>', re.UNICODE )): 
    r = requests.get(url)
    if r.status_code == 200:
        match = title_re.search(r.text)
        if match:
            return match.group(1)
        return Exception("No match for title in page")
    raise Exception(r.status_code)

def containsYTURL(s):
  url = re.search('((?:https?:)?//)?((?:www|m).)?((?:youtube.com|youtu.be))(/(?:[\\w-]+\\?v=|embed/|v/)?)([\\w-]+)(\\S+)?',s)
  if url:
    return url.group()
  else:
    return False

def getMD5Hash(s):
  byte_s = s.encode('utf-8')
  return hashlib.md5(byte_s).hexdigest()

def stripURI(uri):
  regex = re.compile(r"https?://?")
  return regex.sub('', uri).strip().strip('/')

def getURIHash(uri):
  return getMD5Hash(stripURI(uri))

def getPageTitle(path):
  return basename(path).replace(journalsFilesExtension, '')

#uri = ("https://web.hypothes.is")
# print(getURIHash(uri))
#print(getAnnotationPath(uri))
#print(getPageTitle("annotations/adac032c3d5d75eda161dd3d0aab31ee.md"))
