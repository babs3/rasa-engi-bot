## Bot Pipeline
Set CURRENT_CLASS in .env file
```
CURRENT_CLASS=GEE   # GEE, SCI, LGP
```
Create vector_store folder
```
python process_pdfs.py
```
Create generic_words.json file (need to use lower python version because of spacy)
```
py -3.10 generic_words.py
```
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
If I need to change the database configuration:
```
docker-compose down -v  # Stops all services and removes named volumes
```

Open ```http://localhost:8501/``` to test the bot.

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
**NOTE:** If you get some error like ```ERROR [flask_migrate] Error: Can't locate revision identified by [revision-id]```, just run the following:
```
flask db revision --rev-id [revision-id]
```
```
flask db migrate
```
```
flask db upgrade
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
Drop all rows from the table:
```
DELETE FROM "user";
```
Exit PostgreSQL container:
```
\q
```

## Virtual Environment

Activate Virtual Environment
```
conda activate rasa-env
```
