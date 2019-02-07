# cart server

This server is part of the new polygot acme fitness online store.
This will help interact with the catalog, front-end, and make calls to the order services.
It is meant to be run with redis.

## pre-requirements

* Python 3.7.2
* redis-server 5.0.3
* python libraries in requirements.txt


## docker image build & run

```
git clone directory
docker build -t acmeshop-cart .
```

Ensure redis is installed and running locally on port 6379

```
docker run -p 5000:5000 acmeshop-cart
```

## api is as follows:

**/cart/items/\<userid\>, methods=['GET']**<br>

   Get the list of items for a user's cart<br>


**/cart/items/\<userid\>, methods=['GET']**<br>

   Get all the carts for the shop that are in progress<br>


**/cart/all, methods=['GET']**<br>


**/cart/item/\<userid\>, methods=['GET', 'POST']**<br>

  Insert an item(s) or create a cart with a specific item(s) for a user<br>


**/cart/clear/\<userid\>, methods=['GET', 'POST']**<br>

  Clear cart for specific user <br>

**/cart/total/<userid>, methods=['GET', 'POST']**<br>

  Get total from the cart
