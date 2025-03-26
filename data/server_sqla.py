#!/usr/bin/python3 
# -*- coding:utf-8 -*- 

#################
# AFaire :
# Completer les trous listés dans ce fichier
# Attention, ceci peut entrainer l'édition de templates, de fichiers javascript, css

from flask import Flask, request, render_template_string, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename   
import sqlalchemy
from sqlalchemy.orm import sessionmaker
import traceback
import requests
import os


app = Flask(__name__) 

# pour les sessions
app.secret_key = 'ItShouldBeAnythingButSecret'     #you can set any secret key but remember it should be secret

# pour des session qui n'expire pas 
#session.permanent = True

# apache server must run !
url_base = 'http://localhost/PHP-FNUC/'
path_doc = 'D:/tools/xampp-7.2.15-0-VC15-x64/htdocs/PHP-FNUC/'
max_upload_size = 16 * 1024 * 1024
mode_admin = False
mode_echo = True
# SQLAlchemy without Flask-SQLAlchemy
engine = sqlalchemy.create_engine("mysql://python:python@localhost:3312/fnuc_simple_sqla_python", echo=mode_echo)
db_server='mysql'
connection = engine.connect()

# ordonner la reflexion de toutes les tables
metadata = sqlalchemy.MetaData()
# la reflexion d'une vue ne marche pas avec mysql
#metadata.reflect(bind=engine, views=True)
metadata.reflect(bind=engine)

#Connaitre le dialect donc le SGBDR connecte au moteur sqla
Session = sessionmaker(bind=engine)
session_sqla = Session()
db=session_sqla.bind.dialect.name


@app.route('/', methods=['GET']) 
@app.route('/login' , methods=['GET']) 
def loginForm(): return render_template_string("""<!DOCTYPE html> 
<html><head><title>Login screen</title></head> 
<body style="text-align: center"><h1>Login screen</h1>
<form method="post" action="{{url_for('loginChecks')}}">
Login : 
<input name="txtLogin" autofocus /><br/> 
Password :
<input name="txtPassword" type="password" /><br> 
<br/> 
<input type="submit" value="Connecter" /> 
</form> 
</body></html>""") 

@app.route('/login' , methods=['POST'])  
def loginChecks(): 
   login=request.form.get("txtLogin") 
   password=request.form.get("txtPassword")    
   clients_table = metadata.tables["clients"]
   userRow=connection.execute(sqlalchemy.select([clients_table.c.id, clients_table.c.nom, clients_table.c.motdepasse]).where((clients_table.c.nom==login) & (clients_table.c.motdepasse==password))).fetchone() 
   if userRow is None: 
     return redirect(url_for("loginForm"))
   session['userid'] = userRow[0]     
   session['userfname'] = userRow[2]
   session['userlname'] = userRow[1]
   if userRow[0]==1:
     session['usertype'] ='admin'
   else:
     session['usertype'] ='user'
   return redirect(url_for("showAllTopics"))

@app.route('/logout')
def logout():
   session.pop('userid', None)
   session.pop('userfname', None)
   session.pop('userlname', None)
   session.pop('usertype', None)
   return redirect(url_for('showAllTopics'))

@app.route('/' , methods=['GET'])      
@app.route('/showalltopics' , methods=['GET'])   
def showAllTopics():
    mode_admin = False
    sujets_table = metadata.tables["sujets"]
    sujetsList=connection.execute(sqlalchemy.select([sujets_table])).fetchall()
    return render_template("showalltopics.html", db = db, url_base=url_base, mode_admin=mode_admin, topics = sujetsList)       

@app.route('/search' , methods=['GET'])   
def searchForm():
    motscles_table = metadata.tables["motscles"]
    motsclesList=connection.execute(sqlalchemy.select([motscles_table])).fetchall()
    return render_template("search.html", db = db, url_base=url_base, keywords=motsclesList)

