import os
from app import create_app

app = create_app()  # <- biến top-level để có thể dùng flask CLI nếu cần

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"Starting app on http://{host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
