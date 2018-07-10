from models import db
from models.camera import Camera


class Place(db.Model):
    __tablename__ = 'place'

    id = db.Column(db.Integer(), primary_key=True)
    camera_id = db.Column(db.Integer(), db.ForeignKey('%s.id' % Camera.__tablename__))
    status = db.Column(db.Boolean(), server_default='false')
    label = db.Column(db.String(), nullable=False)
    x = db.Column(db.Integer(), nullable=False)
    y = db.Column(db.Integer(), nullable=False)

    _idx = db.Index('camera_label_idx', 'camera_id', 'label', unique=True)
