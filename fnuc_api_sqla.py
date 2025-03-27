#!/usr/bin/python3 
# -*- coding:utf-8 

# Correspondance des tables :

# people_events_table : livres_sujets_table
# people_id : book_id
# event_id : topic_id

# people_events_table : livres_motscles_table
# people_id : book_id
# event_id : keyword_id

# people_table: clients_table
# id : id

# events_table : livres_table join stocks_table
# id : id

# bills_table : commandes_table
# id : id
# payer_id : client
# event_id : article



# Correspondance des URLs :
# /people :                                       /api/customers
# /people/<int:id>                              : /api/customers/<int:id>
# /events                                       : /api/books
# /events/<int:id>                              : /api/books/<int:id>
# /bills                                        : /api/orders
# /bills/<int:id>                               : /api/orders/<int:id>
# /people/<int:people_id>/events                : /api/books/<int:book_id>/topics
# /people/<int:people_id>/events/<int:event_id> : /api/books/<int:book_id>/topics/<int:topic_id>
# /events/<int:event_id>/people/<int:people_id> : /api/topics/<int:topic_id>/books/<int:book_id>
# /people/<int:people_id>/events                : /api/books/<int:book_id>/keywords
# /people/<int:people_id>/events/<int:event_id> : /api/books/<int:book_id>/keywords/<int:keyword_id>
# /events/<int:event_id>/people/<int:people_id> : /api/keywords/<int:keyword_id>/books/<int:book_id>
# /people/<int:people_id>/bills                 : /api/customers/<int:customer_id>/orders
# /people/<int:people_id>/bills/<int:bill_id>   : /api/customers/<int:customer_id>/orders/<int:order_id>

# /api/books/<int:book_id>/orders
# /api/books/<int:book_id>/orders/<int:order_id>

# /api/topics/
# /api/topics/<int:topic_id>
# /api/topics/<int:topic_id>/books
# /api/keywords/
# /api/keywords/<int:keyword_id>
# /api/keywords/<int:keyword_id>/books

#################
# AFaire :
# Completer les trous listés dans ce fichier
# Attention, ceci peut entrainer l'édition de templates, de fichiers javascript, css
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from flask import Flask, Response, request, render_template, make_response
from datetime import datetime
from typing import Any, Dict

app = Flask(__name__)

# apache server must run !
url_base = 'http://localhost:5000/static/'
embedding = True
linking = True
mode_echo = True
tva_rate = 0.196
# SQLAlchemy without Flask-SQLAlchemy

# Connect to the DB and reflect metadata.
# mysql+mysqlconnector://python:python@localhost:3312/fnuc_simple_sqla_python?auth_plugin=mysql_native_password
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

def get_all(table_name: str) -> Dict:
    table = metadata.tables[table_name]
    result = connection.execute(table.select()).fetchall()
    return {
        "result": [
            dict(resource) for resource in result
        ]
    }


def get_one(table_name: str, column_name: str, value: Any) -> Dict:
    table = metadata.tables[table_name]
    result = connection.execute(
        sqlalchemy.select([table]).where(
            getattr(table.c, column_name) == value
        )
    ).fetchall()
    return {
        "result": [
            dict(resource) for resource in result
        ]
    }


def patch_one(table_name: str, column_name: str, value: Any) -> Response:
    content_type = request.headers.get("Content-Type")
    if (content_type != "application/json"):
        return {
            "result": "Failure",
            "reason": "Content-Type not supported!",
        }

    table = metadata.tables[table_name]
    # There should be validation that the PATCH body is valid here!
    connection.execute(
        sqlalchemy.update(table).where(
            getattr(table.c, column_name) == value
        ).values(
            **request.json,
        )
    )
    return Response(status=204)  # No Content


def post(table_name: str) -> Response:
    content_type = request.headers.get("Content-Type")
    if (content_type != "application/json"):
        return {
            "result": "Failure",
            "reason": "Content-Type not supported!",
        }

    table = metadata.tables[table_name]
    # There should be validation that the POST body is valid here!
    connection.execute(
        sqlalchemy.insert(table).values(
            **request.json,
        )
    )
    return Response(status=201)  # Created


def delete_one(table_name: str, column_name: str, value: Any) -> Response:
    table = metadata.tables[table_name]
    connection.execute(
        sqlalchemy.delete(table).where(
            getattr(table.c, column_name) == value
        )
    )
    return Response(status=204)  # No Content


def insert_book_topic(book_id: int, topic_id: int) -> None:
    livres_sujets_table = metadata.tables["livres_sujets"]
    connection.execute(
        sqlalchemy.insert(livres_sujets_table).values(
            book_id=book_id,
            topic_id=topic_id,
        )
    )


def delete_book_topic(book_id: int, topic_id: int) -> None:
    livres_sujets_table = metadata.tables["livres_sujets"]
    connection.execute(
        sqlalchemy.delete(livres_sujets_table).where(
            (livres_sujets_table.c.book_id == book_id)
            & (livres_sujets_table.c.topic_id == topic_id)
        )
    )

def insert_book_keyword(book_id: int, keyword_id: int) -> None:
    livres_motscles_table = metadata.tables["livres_motscles"]
    connection.execute(
        sqlalchemy.insert(livres_motscles_table).values(
            book_id=book_id,
            keyword_id=keyword_id,
        )
    )


