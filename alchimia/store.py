"""
va fatto un client del negoziante con cui si interagisce con il database tramite le chiamate sotto
poi va fatta una funzione che gestisce le query e le ritorna al servizio che poi le postera sul sito
"""
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('spyne.protocol.xml').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(logging.DEBUG)

from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from spyne.application import Application
from spyne.decorator import rpc
from spyne.error import ResourceNotFoundError
from spyne.protocol.soap import Soap11
from spyne.model.primitive import Mandatory
from spyne.model.primitive import Unicode
from spyne.error import InternalError
from spyne.model.fault import Fault
from spyne.model.complex import Array
from spyne.model.complex import Iterable
from spyne.model.complex import ComplexModelBase
from spyne.model.complex import ComplexModelMeta
from spyne.model.primitive import UnsignedInteger32
from spyne.server.wsgi import WsgiApplication
from spyne.service import ServiceBase


db = create_engine('sqlite:////home/luca/Documents/Anno_3/Sistemi_Aperti_e_Distribuiti/progettosaed/alchimia/prova.db')
Session = sessionmaker(bind=db)

# This is what calling TTableModel does. This is here for academic purposes.
class TableModel(ComplexModelBase):
    __metaclass__ = ComplexModelMeta
    __metadata__ = MetaData(bind=db)

class Album(TableModel):
    __tablename__ = 'album'
    __namespace__ = 'spyne.recordstore.album'
    __table_args__= {"sqlite_autoincrement": True}

    id = UnsignedInteger32(pk=True)
    title = Unicode(128)
    author = Unicode(128)
    lenght = UnsignedInteger32
    tracks = UnsignedInteger32
    genre = Unicode(64)
    label = Unicode(64) 
######################################
#CLIENT PART(REGISTERING TO SERVICE)
##############################
from suds.client import Client as SudsClient
def register_service(shop_name, my_url):
    srv_url = 'http://127.0.0.1:5000/soap/registrationservice?wsdl'
    client = SudsClient(url=url, cache=None)
    return client.service.register_shop(shop_name ,my_url)

################################################
#WEB SERVICE DEFINITION
################################################
class RecordStoreService(ServiceBase):
    """
    all query are pretty useless except get_all_album, TODO: useful things...
    """
    @rpc(Mandatory.UnsignedInteger32, _returns=Album)
    """
    gets album by id
    """
    def get_album(ctx, user_id):
        return ctx.udc.session.query(Album).filter_by(id=album_id).one()

    @rpc(Album, _returns=UnsignedInteger32)
    """
    add an album to the database and returns his id
    """
    def put_album(ctx, album):
        if album.id is None:
            ctx.udc.session.add(album)
            ctx.udc.session.flush() # so that we get the album.id value

        else:
            if ctx.udc.session.query(Album).get(album.id) is None:
                # this is to prevent the client from setting the primary key
                # of a new object instead of the database's own primary-key
                # generator.
                # Instead of raising an exception, you can also choose to
                # ignore the primary key set by the client by silently doing
                # album.id = None
                raise ResourceNotFoundError('album.id=%d' % album.id)

            else:
                ctx.udc.session.merge(album)

        return album.id

    @rpc(Mandatory.UnsignedInteger32)
    def del_album(ctx, album_id):
        """
        removes an album from the database if one with the provided id exist
        """
        count = ctx.udc.session.query(User).filter_by(id=user_id).count()
        if count == 0:
            raise ResourceNotFoundError(user_id)

        ctx.udc.session.query(User).filter_by(id=user_id).delete()
    
    @rpc(_returns=Iterable(Album))
    def get_all_album(ctx):
        """
        returns an Iterable with all albums in the database
        """
        return ctx.udc.session.query(Album)


class UserDefinedContext(object):
    def __init__(self):
        self.session = Session()

def _on_method_call(ctx):
    ctx.udc = UserDefinedContext()

def _on_method_context_closed(ctx):
    if ctx.udc is not None:
        ctx.udc.session.commit()
        ctx.udc.session.close()

class MyApplication(Application):
    def __init__(self, services, tns, name=None,
                                         in_protocol=None, out_protocol=None):
        super(MyApplication, self).__init__(services, tns, name, in_protocol,
                                                                 out_protocol)

        self.event_manager.add_listener('method_call', _on_method_call)
        self.event_manager.add_listener("method_context_closed",
                                                    _on_method_context_closed)

    def call_wrapper(self, ctx):
        try:
            return ctx.service_class.call_wrapper(ctx)

        except NoResultFound:
            raise ResourceNotFoundError(ctx.in_object)

        except Fault, e:
            logging.error(e)
            raise

        except Exception, e:
            logging.exception(e)
            raise InternalError(e)

if __name__=='__main__':
    from wsgiref.simple_server import make_server

    application = MyApplication([RecordStoreService],
                'spyne.recordstore',
                in_protocol=Soap11(validator='lxml'),
                out_protocol=Soap11(),)

    wsgi_app = WsgiApplication(application)
    server = make_server('127.0.0.1', 8000, wsgi_app)

    TableModel.Attributes.sqla_metadata.create_all()
    logging.info("listening to http://127.0.0.1:8000")
    logging.info("wsdl is at: http://localhost:8000/?wsdl")

    server.serve_forever()