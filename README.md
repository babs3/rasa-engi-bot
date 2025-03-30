## Install docker on VM
```
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt install git curl unzip tar make sudo vim wget nano -y
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
newgrp docker
rm get-docker.sh
```

## Virtual Environment
Outside of `rasa-engi-bot` folder create a virtual environment:
```
python3 -m venv rasa-env
```

## Bot Pipeline
Generate words and embeddings
```
source rasa-env/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python generic_words.py
python process_pdfs.py
```
Start Containers
```
docker compose up -d --build
```
Pause the containers
```
docker compose stop
```
Stop and Remove Containers Gracefully
```
docker compose down
```
```
docker-compose down -v  # Stops all services and removes named volumes
```
Check if containers are running
```
docker container ls -a
```
**Note:** the `.env` file must be on root directory and must contain keys in the form `key_name=secret_value`

`.env` file template:
```
GOOGLE_API_KEY=MY_API_KEY_HERE
CURRENT_CLASS=SCI   # GEE, SCI, LGP or GEE_LGP
APP_DATABASE_USER=MY_DB_USER
APP_DATABASE_PASS=MY_DB_PASSWORD
APP_DATABASE_NAME=MY_DB_NAME
```


## Test the bot
### Locally:
Open ```http://localhost/``` to test the bot.
Open ```http://localhost:8081``` to access the Adminer view of db.
### On VM:
Open ```http://13.48.28.234/`` to test the bot.
Open ```http://13.48.28.234:8081``` to access the Adminer view of db.


## Useful commands:

Reports information about space on file system
```
df -h
```
Monitor the resources of the Linux operating system in real time
```
htop
```

Gain space by removing all unused containers, networks, images (both dangling and unused), and optionally, volumes.
```
docker system prune
```

Command to generate requirements
```
pipreqs . --force
```

Upgrade VM volume storage, after update on AWS:
```
sudo growpart /dev/nvme0n1 1
sudo resize2fs /dev/nvme0n1p1
```

Train a model (Only train models locally‼️)
```
docker run -v ${PWD}:/app rasa/rasa:3.6.20-full train
```

