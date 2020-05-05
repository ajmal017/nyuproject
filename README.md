# nyuproject
## Project Title: Social Impact Investing Recommender 
Team Members: Gloria Zheng, Angel Yu, Anvi Agarwal, Kyle Lai, Hadia Faheem

### Motivation & Objectives: 
It can be difficult to determine which companies to invest in and understand their CSR initiatives and business practices. Our project aims to provide an inclusive platform, where individuals can educate themselves on the CSR initiatives, business practices, and sentiment surrounding different companies they’re interested in investing in, as well as helping investors potentially discover new companies doing work to help alleviate issues they care about. In addition, users will be able to study stock performance of these companies, access important financial information, build a sample impact investing portfolio, and see which investments are popular among other users as well. 

### Features:
- Registration & Login
- Quizes to test knowledge on ESG, CSR
- Learning pages with ESG info, news articles
- Customizable Portfolio with visualization of ESG relevance
- Viewing other user profiles, portfolios
- List of stocks grouped by social initiatives, with predicted relevance to those initiatives
- Stock info: financial, ESG related scoring from Yahoo Finance, CSR hub, stock news classified using prediction
- NLP text classification to identify recent news by CSR category
- Discovering, classifying and storing new stocks not in database using yfinance, scraping & fasttext

### Requirements
-Flask framework
-wtforms: for registration
-functools
-yfinance module
-APScheduler module: to update daily prices
-BeautifulSoup
-SQLAlchemy, flask_mysqldb
-Fasttext module and g++ compiler: for training model

-Change the MySQL server when cloning due to expiration. API for stocknews, alphavantage will expire

### Directory
- templates: all HTML pages
  - includes: helper HTML for navbar, forms, wrapper
  
- textanalysis: 
  - analtext.py : trains,loads & runs the model, need to create a new model when cloning since it was too big to upload.
  - requirements.txt : lists requirements needed for fasttext and g++ compiler
  - categ.train, categ.valid : training and validation data to run the model
  - training_data.csv : news articles scraped using scrapy from ESG site to create training & validation, split 70,30%
  - ESG categories.csv : contains the topics model is trained on. The webserver only has 4 categories since the stock news processed is slightly different which messes with model accuracy for range of categories it can process.
  - News.ipynb : contains demo functions to retrieve stock news for model to run on. In jupyter notebook form. The actual functions are compiled onto app.py
  
- Run_project.ipynb : runs the app.py on a jupyter server
- Yahoo_Finance_Installation.ipynb : installs yfinance module and bokeh graphing using jupyter server
- app.db : database for quiz and non-stock news
- app.py : Main Flask webserver. Change the MySQL server when cloning due to expiration. API for stocknews, alphavantage will expire
- esg_models.py : Contains radio/spider graph function, consolidated into app.py
- gloria_graph_for_anvi.ipynb : Contains demo for graph function for stock price over time using yfinance and bokeh
- gloria_yahoo_finance.ipynb : Contains demo function for getting stock info from yfinance
- nyuproject.sql : Contains datatables for Users, Stocks, Portfolios, Articles, Topics, Stocks_Topics. Import into MySQL
