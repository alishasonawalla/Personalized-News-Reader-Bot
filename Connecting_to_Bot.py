
# # Connecting to Bot
#
# ** Part 2: Designating regex expressions for each match**
#
# NewsBerry has **five** questions intended to return data retrieved from the database and **one** question that returns a quick user manual.

# In[1]:



import time, datetime
import arrow
import re
import requests
import json
import MySQLdb as mdb
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from slackclient import SlackClient
from sqlalchemy import create_engine
get_ipython().magic(u'matplotlib inline')


# In[2]:


def message_is_for_our_bot(user_id, message_text):

    regex_expression = '.*@' + user_id + '.*bot.*'
    regex = re.compile(regex_expression)

    #Checking that the message text matches the regex above
    match = regex.match(message_text)

    #Returns true if the match is not None (i.e. the regex had a match)
    return match != None


# In[3]:


#The extract_info function checks if the message_text matches with any of the 6 regex expressions defined
#in the function below

def extract_info(message_text):

    pattern = 'headlines and descriptions from (.+)'
    regex = re.compile(pattern)
    matches = regex.finditer(message_text)
    for match in matches:
        return {
            'match_type'    : 1,
            'regex_matched' : pattern,
            'extracted_info': [match.group(1)]
        }

    pattern = 'headlines for today'
    regex = re.compile(pattern)
    matches = regex.finditer(message_text)
    for match in matches:
        return {
            'match_type'    : 2,
            'regex_matched' : pattern,
        }

    pattern = 'according to (.+)'
    regex = re.compile(pattern)
    matches = regex.finditer(message_text)
    for match in matches:
        return {
            'match_type'    : 3,
            'regex_matched' : pattern,
            'extracted_info': [match.group(1)]
        }

    pattern = 'people in the news'
    regex = re.compile(pattern)
    matches = regex.finditer(message_text)
    for match in matches:
        return {
            'match_type'    : 4,
            'regex_matched' : pattern,
        }

    pattern = 'about (.+)'
    regex = re.compile(pattern)
    matches = regex.finditer(message_text)
    for match in matches:
        return {
            'match_type'    : 5,
            'regex_matched' : pattern,
            'extracted_info': [match.group(1)]
        }


    pattern = 'Introduce yourself'
    regex = re.compile(pattern)
    matches = regex.finditer(message_text)
    for match in matches:
        return {
            'match_type'    : 11,
            'regex_matched' : pattern,
        }

    #If no matches, return None --> bot will display error message to guide the user to correct prompts
    return None

'''
print(extract_info("hello"))
print(extract_info("top headlines and descriptions from ABC News"))
print(extract_info("Give me all the articles from ABC between 12-01-2017 and 12-07-2017"))
print(extract_info("Give me the URLs for Donald Trump"))
'''


# In[4]:


#The get_news_data function retrieves the information from our news aggregator database

def get_news_data(source):

    con = mdb.connect(host = 'localhost',
                  user = 'root',
                  database = 'news_agg',
                  passwd = 'dwdstudent2015',
                  charset='utf8', use_unicode=True)

    query_template = '''SELECT title,
                            description,
                            author,
                            url,
                            publishedAt
                        FROM News_aggregator5
                        WHERE source = %s'''

    cur = con.cursor(mdb.cursors.DictCursor)
    cur.execute(query_template, (source,) )
    data = cur.fetchall()
    cur.close()
    con.close()

    return data


# ** Part 2: Writing messages for each function**
#
# We tried to replicate the most natural response for each function. There are two types of answers:
#
# * Text for messages 1 2 3 and 6
# * Plot for messages 4 and 5
#
# We chose the sentiment and the most-talked about entities to be displayed in plots for efficient delivery.
#
# The answers are limited to between 10 to 25 news articles to prevent NewsBerry from generating too many lines.

# In[5]:


#The first create_message function returns information to the user regarding the top 10 article headlines,
#URLs and descriptions
#The user must type a message to the bot that includes the following text: 'headlines and descriptions from [SOURCE]'

