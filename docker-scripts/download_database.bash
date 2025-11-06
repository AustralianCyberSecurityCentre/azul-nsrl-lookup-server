#!/bin/bash
##
# Download the RDSv3 modern minimal database.
# ENV Variables (set them to override defaults):
#   RDS_RELEASE_VERSION  -- Version in form YYYY.MM.<patch>  (eg. 2024.03.1)
#   BASE_PATH            -- Where to save and unpack the DB
#   DOWNLOAD_URL         -- URL to the nist database up to RDS e.g https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS
##
set -e
echo RDS_RELEASE_VERSION \(Version of NSRL db to download\): "${RDS_RELEASE_VERSION:=2024.03.1}"
echo BASE_PATH \(Path to save the db to\): "${BASE_PATH:=/data/nsrl}"
echo DOWNLOAD_URL \(URL to download the DB from\): "${DOWNLOAD_URL:=https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS}"

# Drop trailing slash if it's present
TRIMMED_URL=$(echo "${DOWNLOAD_URL}" | sed 's:/*$::')

# NOTE VERSION 2024.03.1 when unzipped is 98GB
RELEASE=RDS_${RDS_RELEASE_VERSION}_modern_minimal
ARCHIVE=${RELEASE}.zip
URL=${TRIMMED_URL}/rds_${RDS_RELEASE_VERSION}/${ARCHIVE}

mkdir -p "${BASE_PATH}"
cd "${BASE_PATH}"

if [ -d "${RELEASE}" ]; then
    echo "Database already downloaded, no changes made."
    exit 0
fi

echo
echo Downloading database from the url \'"${URL}"\'
echo

curl -o "${ARCHIVE}" "${URL}"
unzip "${ARCHIVE}"
if [ $? -ne 0 ]; then
    echo "Database extraction failed."
    exit 1
fi

DB_FILE="${BASE_PATH}/${RELEASE}/${RELEASE}.db"
echo Database extracted to: $(ls "${DB_FILE}")
rm -f "${ARCHIVE}"
