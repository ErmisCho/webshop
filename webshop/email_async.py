from concurrent.futures import ThreadPoolExecutor

# Keep it small to avoid exhausting your dyno/container
executor = ThreadPoolExecutor(max_workers=4)
