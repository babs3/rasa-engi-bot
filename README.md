## Pipeline
Train a model
```
docker run -v ${PWD}:/app rasa/rasa:3.6.20-full train
```
When you update your Dockerfile, change dependencies, or modify code and need fresh images.
```
docker-compose up --build
```
When you just want to restart your containers quickly without rebuilding (e.g., after restarting your machine).
```
docker-compose up -d
```
Stop Containers Gracefully
```
docker-compose down
```
**Note:** the `.env` file must be on root directory and must contain keys in the form `key_name=secret_value`

---
### Additional commands:
To remove all stopped containers: ```docker rm $(docker ps -aq)```
