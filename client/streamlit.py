from dotenv import load_dotenv

try:
    load_dotenv("../.env")
except:
    print("Can't load config from .env file!")
    exit(0)
import os
import streamlit as st
import requests
import json

URL = f"http://{os.environ['API_ADDRESS']}/api/{os.environ['API_VERSION']}/generate_captions"

st.title("Image captioning demo")

st.markdown("### Upload your image(s) here")

uploaded_files = st.file_uploader(
    "Choose image file(s)", type=["png", "jpg", "jpeg"], accept_multiple_files=True
)

if uploaded_files:
    filenames = []
    image_files = []
    all_images = []
    for file_index, uploaded_file in enumerate(uploaded_files):
        bytes_data = uploaded_file.read()
        file_extension = uploaded_file.name.split(".")[-1]
        image_files.append(("images", bytes_data))
        filenames.append(f"{file_index}.{file_extension}")
        all_images.append(bytes_data)
    if st.button("Generate caption(s)"):
        with st.spinner("Generating..."):
            response = requests.post(
                URL, data={"filenames": filenames}, files=image_files
            )
        if response.status_code == 200:
            results = json.loads(response.text)
            captions = []
            for result in results:
                captions.append(result["caption"])
            st.image(image=all_images, caption=captions)
        else:
            st.error("Error while generating captions!", icon="🚨")
