from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, IntegerField, FloatField, validators, SelectField
import datetime
from datetime import datetime
from wtforms.fields.html5 import DateTimeField
from passlib.hash import sha256_crypt
# from data import Trades
from functools import wraps

app = Flask(__name__)

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'MyFlaskApp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL
mysql = MySQL(app)

# Trades = Trades()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

# register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=10)])
    username = StringField('Username', [validators.Length(min=3, max=15)])
    email = StringField('Email ID', [validators.Length(min=7, max=50)])
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        print('2')
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #cursor for MYSQL
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email_id, username,password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        mysql.connection.commit()
        cur.close()

        # flash a message on screen with status like success
        flash('You are now registered and logged in', 'success')

        return redirect(url_for('index'))
    return render_template('register.html', form = form)

# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # fetch form fields, this is different from register where we validate. Here we just grab the fields
        # so we use rquest.form and not form.name.data
        username = request.form['username']
        entered_password = request.form['password']

        # get the users and their password from the Database
        cur = mysql.connection.cursor()
        user_data = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if user_data > 0:
            #get the first result
            data = cur.fetchone()
            password = data['password']
            #compare the pass entered and the pass in db
            if sha256_crypt.verify(entered_password, password):
                app.logger.info('Pass matched')
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid password'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
        cur.close()

    return render_template('login.html')

# Check if user is logged in
def if_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauth, pls login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@if_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM trade")

    trades = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', trades=trades)
    else:
        msg = 'No trades'
        return render_template('dashboard.html', msg=msg)

    cur.close()

class TradeForm(Form):
    nominal = IntegerField('Nominal', [validators.InputRequired(message='Required input')])
    price = FloatField('Price', [validators.InputRequired(message='Required field')])
    market = StringField('Market', [validators.Length(min=1, max=4, message='Max length is 4.'), validators.InputRequired(message='Required Field')])
    cpty = StringField('Counterparty', [validators.Length(min=1, max=4, message='Max length is 4.'), validators.InputRequired(message='Required Field')])
    instrument = StringField('Instrument', [validators.Length(min=3, max=20, message='Max length is 20.'), validators.InputRequired(message='Required Field')])
    trade_date = StringField('Trade date')
    sett_date = StringField('Sett date')
    # sett_stus_ind = ['O','F','P'
    sett_stus_ind = SelectField(u'Settlement status', choices = [('O','Open'),('F','Fully Settled'),('P','Partially Settled')])
    seti_stus_ind = SelectField(u'Settlement instruction status', choices = [('O','Open'),('F','Fully Settled'),('P','Partially Settled')])
    cptystockaccount = StringField('Counterparty Stock Account', [validators.Length(min=1, max=15, message='Max length is 15.'), validators.InputRequired(message='Required Field')])
    cmpystockaccount = StringField('Company Stock Account', [validators.Length(min=1, max=15, message='Max length is 15.'), validators.InputRequired(message='Required Field')])
    # sett_stus_ind = StringField('Settlement Status', [validators.Length(min=1, max=1, message='Max length is 1.'), validators.InputRequired(message='Required Field')])
    # trade_date = datetime.datetime.strptime('Trade date', "%b %d %Y %H:%M")
    # sett_date = datetime.datetime.strptime('Sett date', "%b %d %Y %H:%M")
    # trade_date = DateTimeField('Trade date', format='%Y-%m-%d %H:%M:%S')
    # sett_date = DateTimeField('Settlement date', format='%Y-%m-%d')

