# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Software Solutions
#    Copyright (C) 2004-2010 Globalteckz (<http:www.globalteckz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models,fields,api,_
from odoo.exceptions import UserError
import StringIO
import base64
import csv
import xlsxwriter
from odoo.tools.misc import xlwt


class DynamicExcelReport(models.Model):
    _name = 'dynamic.xls.report'

    model_name =  fields.Many2one('ir.model','Model',help="Select the model name.")

    field_name = fields.Many2many('ir.model.fields','rel_fields_model_rpt','wiz_id','rec_id','Field Name', help="Select the required fields.",copy=True)
    # field_name = fields.One2many('ir.model.fields','fields_id','Field Name', help="Select the required fields.",copy=True)

    search_domain = fields.Char('Domain')
    m2m_value = fields.Boolean('Value instead of id ?', help='Select if You want the value instead of id for Many2one field')
    filedata = fields.Binary('File', readonly=True)
    filename = fields.Char('Filename', size = 64, readonly=True)
    limit_rec = fields.Integer('Limit', help="Limit your records")
    order_type = fields.Boolean('Descending Order ?',help='Check if you want the records in descending order')
    order_on_field = fields.Many2one('ir.model.fields','Order BY',domain="[('model_id','=',model_name)]",help="Select the field by which you want to sort.")
    set_offset = fields.Integer('Offset')
    domain_lines = fields.One2many('dynamic.domain.line','dynamic_rpt_id', 'Domain',help="Put the domain if any")
    action_window=fields.Many2one('ir.actions.act_window')
    action_value=fields.Many2one('ir.values')


    group_by=fields.Boolean('Group By')
    group_by_field=fields.Many2one('ir.model.fields','Group By Field',domain=[
            ('state', 'in', ['sale', 'done'])])
    # group_by_field=fields.Many2one('ir.model.fields','Group By Field',domain=[
    #         ('state', 'in', ['sale', 'done'])],compute="_compute_call")


    excel_sheet_name=fields.Char('')
    header_text=fields.Char('',required=True)
    sum_bkg_col=fields.Char('Sum Background Color')
    total_font_col=fields.Char('Total Font Color')

    # company_txt_stye=fields.Char('Text Style')
    # company_italic=fields.Boolean('Italic')
    # company_txt_size=fields.Char('Text Size')
    # company_underline=fields.Boolean('Underline')
    # company_txt_color=fields.Char('Text Color')
    # company_txt_align=fields.Selection([('right','Right'),('left','Left'),('center','Center')],default="left", string ='Text Align')
    # company_bkg_col=fields.Char('Background Color')
    # company_border=fields.Boolean('Border')
    # company_bold=fields.Boolean('Bold')
    # company_border_color=fields.Char('Border Color')

    header_txt_stye = fields.Char('Text Style')
    header_italic = fields.Boolean('Italic')
    header_txt_size = fields.Char('Text Size')
    header_underline = fields.Boolean('Underline')
    header_txt_color = fields.Char('Text Color')
    header_txt_align = fields.Selection([('right', 'Right'), ('left', 'Left'), ('center', 'Center')], default="center", string='Text Align')
    header_bkg_col = fields.Char('Background Color')
    header_border = fields.Boolean('Border')
    header_bold = fields.Boolean('Bold')
    header_border_color = fields.Char('Border Color')

    group_txt_stye = fields.Char('Text Style')
    group_italic = fields.Boolean('Italic')
    group_txt_size = fields.Char('Text Size')
    group_underline = fields.Boolean('Underline')
    group_txt_color = fields.Char('Text Color')
    group_txt_align = fields.Selection([('right', 'Right'), ('left', 'Left'), ('center', 'Center')], default="left", string='Text Align')
    group_bkg_col = fields.Char('Background Color')
    group_border = fields.Boolean('Border')
    group_sub_bkg_col=fields.Char('Subgroup Background Color')
    group_border_color = fields.Char('Border Color')
    group_bold = fields.Boolean('Bold')



    @api.multi
    def get_xls(self,token):

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(self.header_text or 'Sheet-1')

        field_model = self.env['ir.model.fields']
        for val in self:
            model = val.model_name.model
            model_obj = self.env[model]

            field_sel = []
            lable_sel = []
            for field_name in val.field_name:
                field_sel.append(field_name.name)
                lable_sel.append(field_name.field_description)


            if self.group_by and self.group_by_field.name not in field_sel:
                field_sel.append(self.group_by_field.name)
                # lable_sel.append(self.group_by_field.field_description)


            if not len(field_sel):
                fld = field_model.search([('model_id','=',val.model_name.id),('ttype','!=','binary')])
                if len(fld):
                    for f in field_model.browse(fld):
                        field_sel.append(f.name)
                else:
                    raise UserError(_('No column found to Export'))
            domain = []
            for d_line in val.domain_lines:
                temp = ()
                d_val = str(d_line.value) or False
                if d_val in ('false','False'):
                    d_val = False
                if d_val in ('true','True'):
                    d_val  = True
                temp = (str(d_line.field_name.name),str(d_line.operator),d_val)
                domain.append(temp)
            limit = val.limit_rec or None
            order_field = val.order_on_field and val.order_on_field.name or None
            if order_field and val.order_type:
                order = order_field +' desc'
            elif order_field:
                order = order_field
            else:
                order = None


            # if self.group_by:
            #     try:
            #         grp_recs= model_obj.read_group(domain, field_sel, self.group_by_field.name, offset=val.set_offset, limit = limit, order =  order )
            #     except:
            #         grp_recs= model_obj.read_group(domain, field_sel, self.group_by_field.name, offset=val.set_offset, limit = limit, orderby =  order )
            #         print"----------------------------------- grp_recs ----------------------",grp_recs
            #
            #     if not field_sel:
            #         if grp_recs:
            #             field_sel = grp_recs[0].keys()
            #         else:
            #             raise UserError(_('No record found to Export'))
            #
            #     result = []
            #     # result.append(field_sel)
            #
            #     for rec in grp_recs:
            #         value = ''
            #         temp = []
            #         for key in field_sel:
            #             print"-------------------------- grp_key --------------------", key
            #             v = rec.get(key)
            #             if v:
            #                 if type(v) == tuple:
            #                     if val.m2m_value:
            #                         value = v[1]
            #                     else:
            #                         value = v[0]
            #                 else:
            #                     value = str(v)
            #             else:
            #                 value = v
            #             temp.append(value)
            #         result.append(temp)
            #

            # else:
            try:
                recs = model_obj.search_read(domain, field_sel, offset=val.set_offset, limit = limit, order =  order )
                # print"-----------------------------------recs-----------------------",recs
            except:
                mod_ids = model_obj.search(domain, offset=val.set_offset, limit = limit, order =  order )
                recs = model_obj.read(mod_ids,field_sel)

            if not field_sel:
                if recs:
                    field_sel = recs[0].keys()
                else:
                    raise UserError(_('No record found to Export'))


            result = []
            # result.append(field_sel)



            if self.group_by:
                dict_grp={}
                # a = self.group_by_field.name
                # print "========================== recs ==================", recs
                for rec in recs:
                    value = ''
                    temp = []
                    key1 = rec.get(self.group_by_field.name)
                    # print "========================== rec ==================", rec
                    # print "========================== a ===================", self.group_by_field.name
                    # print
                    if not dict_grp.get(key1):
                        dict_grp.update({key1: [rec]})
                    else:
                        dict_grp.update({key1: dict_grp[key1]+ [rec]})
                    # print "========================== dict ===================", dict_grp


                    for key in field_sel:
                        # print"-------------------------- key --------------------",key
                        v = rec.get(key)
                        if v:
                            if type(v) == tuple:
                                if val.m2m_value:
                                    value = v[1]
                                else:
                                    value = v[0]
                            else:
                                value = str(v)
                        else:
                            value = v
                        temp.append(value)

                        # dict_grp.update({a: temp})
                    # print "-------------- dict ----------",dict_grp

                    result.append(temp)
                    # print "dodddddddddddddddddddddd",dict_grp


            else:
                for rec in recs:
                    value = ''
                    temp = []
                    for key in field_sel:
                        # print"-------------------------- key --------------------", key
                        v = rec.get(key)
                        # print"------------------------- rec ----------------------",rec
                        # print"------------------------- v ----------------------",v
                        if v:
                            if type(v) == tuple:
                                if val.m2m_value:
                                    value = v[1]
                                else:
                                    value = v[0]
                            else:
                                value = str(v)
                        else:
                            value = v
                        temp.append(value)
                    # print"----------- temp ------------------",temp
                    result.append(temp)
                # print"----------- result ------------------",result





            style_table_header = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center; pattern: pattern solid, fore_colour gray25;')
            style_col_header = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center; pattern: pattern solid, fore_colour gray25;')
            style_grp_header = xlwt.easyxf('font: bold on; align: wrap on, vert centre; pattern: pattern solid, fore_colour gray50;')
            data_style = xlwt.easyxf('align: wrap on, vert centre, horiz center;')
            # datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')


    # Write Header Cell
    #         header_cell = len(field_sel) / 2
    #         if self.group_by:
                # print"============== before =================",field_sel
                # field_sel.pop()
                # print"============== after =================",field_sel

            worksheet.write_merge(1, 2, 1, len(field_sel)-2,self.header_text,style_table_header)


            # worksheet.write(0, header_cell,self.header_text,style_table_header)
            # if (len(field_sel) % 2) == 0:
            #     worksheet.write_merge(1, 2, header_cell-1, header_cell, self.header_text, style_table_header)
            # else:
            #     worksheet.write_merge(1, 2, header_cell, header_cell,self.header_text,style_table_header)



    # Write Table Header Row
            for i, field_name in enumerate(lable_sel):
                worksheet.write_merge(4, 5, i, i, field_name, style_col_header)
                # worksheet.write(3, i, field_name,style_col_header)
                worksheet.col(i).width = 5000  # around 220 pixels
                # print"--------------- lable_sel------------------------",lable_sel



    # Write Table Data Row
            if self.group_by:
                # print"------------ group_by--------------------"
                row_no = 7
                row=6

                for grp in dict_grp:
                    # print"------------------- grp ---------------",dict_grp
                    # print"------------------- grp ---------------",grp
                    # print"------------------- grp ---------------",grp[1]
                    worksheet.write_merge(row, row, 0, 5, grp[1], style_grp_header)
                    row += 1
                    for data in dict_grp[grp]:
                        # print"--------------data----------------",data
                        # print"----------------",data.values

                        # worksheet.write(row, i, data[i], data_style)
                        i = 0
                        # for key, value in data.iteritems():
                        for key in field_sel:
                            v=data.get(key)
                            if v:
                                if type(v) == tuple:
                                    if val.m2m_value:
                                        value = v[1]
                                    else:
                                        value = v[0]
                                else:
                                    value = str(v)
                            else:
                                value = v

                            # print"-00000000000000 vvvvvvvvvvvvvv 000000000000000000",v
                            # print"-000000000000000 value value value 0000000000000-",value

                            worksheet.write(row, i, value, data_style)
                            i+=1
                        row+=1
                    row += 1


                # for data in result:
                #
                #     print"--------------- data in result------------------------", data
                #     # print"--------------- self.group_by_field ------------------------",self.group_by_field.id
                #
                #     for i, vals in enumerate(data):
                #         worksheet.write(row_no, i, vals, data_style)
                #         worksheet.col(i).width = 5000  # around 220 pixels
                #         # print"--------------- field vals------------------------",vals
                #     row_no += 1

            else:
                # print"------------ NOT group_by--------------------"
                row_no=6
                for data in result:
                    # print"--------------- data in result------------------------", data
                    for i, vals in enumerate(data):
                        worksheet.write(row_no, i, vals, data_style)
                        worksheet.col(i).width = 5000  # around 220 pixels
                        # print"--------------- field vals------------------------",vals
                    row_no+=1

                # Same as above
                # row =3; c_nbr =0
                # for data in result:
                #     c_nbr =0
                #     print"++++++++++++++++++++++++ data +++++++++++++++++++++++++++++",i,data
                #     for vals in data:
                #         worksheet.write(row, c_nbr, vals)
                #         worksheet.col(c_nbr).width = 8000  # around 220 pixels
                #         c_nbr += 1
                #     row += 1


            file_name = str(val.model_name.name) + '.xls'

            fp = StringIO.StringIO()
            workbook.save(fp)
            fp.seek(0)
            data = fp.read()
            fp.close()
            out=base64.encodestring(data)

            self.write({'filedata':out, 'filename':file_name})

        return {
            'name':'Dynamic Report',
            'res_model':'dynamic.xls.report',
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'form',
            'target':'new',
            'view_id': self.env.ref('gt_dynamic_global_export_excel_report.wizard_dynamic_xls_report_download').id,
            'res_id': self.id
        }
    # dynamic_xls_report()


    @api.one
    def add_action_model(self):
        # print "--------------------called add----------------------"

        if not self.field_name:
            raise UserError(_("Please Select Atleast One Field To export."))
        res={
            'name': self.excel_sheet_name,
            'res_model': 'dynamic.xls.report',
            'src_model':self.model_name.model,
            'type': 'ir.actions.act_window',
            # 'key2': 'client_action_multi',
            'multi':'True',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('gt_dynamic_global_export_excel_report.wizard_dynamic_xls_report').id,
            'target': 'new',
            'res_id': self.id
        }

        act_id=self.env['ir.actions.act_window'].create(res)

        res2 = {
            'name': 'Export',
            'model_id':self.model_name.id,
            'key2':'client_action_multi',
            'value':'ir.actions.act_window,'+str(act_id.id),
            'key':'action',
            'model': self.model_name.model,

        }
        act2_id=self.env['ir.values'].create(res2)
        # print"----------------------------------------",act_id,act2_id
        self.write({'action_window':act_id.id,'action_value':act2_id.id})
        return True

    @api.one
    def remove_action_model(self):
        # print"------------------called remove---------------"
        if self.action_window :
            self.sudo().action_window.unlink()

        if self.action_value:
            self.sudo().action_value.unlink()

        return True

    # @api.model
    # def create(self, vals):
    #
    #     grp_field=vals.get('group_by_field')
    #     selected_field=vals.get('field_name')
    #
    #     if not grp_field in selected_field[0][2]:
    #         print"----------------- no -------------------",grp_field
    #         print"----------------- no -------------------",selected_field
    #         raise UserError(_(
    #                 'Configuration Error!, Your Group By Field must be from your Selected Fields.'))
    #     print"-------------------- vals ------------------------",vals
    #     res = super(DynamicExcelReport, self).create(vals)
    #     # print x
    #     return res
    #

    @api.multi
    def write(self, vals):

        # print"======================== vals ---------------------------",vals
        # grp_field = vals.get('group_by_field')
        # selected_field = self.field_name
        # print"========================  ---------------------------",grp_field
        # print"========================  ---------------------------",selected_field
        #
        #
        # if not grp_field in selected_field:
        #     print"----------------- no -------------------", grp_field
        #     print"----------------- no -------------------", selected_field
        #     raise UserError(_(
        #         'Configuration Error!, Your Group By Field must be from your Selected Fields.'))
        # print"-------------------- vals ------------------------", vals

        if self.action_window:
            self.remove_action_model()
            self.add_action_model()

        return super(DynamicExcelReport, self).write(vals)





class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'
    # _order='sequence'

    sequence = fields.Integer(string='Sequence')
    # fields_id=fields.Many2one('dynamic.xls.report')

class dynamic_domain_line(models.Model):
    _name = 'dynamic.domain.line'

    dynamic_rpt_id = fields.Many2one('dynamic.xls.report','Relation Field')
    field_name = fields.Many2one('ir.model.fields','Field Name',domain="[('model_id','=',parent.model_name)]")
    operator = fields.Selection([('ilike','Contains'),('=','Equal'),('!=','Not Equal'),('<','Less Than'),('>','Greater Than'),('<=','Less Than Equal To'),('>=','Greater Than Equal To')],'Operator')
    value = fields.Char('Value',help='For relation use dot(.) with field name')