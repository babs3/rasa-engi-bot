## Pipeline
Train a model
```
docker run -v ${PWD}:/app rasa/rasa:3.6.20-full train
```

Build the actions container
```
docker build . -t rasa/rasa-sdk:3.6.2
```

Run the actions container
```
docker run -d -v ${pwd}/actions:/app/actions --net my-project --name action-server rasa/rasa-sdk:3.6.2
```
(Or with the `.env` file)
```
docker run -d -v ${pwd}/actions:/app/actions --net my-project --name action-server --env-file .env rasa/rasa-sdk:3.6.2
```
**Note:** the `.env` file must contain keys in the form `key_name=secret_value`

Talk to the bot in a shell
```
docker run -it -v ${pwd}:/app -p 5005:5005 --net my-project rasa/rasa:3.6.20-full shell
```

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
