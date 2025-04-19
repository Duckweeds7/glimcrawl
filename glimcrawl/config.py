import os

SAVE_DIR = os.path.join(os.path.dirname(__file__), "downloaded_images")
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)



