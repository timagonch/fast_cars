import modal
app = modal.App("hello-test")

@app.local_entrypoint()
def ping():
    print("pong")