def delete_book_keyword(book_id: int, keyword_id: int) -> None:
    livres_motscles_table = metadata.tables["livres_motscles"]
    connection.execute(
        sqlalchemy.delete(livres_motscles_table).where(
            (livres_motscles_table.c.book_id == book_id)
            & (livres_motscles_table.c.keyword_id == keyword_id)
        )
    )

# Endpoints:
@app.route('/')
def get_root():
    print('sending root')
    return render_template('index.html')

@app.route('/showbookreferenceoftopic' , methods=['GET'])   
def showBookReferenceOfTopic():
    topic_id = request.args['topicId']
    topic_name = request.args['topicName']
    return render_template('GetBookReferencesOfTopic.html', topicName=topic_name, topicId=topic_id)

@app.route('/search' , methods=['GET'])   
def search():
    #################
    # Nouveau : déjà implanté donc pas à faire
    # construction en javascript du formulaire utilisant une table HTML
    return render_template('search.html')
    
@app.route('/showbook' , methods=['GET'])   
def showBook():
    book_id = request.args['bookId']
    #################
    # Nouveau : déjà implanté donc pas à faire
    # Prise en compte du paramètre embedding qui peut valoir False pour en javascript récupérer le niveau actuel du stock
    # Et n'afficher les liens pour commander le livre que s'il reste au moins une quantité supérieure à 1
    return render_template('GetBook.html', url_base=url_base, bookId=book_id, embedding=embedding)

@app.route('/orderbook' , methods=['GET'])
def orderBookForm():
    book_id = request.args['bookId']
    book_price = request.args['bookPrice']    
    user_id = request.args['userId']
    user_name = request.args['userName']
    qty_max = request.args['qtyMax']
    date_com = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #################
    # Nouveau : déjà implanté donc pas à faire
    # Prise en compte du paramètre embedding qui peut valoir False pour en javascript récupérer le niveau actuel du stock
    # Faire en javascript que l'API REST soit éffectivement appelée pour baisser le niveau de stock et enregistrer une nouvelle commande
    return render_template('OrderBook.html', url_base=url_base, bookId=book_id, userId=user_id, userName=user_name, qtyMax=qty_max, datecom=date_com, embedding=embedding, book_price=book_price, book_taux_tva=format(tva_rate*100, '.2f'))

@app.route('/past_orders')
def get_orders():
    user_id = request.args['userId']
    user_name = request.args['userName']
    print('sending orders')
    #################
    # AFaire :
    # Pour le client, donner dans une table html générée en javascript l'historique de ses commandes
    #
    return render_template('GetOrders.html', url_base=url_base, userId=user_id, userName=user_name)

    
@app.route('/admin' , methods=['GET'])   
def adminParameter():
    app_parametreList=[{"url_root": "{}".format(request.url_root),"url_base":"{}".format(url_base), "embedding":"{}".format(embedding), "linking":"{}".format(linking), "dialect":"{}".format(db), "mode_echo":"{}".format(mode_echo)}]
    app_parametreRow={"url_root": "{}".format(request.url_root),"url_base":"{}".format(url_base), "embedding":"{}".format(embedding), "linking":"{}".format(linking), "dialect":"{}".format(db), "mode_echo":"{}".format(mode_echo)}    

    return render_template('admin_parameter.html', url_base=url_base, app_parameter=app_parametreRow, app_parameters=app_parametreList, db_server=db_server, mode_echo=mode_echo, embedding=embedding, linking=linking)

@app.route('/admin_parameter_update' , methods=['POST'])   
def adminParameterUpdateProcess():
    global url_base, db_server, db, connection, engine, metadata, mode_echo, linking, embedding
    error=False
    try:
        mode_echo_value = False
        if request.form.get('mode_echo') == 'True':
            mode_echo_value = True
        linking_value = False
        if request.form.get('linking') == 'True':
            linking_value = True
        embedding_value = False
        if request.form.get('embedding') == 'True':
            embedding_value = True            
        if url_base!=request.form.get('url_base'):
            url_base = request.form.get('url_base')
        if mode_echo!=mode_echo_value:
            mode_echo = mode_echo_value
        if linking!=linking_value:
            linking = linking_value
        if embedding!=embedding_value:
            embedding = embedding_value
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
                engine = sqlalchemy.create_engine('sqlite:///D:\\tools\\WinPython-64bit-3.5.3.1Qt5\\python-3.5.3.amd64\\projects\\fnuc_flask_sqla_rest\\fnuc_simple_lowercase.sqlite?check_same_thread=False', echo=mode_echo)
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

        message = 'Les paramètres en mémoire sont modifiés'
    except:
        message = 'Il y a un problème avec la base de données ! trace='+traceback.format_exc()
        error = True
    if error:
        return render_template("admin_message_error.html", db = db, url_base=url_base, operation="Modifier les paramètres de l'application en mémoire", message=message) 
    else:
        return render_template("admin_message_done.html", db = db, url_base=url_base, operation="Modifier les paramètres de l'application en mémoire", message=message) 

