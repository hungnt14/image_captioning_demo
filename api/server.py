from dotenv import load_dotenv

try:
    load_dotenv("../.env")
except:
    print("Can't load config from .env file!")
    exit(0)

from typing import List, Union, Dict
from fastapi import FastAPI

import os
import time
import yaml
import logging
import logging.config
from pathlib import Path
import json
import uuid

import pymysql

from PIL import Image
import torch

from typing import List, Union, Dict
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from captioning.models.blip import blip_decoder
from captioning import captioning, loader

"""
API Decleration
"""
print("Setting up API...")
API_VERSION = os.environ["API_VERSION"]
app = FastAPI(
    title="Image Captioning API",
    description="API designed for generating captions of images",
    version=API_VERSION,
    contact={"name": "Nguyen Tien Hung", "email": "ngtienhung14@gmail.com"},
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
Setting up loggers
"""
print("Creating loggers...")
os.chdir(Path(__file__).parent)
Path("logs").mkdir(parents=True, exist_ok=True)
logging.config.dictConfig(json.load(open(os.environ["LOG_CONFIG"])))
app_logger = logging.getLogger("app_logger")
error_logger = logging.getLogger("error_logger")

"""
Pre-loading model
"""
print("Pre-loading model...")
# load configs
try:
    configs = yaml.load(open(os.environ["CONFIGS_PATH"], "r"), Loader=yaml.Loader)
    model = blip_decoder(
        med_config=configs["inference"]["med_config"],
        pretrained=configs["inference"]["pretrained"],
        image_size=configs["dataset"]["image_size"],
        vit=configs["inference"]["vit"],
        prompt=configs["inference"]["prompt"],
    )
    device = torch.device(configs["inference"]["device"])
    if configs["inference"]["device"] == "cuda" and not torch.cuda.is_available():
        print("cuda is not available, switched to cpu")
        device = torch.device("cpu")
    model = model.to(device)
except:
    message = "ERROR Pre-loading model"
    error_logger.info(message)
    raise Exception(message)

"""
Creating database connection
"""
print("Creating connection to database...")
try:
    mydb = pymysql.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_ROOT_PASSWORD"],
        database=os.environ["MYSQL_DATABASE_NAME"],
    )
    mycursor = mydb.cursor()
except:
    message = "ERROR Creating connection to database"
    error_logger.info(message)
    raise Exception(message)

print("API is ready!")


@app.get("/")
async def home():
    return {"message": "Ready!"}


@app.post(f"/api/{API_VERSION}/generate_captions")
async def generate_captions(filenames: List[str], images: List[UploadFile] = File(...)):
    app_logger.info(f"Generating captions for {len(filenames)} images...")
    start_time = time.time()
    date_created = time.strftime("%Y-%m-%d %H:%M:%S")
    # create Pillow images dict
    imgs_dict = {}
    for filename, image in zip(filenames, images):
        try:
            raw_img = Image.open(image.file).convert("RGB")
            imgs_dict[filename] = raw_img
        except:
            message = "ERROR Creating images dict"
            error_logger.info(message)
            raise Exception(message)

    # create dataloader
    try:
        dataloader = loader.create_loader(imgs_dict, configs)
    except:
        message = "ERROR Creating dataloader"
        error_logger.info(message)
        raise Exception(message)
    # generate results
    try:
        results = captioning.generate_captions(model, device, dataloader, configs)
    except:
        message = "ERROR Inferencing"
        error_logger.info(message)
        raise Exception(message)

    time_execution = time.time() - start_time

    # save run to database
    try:
        run_id = str(uuid.uuid4())
        sql = f"INSERT INTO Runs (runID, dateCreated, modelConfigurations, timeExecutionInSeconds) VALUES ('{run_id}', '{date_created}', '{json.dumps(configs)}', {time_execution})"
        mydb.ping()
        mycursor.execute(sql)
        mydb.commit()
        saved_uploaded_images_path = os.path.join(
            os.environ["USER_UPLOADED_IMAGES_ROOT"], run_id
        )
        if not os.path.exists(saved_uploaded_images_path):
            os.makedirs(saved_uploaded_images_path)
    except:
        message = "ERROR Saving run to database"
        error_logger.info(message)
        raise Exception(message)

    # save image to database and disk
    try:
        for filename, image in imgs_dict.items():
            # concatenate generated captions
            generated_captions = ""
            for result in results:
                if result["filename"] == filename:
                    generated_captions += f'{result["caption"]}\n'
            # insert into database
            image_id = str(uuid.uuid4())
            sql = f"INSERT INTO Images (imageID, runID, imageFilename, generatedCaptions) VALUES ('{image_id}', '{run_id}', '{filename}', '{generated_captions}')"
            mycursor.execute(sql)
            mydb.commit()
            # save image to disk
            image.save(os.path.join(saved_uploaded_images_path, filename))
    except:
        message = "ERROR Saving images to disk"
        error_logger.info(message)
        raise Exception(message)
    app_logger.info(
        f"Done. Finshed generating captions for {len(filenames)} images in {time_execution} seconds"
    )
    return results