@app.route('/search' , methods=['POST'])   
def searchProcess():
    if request.form['validation'] == 'Rechercher':
        # la méthode getlist renvoie un tableau des valeurs des cases cochées
        motsclesList = request.form.getlist("keywords")
        operation=request.form.get('operator')
        livres_motscles_table = metadata.tables["livres_motscles"]
        livres_table = metadata.tables["livres"]
        motscles_table = metadata.tables["motscles"]
        if operation=='union':
            referenceList = connection.execute(
                        sqlalchemy.select([livres_table]).distinct().select_from(livres_table.join(livres_motscles_table,
                        livres_table.c.id == livres_motscles_table.c.book_id).join(motscles_table,
                        motscles_table.c.id == livres_motscles_table.c.keyword_id)).where(
                        motscles_table.c.libelle.in_(motsclesList)
                )        
            ).fetchall()
        elif operation == 'except':
            referenceList = connection.execute(
                        sqlalchemy.select([livres_table]).distinct().select_from(livres_table.join(livres_motscles_table,
                        livres_table.c.id == livres_motscles_table.c.book_id).join(motscles_table,
                        motscles_table.c.id == livres_motscles_table.c.keyword_id)).where(
                        motscles_table.c.libelle.notin_(motsclesList)
                )        
            ).fetchall()
        else:
            r=sqlalchemy.select([livres_table])
            if db=='mysql' or db=='sqlite' :
                r="SELECT id,titre FROM livres WHERE 1 "
            # SELECT id,titre 
            # FROM livres 
            # WHERE EXISTS(SELECT libelle FROM livres_motscles INNER JOIN motscles ON livres_motscles.keyword_id=motscles.id WHERE livres.id=livres_motscles.book_id AND libelle='Java') 
            # AND EXISTS(SELECT libelle FROM livres_motscles INNER JOIN motscles ON livres_motscles.keyword_id=motscles.id WHERE livres.id=livres_motscles.book_id AND libelle='Programmation') 
            # AND EXISTS(SELECT libelle FROM livres_motscles INNER JOIN motscles ON livres_motscles.keyword_id=motscles.id WHERE livres.id=livres_motscles.book_id AND libelle='Internet')
                for mot in motsclesList:
                    #mysql no support INTERSECT
                    r=r + "AND EXISTS(SELECT libelle FROM livres_motscles INNER JOIN motscles ON livres_motscles.keyword_id=motscles.id WHERE livres.id=livres_motscles.book_id AND libelle='%s') "%(mot)
                referenceList = connection.execute(r).fetchall()                            
            else:
            
                for mot in motsclesList:
                    # mysql no support INTERSECT but Oracle does, PostgreSQL does, recent SQLite does and MariaDB does as of version 10.3
                    # Since 10 November 2022, MySQL has added support to the INTERSECT and EXCEPT operators with the updates of version 8.0.31.
                    r=sqlalchemy.intersect(r,
                            sqlalchemy.select([livres_table]).select_from(livres_table.join(livres_motscles_table,
                            livres_table.c.id == livres_motscles_table.c.book_id).join(motscles_table,
                            motscles_table.c.id == livres_motscles_table.c.keyword_id)).where(
                            motscles_table.c.libelle==mot))                    
                referenceList = connection.execute(r).fetchall()

            
    return render_template("searchresult.html", db = db, url_base=url_base, operation=operation, keywords=motsclesList, books=referenceList)    
    
@app.route('/showbookreferenceoftopic' , methods=['GET'])   
def showBookReferenceOfTopic():
    livres_sujets_table = metadata.tables["livres_sujets"]
    livres_table = metadata.tables["livres"]
    sujets_table = metadata.tables["sujets"]
    sujet_id=request.args['id']
    sujetRow=connection.execute(sqlalchemy.select([sujets_table.c.libelle, sujets_table.c.sujet_url]).where(sujets_table.c.id==sujet_id )).fetchone() 
    referenceList = connection.execute(
                sqlalchemy.select([livres_table]).select_from(livres_table.join(livres_sujets_table,
                livres_table.c.id == livres_sujets_table.c.book_id)).where(
             livres_sujets_table.c.topic_id == sujet_id
        )        
    ).fetchall()
    return render_template("showbookreferenceoftopic.html", db = db, url_base=url_base, mode_admin=mode_admin, topic=sujetRow, books =referenceList)       

@app.route('/showbook' , methods=['GET'])   
def showBook():
    #################
    # AFaire :
    # Afficher les informations sur le livre
    # Attention, ceci peut entrainer l'édition de templates, de fichiers javascript, css
    livres_table = metadata.tables["livres"]
    book_id = request.args['bookId']
    parametres = metadata.tables['parametres']

    bookinfoList = connection.execute(
                sqlalchemy.select([livres_table]).select_from(livres_table).where(livres_table.c.id == book_id)
    ).fetchall()[0]

    param = connection.execute(
                sqlalchemy.select([parametres.c.taux_tva]).where(parametres.c.id == 1)
    ).fetchall()[0]

    book = {
    'id' : bookinfoList[0],
    'titre' : bookinfoList[1],
    'auteurs' : bookinfoList[2],
    'resume_url' : bookinfoList[3],
    'prix' : bookinfoList[5],
    'couverture_url' : bookinfoList[4]
    }

    URL_BASE = url_base
    resume = requests.get(URL_BASE + str(book['resume_url']))
    if resume.status_code == 200 :
        htmlSource = resume.text
    else :
        htmlSource = "ERROR : Il n'y a pas de description pour cet ouvrage"
    

    book_taux_tva = param[0]*100

    return render_template("showbook.html", db = db, url_base=url_base, mode_admin=mode_admin, book=book, book_taux_tva = book_taux_tva, htmlSource = htmlSource)