@app.route('/docs')
def get_docs():
    #################
    # Nouveau : déjà implanté donc pas à faire
    # Enrichir la documentation OpenAPI (fichier openapi.yaml) en y ajoutant des points de terminaison supplémentaires
    #
    print('sending docs')
    return render_template('swaggerui.html')
    
@app.route('/help')
def get_help():
    #################
    # Nouveau : déjà implanté donc pas à faire
    # Transposez au cas la Fnuc le raisonnement faits sur les évennements (events, people, bills, people_events)
    #
    print('sending help')
    return render_template('help.html')


@app.route("/customers", methods=["GET"])
def get_all_customers() -> Dict:
    return get_all(table_name="clients")


@app.route("/customers/<int:id>", methods=["GET"])
def get_one_customers(id: int) -> Dict:
    return get_one(
        table_name="clients",
        column_name="id",
        value=id,
    )


@app.route("/customers", methods=["POST"])
def post_customers()  -> Response:
    return post("clients")


@app.route("/customers/<int:id>", methods=["PATCH"])
def patch_customers(id: int) -> Response:
    return patch_one(
        table_name="clients",
        column_name="id",
        value=id,
    )


@app.route("/customers/<int:id>", methods=["DELETE"])
def delete_customers(id: int) -> Response:
    # Should cascade deleting relationship(s) in `clients_events` here
    # Should also cascade deleting related `bill`(s) here
    return delete_one(
        table_name="clients",
        column_name="id",
        value=id,
    )

@app.route("/topics", methods=["GET"])
def get_all_topics() -> Dict:
    return get_all(table_name="sujets")


@app.route("/topics/<int:id>", methods=["GET"])
def get_one_topics(id: int) -> Dict:
    return get_one(
        table_name="sujets",
        column_name="id",
        value=id,
    )


@app.route("/topics", methods=["POST"])
def post_topics()  -> Response:
    return post("sujets")


@app.route("/topics/<int:id>", methods=["PATCH"])
def patch_topics(id: int) -> Response:
    return patch_one(
        table_name="sujets",
        column_name="id",
        value=id,
    )


@app.route("/topics/<int:id>", methods=["DELETE"])
def delete_topics(id: int) -> Response:
    # Should cascade deleting relationship(s) in `sujets_events` here
    # Should also cascade deleting related `bill`(s) here
    return delete_one(
        table_name="sujets",
        column_name="id",
        value=id,
    )

@app.route("/keywords", methods=["GET"])
def get_all_keywords() -> Dict:
    return get_all(table_name="motscles")


@app.route("/keywords/<int:id>", methods=["GET"])
def get_one_keywords(id: int) -> Dict:
    return get_one(
        table_name="motscles",
        column_name="id",
        value=id,
    )


@app.route("/keywords", methods=["POST"])
def post_keywords()  -> Response:
    return post("motscles")


@app.route("/keywords/<int:id>", methods=["PATCH"])
def patch_keywords(id: int) -> Response:
    return patch_one(
        table_name="motscles",
        column_name="id",
        value=id,
    )


@app.route("/keywords/<int:id>", methods=["DELETE"])
def delete_keywords(id: int) -> Response:
    # Should cascade deleting relationship(s) in `motscles_events` here
    # Should also cascade deleting related `bill`(s) here
    return delete_one(
        table_name="motscles",
        column_name="id",
        value=id,
    )

# Without 'links'
# @app.route("/books", methods=["GET"])
# def get_all_books() -> Dict:
#     return get_all(table_name="livres")


@app.route("/books", methods=["GET"])
def get_all_books() -> Dict:
    # Ideally you'd simplify this so you aren't making so many Database calls,
    # but it's left this way for clarity.
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    result = connection.execute(livres_table.select()).fetchall()
    books = []
    for book in result:
        book = dict(book)

        # Get related inventory
        inventory = connection.execute(
            sqlalchemy.select([stocks_table]).where(
                stocks_table.c.article == book.get("id")
            )
        ).fetchall()
        if len(inventory) > 0:
            if linking:
                inventory_id = dict(inventory[0]).get("id")
                book["links"] = {
                    # "inventory": "/inventories/{}".format(inventory_id),
                    "inventory": "{}inventories/{}".format(request.url_root,inventory_id),
                }
            if embedding:
                inventory = dict(inventory[0])
                book["inventory"] = inventory
        books.append(book)
    return {
        "result": books
    }


# Without 'links'
# @app.route("/books/<int:id>", methods=["GET"])
# def get_one_books(id: int) -> Dict:
#     return get_one(
#         table_name="livres",
#         column_name="id",
#         value=id,
#     )


@app.route("/books/<int:id>", methods=["GET"])
def get_one_books_with_links(id: int) -> Dict:
    # Ideally you'd simplify this so you aren't making so many Database calls,
    # but it's left this way for clarity.
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    result = connection.execute(
        sqlalchemy.select([livres_table]).where(
            livres_table.c.id == id
        )
    ).fetchall()
    books = []
    for book in result:
        book = dict(book)

        # Get related inventory
        inventory = connection.execute(
            sqlalchemy.select([stocks_table]).where(
                stocks_table.c.article == id
            )
        ).fetchall()
        if len(inventory) > 0:
            if linking:
                inventory_id = dict(inventory[0]).get("id")
                book["links"] = {
                    # "inventory": "/inventories/{}".format(inventory_id),
                    "inventory": "{}inventories/{}".format(request.url_root,inventory_id),
                }
            if embedding:
                inventory = dict(inventory[0])
                book["inventory"] = inventory
        books.append(book)
    return {
        "result": books
    }


