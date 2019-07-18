#!/usr/bin/python

#general imports
import json
import pickle
import os
import random
import sys

#Logging initialization
import logging
from logging.config import dictConfig
from logging.handlers import SysLogHandler

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi'],
        'propagate': True,
    }
})

#Uncomment below to turnon statsd
#from statsd import StatsClient
#statsd = StatsClient(host='localhost',
#                     port=8125,
#                     prefix='fitcycle-api-server',
#                     maxudpsize=512)

#initializing requests
import requests
from requests.auth import HTTPBasicAuth

#initializing flask
from flask import Flask, render_template, jsonify, flash, request
app = Flask(__name__)
app.debug=True

# set variables with env variables
from os import environ

if environ.get('REDIS_HOST') is not None:
    if os.environ['REDIS_HOST'] != "":
        redishost=os.environ['REDIS_HOST']
    else:
        redishost='localhost'
else:
    redishost='localhost'

if environ.get('REDIS_PORT') is not None:
    if os.environ['REDIS_PORT'] != "":
        redisport=os.environ['REDIS_PORT']
    else:
        redisport=6379
else:
    redisport=6379

if environ.get('REDIS_PASSWORD') is not None:
    if os.environ['REDIS_PASSWORD'] != "":
        redispassword=os.environ['REDIS_PASSWORD']
    else:
        redispassword= None
else:
    redispassword= None

if environ.get('CART_PORT') is not None:
    if os.environ['CART_PORT'] != "":
        cartport=os.environ['CART_PORT']
    else:
        cartport=5000
else:
    cartport=5000

#initializing redis connections on localhost and port 6379
#If error terminates process- entire cart is shut down

import redis

try:
    if redispassword is not None:
        app.logger.info('initiating redis connection with password %s', redispassword)
        rConn=redis.StrictRedis(host=redishost, port=redisport, password=redispassword, db=0)
    else:
        app.logger.info('initiating redis connection with no password %s', redispassword)
        rConn=redis.StrictRedis(host=redishost, port=redisport, password=None, db=0)
    app.logger.info('initiated redis connection %s', rConn)
    rConn.ping()
    app.logger.info('Connected to redis')
except Exception as ex:
    app.logger.error('Error for redis connection %s', ex)
    exit('Failed to connect, terminating')

