#!/usr/bin/python2.7

import re,logging,logging.handlers,datetime,requests,requests.auth,sys,json,unicodedata
import time
import praw
import calendar
from praw.models import Message
from collections import Counter
from itertools import groupby
from time import sleep
from bs4 import BeautifulSoup
import pyotp

def getTimestamp():
        dt = str(datetime.datetime.now().month) + '/' + str(datetime.datetime.now().day) + ' '
        hr = str(datetime.datetime.now().hour) if len(str(datetime.datetime.now().hour)) > 1 else '0' + str(datetime.datetime.now().hour)
        min = str(datetime.datetime.now().minute) if len(str(datetime.datetime.now().minute)) > 1 else '0' + str(datetime.datetime.now().minute)
        t = '[' + hr + ':' + min + '] '
        return dt + t

def loginBot():
    try:
        f = open('/root/reddit/towjk/login.txt')
        fkey = open('/root/reddit/sidebar/2fakey.txt')
        admin,username,password,subreddit,user_agent,id,secret,redirect = f.readline().split('||',8)
        key = fkey.readline().rstrip()
        password += ':'+pyotp.TOTP(key).now()
        f.close()
        fkey.close()
        r = praw.Reddit(client_id=id,
             client_secret=secret,
             password=password,
             user_agent=user_agent,
             username=username)
        print getTimestamp() + "OAuth session opened as /u/" + r.user.me().name
        return r,admin,username,password,subreddit,user_agent,id,secret,redirect
    except Exception, e:
        print getTimestamp() + str(e)
        if e == 'invalid_grant error processing request':
            print getTimestamp() + 'Attempting to log in again.\n'
            sleep(5)
            loginBot()
            return
        print getTimestamp() + "Setup error \n"
        sleep(10)


def parseGuest(guest):
    website = "https://en.wikipedia.org"+guest
    guestWebsite = requests.get(website, timeout=15)
    guest_html = guestWebsite.text
    #guestInfo = guest_html.split('</table>')[1]
    guestInfo = guest_html.split('<div id=\"mw-content-text\"')[1]
    #paragraph = re.findall('<p>(.*?)</p>',guestInfo)[0]
    paragraph = re.findall('<p>(.*?)</p>',guestInfo)
    text = ""
    for p in paragraph[0:2]:
        soup = BeautifulSoup(p, "lxml")
        html = soup.get_text()
        text += re.sub(r'(\[[0-9]?[0-9]?\])','',html)
        text += '\n\n>'
    #soup = BeautifulSoup(paragraph, "lxml")
    #soup = soup.replace("(\[[0-9]?[0-9]?\])","")
    return text

def parseDescription(description):
    soup = BeautifulSoup(description, 'lxml')
    return soup.get_text()
    
def parseEpisode(episode):
    body = ""
    description = "#Description\n\n"
    try:
        desc = ">"+re.findall('<td class=\"description\".*?>(.*)<\/td>',episode)[0]
        description += parseDescription(desc)
        
    except:
        print getTimestamp() + "No description yet."
        description += "No description available yet."
    body += "\n\n"+description
    guest = "#Tonight's Guest\n\n"
    guestName = re.findall('<td><a href=.*?>(.*?)<\/a>',episode)[0]
    tempGuest = re.findall('<td><a href=\"(.*)\" title',episode)[0]
    guestInfo = parseGuest(tempGuest)
    guestLink = "https://en.wikipedia.org"+tempGuest
    guest += "["+guestName+"]("+guestLink+")"
    body += "\n\n"+guest
    body += "\n\n>"+guestInfo
    return guestName,body
    

def getEpisode():
    #today = time.strftime("%Y-%m-%d")
    today = str(datetime.datetime.now().year)+'-'
    today += str(datetime.datetime.now().month)+'-' if len(str(datetime.datetime.now().month)) > 1 else '0' +  str(datetime.datetime.now().month)+'-'
    today += str(datetime.datetime.now().day - 1) if len(str(datetime.datetime.now().day)) > 1 else '0' +  str(datetime.datetime.now().day - 1)
    website = "https://en.wikipedia.org/wiki/List_of_The_Opposition_with_Jordan_Klepper_episodes"
    tableWebsite = requests.get(website, timeout=15)
    table_html = tableWebsite.text
    table = table_html.split('<table ')[1]
    episodes = table.split('<tr class')[1:]
    for episode in episodes:
        episodeDate = re.findall('\(<span.*?>(.*)<\/span>\)',episode)[0]
        if today == episodeDate:
            guest, body = parseEpisode(episode)
    titleDate = datetime.datetime.now().month 
    titleDate = calendar.month_name[titleDate]+ " "
    titleDate += str(datetime.datetime.now().day - 1)+", " if len(str(datetime.datetime.now().day)) > 1 else '0' +  str(datetime.datetime.now().day - 1)+", "
    titleDate += str(datetime.datetime.now().year)
    title = titleDate + " | The Opposition with Jordan Klepper | "+guest 
    return title,body

def postThread():
    title,body = getEpisode()
    r,admin,username,password,subreddit,user_agent,id,secret,redirect = loginBot()
    print getTimestamp() + "Submitting Thread"
    submission = r.subreddit(subreddit).submit(title,selftext=body,send_replies=False)
    submission.mod.sticky(state=True)
    shortlink = submission.shortlink
    print shortlink
    print getTimestamp() + "Thread Submitted"
    return submission

def updateThread(link):
    title,body = getEpisode()
    r,admin,username,password,subreddit,user_agent,id,secret,redirect = loginBot()
    print getTimestamp() + "Updating thread"
    #thread = r.submission(link)
    link.edit(body)

shortlink = postThread()
#sleep until Midnight? Then update submission.
#t = datetime.datetime.today()
#future = datetime.datetime(t.year,t.month,t.day,4,0)
#if t.hour >= 4:
#    future += datetime.timedelta(days=1)
#time.sleep((future-t).seconds)
#updateThread(shortlink)
