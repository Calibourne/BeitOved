import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
import boto3
import os
import io

# ========== 🌍 Determine current config ==========
st.set_page_config(page_title="Dog Audio Logger", page_icon="🐶")
available_configs = st.secrets["configs"]
query_params = st.query_params
mode = query_params.get("mode", [None])[0] or st.selectbox("Choose Project", options=available_configs.keys())

config = available_configs[mode]

# ========== ☁️ AWS SETUP ==========
if "AWS_ACCESS_KEY_ID" in st.secrets:
    AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
    AWS_REGION = st.secrets.get("AWS_REGION", "eu-central-1")
    S3_BUCKET = st.secrets["S3_BUCKET_NAME"]
else:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
    S3_BUCKET = os.getenv("S3_BUCKET_NAME")

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET]):
    st.error("🚫 AWS credentials or bucket not configured!")
    st.stop()

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

# ========== 🚀 Streamlit UI ==========
st.title(config["title"])
st.subheader(config["subtitle"])

# 🐕 Dynamic fields from config
field_values = {}
for field_key, field_info in config["fields"].items():
    value = st.selectbox(
        field_info["label"],
        options=field_info["options"],
    )
    field_values[field_key] = value

# 📅 Date and Time
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Jerusalem")
local_time = datetime.now(ZoneInfo(APP_TIMEZONE)).time()
date = st.date_input("Date*", value=datetime.today())
time = st.time_input("Time*", value=local_time, help="Select the time of the training session.")

# 🎙️ Audio Recording
st.markdown("### 🎧 Record Audio:")
st.info(config["audio_prompt"])
wav_audio_data = st.audio_input("Click to start recording", key="audio_recorder")

if wav_audio_data is not None:
    st.audio(wav_audio_data, format="audio/wav")

# 🚀 Submit Button
if st.button("Submit"):
    if not field_values.get("dog_name"):
        st.error("🚫 Dog name is required!")
    elif wav_audio_data is None:
        st.error("🚫 Audio recording is required!")
    else:
        st.success("✅ Submission received!")

        # 🔒 Safe filename
        safe_fields = [field_values[k].replace(" ", "_") for k in field_values]
        filename = f"{config['s3_prefix']}/{'_'.join(safe_fields)}_{date}_{time}.wav".replace(":", "-")

        # Upload
        upload_to_s3(wav_audio_data, filename, S3_BUCKET)

        # Summary
        st.markdown("### ✅ Submission Summary")
        for key, val in field_values.items():
            st.write(f"**{config['fields'][key]['label']}**: {val}")
        st.write(f"**Date:** {date}")
        st.write(f"**Time:** {time}")
