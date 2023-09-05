from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import os
import base64
import socket
app = FastAPI()
import random
import string 


def generate_random_string(length):
    # Define the characters you want to include in the random string
    characters = string.ascii_letters + string.digits  # You can customize this to include other characters if needed

    # Generate a random string of the specified length
    random_string = ''.join(random.choice(characters) for _ in range(length))
    
    return random_string

# Define allowed programming languages and their respective Docker images
languages = {
    "python": "python:3.9-slim",
    "c": "clang",
    "cpp": "gcc:11",
}

temp_dir="/app/temp/"
hostname=socket.gethostname()
# Function to compile code using Docker container
def compile_code(language, code):
    code=base64.b64decode(code).decode('utf-8')
    #print(code)
    if language not in languages:
        raise HTTPException(status_code=400, detail="Unsupported language")

    # Create a temporary directory to store code
    #with tempfile.TemporaryDirectory() as temp_dir:
    code_file = os.path.join(temp_dir, f"code_{hostname}_{generate_random_string(10)}.{language}")
    output_file = os.path.join(temp_dir, f"output_{hostname}_{generate_random_string(10)}")
    print(code_file,output_file)

    # Write code to a temporary file
    with open(code_file, "w") as file:
        file.write(code)

    # Determine the appropriate Docker image and command
    image = languages[language]
    if language == "python":
        command = ["python", code_file]
    elif language == "c":
        command = ["gcc", code_file, "-o",output_file]
    elif language == "cpp":
        command = ["g++", code_file, "-o", output_file]

    try:
        # Run the Docker container to compile the code
        #print(command)
        output=subprocess.run(command, check=True)
        #print(temp_dir)
        # Read and return the compiled output
        if language == "c" or language == "cpp":
            output=subprocess.run([output_file],stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
        return {"output": output, "hostname":socket.gethostname()}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail="Compilation failed")

class Payload(BaseModel):
    language: str
    code: str

@app.post("/compile")
async def compile_language(payload: Payload):
    try:
        output = compile_code(payload.language, payload.code)
        return {"output": output}
    except HTTPException as e:
        raise e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
