# Umgebung fuer das lokale Test-Backend (SQLite + Moto). Wird von
# run-backend.sh eingelesen; Werte wie in seed_store.py.
FLEXR_TEST_HOME="${FLEXR_TEST_HOME:-$HOME/.cache/flexr-test}"
export DATABASE_URL="sqlite:///$FLEXR_TEST_HOME/store.db"
export JWT_SECRET=store-demo-only
export S3_ENDPOINT_URL=http://localhost:5055
export S3_ACCESS_KEY_ID=test S3_SECRET_ACCESS_KEY=test
export S3_BUCKET_NAME=flexr-photos S3_PRIVATE_BUCKET_NAME=flexr-verification
export S3_REGION=us-east-1
export S3_PUBLIC_BASE_URL=http://localhost:5055/flexr-photos
export ENV=development PREMIUM_ENABLED=false