@app.route("/books", methods=["POST"])
def post_books() -> Response:
    return post("livres")


@app.route("/books/<int:id>", methods=["PATCH"])
def patch_books(id: int) -> Response:
    return patch_one(
        table_name="livres",
        column_name="id",
        value=id,
    )


@app.route("/books/<int:id>", methods=["DELETE"])
def delete_books(id: int) -> Response:
    # Should cascade deleting relationship(s) in `people_events` here
    # Should also cascade deleting related `bill` here
    return delete_one(
        table_name="livres",
        column_name="id",
        value=id,
    )

# Without 'links'
# @app.route("/inventories", methods=["GET"])
# def get_all_inventories() -> Dict:
#     return get_all(table_name="stocks")


@app.route("/inventories", methods=["GET"])
def get_all_inventories() -> Dict:
    # Ideally you'd simplify this so you aren't making so many Database calls,
    # but it's left this way for clarity.
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    result = connection.execute(stocks_table.select()).fetchall()
    inventories = []
    for inventory in result:
        inventory = dict(inventory)

        # Get related book
        book = connection.execute(
            sqlalchemy.select([livres_table]).where(
                livres_table.c.id == inventory.get("article")
            )
        ).fetchall()
        
        if len(book) > 0:
            if linking:
                book_id = dict(book[0]).get("id")
                inventory["links"] = {
                    # "book": "/books/{}".format(book_id),
                    "book": "{}books/{}".format(request.url_root,book_id),
                }
            if embedding:
                book = dict(book[0])
                inventory["book"] = book

        inventories.append(inventory)
    return {
        "result": inventories
    }


# Without 'links'
# @app.route("/inventories/<int:id>", methods=["GET"])
# def get_one_inventories(id: int) -> Dict:
#     return get_one(
#         table_name="stocks",
#         column_name="id",
#         value=id,
#     )


@app.route("/inventories/<int:id>", methods=["GET"])
def get_one_inventories_with_links(id: int) -> Dict:
    # Ideally you'd simplify this so you aren't making so many Database calls,
    # but it's left this way for clarity.
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    result = connection.execute(
        sqlalchemy.select([stocks_table]).where(
            stocks_table.c.id == id
        )
    ).fetchall()
    inventories = []
    for inventory in result:
        inventory = dict(inventory)

        # Get related book
        book = connection.execute(
            sqlalchemy.select([livres_table]).where(
                livres_table.c.id == inventory.get("article")
            )
        ).fetchall()
        if len(book) > 0:
            if linking:
                book_id = dict(book[0]).get("id")
                inventory["links"] = {
                    # "book": "/books/{}".format(book_id),
                    "book": "{}books/{}".format(request.url_root,book_id),
                }
            if embedding:
                book = dict(book[0])
                inventory["book"] = book

        inventories.append(inventory)
    return {
        "result": inventories
    }


@app.route("/inventories", methods=["POST"])
def post_inventories() -> Response:
    return post("stocks")


@app.route("/inventories/<int:id>", methods=["PATCH"])
def patch_inventories(id: int) -> Response:
    return patch_one(
        table_name="stocks",
        column_name="id",
        value=id,
    )


@app.route("/inventories/<int:id>", methods=["DELETE"])
def delete_inventories(id: int) -> Response:
    # Should cascade deleting relationship(s) in `people_events` here
    # Should also cascade deleting related `bill` here
    return delete_one(
        table_name="stocks",
        column_name="id",
        value=id,
    )


# Without 'links'
# @app.route("/orders", methods=["GET"])
# def get_all_orders() -> Dict:
#     return get_all(table_name="commandes")


@app.route("/orders", methods=["GET"])
def get_all_orders() -> Dict:
    livres_table = metadata.tables["livres"]
    clients_table = metadata.tables["clients"]
    commandes_table = metadata.tables["commandes"]
    result = connection.execute(commandes_table.select()).fetchall()
    orders = []
    for order in result:
        order = dict(order)

        # Get related customer
        customer = connection.execute(
            sqlalchemy.select([clients_table]).where(
                clients_table.c.id == order.get("client")
            )
        ).fetchall()
        # Get related book
        book = connection.execute(
            sqlalchemy.select([livres_table]).where(
                livres_table.c.id == order.get("article")
            )
        ).fetchall()
        
        if len(customer) > 0 and len(book)>0:
            if linking:
                customer_id = dict(customer[0]).get("id")
                book_id = dict(book[0]).get("id")
                order["links"] = {            
                    "client": "{}customers/{}".format(request.url_root, customer_id),
                    "article": "{}books/{}".format(request.url_root, book_id)
                }
            if embedding:
                customer = dict(customer[0])
                book = dict(book[0])
                order["book"] = book
                order["customer"] = customer
        orders.append(order)
    return {
        "result": orders
    }


