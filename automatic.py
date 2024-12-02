import subprocess

import modal

PORT = 8000

a1111_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "wget",
        "git",
        "libgl1",
        "libglib2.0-0",
        "google-perftools",  # For tcmalloc
    )
    .env({"LD_PRELOAD": "/usr/lib/x86_64-linux-gnu/libtcmalloc.so.4"})
    .run_commands(
        "git clone --depth 1 https://github.com/Twane70/sd-NAD /webui",
        "python -m venv /webui/venv",
        "cd /webui && . venv/bin/activate && "
        + "python -c 'from modules import launch_utils; launch_utils.prepare_environment()' --xformers",
        gpu="a10g",
    )
    .run_commands(
        "cd /webui && . venv/bin/activate && "
        + "python -c 'from modules import shared_init, initialize; shared_init.initialize(); initialize.initialize()'",
        gpu="a10g",
    )
)

app = modal.App("a1111-NAD", image=a1111_image)


@app.function(
    gpu="h100", #"h100"
    cpu=2,
    memory=1024,
    timeout=3600,
    allow_concurrent_inputs=100,
    container_idle_timeout=20 * 60
    #keep_warm=1,
)
@modal.web_server(port=PORT, startup_timeout=180)
def run():
    START_COMMAND = f"""
cd /webui && \
. venv/bin/activate && \
accelerate launch \
    --num_processes=1 \
    --num_machines=1 \
    --mixed_precision=fp16 \
    --dynamo_backend=inductor \
    --num_cpu_threads_per_process=6 \
    /webui/launch.py \
        --skip-prepare-environment \
        --no-gradio-queue \
        --listen \
        --enable-insecure-extension-access \
        --api \
        --port {PORT}
"""
    subprocess.Popen(START_COMMAND, shell=True)

# https://one-click-studio--a1111-nad-run.modal.run

# https://github.com/thygate/stable-diffusion-webui-depthmap-script
# https://github.com/MackinationsAi/sd-webui-udav2