@app.route('/viewProfile' , methods=['GET'])
def viewProfile():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    clients_table = metadata.tables["clients"]
    userRow=connection.execute(sqlalchemy.select([clients_table]).where(clients_table.c.id==session['userid'])).fetchone()
    # use of view => standart SQL not SQL Expression Language de SQLalchemy Core 
    r="SELECT article,titre,SUM(nbcommandes) AS quantite  FROM commandes_article_client WHERE client="+str(session['userid'])+" GROUP BY article,titre ORDER BY article"
    dataList = connection.execute(r).fetchall()
    dataString = "["
    for data in dataList:
        # modify Decimal(1) in 1
        quantite=int(data.quantite)
        dataString=dataString+'{titre: "'+data.titre+'", quantité:'+str(quantite)+'},'
    dataString = dataString+"]"    
    return render_template("viewprofile.html", db = db, url_base=url_base, mode_admin=mode_admin, user=userRow, data=dataString)
    
@app.route('/orderbook' , methods=['GET'])
def orderBookForm():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    #################
    # AFaire :
    # Afficher les informations sur le livre et proposer le formulaire de commandes
    # Attention, ceci peut entrainer l'édition de templates, de fichiers javascript, css  
    livres_table = metadata.tables["livres"]
    book_id = request.args['bookId']
    parametres = metadata.tables['parametres']

    bookinfoList = connection.execute(
                sqlalchemy.select([livres_table]).select_from(livres_table).where(livres_table.c.id == book_id)
    ).fetchall()[0]

    param = connection.execute(
                sqlalchemy.select([parametres.c.taux_tva]).where(parametres.c.id == 1)
    ).fetchall()[0]

    book = {
    'id' : bookinfoList[0],
    'titre' : bookinfoList[1],
    'auteurs' : bookinfoList[2],
    'resume_url' : bookinfoList[3],
    'prix' : bookinfoList[5],
    'couverture_url' : bookinfoList[4]
    }

    URL_BASE = url_base
    resume = requests.get(URL_BASE + str(book['resume_url']))
    if resume.status_code == 200 :
        htmlSource = resume.text
    else :
        htmlSource = "ERROR : Il n'y a pas de description pour cet ouvrage"
    

    book_taux_tva = param[0]*100

    return render_template("orderbook.html", db = db, url_base=url_base, mode_admin=mode_admin, book=book, book_taux_tva = book_taux_tva, htmlSource = htmlSource) 

@app.route('/orderbook' , methods=['POST'])
def orderBook():
    import datetime
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    message = ''
    error = False

    #################
    # AFaire :
    # Traiter le formulaire de commandes
    # Attention, ceci peut entrainer l'édition de templates, de fichiers javascript, css

    livres_table = metadata.tables["livres"]
    commandes = metadata.tables["commandes"]
    book_id = request.form.get('bookId')
    parametres = metadata.tables['parametres']

    quantite_ach = request.form.get('quantity')
    stock = metadata.tables['stocks']

    quantite_stock = connection.execute(
                sqlalchemy.select([stock]).select_from(stock).where(stock.c.article == book_id)
    ).fetchall()[0] 

    bookinfoList = connection.execute(
                sqlalchemy.select([livres_table]).select_from(livres_table).where(livres_table.c.id == book_id)
    ).fetchall()[0]

    param = connection.execute(
                sqlalchemy.select([parametres.c.taux_tva]).where(parametres.c.id == 1)
    ).fetchall()[0]

    book = {
    'id' : bookinfoList[0],
    'titre' : bookinfoList[1],
    'auteurs' : bookinfoList[2],
    'resume_url' : bookinfoList[3],
    'prix' : bookinfoList[5],
    'couverture_url' : bookinfoList[4],
    'stock_secu' : quantite_stock[3],
    'stock_tot' : quantite_stock[2]
    }
    try:
        if book['stock_tot']-book['stock_secu'] >= int(quantite_ach):

            error = False
            restant = book['stock_tot']-int(quantite_ach)

            connection.execute(
                commandes.insert().values(datecom=datetime.datetime.now(), article=book_id, client=session['userid'], quantite=quantite_ach)
                ) 
            
            connection.execute(
                stock.update().where(stock.c.article == book_id).values(niveau=restant)
                )
            
            connection.begin().commit()
            message = "Merci pour votre commande :)"
        else  :
            error = True
            message = str("ERREUR : Il n'y a pas assez de livre disponnible " + str(book['stock_tot']-book['stock_secu']) + " " + str(quantite_ach))
    except BaseException as e:
        message = str("ERREUR : Il n'y a pas assez de livre disponnible " + str(e))
        error = True
        connection.begin().rollback()


    URL_BASE = url_base
    resume = requests.get(URL_BASE + str(book['resume_url']))
    if resume.status_code == 200 :
        htmlSource = resume.text
    else :
        htmlSource = "ERROR : Il n'y a pas de description pour cet ouvrage"
    

    book_taux_tva = param[0]*100
    

    if error:
        return render_template("orderbook_error.html", db = db, url_base=url_base, mode_admin=mode_admin, book=book, htmlSource=htmlSource, message=message) 
    else:
        return render_template("orderbook_done.html", db = db, url_base=url_base, mode_admin=mode_admin, book=book, htmlSource=htmlSource, message=message) 
    
