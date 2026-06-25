# sust-hackathon-mock

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Run with Docker

```bash
docker build -t sust-hackathon-mock .
docker run --rm -p 8000:8000 --env-file .env sust-hackathon-mock
```

Open `http://127.0.0.1:8000/health`.

## Deploy on Render

1. Push this repo to GitHub.
2. Create a new Render Web Service.
3. Select Docker as the environment.
4. Add `OPENAI_API_KEY` in Render environment variables.
5. Deploy.

Render will provide the `PORT` environment variable automatically.
