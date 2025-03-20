import qrcode
from io import BytesIO
from flask import url_for
from config import Config

def generate_rsvp_qr(guest_token, size=10):
    """Generate QR code for RSVP link"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=4,
        )
        
        # Create RSVP URL with _external=True to get full URL
        rsvp_url = url_for('routes.rsvp_page', token=guest_token, _external=True)
        qr.add_data(rsvp_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return img_io
    except Exception as e:
        print(f"QR Generation error: {e}")
        return None