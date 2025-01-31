import os
import csv
import pandas as pd
from flask import Flask, request, render_template, send_file, jsonify
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

app = Flask(__name__)

def extract_video_id(video_url):
    """Extracts video ID from YouTube URL"""
    if "youtube.com/watch?v=" in video_url:
        return video_url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in video_url:
        return video_url.split("youtu.be/")[1].split("?")[0]
    return None

def fetch_comments(video_id):
    """Fetches all comments from a YouTube video"""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    comments = []
    next_page_token = None

    while True:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100,
            pageToken=next_page_token
        ).execute()

        for item in response["items"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "Author": snippet["authorDisplayName"],
                "Comment": snippet["textDisplay"],
                "Date": snippet["publishedAt"],
                "Likes": snippet["likeCount"]
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break  # No more pages

    return comments

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        video_url = request.form.get("video_url") # type: ignore

        if not video_url:
            return render_template("index.html", error="Please enter a YouTube URL.")

        video_id = extract_video_id(video_url)
        if not video_id:
            return render_template("index.html", error="Invalid YouTube URL.")

        comments = fetch_comments(video_id)

        # Save to CSV
        csv_filename = f"comments_{video_id}.csv"
        df = pd.DataFrame(comments)
        df.to_csv(csv_filename, index=False)

        return send_file(csv_filename, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
