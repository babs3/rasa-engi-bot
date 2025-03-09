```
docker run -v ${PWD}:/app rasa/rasa:3.6.20-full train
```
```
docker build . -t rasa/rasa-sdk:3.6.2
```
```
docker run -d -v ${pwd}/actions:/app/actions --net my-project --name action-server rasa/rasa-sdk:3.6.2
```
```
docker run -it -v ${pwd}:/app -p 5005:5005 --net my-project rasa/rasa:3.6.20-full shell
```
To remove all the containers:
```
docker rm $(docker ps -aq)
```