#errorhandler for specific responses
class FoundIssue(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(FoundIssue)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

#initialization of redis with fake data from the San Francisco legal offices of Shri, Dan and Bill SDB.
def insertData():

    app.logger.info('inserting data')

    rConn.flushall()

    keys = ['bill', 'dan', 'shri']

    data=[
        {'itemid':'sdfsdfsfs', 'name':'fitband','description':'fitband for any age - even babies', 'quantity':1, 'price':4.5},
        {'itemid':'sfsdsda3343','name':'redpant','description':'the most awesome redpants in the world', 'quantity':1, 'price':400},
        ]

    payload=json.dumps(data)

    for x in keys:
        rConn.set(x, payload)

#Gets all items from a specific userid
def getitems(userid):

    if rConn.exists(userid):
        unpacked_data = json.loads(rConn.get(userid).decode('utf-8'))
        app.logger.info('got data')
    else:
        app.logger.info('empty - no data for key %s', userid)
        unpacked_data = 0

    return unpacked_data

#convert string to number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#http call to gets all Items from a cart (userid)
#If successful this returns the cart and items, if not successfull (the user id is non-existant) - 204 returned

#@statsd.timer('getCartItems')
@app.route('/cart/items/<userid>', methods=['GET'])
def getCartItems(userid):

    app.logger.info('getting all items on cart')
    PPTable = getitems(userid)
    if PPTable:
        packed_data=jsonify({"userid":userid, "cart":PPTable})
    else:
        app.logger.info('no items in cart found for %s', userid)
        output_message="no cart found for "+userid

        raise FoundIssue(str(output_message), status_code=204)
#        return ({'message':str(output_message)},204)

    return packed_data

#gets total items in users cart
@app.route('/cart/items/total/<userid>', methods=['GET', 'POST'])
def cartItemsTotal(userid):

    app.logger.info('getting total for %s cart',userid)

    jsonobj=getitems(userid)

    keylist=[]
    for item in jsonobj:
        keylist.append(list(item.keys())[0])

    keyindex=0
    total=0

    while keyindex < len(jsonobj):
        quantity=jsonobj[keyindex]['quantity']
        if is_number(quantity):
            total=total+float(quantity)
        else:
            total=total+0
        keyindex += 1

    app.logger.info("The total number of items is %s", str(total))

    totaljson={"userid":userid, "cartitemtotal":total}

    return jsonify(totaljson)


#http call to get all carts and their values
#@statsd.timer('getAllCarts')
@app.route('/cart/all', methods=['GET'])
def getAllCarts():
    app.logger.info('getting carts')

    carts=[]
    cart={}

    for x in rConn.keys():
        cleankey=x.decode('utf-8')
        cart['id']=cleankey
        cart['cart']=json.loads(rConn.get(cleankey).decode('utf-8'))
        carts.append(cart)
        cart={}

    return jsonify({'all carts': carts})

#http call to add an item - if user id non-existant - this will add the user into the database or it will concatenate the item to the existing carts
#example curl call to test: curl --header "Content-Type: application/json" --request POST --data '{"mytext":"xyz", "idname":"1234"}' http://34.215.155.50:5000/additem/bill
#If add is positive returns the userid
#@statsd.timer('addItem')
@app.route('/cart/item/add/<userid>', methods=['GET', 'POST'])
def addItem(userid):
    content = request.json

    app.logger.info('the content to add is %s', content)


    jsonobj=getitems(userid)

    if (jsonobj):
        keyindex = 0
        while keyindex < len(jsonobj):
            if (jsonobj[keyindex]['itemid'] == content['itemid']):
                jsonobj[keyindex]['quantity'] = int(jsonobj[keyindex]['quantity']) + int(content['quantity'])
                keyindex=len(jsonobj)+1
                payload=json.dumps(jsonobj)
                try:
                    app.logger.info('inserting cart for %s with following contents %s',userid, json.dumps(content))
                    rConn.set(userid, payload)
                except Exception as e:
                    app.logger.error('Could not insert data %s into redis, error is %s', json.dumps(content), e)
            else:
                keyindex += 1

        if keyindex <= len(jsonobj):
            jsonobj.append(content)
            payload=json.dumps(jsonobj)
            try:
                app.logger.info('inserting cart for %s with following contents %s',userid, json.dumps(content))
                rConn.set(userid, payload)
            except Exception as e:
                app.logger.error('Could not insert data %s into redis, error is %s', json.dumps(content), e)
    else:
        payload=[]
        payload.append(content)
        app.logger.info("added to payload for new insert %s", json.dumps(payload))
        try:
            rConn.set(userid, json.dumps(payload))
        except Exception as e:
            app.logger.error('Could not insert data %s into redis, error is %s', json.dumps(content), e)

    return jsonify({"userid":userid})

#Call to modify entire cart
#
#Must be in following format
#    "cart": [
#        {
#            "description": "red is awesome",
#            "itemid": "250",
#            "name": "redpants",
#            "price": 100,
#            "quantity": 22
#        },
#        {
#            "description": "blue is better than red",
#            "itemid": "7943xxx3659",
#            "name": "bluepants",
#            "price": 10,
#            "quantity": 12
#        }
#    ]
#}
#########


@app.route('/cart/modify/<userid>', methods=['GET', 'POST'])
def replaceCart(userid):
    content = request.json

    app.logger.info('the content to modify is %s', content)


    jsonobj=getitems(userid)

    payload=[]
    for item in content['cart']:
        payload.append(item)

    app.logger.info("added to payload for new insert %s", json.dumps(payload))
    try:
        rConn.set(userid, json.dumps(payload))
    except Exception as e:
        app.logger.error('Could not insert data %s into redis, error is %s', json.dumps(content), e)

    return jsonify({"userid":userid})


#clear item from cart
#minimum content must be {"itemid":"shjhjssr", "quantity":"x"}
@app.route('/cart/item/modify/<userid>', methods=['GET', 'POST'])
def deleteItem(userid):
    content = request.json

    app.logger.info('the item to delete is %s', content)


    jsonobj=getitems(userid)
    if (jsonobj):
        keyindex = 0
        while keyindex < len(jsonobj):
            if (jsonobj[keyindex]['itemid'] == content['itemid']) and (content['quantity']==0):
                del jsonobj[keyindex]
                payload=json.dumps(jsonobj)
                try:
                    app.logger.info('removing item for %s with following contents %s',userid, json.dumps(content))
                    rConn.set(userid, payload)
                except Exception as e:
                    app.logger.error('Could not remove data %s into redis, error is %s', json.dumps(content), e)
                keyindex=len(jsonobj)
            elif (jsonobj[keyindex]['itemid'] == content['itemid']):
                jsonobj[keyindex]['quantity']=content['quantity']
                payload=json.dumps(jsonobj)
                try:
                    app.logger.info('modifying cart for %s with following contents %s',userid, json.dumps(content))
                    rConn.set(userid, payload)
                except Exception as e:
                    app.logger.error('Could not modify cart %s into redis, error is %s', json.dumps(content), e)
                keyindex=len(jsonobj)
            else:
                keyindex += 1
    else:
        app.logger.info('no items in cart found for %s', userid)
        output_message="no cart found for "+userid
        raise FoundIssue(str(output_message), status_code=204)

    return jsonify({"userid":userid})


#clear cart
@app.route('/cart/clear/<userid>', methods=['GET', 'POST'])
def clearCart(userid):

    try:
        app.logger.info("clearing cart for %s", userid)
        rConn.delete(userid)
    except Exception as e:
        app.logger.error('Could not delete %s cart due to %s', userid, e)
        raise FoundIssue(str(e), status_code=500)
#        return('',500)

    return ('',200)

#placeholder for call to order
@app.route('/order/userid')
def order(userid):
    return render_template('hello.html')

#get total amount in users cart
@app.route('/cart/total/<userid>', methods=['GET', 'POST'])
def cartTotal(userid):

    app.logger.info('getting total for %s cart',userid)

    jsonobj=getitems(userid)

    keylist=[]
    for item in jsonobj:
        keylist.append(list(item.keys())[0])

    keyindex=0
    total=0

    while keyindex < len(jsonobj):
        quantity=jsonobj[keyindex]['quantity']
        price=jsonobj[keyindex]['price']
#        quantity=jsonobj[keyindex][keylist[keyindex]]['quantity']
#        price=jsonobj[keyindex][keylist[keyindex]]['price']
        if is_number(quantity) and is_number(price):
            total=total+(float(quantity)*float(price))
        else:
            total=total+0
        keyindex += 1

    app.logger.info("The total calculated is %s", str(total))

    totaljson={"userid":userid, "carttotal":total}

    return jsonify(totaljson)



#baseline route to check is server is live ;-)
@app.route('/')
def hello_world(name=None):
	return render_template('hello.html')


if __name__ == '__main__':

    insertData() #initialize the database with some baseline
    app.run(host='0.0.0.0', port=cartport)