@app.route('/admin' , methods=['GET'])   
def adminBooks():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    mode_admin = True        
    # pas de reflexion sur les vue => pas de SQL Expression
    # livres_table = metadata.tables["livres"]
    # livres_sujets_motscles_table = metadata.tables["livres_sujets_motscles"]
    # livreList = connection.execute(
                # sqlalchemy.select([livres_table]).select_from(livres_table.join(livres_sujets_motscles_table,
                # livres_table.c.id == livres_sujets_motscles_table.c.id))
    # ).fetchall()
    # plain SQL
    # on utilise la vue pour eviter du SQL specifique a MySQL, Oracle, PostgreSQL
    # les livres peuvent ne pas avoir de mots-cles ou de sujet => LEFT JOIN
    livreList = connection.execute("""SELECT livres.id,titre,auteurs,prix,resume_url,couverture_url,niveau, securite, rayons, motscles 
FROM livres 
INNER JOIN stocks
ON stocks.article=livres.id
LEFT JOIN livres_sujets_motscles
ON livres.id=livres_sujets_motscles.id
ORDER BY livres.id""").fetchall()
    return render_template("admin.html", db = db, url_base=url_base, mode_admin=mode_admin, books=livreList)   

@app.route('/admin_book_add' , methods=['GET'])   
def adminBookAdd():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics")) 
    return render_template("admin_book_add.html", db = db, url_base=url_base, mode_admin=mode_admin)  

@app.route('/admin_book_add' , methods=['POST'])   
def adminBookAddProcess():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    livre_titre = request.form.get('title')
    livre_auteurs = request.form.get('authors')
    livre_prix = request.form.get('price')
    livre_resumeurl = request.form.get('summaryurl')
    livre_couvertureurl = request.form.get('coverurl')
    stock_niveau = request.form.get('inventorylevel')
    stock_securite = request.form.get('securitylevel')
    transaction = connection.begin()
    error=False
    try:
        # execute 1st statement
        r=connection.execute(livres_table.insert().values(titre=livre_titre, auteurs=livre_auteurs, prix=livre_prix, resume_url=livre_resumeurl, couverture_url=livre_couvertureurl))
        livre_id = r.lastrowid
        # execute 2nd statement
        r=connection.execute(stocks_table.insert().values(id=livre_id, article=livre_id, niveau=stock_niveau, securite=stock_securite))
        # commit the transaction
        transaction.commit()
        message = 'Le nouvel ouvrage et son stock sont enregistres !'
    except:
        message = 'Le nouvel ouvrage et son stock non enregistres suite à un probleme avec la base de donnees ! trace='+traceback.format_exc()
        error = True
        transaction.rollback()
    if error:
        return render_template("admin_message_error.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Ajouter un nouveau livre au catalogue", message=message) 
    else:
        return render_template("admin_message_done.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Ajouter un nouveau livre au catalogue", message=message) 


@app.route('/admin_book_update' , methods=['GET'])   
def adminBookUpdate():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics")) 
    id = request.args['id']
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    livreRow = connection.execute(sqlalchemy.select([livres_table.c.id, livres_table.c.titre, livres_table.c.auteurs, livres_table.c.resume_url, livres_table.c.couverture_url, livres_table.c.prix, stocks_table.c.niveau, stocks_table.c.securite]).select_from(livres_table.join(stocks_table,
                livres_table.c.id == stocks_table.c.article)).where(
             livres_table.c.id == id
        )).fetchone()    
    return render_template("admin_book_update.html", db = db, url_base=url_base, mode_admin=mode_admin, book=livreRow)  

