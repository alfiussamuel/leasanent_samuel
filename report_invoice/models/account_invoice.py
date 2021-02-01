from odoo import api, models

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def total_terbilang(self, amount_total):
        """
        Function to generate word of amount
        """
        for order in self:
            unit = ["", "Satu", "Dua", "Tiga", "Empat",
                    "Lima", "Enam", "Tujuh", "Delapan",
                    "Sembilan", "Sepuluh", "Sebelas"]
            result = " "
            total_terbilang = self.total_terbilang
            n = int(amount_total)
            if n >= 0 and n <= 11:
                result = result + unit[n]
            elif n < 20:
                result = total_terbilang(n % 10) + " Belas"
            elif n < 100:
                result = total_terbilang(n / 10) + " Puluh" + total_terbilang(n % 10)
            elif n < 200:
                result = " Seratus" + total_terbilang(n - 100)
            elif n < 1000:
                result = total_terbilang(n / 100) + " Ratus" + total_terbilang(n % 100)
            elif n < 2000:
                result = " Seribu" + total_terbilang(n - 1000)
            elif n < 1000000:
                result = total_terbilang(n / 1000) + " Ribu" + total_terbilang(n % 1000)
            elif n < 1000000000:
                result = total_terbilang(n / 1000000) + " Juta" + total_terbilang(n % 1000000)
            else:
                result = total_terbilang(n / 1000000000) + " Miliar" + total_terbilang(n % 1000000000)
            return result