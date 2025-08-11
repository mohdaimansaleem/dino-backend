"""
Enhanced password security utilities
Implements secure password hashing, validation, and policies
"""
import re
import secrets
import string
from typing import Dict, List, Optional
from passlib.context import CryptContext
from passlib.hash import bcrypt
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Enhanced password context with configurable rounds
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS if hasattr(settings, 'BCRYPT_ROUNDS') else 12
)

class PasswordPolicy:
    """Password policy enforcement"""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Common weak passwords to reject
    WEAK_PASSWORDS = {
        "password", "123456", "password123", "admin", "qwerty",
        "letmein", "welcome", "monkey", "dragon", "master",
        "password1", "123456789", "12345678", "admin123"
    }

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash with timing attack protection"""
    try:
        # Use constant-time comparison
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        # Return False but still take similar time to prevent timing attacks
        pwd_context.hash("dummy_password")
        return False

def get_password_hash(password: str) -> str:
    """Generate secure password hash"""
    try:
        # Validate password before hashing
        validation_result = validate_password_strength(password)
        if not validation_result["is_valid"]:
            raise ValueError(f"Password validation failed: {', '.join(validation_result['errors'])}")
        
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise

def validate_password_strength(password: str) -> Dict[str, any]:
    """
    Validate password strength according to security policy
    Returns dict with validation results
    """
    errors = []
    warnings = []
    score = 0
    
    # Check if strong passwords are required
    if not getattr(settings, 'REQUIRE_STRONG_PASSWORDS', True):
        return {"is_valid": True, "errors": [], "warnings": [], "score": 100}
    
    # Length checks
    if len(password) < PasswordPolicy.MIN_LENGTH:
        errors.append(f"Password must be at least {PasswordPolicy.MIN_LENGTH} characters long")
    elif len(password) < 12:
        warnings.append("Consider using a longer password for better security")
        score += 10
    else:
        score += 25
    
    if len(password) > PasswordPolicy.MAX_LENGTH:
        errors.append(f"Password must not exceed {PasswordPolicy.MAX_LENGTH} characters")
    
    # Character type checks
    if PasswordPolicy.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    else:
        score += 15
    
    if PasswordPolicy.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    else:
        score += 15
    
    if PasswordPolicy.REQUIRE_DIGITS and not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    else:
        score += 15
    
    if PasswordPolicy.REQUIRE_SPECIAL and not re.search(f'[{re.escape(PasswordPolicy.SPECIAL_CHARS)}]', password):
        errors.append(f"Password must contain at least one special character: {PasswordPolicy.SPECIAL_CHARS}")
    else:
        score += 15
    
    # Check for common weak passwords
    if password.lower() in PasswordPolicy.WEAK_PASSWORDS:
        errors.append("Password is too common and easily guessable")
    
    # Check for repeated characters
    if re.search(r'(.)\1{2,}', password):
        warnings.append("Avoid repeating the same character multiple times")
        score -= 5
    
    # Check for sequential characters
    if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)', password.lower()):
        warnings.append("Avoid sequential characters")
        score -= 5
    
    # Bonus points for length
    if len(password) >= 16:
        score += 15
    elif len(password) >= 12:
        score += 10
    
    # Ensure score is within bounds
    score = max(0, min(100, score))
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "score": score,
        "strength": get_password_strength_label(score)
    }

def get_password_strength_label(score: int) -> str:
    """Get password strength label based on score"""
    if score >= 90:
        return "Very Strong"
    elif score >= 75:
        return "Strong"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Weak"

def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure password"""
    if length < PasswordPolicy.MIN_LENGTH:
        length = PasswordPolicy.MIN_LENGTH
    if length > PasswordPolicy.MAX_LENGTH:
        length = PasswordPolicy.MAX_LENGTH
    
    # Ensure we have at least one character from each required category
    password_chars = []
    
    if PasswordPolicy.REQUIRE_UPPERCASE:
        password_chars.append(secrets.choice(string.ascii_uppercase))
    if PasswordPolicy.REQUIRE_LOWERCASE:
        password_chars.append(secrets.choice(string.ascii_lowercase))
    if PasswordPolicy.REQUIRE_DIGITS:
        password_chars.append(secrets.choice(string.digits))
    if PasswordPolicy.REQUIRE_SPECIAL:
        password_chars.append(secrets.choice(PasswordPolicy.SPECIAL_CHARS))
    
    # Fill the rest with random characters from all categories
    all_chars = string.ascii_letters + string.digits + PasswordPolicy.SPECIAL_CHARS
    for _ in range(length - len(password_chars)):
        password_chars.append(secrets.choice(all_chars))
    
    # Shuffle the password to avoid predictable patterns
    secrets.SystemRandom().shuffle(password_chars)
    
    return ''.join(password_chars)

