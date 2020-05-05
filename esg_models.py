from flask_wtf import FlaskForm
from wtforms import StringField,RadioField, SubmitField, IntegerField
from wtforms.validators import InputRequired

class ESGQuiz(FlaskForm):
    username = StringField('Enter Username: ')
    q1 = RadioField('(1) Which of the following is not a part of the “ESG” Framework?',
                    choices=[('Environmental', 'Environmental'), ('Stakeholder', 'Stakeholder'), ('Governance', 'Governance'), ('Social', 'Social')],
                    validators=[InputRequired()])

    q2 = RadioField('(2) True or False: ESG programs reduce returns on capital and long-run shareholder value”.',
                    choices=[('True', 'True'), ('False', 'False')],
                    validators=[InputRequired()])

    q3 = RadioField('(3) The method of constructing your portfolio so that it excludes or avoids “problem” stocks, such as tobacco companies, is called ________________.',
                    choices=[('Impact Investing', 'Impact Investing'), ('Positive Screening', 'Positive Screening'), 
                            ('Negative Screening', 'Negative Screening')],
                    validators=[InputRequired()])

    q4 = RadioField('(4) Which of the following investing categories fit into the framework of sustainable investing?',
                    choices=[('Exclusion', 'Exclusion'), ('Integration', 'Integration'), ('Impact', 'Impact'), ('All of the above', 'All of the above')],
                    validators=[InputRequired()])

    q5 = RadioField('(5) If you wanted to invest in companies that contribute to the transition to a green economy, what kinds of funds would you focus on?',
                    choices=[('Sustainable Sector Funds', 'Sustainable Sector Funds'), ('EFG Consideration funds', 'EFG Consideration funds'), ('ESG Focus Funds', 'ESG Focus Funds')],
                    validators=[InputRequired()])

    q6 = RadioField('(6) Approximately what percent of US investors have sustainable investments in their portfolios?',
                    choices=[('10%', '10%'), ('20%', '20%'), ('40%', '40%'), ('60%', '60%')],
                    validators=[InputRequired()])

    q7 = RadioField('(7) Which demographic holds a larger share of sustainable investments?',
                    choices=[('Investors with USD 50+ mn in assets', 'Investors with USD 50+ mn in assets'), ('Investors with USD 1 mn - 2mn in assets', 'Investors with USD 1 mn - 2mn in assets')],
                    validators=[InputRequired()])

    q8 = RadioField('(8) How much performance do investors typically sacrifice by investing sustainably?',
                    choices=[('None - comparable performance', 'None - comparable performance'), ('None - outperformance', 'None - outperformance'), ('Moderate loss of performance', 'Moderate loss of performance'), ('Significant loss of performance', 'Significant loss of performance')],
                    validators=[InputRequired()])

    submit = SubmitField('Submit My Answers')
    

class InvestorQuiz(FlaskForm):
    username = StringField('Enter Username: ')
    q1 = RadioField('(1) What is the difference between saving and investing?',
                    choices=[('Savings is putting money aside for future use. Investing is using the money to generate further returns', 'Savings is putting money aside for future use. Investing is using the money to generate further returns'), ('Savings will allow my money to grow while investing does not because it carries significant risks', 'Savings will allow my money to grow while investing does not because it carries significant risks'), ('They’re the same!', 'They’re the same!'), ('I don’t know', 'I don’t know')],
                    validators=[InputRequired()])

    q2 = IntegerField('(2) If Sue invests $3,000 every year for 40 years until retirement at an annual rate of 6%, how much will she have upon retirement (round to nearest dollar)?',
                    validators=[InputRequired()])

    q3 = RadioField('(3) What are factors you should consider when deciding how to invest?',
                    choices=[('Investment Horizon', 'Investment Horizon'), ('Risk', 'Risk'), 
                            ('Ability to generate income', 'Ability to generate income'), ('All of the Above', 'All of the Above')],
                    validators=[InputRequired()])

    q4 = RadioField('(4) If you buy a company’s stock...',
                    choices=[('You own a part of the company', 'You own a part of the company'), ('You have lent money to the company', 'You have lent money to the company'), ('You are liable for the company’s debts', 'You are liable for the company’s debts'), ('The company will return your original investment to you with interest', 'The company will return your original investment to you with interest')],
                    validators=[InputRequired()])

    q5 = RadioField("(5) If you buy a company's bond…",
                    choices=[('You own a part of the company', 'You own a part of the company'), ('You have lent money to the company', 'You have lent money to the company'), ('You are liable for the company’s debts', 'You are liable for the company’s debts'), ('The company will return your original investment to you with interest', 'The company will return your original investment to you with interest')],
                    validators=[InputRequired()])

    q6 = RadioField('(6) In general, if interest rates go down, then bond prices…',
                    choices=[('Go Down', 'Go Down'), ('Go Up', 'Go Up'), ('Are Not Affected', 'Are Not Affected'), ('Not Sure', 'Not Sure')],
                    validators=[InputRequired()])

    q7 = RadioField('(7) Which is the best definition of "selling short"?',
                    choices=[('Selling shares of a stock shortly after buying it', 'Selling shares of a stock shortly after buying it'), ('Selling shares of a stock before it has reached its peak', 'Selling shares of a stock before it has reached its peak'), ('Selling shares of a stock at a loss', 'Selling shares of a stock at a loss'), ('Selling borrowed shares of a stock', 'Selling borrowed shares of a stock')],
                    validators=[InputRequired()])

    q8 = RadioField('(8) What is the relationship between risk and return?',
                    choices=[('The higher the risk, the higher the return', 'The higher the risk, the higher the return'), ('The higher the risk, the lower the return', 'The higher the risk, the lower the return'), ('The lower the risk, the higher the return', 'The lower the risk, the higher the return')],
                    validators=[InputRequired()])

    submit = SubmitField('Submit My Answers')


