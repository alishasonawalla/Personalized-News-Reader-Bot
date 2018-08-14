# **Part 1: Gathering and Collecting Data from the NewsAPI and passing it into IBM NLU**
#
# In Part 1 of the project we gather data from 20 different news sources
#
# The process is repeated daily.

# In[2]:


import requests
import json
import MySQLdb as mdb
from datetime import datetime

api_key = 'c4b2099ed8b74e86a0d69fc0fa0b9ce5'

url = 'https://newsapi.org/v2/top-headlines?sources=abc-news,bloomberg,business-insider,espn,buzzfeed,fortune,nbc-news,mtv-news,the-wall-street-journal,the-new-york-times,techcrunch,national-geographic,fox-sports,crypto-coins-news,al-jazeera-english,engadget,google-news,reddit-r-all,the-economist,wired&apiKey=c4b2099ed8b74e86a0d69fc0fa0b9ce5'


# In[3]:


#results_topstories stories data retrieved from api url call
results_stories = requests.get(url).json()
results_stories


# In[4]:


#Process the url
def processURL(url_to_analyze):
    endpoint_watson = "https://gateway.watsonplatform.net/natural-language-understanding/api/v1/analyze"
    params = {
        'version': '2017-02-27',
    }
    headers = {
        'Content-Type': 'application/json',
    }
    watson_options = {
      "url": url_to_analyze,
      "features": {
        "entities": {
          "sentiment": True,
          "limit": 1
        }

      }
    }

    #Updated on Dec 10
    username = "07e5f1fc-8da0-479f-841a-3dadf6e7fcd0"
    password = "kOnp2G2QQKbh"

    resp = requests.post(endpoint_watson, data=json.dumps(watson_options),
                         headers=headers, params=params, auth=(username, password) )
    return resp.json()


# In[5]:


#Create list to store top story urls
storiesURL = []

#Append each url from news api to the list created above
for element in results_stories ["articles"]:
    urls = element['url']
    storiesURL.append(urls)

storiesURL


# In[6]:


# Create a function to extract entities
# from the IBM Watson API and returns a list
# of entities that are relevant (above threshold)
# to the article
def getEntities(data):
    result = []
    result.append({"entities": data['entities'][0]['text'], "type": data['entities'][0]['type'], "sentiment":data['entities'][0]['sentiment']['label']})
    return result


# In[7]:


#Create a new list to store output from watson API
watson_output = []

#Pass each of the in the list of urls, pass it to processUrl to get entities
for url in storiesURL:
    element = processURL(url)
    #print(element)
    print(url)
    try:
        print(element['entities'][0]['text'])
        print(element['entities'][0]['sentiment']['label'])
        print(element['entities'][0]['type'])
        results = getEntities(element)
        watson_output.append(results)
    except:
        #If text and type is there but to sentiment
        #if element['entities'] == []:
        watson_output.append({"entities": None, "type": None, "sentiment":None})

print(watson_output)


# Part 2: Storing the data
#
# We created a table in the database where our Slack bot pulls the data from. We keep the data from the News API and IBM NLU in single table.

# In[8]:


con = mdb.connect(host = 'localhost',
                  user = 'root',
                  passwd = 'dwdstudent2015',
                  charset='utf8', use_unicode=True);


# In[9]:


# Run a query to create a database that will hold the data
db_name = 'news_agg'
create_db_query = "CREATE DATABASE IF NOT EXISTS {db} DEFAULT CHARACTER SET 'utf8'".format(db=db_name)

# Create a database
cursor = con.cursor()
cursor.execute(create_db_query)
cursor.close()


# In[10]:


#Table
cursor = con.cursor()

#Use 'News_aggregator1' for now, since we couldn't add entity columns to the old table
table_name = 'News_aggregator5'
create_table_query = '''CREATE TABLE IF NOT EXISTS {db}.{table}
                                (author varchar(100),
                                title varchar(300),
                                source varchar(250),
                                description varchar(1000),
                                url varchar(250),
                                publishedAts datetime,
                                urlToImage varchar(50),
                                entities varchar(50),
                                entity_type varchar(50),
                                entity_sentiment varchar(50),
                                PRIMARY KEY(url)
                                )'''.format(db=db_name, table=table_name)
cursor.execute(create_table_query)
cursor.close()


# In[11]:


query_template = '''INSERT IGNORE INTO {db}.{table}(author,
                                title,
                                source,
                                description,
                                url,
                                publishedAt,
                                urlToImage,
                                entities,
                                entity_type,
                                entity_sentiment
                                )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''.format(db=db_name, table=table_name)
cursor = con.cursor()

data = results_stories["articles"]
#print(data)
i = 0
for entry in data:
    author = entry['author']
    print(author)
    title = entry['title']
    print(title)

    source = entry['source']['name']
    description = entry['description']
    url = entry['url']
    publishedAt = entry['publishedAt']
    urlToImage = entry['urlToImage']


    try:

        entities = watson_output[i][0]['entities']
        entity_type = watson_output[i][0]['type']
        entity_sentiment = watson_output[i][0]['sentiment']

    except:
        entities = None
        entity_type = None
        entity_sentiment = None


    print(entry)
    print(entities)
    print (entity_type)
    print (entity_sentiment)
    print('------------')

    i+=1

    query_parameters = (author, title, source, description, url, publishedAt, urlToImage, entities, entity_type, entity_sentiment)
    cursor.execute(query_template, query_parameters)

con.commit()
cursor.close()


# In[12]:


print (watson_output[2][0]['entities'])


# In[13]:


print (entry)

