// Load books when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadAllBooks();
    loadAllReviews(); // FIXED: Changed from showAllReviews to loadAllReviews
    
    // Enable Enter key for search
    document.getElementById('searchBox').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchBooks();
        }
    });
});

/**
 * Load all books from the database
 */
function loadAllBooks() {
    const bookshelf = document.getElementById('bookshelf');
    bookshelf.innerHTML = '<div class="loading">Loading your books...</div>';

    fetch('/api/books')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                bookshelf.innerHTML = `<div class="empty-state"><h3>Error loading books</h3><p>${data.error}</p></div>`;
                return;
            }

            displayBooks(data.books);
        })
        .catch(error => {
            console.error('Error:', error);
            bookshelf.innerHTML = '<div class="empty-state"><h3>Error loading books</h3><p>Please try again later.</p></div>';
        });
}

/**
 * Display books in the bookshelf
 */
function displayBooks(books) {
    const bookshelf = document.getElementById('bookshelf');
    const bookCount = document.getElementById('bookCount');

    if (books.length === 0) {
        bookshelf.innerHTML = `
            <div class="empty-state">
                <h3>No books found</h3>
                <p>Start building your collection by adding books above!</p>
            </div>
        `;
        bookCount.textContent = '0 books';
        return;
    }

    bookCount.textContent = `${books.length} book${books.length !== 1 ? 's' : ''} in collection`;

    let html = '';
    books.forEach(book => {
        html += `
            <div class="book-card" title="Click for details">
                <img src="${book.image_url || 'https://via.placeholder.com/200x300?text=No+Cover'}" 
                     alt="${book.title}" 
                     class="book-cover"
                     onerror="this.src='https://via.placeholder.com/200x300?text=No+Cover'">
                <div class="book-info">
                    <div class="book-title">${escapeHtml(book.title)}</div>
                    <div class="book-author">by ${escapeHtml(book.author || 'Unknown Author')}</div>
                    <div class="book-year">${book.publication_year || 'Year N/A'}</div>
                    <div style="font-size: 0.7rem; color: #999; margin-top: 0.5rem;">ID: ${book.book_id}</div>
                </div>
            </div>
        `;
    });

    bookshelf.innerHTML = html;
}

/**
 * Search for books by title or author
 */
