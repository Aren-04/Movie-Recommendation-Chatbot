from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import random
from datetime import datetime

app = Flask(__name__)

# Gemini API setup
GEMINI_API_KEY = "AIzaSyCYIg9uqSS-CR7DicNpyQEmxqHleQ6CX7w"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
HEADERS = {"Content-Type": "application/json"}

# Load CSV
df = pd.read_csv("movies.csv")
df.fillna("", inplace=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json["message"].strip().lower()

    # Casual conversation responses
    casual_responses = {
        "hello": "Hey there! 😊 What kind of movies are you in the mood for today?",
        "hi": "Hi! 👋 I’m your movie buddy. Ask me for recommendations anytime!",
        "how are you": "I'm doing great, thanks for asking! 🎬 Ready to help you find some amazing movies.",
        "bye": "Goodbye! 🎥 Hope to see you again soon for more movie fun!",
        "thank you": "You're welcome! 😄 I'm always here for movie suggestions!",
        "what's up": "Not much, just here to help you find some awesome movies! 😎"
    }

    if user_input in casual_responses:
        return jsonify({"response": casual_responses[user_input]})

    # Search by title or genre
    title_matches = df[df["title"].str.contains(user_input, case=False, na=False)]
    genre_matches = df[df["genres"].str.contains(user_input, case=False, na=False)]

    if title_matches.empty and genre_matches.empty:
        return jsonify({"response": "Hmm, I couldn't find any movies related to that. Maybe try asking me about a movie or genre!"})

    # Combine and shuffle matches
    results = pd.concat([title_matches, genre_matches]).drop_duplicates()
    results = results.sample(frac=1).head(5)  # shuffle and pick top 5

    # Create movie summary
    movie_info = ""
    for _, row in results.iterrows():
        movie_info += (
            f"Title: {row['title']}\n"
            f"Genre: {row['genres']}\n"
            f"Rating: {row['vote_average']}/10\n"
            f"Year: {row.get('release_year', 'N/A')}\n"
            f"Cast: {row['cast'][:60]}...\n"
            f"Overview: {row['overview'][:200]}...\n\n"
        )

    # Random prompt variation
    prompt_variations = [
        "Make it sound like you're texting a friend.",
        "Use a cheerful and casual tone.",
        "Be playful but informative.",
        "Use emojis if you feel like it.",
        "Make it sound fun and enthusiastic."
    ]

    prompt = (
        "You're a friendly and helpful movie assistant. "
        "Based on the following movie details, create a fun, engaging, and informal summary (1-2 sentences) for each movie. "
        + random.choice(prompt_variations) +
        " Avoid formatting symbols. Just rephrase the details in a friendly, human way:\n\n" + movie_info
    )

    # Gemini API request
    data = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=data)
        response.raise_for_status()
        result = response.json()
        bot_response = result["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"response": bot_response})
    
    except Exception as e:
        print("Error:", e)
        return jsonify({"response": "Oops, something went wrong! 😢 Please try again."})

if __name__ == "__main__":
    app.run(debug=True)
