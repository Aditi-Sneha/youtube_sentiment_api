from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from googleapiclient.discovery import build
from textblob import TextBlob
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

app = FastAPI(title="YouTube Sentiment Analysis API")
templates = Jinja2Templates(directory="templates")

youtube = build("youtube", "v3", developerKey=API_KEY)


# Sentiment Function
def analyze_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"


# Fetch Comments
def fetch_comments(query, max_comments):
    search_response = youtube.search().list(
        q=query,
        part="id",
        type="video",
        maxResults=1
    ).execute()

    video_id = search_response["items"][0]["id"]["videoId"]

    comments_response = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_comments
    ).execute()

    results = []

    for item in comments_response["items"]:
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        sentiment = analyze_sentiment(comment)

        results.append({
            "text": comment,
            "sentiment": sentiment
        })

    return results


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/", response_class=HTMLResponse)
def analyze(request: Request,
            keyword: str = Form(...),
            count: int = Form(...)):

    comments = fetch_comments(keyword, count)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "comments": comments,
            "keyword": keyword,
            "total": len(comments)
        }
    )


# uvicorn main:app --reload