@app.route('/admin_book_update' , methods=['POST'])   
def adminBookUpdateProcess():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    livre_id = request.form.get('id')
    livre_titre = request.form.get('title')
    livre_auteurs = request.form.get('authors')
    livre_prix = request.form.get('price')
    livre_resumeurl = request.form.get('summaryurl')
    livre_couvertureurl = request.form.get('coverurl')
    stock_niveau = request.form.get('inventorylevel')
    stock_securite = request.form.get('securitylevel')
    transaction = connection.begin()
    error=False
    try:
        # execute 1st statement
        r=connection.execute(livres_table.update().values(titre=livre_titre, auteurs=livre_auteurs, prix=livre_prix, resume_url=livre_resumeurl, couverture_url=livre_couvertureurl).where(livres_table.c.id==livre_id))
        # execute 2nd statement
        r=connection.execute(stocks_table.update().values(niveau=stock_niveau, securite=stock_securite).where(stocks_table.c.article==livre_id))
        # commit the transaction
        transaction.commit()
        message = "L'ouvrage et son stock sont enregistres !"
    except:
        message = "L'ouvrage et son stock non enregistres suite à un probleme avec la base de donnees ! trace="+traceback.format_exc()
        error = True
        transaction.rollback()
    if error:
        return render_template("admin_message_error.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Modifier un livre du catalogue", message=message) 
    else:
        return render_template("admin_message_done.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Modifier un livre du catalogue", message=message) 

@app.route('/admin_book_delete' , methods=['GET'])   
def adminBookDelete():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    id = request.args['id']
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    livreRow = connection.execute(sqlalchemy.select([livres_table.c.id, livres_table.c.titre, livres_table.c.auteurs, livres_table.c.resume_url, livres_table.c.couverture_url, livres_table.c.prix, stocks_table.c.niveau, stocks_table.c.securite]).select_from(livres_table.join(stocks_table,
                livres_table.c.id == stocks_table.c.article)).where(
             livres_table.c.id == id
        )).fetchone()    
        
    return render_template("admin_book_delete.html", db = db, url_base=url_base, mode_admin=mode_admin, book=livreRow)  

@app.route('/admin_book_delete' , methods=['POST'])   
def adminBookDeleteProcess():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    commandes_table = metadata.tables["commandes"]
    livres_motscles_table = metadata.tables["livres_motscles"]
    livres_sujets_table = metadata.tables["livres_sujets"]    
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    livre_id = request.form.get('id')
    transaction = connection.begin()
    error=False
    try:
        # execute 1st statement
        r=connection.execute(sqlalchemy.delete(commandes_table).where(commandes_table.c.article == livre_id))
        # execute 2nd statement
        r=connection.execute(sqlalchemy.delete(livres_motscles_table).where(livres_motscles_table.c.book_id == livre_id))
        # execute 3rd statement
        r=connection.execute(sqlalchemy.delete(livres_sujets_table).where(livres_sujets_table.c.book_id == livre_id))
        # execute 4th statement
        r=connection.execute(sqlalchemy.delete(stocks_table).where(stocks_table.c.article == livre_id))
        # execute 5th statement
        r=connection.execute(sqlalchemy.delete(livres_table).where(livres_table.c.id == livre_id))
        # commit the transaction
        transaction.commit()
        message = "L'ouvrage et son stock sont supprimés !"
    except:
        message = "L'ouvrage et son stock non supprméss suite à un probleme avec la base de données ! trace="+traceback.format_exc()
        error = True
        transaction.rollback()
    if error:
        return render_template("admin_message_error.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Supprimer un livre du catalogue", message=message) 
    else:
        return render_template("admin_message_done.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Supprimer un livre du catalogue", message=message) 

@app.route('/admin_book_topics' , methods=['GET'])   
def adminBookTopics():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics")) 
    id = request.args['id']
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    livreRow = connection.execute(sqlalchemy.select([livres_table.c.id, livres_table.c.titre, livres_table.c.auteurs, livres_table.c.resume_url, livres_table.c.couverture_url, livres_table.c.prix, stocks_table.c.niveau, stocks_table.c.securite]).select_from(livres_table.join(stocks_table,
                livres_table.c.id == stocks_table.c.article)).where(
             livres_table.c.id == id
        )).fetchone()
    sujets_table = metadata.tables["sujets"]
    sujetsList=connection.execute(sqlalchemy.select([sujets_table])).fetchall()
    livres_sujets_table = metadata.tables["livres_sujets"]
    topic_idList = connection.execute(
                sqlalchemy.select([livres_sujets_table.c.topic_id]).where(livres_sujets_table.c.book_id==id)
    ).fetchall()
    topic_ids=[]
    for livres_topics in topic_idList:
        topic_ids.append(livres_topics.topic_id)
    precheckArray=[]
    for sujet in sujetsList:
        value=False
        if sujet.id in topic_ids:
            value=True
        precheckArray.append(value)
    return render_template("admin_book_topics.html", db = db, url_base=url_base, mode_admin=mode_admin, book=livreRow, topics=sujetsList, precheckArray=precheckArray)  

