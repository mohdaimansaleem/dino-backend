"""
QR Code Generation Service
Handles QR code creation for table ordering with Cloud Storage
"""
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SquareGradiantColorMask
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import uuid
import logging

from app.core.config import settings, get_storage_bucket

logger = logging.getLogger(__name__)


class QRCodeService:
    """Service for generating QR codes for table ordering"""
    
    def __init__(self):
        self.base_url = settings.QR_CODE_BASE_URL
        logger.info(f"QR Service initialized with base URL: {self.base_url}")
    
    def generate_table_url(self, cafe_id: str, table_id: str) -> str:
        """Generate the URL that QR code will point to"""
        return f"{self.base_url}/menu/{cafe_id}/{table_id}"
    
    def create_qr_code(self, data: str, cafe_name: str = "", table_number: int = 0) -> qrcode.QRCode:
        """Create a QR code object with styling"""
        qr = qrcode.QRCode(
            version=1,  # Controls the size of the QR Code
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
            box_size=10,  # Size of each box in pixels
            border=4,  # Border size in boxes
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        return qr
    
    def generate_styled_qr_image(self, qr: qrcode.QRCode, cafe_name: str = "", 
                                table_number: int = 0) -> Image.Image:
        """Generate a styled QR code image with branding"""
        # Create QR code image with styling
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=SquareGradiantColorMask(
                back_color=(255, 255, 255),  # White background
                center_color=(46, 125, 50),  # Green center (primary color)
                edge_color=(27, 94, 32)      # Darker green edge
            )
        )
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Create a larger canvas for branding
        canvas_width = img.width + 100
        canvas_height = img.height + 150
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        
        # Paste QR code in center
        qr_x = (canvas_width - img.width) // 2
        qr_y = 80  # Leave space for header
        canvas.paste(img, (qr_x, qr_y))
        
        # Add text overlay
        draw = ImageDraw.Draw(canvas)
        
        try:
            # Try to use a nice font (fallback to default if not available)
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            footer_font = ImageFont.load_default()
        except Exception as e:
            logger.warning(f"Font loading failed, using default: {e}")
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            footer_font = ImageFont.load_default()
        
        # Header text
        header_text = "🦕 Dino E-Menu"
        try:
            header_bbox = draw.textbbox((0, 0), header_text, font=title_font)
            header_width = header_bbox[2] - header_bbox[0]
        except:
            # Fallback for older PIL versions
            header_width = len(header_text) * 10
        
        header_x = (canvas_width - header_width) // 2
        draw.text((header_x, 20), header_text, fill=(46, 125, 50), font=title_font)
        
        # Cafe name
        if cafe_name:
            try:
                cafe_bbox = draw.textbbox((0, 0), cafe_name, font=subtitle_font)
                cafe_width = cafe_bbox[2] - cafe_bbox[0]
            except:
                cafe_width = len(cafe_name) * 8
            
            cafe_x = (canvas_width - cafe_width) // 2
            draw.text((cafe_x, 50), cafe_name, fill=(33, 33, 33), font=subtitle_font)
        
        # Table number
        if table_number > 0:
            table_text = f"Table {table_number}"
            try:
                table_bbox = draw.textbbox((0, 0), table_text, font=subtitle_font)
                table_width = table_bbox[2] - table_bbox[0]
            except:
                table_width = len(table_text) * 8
            
            table_x = (canvas_width - table_width) // 2
            table_y = qr_y + img.height + 20
            draw.text((table_x, table_y), table_text, fill=(46, 125, 50), font=subtitle_font)
        
        # Footer instructions
        footer_text = "Scan to view menu & order"
        try:
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
        except:
            footer_width = len(footer_text) * 6
        
        footer_x = (canvas_width - footer_width) // 2
        footer_y = canvas_height - 30
        draw.text((footer_x, footer_y), footer_text, fill=(117, 117, 117), font=footer_font)
        
        return canvas
    
    async def generate_table_qr(self, cafe_id: str, table_id: str, cafe_name: str = "", 
                               table_number: int = 0) -> Dict[str, Any]:
        """Generate QR code for a table and upload to Cloud Storage"""
        try:
            # Generate URL
            table_url = self.generate_table_url(cafe_id, table_id)
            
            # Create QR code
            qr = self.create_qr_code(table_url, cafe_name, table_number)
            
            # Generate styled image
            img = self.generate_styled_qr_image(qr, cafe_name, table_number)
            
            # Convert image to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG', quality=95)
            img_bytes = img_buffer.getvalue()
            
            # Generate filename
            filename = f"table_{cafe_id}_{table_number}_{table_id}_{uuid.uuid4().hex[:8]}.png"
            blob_path = f"{settings.GCS_QR_CODES_FOLDER}/{cafe_id}/{filename}"
            
            # Upload to Cloud Storage
            try:
                bucket = get_storage_bucket()
                blob = bucket.blob(blob_path)
                blob.upload_from_string(img_bytes, content_type='image/png')
                blob.make_public()
                
                public_url = blob.public_url
                logger.info(f"✅ QR code uploaded to Cloud Storage: {public_url}")
                
            except Exception as storage_error:
                logger.warning(f"⚠️ Cloud Storage upload failed: {storage_error}")
                # Fallback to base64 if storage fails
                public_url = f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}"
            
            return {
                "qr_code_data": table_url,
                "qr_code_url": public_url,
                "filename": filename,
                "blob_path": blob_path,
                "cafe_id": cafe_id,
                "table_id": table_id,
                "table_number": table_number
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating QR code: {e}")
            raise
    
    async def generate_qr_base64(self, cafe_id: str, table_id: str, cafe_name: str = "", 
                                table_number: int = 0) -> str:
        """Generate QR code and return as base64 string"""
        try:
            # Generate URL
            table_url = self.generate_table_url(cafe_id, table_id)
            
            # Create QR code
            qr = self.create_qr_code(table_url, cafe_name, table_number)
            
            # Generate styled image
            img = self.generate_styled_qr_image(qr, cafe_name, table_number)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"❌ Error generating QR code base64: {e}")
            raise
    
    async def delete_qr_file(self, blob_path: str) -> bool:
        """Delete QR code file from Cloud Storage"""
        try:
            bucket = get_storage_bucket()
            blob = bucket.blob(blob_path)
            
            if blob.exists():
                blob.delete()
                logger.info(f"✅ Deleted QR code: {blob_path}")
                return True
            else:
                logger.warning(f"⚠️ QR code not found: {blob_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting QR file {blob_path}: {e}")
            return False
    
    async def regenerate_table_qr(self, cafe_id: str, table_id: str, old_blob_path: str = "", 
                                 cafe_name: str = "", table_number: int = 0) -> Dict[str, Any]:
        """Regenerate QR code for a table (useful when URL changes)"""
        # Delete old file if provided
        if old_blob_path:
            await self.delete_qr_file(old_blob_path)
        
        # Generate new QR code
        return await self.generate_table_qr(cafe_id, table_id, cafe_name, table_number)
    
    def validate_qr_url(self, url: str) -> bool:
        """Validate if URL is a valid table QR URL"""
        try:
            # Check if URL matches expected pattern
            if not url.startswith(self.base_url):
                return False
            
            # Extract path
            path = url.replace(self.base_url, "")
            
            # Should match pattern: /menu/{cafe_id}/{table_id}
            parts = path.strip("/").split("/")
            if len(parts) != 3 or parts[0] != "menu":
                return False
            
            return True
            
        except Exception:
            return False
    
    async def get_qr_info(self, cafe_id: str, table_id: str) -> Dict[str, Any]:
        """Get QR code information for a table"""
        table_url = self.generate_table_url(cafe_id, table_id)
        
        return {
            "table_url": table_url,
            "cafe_id": cafe_id,
            "table_id": table_id,
            "base_url": self.base_url,
            "is_valid": self.validate_qr_url(table_url)
        }


# Service instance - will be initialized when imported
def get_qr_service() -> QRCodeService:
    """Get QR service instance"""
    return QRCodeService()


# For backward compatibility
qr_service = None

def init_qr_service():
    """Initialize QR service"""
    global qr_service
    try:
        qr_service = QRCodeService()
        logger.info("✅ QR service initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize QR service: {e}")
        qr_service = None