from textanalysis import analtext as textanal
from flask import Flask, render_template, request, flash, redirect, url_for, session, logging, jsonify, Response
from flask_mysqldb import MySQL 
from apscheduler.schedulers.background import BackgroundScheduler
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import requests
import re
from bs4 import BeautifulSoup 
import json
import os 
import io
from flask_sqlalchemy import SQLAlchemy
from esg_models import ESGQuiz, InvestorQuiz
import pytz
import time 

import yfinance as yf
import pandas as pd
from datetime import datetime
from bokeh.plotting import figure, show, save
from bokeh.io import output_notebook
from bokeh.io import export_png
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
from matplotlib.backends.backend_agg import FigureCanvasAgg


app = Flask(__name__)
#Schedule Price Updates daily
sched=BackgroundScheduler(daemon=True)

#Config MySQL
app.config['MYSQL_HOST'] = '35.221.52.59'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'dwdstudent2015'
app.config['MYSQL_DB'] = 'nyuproject'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

app.config['SECRET_KEY'] = 'coffee'

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
@app.before_first_request
def create_tables():
    db.create_all()

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

#About Page
@app.route('/about')
def about():
    render_template('home.html')

#User Class to store functions
class appUser():
    def __init__(self, id):
        self.user_id = int(id)
        self.portfolio_list=[]
        self.watch_list=[]
        self.user_likes=0
    def add_like(self):
        self.user_likes +=1
    def delete_like(self):
        self.user_likes -=1

    def add_stock(self,stock_id,shares):
        cur = mysql.connection.cursor()
        try:
            print('adddding')
            price= cur.execute("SELECT current_price FROM stocks WHERE symbol=%s", [stock_id])
            buy_price=cur.fetchone()['current_price']    
            print(buy_price)  
            result = cur.execute("INSERT INTO portfolios(user_id, ticker,shares, buy_price) VALUES (%s,%s,%s,%s)",[ session['user_id'],stock_id,shares, buy_price])
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            print(e)

    def delete_stock(self,stock_id):
        cur = mysql.connection.cursor()
        result = cur.execute("DELETE FROM portfolios WHERE user_id = %s AND ticker = %s",[ session['user_id'],stock_id])
        mysql.connection.commit()
        cur.close()
    def add_watch(self,port_id):
        self.watch_list.append(port_id)
    def delete_watch(self,port_id):
        self.watch_list.remove(port_id)
        
#initialize User to use functions      
userA = appUser(0)

#User Profile Page. Scrapped.
@app.route('/user/<string:id>/')
def use_page(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM users WHERE id = %s",[id])
    user_info=cur.fetchone()
    return render_template('user.html', id = id, user_info = user_info)

#update current price daily used by Scheduler
def update_current_price():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT symbol FROM stocks")
    stocks = cur.fetchall()
    for stock in stocks:
        ticker = stock['symbol']
        stock_object=yf.Ticker(ticker)
        try:
            current_price=stock_object.info['regularMarketOpen']
            result = cur.execute("UPDATE IGNORE stocks SET current_price = %s WHERE symbol = %s",[current_price,ticker])
            mysql.connection.commit()
            print(current_price)
            print(ticker)
        except Exception as e:
            print(e)
    cur.close()

#convert to proper date format from Thur,10 May 2020 -> 2020 10 May
def make_date_standard(news_date):
    m = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr':'04',
    'May':'05',
    'Jun':'06',
    'Jul':'07',
    'Aug':'08',
    'Sep':'09',
    'Oct':'10',
    'Nov':'11',
    'Dec':'12'
    }
    match = re.search(r'(\d\d)',news_date)
    date = match.group()
    match = re.search(r'(\w\w\w )',news_date)
    month = match.group().strip()
    month = m[month]
    match = re.search(r'(\d\d\d\d)',news_date)
    year = match.group()
    x=year.strip()+'-'+month+'-'+date.strip()
    print(x)
    return(x)

#given url returns article body text and cleans text
def get_news_text(url):
    sources = {
                "nytimes"  : ["p", "css-exrw3m evys1bk0"], 
                "forbes"   : ["div", "article-body fs-article fs-responsive-text current-article"],
                "reuters"  : ["div", "StandardArticleBody_body"],
                "cnbc"     : ["div", "group"],
                "cnn"      : ["div", "zn-body__paragraph"],
                "abcnews"  : ["article", "Article__Content story"],
                "foxnews"  : ["div", "article-body"]
              }
    text = ''
    for source in sources.keys():
        s = r"" + source + "."
        match = re.search(s, url)
        #if url matches one of the sources
        if match:
            #print(url)
            page = requests.get(url)
            bs = BeautifulSoup(page.text, "html.parser")
            body = bs.findAll(sources[source][0], sources[source][1])
            for i in body:
                text += i.text.strip()
    return text

