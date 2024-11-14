# locaLLM Server

This project is a Local LLM server built with FastAPI. It uses a pre-trained language model from the `transformers` library and runs on a GPU-accelerated environment.

## Prerequisites

- Docker
- Docker Compose
- NVIDIA GPU with CUDA support
- NVIDIA Container Toolkit

## Getting Started

### Step 1: Clone the repository
```bash
git clone https://github.com/yourusername/locallm.git
cd locallm
### Step 2: Build and run the Docker containers

To build and run the Docker containers, use the following command:

```bash
docker-compose up --build
```

This command will build the Docker image and start the locaLLM server. The server will be accessible at `http://localhost:8000`.

### Step 3: Test the API

Once the server is running, you can test the API using a tool like `curl` or Postman. Here's an example using `curl`:

```bash
curl -X POST "http://localhost:8000/generate/" -H "Content-Type: application/json" -d '{"prompt": "Once upon a time", "max_length": 100}'
```

This will send a request to the `/generate/` endpoint with a prompt and a maximum length for the generated text. The server will respond with the generated text.

## Configuration

- **Model**: The server uses the `falcon-40b-instruct` model from the `transformers` library. You can change the model by modifying the `model_name` variable in `app.py`.
- **GPU Acceleration**: The server is configured to use GPU acceleration. Ensure that your environment has a compatible NVIDIA GPU and the necessary drivers installed.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