def create_message(source):

    attachments = []

    if 'regex_matched' in source:

        message = "Thank you for asking about the news from " + source['extracted_info'][0] + "!\n\n"


        get_data = source['extracted_info'][0]

        con = mdb.connect(host = 'localhost',
                  user = 'root',
                  database = 'news_agg',
                  passwd = 'dwdstudent2015',
                  charset='utf8', use_unicode=True)

        query_template = '''SELECT title,
                                description,
                                author,
                                url,
                                publishedAt
                            FROM News_aggregator5
                            WHERE source = %s
                            LIMIT 10'''

        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute(query_template, (get_data,) )
        data = cur.fetchall()
        cur.close()
        con.close()

        matching_news = data

        # If we cannot find any matching news...
        if len(matching_news) == 0:
            message += "Seems like their entire office is on vacation today. There's nothing!\n"
        # If there are multiple matching news
        if len(matching_news) > 1:
            message += "Here are the most recent articles from " + source['extracted_info'][0] + ".\n\n"

        count = 1

        for n in matching_news:
            date = n['publishedAt']
            url = n['url']
            description = n['description']
            title = n['title']

            message += "{a}) Headline: {b}.\n".format(a=count, b=title)
            message += "Description: {a}.\n".format(a=description)
            message += "Article URL: {a}.\n\n".format(a=url)


            count += 1

    else:
        message = "Unfortunately, I could not understand your command. :/\n"
        message += "Ask me `Show me the top headlines and descriptions from [SOURCE].` and I will try to answer."

    return message, None


# In[6]:


#The second create_message function returns information to the user regarding the top 20 headlines throughout
#all of the news sources in the database for TODAY
#The user must type a message to the bot that includes the following text: 'headlines for today'

def create_message2(source):

    attachments = []

    if 'regex_matched' in source:

        message = "Thank you for asking about today's top news!\n"


        con = mdb.connect(host = 'localhost',
                  user = 'root',
                  database = 'news_agg',
                  passwd = 'dwdstudent2015',
                  charset='utf8', use_unicode=True)

        date = datetime.datetime.today().strftime("%Y-%m-%d")

        query_template = '''SELECT title,
                                description,
                                author,
                                url,
                                publishedAt
                            FROM News_aggregator5
                            WHERE publishedAt = %s
                            LIMIT 20
                            '''

        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute(query_template, (date,))
        data = cur.fetchall()
        cur.close()
        con.close()

        matching_news = data

        # If we cannot find any matching news...
        if len(matching_news) == 0:
            message += "Sorry! There's nothing! We might be in different time zones. (Mine's UTC)\n"
        # If there are multiple matching news
        if len(matching_news) > 1:
            message += "Here are the top 20 headlines for today.\n"

        count = 1

        for n in matching_news:
            date = n['publishedAt']
            url = n['url']
            description = n['description']
            title = n['title']

            message += "{a}) Headline: {b}, {c}.\n".format(a=count, b=title, c=date)
            message += "URL: {b}.\n".format(a=count, b=url)

            count += 1


    else:
        message = "Unfortunately I could not understand your command.\n"
        message += "Ask me `Show me the top headlines for today` and I will try to answer."

    return message, None


# In[7]:


#The following plot_sentiment function creates the plot for our third message (create_message3)

def plot_sentiment(source, positive, negative, other):

    matplotlib.style.use(['seaborn-talk', 'seaborn-ticks'])
    df = pd.DataFrame([{"Positive": positive, "Negative": negative, "No Feelings": other}])
    ax = df.plot(kind='bar')
    plt.xlabel('Sentiment', size = 15)
    plt.ylabel('Degree of Sentiment', size = 15)
    plt.title("How's the world feeling today", size = 20)
    plt.legend(prop={'size':10})

    #Saving the plot and returning its url

    fig = ax.get_figure()
    filename = 'plots/'+ str(hash(source)) + '.png'
    fig.savefig(filename)
    plt.close(fig)

    url = 'http://34.234.165.121:5000/' + filename

    return url


# In[8]:


#The third create_message function returns information (and a plot) to the user regarding the overall sentiment
#from a specific news source
#The user must type a message to the bot that includes the following text: 'according to [SOURCE]'

