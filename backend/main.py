from fastapi import FastAPI

app = FastAPI()

@app.get(”/”)
def root():
return {“status”: “AI Finance backend is running”}
