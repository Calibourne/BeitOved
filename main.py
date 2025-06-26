import streamlit as st
from datetime import datetime
from audio_recorder_streamlit import audio_recorder
import boto3
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


# ===========================
# 🔧 AWS S3 CONFIG
# ===========================
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")  # or whatever your region is
S3_BUCKET = os.getenv("S3_BUCKET_NAME")


def upload_to_s3(file_data, filename, bucket):
    s3 = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    try:
        s3.upload_fileobj(file_data, bucket, filename)
        st.success(f"☁️ Uploaded to S3 as `{filename}`")
        s3_link = f"https://{bucket}.s3.{AWS_REGION}.amazonaws.com/{filename}"
        st.markdown(f"[🔗 Open file in S3]({s3_link})")
    except Exception as e:
        st.error(f"❌ Upload failed: {e}")


# ===========================
# 🚀 Streamlit UI
# ===========================
st.set_page_config(page_title="Beit Oved Training", page_icon="🐶")

st.title("🐾 Beit Oved Training")
st.subheader("Insert data here")


# 🐕 Dog Name
dog_name = st.selectbox(
    "Dog Name*",
    options=os.getenv("DOGS", "").split(","),
    help="Select the dog's name from the list or type a new one.",
)


# 📅 Date and Time
date = st.date_input("Date*", value=datetime.today())
time = st.time_input("Time*", value=datetime.now().time())


# 🎙️ Audio Recording
st.markdown("### 🎧 Record Audio:")
wav_audio_data = audio_recorder()

if wav_audio_data is not None:
    st.audio(wav_audio_data, format="audio/wav")


# 🚀 Submit Button
if st.button("Submit"):
    if not dog_name:
        st.error("🚫 Dog name is required!")
    elif wav_audio_data is None:
        st.error("🚫 Audio recording is required!")
    else:
        st.success("✅ Submission received!")

        # Filename construction
        safe_dog_name = dog_name.replace(" ", "_")
        filename = f"beit_oved/{safe_dog_name}_{date}_{time}.wav".replace(":", "-")

        # Write to a BytesIO for S3 upload
        import io

        audio_bytes = io.BytesIO(wav_audio_data)
        audio_bytes.seek(0)

        # Upload to S3
        upload_to_s3(audio_bytes, filename, S3_BUCKET)

        # Display submission summary
        st.markdown("### ✅ Submission Summary")
        st.write(f"**Dog Name:** {dog_name}")
        st.write(f"**Date:** {date}")
        st.write(f"**Time:** {time}")