#Main Function
#stock_news_api('TSLA')
import fasttext
import string
import re
import requests
from bs4 import BeautifulSoup 
from sqlalchemy import create_engine
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
#Format Precision Recall Rate
def print_results(N, p, r):
    print("N\t" + str(N))
    print("P@{}\t{:.3f}".format(1, p))
    print("R@{}\t{:.3f}".format(1, r))

#Train Model
#model = fasttext.train_supervised(input="categ.train", lr=1.0, epoch=25, wordNgrams=2)
#model.save_model("model_categ.bin")
#model.quantize(input='categ.train', retrain=True)

#Load Model
model = fasttext.load_model("textanalysis/model_categ.ftz")

#print(model.test('categ.valid'))
#model.save_model("model_categ.ftz")

#Tests Validation Data
#print_results(*model.test('categ.valid'))


#Clean text for NLP analysis
def clean(text):
    text = str(text)
    text = text.lower()
    text=re.sub('[%s]' % re.escape(string.punctuation),'',text)
    text=re.sub('\w*\d\w*','',text)
    text = re.sub('\s+',' ',text)
    return text

#Run Model
def text_anal(text):
    try:
        text=clean(text)
        m=model.predict(text,k=5,threshold=0.62)
        return (str(m[0][0]).replace('__label__',''),m[1][0])
    except Exception as e:
        print(e)
        return (None,None)


#Read Text from Server, Insert Topics Predicted into SQL
def get_text(ticker):
    topics=set()
    #Connect to Server
    #conn_string= 'mysql://{user}:{passw}@{host}/{db}?charset={encoding}'.format(
    #host = '35.221.52.59',
    #user = 'root',
    #db = 'nyuproject',
    #passw = 'dwdstudent2015',
    #encoding = 'utf8mb4'
    #)
    #engine = create_engine(conn_string)
    #con = engine.connect()
    #result = con.execute("SELECT id,txt FROM articles WHERE ticker = %s AND sentiment != 'negative' AND csr_topic is NULL",(ticker))
    
    #Predict Text, insert topic into SQL
    #for r in result:
    #    txt_id = int(r[0])
     #   x=r[1].encode('utf-8')
      #  t=clean(x)
        #print(t)
       # txt_topic = text_anal(t)
        #con.execute("UPDATE articles SET csr_topic = %s WHERE id = %s",(txt_topic,txt_id))
        #topics.add(txt_topic)
    #return topics




#Test on text
#t ='Engineers at Tesla Inc  showed a prototype for a ventilator on Sunday evening in a video published on the companys YouTube channel as hospitals around the country overwhelmed by coronavirus patients face device shortages'
#print(text_anal(t))




#Calls Main Function
#stock_news_api('TSLA')