# Without 'links'
# @app.route("/orders/<int:id>", methods=["GET"])
# def get_one_orders(id: int) -> Dict:
#     return get_one(
#         table_name="commandes",
#         column_name="id",
#         value=id,
#     )


@app.route("/orders/<int:id>", methods=["GET"])
def get_one_orders(id: int) -> Dict:
    livres_table = metadata.tables["livres"]
    clients_table = metadata.tables["clients"]
    commandes_table = metadata.tables["commandes"]
    result = connection.execute(
        sqlalchemy.select([commandes_table]).where(
            commandes_table.c.id == id
        )
    ).fetchall()
    orders = []
    for order in result:
        order = dict(order)

        # Get related customer
        customer = connection.execute(
            sqlalchemy.select([clients_table]).where(
                clients_table.c.id == order.get("client")
            )
        ).fetchall()
        # Get related book
        book = connection.execute(
            sqlalchemy.select([livres_table]).where(
                livres_table.c.id == order.get("article")
            )
        ).fetchall()
        
        if len(customer) > 0 and len(book)>0:
            if linking:
                customer_id = dict(customer[0]).get("id")
                book_id = dict(book[0]).get("id")
                order["links"] = {            
                    "client": "{}customers/{}".format(request.url_root, customer_id),
                    "article": "{}books/{}".format(request.url_root, book_id)
                }
            if embedding:
                customer = dict(customer[0])
                book = dict(book[0])
                order["book"] = book
                order["customer"] = customer

        orders.append(order)
    return {
        "result": orders
    }


@app.route("/orders", methods=["POST"])
def post_orders() -> Response:
    return post("commandes")


@app.route("/orders/<int:id>", methods=["PATCH"])
def patch_orders(id: int) -> Response:
    return patch_one(
        table_name="commandes",
        column_name="id",
        value=id,
    )


@app.route("/orders/<int:id>", methods=["DELETE"])
def delete_orders(id: int) -> Response:
    return delete_one(
        table_name="commandes",
        column_name="id",
        value=id,
    )


# Many to Many relationships:

@app.route("/books/<int:book_id>/topics", methods=["GET"])
def get_books_topics_all(book_id: int) -> Dict:
    livres_sujets_table = metadata.tables["livres_sujets"]
    sujets_table = metadata.tables["sujets"]
    result = connection.execute(
        # sujets_table.select().join(
            # livres_sujets_table,
            # sujets_table.c.id == livres_sujets_table.c.topic_id
        # ).where(
            # livres_sujets_table.c.book_id == book_id
        # )
        sqlalchemy.select([sujets_table]).select_from(sujets_table.join(livres_sujets_table,
                sujets_table.c.id == livres_sujets_table.c.topic_id)).where(
             livres_sujets_table.c.book_id == book_id
        )        
    ).fetchall()
    return {
        "result": [
            dict(topic) for topic in result
        ]
    }


@app.route("/books/<int:book_id>/topics/<int:topic_id>", methods=["GET"])
def get_books_topics_one(book_id: int, topic_id: int) -> Dict:
    livres_sujets_table = metadata.tables["livres_sujets"]
    sujets_table = metadata.tables["sujets"]
    result = connection.execute(
        # sujets_table.select().join(
            # livres_sujets_table,
            # sujets_table.c.id == livres_sujets_table.c.topic_id
        # ).where(
            # (livres_sujets_table.c.book_id == book_id)
            # & (livres_sujets_table.c.topic_id == topic_id)
        # )
          sqlalchemy.select([sujets_table]).select_from(sujets_table.join(livres_sujets_table,
                sujets_table.c.id == livres_sujets_table.c.topic_id)).where(
             (livres_sujets_table.c.book_id == book_id)
             & (livres_sujets_table.c.topic_id == topic_id)
             
        ) 
    ).fetchall()
    return {
        "result": [
            dict(topic) for topic in result
        ]
    }


@app.route("/topics/<int:topic_id>/books", methods=["GET"])
def get_topics_books_all(topic_id: int) -> Dict:
    livres_sujets_table = metadata.tables["livres_sujets"]
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    result = connection.execute(
        # livres_table.select().join(
            # livres_sujets_table,
            # livres_table.c.id == livres_sujets_table.c.topic_id
        # ).where(
            # livres_sujets_table.c.topic_id == topic_id
        # )
        
        sqlalchemy.select([livres_table]).distinct().select_from(livres_table.join(livres_sujets_table,
                livres_table.c.id == livres_sujets_table.c.book_id)).where(
             livres_sujets_table.c.topic_id == topic_id
         )
    ).fetchall()
    books = []
    for book in result:
        book = dict(book)

        # Get related inventory
        inventory = connection.execute(
            sqlalchemy.select([stocks_table]).where(
                stocks_table.c.article == book.get("id")
            )
        ).fetchall()
        if len(inventory) > 0:
            if linking:
                inventory_id = dict(inventory[0]).get("id")
                book["links"] = {
                    # "inventory": "/inventories/{}".format(inventory_id),
                    "inventory": "{}inventories/{}".format(request.url_root,inventory_id),
                }
            if embedding:
                inventory = dict(inventory[0])
                book["inventory"] = inventory
        books.append(book)
    return {
        "result": books
    }


