from fastapi import FastAPI, HTTPException
import subprocess
import tempfile
import os
import base64

app = FastAPI()

# Define allowed programming languages and their respective Docker images
languages = {
    "python": "python:3.9-slim",
    "c": "gcc:11",
    "cpp": "gcc:11",
}
temp_dir="temp"
# Function to compile code using Docker container
def compile_code(language, code):
    code=base64.b64decode(code).decode('utf-8')
    print(code)
    if language not in languages:
        raise HTTPException(status_code=400, detail="Unsupported language")

    # Create a temporary directory to store code
    #with tempfile.TemporaryDirectory() as temp_dir:
    code_file = os.path.join(temp_dir, f"code.{language}")
    print(code_file)

    # Write code to a temporary file
    with open(code_file, "w") as file:
        file.write(code)

    # Determine the appropriate Docker image and command
    image = languages[language]
    if language == "python":
        command = ["python", code_file]
    elif language == "c":
        command = ["gcc", code_file, "-o", os.path.join(temp_dir, "output")]
    elif language == "cpp":
        command = ["g++", code_file, "-o", os.path.join(temp_dir, "output")]

    try:
        # Run the Docker container to compile the code
        output=subprocess.run(["docker", "run", "--rm", "-v", f"./{temp_dir}:/{temp_dir}", image] + command, check=True)
        print(temp_dir)
        # Read and return the compiled output
        if language == "c" or language == "cpp":
             output = subprocess.run(["sh", os.path.join(temp_dir, "output")], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail="Compilation failed")

@app.post("/compile/{language}")
async def compile_language(language: str, code: str):
    try:
        output = compile_code(language, code)
        return {"output": output}
    except HTTPException as e:
        raise e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
