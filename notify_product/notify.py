# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)


class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """    
    _inherit = 'product.product'

    def notify_product_creation(self, cr, uid, ids, context=None):
        ''' Function for notify product creation passed:
        '''
        assert len(ids) == 1, 'Work only with one product a time'
        
        # Pool used
        data_pool = self.pool.get('ir.model.data')
        group_pool = self.pool.get('res.groups')
        mail_pool = self.pool.get('mail.message')

        # Read notify group:
        group_ref = data_pool.get_object_reference(
            cr, uid, 'notify_product', 'group_notify_product')
        import pdb; pdb.set_trace()
        if not group_ref:
            _logger.error(
                '''Original group create by module not found: 
                        group_notify_product''')
            return False
        group_proxy.group_pool.browse(cr, uid, group_ref, context=context)
        recipient_ids = group_proxy.user_ids

        #recipient_links = [(4, partner_id) for partner_id in recipient_ids]
        recipient_links = [(6, 0, recipient_ids)]
        ref = data_pool.get_object_reference(
            cr, uid, 'mail', 'mt_comment')

        message = {
            'type': 'notification',
            'subject': 'Prodotto creato',
            'body': 'Creazione prodotto',
            'partner_ids': recipient_links,
            'subtype_id': ref,
            }

        mail_pool.create(cr, uid, message, context=context)
        return True
    
    # ----------------
    # Override action:
    # ----------------
    def create(self, cr, uid, vals, context=None):
        """ Create a new record for a model ProductProduct
            @param cr: cursor to database
            @param uid: id of current user
            @param vals: provides a data for new record
            @param context: context arguments, like lang, time zone
            
            @return: returns a id of new record
        """    
        res_id = super(ProductProduct, self).create(
            cr, uid, vals, context=context)
            
        # Nofitication:    
        notify_product_creation(self, cr, uid, [res_id], context=None)    
        return res_id
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