def create_message3(source):

    attachments = []

    if 'regex_matched' in source:

        message = "Thank you for caring about the world! You're awesome!\n\n"

        get_data = source['extracted_info'][0]

        con = mdb.connect(host = 'localhost',
                  user = 'root',
                  database = 'news_agg',
                  passwd = 'dwdstudent2015',
                  charset='utf8', use_unicode=True)

        query_template = '''SELECT entity_sentiment
                            FROM News_aggregator5
                            WHERE source = %s'''

        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute(query_template, (get_data,) )
        data = cur.fetchall()
        cur.close()
        con.close()

        matching_news = data

        # If we cannot find any matching news...
        if len(matching_news) == 0:
            message += "It's hard to read people's feelings sometimes... There's nothing!\n"
        # If there are multiple matching news
        if len(matching_news) > 1:
            message += "Here is a plot of the 'emotions' from " + source['extracted_info'][0] + ".\n\n"

        positive = 0
        negative = 0
        other = 0

        for n in matching_news:

            emotion = n['entity_sentiment']

            if emotion == "positive":
                positive += 1
            elif emotion == "negative":
                negative += 1
            elif emotion == "null":
                other += 1
            else:
                other += 1

        message += "Positive: " + str(positive) + "\n"
        message += "Negative: " + str(negative) + "\n"
        message += "No Feelings: " + str(other) + "\n"

        url = plot_sentiment(source['extracted_info'][0],positive, negative, other)

        attachment = {
            "image_url": url,
            "title": "Emotions of {a}".format(a = source['extracted_info'][0])
        }
        attachments.append(attachment)

    else:
        message = "Unfortunately I could not understand your command.\n"
        message += "Ask me `How’s the world doing according to [SOURCE]?` and I will try to answer."

    return message, attachments


# In[9]:


#The fourth create_message function returns information (and a plot) to the user regarding the top 10 most
#featured entities in the database
#The user must type a message to the bot that includes the following text: 'people in the news'

def create_message4(source):

    attachments = []

    message = "Thank you for asking about the people in the news!\n\n"


    con = 'mysql://{user}:{password}@{host}:{port}/{db}'.format(
           user='root',
           password='dwdstudent2015',
           host = 'localhost',
           port=3306,
           db='news_agg'
    )

    engine_people = create_engine(con)

    people = 'Person'

    query_template = '''Select entity_type, entities, COUNT(entity_type) AS count
                            FROM News_aggregator5
                            WHERE entity_type = %s
                            GROUP BY entities
                            ORDER BY count DESC
                            LIMIT 10;'''

    df_people = pd.read_sql(query_template, con = engine_people, params = (people,))

    matplotlib.style.use(['seaborn-notebook'])
    df_people = df_people.set_index('entities')
    ax = df_people.plot(kind = 'barh')

    plt.rcParams['figure.figsize'] = (150, 65)
    plt.title("Who's in the News")
    plt.rcParams['figure.titlesize'] = 10
    plt.xlabel('Number of Appearances')
    plt.ylabel('People')
    plt.rcParams['ytick.labelsize'] = 2
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['xtick.labelsize'] = 5
    plt.rcParams['axes.labelsize'] = 2
    plt.rcParams['axes.ymargin'] = 0.1
    plt.rcParams['legend.fontsize'] = 5
    plt.rcParams['font.size'] = 5
    plt.tight_layout()
    #matplotlib.rcParams.update({'font.size': 10})




    #plt.legend(prop={'size':15})

    # Save the plot and return its url
    fig = ax.get_figure()
    filename = 'plots/'+ str(hash('OURBOTISocoool')) + '1.png'
    fig.savefig(filename)
    plt.close(fig)

    url = 'http://34.234.165.121:5000/' + filename

    attachment = {
        "image_url": url,
        "title": "Top People in the News"
    }
    attachments.append(attachment)

    message += "Let's find out who's in trouble!"

    return message, attachments


# In[10]:


create_message4('people in the news')


# In[11]:


#The fifth create_message function returns information to the user regarding the top 10 articles
#that feature a specific entity requested by the user
#The user must type a message to the bot that includes the following text: 'about [ENTITY]'

def create_message5(source):

    attachments = []

    if 'regex_matched' in source:


        message = "Thank you for asking about news about " + source['extracted_info'][0] + "\nLet's see what we can pull out!\n\n"

        get_data = source['extracted_info'][0]

        con = mdb.connect(host = 'localhost',
                  user = 'root',
                  database = 'news_agg',
                  passwd = 'dwdstudent2015',
                  charset='utf8', use_unicode=True)

        query_template = '''SELECT title,
                                description,
                                url,
                                publishedAt,
                                entities,
                                source
                            FROM News_aggregator5
                            WHERE entities = %s
                            LIMIT 10'''

        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute(query_template, (get_data,) )
        data = cur.fetchall()
        cur.close()
        con.close()

        matching_news = data

        # If we cannot find any matching news...
        if len(matching_news) == 0:
            message += "I guess not that many people know about your entity. There's nothing!\n" #change this message lol
        # If there are multiple matching news
        if len(matching_news) > 1:
            message += "Here we go! Let's find out about " + source['extracted_info'][0] + ".\n\n"

        count = 1

        for n in matching_news:
            url = n['url']
            description = n['description']
            title = n['title']
            source = n['source']


            message += "{a}) Headline: {b}.\n".format(a=count, b=title)
            message += "Aritcle URL: {a}.\n\n".format(a=url)

            count += 1

    else:
        message = "Unfortunately I could not understand your command.\n"
        message += "Ask me `I’m curious about [ENTITIES]` and I will try to answer."

    return message, None


