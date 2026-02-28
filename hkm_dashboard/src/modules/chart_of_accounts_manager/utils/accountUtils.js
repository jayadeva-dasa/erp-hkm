/**
 * Format currency value with CR/DR notation
 * @param {number} value - Value to format
 * @param {string} currency - Currency code (default: INR)
 * @param {boolean} showCrDr - Show CR/DR notation (default: true)
 */
export const formatCurrency = (value, currency = 'INR', showCrDr = true) => {
  if (value === null || value === undefined) return '-';
  
  const absValue = Math.abs(value);
  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  
  const formatted = formatter.format(absValue);
  
  if (!showCrDr) {
    return value >= 0 ? formatted : `(${formatted})`;
  }
  
  // Positive = Debit (DR), Negative = Credit (CR)
  const suffix = value >= 0 ? ' DR' : ' CR';
  return formatted + suffix;
};

/**
 * Format number with Indian numbering system
 * @param {number} value - Value to format
 */
export const formatNumber = (value) => {
  if (value === null || value === undefined) return '-';
  
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * Get account type color
 * @param {string} accountType - Account type
 */
export const getAccountTypeColor = (accountType) => {
  const colorMap = {
    'Asset': 'blue',
    'Liability': 'red',
    'Equity': 'purple',
    'Income': 'green',
    'Expense': 'orange',
    'Cost of Goods Sold': 'pink',
  };
  
  return colorMap[accountType] || 'gray';
};

/**
 * Get account type icon
 * @param {string} accountType - Account type
 */
export const getAccountTypeIcon = (accountType) => {
  const iconMap = {
    'Asset': '💰',
    'Liability': '📊',
    'Equity': '🏦',
    'Income': '💵',
    'Expense': '💸',
    'Cost of Goods Sold': '📦',
  };
  
  return iconMap[accountType] || '📁';
};

/**
 * Build tree structure from flat account list
 * @param {Array} accounts - Flat list of accounts
 * @param {number} maxDepth - Maximum depth to show
 */
export const buildAccountTree = (accounts, maxDepth = null) => {
  if (!accounts || accounts.length === 0) return [];
  
  const accountMap = new Map();
  const rootAccounts = [];
  
  // First pass: create map of all accounts
  accounts.forEach(account => {
    accountMap.set(account.name, {
      ...account,
      children: [],
      expanded: maxDepth === null || account.level <= maxDepth,
    });
  });
  
  // Second pass: build tree structure
  accounts.forEach(account => {
    const node = accountMap.get(account.name);
    
    if (account.parent_account) {
      const parent = accountMap.get(account.parent_account);
      if (parent) {
        parent.children.push(node);
      } else {
        rootAccounts.push(node);
      }
    } else {
      rootAccounts.push(node);
    }
  });
  
  return rootAccounts;
};

/**
 * Flatten tree structure to array
 * @param {Array} tree - Tree structure
 * @param {number} level - Current level
 */
export const flattenTree = (tree, level = 0) => {
  let result = [];
  
  tree.forEach(node => {
    result.push({ ...node, level });
    if (node.children && node.children.length > 0) {
      result = result.concat(flattenTree(node.children, level + 1));
    }
  });
  
  return result;
};

/**
 * Find account in tree by name
 * @param {Array} tree - Tree structure
 * @param {string} accountName - Account name to find
 */
export const findAccountInTree = (tree, accountName) => {
  for (const node of tree) {
    if (node.name === accountName) {
      return node;
    }
    if (node.children && node.children.length > 0) {
      const found = findAccountInTree(node.children, accountName);
      if (found) return found;
    }
  }
  return null;
};

/**
 * Check if account is ancestor of another account
 * @param {Array} tree - Tree structure
 * @param {string} ancestorName - Potential ancestor account name
 * @param {string} descendantName - Potential descendant account name
 */
export const isAncestor = (tree, ancestorName, descendantName) => {
  const ancestor = findAccountInTree(tree, ancestorName);
  if (!ancestor) return false;
  
  const checkDescendants = (node) => {
    if (node.name === descendantName) return true;
    if (node.children && node.children.length > 0) {
      return node.children.some(child => checkDescendants(child));
    }
    return false;
  };
  
  return checkDescendants(ancestor);
};

/**
 * Get all account names from tree
 * @param {Array} tree - Tree structure
 */
export const getAllAccountNames = (tree) => {
  let names = [];
  
  tree.forEach(node => {
    names.push(node.name);
    if (node.children && node.children.length > 0) {
      names = names.concat(getAllAccountNames(node.children));
    }
  });
  
  return names;
};

/**
 * Update account in tree
 * @param {Array} tree - Tree structure
 * @param {string} accountName - Account name to update
 * @param {Object} updates - Updates to apply
 */
export const updateAccountInTree = (tree, accountName, updates) => {
  return tree.map(node => {
    if (node.name === accountName) {
      return { ...node, ...updates };
    }
    if (node.children && node.children.length > 0) {
      return {
        ...node,
        children: updateAccountInTree(node.children, accountName, updates),
      };
    }
    return node;
  });
};

/** Balance Sheet root types (left column) */
export const BALANCE_SHEET_ROOT_TYPES = ['Asset', 'Liability', 'Equity'];

/** P&L root types (right column) */
export const PL_ROOT_TYPES = ['Income', 'Expense', 'Cost of Goods Sold'];

/**
 * Split tree roots into Balance Sheet (left) and P&L (right)
 * @param {Array} tree - Full account tree (root nodes)
 */
export const splitTreesBySection = (tree) => {
  if (!tree || tree.length === 0) {
    return { balanceSheet: [], profitLoss: [] };
  }
  const balanceSheet = tree.filter((node) => BALANCE_SHEET_ROOT_TYPES.includes(node.root_type));
  const profitLoss = tree.filter((node) => PL_ROOT_TYPES.includes(node.root_type));
  return { balanceSheet, profitLoss };
};

/**
 * Get group accounts of a given root type (for "Move to parent" selector)
 * @param {Array} accounts - Flat list of accounts
 * @param {string} rootType - Root type
 * @param {string} excludeAccountName - Optional account to exclude (e.g. current account)
 */
export const getGroupAccountsByRootType = (accounts, rootType, excludeAccountName = null) => {
  return accounts
    .filter(
      (acc) =>
        acc.root_type === rootType &&
        acc.is_group &&
        acc.name !== excludeAccountName
    )
    .map((acc) => ({ name: acc.name, account_name: acc.account_name }))
    .sort((a, b) => a.account_name.localeCompare(b.account_name));
};

/**
 * Get account path (breadcrumb)
 * @param {Array} accounts - Flat list of accounts
 * @param {string} accountName - Account name
 */
export const getAccountPath = (accounts, accountName) => {
  const path = [];
  let currentAccount = accounts.find(acc => acc.name === accountName);
  
  while (currentAccount) {
    path.unshift(currentAccount.account_name);
    if (currentAccount.parent_account) {
      currentAccount = accounts.find(acc => acc.name === currentAccount.parent_account);
    } else {
      currentAccount = null;
    }
  }
  
  return path;
};

/**
 * Export chart of accounts to CSV
 * @param {Array} accounts - Flat list of accounts
 */
export const exportToCSV = (accounts) => {
  const headers = ['Account Name', 'Account Number', 'Parent Account', 'Account Type', 'Root Type', 'Is Group', 'Balance'];
  const rows = accounts.map(acc => [
    acc.account_name,
    acc.account_number || '',
    acc.parent_account || '',
    acc.account_type || '',
    acc.root_type || '',
    acc.is_group ? 'Yes' : 'No',
    acc.balance || 0,
  ]);
  
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', `chart_of_accounts_${new Date().toISOString().split('T')[0]}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Get today's date as default
 */
export const getDefaultAsOnDate = () => {
  const today = new Date();
  return today.toISOString().split('T')[0];
};
