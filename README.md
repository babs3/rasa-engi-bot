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


## How to Visualize the Database?

Access the PostgreSQL container:
```
docker exec -it rasa-engi-bot-db-1 psql -U admin -d chatbotdb
```
Show the structure of the user table:
```
\d user
```
View all records in the user table:
```
SELECT * FROM "user";
```
Exit PostgreSQL container:
```
\q
```