@app.route("/topics/<int:topic_id>/books/<int:book_id>", methods=["GET"])
def get_topics_books_one(topic_id: int, book_id: int) -> Dict:
    livres_sujets_table = metadata.tables["livres_sujets"]
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    result = connection.execute(
        # livres_table.select().join(
            # livres_sujets_table,
            # livres_table.c.id == livres_sujets_table.c.topic_id
        # ).where(
            # (livres_sujets_table.c.book_id == book_id)
            # & (livres_sujets_table.c.topic_id == topic_id)
        # )
        
        sqlalchemy.select([livres_table]).distinct().select_from(livres_table.join(livres_sujets_table,
                livres_table.c.id == livres_sujets_table.c.book_id)).where(
             (livres_sujets_table.c.book_id == book_id)
            & (livres_sujets_table.c.topic_id == topic_id)
        )
 
    ).fetchall()
    books = []
    for book in result:
        book = dict(book)

        # Get related inventory
        inventory = connection.execute(
            sqlalchemy.select([stocks_table]).where(
                stocks_table.c.article == book.get("id")
            )
        ).fetchall()
        if len(inventory) > 0:
            if linking:
                inventory_id = dict(inventory[0]).get("id")
                book["links"] = {
                    # "inventory": "/inventories/{}".format(inventory_id),
                    "inventory": "{}inventories/{}".format(request.url_root,inventory_id),
                }
            if embedding:
                inventory = dict(inventory[0])
                book["inventory"] = inventory
        books.append(book)
    return {
        "result": books
    }


@app.route("/books/<int:book_id>/topics/<int:topic_id>", methods=["PATCH"])
def patch_books_topics(book_id: int, topic_id: int) -> Response:
    # Ideally there'd be error handling for if the event doesn't exist here

    # Sign person up for event
    insert_book_topic(book_id, topic_id)
    return Response(status=204)  # No Content


@app.route("/topics/<int:topic_id>/books/<int:book_id>", methods=["PATCH"])
def patch_topics_books(topic_id: int, book_id: int) -> Response:
    # Ideally there'd be error handling for if the event doesn't exist here

    # Sign person up for event
    insert_book_topic(book_id, topic_id)
    return Response(status=204)  # No Content


@app.route("/books/<int:book_id>/topics/<int:topic_id>", methods=["DELETE"])
def delete_books_topics(book_id: int, topic_id: int) -> Response:
    delete_book_topic(book_id, topic_id)
    return Response(status=204)  # No Content


@app.route("/topics/<int:topic_id>/books/<int:book_id>", methods=["DELETE"])
def delete_topics_books(topic_id: int, book_id: int) -> Response:
    delete_book_topic(book_id, topic_id)
    return Response(status=204)  # No Content

# Many to Many relationships:

@app.route("/books/<int:book_id>/keywords", methods=["GET"])
def get_books_keywords_all(book_id: int) -> Dict:
    livres_motscles_table = metadata.tables["livres_motscles"]
    motscles_table = metadata.tables["motscles"]
    result = connection.execute(
        # motscles_table.select().join(
            # livres_motscles_table,
            # motscles_table.c.id == livres_motscles_table.c.keyword_id
        # ).where(
            # livres_motscles_table.c.book_id == book_id
        # )
        sqlalchemy.select([motscles_table]).select_from(motscles_table.join(livres_motscles_table,
                motscles_table.c.id == livres_motscles_table.c.keyword_id)).where(
             livres_motscles_table.c.book_id == book_id
        )        
    ).fetchall()
    return {
        "result": [
            dict(keyword) for keyword in result
        ]
    }


@app.route("/books/<int:book_id>/keywords/<int:keyword_id>", methods=["GET"])
def get_books_keywords_one(book_id: int, keyword_id: int) -> Dict:
    livres_motscles_table = metadata.tables["livres_motscles"]
    motscles_table = metadata.tables["motscles"]
    result = connection.execute(
        # motscles_table.select().join(
            # livres_motscles_table,
            # motscles_table.c.id == livres_motscles_table.c.keyword_id
        # ).where(
            # (livres_motscles_table.c.book_id == book_id)
            # & (livres_motscles_table.c.keyword_id == keyword_id)
        # )
          sqlalchemy.select([motscles_table]).select_from(motscles_table.join(livres_motscles_table,
                motscles_table.c.id == livres_motscles_table.c.keyword_id)).where(
             (livres_motscles_table.c.book_id == book_id)
             & (livres_motscles_table.c.keyword_id == keyword_id)
             
        ) 
    ).fetchall()
    return {
        "result": [
            dict(keyword) for keyword in result
        ]
    }


