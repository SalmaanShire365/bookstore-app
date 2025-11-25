from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
from bson import ObjectId
from config import MON_URI, DATABASE_NAME
import sqlite3
from datetime import datetime
import time
from functools import wraps
import os

app = Flask(__name__)

# MongoDB Connection
try:
    client = MongoClient(MON_URI)
    client.admin.command('ping')
    print("Connected to MongoDB Atlas!")
except Exception as e:
    print(f"MongoDB connection error: {e}")

db = client[DATABASE_NAME]
books_collection = db['books']
reviews_collection = db['reviews']
users_collection = db['users']

DATABASE = 'db/books.db'


def get_db_connection():
    """Create a connection to the SQLite database for logs."""
    # Ensure the db directory exists
    os.makedirs('db', exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows dict-like access to rows
    return conn


def init_logs_table():
    """Initialize the SQLite database with the logs table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                function_name TEXT NOT NULL,
                status TEXT NOT NULL,
                execution_time REAL,
                error_message TEXT,
                details TEXT
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("SQLite logs table initialized successfully")
    except sqlite3.Error as e:
        print(f"Error initializing SQLite logs table: {e}")


def log_to_db(function_name, status, execution_time=None, error_message=None, details=None):
    """Insert a log entry into the SQLite logs table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO logs (timestamp, function_name, status, execution_time, error_message, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        values = (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            function_name,
            status,
            execution_time,
            error_message,
            details
        )
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
    except sqlite3.Error as e:
        print(f"Failed to log to database: {e}")


def timeit(func):
    """Decorator to log function execution time to SQLite."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        function_name = func.__name__
        t1 = time.time()
        
        try:
            result = func(*args, **kwargs)
            t2 = time.time()
            delta_t = t2 - t1
            
            # Log successful execution
            log_to_db(
                function_name=function_name,
                status='success',
                execution_time=delta_t,
                details=f'Executed successfully in {delta_t:.4f} seconds'
            )
            
            return result
            
        except Exception as e:
            # Log error without execution time
            log_to_db(
                function_name=function_name,
                status='error',
                error_message=str(e),
                details=f'Function failed with exception: {str(e)}'
            )
            raise  # Re-raise the exception
    
    return wrapper


def serialize_book(book):
    """Convert MongoDB book document to JSON-serializable format."""
    if book and '_id' in book:
        book['book_id'] = str(book['_id'])
        del book['_id']
    return book


def serialize_review(review):
    """Convert MongoDB review document to JSON-serializable format."""
    if review and '_id' in review:
        review['review_id'] = str(review['_id'])
        del review['_id']
        if 'book_id' in review and isinstance(review['book_id'], ObjectId):
            review['book_id'] = str(review['book_id'])
        if 'user_id' in review and isinstance(review['user_id'], ObjectId):
            review['user_id'] = str(review['user_id'])
    return review



def init_mongodb():
    """Initialize MongoDB with sample data if empty."""
    try:
        count = books_collection.count_documents({})
        if count == 0:
            print("Initializing sample books data in MongoDB...")
            sample_books = [
                {
                    "title": "Clean Code",
                    "publication_year": 2008,
                    "author": "Robert C. Martin",
                    "image_url": "https://m.media-amazon.com/images/I/41xShlnTZTL._SX376_BO1,204,203,200_.jpg"
                },
                {
                    "title": "The Pragmatic Programmer",
                    "publication_year": 1999,
                    "author": "Andrew Hunt",
                    "image_url": "https://m.media-amazon.com/images/I/51W1sBPO7tL._SX380_BO1,204,203,200_.jpg"
                },
                {
                    "title": "Design Patterns",
                    "publication_year": 1994,
                    "author": "Erich Gamma",
                    "image_url": "https://m.media-amazon.com/images/I/51szD9HC9pL._SX395_BO1,204,203,200_.jpg"
                },
                {
                    "title": "You Don't Know JS",
                    "publication_year": 2014,
                    "author": "Kyle Simpson",
                    "image_url": "https://m.media-amazon.com/images/I/41T5H8u7fUL._SX331_BO1,204,203,200_.jpg"
                },
                {
                    "title": "The Clean Coder",
                    "publication_year": 2011,
                    "author": "Robert C. Martin",
                    "image_url": "https://m.media-amazon.com/images/I/51ZWsJc-p5L._SX384_BO1,204,203,200_.jpg"
                },
                {
                    "title": "Code Complete",
                    "publication_year": 2004,
                    "author": "Steve McConnell",
                    "image_url": "https://m.media-amazon.com/images/I/515iO+E+8CL._SX408_BO1,204,203,200_.jpg"
                },
                {
                    "title": "Refactoring",
                    "publication_year": 1999,
                    "author": "Martin Fowler",
                    "image_url": "https://m.media-amazon.com/images/I/41LBzpPXCOL._SX376_BO1,204,203,200_.jpg"
                },
                {
                    "title": "Introduction to Algorithms",
                    "publication_year": 2009,
                    "author": "Thomas H. Cormen",
                    "image_url": "https://m.media-amazon.com/images/I/51fgDX37U7L._SX440_BO1,204,203,200_.jpg"
                },
                {
                    "title": "Cracking the Coding Interview",
                    "publication_year": 2015,
                    "author": "Gayle Laakmann McDowell",
                    "image_url": "https://m.media-amazon.com/images/I/41oYsXjLvZL._SX348_BO1,204,203,200_.jpg"
                },
                {
                    "title": "The Mythical Man-Month",
                    "publication_year": 1975,
                    "author": "Frederick P. Brooks Jr.",
                    "image_url": "https://m.media-amazon.com/images/I/51XnDL5KC+L._SX334_BO1,204,203,200_.jpg"
                },
                {
                    "title": "Eloquent JavaScript",
                    "publication_year": 2018,
                    "author": "Marijn Haverbeke",
                    "image_url": "https://m.media-amazon.com/images/I/51InjRPaF7L._SX377_BO1,204,203,200_.jpg"
                },
                {
                    "title": "Head First Design Patterns",
                    "publication_year": 2004,
                    "author": "Eric Freeman",
                    "image_url": "https://m.media-amazon.com/images/I/51S8VRFN0CL._SX430_BO1,204,203,200_.jpg"
                }
            ]
            result = books_collection.insert_many(sample_books)
            print(f"Inserted {len(result.inserted_ids)} sample books into MongoDB")
        else:
            print(f"MongoDB already initialized with {count} books")
    except Exception as e:
        print(f"Error initializing MongoDB: {e}")


# ==================== BOOKS ENDPOINTS ====================

@app.route('/api/books', methods=['GET'])
@timeit
def get_all_books():
    books = list(books_collection.find())
    book_list = [serialize_book(book.copy()) for book in books]
    return jsonify({'books': book_list})


@app.route('/api/authors', methods=['GET'])
@timeit
def get_all_authors():
    authors = books_collection.distinct("author")
    author_list = [{'name': author} for author in authors]
    return jsonify({'authors': author_list})


@app.route('/api/add_book', methods=['POST'])
@timeit
def add_book():
    data = request.get_json()
    title = data.get('title')
    publication_year = data.get('publication_year')
    author = data.get('author')
    image_url = data.get('image_url', 'https://via.placeholder.com/200x300?text=No+Cover')

    if not title or not author:
        return jsonify({'error': 'Title and author are required'}), 400
    
    book_document = {
        'title': title,
        'publication_year': publication_year,
        'author': author,
        'image_url': image_url
    }

    result = books_collection.insert_one(book_document)
    book_id = str(result.inserted_id)

    return jsonify({
        'message': 'Book added successfully',
        'book_id': book_id
    }), 201


@app.route('/api/search', methods=['GET'])
@timeit
def search_books():
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    search_filter = {
        '$or': [
            {'title': {'$regex': query, '$options': 'i'}},
            {'author': {'$regex': query, '$options': 'i'}}
        ]
    }
    results = list(books_collection.find(search_filter).sort('title', 1))
    books = [serialize_book(book.copy()) for book in results]
    
    return jsonify({'results': books, 'count': len(books)})


@app.route('/api/book/<book_id>', methods=['GET'])
@timeit
def get_book(book_id):
    if not ObjectId.is_valid(book_id):
        return jsonify({'error': 'Invalid book ID format'}), 400
    
    book = books_collection.find_one({'_id': ObjectId(book_id)})

    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    book_dict = serialize_book(book.copy())
    return jsonify({'book': book_dict})


@app.route('/api/book/<book_id>', methods=['DELETE'])
@timeit
def delete_book(book_id):
    if not ObjectId.is_valid(book_id):
        return jsonify({'error': 'Invalid book ID format'}), 400
    
    result = books_collection.delete_one({'_id': ObjectId(book_id)})

    if result.deleted_count == 0:
        return jsonify({'error': 'Book not found'}), 404

    return jsonify({'message': 'Book deleted successfully'})


# ==================== REVIEWS ENDPOINTS ====================

@app.route('/api/reviews', methods=['GET'])
@timeit
def get_all_reviews():
    # Get all reviews from MongoDB.
    reviews = list(reviews_collection.find())
    review_list = [serialize_review(review.copy()) for review in reviews]
    return jsonify({'reviews': review_list})
@app.route('/api/add_review', methods=['POST'])
@timeit
def add_review():
    # Add a new review to MongoDB.
    data = request.get_json()
    book_id = data.get('book_id')
    user = data.get('user_name')
    rating = data.get('rating')
    comment = data.get('review_text')

    review = {
        'book_id': book_id,
        'user': user,
        'rating': rating,
        'comment': comment,
        'review_date': datetime.utcnow().isoformat()
    }
    result = reviews_collection.insert_one(review)
    
    return jsonify({
        'message': 'Review added successfully',
        'review_id': str(result.inserted_id)
    })
@app.route('/api/reviews/book/<book_id>', methods=['GET'])
@timeit
def get_reviews_by_book(book_id):
    # Get all reviews for a specific book
    reviews = list(reviews_collection.find({'book_id': book_id}))
    review_list = [serialize_review(review.copy()) for review in reviews]
    return jsonify({'reviews': review_list, 'count': len(review_list)})

# ==================== LOGS ENDPOINTS ====================

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Retrieve logs from SQLite database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Optional filtering
        status = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)
        
        if status:
            cursor.execute(
                "SELECT * FROM logs WHERE status = ? ORDER BY timestamp DESC LIMIT ?",
                (status, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        
        logs = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return jsonify({'logs': logs, 'count': len(logs)})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs/stats', methods=['GET'])
def get_log_stats():
    """Get statistics about logged functions."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get average execution time per function
        cursor.execute("""
            SELECT 
                function_name,
                COUNT(*) as call_count,
                AVG(execution_time) as avg_time,
                MIN(execution_time) as min_time,
                MAX(execution_time) as max_time,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
            FROM logs
            WHERE execution_time IS NOT NULL
            GROUP BY function_name
            ORDER BY avg_time DESC
        """)
        
        stats = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return jsonify({'stats': stats})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs/clear', methods=['DELETE'])
def clear_logs():
    """Clear all logs from SQLite database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM logs")
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': f'Cleared {deleted_count} log entries'})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500


# ==================== MAIN ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html', current_year=2025)


if __name__ == '__main__':
    # Initialize databases
    init_logs_table()
    init_mongodb()
    
    print("\n" + "="*50)
    print("Application started successfully!")
    print("SQLite logging enabled for all functions")
    print("="*50 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=5000)
