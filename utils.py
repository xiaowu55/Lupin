from datetime import datetime
import re
import json
import requests
import hashlib
from os.path import basename
from bs4 import BeautifulSoup
import urllib.parse


from config import (
    hour24,
    journalsFilesFormat,
    journalsFilesExtension,
    journalsFolder,
    isEntryTimestamped,
    journalsPrefix,
    getFirebaseBucketName,
    getlastNewsDisplayed,
    setlastNewsDisplayed,
    getcalendarFile,
    getCommandsMap,
    getMonths2Generate,
)

import flashcards
from mindmap import buildMindmapTree
from calc import buildCalendar


bootTime = datetime.now()


def getJournalPath():
    dateTimeObj = datetime.now()

    if journalsPrefix == "none":
        return (
            journalsFolder
            + "/"
            + dateTimeObj.strftime(journalsFilesFormat)
            + journalsFilesExtension
        )
    else:
        return (
            journalsFolder
            + "/"
            + journalsPrefix
            + dateTimeObj.strftime(journalsFilesFormat)
            + journalsFilesExtension
        )


def getAnnotationPath(uri):
    return "annotations/" + getURIHash(uri) + journalsFilesExtension


def getCurrentTime():
    if not (isEntryTimestamped()):
        return ""
    else:
        dateTimeObj = datetime.now()

        if hour24 == "true":
            return dateTimeObj.strftime("%H:%M")
        else:
            return dateTimeObj.strftime("%I:%M %p")


def getTimestamp(isoFormat=False, withSeconds=False):
    dateTimeObj = datetime.now()

    if isoFormat:
        if withSeconds:
            return dateTimeObj.strftime("%Y%m%d%H%M%S%f")
        else:
            return dateTimeObj.strftime("%Y%m%d%H%M")
    elif hour24 == "true":
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
    url = re.search(
        "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        s,
    )
    if url:
        return url.group()
    else:
        return False


def containsRefBlock(s):
    try:
        return (re.search(r"\(\((.*?)\)\)", s)).group(1)
    except:
        return False


def getWebPageTitle(url):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code == 200:
        html_text = r.text
        soup = BeautifulSoup(html_text, "html.parser")
        if soup.title:
            return soup.title.text.strip()
        else:
            return r.url.strip()
    raise Exception(r.status_code)


def containsYTURL(s):
    url = re.search(
        "((?:https?:)?//)?((?:www|m).)?((?:youtube.com|youtu.be))(/(?:[\\w-]+\\?v=|embed/|v/)?)([\\w-]+)(\\S+)?",
        s,
    )
    if url:
        return url.group()
    else:
        return False


def getMD5Hash(s):
    byte_s = s.encode("utf-8")
    return hashlib.md5(byte_s).hexdigest()


def stripURI(uri):
    regex = re.compile(r"https?://?")
    return regex.sub("", uri).strip().strip("/")


def getURIHash(uri):
    return getMD5Hash(stripURI(uri))


def getPageTitle(path):
    return basename(path).replace(journalsFilesExtension, "")


def UploadToFirebase(data, path):
    APIRUI = (
        "https://firebasestorage.googleapis.com/v0/b/"
        + getFirebaseBucketName()
        + "/o/"
        + path.replace("/", "%2F")
    )

    headers = {"Content-Type": "img/jpg"}

    result = requests.post(APIRUI, headers=headers, data=data)
    return APIRUI + "?alt=media&token=" + result.json()["downloadTokens"]


def getlatestNews():
    url = "https://github.com/akhater/Lupin/raw/master/news.json"

    newslist = (requests.get(url)).json()
    lastNewsDisplayed = getlastNewsDisplayed()
    recentNews = []
    lstNewsID = 0
    for news in newslist["news"]:
        # print(news)
        if news["newsid"] > int(lastNewsDisplayed):
            recentNews.append(news["news"])
        lstNewsID = news["newsid"]
    print(lstNewsID)
    setlastNewsDisplayed(lstNewsID)
    return recentNews


def saveasJson(content, file):
    with open(file, "w") as outfile:
        json.dump(content, outfile)


