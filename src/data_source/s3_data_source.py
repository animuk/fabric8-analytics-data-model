from abstract_data_source import AbstractDataSource
import botocore
import boto3
import json
import config

class S3DataSource(AbstractDataSource):
    _DEFAULT_REGION_NAME = 'us-east-1'

    def __init__(self, src_bucket_name, access_key, secret_key):
        self.is_local = config.AWS_S3_IS_LOCAL

        if self.is_local:
            self.session = boto3.session.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                                                 region_name=self._DEFAULT_REGION_NAME)
            self.s3_resource = self.session.resource('s3', config=botocore.client.Config(signature_version='s3v4'),
                                                     use_ssl=False, endpoint_url="http://"+config.LOCAL_MINIO_ENDPOINT)
        else:
            self.session = boto3.session.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
            self.s3_resource = self.session.resource('s3', config=botocore.client.Config(signature_version='s3v4'))

        self.bucket_name = src_bucket_name

    def get_source_name(self):
        return "S3"

    def read_json_file(self, filename, bucket_name=None):
        """Read JSON file from the data source"""

        if bucket_name is None:
            bucket_name = self.bucket_name

        obj = self.s3_resource.Object(bucket_name, filename).get()['Body'].read()
        utf_data = obj.decode("utf-8")
        return json.loads(utf_data)

    def list_files(self, prefix=None, bucket_name=None):
        """List all the files in the source directory"""

        list_filenames = []
        if bucket_name is None:
            bucket_name = self.bucket_name

        bucket = self.s3_resource.Bucket(bucket_name)

        # TODO: Pagination ??
        #   For a huge bucket, we should consider reading in chunks i.e. 'MaxKeys'
        # TODO: Marker ??
        #   For retry after a previously failed full-import,
        #   we can use 'Marker' = graph_meta.last_imported_s3_key
        if prefix is None:
            objects = bucket.objects.all()
            list_filenames = [x.key for x in objects]
        else:
            for obj in bucket.objects.filter(Prefix=prefix):
                list_filenames.append(obj.key)
        
        return list_filenames