@app.route('/admin_book_topics' , methods=['POST'])   
def adminBookTopicsProcess():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    livres_sujets_table = metadata.tables["livres_sujets"]
    livre_id = request.form.get('id')
    index_topics = request.form.getlist("index_topics")
    transaction = connection.begin()
    error=False
    try:
        # execute 1st statement
        r=connection.execute(sqlalchemy.delete(livres_sujets_table).where(livres_sujets_table.c.book_id == livre_id))
        for topic_id in index_topics:
            r=connection.execute(livres_sujets_table.insert().values(book_id=livre_id, topic_id=topic_id))
        # commit the transaction
        transaction.commit()
        message = "Les rayons sont affectés au livre !"
    except:
        message = "Les rayons non affectés suite à un probleme avec la base de données ! trace="+traceback.format_exc()
        error = True
        transaction.rollback()
    if error:
        return render_template("admin_message_error.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Affecter les rayons à un livre du catalogue", message=message) 
    else:
        return render_template("admin_message_done.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Affecter les rayons à un livre du catalogue", message=message) 
        
@app.route('/admin_book_keywords' , methods=['GET'])   
def adminBookKeywords():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics")) 
    id = request.args['id']
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    livreRow = connection.execute(sqlalchemy.select([livres_table.c.id, livres_table.c.titre, livres_table.c.auteurs, livres_table.c.resume_url, livres_table.c.couverture_url, livres_table.c.prix, stocks_table.c.niveau, stocks_table.c.securite]).select_from(livres_table.join(stocks_table,
                livres_table.c.id == stocks_table.c.article)).where(
             livres_table.c.id == id
        )).fetchone()
    motscles_table = metadata.tables["motscles"]
    motsclesList=connection.execute(sqlalchemy.select([motscles_table])).fetchall()
    livres_motscles_table = metadata.tables["livres_motscles"]
    keyword_idList = connection.execute(
                sqlalchemy.select([livres_motscles_table.c.keyword_id]).where(livres_motscles_table.c.book_id==id)
    ).fetchall()
    keyword_ids=[]
    for livres_keywords in keyword_idList:
        keyword_ids.append(livres_keywords.keyword_id)
    precheckArray=[]
    for motcle in motsclesList:
        value=False
        if motcle.id in keyword_ids:
            value=True
        precheckArray.append(value)
    return render_template("admin_book_keywords.html", db = db, url_base=url_base, mode_admin=mode_admin, book=livreRow, keywords=motsclesList, precheckArray=precheckArray)  
 
@app.route('/admin_book_keywords' , methods=['POST'])   
def adminBookKeywordsProcess():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    livres_motscles_table = metadata.tables["livres_motscles"]
    livre_id = request.form.get('id')
    index_keywords = request.form.getlist("index_keywords")
    transaction = connection.begin()
    error=False
    try:
        # execute 1st statement
        r=connection.execute(sqlalchemy.delete(livres_motscles_table).where(livres_motscles_table.c.book_id == livre_id))
        for keyword_id in index_keywords:
            r=connection.execute(livres_motscles_table.insert().values(book_id=livre_id, keyword_id=keyword_id))
        # commit the transaction
        transaction.commit()
        message = "Les mots clef sont affectés au livre !"
    except:
        message = "Les mots clef non affectés suite à un probleme avec la base de données ! trace="+traceback.format_exc()
        error = True
        transaction.rollback()
    if error:
        return render_template("admin_message_error.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Affecter les mots clef à un livre du catalogue", message=message) 
    else:
        return render_template("admin_message_done.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Affecter les mots clef à un livre du catalogue", message=message) 
    
    
@app.route('/admin_keywords' , methods=['GET'])   
def adminKeywords():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics")) 
    return render_template("admin.html", db = db, url_base=url_base, mode_admin=mode_admin)   

@app.route('/admin_topics' , methods=['GET'])   
def adminTopics():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics")) 
    return render_template("admin_topics.html", db = db, url_base=url_base, mode_admin=mode_admin)   

@app.route('/admin_customers' , methods=['GET'])   
def adminCustomers():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    clients_table = metadata.tables["clients"]
    clientList=connection.execute(sqlalchemy.select([clients_table])).fetchall()         
    return render_template("admin_customers.html", db = db, url_base=url_base, mode_admin=mode_admin, customers=clientList)   

@app.route('/admin_customer_add' , methods=['GET'])   
def adminCustomerAdd():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics")) 
    return render_template("admin_customers_add.html", db = db, url_base=url_base, mode_admin=mode_admin) 

