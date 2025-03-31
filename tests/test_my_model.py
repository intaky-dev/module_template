from odoo.tests.common import TransactionCase

class TestMyModel(TransactionCase):

    def test_create(self):
        rec = self.env['my.model'].create({'name': 'Test'})
        self.assertEqual(rec.name, 'Test')