@app.route('/add_trade', methods=['GET', 'POST'])
@if_logged_in
def add_trade():
    form = TradeForm(request.form)
    if request.method == 'POST' and form.validate():
        nominal = int(form.nominal.data)
        price = float(form.price.data)
        market = form.market.data
        cpty = form.cpty.data
        instrument = form.instrument.data
        seti_stus_ind = form.seti_stus_ind.data
        cmpystockaccount = form.cmpystockaccount.data
        cptystockaccount = form.cptystockaccount.data
        # trade_date = datetime.datetime.strptime(form.trade_date.data, "%b %d %Y %H:%M:%S")
        # sett_date = datetime.datetime.strptime(form.sett_date.data, "%b %d %Y %H:%M:%S")
        # This is the datetime format thats required for sql.
        trade_date = datetime.strptime(form.trade_date.data, "%Y-%m-%d")
        sett_date = datetime.strptime(form.sett_date.data, "%Y-%m-%d")
        # the format below is to get the output in a string format
        # datetime.strptime(trade_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        sett_stus_ind = form.sett_stus_ind.data
        # connect to mysql and INSERT
        cur = mysql.connection.cursor()
        #execute the cursor
        # cur.execute('INSERT INTO trade(nominal, price, cpty, market, instrument, trade_date, sett_date, sett_stus_ind) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (nominal, price, cpty, market, instrument, (trade_date.strftime('%Y-%m-%d %H:%M:%S'),), (sett_date.strftime('%Y-%m-%d %H:%M:%S'),), sett_stus_ind))
        # https://stackoverflow.com/questions/19887353/attributeerror-str-object-has-no-attribute-strftime?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        cur.execute('INSERT INTO trade(nominal, price, cpty, market, instrument, trade_date, sett_date, sett_stus_ind) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (nominal, price, cpty, market, instrument, (trade_date), (sett_date), sett_stus_ind))
        retrieved_trade_id = cur.lastrowid
        cur.execute('INSERT INTO sett_instruction(trade_id, seti_stus_ind, nominal, price, cmpystockaccount, cptystockaccount) VALUES (%s, %s, %s, %s, %s, %s)', (retrieved_trade_id, seti_stus_ind, nominal, price, cmpystockaccount, cptystockaccount))
        #commit
        mysql.connection.commit()
        #close
        cur.close()

        # TODO: this is not working
        flash('Trade entered', 'success')

        return redirect(url_for('dashboard'))
    return render_template('add_trade.html', form = form)

@app.route('/trades')
# needed to change the placement of this view here from before register view as it was giving error
# that if_logged_in is not defined
@if_logged_in
def trades():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM trade")

    trades = cur.fetchall()

    if result > 0:
        return render_template('all_trades.html', trades=trades)
    else:
        msg = 'No trades'
        return render_template('all_trades.html', msg=msg)

    cur.close()

