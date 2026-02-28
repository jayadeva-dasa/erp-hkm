import erpnext.accounts.report.general_ledger.general_ledger

from hkm.erpnext___custom.extend.reports.general_ledger.general_ledger import execute as hkm_general_ledger_execute

erpnext.accounts.report.general_ledger.general_ledger.execute = hkm_general_ledger_execute