@app.route("/keywords/<int:keyword_id>/books", methods=["GET"])
def get_keywords_books_all(keyword_id: int) -> Dict:
    livres_motscles_table = metadata.tables["livres_motscles"]
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    result = connection.execute(
        # livres_table.select().join(
            # livres_motscles_table,
            # livres_table.c.id == livres_motscles_table.c.keyword_id
        # ).where(
            # livres_motscles_table.c.keyword_id == keyword_id
        # )
        
        sqlalchemy.select([livres_table]).distinct().select_from(livres_table.join(livres_motscles_table,
                livres_table.c.id == livres_motscles_table.c.book_id)).where(
             livres_motscles_table.c.keyword_id == keyword_id
         )
    ).fetchall()
    books = []
    for book in result:
        book = dict(book)

        # Get related inventory
        inventory = connection.execute(
            sqlalchemy.select([stocks_table]).where(
                stocks_table.c.article == book.get("id")
            )
        ).fetchall()
        if len(inventory) > 0:
            if linking:
                inventory_id = dict(inventory[0]).get("id")
                book["links"] = {
                    # "inventory": "/inventories/{}".format(inventory_id),
                    "inventory": "{}inventories/{}".format(request.url_root,inventory_id),
                }
            if embedding:
                inventory = dict(inventory[0])
                book["inventory"] = inventory
        books.append(book)
    return {
        "result": books
    }


@app.route("/keywords/<int:keyword_id>/books/<int:book_id>", methods=["GET"])
def get_keywords_books_one(keyword_id: int, book_id: int) -> Dict:
    livres_motscles_table = metadata.tables["livres_motscles"]
    livres_table = metadata.tables["livres"]
    stocks_table = metadata.tables["stocks"]
    result = connection.execute(
        # livres_table.select().join(
            # livres_motscles_table,
            # livres_table.c.id == livres_motscles_table.c.keyword_id
        # ).where(
            # (livres_motscles_table.c.book_id == book_id)
            # & (livres_motscles_table.c.keyword_id == keyword_id)
        # )
        
        sqlalchemy.select([livres_table]).distinct().select_from(livres_table.join(livres_motscles_table,
                livres_table.c.id == livres_motscles_table.c.book_id)).where(
             (livres_motscles_table.c.book_id == book_id)
            & (livres_motscles_table.c.keyword_id == keyword_id)
        )
 
    ).fetchall()
    books = []
    for book in result:
        book = dict(book)

        # Get related inventory
        inventory = connection.execute(
            sqlalchemy.select([stocks_table]).where(
                stocks_table.c.article == book.get("id")
            )
        ).fetchall()
        if len(inventory) > 0:
            if linking:
                inventory_id = dict(inventory[0]).get("id")
                book["links"] = {
                    # "inventory": "/inventories/{}".format(inventory_id),
                    "inventory": "{}inventories/{}".format(request.url_root,inventory_id),
                }
            if embedding:
                inventory = dict(inventory[0])
                book["inventory"] = inventory
        books.append(book)
    return {
        "result": books
    }


@app.route("/books/<int:book_id>/keywords/<int:keyword_id>", methods=["PATCH"])
def patch_books_keywords(book_id: int, keyword_id: int) -> Response:
    # Ideally there'd be error handling for if the event doesn't exist here

    # Sign person up for event
    insert_book_keyword(book_id, keyword_id)
    return Response(status=204)  # No Content


@app.route("/keywords/<int:keyword_id>/books/<int:book_id>", methods=["PATCH"])
def patch_keywords_books(keyword_id: int, book_id: int) -> Response:
    # Ideally there'd be error handling for if the event doesn't exist here

    # Sign person up for event
    insert_book_keyword(book_id, keyword_id)
    return Response(status=204)  # No Content


@app.route("/books/<int:book_id>/keywords/<int:keyword_id>", methods=["DELETE"])
def delete_books_keywords(book_id: int, keyword_id: int) -> Response:
    delete_book_keyword(book_id, keyword_id)
    return Response(status=204)  # No Content


@app.route("/keywords/<int:keyword_id>/books/<int:book_id>", methods=["DELETE"])
def delete_keywords_books(keyword_id: int, book_id: int) -> Response:
    delete_book_keyword(book_id, keyword_id)
    return Response(status=204)  # No Content


# 1 to Many Relationships:

@app.route("/customers/<int:customer_id>/orders", methods=["GET"])
def get_customers_orders_all(customer_id: int) -> Dict:
    commandes_table = metadata.tables["commandes"]
    clients_table = metadata.tables["clients"]
    livres_table = metadata.tables["livres"]
    result = connection.execute(
        # commandes_table.select().join(
            # people_table,
            # people_table.c.id == commandes_table.c.payer_id
        # ).where(
            # (people_table.c.id == people_id)
        # )
        sqlalchemy.select([commandes_table]).select_from(commandes_table.join(clients_table,
                clients_table.c.id == commandes_table.c.client)).where(
             clients_table.c.id == customer_id
        )
    ).fetchall()
    orders = []
    for order in result:
        order = dict(order)

        # Get related customer
        customer = connection.execute(
            sqlalchemy.select([clients_table]).where(
                clients_table.c.id == order.get("client")
            )
        ).fetchall()
        # Get related book
        book = connection.execute(
            sqlalchemy.select([livres_table]).where(
                livres_table.c.id == order.get("article")
            )
        ).fetchall()
        
        if len(customer) > 0 and len(book)>0:
            if linking:
                customer_id = dict(customer[0]).get("id")
                book_id = dict(book[0]).get("id")
                order["links"] = {            
                    "client": "{}customers/{}".format(request.url_root, customer_id),
                    "article": "{}books/{}".format(request.url_root, book_id)
                }
            if embedding:
                customer = dict(customer[0])
                book = dict(book[0])
                order["book"] = book
                order["customer"] = customer
        orders.append(order)
    return {
        "result": orders
    }


