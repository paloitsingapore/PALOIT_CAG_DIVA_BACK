from aws_cdk import (
    NestedStack,
    RemovalPolicy,
    aws_rekognition as rekognition,
    aws_s3 as s3,
)
from constructs import Construct


class StorageStack(NestedStack):
    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket for passenger photos
        self.passenger_photos_bucket = s3.Bucket(
            self,
            "PassengerPhotosBucket",
            bucket_name=f"{config['project_name']}-passenger-photos-{config['environment']}".lower(),
            removal_policy=RemovalPolicy.DESTROY if config["environment"] == "dev" else RemovalPolicy.RETAIN,
            auto_delete_objects=True if config["environment"] == "dev" else False,
        )
        self.map_images_bucket = s3.Bucket(
            self,
            f"{config['project_name']}mapimagesbucket",
            bucket_name=config["MAP_IMAGE_BUCKET"],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        # Create Rekognition collection
        self.face_collection = rekognition.CfnCollection(
            self, "FaceCollection", collection_id=config["rekognition_collection_id"]
        )
