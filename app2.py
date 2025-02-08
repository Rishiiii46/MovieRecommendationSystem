from flask import Flask, request, render_template, redirect, url_for
import pickle
import pandas as pd
import requests

app = Flask(__name__)

API_KEY = '8265bd1679663a7ea12ac168da84d2e8'

# Load the movie data and similarity matrix
try:
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    print("✅ Movie data and similarity matrix loaded successfully.")
except Exception as e:
    print(f"❌ Error loading movie data or similarity matrix: {e}")

# Function to fetch movie details from TMDB
def fetch_movie_details(movie_id):
    try:
        response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US', timeout=15)
        response.raise_for_status()  # Ensure we raise an error if there's an HTTP issue
        data = response.json()
    except requests.exceptions.RequestException as e:
        return {
            'poster': "https://via.placeholder.com/500x750?text=No+Image+Available",
            'title': "Title not available",
            'overview': "No overview available",
            'release_date': "Unknown",
            'rating': "No rating",
            'genres': [],
            'runtime': "Unknown"
        }

    poster_url = "https://via.placeholder.com/500x750?text=No+Image+Available"
    if 'poster_path' in data and data['poster_path']:
        poster_url = "https://image.tmdb.org/t/p/w500/" + data['poster_path']

    return {
        'poster': poster_url,
        'title': data.get('title', 'Title not available'),
        'overview': data.get('overview', 'No overview available'),
        'release_date': data.get('release_date', 'Unknown'),
        'rating': data.get('vote_average', 'No rating'),
        'genres': [genre['name'] for genre in data.get('genres', [])],
        'runtime': data.get('runtime', 'Unknown'),
    }

# Function to recommend movies
def recommend(movie):
    movie = movie.lower().strip()  # Normalize input to lowercase for case-insensitive matching
    print(f"Looking for recommendations for: {movie}")  # Debugging print

    # Check if the movie exists in the dataset
    matching_movies = movies[movies['title'].str.lower() == movie]  # Case-insensitive search
    if matching_movies.empty:
        print(f"⚠ Movie '{movie}' not found in dataset!")  # Debugging message
        return None  # Return None if movie is not found

    movie_index = matching_movies.index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]  # Get top 5 similar movies

    recommended_movies = []
    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        movie_details = fetch_movie_details(movie_id)
        recommended_movies.append(movie_details)

    return recommended_movies

# Route for the main page
@app.route('/')
def index():
    movie_titles = movies['title'].values  # Get movie titles from the dataset
    return render_template('index.html', movies=movie_titles)

# Route for recommendations
@app.route('/recommend', methods=['POST'])
def recommend_movies():
    selected_movie = request.form.get('movie')  # Get movie name from dropdown
    search_input = request.form.get('search')  # Get the search input value

    # If search input is filled, use it as the movie name
    if search_input:
        selected_movie = search_input

    # If no movie is selected, go back to the index page
    if not selected_movie:
        print("⚠ No movie selected!")
        return redirect(url_for('index'))

    recommendations = recommend(selected_movie)
    
    if not recommendations:
        return render_template('index.html', movies=movies['title'].values, selected_movie=selected_movie, recommendations=None)

    return render_template('index.html', movies=movies['title'].values, selected_movie=selected_movie, recommendations=recommendations)

if __name__ == '__main__':
    app.run(debug=True)