# In[12]:


#'How-to' User Guide (What can this bot answer?)
#This will prompt the bot to deliver the 'How-to' guide (on using the SlackBot)

#Sources: abc-news,bloomberg,business-insider,espn,buzzfeed,fortune,nbc-news,mtv-news,the-wall-street-journal,
#the-new-york-times,techcrunch,national-geographic,fox-sports,crypto-coins-news,al-jazeera-english,
#engadget,google-news,reddit-r-all,the-economist,wired

def create_message11(source):


    message = "Hey, its nice to meet you!\n\n"
    message += "My name is NewsBerry and I collect news data from many different sources from around the web!\n\n"

    message += "I collect my information from the following sources: \n\n"
    message += "1)  ABC News               11)  Bloomberg\n"
    message += "2)  Business Insider      12)  ESPN\n"
    message += "3)  Buzzfeed                 13)  Fortune\n"
    message += "4)  NBC News              14)  MTV News\n"
    message += "5)  The NY Times         15)  The Wall Street Journal\n"
    message += "6)  TechCrunch             16)  National Geographic\n"
    message += "7)  Fox Sports               17)  Crypto Coins News\n"
    message += "8)  Engadget                 18)  Al Jazeera English\n"
    message += "9)  Google News          19)  Reddit /r/all\n"
    message += "10) The Economist       20)  Wired\n\n"

    message += "Here is the list of commands that I can answer: \n\n"
    message += "1) Introduce yourself\n"
    message += "2) Show me the top headlines and descriptions from [SOURCE]\n"
    message += "3) Show me the top headlines for today\n"
    message += "4) How’s the world doing according to [SOURCE]\n"
    message += "5) Who are the people in the news\n"
    message += "6) I’m curious about [ENTITIES]\n\n"

    message += "Well, feel free to ask me any questions and hopefully I can help :)"

    return message, None


# In[13]:


#The message_to_act_upon function decides which message (from above) to return to the user based on the
#specific message's 'match_type'

matches = extract_info("top headlines and descriptions from ABC News")

def message_to_act_upon(matches):

    print(matches)

    if matches == None:
        message = "Hey, it's nice to meet you!\n"
        message += "If you aren't sure what to ask me, write 'Introduce yourself' and I will show you what I can do!"
        return message, None

    elif matches['match_type'] == 1:
        return create_message(matches)

    elif matches['match_type'] == 2:
        return create_message2(matches)

    elif matches['match_type'] == 3:
        return create_message3(matches)

    elif matches['match_type'] == 4:
        return create_message4(matches)

    elif matches['match_type'] == 5:
        return create_message5(matches)

    else:
        return create_message11(matches)


# In[ ]:


#This is the beginning of the program.
#We readthe access token from the file and create the Slack Client
secrets_file = 'slack_secret.json'
f = open(secrets_file, 'r')
content = f.read()
f.close()

auth_info = json.loads(content)
auth_token = auth_info["access_token"]
bot_user_id = auth_info["user_id"]

#Connect to the Real Time Messaging API of Slack and process the events
sc = SlackClient(auth_token)


# In[ ]:


if sc.rtm_connect():

    while True:

        time.sleep(1)

        response = sc.rtm_read()

        for item in response:
            # Check that the event is a message. If not, ignore and proceed to the next event.
            if item.get("type") != 'message':
                continue

            # Check that the message comes from a user. If not, ignore and proceed to the next event.
            if item.get("user") == None:
                continue

            # Check that the message is asking the bot to do something. If not, ignore and proceed to the next event.
            message_text = item.get('text')
            if not message_is_for_our_bot(bot_user_id, message_text):
                continue

            # Get the username of the user who asked the question
            response = sc.api_call("users.info", user=item["user"])
            username = response['user'].get('source') #change 'source' back to 'name'

            # Extract the message_text from the user's message
            source = extract_info(message_text)

            # Prepare the message that we will send back to the user
            message, attachments = message_to_act_upon(source)

            # Post a response to the #bots channel
            if attachments == None:
                sc.api_call("chat.postMessage", channel="#newsberry_bot", text=message)
            else:
                sc.api_call("chat.postMessage", channel="#newsberry_bot", text=message, attachments=attachments)
                print(attachments)