@app.route('/admin_customer_update' , methods=['GET'])   
def adminCustomerUpdate():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    id = request.args['id']    
    clients_table = metadata.tables["clients"]
    clientRow=connection.execute(sqlalchemy.select([clients_table]).where(clients_table.c.id==id)).fetchone()  
    return render_template("admin_customers_update.html", db = db, url_base=url_base, mode_admin=mode_admin) 

@app.route('/admin_customer_delete' , methods=['GET'])   
def adminCustomerDelete():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics")) 
    return render_template("admin_customer_delete.html", db = db, url_base=url_base, mode_admin=mode_admin) 
 
@app.route('/admin_parameter' , methods=['GET'])   
def adminParameter():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    parametres_table = metadata.tables["parametres"]
    parametreList=connection.execute(sqlalchemy.select([parametres_table]).where(parametres_table.c.id==1)).fetchall() 
    app_parametreList=[{"url_root": "{}".format(request.url_root),"url_base":"{}".format(url_base), "path_doc":"{}".format(path_doc), "max_size":"{}".format(max_upload_size), "dialect":"{}".format(db), "mode_echo":"{}".format(mode_echo)}]
    return render_template("admin_parameter.html", db = db, url_base=url_base, mode_admin=mode_admin, parameters=parametreList, app_parameters=app_parametreList)   

@app.route('/admin_parameter_add' , methods=['GET'])   
def adminParameterAdd():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics")) 
    return render_template("admin_parameter_add.html", db = db, url_base=url_base, mode_admin=mode_admin)  

@app.route('/admin_parameter_add' , methods=['POST'])   
def adminParameterAddProcess():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    parametres_table = metadata.tables["parametres"]
    taux_tva = request.form.get('vat_rate')
    logo_url = request.form.get('logo_url')
    error=False
    try:
        r=connection.execute(parametres_table.insert().values(id=1, logo_url=logo_url, taux_tva=taux_tva))
        message = 'Les nouveaux paramètres en base de données sont enregistrés !'
    except:
        message = 'Les nouveaux paramètres en base de données non enregistrés suite à un probleme avec la base de donnees ! trace='+traceback.format_exc()
        error = True
    if error:
        return render_template("admin_message_error.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Ajouter les paramètres en base de données", message=message) 
    else:
        return render_template("admin_message_done.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Ajouter les paramètres en base de données", message=message) 


@app.route('/admin_parameter_update' , methods=['GET'])   
def adminParameterUpdate():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    parametres_table = metadata.tables["parametres"]
    parametreRow=connection.execute(sqlalchemy.select([parametres_table]).where(parametres_table.c.id==1)).fetchone()   
    app_parametreRow={"url_root": "{}".format(request.url_root),"url_base":"{}".format(url_base), "path_doc":"{}".format(path_doc), "max_size":"{}".format(max_upload_size), "dialect":"{}".format(db), "mode_echo":"{}".format(mode_echo)}    
    return render_template("admin_parameter_update.html", db = db, url_base=url_base, mode_admin=mode_admin, parameter=parametreRow, app_parameter=app_parametreRow, db_server=db_server, mode_echo=mode_echo)  

