import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import broadcast, col

# retest1

args = getResolvedOptions(sys.argv, ["JOB_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)


# Read source data
source_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="sales_db",
    table_name="raw_transactions",
    transformation_ctx="source_dyf",
)

df = source_dyf.toDF()

# Incremental load: only process records newer than the last run
incremental_df = df.filter(col("updated_at") > col("last_run_watermark"))

# Reference lookup data (small table, safe to broadcast)
customers_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="sales_db",
    table_name="customers",
    transformation_ctx="customers_dyf",
)
customers_df = customers_dyf.toDF()

# Join transactions to customers
joined_df = incremental_df.join(
    broadcast(customers_df),
    incremental_df.customer_id == customers_df.customer_id,
    "inner",
)

# Filter active customers only
filtered_df = joined_df.filter(joined_df.status == "active")

# Compute discount
result_df = filtered_df.withColumn(
    "discount", filtered_df.amount * 0.10
)

# Write output, partitioned by date for efficient Athena queries
result_df.write.mode("overwrite").partitionBy("transaction_date").parquet(
    "s3://my-bucket/processed/transactions/"
)

job.commit()
