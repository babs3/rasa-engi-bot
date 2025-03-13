## Pipeline
Train a model
```
docker run -v ${PWD}:/app rasa/rasa:3.6.20-full train
```
Start Containers
```
docker-compose up -d --build
```
Stop Containers Gracefully
```
docker-compose down
```
Open ```http://localhost:8080/``` to test the bot.

**Note:** the `.env` file must be on root directory and must contain keys in the form `key_name=secret_value`

---
### Additional commands:
To remove all stopped containers: ```docker rm $(docker ps -aq)```
