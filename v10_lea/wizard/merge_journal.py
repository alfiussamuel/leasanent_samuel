from odoo.exceptions import UserError
from odoo import api,fields,models,_


class MergeAccountMove(models.TransientModel):
    _name = "merge.account.move"
    _description = "Merge Account Move"

    company_id = fields.Many2one('res.company', string='Organisasi', default=lambda self:self.env.user.company_id)
    journal_id = fields.Many2one('account.journal', 'Journal')
    desc = fields.Char('Keterangan')
    date = fields.Date('Tanggal Journal', default=fields.Date.today())
    type = fields.Selection([('Debit','Debit'),('Credit','Credit'),('Debit Credit','Debit Credit'),('Tidak Gabung','Tidak Gabung')], string="Tipe", default="Tidak Gabung")
    
    @api.multi
    def merge_move(self):
        context = dict(self._context or {})
        moves = self.env['account.move'].browse(context.get('active_ids'))
        move_to_unpost = self.env['account.move']
        data_final = []
        if self.type == "Tidak Gabung":
            for move in moves:                        
                for line in move.line_ids:
                    if line.debit > 0:
                        debit_line_vals = (0,0,{
                                'name': line.name,
                                'partner_id': line.partner_id.id,
                                'journal_id': line.journal_id.id,
                                'date': line.date,
                                'company_id': line.company_id.id,
                                'account_id': line.account_id.id,                                        
                                'debit': line.debit,              
                                'credit': line.credit,      
                            })
                        data_final.append(debit_line_vals)
                    elif line.credit > 0:
                        credit_line_vals = (0,0,{
                                'name': line.name,
                                'partner_id': line.partner_id.id,
                                'journal_id': line.journal_id.id,
                                'date': line.date,
                                'company_id': line.company_id.id,
                                'account_id': line.account_id.id,                                        
                                'debit': line.debit,              
                                'credit': line.credit,
                            })
                        data_final.append(credit_line_vals)
                                                                                                
            AccountMove = self.env['account.move']
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.create({
                'journal_id': self.journal_id.id,
                'line_ids': data_final,
                'date': self.date,
                'ref':self.desc,
                })        
            new_account_move.post()
            
        elif self.type == "Debit":                        
            debit_list = []                    
            for move in moves:                                  
                for line in move.line_ids:
                    if line.debit > 0:                                                                                                                                            
                        debit_list.append({
                                           'name': line.name,
                                           'partner_id': line.partner_id.id,
                                           'journal_id': line.journal_id.id,
                                           'date': line.date,
                                           'company_id': line.company_id.id,
                                           'account_id': line.account_id.id,                                        
                                           'debit': line.debit,              
                                           'credit': line.credit,
                                           })                                                                                                                                                                                                                                        
                                                                    
                    if line.credit > 0:
                        credit_line_vals = (0,0,{
                                 'name': line.name,
                                 'partner_id': line.partner_id.id,
                                 'journal_id': line.journal_id.id,
                                 'date': line.date,
                                 'company_id': line.company_id.id,
                                 'account_id': line.account_id.id,                                        
                                 'debit': line.debit,              
                                 'credit': line.credit,
                                 })
                        data_final.append(credit_line_vals)
                                                    
            final_list = {}            
            for debit in debit_list:                                
                tmp = "" + str(debit['account_id']) + "-" + str(debit['partner_id'])
                if tmp in final_list:                                        
                    final_list[tmp]['debit'] += debit['debit']                    
                else:                    
                    final_list[tmp] = debit                    
                
            final_debit = []
            for key, final in final_list.items():                
                final_debit.append((0,0, final))                
                                        
            for final in final_debit:
                data_final.append(final)                                
                                                                                                            
            AccountMove = self.env['account.move']            
            new_account_move = AccountMove.create({
                'journal_id': self.journal_id.id,
                'line_ids': data_final,
                'date': self.date,
                'ref':self.desc,
                })        
            new_account_move.post()
                        
        elif self.type == "Credit":                        
            credit_list = []                    
            for move in moves:                                  
                for line in move.line_ids:
                    if line.credit > 0:                                                                                                                                            
                        credit_list.append({
                                           'name': line.name,
                                           'partner_id': line.partner_id.id,
                                           'journal_id': line.journal_id.id,
                                           'date': line.date,
                                           'company_id': line.company_id.id,
                                           'account_id': line.account_id.id,                                        
                                           'debit': line.debit,              
                                           'credit': line.credit,
                                           })                                                                                                                                                                                                                                        
                                                                    
                    if line.debit > 0:
                        debit_line_vals = (0,0,{
                                 'name': line.name,
                                 'partner_id': line.partner_id.id,
                                 'journal_id': line.journal_id.id,
                                 'date': line.date,
                                 'company_id': line.company_id.id,
                                 'account_id': line.account_id.id,                                        
                                 'debit': line.debit,              
                                 'credit': line.credit,
                                 })
                        data_final.append(debit_line_vals)
                                                    
            final_list = {}            
            for credit in credit_list:                                
                tmp = "" + str(credit['account_id']) + "-" + str(credit['partner_id'])
                if tmp in final_list:                                        
                    final_list[tmp]['credit'] += credit['credit']                    
                else:                    
                    final_list[tmp] = credit                    
                
            final_credit = []
            for key, final in final_list.items():                
                final_credit.append((0,0, final))                
                                        
            for final in final_credit:
                data_final.append(final)                                
                                                                                                            
            AccountMove = self.env['account.move']            
            new_account_move = AccountMove.create({
                'journal_id': self.journal_id.id,
                'line_ids': data_final,
                'date': self.date,
                'ref':self.desc,
                })        
            new_account_move.post()
            
        elif self.type == "Debit Credit":                        
            debit_list = []
            credit_list = []                    
            for move in moves:                                  
                for line in move.line_ids:
                    if line.credit > 0:                                                                                                                                            
                        credit_list.append({
                                           'name': line.name,
                                           'partner_id': line.partner_id.id,
                                           'journal_id': line.journal_id.id,
                                           'date': line.date,
                                           'company_id': line.company_id.id,
                                           'account_id': line.account_id.id,                                        
                                           'debit': line.debit,              
                                           'credit': line.credit,
                                           })                                                                                                                                                                                                                                        
                                                                    
                    if line.debit > 0:
                        debit_list.append({
                                           'name': line.name,
                                           'partner_id': line.partner_id.id,
                                           'journal_id': line.journal_id.id,
                                           'date': line.date,
                                           'company_id': line.company_id.id,
                                           'account_id': line.account_id.id,                                        
                                           'debit': line.debit,              
                                           'credit': line.credit,
                                           })
                                                    
            final_list_debit = {}            
            for debit in debit_list:                                
                tmp_debit = "" + str(debit['account_id']) + "-" + str(debit['partner_id'])
                if tmp_debit in final_list_debit:                                        
                    final_list_debit[tmp_debit]['debit'] += debit['debit']                    
                else:                    
                    final_list_debit[tmp_debit] = debit                
            final_list_credit = {}            
            for credit in credit_list:                                
                tmp_credit = "" + str(credit['account_id']) + "-" + str(credit['partner_id'])
                if tmp_credit in final_list_credit:                                        
                    final_list_credit[tmp_credit]['credit'] += credit['credit']                    
                else:                    
                    final_list_credit[tmp_credit] = credit                    
                
            final_debit = []
            for key, final in final_list_debit.items():                
                final_debit.append((0,0, final))                
            final_credit = []
            for key, final in final_list_credit.items():                
                final_credit.append((0,0, final))                
                                        
            for final in final_credit:
                data_final.append(final)
            for final in final_debit:
                data_final.append(final)                                
                                                                                                            
            AccountMove = self.env['account.move']            
            new_account_move = AccountMove.create({
                'journal_id': self.journal_id.id,
                'line_ids': data_final,
                'date': self.date,
                'ref':self.desc,
                })        
            new_account_move.post()            
                                                                
        return {'type': 'ir.actions.act_window_close'}
