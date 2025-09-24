# modal_app.py
import shlex
import subprocess
from pathlib import Path
import modal

# Path to your local Streamlit script
streamlit_script_local_path = Path(__file__).parent / "streamlit_app.py"
streamlit_script_remote_path = "/root/streamlit_app.py"

# Define container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "streamlit~=1.35.0",   # stable tested version
        "numpy~=1.26.4",
        "pandas~=2.2.2",
        "plotly>=5.20",
        "supabase>=2",
        "python-dotenv>=1.0",
    )
    .add_local_file(streamlit_script_local_path, streamlit_script_remote_path)
)

# Create Modal app
app = modal.App(name="fastest-cars-dashboard", image=image)

# Check that your Streamlit script actually exists locally
if not streamlit_script_local_path.exists():
    raise RuntimeError("⚠️ streamlit_app.py not found! Place it in the same folder as modal_app.py")

# Function: run Streamlit inside container, expose port 8000
@app.function(secrets=[modal.Secret.from_name("supabase-creds")])
@modal.web_server(8000)  # Modal will map port 8000 → public URL
def serve():
    target = shlex.quote(str(streamlit_script_remote_path))
    cmd = (
        f"streamlit run {target} "
        "--server.port 8000 "
        "--server.enableCORS=false "
        "--server.enableXsrfProtection=false"
    )
    subprocess.Popen(cmd, shell=True)
