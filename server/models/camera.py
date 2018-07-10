from models import db
from models.account import Account


class Camera(db.Model):
    __tablename__ = 'camera'

    id = db.Column(db.Integer(), primary_key=True)
    account_id = db.Column(db.Integer(), db.ForeignKey('%s.id' % Account.__tablename__))
    name = db.Column(db.String(), nullable=False)
    status = db.Column(db.Boolean(), server_default='true')
    delay = db.Column(db.Integer(), server_default='10')
    last_update = db.Column(db.Integer(), server_default='0')
    is_complete = db.Column(db.Boolean(), server_default='true')
    detector_id = db.Column(db.Integer(), server_default='0')

    _name_idx = db.Index('name_idx', 'account_id', 'name', unique=True)
    _account_id_idx = db.Index('account_id_idx', 'account_id', unique=False)
    _last_update_idx = db.Index('last_update_idx', 'last_update', unique=False)
