# Repo stars sniffer
The telegram bot scans for stars changes for repos which user is subscribed to.

# Notes
The bot is under lazy developing stage. I'm picking it as much as I have opportinuty for that. But the plan is to finish it soon. Main funciton is ready and tested. Left things to do:

 - [ ] Pass flag for github if it's presented.
 - [ ] Validate the url when subscribe.

# Run
The start process is pretty simple. Just:

```
docker compose up --build
```

Just fix the `docker-compose.yml` file.

# Configurations.
The `docker-compose.yml` file contains all required configurations.

# Main flags:
 - TELEGRAM_API_TOKEN: the token of telegram bot which you are going to use.
