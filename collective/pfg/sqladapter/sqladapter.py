from zope.interface import implements
from AccessControl import ClassSecurityInfo
from Products.Archetypes import atapi
from Products.ATContentTypes.content import schemata
from Products.PloneFormGen.interfaces import IPloneFormGenActionAdapter
from Products.PloneFormGen.content.actionAdapter import FormAdapterSchema
from Products.PloneFormGen.content.actionAdapter import FormActionAdapter
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.expression import insert
from zope.sqlalchemy import ZopeTransactionExtension
from collective.pfg.sqladapter.interfaces import ISQLAdapter
from collective.pfg.sqladapter.config import PROJECTNAME
from collective.pfg.sqladapter import _


SQLAdapterSchema = FormAdapterSchema.copy() + atapi.Schema((

    atapi.StringField(
        'dsn',
        required=True,
        widget=atapi.StringWidget(
            label=_(u"label_dsn", default=u"DSN"),
            description=_(u"help_dsn", 
                default=u"Provide the data source name for the database. "
                         "(e.g. mysql://user:password@localhost/db)")
         ),
    ),

    atapi.StringField(
        'tablename',
        required=True,
        widget=atapi.StringWidget(
            label=_(u"label_tablename", default=u"Table Name"),
            description=_(u"help_tablename",
                default=u"Provide the name of the table where form input "
                         "data should be saved to. If the table doesn't "
                         "exist yet, it will be created.")
         ),
    ),


))

schemata.finalizeATCTSchema(SQLAdapterSchema, moveDiscussion=False)


class SQLAdapter(FormActionAdapter):
    """A form action adapter that saves form input data in a SQL database"""
    implements(IPloneFormGenActionAdapter, ISQLAdapter)

    portal_type = "SQLAdapter"
    schema = SQLAdapterSchema
    security = ClassSecurityInfo()

    def onSuccess(self, fields, REQUEST=None):
        """Save form input in SQL database.
        """

        session = self.getSession()
        metadata = MetaData(bind=session.bind)
        table = Table(self.getTablename(), metadata, autoload=True)
        session.bind_table(table, session.bind)
        
        record = {}
        for field in fields:
            fname = field.fgField.getName()
            if fname in table.columns:
                val = REQUEST.form.get(fname, '')
                record[fname] = val
        if record:
            # TODO: use the session for inserts
            #session.execute(table.insert().values(record))
            table.insert().execute(record)


    security.declarePrivate("getSession")
    def getSession(self):
        engine = create_engine(self.getDsn())
        Session = scoped_session(sessionmaker(bind=engine,
                                 extension=ZopeTransactionExtension()))
        return Session()

atapi.registerType(SQLAdapter, PROJECTNAME)
