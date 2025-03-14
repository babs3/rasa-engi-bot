## Bot Pipeline
Train a model
```
docker run -v ${PWD}:/app rasa/rasa:3.6.20-full train
```
Start Containers
```
docker-compose up -d --build
```
Pause the containers
```
docker-compose stop
```
Stop and Remove Containers Gracefully
```
docker-compose down
```
Open ```http://localhost:8080/``` to test the bot.

**Note:** the `.env` file must be on root directory and must contain keys in the form `key_name=secret_value`

## Flask-Migrate Workflow for Database Updates
Enter the Flask container
```
docker exec -it rasa-engi-bot-flask-server-1 bash
```
Create migrations folder if needed
```
flask db init
```
After modifying models.py, generate a migration script
```
flask db migrate -m "Describe your change here"
```
Apply the migration to the database
```
flask db upgrade
```
If something goes wrong, undo the last migration:
```
flask db downgrade
```

## How to Visualize the Database?

Access the PostgreSQL container:
```
docker exec -it rasa-engi-bot-db-1 psql -U admin -d chatbotdb
```
Show the structure of the user table:
```
\d user
```
or list all tables:
```
\dt;
```
View all records in the user table:
```
SELECT * FROM "user";
```
Exit PostgreSQL container:
```
\q
```
