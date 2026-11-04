# ============================================================================
# Plantix AI / AgriVision Platform - Security, Auth, Rate Limiter & Sanitization (Phase 9)
# Cryptographic tokens, sliding-window rate limiting, upload byte sanitization,
# image compression for rural 2G/3G networks, and XSS/SQLi defense.
# ============================================================================

import os
import hmac
import hashlib
import base64
import json
import time
import re
import threading
from io import BytesIO
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

class SecurityService:
    def __init__(self):
        self._rate_limits = {}
        self._rate_lock = threading.RLock()
        self.secret_key = Config.SECRET_KEY.encode('utf-8')

    # --- CRYPTOGRAPHIC TOKEN AUTHENTICATION ---
    def generate_token(self, user_id, role="farmer", expires_in_hours=72):
        """Generates a cryptographically signed HMAC-SHA256 session token."""
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "uid": user_id,
            "role": role,
            "iat": int(time.time()),
            "exp": int(time.time() + (expires_in_hours * 3600))
        }

        h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        signing_input = f"{h_b64}.{p_b64}".encode()

        sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip('=')

        return f"{h_b64}.{p_b64}.{sig_b64}"

    def verify_token(self, token):
        """Verifies cryptographic signature and expiration of an authentication token."""
        if not token or not isinstance(token, str):
            return {"valid": False, "error": "Missing token"}

        parts = token.split('.')
        if len(parts) != 3:
            return {"valid": False, "error": "Malformed token format"}

        h_b64, p_b64, sig_b64 = parts
        signing_input = f"{h_b64}.{p_b64}".encode()
        expected_sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return {"valid": False, "error": "Invalid token signature"}

        try:
            # Add padding back if necessary
            padded_p = p_b64 + '=' * (-len(p_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded_p.encode()).decode())
        except Exception:
            return {"valid": False, "error": "Corrupted token payload"}

        if payload.get("exp") and time.time() > payload["exp"]:
            return {"valid": False, "error": "Token has expired. Please re-authenticate."}

        return {
            "valid": True,
            "user_id": payload.get("uid"),
            "role": payload.get("role", "farmer"),
            "issued_at": payload.get("iat"),
            "expires_at": payload.get("exp")
        }

    # --- SLIDING-WINDOW RATE LIMITER ---
    def check_rate_limit(self, client_key, limit=120, window_seconds=60):
        """
        Thread-safe sliding-window rate limiter per client IP or user token.
        Returns (is_allowed, remaining, retry_after_seconds).
        """
        now = time.time()
        window_start = now - window_seconds

        with self._rate_lock:
            # Clean up old timestamps
            timestamps = self._rate_limits.get(client_key, [])
            timestamps = [t for t in timestamps if t > window_start]

            if len(timestamps) >= limit:
                oldest = timestamps[0]
                retry_after = int(oldest + window_seconds - now) + 1
                self._rate_limits[client_key] = timestamps
                return False, 0, max(1, retry_after)

            timestamps.append(now)
            self._rate_limits[client_key] = timestamps
            remaining = limit - len(timestamps)
            return True, remaining, 0

    # --- IMAGE VALIDATION & RURAL BANDWIDTH OPTIMIZATION ---
    def sanitize_and_optimize_image(self, file_stream, max_dimension=1600, quality=85):
        """
        Inspects file bytes, verifies image integrity using Pillow,
        strips dangerous EXIF/metadata, downscales large dimensions,
        and re-compresses to standard JPEG for significant 2G/3G bandwidth savings.
        """
        try:
            # Read first few bytes for verification
            img_bytes = file_stream.read()
            file_stream.seek(0)

            # Pillow inspection
            img = Image.open(BytesIO(img_bytes))
            img.verify() # Checks image integrity and format

            # Re-open for actual processing (verify closes stream)
            img = Image.open(BytesIO(img_bytes))

            # Convert RGBA to RGB for standard JPEG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Downscale if exceeding mobile limits
            w, h = img.size
            if max(w, h) > max_dimension:
                scale = max_dimension / max(w, h)
                new_size = (int(w * scale), int(h * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Save clean optimized output
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            return {
                "valid": True,
                "optimized_bytes": output,
                "original_size_kb": round(len(img_bytes) / 1024, 1),
                "optimized_size_kb": round(output.getbuffer().nbytes / 1024, 1),
                "width": img.width,
                "height": img.height
            }
        except Exception as e:
            return {"valid": False, "error": f"Invalid or corrupted image format: {str(e)}"}

    # --- INPUT SANITIZATION ---
    def sanitize_input(self, text):
        """Strips HTML script tags and harmful injection characters from user input."""
        if not text or not isinstance(text, str):
            return text
        # Remove script tags
        cleaned = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        # Remove event handlers like onclick=, onerror=
        cleaned = re.sub(r'on\w+\s*=', '', cleaned, flags=re.IGNORECASE)
        # Strip iframe / embed
        cleaned = re.sub(r'<(iframe|embed|object).*?>.*?</\1>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        return cleaned.strip()

security_service = SecurityService()
