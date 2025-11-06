#!/bin/bash
##
# Download the delta patch for the RDSv3 modern minimal database.
# ENV Variables:
#   BASE_RELEASE_VERSION  -- Initial version in form YYYY.MM.<patch>  (eg. 2024.03.1)
#   DELTA_RELEASE_VERSION -- Updated version in form YYYY.MM.<patch>  (eg. 2024.09.1)
#   BASE_PATH             -- Where to save and unpack the DB
#   DOWNLOAD_URL          -- URL to the nist database up to RDS e.g https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS
##
set -e
echo BASE_RELEASE_VERSION \(Original version of NSRL db that was downloaded\): "${BASE_RELEASE_VERSION:=2024.03.1}"
echo DELTA_RELEASE_VERSION \(SQL patch to download an apply to existing db\): "${DELTA_RELEASE_VERSION:=2024.09.1}"
echo BASE_PATH \(Path to save the db to\): "${BASE_PATH:=/data/nsrl}"
echo DOWNLOAD_URL \(URL to download the DB from\): "${DOWNLOAD_URL:=https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS}"

# Drop trailing slash if it's present
TRIMMED_URL=$(echo "${DOWNLOAD_URL}" | sed 's:/*$::')

BASE_RELEASE=${BASE_RELEASE_VERSION}_modern_minimal
DELTA_RELEASE=${DELTA_RELEASE_VERSION}_modern_minimal_delta
ARCHIVE=RDS_${DELTA_RELEASE}.zip
URL=${TRIMMED_URL}/rds_${DELTA_RELEASE_VERSION}/${ARCHIVE}


cd "${BASE_PATH}"
if [ $? -ne 0 ]; then
    echo "Unable to find base path. An existing database is required to update."
    echo "Did you mean to download a new database?"
    exit 1
fi

DB_DIR="${BASE_PATH}/RDS_${BASE_RELEASE}"
DB_FILE="${DB_DIR}/RDS_${BASE_RELEASE}.db"
if [ ! -f "${DB_FILE}" ]; then
    echo "Unable to find an existing database to update."
    exit 1
fi

DELTA_DIR="${BASE_PATH}/RDS_${DELTA_RELEASE}"
if [ -d "${DELTA_DIR}" ]; then
    echo "Database delta already downloaded, no changes made."
    exit 0
fi

echo
echo Downloading database delta from the url \'"${URL}"\'
echo

curl -o ${ARCHIVE} ${URL}
unzip ${ARCHIVE}
if [ $? -ne 0 ]; then
    echo "Database extraction failed."
    exit 1
fi
rm -f "${ARCHIVE}"

echo "Updating SQL db with delta"

DELTA_SQL_FILE="${DELTA_DIR}/RDS_${DELTA_RELEASE}.sql"
sqlite3 "${DB_FILE}" ".read ${DELTA_SQL_FILE}"
if [ $? -ne 0 ]; then
    echo "Database failed to update. Update sql file not removed."
    exit 1
fi
rm "${DELTA_SQL_FILE}"
echo "Database updated."
