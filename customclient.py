import httpx


class CustomClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        # Initialize httpx.Client with verify=False to disable SSL verification
        super().__init__(verify=False, *args, **kwargs)
