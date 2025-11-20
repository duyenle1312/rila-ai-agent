# README File

## Install venv

```shell
python3 -m venv .venv
source .venv/bin/activate
```

Check ```which python```

## Install requirements

```shell
pip3 install -r requirements.txt
```

## Run the app

```shell
python -m uvicorn app.main:app --reload
```
