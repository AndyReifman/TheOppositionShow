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

def getTimestamp():
        dt = str(datetime.datetime.now().month) + '/' + str(datetime.datetime.now().day) + ' '
        hr = str(datetime.datetime.now().hour) if len(str(datetime.datetime.now().hour)) > 1 else '0' + str(datetime.datetime.now().hour)
        min = str(datetime.datetime.now().minute) if len(str(datetime.datetime.now().minute)) > 1 else '0' + str(datetime.datetime.now().minute)
        t = '[' + hr + ':' + min + '] '
        return dt + t

def loginBot():
    try:
        f = open('/root/reddit/towjk/login.txt')
        admin,username,password,subreddit,user_agent,id,secret,redirect = f.readline().split('||',8)
        f.close()
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


def parseGuest(guest,guestHtml):
    website = "https://en.wikipedia.org"+guestHtml
    guestWebsite = requests.get(website, timeout=15)
    guest_html = guestWebsite.text
    soup = BeautifulSoup(guest_html, 'lxml')
    print soup.prettify()
    content = soup.find("div",{"id":"mw-content-text"})
    summary = content.findAll("p")
    text = ""
    for x in range(0,2):
        text += ">"+summary[x].getText()
        text += "\n\n"
    text = re.sub(r'(\[[0-9]?[0-9]?\])','',text)
    header = "["+guest.getText()+"]("+website+")\n\n"
    header += text
    print header
    return text

def parseDescription(description):
    soup = BeautifulSoup(description, 'lxml')
    return soup.get_text()
    
def parseEpisode(index,episode):
    body = ""
    description = "#Description\n\n"
    body += "\n\n"+description+"\n\n"
    body += "#Tonight's Guest\n\n"
    return body
    

def getEpisode():
    today = str(datetime.datetime.now().year)+'-'
    today += str(datetime.datetime.now().month)+'-' if len(str(datetime.datetime.now().month)) > 1 else '0' +  str(datetime.datetime.now().month)+'-'
    today += str(datetime.datetime.now().day) if len(str(datetime.datetime.now().day)) > 1 else '0' +  str(datetime.datetime.now().day)
    month = calendar.month_name[datetime.datetime.now().month]
    website = "https://en.wikipedia.org/wiki/List_of_The_Opposition_with_Jordan_Klepper_episodes#"+month
    tableWebsite = requests.get(website, timeout=15)
    table_html = tableWebsite.text
    soup = BeautifulSoup(table_html, 'lxml')
    month+= ' '+str(datetime.datetime.now().day)+','
    table = soup.findAll("table",{"class": "wikitable plainrowheaders wikiepisodetable"})[-1]
    episodes = table.findAll("tr",{"class":"vevent"})
    for index,episode in enumerate(episodes):
        episodeDate = episode.find("td", {"class":"summary"}).getText()
        episodeDate = re.findall('\((.*)\)',episodeDate)[0]
        if today in episodeDate:
            body = parseEpisode(index,episode)
            guest = episode.findAll("td")[1]
            try:
                guestLink = guest.find('a')
                guestLink = guestLink['href']
                print guestLink
            except:
                pass
            if guestLink:
                guestText = parseGuest(guest,guestLink )
                body += guestText
            else:
                body += guest.getText()+"\n\n"
        

    titleDate = datetime.datetime.now().month 
    titleDate = calendar.month_name[titleDate]+ " "
    titleDate += str(datetime.datetime.now().day)+", " if len(str(datetime.datetime.now().day)) > 1 else '0' +  str(datetime.datetime.now().day)+", "
    titleDate += str(datetime.datetime.now().year)
    title = titleDate + " | The Opposition with Jordan Klepper | "+guest.getText()
    return title,body

def postThread():
    title,body = getEpisode()
    r,admin,username,password,subreddit,user_agent,id,secret,redirect = loginBot()
    print getTimestamp() + "Submitting Thread"
    submission = r.subreddit(subreddit).submit(title,selftext=body,send_replies=False)
    submission.mod.sticky(state=True)
    shortlink = submission.shortlink
    print getTimestamp() + "Thread Submitted"
    return submission

def updateThread(link):
    title,body = getEpisode()
    r,admin,username,password,subreddit,user_agent,id,secret,redirect = loginBot()
    print getTimestamp() + "Updating thread"
    link.edit(body)

shortlink = postThread()
#sleep until Midnight? Then update submission.
#t = datetime.datetime.today()
#future = datetime.datetime(t.year,t.month,t.day,4,0)
#if t.hour >= 4:
#    future += datetime.timedelta(days=1)
#time.sleep((future-t).seconds)
#updateThread(shortlink)
