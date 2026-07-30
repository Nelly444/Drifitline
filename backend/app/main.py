from fastapi import FastAPI

app = FastAPI(title="Driftline")


@app.get("/health")
def health():
    return {"status": "ok"}
