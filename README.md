# Logit-bin

This repository contains code which I used to deploy a simple pastebin to Heroku. Just clone it and start using it.

## Usage

### Initial

```bash
$ git clone git@github.com:yasoob/logit-bin.git
$ cd logit-bin
$ foreman start
$ # in order to deploy it to heroku
$ # I am not including the steps to 
$ # initialize a heroku app
$ git push heroku master
```

### Database

```bash
$ heroku addons:add heroku-postgresql:dev
-----> Adding heroku-postgresql:dev to some-app-name... done, v196 (free)
Attached as HEROKU_POSTGRESQL_COLOR
Database has been created and is available
$ heroku pg:promote HEROKU_POSTGRESQL_COLOR
$ heroku run python
```

and in the Python REPL:

```python
>>> from app import db
>>> db.create_all()
```

##TODO:
- add syntax highlighting using pygments.
- allow line highlighting using target identifier like gist.
- add facebook and twitter sharing
- introduce more features
