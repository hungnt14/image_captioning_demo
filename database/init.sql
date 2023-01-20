CREATE DATABASE IF NOT EXISTS image_captioning_demo;
USE image_captioning_demo;
CREATE TABLE IF NOT EXISTS Runs (
    runID varchar(64) NOT NULL,
    dateCreated datetime,
    modelConfigurations text,
    timeExecutionInSeconds float,
    PRIMARY KEY (runID)
);
CREATE TABLE IF NOT EXISTS Images (
    imageID varchar(64) NOT NULL,
    runID varchar(64) NOT NULL,
    imageFilename varchar(255) NOT NULL,
    generatedCaptions text,
    PRIMARY KEY (imageID),
    FOREIGN KEY (runID) REFERENCES Runs(runID)
);