#Given ticker, Checks news if CSR related, Stores news info into SQL 
def stock_news_api(name):
    url_list = []
    #Connect to API
    api = "https://stocknewsapi.com/api/v1"
    params = {
        "tickers": name,
        "items"  : 30,
        "token"  : "4okeu5r8mulzj6oycl8waqnry2dzmtmhdln2jxzg",
        "source" : "Reuters,Forbes,CNBC,CNN,NYTimes",
        "topicexclude":"earnings,manda,product,dividend,CEO,tanalysis",
        "type":"article"
    }
    data = requests.get(api, params = params).json()
    #Connect to Server
    cur = mysql.connection.cursor()
    #for each article
    for i in data["data"]:
        #Check if article only talks about 1 company
        if len(i['tickers'])==1 and i['sentiment'] !='Negative':
            #process text from url
            text=get_news_text(i['news_url'])
            #run model
            predict_txt = textanal.text_anal(text)

            txt_topic = predict_txt[0]
            #if model prediction passes then store it
            if isinstance(txt_topic,str):
                try:
                    predict_rate = "{:.2f}".format(predict_txt[1])
                    if predict_rate != '1.00':
                        news = i['news_url']
                        img = i['image_url']
                        title = i['title']
                        txt = i['text']
                        src = i['source_name']
                        date = make_date_standard(i['date'])
                        sent = i['sentiment']
                        tick = i['tickers'][0]
                        csr_topic = txt_topic
                        result = cur.execute("INSERT IGNORE INTO stocks_topics(ticker,topic) VALUES (%s,%s)",(tick,csr_topic))
                        mysql.connection.commit()
                        status = cur.execute("INSERT INTO articles(title,txt,create_date, sentiment, news_url,image_url,source_name,ticker, csr_topic,predict_rate) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(title,txt,date,sent,news,img,src,tick,csr_topic,predict_rate))
                        mysql.connection.commit()
                        print(status)
                except Exception as e:
                    print(e)
                    pass
    cur.close()
    
#Check if stock is in user's portfolio
def stock_is_in_list(ticker):
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM portfolios WHERE ticker = %s AND user_id = %s",[ticker, session['user_id']])
        stock = cur.fetchone()
        cur.close()
        if stock == None:
               return False                                                                           
        return True

#get financials from Alpha Vantage 
def get_financials(symbol): 
    
    url = "https://www.alphavantage.co/query"

    params = {
        "function"   : "GLOBAL_QUOTE",
        "symbol"     : symbol,
        "outputsize" : "compact",
        "datatype"   : "json",
        "apikey"     : "B2RZQV8B10444N5I"
    }

    data = requests.get(url, params = params).json()
    
    try: 
        open_price = data['Global Quote']['02. open'] 
    except: open_price =  None
    try: 
        current_price = data['Global Quote']['05. price'] 
    except: current_price = None
    try: 
        daily_high = data['Global Quote']['03. high'] 
    except: daily_high = None
    try: 
        daily_low = data['Global Quote']['04. low'] 
    except: daily_low = None
    try: 
        daily_volume = data['Global Quote']['06. volume'] 
    except: daily_volume = None
    try: 
        previous_close = data['Global Quote']['08. previous close'] 
    except: previous_close = None
    try: 
        price_change = data['Global Quote']['10. change percent'].replace("%","") 
    except: price_change = None
    
    yahoofinance_link = "https://finance.yahoo.com/quote/" + symbol + "?p=" + symbol
    
    return {
            "open_price" : open_price,
            "current_price": current_price,
            "daily_high": daily_high,
            "daily_low": daily_low,
            "daily_volume": daily_volume,
            "previous_close": previous_close,
            "price_change": price_change,
            "yahoofinance_link": yahoofinance_link
           }

#get esg scores from yahoo finance 
# Yahoo Finance ESG Scores 
def get_yf_esg_scores(symbol):

    url = "https://finance.yahoo.com/quote/" + symbol + "/sustainability?p=" + symbol
    page = requests.get(url)
    bs = BeautifulSoup(page.text, "html.parser")
    
    try:
        esg_score = bs.findAll("div", "Fz(36px) Fw(600) D(ib) Mend(5px)")[0].text
    except: esg_score = None
    try:
        esg_percentile = bs.findAll("span", "Bdstarts(s) Bdstartw(0.5px) Pstart(10px) Bdc($seperatorColor) Fz(12px) smartphone_Bd(n) Fw(500)")[0].find("span").text
    except: esg_percentile = None
    try:
        scores = bs.findAll("div", "D(ib) Fz(23px) smartphone_Fz(22px) Fw(600)")
    except: scores = None
    try:
        env_score = scores[0].text
    except: env_score = None
    try:
        soc_score = scores[1].text
    except: soc_score = None
    try:
        gov_score = scores[2].text
    except: gov_score = None
    
    return {
        "esg_score": esg_score,
        "esg_percentile": esg_percentile,
        "env_score": env_score,
        "soc_score": soc_score,
        "gov_score": gov_score
    }


#scrape CSR Hub for score
def get_csr_score_and_industry(name):
    name = name.replace(", Inc.","")
    name = name.replace(" ", "-")
    
    url = "https://www.csrhub.com/CSR_and_sustainability_information/" + name
    page = requests.get(url)
    bs = BeautifulSoup(page.text, "html.parser")
    
    try:
        csr_score = bs.findAll("span", "value")[0].text
        industry = bs.find("div", "company-section_sheet").find("td", text = "Industry:").find_next_sibling("td").text.split(", ")[0]
    except:
        csr_score = None,
        industry = None 
        
    return {
        "csr_score": csr_score,
        "industry" : industry
    }


#update stock info 
@app.route('/update/<string:ticker>/')
def update_stock_info(ticker):
    cur = mysql.connection.cursor()
    cur.execute("select symbol,name,last_update from stocks where symbol = %s",[ticker])
    stock = cur.fetchone()
    
    if stock['last_update'] == None or stock['last_update'].date() != datetime.now(pytz.timezone("US/Eastern")).date():

        update_template = '''update nyuproject.stocks
                            set
                                current_price = %s,
                                open_price = %s,
                                daily_high = %s,
                                daily_low = %s,
                                daily_volume = %s,
                                previous_close = %s,
                                price_change = %s,
                                yf_esg_score = %s,
                                yf_esg_percentile = %s,
                                yf_env_score = %s,
                                yf_soc_score = %s,
                                yf_gov_score = %s,
                                ch_csr_score = %s,
                                last_update = %s      
                            where symbol = %s;'''


        current_time = datetime.now(pytz.timezone("US/Eastern"))

        financials = get_financials(stock['symbol'])
        yf1 = get_yf_esg_scores(stock['name'])
        ch = get_csr_score_and_industry(stock['name'])

        update_parameters = financials["current_price"], financials["open_price"], financials["daily_high"], financials["daily_low"], financials["daily_volume"], financials["previous_close"],financials["price_change"], yf1["esg_score"], yf1["esg_percentile"], yf1["env_score"] , yf1["soc_score"], yf1["gov_score"], ch["csr_score"], current_time, stock["symbol"]

        cur.execute(update_template, update_parameters)

    
    return redirect(url_for('stock_page',ticker=ticker)) 

#stock info page 
@app.route('/stock/<string:ticker>/', methods = ['GET','POST'])
def stock_page(ticker):
    if request.method == 'GET':
        #If not logged-in
        stock_in_list = ticker in userA.portfolio_list
        #If logged in, show add portfolio button
        if 'logged_in' in session:
            stock_in_list =stock_is_in_list(ticker)
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM stocks WHERE symbol = %s",[ticker])
        stock = cur.fetchone()
        result = cur.execute("SELECT * FROM articles WHERE ticker = %s ORDER BY create_date DESC",[ticker])
        news=cur.fetchall()
        cur.close()
        #if(len(news)==0):
            #return render_template('stock_info.html',stock = stock,ticker=ticker, user = userA, stock_in_list=stock_in_list, news = news, news_exist = False)    

#plotting graphs
        data = yf.download(tickers = ticker, period='ytd')
        data = data.reset_index()
        title = ''.join(("Year-to-Date performance of ", ticker.upper()))
        p = figure(title=title, x_axis_label = "Date", y_axis_label="Stock Price", x_axis_type="datetime", plot_width=700, plot_height=300)
        p.toolbar.logo = None
        p.toolbar_location = None
        p.line(y = data["Open"], x = data["Date"], color="green")
        
        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()
        script, div = components(p)

#other information
        obj = yf.Ticker(ticker)
        try: 
            country = obj.info['country']
        except: 
            country = 'N/A'
        try: 
            website = obj.info['website']
        except: 
            website = 'N/A'
        try: 
            bus = obj.info['longBusinessSummary']
        except: 
            bus = ''
        try: 
            name = obj.info['longName']
        except: 
            name = 'N/A'
        Vol = obj.info['averageVolume10days']
        beta = obj.info['beta']
        PEG = obj.info['pegRatio']
        ADR = obj.info['trailingAnnualDividendRate']
        BV = obj.info['bookValue']
        bid = obj.info['bid']
        ask = obj.info['ask']
        vol = obj.info['volume']
        vol10 = obj.info['averageDailyVolume10Day']
        low = obj.info['dayLow']
        high = obj.info['dayHigh']
        mclose = obj.info['previousClose']
        mopen = obj.info['regularMarketOpen']

        
#CSR topics 
        topics = stock_topics(ticker)
        
        return render_template('stock_info.html',stock = stock,ticker=ticker, user = userA, stock_in_list=stock_in_list, news = news, news_exist=True, plot_script=script, plot_div=div, js_resources=js_resources, css_resources=css_resources, country=country, website=website, bus=bus, Vol=Vol, beta=beta, PEG=PEG, ADR=ADR, BV=BV, name=name, bid=bid, ask=ask, vol=vol, vol10 = vol10, low=low, high=high, mclose=mclose, mopen=mopen, topics=topics)    
    #Post Request
    if request.method == 'POST':
        #remove stock from portfolio
        if stock_is_in_list(ticker):
            userA.delete_stock(ticker)
            flash('Removed stock {} from portfolio'.format(ticker),'success')
            return redirect(url_for('stock_page',ticker=ticker))

        return redirect(url_for('stock_page',ticker=ticker))

#JSON process num shares when add portfolio
@app.route('/process',methods=['POST'])
def process():
    if request.method == 'POST':
        req = request.get_json()
        numShares=req['shares']
        ticker = req['ticker']
        if ticker!=0 and ticker is not None:
            userA.add_stock(ticker,numShares)           
            return jsonify({'num':req})
        return jsonify({'error':'Missing Value'})

    
    
#Call Article Topic Predictor
@app.route('/predict/<string:ticker>/', methods = ['GET','POST'])
def predict(ticker):
    if request.method == 'POST':
        stock_news_api(ticker)
        return redirect(url_for('stock_page',ticker=ticker))

#Display List of All stocks
@app.route('/allstocks', methods = ['GET','POST'])
def allstocks():
    cur= mysql.connection.cursor()
    #The dropdown is selected
    categ = request.form.getlist('Item_1')
    if len(categ)>0 and categ[0] !='0':
        #Get the stocks from the related dropdown
        categ=categ[0]
        print(categ)
        action0A = cur.execute("SELECT stocks.symbol, stocks.name, stocks.industry, AVG(articles.predict_rate) AS relevancy FROM stocks_topics INNER JOIN stocks ON stocks_topics.ticker = stocks.symbol INNER JOIN articles ON stocks_topics.ticker = articles.ticker WHERE articles.csr_topic LIKE %s GROUP BY stocks_topics.ticker", [categ])
        stocks = cur.fetchall()
        #Change the key for HTML to process
        for x in stocks:
            x['relevancy']='{:.0%}'.format(x['relevancy'])
    #No selection
    else:
        categ=''
        print('category empty')
        print(categ)
        action0B = cur.execute("SELECT stocks.name, stocks.industry, stocks.symbol, AVG(articles.predict_rate) AS relevancy FROM stocks LEFT OUTER JOIN articles ON stocks.symbol = articles.ticker GROUP BY stocks.symbol")
        stocks = cur.fetchall()
        for x in stocks:
            if x['relevancy'] is None:
                x['relevancy'] = "N/A"
            else:
                x['relevancy']='{:.0%}'.format(x['relevancy'])
    cur.close()
    categ = categ.replace('-',' ')
    return render_template("allstocks.html", stocks = stocks,category = categ)

#Call Stock Discovery if stock doesnt exist in database
@app.route('/discover/<string:ticker>/', methods = ['GET','POST'])
def discover(ticker):
    if request.method == 'GET':
        return render_template('notfound.html',ticker=ticker,notfound=True)
    if request.method == 'POST':
        print('LETS MAKE A DISCOVERY')
        try:
            stock_yf=yf.Ticker(ticker)
            stock_name = stock_yf.info['shortName']
            financials = get_financials(ticker)
            yfs = get_yf_esg_scores(ticker)
            ch = get_csr_score_and_industry(stock_name)
        except Exception as e:
            print(e)
            flash('We Could Not Find {}'.format(ticker),'danger')
            return render_template('notfound.html',ticker=ticker,notfound = True)
        cur = mysql.connection.cursor()
        cur.execute('''INSERT IGNORE INTO stocks(symbol,
                                        name,
                                        current_price,
                                        open_price,
                                        daily_high,
                                        daily_low,
                                        daily_volume,
                                        previous_close,
                                        price_change,
                                        yf_esg_score,
                                        yf_esg_percentile,
                                        yf_env_score,
                                        yf_soc_score,
                                        yf_gov_score,
                                        ch_csr_score,
                                        industry
                                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',[ticker, stock_name,financials["current_price"], financials["open_price"], financials["daily_high"], financials["daily_low"], financials["daily_volume"], financials["previous_close"],financials["price_change"], yfs["esg_score"], yfs["esg_percentile"], yfs["env_score"] , yfs["soc_score"], yfs["gov_score"], ch["csr_score"], stock_yf.info['industry']])
        mysql.connection.commit()
        print('inserted new stock')
        stock_news_api(ticker)
        return redirect(url_for('stock_page',ticker=ticker))

#Ticker Search Bar
@app.route('/search')
def search():
    name = request.args.get('searcher')
    name = name.upper()
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * FROM stocks WHERE symbol = %s',[name])
    #Redirects to stock page
    if result > 0:
        return redirect(url_for('stock_page',ticker=name))
    else:
        print(result)
    return render_template("notfound.html",ticker=name,notfound=False)



# Register Form Class
class RegisterForm(Form):
    #name = StringField('Name', [validators.Length(min=1,max=50)])
    username=StringField('Username',[validators.Length(min=4,max=25)])
    #email=StringField('email',[validators.Length(min=6,max=25)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message ='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

#Register Users
@app.route('/register', methods = ['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            #name = form.name.data
            #email = form.email.data
            username = form.username.data
            password = sha256_crypt.encrypt(str(form.password.data))
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users(username,password) VALUES (%s, %s)",(username,password))
            mysql.connection.commit()
            cur.close()
            flash('You are now registered and can log in','success')
            return redirect(url_for('login'))
        except:
            flash('Username taken','danger')
            return redirect(url_for('register'))
    return render_template('signup.html',form=form) 

#Login Page
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        #Get Form Fields
        username=request.form['username']
        password_candidate = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute('SELECT * FROM users WHERE username = %s',[username])
        if result > 0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']
            #compare passwords
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in']=True
                session['username'] = username
                session['user_id'] = data['id']
                userA = appUser(data['id'])
                cur.close()
                flash('You are now logged in','success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error = error)
            #close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html',error = error)
        
    return render_template('login.html')

#Check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login','danger')
            return redirect(url_for('login'))
    return wrap

#Logout User
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#Dashboard for User
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

#Charts
@app.route('/users_chart')
@is_logged_in
def users_chart(): 
    cur= mysql.connection.cursor()
    cur.execute('SELECT ticker, COUNT(*) as count FROM portfolios GROUP BY ticker ORDER BY count DESC')
    t = cur.fetchall()
    return render_template('users_chart.html', t=t)

@app.route('/learn_more_esg')
def learn_more_esg ():
    data = yf.download(tickers = 'DSI, SPY', period='10y')
    data = data.reset_index()
    p = figure(title="Stock chart of KLD400 Social Index and S&P 500", x_axis_label = "Date", y_axis_label="Stock Price", x_axis_type="datetime", plot_width=800, plot_height=300)
    p.line(y = data['Adj Close']['SPY'], x = data["Date"], color="green",  legend_label="S&P 500")
    p.line(y = data['Adj Close']['DSI'], x = data["Date"], color="blue", legend_label="KLD400 Social Index")
    p.legend.location = "top_left"
    p.legend.click_policy="hide"
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    script, div = components(p)
    
    return render_template('learn_more_esg.html', plot_script=script, plot_div=div, js_resources=js_resources, css_resources=css_resources)

@app.route('/learn_more_investing')
def learn_more_investing ():
    data = yf.download(tickers = 'SPY', period='5y')
    data = data.reset_index()
    p = figure(title="Stock chart of S&P 500", x_axis_label = "Date", y_axis_label="Stock Price", x_axis_type="datetime", plot_width=800, plot_height=300)
    p.line(y = data['Adj Close'], x = data["Date"], color="green")
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    script, div = components(p)

    return render_template('learn_more_investing.html', plot_script=script, plot_div=div, js_resources=js_resources, css_resources=css_resources)

@app.route('/choose_quiz')
def choose_quiz(): 
    return render_template ('choose_quiz.html')

############QUIZZES################
class ESGAnswers(db.Model):
    __tablename__ = 'ESGAnswers'
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.Text)
    q1 = db.Column(db.Text)
    q2 = db.Column(db.Text)
    q3 = db.Column(db.Text)
    q4 = db.Column(db.Text)
    q5 = db.Column(db.Text)
    q6 = db.Column(db.Text)
    q7 = db.Column(db.Text)
    q8 = db.Column(db.Text)

    def __init__(self,username,q1,q2,q3,q4,q5,q6,q7,q8):
        self.username = username
        self.q1=q1
        self.q2=q2
        self.q3=q3
        self.q4=q4
        self.q5=q5
        self.q6=q6
        self.q7=q7
        self.q8=q8

@app.route('/esg_quiz', methods = ['GET', 'POST'])
def esg_quiz(): 
    form = ESGQuiz()
    if form.validate_on_submit():
        username = form.username.data
        q1=form.q1.data
        q2=form.q2.data
        q3=form.q3.data
        q4=form.q4.data
        q5=form.q5.data
        q6=form.q6.data
        q7=form.q7.data
        q8=form.q8.data
        my_answers = ESGAnswers(username,q1,q2,q3,q4,q5,q6,q7,q8)
        db.session.add(my_answers)
        db.session.commit()

        return redirect('/esgquiz_answers?username='+username)


    return render_template('esgquiz.html', form=form)

@app.route('/esgquiz_answers', methods=['GET','POST'])
def esgquiz_answers():
    form = ESGQuiz()
    q1=form.q1.label
    q2=form.q2.label
    q3=form.q3.label
    q4=form.q4.label
    q5=form.q5.label
    q6=form.q6.label
    q7=form.q7.label
    q8=form.q8.label
    questions = [q1, q2, q3, q4, q5, q6, q7, q8]    
    user = request.args.get('username')
    answers = ESGAnswers.query.filter_by(username=user).first()
    myanswers = [answers.q1, answers.q2, answers.q3, answers.q4, answers.q5, answers.q6,
                    answers.q7, answers.q8]
    right_answers = ['Stakeholder', 'False', 'Negative Screening', 'All of the above', 'Sustainable Sector Funds', '10%', 'Investors with USD 50+ mn in assets', 'None - comparable performance']
    explanation = ['ESG stands for environmental, social, and governance. It does not include Stakeholder', '“ESG programs reduce returns on capital and long-run shareholder value” is a common myth but that is simply not true. Companies who responsibly their ESG metrics are also those who manage to do well.', 'The method of constructing your portfolio to exclude select stocks is called negative screening. Positive screening is when you construct your portfolio with the intention of including certain stocks.', 'Exclusion, integration, and impact all fit into the framework of sustainable investing!', 'Sustainable Sector funds contribute to the transition to a green economy. ESG Consideration funds are are otherwise conventional funds that now say they consider ESG factors in their investment process. ESG focus funds may have ‘ESG’ in it but it’s not a commonly used term!', 'Did you know that US is lagging behind its global peers when it comes to sustainable investments in their portfolios? Only 12% of US investors have adopted sustainable investments compared to 39% globally.', 'People with more assets are more likely to invest sustainably. 40% of people with USD 50 million+ in assets are investing sustainably compared to 8% of people with 1million - 2 million in assets. Also, whilst 72% of people ages 19-34 invest sustainably,  only 6% of people ages 65+ invest sustainably. When it comes to investing sustainably, the young and wealthy lead the way!', 'UBS did a comparison of historical returns of sustainable investment indices and conventional indices. The fundings suggested that investing sustainably does not hinder performance of the portfolio. For example, over a 28 year period, the S&P 500 index generalised an annualised return of 10.3% whilst the MSCI KLD 400 Social Index, which is the sustainable equivalent of the S&P generated an annualised return of 10.7%. The volatility during that time was also comparable - S&P 500 had a volatility of 14.1% whilst MSCI KLD 400 Social Index had a volatility of 14.6%.']
    db.session.delete(answers)
    db.session.commit()
    return render_template('esgquiz_answers.html', myanswers=myanswers, right_answers=right_answers, questions=questions, user=user, explanation=explanation)

class InvestorAnswers(db.Model):
    __tablename__ = 'InvestorAnswers'
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.Text)
    q1 = db.Column(db.Text)
    q2 = db.Column(db.Text)
    q3 = db.Column(db.Text)
    q4 = db.Column(db.Text)
    q5 = db.Column(db.Text)
    q6 = db.Column(db.Text)
    q7 = db.Column(db.Text)
    q8 = db.Column(db.Text)

    def __init__(self,username,q1,q2,q3,q4,q5,q6,q7,q8):
        self.username = username
        self.q1=q1
        self.q2=q2
        self.q3=q3
        self.q4=q4
        self.q5=q5
        self.q6=q6
        self.q7=q7
        self.q8=q8

@app.route('/investor_quiz', methods = ['GET', 'POST'])
def investor_quiz(): 
    form = InvestorQuiz()
    if form.validate_on_submit():
        username = form.username.data
        q1=form.q1.data
        q2=form.q2.data
        q3=form.q3.data
        q4=form.q4.data
        q5=form.q5.data
        q6=form.q6.data
        q7=form.q7.data
        q8=form.q8.data
        my_answers = InvestorAnswers(username,q1,q2,q3,q4,q5,q6,q7,q8)
        db.session.add(my_answers)
        db.session.commit()

        return redirect('/investorquiz_answers?username='+username)
    return render_template('investorquiz.html', form=form)

@app.route('/investorquiz_answers', methods=['GET','POST'])
def investorquiz_answers():
    form = InvestorQuiz()
    q1=form.q1.label
    q2=form.q2.label
    q3=form.q3.label
    q4=form.q4.label
    q5=form.q5.label
    q6=form.q6.label
    q7=form.q7.label
    q8=form.q8.label
    questions = [q1, q2, q3, q4, q5, q6, q7, q8]    
    user = request.args.get('username')
    answers = InvestorAnswers.query.filter_by(username=user).first()
    myanswers = [answers.q1, answers.q2, answers.q3, answers.q4, answers.q5, answers.q6,
                    answers.q7, answers.q8]
    right_answers = ['Savings is putting money aside for future use. Investing is using the money to generate further returns', '$46,4285', 'All of the Above', 'You own a part of the company', 'You have lent money to the company', 'Go Up', 'Selling shares of a stock at a loss', 'The higher the risk, the higher the return']
    explanation = ['Savings is putting money aside for future use. Investing is using the money to generate further returns. Savings often involves putting the money in a savings account in a bank. Investing often involves using the money to buy securities, such as stocks, bonds, and ETFs in the hopes that their value will increase in the future.', 'The equation for calculating the future value of the money belonging to Sue is as follows: 3,000*(((1+6%)^40-1)/6%)=50,000*(1.06^40-1)=$46,4285.89', 'Investment Horizon, risk, and ability to generate income are all important factors to consider before you start investing.', 'A stock is a security that indicates the holder has ownership in the issuing company. So if you buy a company’s stock, then you own a part of the company.', 'A bond is a security that indicates the holder is lending money to the company. In return, the user is entitled to the future cash flow of the company. Thus, if you buy a company’s bonds, then you have lent money to the company. You are not liable for the company’s debts - the own the company’s debts.', 'If interest rates go down, the bond prices go up. This is due to the mathematical relationship between the interest rates and the bond prices. The yield of a bond is the return to an investor and this has an inverse relationship with the bond price', 'Short selling occurs when an investor borrows a security and sells it in the open market. It sounds weird, but you’re essentially selling what you don’t own! You are able to do this because you are planning to buy the security back later for less money. When you sell short, you are betting the price of the security will decrease in the future. Therefore, you can sell at the price in the open market, and when the price decreases, you can return the security you borrowed by buying it back at a lower price.', 'There is a positive relationship between the risk and return. When the risk increases, the return typically decreases. From another perspective, when you receive a higher return, this is because you are willing to take on the additional risk. People are willing to pay you additional money for the risk that you are taking on.']
    db.session.delete(answers)
    db.session.commit()
    return render_template('investorquiz_answers.html', myanswers=myanswers, right_answers=right_answers, questions=questions, user=user, explanation=explanation)

############END QUIZ SECTION ##################
@app.route('/more_info')
def more_info():
    return render_template('more_info.html')

@app.route('/news_topics')
def news_topics(): 
    return render_template('news_topics.html')

@app.route('/clean_energy')
def clean_energy(): 
    subscription_key = "f060e0cc74e1475fac9385655fdb1f44"
    search_term = "business clean energy"
    search_url = "https://api.cognitive.microsoft.com/bing/v7.0/news/search"

    headers = {"Ocp-Apim-Subscription-Key" : subscription_key}
    params  = {"q": search_term}

    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()

    display_news = search_results['value']
    return render_template('clean_energy.html', display_news=display_news)

@app.route('/diversity')
def diversity():
    subscription_key = "f060e0cc74e1475fac9385655fdb1f44"
    search_term = "business diversity inclusion"
    search_url = "https://api.cognitive.microsoft.com/bing/v7.0/news/search"

    headers = {"Ocp-Apim-Subscription-Key" : subscription_key}
    params  = {"q": search_term}

    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()

    display_news = search_results['value']
    return render_template('diversity.html', display_news=display_news)

@app.route('/supply_chain')
def supply_chain(): 
    subscription_key = "f060e0cc74e1475fac9385655fdb1f44"
    search_term = "business supply chain transparency"
    search_url = "https://api.cognitive.microsoft.com/bing/v7.0/news/search"

    headers = {"Ocp-Apim-Subscription-Key" : subscription_key}
    params  = {"q": search_term}

    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()

    display_news = search_results['value']
    return render_template('supply_chain.html', display_news=display_news)

@app.route('/employees')
def employees(): 
    subscription_key = "f060e0cc74e1475fac9385655fdb1f44"
    search_term = "employee benefits"
    search_url = "https://api.cognitive.microsoft.com/bing/v7.0/news/search"

    headers = {"Ocp-Apim-Subscription-Key" : subscription_key}
    params  = {"q": search_term}

    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()

    display_news = search_results['value']
    return render_template('employees.html', display_news=display_news)

@app.route('/investing_news')
def investing_news(): 
    subscription_key = "f060e0cc74e1475fac9385655fdb1f44"
    search_term = "esg investing"
    search_url = "https://api.cognitive.microsoft.com/bing/v7.0/news/search"

    headers = {"Ocp-Apim-Subscription-Key" : subscription_key}
    params  = {"q": search_term}

    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()

    display_news = search_results['value']
    return render_template('investing_news.html', display_news=display_news)

@app.route("/portfolio")
@is_logged_in
def portfolio():
    cur= mysql.connection.cursor()
    stocks= cur.execute("SELECT * from portfolios WHERE user_id= %s", session['user_id'])
    portfolios= cur.fetchall()
    stock_info= cur.execute("SELECT * from stocks")
    info= cur.fetchall()
    return render_template("portfolio.html", portfolios=portfolios, info=info)

#get CSR topics on aggregate
def stock_topics(ticker):
    cur = mysql.connection.cursor() 
    cur.execute("select topic from stocks_topics where ticker = %s", [ticker])
    results = cur.fetchall()
    result_list = []
    for i in results:
        result_list.append(i['topic'])
    return result_list

@app.route("/allusers")
@is_logged_in
def allusers():
    cur= mysql.connection.cursor()
    cur.execute("select * from users")
    users = cur.fetchall()
    cur.execute("select * from portfolios")
    portfolios = cur.fetchall()
    user_list = []
    for i in users:
        flag = True 
        for j in portfolios:
            if i['id'] == j['user_id']:
                user_list.append([i['id'], i['username'], j['ticker'], j['shares']])
                flag = False 
        if flag: user_list.append([i['id'], i['username'], None, None]) 
    return render_template("allusers.html", user_list=user_list)


#radar chart on portfolio page 
def pull_user_portfolio():
    cur= mysql.connection.cursor()
    cur.execute('''select a.user_id, a.shares, a.ticker, b.topic
                                from portfolios a
                                join stocks_topics b
                                where a.user_id = %s
                                and a.ticker = b.ticker''', session['user_id'])
    results = cur.fetchall() 
    
    params = [0,0,0,0]
    
    for result in results:
        count = result['shares']
        topic = result['topic']
        if topic == 'Environment': params[0] += count
        if topic == 'Health-&-Wellness': params[1] += count
        if topic == 'Human-Resources-&-Diversity': params[2] += count
        if topic == 'Philanthropy-&-Corporate-Contributions': params[3] += count
        
    return params

def radar_factory():
    theta = np.linspace(0, 2*np.pi, 4, endpoint=False)

    class RadarAxes(PolarAxes):

        name = 'radar'
        RESOLUTION = 1

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_theta_zero_location('N')

        def fill(self, *args, closed=True, **kwargs):
            return super().fill(closed=closed, *args, **kwargs)

        def plot(self, *args, **kwargs):
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)

        def _close_line(self, line):
            x, y = line.get_data()
            if x[0] != x[-1]:
                x = np.concatenate((x, [x[0]]))
                y = np.concatenate((y, [y[0]]))
                line.set_data(x, y)

        def set_varlabels(self, labels):
            self.set_thetagrids(np.degrees(theta), labels)

        def _gen_axes_patch(self):
                return RegularPolygon((0.5, 0.5), 4,
                                      radius=.5, edgecolor="k")
        def _gen_axes_spines(self):
                spine = Spine(axes=self,
                              spine_type='circle',
                              path=Path.unit_regular_polygon(4))
                spine.set_transform(Affine2D().scale(.5).translate(.5, .5)
                                    + self.transAxes)
                return {'polar': spine}

    register_projection(RadarAxes)
    return theta

@app.route("/plot.png")
def plot():
    
    parameters = pull_user_portfolio()
            
    data = [
        ['Environment', 'Health & Wellness', 'Human-Resources & Diversity', 'Philanthropy '],
        ('', [parameters])]

    theta = radar_factory()

    spoke_labels = data.pop(0)

    fig, ax = plt.subplots(figsize=(6, 5), nrows=1, ncols=1,subplot_kw=dict(projection='radar'))
    fig.subplots_adjust(wspace=0.25, hspace=0.20, top=0.85, bottom=0.05)

    color = 'g'
    for title, case_data in data:
        ax.set_title(title, weight='bold', size='medium', position=(0.5, 1.1), horizontalalignment='center', verticalalignment='center')
        for d in case_data:
            ax.plot(theta, d, color=color)
            ax.fill(theta, d, facecolor=color, alpha=0.25)
        ax.set_varlabels(spoke_labels)
    fig.text(0.5, 0.965, 'CSR Profile of My Portfolio',
             horizontalalignment='center', color='black', weight='bold', size='large')

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")
    
    


if __name__ == '__main__':
    #Update prices daily Mon-Fri at 10am
    sched.add_job(update_current_price,'cron',day_of_week = 'mon,tue,wed,thu,fri',hour='10')
    sched.start()
    app.secret_key='secret123'
    app.run(host='0.0.0.0', port=5000, debug=True)

    