# single trade info
@app.route('/trade/<string:id>')
def trade(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM trade WHERE trade_id = %s", [id])

    trade = cur.fetchone()

    return render_template('trade.html', trade=trade)

@app.route('/edit_trade/<string:id>', methods=['GET', 'POST'])
@if_logged_in
def edit_trade(id):

    # get trade by trade_id
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM trade WHERE trade_id = %s", [id])
    trade = cur.fetchone()

    form = TradeForm(request.form)

    # populate trade form fields
    form.nominal.data = trade['nominal']
    form.price.data = trade['price']
    form.cpty.data = trade['cpty']
    form.market.data = trade['market']
    form.instrument.data = trade['instrument']
    form.trade_date.data = trade['trade_date']
    form.sett_date.data = trade['sett_date']
    form.sett_stus_ind.data = trade['sett_stus_ind']
    # d = datetime.datetime(trade['trade_date'])
    # form.trade_date.data = d.strftime("%b %d %Y %H:%M:%S")
    # d = datetime.datetime.strptime('2011-06-09', '%Y-%m-%d')
    # d.strftime('%b %d,%Y')
    # form.trade_date.data = datetime.datetime.strptime(trade['trade_date'], '%Y-%m-%d').strftime('%b %d %Y %H:%M:%S')


    if request.method == 'POST' and form.validate():
        nominal = request.form['nominal']
        price = request.form['price']
        cpty = request.form['cpty']
        market = request.form['market']
        instrument = request.form['instrument']
        trade_date = request.form['trade_date']
        sett_date = request.form['sett_date']
        sett_stus_ind = request.form['sett_stus_ind']
        # TODO: we dont need the h m s for sett date and trade date
        # trade_date = datetime.datetime.strptime(request.form['trade_date'], "%b %d %Y %H:%M:%S")
        # sett_date = datetime.datetime.strptime(request.form['sett_date'], "%b %d %Y %H:%M:%S")

        # connect to mysql and INSERT
        cur = mysql.connection.cursor()
        #execute the cursor
        # cur.execute("UPDATE trade SET nominal=%s, price=%s, cpty=%s, market=%s, instrument=%s, trade_date=%s, sett_date=%s, sett_stus_ind=%s WHERE trade_id=%s", (nominal, price, cpty, market, instrument, (trade_date.strftime('%Y-%m-%d %H:%M:%S'),), (sett_date.strftime('%Y-%m-%d %H:%M:%S'),), sett_stus_ind, id))
        cur.execute("UPDATE trade SET nominal=%s, price=%s, cpty=%s, market=%s, instrument=%s, trade_date=%s, sett_date=%s, sett_stus_ind=%s WHERE trade_id=%s", (nominal, price, cpty, market, instrument, (datetime.strptime(trade_date, '%Y-%m-%d').strftime('%Y-%m-%d')), (datetime.strptime(sett_date, '%Y-%m-%d').strftime('%Y-%m-%d')), sett_stus_ind, id))
        #commit
        mysql.connection.commit()
        #close
        cur.close()

        # TODO: this is not working
        flash('Trade updated', 'success')

        return redirect(url_for('dashboard'))
    return render_template('edit_trade.html', form = form)

#delete trades
@app.route('/delete_trade/<string:id>', methods=['POST'])
@if_logged_in
def delete_trade(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM trade WHERE trade_id = %s", [id])
    mysql.connection.commit()
    cur.close()

    flash('Trade deleted', 'success')

    return redirect(url_for('dashboard'))

# Settlement instruction
class SetiForm(Form):
    nominal = IntegerField('Nominal', [validators.InputRequired(message='Required input')])
    price = FloatField('Price', [validators.InputRequired(message='Required field')])
    market = StringField('Market', [validators.Length(min=1, max=4, message='Max length is 4.'), validators.InputRequired(message='Required Field')])
    cpty = StringField('Counterparty', [validators.Length(min=1, max=4, message='Max length is 4.'), validators.InputRequired(message='Required Field')])
    instrument = StringField('Instrument', [validators.Length(min=3, max=20, message='Max length is 20.'), validators.InputRequired(message='Required Field')])
    trade_date = StringField('Trade date')
    sett_date = StringField('Sett date')
    # sett_stus_ind = ['O','F','P'
    sett_stus_ind = SelectField(u'Settlement status', choices = [('O','Open'),('F','Fully Settled'),('P','Partially Settled')])

# single trade info
@app.route('/trade/seti/<string:id>')
def seti(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT seti.seti_id,seti.trade_id,seti.seti_stus_ind,seti.nominal,seti.price,seti.cmpystockaccount,seti.cptystockaccount,trad.market,trad.cpty,trad.instrument FROM sett_instruction seti, trade trad WHERE seti.trade_id = %s AND seti.trade_id=trad.trade_id", [id])
    seti = cur.fetchone()
    return render_template('seti.html', seti=seti)
    cur.close()

@app.route('/summary')
def summary():
    cur = mysql.connection.cursor()
    cur2 = mysql.connection.cursor()
    # result = cur.execute("SELECT ot.c_ot, pt.c_pt, st.c_st FROM (SELECT COUNT(trade_id) AS c_ot FROM trade WHERE sett_stus_ind ='O') AS ot, (SELECT COUNT(trade_id) AS c_pt FROM trade WHERE sett_stus_ind ='P') AS pt, (SELECT COUNT(trade_id) AS c_st FROM trade WHERE sett_stus_ind ='F') AS st")
    result = cur.execute("SELECT ot.c_ot/total_trades.count_total*100 as count_open, pt.c_pt/total_trades.count_total*100 as count_partial, st.c_st/total_trades.count_total*100 as count_settled FROM (SELECT COUNT(trade_id) AS c_ot FROM trade WHERE sett_stus_ind ='O') AS ot, (SELECT COUNT(trade_id) AS c_pt FROM trade WHERE sett_stus_ind ='P') AS pt, (SELECT COUNT(trade_id) AS c_st FROM trade WHERE sett_stus_ind ='F') AS st, (SELECT COUNT(trade_id) AS count_total FROM trade WHERE sett_stus_ind ='O' OR sett_stus_ind ='P' OR sett_stus_ind ='F') AS total_trades")
    trade_stus_count = cur.fetchone()

    result2 = cur2.execute("SELECT ot.c_ot/total_trades.count_total*100 as count_open, pt.c_pt/total_trades.count_total*100 as count_partial, st.c_st/total_trades.count_total*100 as count_settled FROM (SELECT COUNT(trade_id) AS c_ot FROM trade WHERE sett_stus_ind ='O' AND DATE(entry_date) = DATE(NOW())) AS ot, (SELECT COUNT(trade_id) AS c_pt FROM trade WHERE sett_stus_ind ='P' AND DATE(entry_date) = DATE(NOW())) AS pt, (SELECT COUNT(trade_id) AS c_st FROM trade WHERE sett_stus_ind ='F' AND DATE(entry_date) = DATE(NOW())) AS st, (SELECT COUNT(trade_id) AS count_total FROM trade WHERE (sett_stus_ind ='O' OR sett_stus_ind ='P' OR sett_stus_ind ='F') AND DATE(entry_date) = DATE(NOW())) AS total_trades;")
    today_sett_stus_count = cur2.fetchone()
    # if result2 > 0:
    return render_template('summary.html', trade_stus_count=trade_stus_count, today_sett_stus_count=today_sett_stus_count )
    # else:
    #     msg = 'No trades'
    #     return render_template('summary.html', trade_stus_count=trade_stus_count, msg=msg)
    cur.close()
    cur2.close()


if __name__ == '__main__':
    app.secret_key='secret1234'
    app.run(debug=True)
