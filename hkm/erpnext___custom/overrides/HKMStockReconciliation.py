from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import StockReconciliation


class HKMStockReconciliation(StockReconciliation):
    def set_current_serial_and_batch_bundle(self, voucher_detail_no=None, save=False):
        # Save which items the user has explicitly flagged for zero valuation
        # before the core method overwrites valuation_rate with current_valuation_rate
        zero_valuation_items = {
            item.name
            for item in self.items
            if item.allow_zero_valuation_rate
        }

        super().set_current_serial_and_batch_bundle(
            voucher_detail_no=voucher_detail_no, save=save
        )

        # Restore zero valuation rate — core logic at line ~233 treats 0 as falsy
        # and replaces it with current_valuation_rate, which we undo here
        for item in self.items:
            if item.name in zero_valuation_items:
                item.valuation_rate = 0
