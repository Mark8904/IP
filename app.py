from flask import Flask, render_template, request
import subprocess
import threading
import time
import re

app = Flask(__name__)

# Function to run Serveo in the background
def run_serveo(localhost_port, output_file):
    serveo_command = (
        f"ssh -o StrictHostKeyChecking=no "
        f"-o UserKnownHostsFile=/dev/null "
        f"-R 80:localhost:{localhost_port} serveo.net"
    )
    with open(output_file, 'w') as out:
        subprocess.Popen(serveo_command, shell=True, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)

# Function to extract the public URL from Serveo's output
def get_public_url(output_file):
    public_url = None
    timeout = time.time() + 15  # 15 seconds timeout

    while not public_url and time.time() < timeout:
        with open(output_file, 'r') as out:
            lines = out.readlines()
            for line in lines:
                # Remove ANSI escape sequences and extract the URL
                cleaned_line = re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', line)
                match = re.search(r'https://[^\s]+.serveo.net', cleaned_line)
                if match:
                    public_url = match.group(0)
                    break
        time.sleep(1)  # Wait a bit before checking again

    return public_url

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        localhost_url = request.form['localhost_url']
        localhost_port = localhost_url.split(':')[-1]
        output_file = f"serveo_{localhost_port}.log"

        # Run Serveo in a background thread
        thread = threading.Thread(target=run_serveo, args=(localhost_port, output_file))
        thread.start()

        # Wait and retrieve the public URL
        public_url = get_public_url(output_file)

        if public_url:
            return render_template('index.html', public_url=public_url)
        else:
            return render_template('index.html', error="Could not retrieve the public URL. Please try again.")
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
