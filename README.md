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
