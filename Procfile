web: gunicorn --bind 0.0.0.0:$PORT simple_web_test:app
worker: python kufar_notifications.py worker
original_web: python kufar_notifications.py web
test_web: python simple_web_test.py