@app.route("/customers/<int:customer_id>/orders/<int:order_id>", methods=["GET"])
def get_customers_orders_one(customer_id: int, order_id: int) -> Dict:
    commandes_table = metadata.tables["commandes"]
    clients_table = metadata.tables["clients"]
    livres_table = metadata.tables["livres"]
    result = connection.execute(
        # commandes_table.select().join(
            # clients_table,
            # clients_table.c.id == commandes_table.c.client
        # ).where(
            # (commandes_table.c.id == order_id)
            # & (clients_table.c.id == customer_id)
        # )
        sqlalchemy.select([commandes_table]).select_from(commandes_table.join(clients_table,
                clients_table.c.id == commandes_table.c.client)).where(
                (commandes_table.c.id == order_id)
             & (clients_table.c.id == customer_id)
        )        
    ).fetchall()
    orders = []
    for order in result:
        order = dict(order)

        # Get related customer
        customer = connection.execute(
            sqlalchemy.select([clients_table]).where(
                clients_table.c.id == order.get("client")
            )
        ).fetchall()
        # Get related book
        book = connection.execute(
            sqlalchemy.select([livres_table]).where(
                livres_table.c.id == order.get("article")
            )
        ).fetchall()
        
        if len(customer) > 0 and len(book)>0:
            if linking:
                customer_id = dict(customer[0]).get("id")
                book_id = dict(book[0]).get("id")
                order["links"] = {            
                    "client": "{}customers/{}".format(request.url_root, customer_id),
                    "article": "{}books/{}".format(request.url_root, book_id)
                }
            if embedding:
                customer = dict(customer[0])
                book = dict(book[0])
                order["book"] = book
                order["customer"] = customer
        orders.append(order)
    return {
        "result": orders
    }

@app.route("/books/<int:book_id>/orders", methods=["GET"])
def get_books_orders_all(book_id: int) -> Dict:
    commandes_table = metadata.tables["commandes"]
    livres_table = metadata.tables["livres"]
    clients_table = metadata.tables["livres"]
    result = connection.execute(
        # commandes_table.select().join(
            # people_table,
            # people_table.c.id == commandes_table.c.payer_id
        # ).where(
            # (people_table.c.id == people_id)
        # )
        sqlalchemy.select([commandes_table]).select_from(commandes_table.join(livres_table,
                livres_table.c.id == commandes_table.c.article)).where(
             livres_table.c.id == book_id
        )
    ).fetchall()
    orders = []
    for order in result:
        order = dict(order)

        # Get related customer
        customer = connection.execute(
            sqlalchemy.select([clients_table]).where(
                clients_table.c.id == order.get("client")
            )
        ).fetchall()
        # Get related book
        book = connection.execute(
            sqlalchemy.select([livres_table]).where(
                livres_table.c.id == order.get("article")
            )
        ).fetchall()
        
        if len(customer) > 0 and len(book)>0:
            if linking:
                customer_id = dict(customer[0]).get("id")
                book_id = dict(book[0]).get("id")
                order["links"] = {            
                    "client": "{}customers/{}".format(request.url_root, customer_id),
                    "article": "{}books/{}".format(request.url_root, book_id)
                }
            if embedding:
                customer = dict(customer[0])
                book = dict(book[0])
                order["book"] = book
                order["customer"] = customer
        orders.append(order)
    return {
        "result": orders
    }

@app.route("/books/<int:book_id>/orders/<int:order_id>", methods=["GET"])
def get_books_orders_one(book_id: int, order_id: int) -> Dict:
    commandes_table = metadata.tables["commandes"]
    livres_table = metadata.tables["livres"]
    result = connection.execute(
        # commandes_table.select().join(
            # clients_table,
            # clients_table.c.id == commandes_table.c.client
        # ).where(
            # (commandes_table.c.id == order_id)
            # & (clients_table.c.id == customer_id)
        # )
        sqlalchemy.select([commandes_table]).select_from(commandes_table.join(livres_table,
                livres_table.c.id == commandes_table.c.client)).where(
                (commandes_table.c.id == order_id)
             & (livres_table.c.id == customer_id)
        )        
    ).fetchall()
    orders = []
    for order in result:
        order = dict(order)

        # Get related customer
        customer = connection.execute(
            sqlalchemy.select([clients_table]).where(
                clients_table.c.id == order.get("client")
            )
        ).fetchall()
        # Get related book
        book = connection.execute(
            sqlalchemy.select([livres_table]).where(
                livres_table.c.id == order.get("article")
            )
        ).fetchall()
        
        if len(customer) > 0 and len(book)>0:
            if linking:
                customer_id = dict(customer[0]).get("id")
                book_id = dict(book[0]).get("id")
                order["links"] = {            
                    "client": "{}customers/{}".format(request.url_root, customer_id),
                    "article": "{}books/{}".format(request.url_root, book_id)
                }
            if embedding:
                customer = dict(customer[0])
                book = dict(book[0])
                order["book"] = book
                order["customer"] = customer
        orders.append(order)
    return {
        "result": orders
    }


if __name__ == "__main__":
    app.run(debug=True)
