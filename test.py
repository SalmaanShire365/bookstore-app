import unittest
import json
import os
import sys
import sqlite3
from app import app, init_db, DATABASE

class BookshelfIntegrationTests(unittest.TestCase):
    """Integration tests for the Bookshelf application"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database once before all tests"""
        cls.test_db = 'test_books.db'
        
    def setUp(self):
        """Set up test client and test database before each test"""
        # Use test database
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        # Create fresh test database
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # Temporarily override DATABASE constant
        import app as app_module
        self.original_db = app_module.DATABASE
        app_module.DATABASE = self.test_db
        
        # Initialize test database
        init_db()
        
    def tearDown(self):
        """Clean up after each test"""
        import app as app_module
        app_module.DATABASE = self.original_db
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    # ==================== GET ALL BOOKS TESTS ====================
    
    def test_get_all_books_success(self):
        """Test retrieving all books from database"""
        response = self.app.get('/api/books')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('books', data)
        self.assertIsInstance(data['books'], list)
        self.assertGreater(len(data['books']), 0)
        
        # Verify book structure
        first_book = data['books'][0]
        self.assertIn('book_id', first_book)
        self.assertIn('title', first_book)
        self.assertIn('author', first_book)
        self.assertIn('publication_year', first_book)
        self.assertIn('image_url', first_book)
    
    def test_get_all_books_contains_sample_data(self):
        """Test that database contains the sample books"""
        response = self.app.get('/api/books')
        data = json.loads(response.data)
        
        titles = [book['title'] for book in data['books']]
        self.assertIn('Clean Code', titles)
        self.assertIn('The Pragmatic Programmer', titles)
        self.assertGreaterEqual(len(titles), 10)
    
    # ==================== ADD BOOK TESTS ====================
    
    def test_add_book_with_all_fields(self):
        """Test adding a book with title, author, year, and image URL"""
        new_book = {
            'title': 'Test Driven Development',
            'author': 'Kent Beck',
            'publication_year': 2002,
            'image_url': 'https://example.com/tdd.jpg'
        }
        
        response = self.app.post('/api/add_book',
                                data=json.dumps(new_book),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('book_id', data)
        
        # Verify book was actually added to database
        get_response = self.app.get('/api/books')
        books_data = json.loads(get_response.data)
        
        added_book = next((b for b in books_data['books'] 
                          if b['title'] == 'Test Driven Development'), None)
        
        self.assertIsNotNone(added_book)
        self.assertEqual(added_book['author'], 'Kent Beck')
        self.assertEqual(added_book['publication_year'], 2002)
        self.assertEqual(added_book['image_url'], 'https://example.com/tdd.jpg')
    
    def test_add_book_without_image_url(self):
        """Test adding a book without an image URL (should use placeholder)"""
        new_book = {
            'title': 'Domain-Driven Design',
            'author': 'Eric Evans',
            'publication_year': 2003
        }
        
        response = self.app.post('/api/add_book',
                                data=json.dumps(new_book),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        # Verify placeholder image was used
        get_response = self.app.get('/api/books')
        books_data = json.loads(get_response.data)
        
        added_book = next((b for b in books_data['books'] 
                          if b['title'] == 'Domain-Driven Design'), None)
        
        self.assertIsNotNone(added_book)
        self.assertIn('placeholder', added_book['image_url'].lower())
    
    def test_add_book_missing_required_fields(self):
        """Test adding a book without required fields returns error"""
        # Missing author
        incomplete_book = {
            'title': 'Incomplete Book',
            'publication_year': 2020
        }
        
        response = self.app.post('/api/add_book',
                                data=json.dumps(incomplete_book),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_add_multiple_books(self):
        """Test adding multiple books increases book count"""
        initial_response = self.app.get('/api/books')
        initial_count = len(json.loads(initial_response.data)['books'])
        
        books_to_add = [
            {'title': 'Book 1', 'author': 'Author 1', 'publication_year': 2020},
            {'title': 'Book 2', 'author': 'Author 2', 'publication_year': 2021},
            {'title': 'Book 3', 'author': 'Author 3', 'publication_year': 2022}
        ]
        
        for book in books_to_add:
            response = self.app.post('/api/add_book',
                                    data=json.dumps(book),
                                    content_type='application/json')
            self.assertEqual(response.status_code, 201)
        
        final_response = self.app.get('/api/books')
        final_count = len(json.loads(final_response.data)['books'])
        
        self.assertEqual(final_count, initial_count + 3)
    
    # ==================== SEARCH TESTS ====================
    
    def test_search_by_title_exact_match(self):
        """Test searching for books by exact title"""
        response = self.app.get('/api/search?q=Clean Code')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('results', data)
        self.assertGreater(len(data['results']), 0)
        
        # Should find "Clean Code" and "The Clean Coder"
        titles = [book['title'] for book in data['results']]
        self.assertTrue(any('Clean Code' in title for title in titles))
    
    def test_search_by_title_partial_match(self):
        """Test searching for books by partial title"""
        response = self.app.get('/api/search?q=patterns')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertGreater(len(data['results']), 0)
        
        # Should find books with "patterns" in title
        for book in data['results']:
            self.assertTrue('patterns' in book['title'].lower())
    
    def test_search_by_author_full_name(self):
        """Test searching for books by full author name"""
        response = self.app.get('/api/search?q=Robert C. Martin')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertGreater(len(data['results']), 0)
        
        # Should find books by Robert C. Martin
        for book in data['results']:
            self.assertEqual(book['author'], 'Robert C. Martin')
    
    def test_search_by_author_partial_name(self):
        """Test searching for books by partial author name"""
        response = self.app.get('/api/search?q=Martin')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertGreater(len(data['results']), 0)
        
        # Should find books with "Martin" in author name
        for book in data['results']:
            self.assertTrue('martin' in book['author'].lower())
    
    def test_search_case_insensitive(self):
        """Test that search is case-insensitive"""
        response_lower = self.app.get('/api/search?q=clean code')
        response_upper = self.app.get('/api/search?q=CLEAN CODE')
        response_mixed = self.app.get('/api/search?q=ClEaN CoDe')
        
        data_lower = json.loads(response_lower.data)
        data_upper = json.loads(response_upper.data)
        data_mixed = json.loads(response_mixed.data)
        
        # All should return the same results
        self.assertEqual(len(data_lower['results']), len(data_upper['results']))
        self.assertEqual(len(data_lower['results']), len(data_mixed['results']))
    
    def test_search_nonexistent_book(self):
        """Test searching for a book that doesn't exist returns empty results"""
        response = self.app.get('/api/search?q=NonexistentBook12345')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 0)
        self.assertEqual(data['count'], 0)
    
    def test_search_empty_query(self):
        """Test searching with empty query returns error"""
        response = self.app.get('/api/search?q=')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_search_no_query_parameter(self):
        """Test searching without query parameter returns error"""
        response = self.app.get('/api/search')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_search_returns_all_book_fields(self):
        """Test that search results include all book fields"""
        response = self.app.get('/api/search?q=JavaScript')
        data = json.loads(response.data)
        
        if len(data['results']) > 0:
            book = data['results'][0]
            self.assertIn('book_id', book)
            self.assertIn('title', book)
            self.assertIn('author', book)
            self.assertIn('publication_year', book)
            self.assertIn('image_url', book)
    
    # ==================== GET SPECIFIC BOOK TEST ====================
    
    def test_get_specific_book_by_id(self):
        """Test retrieving a specific book by ID"""
        # First, get all books to find a valid ID
        response = self.app.get('/api/books')
        data = json.loads(response.data)
        
        if len(data['books']) > 0:
            book_id = data['books'][0]['book_id']
            
            # Get specific book
            response = self.app.get(f'/api/book/{book_id}')
            self.assertEqual(response.status_code, 200)
            
            book_data = json.loads(response.data)
            self.assertIn('book', book_data)
            self.assertEqual(book_data['book']['book_id'], book_id)
    
    def test_get_nonexistent_book_returns_404(self):
        """Test getting a nonexistent book returns 404"""
        response = self.app.get('/api/book/99999')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    # ==================== AUTHORS TEST ====================
    
    def test_get_all_authors(self):
        """Test retrieving all unique authors"""
        response = self.app.get('/api/authors')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('authors', data)
        self.assertIsInstance(data['authors'], list)
        self.assertGreater(len(data['authors']), 0)
    
    # ==================== INTEGRATION WORKFLOW TEST ====================
    
    def test_complete_workflow(self):
        """Test complete workflow: add book, search for it, retrieve it"""
        # Step 1: Add a new book
        new_book = {
            'title': 'Workflow Test Book',
            'author': 'Test Author',
            'publication_year': 2024,
            'image_url': 'https://example.com/test.jpg'
        }
        
        add_response = self.app.post('/api/add_book',
                                     data=json.dumps(new_book),
                                     content_type='application/json')
        self.assertEqual(add_response.status_code, 201)
        
        # Step 2: Search for the newly added book
        search_response = self.app.get('/api/search?q=Workflow Test')
        search_data = json.loads(search_response.data)
        self.assertEqual(len(search_data['results']), 1)
        
        found_book = search_data['results'][0]
        self.assertEqual(found_book['title'], 'Workflow Test Book')
        self.assertEqual(found_book['author'], 'Test Author')
        
        # Step 3: Retrieve the book by ID
        book_id = found_book['book_id']
        get_response = self.app.get(f'/api/book/{book_id}')
        get_data = json.loads(get_response.data)
        
        self.assertEqual(get_data['book']['title'], 'Workflow Test Book')
        self.assertEqual(get_data['book']['image_url'], 'https://example.com/test.jpg')


def run_tests():
    """Run all tests and print results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(BookshelfIntegrationTests)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
