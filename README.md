## Pipeline
Train a model
```
docker run -v ${PWD}:/app rasa/rasa:3.6.20-full train
```
Build and run the containers
```
docker-compose up --build
```
**Note:** the `.env` file must be on root directory and must contain keys in the form `key_name=secret_value`

---
### Additional commands:
To remove all the containers:
```
docker rm $(docker ps -aq)
```

To create the network to connect containers:
```
docker network create my-project
```
