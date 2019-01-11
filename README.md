# cart server

This server is part of the new polygot acme fitness online store.
This will help interact with the catalog, front-end, and make calls to the order services.
It is meant to be run with redis.

#Prerequirements

Python 3.7.2
redis-server 5.0.3
python libraries in requirements.txt


# docker image build & run

git clone directory

If you want to run ALPINE LINUX:

cp Dockerfile.Alpine Dockerfile

docker build -t miniapi .

Ensure redis is installed and running locally on port 6379

docker run -p 5000:5000 miniapi

#api is as follows:

Get the list of items for a user's cart
/cart/items/<userid>, methods=['GET']

Get all the carts for the shop that are in progress
/cart/all, methods=['GET']

Insert an item(s) or create a cart with a specific item(s) for a user
/cart/item/<userid>, methods=['GET', 'POST']

Clear cart
/cart/clear/<userid>, methods=['GET', 'POST']

Get total from the cart
/cart/total/<userid>, methods=['GET', 'POST']
