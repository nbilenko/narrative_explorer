# Run a test server.
import app
import config

bk_app = app.create_app(config)

with bk_app.app_context():
    books_queue = app.tasks.get_books_queue()

if __name__ == '__main__':
	bk_app.run(host='127.0.0.1', port=8080, debug=True)