def findOrigBlock(ref):
    with open("GitDump.json") as json_file:
        AllFilesContent = json.load(json_file)

    origBlock = ""
    for fileContent in AllFilesContent:
        if (
            ":id: " + ref in fileContent.lower() or ":id:" + ref in fileContent.lower()
        ):  # add no space after id:
            lines = fileContent.split("\n")
            i = 0
            while i <= len(lines) - 1:
                if (
                    ":id: " + ref in lines[i].lower()
                    or ":id:" + ref in lines[i].lower()
                ):
                    break
                i += 1
            origLine = lines[i - 2]
            origBlock = origLine[origLine.index(" ") :].strip()
            break
    return origBlock


def scanJson4Flashcards():
    # from git import Git2Json
    # Git2Json()
    with open("GitDump.json") as json_file:
        AllFilesContent = json.load(json_file)

    flashcardsList = []

    for fileContent in AllFilesContent:
        flashcardsList += flashcards.scan4Flashcards(fileContent)

    return flashcardsList


def updateFlashCards():
    return flashcards.saveFlashcardsDB(scanJson4Flashcards())


def convert2MD(pageTitle):
    # from git import Git2Json
    # Git2Json()

    with open("GitDump.json") as json_file:
        AllFilesContent = json.load(json_file)

    for content in AllFilesContent:
        lines = content.split("\n")
        lvl1 = -1

        i = 0
        out = ""
        continueScan = True
        while i <= len(lines) - 1:
            line = lines[i]
            if line:
                # print(line[0])
                if (
                    "title:" in line.lower() and pageTitle.lower() not in line.lower()
                ):  # not correct page
                    continueScan = False
                if not continueScan:
                    break
                if "title:" in line.lower() and pageTitle.lower() in line.lower():
                    out += "# " + line.replace("title:", "").strip() + "\n"
                elif line[0] == "#":
                    outln = ""
                    blockRef = containsRefBlock(line)
                    if blockRef:
                        origLine = (
                            (line[line.index(" ") :])
                            .replace("((" + blockRef + "))", "")
                            .strip()
                        )
                        if origLine:
                            outln = origLine + " "
                        outln += findOrigBlock(blockRef)
                    else:
                        outln = line[line.index(" ") :]

                    if lvl1 == -1:
                        lvl1 = line.index(" ")
                    space = " "
                    for _ in range((line.index(" ") - lvl1) * 4):
                        space += " "
                    out += (
                        space + "- " + outln.strip() + "\n"
                    )  # + (line[line.index(' '):]) + '\n' # .replace('#','-') + "\n"
                    # print(out)
            i += 1
    return out


def convert2Mindmap(pageTitle):
    # from git import Git2Json
    # Git2Json()

    with open("GitDump.json") as json_file:
        AllFilesContent = json.load(json_file)

    for content in AllFilesContent:
        if ("---\ntitle: " + pageTitle.lower()) in content.lower():
            return json.dumps(
                buildMindmapTree(content, pageTitle), default=lambda x: x.__dict__
            )
            # return json.dumps(buildMindmapTree(content, pageTitle).c[0], default=lambda x: x.__dict__)


def pageExists(pageTitle):
    # from git import Git2Json
    # Git2Json()

    with open("GitDump.json") as json_file:
        AllFilesContent = json.load(json_file)

    for content in AllFilesContent:
        if ("---\ntitle: " + pageTitle.lower()) in content.lower():
            return True

    return False


def getdateFormatter():
    with open("GitDump.json") as json_file:
        AllFilesContent = json.load(json_file)

    for content in AllFilesContent:
        dateFormatter = re.findall("\n :date-formatter.*", content)  # ,re.MULTILINE)
        if dateFormatter:
            break

    if not (dateFormatter):
        dateFormatter = "%b {th}, %Y"
    else:
        mapping = {
            "yyyy": "%Y",
            "yy": "%y",
            "MM": "%m",
            "MMM": "%b",
            "MMMM": "%B",
            "dd": "%d",
            "do": "{th}",
            "EE": "%a",
            "EEE": "%a",
            "EEEEEE": "%A",
        }

        def replace(match):
            return mapping[match.group(0)]

        dateFormatter = dateFormatter[0].split(":date-formatter")[1]
        dateFormatter = dateFormatter[1:].replace('"', " ").rstrip()

        dateFormatter = re.sub(
            "|".join(r"\b%s\b" % re.escape(s) for s in mapping), replace, dateFormatter
        )

    print(dateFormatter.strip())
    return dateFormatter.strip()