def check_password_breach(password: str) -> bool:
    """
    Check if password appears in known breach databases
    This is a placeholder - in production, you might want to integrate with HaveIBeenPwned API
    """
    # For now, just check against our weak password list
    return password.lower() in PasswordPolicy.WEAK_PASSWORDS

class LoginAttemptTracker:
    """Track login attempts to prevent brute force attacks"""
    
    def __init__(self):
        self.attempts = {}  # In production, use Redis or database
        self.lockouts = {}
    
    def record_failed_attempt(self, identifier: str) -> None:
        """Record a failed login attempt"""
        now = datetime.utcnow()
        
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        # Clean old attempts (older than 1 hour)
        self.attempts[identifier] = [
            attempt for attempt in self.attempts[identifier]
            if now - attempt < timedelta(hours=1)
        ]
        
        self.attempts[identifier].append(now)
        
        # Check if we should lock the account
        if len(self.attempts[identifier]) >= settings.MAX_LOGIN_ATTEMPTS:
            # Use 100 seconds lockout duration for multiple attempts
            lockout_seconds = 100
            self.lockouts[identifier] = now + timedelta(seconds=lockout_seconds)
            logger.warning(f"Account locked for {lockout_seconds} seconds due to too many failed attempts: {identifier}")
    
    def record_successful_attempt(self, identifier: str) -> None:
        """Record a successful login attempt"""
        # Clear failed attempts on successful login
        if identifier in self.attempts:
            del self.attempts[identifier]
        if identifier in self.lockouts:
            del self.lockouts[identifier]
    
    def is_locked(self, identifier: str) -> bool:
        """Check if an account is currently locked"""
        if identifier not in self.lockouts:
            return False
        
        now = datetime.utcnow()
        if now > self.lockouts[identifier]:
            # Lockout expired
            del self.lockouts[identifier]
            return False
        
        return True
    
    def get_remaining_lockout_time(self, identifier: str) -> Optional[int]:
        """Get remaining lockout time in seconds"""
        if not self.is_locked(identifier):
            return None
        
        now = datetime.utcnow()
        remaining = self.lockouts[identifier] - now
        return int(remaining.total_seconds())
    
    def get_failed_attempts_count(self, identifier: str) -> int:
        """Get number of recent failed attempts"""
        if identifier not in self.attempts:
            return 0
        
        now = datetime.utcnow()
        # Count attempts in the last hour
        recent_attempts = [
            attempt for attempt in self.attempts[identifier]
            if now - attempt < timedelta(hours=1)
        ]
        return len(recent_attempts)

# Global login attempt tracker
login_tracker = LoginAttemptTracker()

def sanitize_error_message(error_msg: str, is_production: bool = None) -> str:
    """Sanitize error messages to prevent information disclosure"""
    if is_production is None:
        is_production = settings.is_production
    
    if not is_production:
        return error_msg
    
    # In production, return generic error messages
    sensitive_keywords = [
        "database", "sql", "firestore", "connection", "timeout",
        "internal", "server", "exception", "traceback", "stack"
    ]
    
    error_lower = error_msg.lower()
    for keyword in sensitive_keywords:
        if keyword in error_lower:
            return "An error occurred. Please try again later."
    
    return error_msg

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks"""
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    
    return result == 0