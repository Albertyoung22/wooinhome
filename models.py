from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class RFQQuotation(db.Model):
    __tablename__ = 'rfq_quotations'

    id = db.Column(db.Integer, primary_key=True)
    rfq_number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), default='先生')
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    line_id = db.Column(db.String(50), nullable=True)
    preferred_contact_time = db.Column(db.String(50), default='全天皆可')
    
    city = db.Column(db.String(50), default='台南市')
    district = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    property_type = db.Column(db.String(50), default='整棟透天')
    size_ping = db.Column(db.Float, default=30.0)
    room_count = db.Column(db.Integer, default=3)
    current_status = db.Column(db.String(50), default='空屋閒置中')
    requirements = db.Column(db.Text, nullable=True)
    
    # Financial estimation snapshot from RFQ
    estimated_monthly_rent = db.Column(db.Integer, default=0)
    renovation_budget = db.Column(db.Integer, default=0)
    expected_roi = db.Column(db.Float, default=0.0)

    # Attachments
    attachment_filename = db.Column(db.String(255), nullable=True)
    attachment_orig_name = db.Column(db.String(255), nullable=True)

    # CRM Status
    status = db.Column(db.String(30), default='pending')  # pending, contacting, quoted, signed, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('RFQItem', backref='rfq', cascade='all, delete-orphan', lazy=True)
    notes = db.relationship('AdminNote', backref='rfq', cascade='all, delete-orphan', order_by='AdminNote.created_at.desc()', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'rfq_number': self.rfq_number,
            'customer_name': self.customer_name,
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email or '',
            'line_id': self.line_id or '',
            'preferred_contact_time': self.preferred_contact_time,
            'city': self.city,
            'district': self.district or '',
            'address': self.address or '',
            'property_type': self.property_type,
            'size_ping': self.size_ping,
            'room_count': self.room_count,
            'current_status': self.current_status,
            'requirements': self.requirements or '',
            'estimated_monthly_rent': self.estimated_monthly_rent,
            'renovation_budget': self.renovation_budget,
            'expected_roi': self.expected_roi,
            'attachment_filename': self.attachment_filename,
            'attachment_orig_name': self.attachment_orig_name,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'items_count': len(self.items)
        }

class RFQItem(db.Model):
    __tablename__ = 'rfq_items'

    id = db.Column(db.Integer, primary_key=True)
    rfq_id = db.Column(db.Integer, db.ForeignKey('rfq_quotations.id'), nullable=False)
    service_code = db.Column(db.String(50), nullable=False) # e.g. manage_host, spatial_renovate, tax_advisory
    service_title = db.Column(db.String(120), nullable=False)
    specs = db.Column(db.Text, nullable=True) # JSON representation of specs
    estimated_price = db.Column(db.String(50), default='專人評估報價')

    def get_specs_dict(self):
        try:
            return json.loads(self.specs) if self.specs else {}
        except Exception:
            return {}

class AdminNote(db.Model):
    __tablename__ = 'admin_notes'

    id = db.Column(db.Integer, primary_key=True)
    rfq_id = db.Column(db.Integer, db.ForeignKey('rfq_quotations.id'), nullable=False)
    author = db.Column(db.String(50), default='管理員')
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'

    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_val(cls, key: str, default: str = '') -> str:
        record = cls.query.filter_by(key=key).first()
        return record.value if record and record.value is not None else default

    @classmethod
    def set_val(cls, key: str, value: str, description: str = None):
        record = cls.query.filter_by(key=key).first()
        if not record:
            record = cls(key=key, value=value, description=description)
            db.session.add(record)
        else:
            record.value = value
            if description:
                record.description = description
        db.session.commit()

class CaseStudy(db.Model):
    __tablename__ = 'case_studies'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False) # 老屋活化, 透天改套, 頂級店面, 景觀公寓
    location = db.Column(db.String(100), default='台南市中西區')
    area_ping = db.Column(db.Float, default=45.0)
    before_rent = db.Column(db.Integer, default=18000)
    after_rent = db.Column(db.Integer, default=48000)
    roi_boost = db.Column(db.String(20), default='+166%')
    vacancy_rate = db.Column(db.String(20), default='0% (簽約即滿租)')
    tags = db.Column(db.String(200), default='包租代管,老屋翻新,日式侘寂,高投報')
    image_before = db.Column(db.String(255), nullable=True)
    image_after = db.Column(db.String(255), nullable=True)
    gallery = db.Column(db.Text, nullable=True) # JSON list of all high-res photos
    summary = db.Column(db.Text, nullable=False)
    highlights = db.Column(db.Text, nullable=True)

class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    cover_image = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), default='法規與稅務')
    author = db.Column(db.String(50), default='窩在家資產管理團隊')
    date_published = db.Column(db.String(20), default='2026-03-15')
    read_time = db.Column(db.String(20), default='5 分鐘閱讀')
    summary = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200), default='房東稅務,包租代管,租稅優惠')

class RentalListing(db.Model):
    __tablename__ = 'rental_listings'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False) # e.g. WOO-R201
    title = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='suite') # suite, apartment, townhouse, studio
    district = db.Column(db.String(50), nullable=False, default='永康區')
    address_summary = db.Column(db.String(150), nullable=True)
    rent_price = db.Column(db.Integer, nullable=False) # e.g. 13500
    management_fee = db.Column(db.Integer, default=0)
    deposit_months = db.Column(db.Integer, default=2)
    area_ping = db.Column(db.Float, default=12.0)
    floor_info = db.Column(db.String(50), default='3F/5F')
    layout = db.Column(db.String(50), default='1房1衛1陽台')
    status = db.Column(db.String(30), default='available') # available, reserved, rented
    cover_image = db.Column(db.String(255), nullable=True)
    gallery = db.Column(db.Text, nullable=True) # JSON list of images
    features = db.Column(db.String(300), default='獨立陽台,乾濕分離,獨立洗脫烘,智慧門禁,一級變頻冷暖,可申請租補')
    description = db.Column(db.Text, nullable=False)
    traffic_surroundings = db.Column(db.String(300), nullable=True)
    is_featured = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'category': self.category,
            'district': self.district,
            'address_summary': self.address_summary,
            'rent_price': self.rent_price,
            'management_fee': self.management_fee,
            'deposit_months': self.deposit_months,
            'area_ping': self.area_ping,
            'floor_info': self.floor_info,
            'layout': self.layout,
            'status': self.status,
            'cover_image': self.cover_image,
            'gallery': json.loads(self.gallery) if self.gallery else [],
            'features': [f.strip() for f in self.features.split(',') if f.strip()],
            'description': self.description,
            'traffic_surroundings': self.traffic_surroundings,
            'is_featured': self.is_featured,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }

class RentalViewingBooking(db.Model):
    __tablename__ = 'rental_viewing_bookings'

    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rental_listings.id'), nullable=True)
    rental_code = db.Column(db.String(32), nullable=True)
    rental_title = db.Column(db.String(180), nullable=True)
    renter_name = db.Column(db.String(100), nullable=False)
    renter_phone = db.Column(db.String(50), nullable=False)
    renter_line_id = db.Column(db.String(100), nullable=True)
    preferred_datetime = db.Column(db.String(100), nullable=True)
    renter_occupation = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='pending') # pending, contacted, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


