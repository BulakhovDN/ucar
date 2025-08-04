import uvicorn as uvicorn
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import sqlite3

app = FastAPI()

DB_NAME = "reviews.db"

positive_words = ["хорош", "люблю"]
negative_words = ["плохо", "ненавиж"]


class ReviewIn(BaseModel):
    text: str


class ReviewOut(BaseModel):
    id: int
    text: str
    sentiment: str
    created_at: str


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()


init_db()


def analyze_sentiment(text: str) -> str:
    text_lower = text.lower()
    if any(word in text_lower for word in positive_words):
        return "positive"
    elif any(word in text_lower for word in negative_words):
        return "negative"
    else:
        return "neutral"


@app.post("/reviews", response_model=ReviewOut)
def create_review(review: ReviewIn):
    sentiment = analyze_sentiment(review.text)
    created_at = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
        (review.text, sentiment, created_at),
    )
    conn.commit()
    review_id = c.lastrowid
    conn.close()

    return ReviewOut(id=review_id, text=review.text, sentiment=sentiment, created_at=created_at)


@app.get("/reviews", response_model=List[ReviewOut])
def get_reviews(sentiment: Optional[str] = Query(None)):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if sentiment:
        c.execute("SELECT id, text, sentiment, created_at FROM reviews WHERE sentiment = ?", (sentiment,))
    else:
        c.execute("SELECT id, text, sentiment, created_at FROM reviews")

    rows = c.fetchall()
    conn.close()

    return [ReviewOut(id=row[0], text=row[1], sentiment=row[2], created_at=row[3]) for row in rows]


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
