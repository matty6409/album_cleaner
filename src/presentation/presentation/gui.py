import streamlit as st
import os
from application.cleaner_service import CleanerService
from infrastructure.settings import Settings
from tqdm import tqdm
import logging

st.set_page_config(page_title="Album Cleaner", layout="centered")
st.title("🎵 Album Cleaner")

# Set up logging
def setup_logger():
    logger = logging.getLogger("album_cleaner")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("album_cleaner.log")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(fh)
    return logger

logger = setup_logger()

# Sidebar options
base_path = st.text_input("Base path to albums", value="/path/to/albums")
to_new_dir = st.checkbox("Save to cleaned/ folder (otherwise rename in place)", value=True)
language = st.selectbox("Language for official track names", ["English", "Traditional Chinese"])
prompt_path = st.text_input("Prompt YAML path", value="prompts/cleaner_prompt.yaml")

if st.button("Run Cleaner"):
    if not os.path.exists(base_path):
        st.error(f"Path not found: {base_path}")
    else:
        settings = Settings()
        service = CleanerService(prompt_path=prompt_path, settings=settings, to_new_dir=to_new_dir)
        albums = [a for a in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, a))]
        progress = st.progress(0, text="Starting...")
        log_lines = []
        for i, album in enumerate(albums):
            album_path = os.path.join(base_path, album)
            st.write(f"Processing: {album}")
            logger.info(f"Processing: {album}")
            try:
                service.clean_album(album_path, language=language)
                msg = f"✅ Cleaned: {album}"
                st.success(msg)
                logger.info(msg)
            except Exception as e:
                msg = f"❌ Error processing {album}: {str(e)}"
                st.error(msg)
                logger.error(msg)
            progress.progress((i + 1) / len(albums), text=f"Processed {i+1}/{len(albums)} albums")
        st.success("All albums processed!")
        st.info("See album_cleaner.log for details.")
        with open("album_cleaner.log") as f:
            st.text_area("Log Output", f.read(), height=200)