@app.route('/admin_parameter_update' , methods=['POST'])   
def adminParameterUpdateProcess():
    global url_base, path_doc, max_upload_size, db_server, db, connection, engine, metadata, mode_echo
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    parametres_table = metadata.tables["parametres"]
    taux_tva = request.form.get('vat_rate')
    logo_url = request.form.get('logo_url')
    parametre_id = request.form.get('parameterId')
    error=False
    db_changed=False
    try:
        mode_echo_value = False
        if request.form.get('mode_echo') == 'True':
            mode_echo_value = True
        if url_base!=request.form.get('url_base'):
            url_base = request.form.get('url_base')
        if path_doc!=request.form.get('path_doc'):
            path_doc = request.form.get('path_doc')
        if max_upload_size!=int(request.form.get('max_size')):
            max_upload_size = int(request.form.get('max_size'))
        if mode_echo!=mode_echo_value:
            mode_echo = mode_echo_value
        if db_server!=request.form.get('db_server'):
            db_server=request.form.get('db_server')
            db_changed=True
            connection.close()
            if db_server=='mysql':
                engine = sqlalchemy.create_engine("mysql://python:python@localhost:3312/fnuc_simple_sqla_python", echo=mode_echo)
            elif db_server=='sqlite':
                # for Linux
                # basedir = os.path.abspath(os.path.dirname(__file__))
                # engine = sqlalchemy.create_engine('sqlite:///' + os.path.join(basedir, 'fnuc_simple_lowercase.sqlite'), echo=mode_echo)
                engine = sqlalchemy.create_engine('sqlite:///D:\\tools\\WinPython-64bit-3.5.3.1Qt5\\python-3.5.3.amd64\\projects\\fnuc_flask_sqla\\fnuc_simple_lowercase.sqlite?check_same_thread=False', echo=mode_echo)
                #engine = sqlalchemy.create_engine('sqlite:///fnuc_simple_lowercase.sqlite', echo=mode_echo)
            elif db_server=='postgresql':
                from urllib.parse import quote_plus
                engine = sqlalchemy.create_engine("postgresql://fnuc_simple_sqla_python:%s@localhost:5437/DB_fnuc_simple_sqla_python" % quote_plus("P@ssw0rd"), mode_echo)
            elif db_server=='oracle12':
                engine = sqlalchemy.create_engine("oracle://mdubois:michel@ora12c.univ-ubs.fr:1521/ORAETUD", echo=mode_echo)
            else:
                engine = sqlalchemy.create_engine("oracle://mdubois:michel@(DESCRIPTION = (ADDRESS_LIST = (ADDRESS = (PROTOCOL = TCP)(HOST = localhost) (PORT = 1521)))(CONNECT_DATA = (SERVICE_NAME = XEPDB1)))", echo=mode_echo)
              
            connection = engine.connect()

            # ordonner la reflexion de toutes les tables
            metadata = sqlalchemy.MetaData()
            # la reflexion d'une vue ne marche pas avec mysql
            #metadata.reflect(bind=engine, views=True)
            metadata.reflect(bind=engine)

            #Connaitre le dialect donc le SGBDR connecte au moteur sqla
            Session = sessionmaker(bind=engine)
            session_sqla = Session()
            db=session_sqla.bind.dialect.name 
        if db_changed==False:    
            r=connection.execute(parametres_table.update().values(logo_url=logo_url, taux_tva=taux_tva).where(parametres_table.c.id==parametre_id))
            message = 'Les paramètres en base de données voire en mémoire sont modifiés !'
        else:
            message = 'Les paramètres en mémoire uniquement sont modifiés car on vient de changer de moteur voire de serveur de données!'
    except:
        message = 'Les paramètres en base de données non enregistrés suite à un probleme avec la base de donnees ! trace='+traceback.format_exc()
        error = True
    if error:
        return render_template("admin_message_error.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Modifier les paramètres en base de données et ceux de l'application en mémoire", message=message) 
    else:
        return render_template("admin_message_done.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Modifier les paramètres en base de données et ceux de l'application en mémoire", message=message) 

@app.route('/admin_parameter_delete' , methods=['GET'])   
def adminParameterDelete():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    parametres_table = metadata.tables["parametres"]
    parametreRow=connection.execute(sqlalchemy.select([parametres_table]).where(parametres_table.c.id==1)).fetchone()   
        
    return render_template("admin_parameter_delete.html", db = db, url_base=url_base, mode_admin=mode_admin, parameter=parametreRow)  

@app.route('/admin_parameter_delete' , methods=['POST'])   
def adminParameterDeleteProcess():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    parametres_table = metadata.tables["parametres"]
    parametre_id = request.form.get('parameterId')
    error=False
    try:
        r=connection.execute(sqlalchemy.delete(parametres_table).where(parametres_table.c.id == parametre_id))
        message = 'Les paramètres en base de données sont détruits !'         
    except:
        message = 'Les paramètres en base de données non détruits suite à un probleme avec la base de donnees ! trace='+traceback.format_exc()
        error = True
    if error:
        return render_template("admin_message_error.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Supprimer les paramètres en base de données", message=message) 
    else:
        return render_template("admin_message_done.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Supprimer les paramètres en base de données", message=message) 

@app.route('/upload', methods = ['GET'])
def uploadFile():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    return render_template('upload.html', db = db, url_base=url_base, mode_admin=mode_admin)
	
@app.route('/upload', methods = ['POST'])
def uploadFileProcess():
    if session.get('usertype') == None:
        return redirect(url_for("loginForm"))
    if session.get('usertype') != 'admin':
        return redirect(url_for("showAllTopics"))
    document_path = request.form.get('document_path')
    app.config['UPLOAD_FOLDER'] = path_doc+document_path
    app.config['MAX_CONTENT_LENGTH'] = max_upload_size
    f = request.files['file']
    error=False
    try:
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
        message = 'Le fichier a bien été envoyé sur le server !'
    except:
        message = 'Le fichier n''a pas été envoyé sur le server suite à un probleme ! trace='+traceback.format_exc()
        error = True    
    if error:
        return render_template("admin_message_error.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Envoyer un fichier sur le serveur des documents", message=message) 
    else:
        return render_template("admin_message_done.html", db = db, url_base=url_base, mode_admin=mode_admin, operation="Envoyer un fichier sur le serveur des documents", message=message) 
      
if __name__ == '__main__' : 
   app.run(debug=True) 
