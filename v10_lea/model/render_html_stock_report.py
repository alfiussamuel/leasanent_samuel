# coding: utf-8
from datetime import datetime
from openerp import models, api


class StockReport(models.AbstractModel):
    _name = 'report.v10_lea.stock_report'
    _template = 'v10_lea.stock_report'
    
    @api.multi
    def _get_barcode(self, data):        
        if data['location_id']:                
            domain = [
                      ('location_id', '=', data['location_id']),
                      ('product_id.product_category3_id', '=', data['product_category3_id']),
                      ('qty', '>', 0),                                            
                     ]            
            
        quant_ids = self.env['stock.quant'].search(domain)
        article_ids = []        
        product_ids = []        
        results = []
            
        for quant in quant_ids:
            if quant.product_id.categ_id.id not in article_ids:
                article_ids.append(quant.product_id.categ_id.id)                
            if quant.product_id.id not in product_ids:
                product_ids.append(quant.product_id.id)                
                    
        for article in article_ids:    
            article_name = self.env['product.category'].browse(article).name            
            
            intsize24 = 0
            intsize25 = 0
            intsize26 = 0
            intsize27 = 0
            intsize28 = 0
            intsize29 = 0
            intsize30 = 0
            intsize31 = 0
            intsize32 = 0
            intsize33 = 0
            intsize34 = 0
            intsize35 = 0
            intsize36 = 0
            intsize37 = 0
            intsize38 = 0
            intsize39 = 0
            intsize40 = 0
            intsize41 = 0
            intsize42 = 0
            intsize43 = 0
            intsize44 = 0
            intsizexs = 0
            intsizes = 0
            intsizem = 0
            intsizel = 0
            intsizexl = 0
            intsizexxl = 0
            intsizeal = 0
            intsizex = 0
            intsizey = 0
            intsizez = 0
            total_qty = 0                                                              
            
            for product in product_ids:
                if self.env['product.product'].browse(product).product_size_id.name == "24" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize24 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "25" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize25 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "26" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize26 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "27" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize27 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "28" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize28 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "29" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize29 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "30" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize30 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "31" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize31 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "32" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize32 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "33" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize33 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "34" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize34 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "35" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize35 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "36" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize36 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "37" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize37 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "38" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize38 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "39" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize39 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "40" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize40 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "41" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize41 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "42" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize42 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "43" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize43 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "44" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsize44 += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "XS" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsizexs += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "S" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsizes += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "M" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsizem += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "L" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsizel += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "XL" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsizexl += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "XXL" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsizexxl += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "AL" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsizeal += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "X" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsizex += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "Y" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsizey += 1
                    total_qty += 1
                elif self.env['product.product'].browse(product).product_size_id.name == "Z" and self.env['product.product'].browse(product).categ_id.id == article:
                    intsizez += 1
                    total_qty += 1
                                                
            size24 = str(intsize24)
            size25 = str(intsize25)
            size26 = str(intsize26)
            size27 = str(intsize27)
            size28 = str(intsize28)
            size29 = str(intsize29)
            size30 = str(intsize30)
            size31 = str(intsize31)
            size32 = str(intsize32)
            size33 = str(intsize33)
            size34 = str(intsize34)
            size35 = str(intsize35)
            size36 = str(intsize36)
            size37 = str(intsize37)
            size38 = str(intsize38)
            size39 = str(intsize39)
            size40 = str(intsize40)
            size41 = str(intsize41)
            size42 = str(intsize42)
            size43 = str(intsize43)
            size44 = str(intsize44)
            sizexs = str(intsizexs)
            sizes = str(intsizes)
            sizem = str(intsizem)
            sizel = str(intsizel)
            sizexl = str(intsizexl)
            sizexxl = str(intsizexxl)
            sizeal = str(intsizeal)
            sizex = str(intsizex)
            sizey = str(intsizey)
            sizez = str(intsizez)
                                                                                                                                            
            if size24 == '0':
                size24 = ''
            if size25 == '0':
                size25 = ''
            if size26 == '0':
                size26 = ''
            if size27 == '0':
                size27 = ''
            if size28 == '0':
                size28 = ''
            if size29 == '0':
                size29 = ''
            if size30 == '0':
                size30 = ''
            if size31 == '0':
                size31 = ''
            if size32 == '0':
                size32 = ''
            if size33 == '0':
                size33 = ''
            if size34 == '0':
                size34 = ''
            if size35 == '0':
                size35 = ''
            if size36 == '0':
                size36 = ''
            if size37 == '0':
                size37 = ''
            if size38 == '0':
                size38 = ''
            if size39 == '0':
                size39 = ''
            if size40 == '0':
                size40 = ''
            if size41 == '0':
                size41 = ''
            if size42 == '0':
                size42 = ''
            if size43 == '0':
                size43 = ''
            if size44 == '0':
                size44 = ''
            if sizexs == '0':
                sizexs = ''
            if sizes == '0':
                sizes = ''
            if sizem == '0':
                sizem = ''            
            if sizel == '0':
                sizel = ''
            if sizexl == '0':
                sizexl = ''
            if sizexxl == '0':
                sizexxl = ''
            if sizeal == '0':
                sizeal = ''
            if sizex == '0':
                sizex = ''
            if sizey == '0':
                sizey = ''
            if sizez == '0':
                sizez = ''
                
            results.append({
                            'article_name': article_name,     
                            'size24' : size24,
                            'size25' : size25,
                            'size26' : size26,
                            'size27' : size27,
                            'size28' : size28,
                            'size29' : size29,
                            'size30' : size30,
                            'size31' : size31,
                            'size32' : size32,
                            'size33' : size33,
                            'size34' : size34,
                            'size35' : size35,
                            'size36' : size36,
                            'size37' : size37,
                            'size38' : size38,
                            'size39' : size39,
                            'size40' : size40,
                            'size41' : size41,
                            'size42' : size42,
                            'size43' : size43,
                            'size44' : size44,
                            'sizexs' : sizexs,
                            'sizes' : sizes,
                            'sizem' : sizem,
                            'sizel' : sizel,
                            'sizexl' : sizexl,
                            'sizexxl' : sizexxl,
                            'sizeal' : sizeal,
                            'sizex' : sizex,
                            'sizey' : sizey,
                            'sizez' : sizez,       
                            'total_qty' : total_qty,                                                                        
                            })
            
        return results


    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],                
            'get_barcode': self._get_barcode,            
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs
        }

        return report_obj.render(self._template, docargs)
