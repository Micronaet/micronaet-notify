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


class SaleOrder(orm.Model):
    """ Model name: SaleOrder
    """    
    _inherit = 'sale.order'

    def schedule_notify_new_sale_order_product(self, cr, uid, days_left=1, 
            context=None):
        ''' Check new product creation and sale order        
        '''          
        context = context or {}
        context['days_left'] = days_left
        return self.notify_sale_new_product_operation(cr, uid, 0, 
            context=context)
        
    def notify_sale_new_product_operation(self, cr, uid, ids, days_left=1, 
            context=None):
        ''' Function for notify product creation passed:
            Context parameters:
            notify_operation > 'create', 'write'
        '''
        context = context or {}
        days_left = context.get('days_left', 1)
        
        # Pool used
        data_pool = self.pool.get('ir.model.data')
        group_pool = self.pool.get('res.groups')
        mail_pool = self.pool.get('mail.message')
        product_pool = self.pool.get('product.product')
        sol_pool = self.pool.get('sale.order.line')
        
        try:
            # ------------------
            # Read notify group:
            # ------------------
            group_ref = data_pool.get_object_reference(
                cr, uid, 'notify_sale_new_product', 'group_notify_sale_new_product')
            group_id = group_ref[1]    
            if not group_id:
                _logger.error(
                    '''Original group create by module not found: 
                            group_notify_sale_new_product''')
                return False                
            group_proxy = group_pool.browse(cr, uid, group_id, context=context)
            recipient_ids = [item.partner_id.id for item in group_proxy.users]
            if not recipient_ids:
                _logger.error(
                    'No recipients in group: group_notify_sale_new_product')
                return False

            recipient_links = [(6, 0, recipient_ids)]
            ref = data_pool.get_object_reference(
                cr, uid, 'mail', 'mt_comment')

            # -------------------
            # Search new product:
            # -------------------
            bottom_date = (datetime.now() - timedelta(
                days=days_left)).strftime(
                    DEFAULT_SERVER_DATE_FORMAT) # no datetime (for time 0:00:00)

            product_ids = product_pool.search(cr, uid, [
                ('create_date', '>=', bottom_date),
                ], context=context)
            if not product_ids:
                return True
            
            # ----------------------------------------
            # Search sale.order.line for that product:
            # ----------------------------------------
            sol_ids = sol_pool.search(cr, uid, [
                ('product_id', 'in', product_ids)], order='order_id', 
                context=context)    

            if not sol_ids:
                return True
            
            body = _('Find %s new product in last %s days') % (
                len(product_ids), days_left)
            body += '''
                <style>
                    .table_bf {
                         border:1px 
                         padding: 3px;
                         solid black;
                     }
                    .table_bf td {
                         border:1px 
                         solid black;
                         padding: 3px;
                         text-align: center;
                     }
                    .table_bf th {
                         border:1px 
                         solid black;
                         padding: 3px;
                         text-align: center;
                         background-color: grey;
                         color: white;
                     }
                </style>
                <table class='table_bf'>
                   <tr>
                       <th>Order</th>
                       <th>Customer</th>
                       <th>Code</th>
                       <th>Qty</th>
                       <th>State</th>
                   </tr>'''
            
            company_name = ''
            for line in sol_pool.browse(cr, uid, sol_ids, context=context):
                if not company_name:
                    company_name = line.order_id.company_id.name
                if line.order_id.state in ('draft', 'sent'):
                    state = 'quotation'
                elif line.order_id.state in ('cancel'):
                    state = 'cancel'
                else:    
                    state = 'order'
                  
                body += '''
                   <tr>
                       <td>&nbsp;&nbsp;%s&nbsp;&nbsp;</td>
                       <td>&nbsp;&nbsp;%s&nbsp;&nbsp;</td>
                       <td>&nbsp;&nbsp;%s&nbsp;&nbsp;</td>
                       <td>&nbsp;&nbsp;%s&nbsp;&nbsp;</td>
                       <td class='{text-align: right;}'>%s</td>
                   </tr>''' % (
                       line.order_id.name,
                       line.order_id.partner_id.name,
                       line.product_id.default_code,
                       line.product_uom_qty,
                       state,
                       )                
            body += '''</table>'''    
                    
            message = {
                'type': 'notification',
                'subject': _('%s: Order with new product') % company_name,
                'body': body,
                'partner_ids': recipient_links,
                'subtype_id': ref[1],
                }

            mail_pool.create(cr, uid, message, context=context)
        except: 
            _logger.error('Error sending email for notify creation!')
        return True    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
