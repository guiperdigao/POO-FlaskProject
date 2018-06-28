#!/usr/bin/python

import cgi, sys
import cgitb; cgitb.enable()
import googlemaps 
from googlemaps import convert
from googlemaps.convert import as_list
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map, icons
from flask import Flask, render_template, request, session, flash, redirect, url_for, logging, make_response
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


form = cgi.FieldStorage()
print("Content-type: text/html")

gmaps = googlemaps.Client(key='AIzaSyC-jyfRJC7gRskgtLADyrOCod3EzhVYE7s')
app = Flask(__name__, template_folder="templates")
app.config['GOOGLEMAPS_KEY'] = "AIzaSyC-jyfRJC7gRskgtLADyrOCod3EzhVYE7s"
app.secret_key = "AIzaSyC-jyfRJC7gRskgtLADyrOCod3EzhVYE7s"
GoogleMaps(app, key="AIzaSyC-jyfRJC7gRskgtLADyrOCod3EzhVYE7s")

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'triptipz'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/paper-plane.png')
def root():
    return app.send_static_file('paper-plane.png')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        return redirect(url_for('login'))
    return render_template('signin.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('plan'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/plan')
@is_logged_in
def plan():
    return render_template('index.html')

@app.route('/result', methods = ['POST','GET'])
@is_logged_in
def need_input():
    if request.method == 'POST':
        form = request.form

    data = {}
    for field in ('nome', 'origin', 'destination1', 'destination2', 'destination3', 'destination4', 'destination5','transporte'):
        if not field in request.form:
            data[field] = "(unknown)"
        else:
                data[field] = request.form[field]
    if data['transporte'] == "":
       data['transporte'] = "driving"
    origem=[]
    destinos=[]
    for field in ('origin', 'destination1', 'destination2', 'destination3', 'destination4', 'destination5'):
        if data[field] != "":
            origem.append(data[field])
            destinos.append(data[field])

    coord1 = gmaps.geocode(data['origin'])
    distancia = gmaps.distance_matrix(origem,destinos,data['transporte'])
    for i in range(len(origem)):
        for j in range(len(origem)):
            if 'ZERO_RESULTS' == distancia['rows'][i]['elements'][j]['status']:
                return render_template('no_routes.html')
    ## Distância local i para local j:  distancia['rows'][i]['elements'][j]['distance']['value']
    ## Tempo local i para local j:  distancia['rows'][i]['elements'][j]['duration']['value']

    ### Calcula a árvore de custo mínimo:
    def Prim():
        pr = [10000000000]*len(origem)
        frg = [0]*len(origem)
        pa = [-1]*(len(origem)+1)
        pa[0] = 0

        for n in range(len(origem)):
            pr[n] = distancia['rows'][0]['elements'][n]['distance']['value']
    
        while (True):
            min = 10000000000
            for w in range(len(origem)):
                if pa[w] == -1 and pr[w] < min:
                    min = pr[w]
                    y = w
            if min == 10000000000:
                break
            pa[y] = frg[y]
            for a in range(len(origem)-1):
                if pa[a] == -1 and distancia['rows'][y]['elements'][a]['distance']['value'] < pr[a]:
                    pr[a] = distancia['rows'][y]['elements'][a]['distance']['value']
                    frg[a] = y
        return pa

    C = [0]*len(origem)
    T = Prim()
    T[len(origem)] = 0

    ### Calcula a melhor rota para passeio:
    def Preordem(v):
        C[T[len(origem)]] = v
        T[len(origem)] = T[len(origem)]+1
        for i in range(len(origem)):
            if T[i] == v and i != v:
                Preordem(i)

    Preordem(0)

    ### Calcula a distancia do ciclo:
    dist = 0
    for i in range(len(origem)):
        if i != len(origem)-1:
            dist = dist + distancia['rows'][C[i]]['elements'][C[i+1]]['distance']['value']
        else: dist = dist + distancia['rows'][C[len(origem)-1]]['elements'][0]['distance']['value']



    ### Calcula coordenadas dos locais no mapa:
    coord1 = gmaps.geocode(data['origin'])
    coord = [(coord1[0]['geometry']['location']['lat'],coord1[0]['geometry']['location']['lng'])]

    for n in range(1,len(origem)):
        if C[n] == 1:
            coord1 = gmaps.geocode(data['destination1'])
            coord.append((coord1[0]['geometry']['location']['lat'],coord1[0]['geometry']['location']['lng']))
        elif C[n] == 2:
            coord1 = gmaps.geocode(data['destination2'])
            coord.append((coord1[0]['geometry']['location']['lat'],coord1[0]['geometry']['location']['lng']))
        elif C[n] == 3:
            coord1 = gmaps.geocode(data['destination3'])
            coord.append((coord1[0]['geometry']['location']['lat'],coord1[0]['geometry']['location']['lng']))
        elif C[n] == 4:
            coord1 = gmaps.geocode(data['destination4'])
            coord.append((coord1[0]['geometry']['location']['lat'],coord1[0]['geometry']['location']['lng']))
        elif C[n] == 5:
            coord1 = gmaps.geocode(data['destination5'])
            coord.append((coord1[0]['geometry']['location']['lat'],coord1[0]['geometry']['location']['lng']))

    ### Coordenadas centrais do mapa
    lat_o, lng_o = coord[0]

    ### Coordenadas dos marcadores:
    marcadores = [{
                   'icon': icons.dots.blue,
                   'lat': lat_o,
                   'lng': lng_o,
                   'infobox': "Seu ponto de saída!"
                 }]

    for i in range(1,len(origem)):
        lat_i, lng_i = coord[i]
        if i == 1:
            marcadores.append({
                'icon': icons.alpha.A,
                'lat': lat_i,
                'lng': lng_i,
                'infobox': ""})
        elif i == 2:
            marcadores.append({
                'icon': icons.alpha.B,
                'lat': lat_i,
                'lng': lng_i,
                'infobox': ""})
        elif i == 3:
            marcadores.append({
                'icon': icons.alpha.C,
                'lat': lat_i,
                'lng': lng_i,
                'infobox': ""})
        elif i == 4:
            marcadores.append({
                'icon': icons.alpha.D,
                'lat': lat_i,
                'lng': lng_i,
                'infobox': ""})
        elif i == 5:
            marcadores.append({
                'icon': icons.alpha.E,
                'lat': lat_i,
                'lng': lng_i,
                'infobox': ""})
    ### Define e imprime o mapa:
    trdmap = Map(
        identifier="trdmap",
        varname="trdmap",
        lat= lat_o,
        lng= lng_o,
        markers=marcadores
    )
    return render_template('route.html',trdmap=trdmap, dist = dist/1000, nome = data['nome'])


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)