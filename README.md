## Pipeline
Train a model
```
docker run -v ${PWD}:/app rasa/rasa:3.6.20-full train
```

Build the actions container
```
docker build . -t rasa/rasa-sdk:3.6.2
```

Run the actions container passing `.env` file contents
```
docker run -d -v ${pwd}/actions:/app/actions --net my-project --name action-server --env-file .env rasa/rasa-sdk:3.6.2
```
**Note:** the `.env` file must be on root directory and must contain keys in the form `key_name=secret_value`

Talk to the bot in a shell
```
docker run -it -v ${pwd}:/app -p 5005:5005 --net my-project rasa/rasa:3.6.20-full shell
```

Talk to the bot on website (open index.html on browser)
```
docker run -it -v ${pwd}:/app -p 5005:5005 --net my-project rasa/rasa:3.6.20-full run --enable-api --cors "*" --connector socketio --debug
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