def generateCalendarsFile(contents):
    import datetime as dt

    today = dt.date.today()

    months2Generate = getMonths2Generate()

    out = "##\n"
    if int(months2Generate[0]) == 1:
        lastMonth = today.replace(day=1) - dt.timedelta(days=1)
        out += buildCalendar(lastMonth.year, lastMonth.month) + "\n##\n"

    out += buildCalendar(today.year, today.month) + "\n"

    if int(months2Generate[1]) == 1:
        nextMonth = today.replace(day=28) + dt.timedelta(days=4)
        out += "##\n" + buildCalendar(nextMonth.year, nextMonth.month) + "\n"

    # out = "##\n" + buildCalendar(lastMonth.year, lastMonth.month) + "\n##\n" + buildCalendar(today.year, today.month) + "\n##\n"  + buildCalendar(nextMonth.year, nextMonth.month) + "\n"

    t = (
        re.sub(
            "(##[\\s\n]<!--LupinCalendarBegins-->).*?(<!--LupinCalendarEnds-->)",
            "",
            contents,
            flags=re.DOTALL,
        )
    ).strip()

    out += t

    return out


def processCommandsMapping(entry):
    # import re
    CommandsMap = getCommandsMap()

    def replace(match):
        return CommandsMap[match.group(0)]

    s = re.sub("|".join(r"\b%s\b" % re.escape(s) for s in CommandsMap), replace, entry)

    rValue = ""
    for _, value in CommandsMap.items():
        if value in s:
            rValue = s.split(value)
            rValue = value + " " + (" ".join([x.strip() for x in rValue])).strip()
    if rValue:
        return rValue
    else:
        return entry


def ord(n):
    return str(n) + (
        "th" if 4 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    )


def styleDateTime(dt, f):
    return dt.strftime(f).replace("{th}", ord(dt.day))


def getJournalTitle():
    return styleDateTime(datetime.now(), getdateFormatter())


def getJournalTemplate():
    with open("GitDump.json") as json_file:
        AllFilesContent = json.load(json_file)

    for content in AllFilesContent:
        JournalTemplate = re.findall(
            "\n :default-templates\n {:journals.*", content
        )  # ,re.MULTILINE)
        if JournalTemplate:
            break

    if JournalTemplate:
        return (
            JournalTemplate[0]
            .split('\n :default-templates\n {:journals "')[1][
                : len(JournalTemplate) - 3
            ]
            .replace("\\n", "\n")
        )
    else:
        return None


def generateTwitterIframe(TwitterUrl):
    endpoint = "https://publish.twitter.com/oembed?url="

    TargetUrl = endpoint + TwitterUrl

    r = requests.get(TargetUrl, headers={"User-Agent": "Mozilla/5.0"})

    if r.status_code == 200:
        jsonObj = json.loads(r.text)
        srcCode = urllib.parse.quote(jsonObj["html"])

        iframeCode = (
            """<iframe style="border:none;" width="550" height="400" data-tweet-url="{}" src="data:text/html;charset=utf-8,{}"></iframe>"""
        ).format(TwitterUrl, srcCode)

        return iframeCode


def containsTWUrl(s):
    # url = re.search('((?:https?:)?//)?((?:www|m).)?((?:youtube.com|youtu.be))(/(?:[\\w-]+\\?v=|embed/|v/)?)([\\w-]+)(\\S+)?',s)
    # url = re.search('(?:http://)?(?:www.)?twitter.com/(?:(?:\\w)*#!/)?(?:pages/)?(?:[\\w-]*/)*([\\w-]*)',s)
    url = re.search(
        "((?:https?:)?//)?(?:www.)?twitter.com/(?:(?:\\w)*#!/)?(?:pages/)?(?:[\\w-]*/)*([\\w-]*)",
        s,
    )
    if url:
        return url.group()
    else:
        return False
