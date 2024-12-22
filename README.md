# Oauth Integration

**Description:**

This full-stack app integrates OAuth authentication with Airtable, HubSpot, and Notion. The FastAPI backend handles secure authentication and API interactions, while the React frontend offers a user-friendly interface. Docker ensures easy deployment and scalability, streamlining workflows across platforms.

**Getting Started**

1.  **Prerequisites:**

    *   Python 3.x ([https://www.python.org/downloads/](https://www.google.com/url?sa=E&source=gmail&q=https://www.python.org/downloads/))
    *   Node.js and npm ([https://nodejs.org/](https://www.google.com/url?sa=E&source=gmail&q=https://nodejs.org/))
    *   Docker ([https://www.docker.com/](https://www.google.com/url?sa=E&source=gmail&q=https://www.docker.com/)) (optional, but recommended)

2.  **Configuration:**

    *   Create a file named `.env` in the root directory of your project.
    *   Copy the contents of `.env.example` to `.env`, replacing the placeholders with your actual values (e.g., API keys, database credentials).

3.  **Backend Setup:**

    *   Open a terminal in the `backend` directory.
    *   Create a virtual environment:

        ```bash
        python -m venv venv
        ```

    *   Activate the virtual environment:

        ```bash
        source venv/bin/activate  # Linux/macOS
        venv\Scripts\activate.bat  # Windows
        ```

    *   Install required dependencies:

        ```bash
        pip install -r requirements.txt
        ```

4.  **Frontend Setup:**

    *   Open a terminal in the `frontend` directory.
    *   Install dependencies:

        ```bash
        npm install
        ```

**Running the Application**

**Option 1: Local Development**

1.  **Backend:**

    *   Start the backend server in the `backend` directory:

        ```bash
        uvicorn main:app --reload
        ```

    *   This will start the backend API server in development mode, automatically reloading on code changes.

2.  **Frontend:**

    *   Start the frontend development server:

        ```bash
        npm run start
        ```

    *   This will typically launch the frontend at `http://localhost:3000` (adjust the port if necessary) and watch for changes in the frontend code.

**Redis Setup:**

*   **Local Redis Installation (If not using Docker Compose):** Ensure Redis is installed and running locally. You might need to start the Redis server manually after installation. Check your operating system's instructions for starting Redis. Usually, it's something like `redis-server`.
*   **Docker Compose (Recommended):** If you're using Docker Compose, Redis will be started automatically as part of the `docker-compose up` command.


**Option 2: Using Docker (Recommended for Production)**

1.  **Build and Run:**

    *   From the root directory of your project:

        ```bash
        docker-compose up --build
        ```

    *   This will build the Docker images for your backend and frontend services, and then start them together.
