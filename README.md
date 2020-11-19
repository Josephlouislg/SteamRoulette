# SteamRoulette


### Migration 
```
docker-compose run alembic revision --autogenerate -m "init"
docker-compose run alembic upgrade head

docker-compose run pgpatch  
```