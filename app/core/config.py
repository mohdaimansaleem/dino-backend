"""
Production Configuration for Dino E-Menu Backend
Environment-based configuration for Google Cloud Run deployment
"""
from pydantic_settings import BaseSettings
from typing import List, Union, Optional
from pydantic import field_validator, Field
import os
from google.cloud import storage, firestore
from google.oauth2 import service_account
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Production application settings"""
    
    # =============================================================================
    # ENVIRONMENT & BASIC CONFIG
    # =============================================================================
    ENVIRONMENT: str = Field(..., description="Environment (development, staging, production)")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # =============================================================================
    # SECURITY
    # =============================================================================
    SECRET_KEY: str = Field(..., description="JWT secret key")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="JWT token expiration")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, description="Refresh token expiration")
    
    # =============================================================================
    # CORS CONFIGURATION
    # =============================================================================
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["*"], 
        description="Allowed CORS origins"
    )
    
    # =============================================================================
    # GOOGLE CLOUD PLATFORM
    # =============================================================================
    GCP_PROJECT_ID: str = Field(..., description="Google Cloud Project ID")
    GCP_REGION: str = Field(default="us-central1", description="GCP region")
    
    # =============================================================================
    # FIRESTORE
    # =============================================================================
    FIRESTORE_DATABASE_ID: str = Field(
        default="(default)", 
        description="Firestore database ID"
    )
    
    # =============================================================================
    # CLOUD STORAGE
    # =============================================================================
    GCS_BUCKET_NAME: str = Field(..., description="Google Cloud Storage bucket name")
    GCS_BUCKET_REGION: str = Field(default="us-central1", description="GCS bucket region")
    GCS_IMAGES_FOLDER: str = Field(default="images", description="Images folder in bucket")
    GCS_DOCUMENTS_FOLDER: str = Field(default="documents", description="Documents folder")
    GCS_QR_CODES_FOLDER: str = Field(default="qr-codes", description="QR codes folder")
    GCS_SIGNED_URL_EXPIRATION: int = Field(default=3600, description="Signed URL expiration")
    
    # =============================================================================
    # FILE UPLOAD CONFIGURATION
    # =============================================================================
    MAX_FILE_SIZE: int = Field(default=5242880, description="Max file size (5MB)")
    MAX_IMAGE_SIZE_MB: int = Field(default=5, description="Max image size in MB")
    MAX_DOCUMENT_SIZE_MB: int = Field(default=10, description="Max document size in MB")
    ALLOWED_IMAGE_TYPES: Union[List[str], str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "image/gif"],
        description="Allowed image MIME types"
    )
    
    # =============================================================================
    # APPLICATION FEATURES
    # =============================================================================
    QR_CODE_BASE_URL: str = Field(..., description="Base URL for QR codes")
    ENABLE_REAL_TIME_NOTIFICATIONS: bool = Field(default=True, description="Enable notifications")
    WEBSOCKET_PING_INTERVAL: int = Field(default=30, description="WebSocket ping interval")
    DEFAULT_CURRENCY: str = Field(default="INR", description="Default currency")
    PAYMENT_GATEWAY: str = Field(default="razorpay", description="Payment gateway")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Rate limit per minute")
    
    # =============================================================================
    # CLOUD RUN CONFIGURATION
    # =============================================================================
    CLOUD_RUN_SERVICE_NAME: str = Field(
        default="dino-backend-api", 
        description="Cloud Run service name"
    )
    CLOUD_RUN_REGION: str = Field(default="us-central1", description="Cloud Run region")
    CLOUD_RUN_MEMORY: str = Field(default="512Mi", description="Cloud Run memory")
    CLOUD_RUN_CPU: str = Field(default="1", description="Cloud Run CPU")
    CLOUD_RUN_MAX_INSTANCES: int = Field(default=10, description="Max instances")
    CLOUD_RUN_MIN_INSTANCES: int = Field(default=0, description="Min instances")
    
    # =============================================================================
    # VALIDATORS
    # =============================================================================
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator('ALLOWED_IMAGE_TYPES', mode='before')
    @classmethod
    def parse_allowed_image_types(cls, v):
        if isinstance(v, str):
            return [img_type.strip() for img_type in v.split(",")]
        return v
    
    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT.lower() == "staging"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


class CloudServiceManager:
    """Manages Google Cloud service clients for production deployment"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._storage_client: Optional[storage.Client] = None
        self._firestore_client: Optional[firestore.Client] = None
        self.logger = logging.getLogger(__name__)
    
    def get_storage_client(self) -> storage.Client:
        """Get Google Cloud Storage client"""
        if not self._storage_client:
            try:
                self._storage_client = storage.Client(project=self.settings.GCP_PROJECT_ID)
                self.logger.info("Storage client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize storage client: {e}")
                raise
        
        return self._storage_client
    
    def get_firestore_client(self) -> firestore.Client:
        """Get Firestore client"""
        if not self._firestore_client:
            try:
                self._firestore_client = firestore.Client(
                    project=self.settings.GCP_PROJECT_ID,
                    database=self.settings.FIRESTORE_DATABASE_ID
                )
                self.logger.info("Firestore client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Firestore client: {e}")
                raise
        
        return self._firestore_client
    
    def get_storage_bucket(self) -> storage.Bucket:
        """Get the main storage bucket"""
        try:
            client = self.get_storage_client()
            bucket = client.bucket(self.settings.GCS_BUCKET_NAME)
            
            # Verify bucket exists
            if not bucket.exists():
                raise ValueError(f"Bucket {self.settings.GCS_BUCKET_NAME} does not exist")
            
            return bucket
        except Exception as e:
            self.logger.error(f"Failed to get storage bucket: {e}")
            raise
    
    def health_check(self) -> dict:
        """Perform health check on cloud services"""
        health = {
            "firestore": False,
            "storage": False,
            "errors": []
        }
        
        # Test Firestore
        try:
            firestore_client = self.get_firestore_client()
            # Simple test - list collections
            list(firestore_client.collections())
            health["firestore"] = True
            self.logger.info("Firestore health check passed")
        except Exception as e:
            error_msg = f"Firestore health check failed: {str(e)}"
            health["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        # Test Storage
        try:
            bucket = self.get_storage_bucket()
            bucket.exists()  # Check if bucket exists
            health["storage"] = True
            self.logger.info("Storage health check passed")
        except Exception as e:
            error_msg = f"Storage health check failed: {str(e)}"
            health["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return health


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================
def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


# Initialize settings
settings = get_settings()
cloud_manager = CloudServiceManager(settings)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================
def get_cloud_manager() -> CloudServiceManager:
    """Get cloud service manager"""
    return cloud_manager


def get_storage_client() -> storage.Client:
    """Get Google Cloud Storage client"""
    return cloud_manager.get_storage_client()


def get_firestore_client() -> firestore.Client:
    """Get Firestore client"""
    return cloud_manager.get_firestore_client()


def get_storage_bucket() -> storage.Bucket:
    """Get the main storage bucket"""
    return cloud_manager.get_storage_bucket()


def initialize_cloud_services() -> bool:
    """Initialize and test cloud services"""
    try:
        logger.info("Initializing cloud services")
        
        health = cloud_manager.health_check()
        
        if health["firestore"]:
            logger.info("Firestore connected successfully")
        else:
            logger.warning("Firestore connection failed")
        
        if health["storage"]:
            logger.info("Cloud Storage connected successfully")
        else:
            logger.warning("Cloud Storage connection failed")
        
        if health["errors"]:
            logger.error("Errors during cloud service initialization")
            for error in health["errors"]:
                logger.error(error)
        
        # Return True if at least one service is working
        success = health["firestore"] or health["storage"]
        
        if success:
            logger.info("Cloud services initialization completed successfully")
        else:
            logger.error("All cloud services failed to initialize")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to initialize cloud services: {e}")
        return False