function searchBooks() {
    const query = document.getElementById('searchBox').value.trim();
    const resultsDiv = document.getElementById('searchResults');

    if (!query) {
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
        return;
    }

    resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
    resultsDiv.style.display = 'block';

    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                resultsDiv.innerHTML = `<p class="error">Error: ${data.error}</p>`;
                return;
            }

            if (data.results.length === 0) {
                resultsDiv.innerHTML = `
                    <h3>No results found for "${escapeHtml(query)}"</h3>
                    <p>Try searching with different keywords.</p>
                `;
                return;
            }

            let html = `<h3>Found ${data.count} result${data.count !== 1 ? 's' : ''} for "${escapeHtml(query)}"</h3>`;
            html += '<div class="search-results-grid">';
            
            data.results.forEach(book => {
                html += `
                    <div class="search-result-item">
                        <img src="${book.image_url || 'https://via.placeholder.com/80x120?text=No+Cover'}" 
                             alt="${book.title}"
                             class="search-result-img"
                             onerror="this.src='https://via.placeholder.com/80x120?text=No+Cover'">
                        <div class="search-result-info">
                            <strong>${escapeHtml(book.title)}</strong>
                            <div>by ${escapeHtml(book.author || 'Unknown')}</div>
                            <div class="search-result-year">${book.publication_year || 'N/A'}</div>
                            <div style="font-size: 0.75rem; color: #999;">ID: ${book.book_id}</div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            resultsDiv.innerHTML = html;
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerHTML = '<p class="error">Error searching books. Please try again.</p>';
        });
}

/**
 * Add a new book to the database
 */
function addBook() {
    const title = document.getElementById('bookTitle').value.trim();
    const author = document.getElementById('bookAuthor').value.trim();
    const year = document.getElementById('publicationYear').value.trim();
    const imageUrl = document.getElementById('imageUrl').value.trim();

    // Validation
    if (!title || !author || !year) {
        alert('Please fill in title, author, and publication year');
        return;
    }

    if (year && (isNaN(year) || year < 1000 || year > new Date().getFullYear() + 10)) {
        alert('Please enter a valid publication year');
        return;
    }

    const bookData = {
        title: title,
        author: author,
        publication_year: parseInt(year),
        image_url: imageUrl || 'https://via.placeholder.com/200x300?text=No+Cover'
    };

    // Disable button to prevent double submission
    const addButton = event.target;
    addButton.disabled = true;
    addButton.textContent = 'Adding...';

    fetch('/api/add_book', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(bookData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Book added successfully!');
            
            // Clear form
            document.getElementById('bookTitle').value = '';
            document.getElementById('bookAuthor').value = '';
            document.getElementById('publicationYear').value = '';
            document.getElementById('imageUrl').value = '';
            
            // Clear search results
            document.getElementById('searchResults').innerHTML = '';
            document.getElementById('searchResults').style.display = 'none';
            document.getElementById('searchBox').value = '';
            
            // Reload books to show the new addition
            loadAllBooks();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error adding book. Please try again.');
    })
    .finally(() => {
        // Re-enable button
        addButton.disabled = false;
        addButton.textContent = 'Add to Shelf';
    });
}

/**
 * Escape HTML to prevent XSS attacks
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Clear search results
 */
function clearSearch() {
    document.getElementById('searchBox').value = '';
    document.getElementById('searchResults').innerHTML = '';
    document.getElementById('searchResults').style.display = 'none';
}

function addReview() {
    const bookId = document.getElementById('reviewBookId').value.trim(); 
    const userName = document.getElementById('reviewUserName').value.trim(); 
    const rating = document.getElementById('reviewRating').value.trim();
    const reviewText = document.getElementById('reviewText').value.trim(); 

    // Validation
    if (!bookId || !userName || !rating || !reviewText) {
        alert('Please fill in all fields');
        return;
    }

    const ratingNum = parseInt(rating);
    if (isNaN(ratingNum) || ratingNum < 1 || ratingNum > 5) {
        alert('Rating must be between 1 and 5');
        return;
    }

 
    const reviewData = {
        book_id: bookId,
        user_name: userName,
        rating: ratingNum,
        review_text: reviewText 
    };

    // Disable button
    const addButton = event.target;
    addButton.disabled = true;
    addButton.textContent = 'Submitting...';

    fetch('/api/add_review', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(reviewData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Review added successfully!');
            
            // Clear form
            document.getElementById('reviewBookId').value = '';
            document.getElementById('reviewUserName').value = '';
            document.getElementById('reviewRating').value = '';
            document.getElementById('reviewText').value = '';
            
            // Reload reviews
            loadAllReviews();
        }
    })
    .catch(error => {
        console.error('Error adding review:', error);
        alert('Error adding review. Please try again.');
    })
    .finally(() => {
        // Re-enable button
        addButton.disabled = false;
        addButton.textContent = 'Submit Review';
    });
}

// Function to fetch and display all reviews
function loadAllReviews() {
    fetch('/api/reviews')
        .then(response => response.json())
        .then(data => {
            const reviewList = document.getElementById('reviewList');
            reviewList.innerHTML = '';  // Clear existing reviews

            data.reviews.forEach(review => {
                const reviewElement = document.createElement('div');
                reviewElement.classList.add('review');
                reviewElement.innerHTML = `
                    <h3>Book ID: ${review.book_id}</h3>
                    <p>User: ${review.user}</p>
                    <p>Rating: ${review.rating}</p>
                    <p>Comment: ${review.comment}</p>
                `;
                reviewList.appendChild(reviewElement);
            });
        })
        .catch(error => {
            console.error('Error fetching reviews:', error);
        });
}

