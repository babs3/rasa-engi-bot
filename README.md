## Connect to repository
Clone the babs3/rasa-engi-bot repository. Then run the following commands:
```
git config --global user.name "babs3"
git config --global user.email "barbaraema3@gmail.com"
```

Copy the `.env` file and `materials` folder.

`.env` file template:
```
GOOGLE_API_KEY=MY_API_KEY_HERE
CURRENT_CLASS=SCI   # GEE, SCI, LGP or GEE_LGP
APP_DATABASE_USER=MY_DB_USER
APP_DATABASE_PASS=MY_DB_PASSWORD
APP_DATABASE_NAME=MY_DB_NAME
```

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
cd ..
sudo apt install python3.10-venv
python3 -m venv rasa-env
source rasa-env/bin/activate
```

## Bot Pipeline
Generate words and embeddings
```
cd ./rasa-engi-bot
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python generic_words.py
python process_pdfs.py
deactivate
```
Start Containers
```
sudo docker compose up -d
```
Build Containers
```
sudo docker compose up -d --build
```
Pause the containers
```
sudo docker compose stop
```
Stop and Remove Containers Gracefully
```
sudo docker compose down
```
```
sudo docker compose down -v  # Stops all services and removes named volumes
```
Check if containers are running
```
sudo docker container ls -a
```

## Test the bot

### Locally:
Open ```http://localhost/``` to test the bot.
Open ```http://localhost:8081``` to access the Adminer view of db.

### Development Server:
Open ```http://51.20.92.206/``` to test the bot.
Open ```http://51.20.92.206:8081``` to access the Adminer view of db.

### Production Server:

#### GEE
Open ```http://13.61.195.140/``` to test the bot.
Open ```http://13.61.195.140:8081``` to access the Adminer view of db.

#### LGP
Open ```http://13.61.195.140/``` to test the bot.
Open ```http://13.61.195.140:8081``` to access the Adminer view of db.

#### SCI
Open ```http://13.61.195.140/``` to test the bot.
Open ```http://13.61.195.140:8081``` to access the Adminer view of db.


## Useful commands:

Reports information about space on file system
```
df -h
```
Monitor the resources of the Linux operating system in real time
```
htop
```

Gain space by removing all unused containers, networks and images (both dangling and unused).
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

