up-streamlit:
	sudo docker compose up -d streamlit-app

build-streamlit:
	sudo docker compose build streamlit-app

down-streamlit:
	sudo docker compose down streamlit-app