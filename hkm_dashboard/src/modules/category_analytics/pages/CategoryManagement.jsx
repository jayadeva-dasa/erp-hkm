import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { 
  getAllCategories, 
  getAllAccounts, 
  saveCategory, 
  deleteCategory,
  moveAccount 
} from '../api/categoryAnalyticsApi';
import { formatIndianNumber } from '../utils/formatters';

const CategoryManagement = ({ company, onBack }) => {
  const [activeTab, setActiveTab] = useState('income');
  const [viewMode, setViewMode] = useState('drag-drop'); // 'drag-drop' or 'list'
  const [showOnlyUnallocated, setShowOnlyUnallocated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [categories, setCategories] = useState({ income: {}, expense: {}, asset: {}, liability: {} });
  const [accounts, setAccounts] = useState({ income: {}, expense: {}, asset: {}, liability: {} });
  const [uncategorized, setUncategorized] = useState([]);
  const [showNewCategoryModal, setShowNewCategoryModal] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDescription, setNewCategoryDescription] = useState('');
  const [message, setMessage] = useState(null);
  
  // Bulk selection state
  const [selectedAccounts, setSelectedAccounts] = useState([]);
  const [bulkCategory, setBulkCategory] = useState('');
  const [bulkPortion, setBulkPortion] = useState(100);
  const [showBulkAssignBar, setShowBulkAssignBar] = useState(false);

  // Helper function to get root type from active tab
  const getRootType = (tab = activeTab) => {
    const rootTypeMap = {
      'income': 'Income',
      'expense': 'Expense',
      'asset': 'Asset',
      'liability': 'Liability'
    };
    return rootTypeMap[tab] || 'Income';
  };

  useEffect(() => {
    if (company) {
      loadData();
    }
  }, [company, activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [categoriesData, accountsData] = await Promise.all([
        getAllCategories(company),
        getAllAccounts(company, getRootType())
      ]);

      setCategories(categoriesData);
      // Update accounts for the current tab
      setAccounts(prev => ({
        ...prev,
        [activeTab]: accountsData.accounts
      }));
      
      // Find uncategorized accounts (including partially allocated accounts)
      const uncategorizedAccounts = Object.entries(accountsData.accounts)
        .filter(([_, accData]) => accData.remaining > 0)
        .map(([account, accData]) => ({
          account,
          account_name: accData.account_name,
          disabled: accData.disabled,
          remaining: accData.remaining,
          total_allocated: accData.total_allocated
        }));
      
      setUncategorized(uncategorizedAccounts);
    } catch (error) {
      console.error('Error loading data:', error);
      showMessage('Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showMessage = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 2000);
  };

  const handleDragEnd = async (result) => {
    const { source, destination, draggableId } = result;

    if (!destination) return;
    if (source.droppableId === destination.droppableId) return;

    const account = draggableId;
    const sourceCategory = source.droppableId === 'uncategorized' ? null : source.droppableId;
    const targetCategory = destination.droppableId === 'uncategorized' ? null : destination.droppableId;
    const currentAccounts = accounts[activeTab] || {};
    const accountData = currentAccounts[account];

    if (!targetCategory) {
      // Moving to uncategorized - remove from source
      try {
        // Optimistically update UI
        if (sourceCategory) {
          setCategories(prev => {
            const updated = { ...prev };
            const catAccounts = { ...updated[activeTab][sourceCategory].accounts };
            delete catAccounts[account];
            updated[activeTab][sourceCategory] = {
              ...updated[activeTab][sourceCategory],
              accounts: catAccounts
            };
            return updated;
          });
        }

        const updatedAccounts = { ...currentAccounts };
        updatedAccounts[account] = {
          ...accountData,
          categories: []
        };
        setAccounts(prev => ({
          ...prev,
          [activeTab]: updatedAccounts
        }));

        setUncategorized(prev => [...prev, {
          account,
          account_name: accountData.account_name,
          disabled: accountData.disabled
        }]);

        await moveAccount(
          company,
          getRootType(),
          account,
          sourceCategory,
          null,
          0
        );
        // Success - no message needed for routine updates
      } catch (error) {
        console.error('Error moving account:', error);
        showMessage('Failed to move account', 'error');
        loadData(); // Reload on error
      }
      return;
    }

    // Calculate remaining portion for this account
    const remaining = accountData.remaining || 100;
    const defaultPortion = sourceCategory === null ? remaining : 100;
    
    // Show portion input modal with smart default
    const portion = prompt(
      `Enter allocation percentage (0-${remaining} available):`, 
      String(Math.min(defaultPortion, remaining))
    );
    if (portion === null) return;

    const portionNum = parseFloat(portion);
    if (isNaN(portionNum) || portionNum < 0 || portionNum > remaining) {
      alert(`Invalid portion. Please enter a number between 0 and ${remaining} (${remaining}% available).`);
      return;
    }

    try {
      // Optimistically update UI
      if (sourceCategory) {
        setCategories(prev => {
          const updated = { ...prev };
          const catAccounts = { ...updated[activeTab][sourceCategory].accounts };
          delete catAccounts[account];
          updated[activeTab][sourceCategory] = {
            ...updated[activeTab][sourceCategory],
            accounts: catAccounts
          };
          return updated;
        });
      } else {
        setUncategorized(prev => prev.filter(acc => acc.account !== account));
      }

      setCategories(prev => {
        const updated = { ...prev };
        if (!updated[activeTab][targetCategory]) {
          updated[activeTab][targetCategory] = { accounts: {} };
        }
        updated[activeTab][targetCategory] = {
          ...updated[activeTab][targetCategory],
          accounts: {
            ...updated[activeTab][targetCategory].accounts,
            [account]: portionNum
          }
        };
        return updated;
      });

      const updatedAccounts = { ...currentAccounts };
      updatedAccounts[account] = {
        ...accountData,
        categories: [{ category: targetCategory, portion: portionNum }]
      };
      setAccounts(prev => ({
        ...prev,
        [activeTab]: updatedAccounts
      }));

      await moveAccount(
        company,
        getRootType(),
        account,
        sourceCategory,
        targetCategory,
        portionNum
      );
      // Success - no message needed for routine updates
    } catch (error) {
      console.error('Error moving account:', error);
      showMessage(error.response?.data?.exception || 'Failed to move account', 'error');
      loadData(); // Reload on error
    }
  };

  const handlePortionChange = async (account, category, oldPortion, newPortion) => {
    const currentAccounts = accounts[activeTab] || {};
    const accountData = currentAccounts[account];
    if (!accountData || category === 'uncategorized') return;
    if (oldPortion === newPortion) return;

    try {
      // Optimistically update UI - update the specific category allocation
      const updatedAccounts = { ...currentAccounts };
      const updatedCategories = accountData.categories.map(cat => 
        cat.category === category ? { ...cat, portion: newPortion } : cat
      );
      
      // Recalculate totals
      const newTotalAllocated = updatedCategories.reduce((sum, cat) => sum + cat.portion, 0);
      
      updatedAccounts[account] = {
        ...accountData,
        categories: updatedCategories,
        total_allocated: newTotalAllocated,
        remaining: 100 - newTotalAllocated
      };
      
      setAccounts(prev => ({
        ...prev,
        [activeTab]: updatedAccounts
      }));

      setCategories(prev => {
        const updated = { ...prev };
        updated[activeTab][category] = {
          ...updated[activeTab][category],
          accounts: {
            ...updated[activeTab][category].accounts,
            [account]: newPortion
          }
        };
        return updated;
      });

      await moveAccount(
        company,
        getRootType(),
        account,
        category,
        category,
        newPortion
      );
      // Success - no message needed for routine updates
    } catch (error) {
      console.error('Error updating portion:', error);
      showMessage('Failed to update portion', 'error');
      loadData();
    }
  };

  // Bulk selection handlers
  const toggleAccountSelection = (account) => {
    setSelectedAccounts(prev => {
      if (prev.includes(account)) {
        return prev.filter(a => a !== account);
      } else {
        return [...prev, account];
      }
    });
  };

  const toggleSelectAll = () => {
    if (selectedAccounts.length === allAccountsForList.length) {
      setSelectedAccounts([]);
    } else {
      setSelectedAccounts(allAccountsForList.map(acc => acc.account));
    }
  };

  const handleBulkAssign = async () => {
    if (!bulkCategory || selectedAccounts.length === 0) {
      showMessage('Please select a category and at least one account', 'error');
      return;
    }

    setSaving(true);
    try {
      // Process each selected account
      for (const account of selectedAccounts) {
        // Find the account's current category in the list
        const accData = allAccountsForList.find(a => a.account === account);
        if (accData) {
          await handleCategoryChangeInList(account, accData.category, bulkCategory, bulkPortion);
        }
      }
      
      showMessage(`Successfully assigned ${selectedAccounts.length} account(s) to ${bulkCategory}`, 'success');
      setSelectedAccounts([]);
      setBulkCategory('');
      setBulkPortion(100);
      setShowBulkAssignBar(false);
      await loadData();
    } catch (error) {
      console.error('Bulk assign error:', error);
      showMessage('Failed to assign accounts in bulk', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleCategoryChangeInList = async (account, currentCategory, newCategory, portion = 100) => {
    // Find account data
    const currentAccounts = accounts[activeTab] || {};
    const accountData = currentAccounts[account];
    if (!accountData) return;

    if (currentCategory === newCategory) return;

    try {
      // Optimistically update the UI
      const updatedAccounts = { ...currentAccounts };
      
      // Update the categories array for this account
      let updatedCategories = [...accountData.categories];
      
      if (currentCategory === 'uncategorized') {
        // Adding a new category allocation
        if (newCategory !== 'uncategorized') {
          updatedCategories.push({ category: newCategory, portion });
        }
      } else {
        // Changing an existing allocation
        updatedCategories = updatedCategories.filter(cat => cat.category !== currentCategory);
        if (newCategory !== 'uncategorized') {
          updatedCategories.push({ category: newCategory, portion });
        }
      }
      
      // Recalculate totals
      const newTotalAllocated = updatedCategories.reduce((sum, cat) => sum + cat.portion, 0);
      
      updatedAccounts[account] = {
        ...accountData,
        categories: updatedCategories,
        total_allocated: newTotalAllocated,
        remaining: 100 - newTotalAllocated
      };
      
      setAccounts(prev => ({
        ...prev,
        [activeTab]: updatedAccounts
      }));

      // Update categories state
      if (currentCategory && currentCategory !== 'uncategorized') {
        setCategories(prev => {
          const updated = { ...prev };
          const catAccounts = { ...updated[activeTab][currentCategory].accounts };
          delete catAccounts[account];
          updated[activeTab][currentCategory] = {
            ...updated[activeTab][currentCategory],
            accounts: catAccounts
          };
          return updated;
        });
      }

      if (newCategory !== 'uncategorized') {
        setCategories(prev => {
          const updated = { ...prev };
          if (!updated[activeTab][newCategory]) {
            updated[activeTab][newCategory] = { accounts: {} };
          }
          updated[activeTab][newCategory] = {
            ...updated[activeTab][newCategory],
            accounts: {
              ...updated[activeTab][newCategory].accounts,
              [account]: portion
            }
          };
          return updated;
        });
      }

      // Save to backend
      await moveAccount(
        company,
        getRootType(),
        account,
        currentCategory === 'uncategorized' ? null : currentCategory,
        newCategory === 'uncategorized' ? null : newCategory,
        newCategory === 'uncategorized' ? 0 : portion
      );
      // Success - no message needed for routine updates
    } catch (error) {
      console.error('Error updating account:', error);
      showMessage(error.response?.data?.exception || 'Failed to update account', 'error');
      // Reload on error to ensure consistency
      loadData();
    }
  };

  const closeNewCategoryModal = () => {
    setShowNewCategoryModal(false);
    setNewCategoryName('');
    setNewCategoryDescription('');
  };

  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) {
      alert('Please enter a category name');
      return;
    }

    try {
      setSaving(true);
      await saveCategory(
        company,
        getRootType(),
        newCategoryName,
        [],
        null,
        newCategoryDescription
      );
      showMessage(`Category "${newCategoryName}" created successfully`);
      closeNewCategoryModal();
      loadData();
    } catch (error) {
      console.error('Error creating category:', error);
      showMessage('Failed to create category', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCategory = async (categoryName) => {
    if (!confirm(`Are you sure you want to delete category "${categoryName}"?`)) {
      return;
    }

    try {
      setSaving(true);
      await deleteCategory(
        company,
        categoryName,
        getRootType()
      );
      showMessage(`Category "${categoryName}" deleted successfully`);
      loadData();
    } catch (error) {
      console.error('Error deleting category:', error);
      showMessage('Failed to delete category', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleRenameCategory = async (oldName) => {
    const newName = prompt('Enter new category name:', oldName);
    if (!newName || newName === oldName) return;

    try {
      setSaving(true);
      const categoryData = categories[activeTab][oldName];
      const accountsData = Object.entries(categoryData.accounts).map(([account, portion]) => ({
        account,
        portion
      }));

      await saveCategory(
        company,
        getRootType(),
        newName,
        accountsData,
        oldName
      );
      showMessage(`Category renamed to "${newName}"`);
      loadData();
    } catch (error) {
      console.error('Error renaming category:', error);
      showMessage('Failed to rename category', 'error');
    } finally {
      setSaving(false);
    }
  };

  const currentCategories = categories[activeTab] || {};
  const categoryNames = Object.keys(currentCategories);
  const currentAccounts = accounts[activeTab] || {};

  // Prepare all accounts for list view (sorted: enabled first, then disabled)
  // Include accounts multiple times if they have remaining unallocated portions
  let allAccountsForList = [];
  
  Object.entries(currentAccounts).forEach(([account, accData]) => {
    // Add entries for each existing category allocation
    if (accData.categories.length > 0) {
      accData.categories.forEach(catAlloc => {
        allAccountsForList.push({
          account,
          account_name: accData.account_name,
          disabled: accData.disabled,
          category: catAlloc.category,
          portion: catAlloc.portion,
          total_allocated: accData.total_allocated,
          remaining: accData.remaining,
          is_partial: accData.remaining > 0
        });
      });
    }
    
    // Add an entry for remaining unallocated portion if any
    if (accData.remaining > 0) {
      allAccountsForList.push({
        account,
        account_name: accData.account_name,
        disabled: accData.disabled,
        category: 'uncategorized',
        portion: accData.remaining,
        total_allocated: accData.total_allocated,
        remaining: accData.remaining,
        is_partial: accData.total_allocated > 0
      });
    }
  });
  
  // Filter if showing only unallocated
  if (showOnlyUnallocated) {
    allAccountsForList = allAccountsForList.filter(acc => acc.remaining > 0);
  }
  
  // Sort: enabled first, then by account name
  allAccountsForList.sort((a, b) => {
    if (a.disabled !== b.disabled) {
      return a.disabled - b.disabled;
    }
    return a.account_name.localeCompare(b.account_name);
  });

  const renderDragDropView = () => (
    <div style={{ padding: '20px' }}>
      <DragDropContext onDragEnd={handleDragEnd}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          {/* Existing Categories */}
          {categoryNames.map((categoryName) => {
            const categoryData = currentCategories[categoryName];
            const categoryAccounts = Object.entries(categoryData.accounts)
              .map(([account, portion]) => ({
                account,
                account_name: currentAccounts[account]?.account_name || account,
                disabled: currentAccounts[account]?.disabled || 0,
                portion
              }))
              .sort((a, b) => {
                // Sort by disabled status first
                if (a.disabled !== b.disabled) {
                  return a.disabled - b.disabled;
                }
                return a.account_name.localeCompare(b.account_name);
              });

            return (
              <div key={categoryName} style={{
                background: '#f9f9f9',
                borderRadius: '8px',
                padding: '15px',
                border: '2px solid #e0e0e0'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '10px',
                  paddingBottom: '10px',
                  borderBottom: '2px solid #ddd'
                }}>
                  <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>
                    {categoryName}
                  </h3>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleRenameCategory(categoryName)}
                      style={{ padding: '4px 8px', fontSize: '11px' }}
                      disabled={saving}
                    >
                      ✏️
                    </button>
                    <button
                      className="btn btn-danger"
                      onClick={() => handleDeleteCategory(categoryName)}
                      style={{ padding: '4px 8px', fontSize: '11px' }}
                      disabled={saving}
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                <Droppable droppableId={categoryName}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      style={{
                        minHeight: '100px',
                        background: snapshot.isDraggingOver ? '#e3f2fd' : 'white',
                        borderRadius: '6px',
                        padding: '10px',
                        border: '2px dashed #ccc'
                      }}
                    >
                      {categoryAccounts.length === 0 ? (
                        <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
                          Drop accounts here
                        </div>
                      ) : (
                        categoryAccounts.map((acc, index) => (
                          <Draggable key={acc.account} draggableId={acc.account} index={index}>
                            {(provided, snapshot) => (
                              <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                                style={{
                                  ...provided.draggableProps.style,
                                  padding: '8px 12px',
                                  marginBottom: '8px',
                                  background: snapshot.isDragging ? '#fff3e0' : (acc.disabled ? '#f5f5f5' : 'white'),
                                  border: '1px solid #ddd',
                                  borderRadius: '4px',
                                  cursor: 'move',
                                  boxShadow: snapshot.isDragging ? '0 4px 8px rgba(0,0,0,0.2)' : 'none',
                                  opacity: acc.disabled ? 0.6 : 1
                                }}
                              >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <div style={{ fontSize: '13px', fontWeight: 500, flex: 1 }}>
                                    {acc.account_name}
                                  </div>
                                  {acc.disabled ? (
                                    <span style={{
                                      fontSize: '10px',
                                      padding: '2px 6px',
                                      background: '#ffcdd2',
                                      color: '#c62828',
                                      borderRadius: '3px',
                                      fontWeight: 600
                                    }}>
                                      DISABLED
                                    </span>
                                  ) : null}
                                </div>
                                <div style={{ fontSize: '11px', color: '#999', marginTop: '2px' }}>
                                  {acc.account}
                                  {acc.portion < 100 && (
                                    <span style={{ 
                                      marginLeft: '8px', 
                                      padding: '2px 6px', 
                                      background: '#fff3e0', 
                                      borderRadius: '3px',
                                      color: '#e65100'
                                    }}>
                                      {acc.portion}%
                                    </span>
                                  )}
                                </div>
                              </div>
                            )}
                          </Draggable>
                        ))
                      )}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </div>
            );
          })}

          {/* Uncategorized */}
          <div style={{
            background: '#fff3e0',
            borderRadius: '8px',
            padding: '15px',
            border: '2px solid #ff9800'
          }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', fontWeight: 600, color: '#e65100' }}>
              ⚠️ Unallocated / Partially Allocated ({uncategorized.length})
            </h3>

            <Droppable droppableId="uncategorized">
              {(provided, snapshot) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  style={{
                    minHeight: '100px',
                    background: snapshot.isDraggingOver ? '#ffebee' : 'white',
                    borderRadius: '6px',
                    padding: '10px',
                    border: '2px dashed #ff9800'
                  }}
                >
                  {uncategorized.length === 0 ? (
                    <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
                      All accounts categorized! 🎉
                    </div>
                  ) : (
                    uncategorized
                      .sort((a, b) => {
                        if (a.disabled !== b.disabled) return a.disabled - b.disabled;
                        return a.account_name.localeCompare(b.account_name);
                      })
                      .map((acc, index) => (
                        <Draggable key={acc.account} draggableId={acc.account} index={index}>
                          {(provided, snapshot) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              style={{
                                ...provided.draggableProps.style,
                                padding: '8px 12px',
                                marginBottom: '8px',
                                background: snapshot.isDragging ? '#fff3e0' : (acc.disabled ? '#f5f5f5' : 'white'),
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                cursor: 'move',
                                boxShadow: snapshot.isDragging ? '0 4px 8px rgba(0,0,0,0.2)' : 'none',
                                opacity: acc.disabled ? 0.6 : 1
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <div style={{ fontSize: '13px', fontWeight: 500, flex: 1 }}>
                                  {acc.account_name}
                                </div>
                                {acc.remaining < 100 && (
                                  <span style={{
                                    fontSize: '10px',
                                    padding: '2px 6px',
                                    background: '#fff3e0',
                                    color: '#e65100',
                                    borderRadius: '3px',
                                    fontWeight: 600
                                  }}>
                                    {acc.remaining}% Available
                                  </span>
                                )}
                                {acc.disabled ? (
                                  <span style={{
                                    fontSize: '10px',
                                    padding: '2px 6px',
                                    background: '#ffcdd2',
                                    color: '#c62828',
                                    borderRadius: '3px',
                                    fontWeight: 600
                                  }}>
                                    DISABLED
                                  </span>
                                ) : null}
                              </div>
                              <div style={{ fontSize: '11px', color: '#999', marginTop: '2px' }}>
                                {acc.account}
                                {acc.total_allocated > 0 && acc.total_allocated < 100 && (
                                  <span style={{ marginLeft: '8px', color: '#666' }}>
                                    ({acc.total_allocated}% already allocated)
                                  </span>
                                )}
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))
                  )}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </div>
        </div>
      </DragDropContext>

      <div style={{ marginTop: '30px', padding: '20px', background: '#e3f2fd', borderRadius: '8px' }}>
        <strong>💡 How to use Drag & Drop View:</strong>
        <ul style={{ marginTop: '10px', marginLeft: '20px' }}>
          <li>Drag accounts from one category to another to reorganize</li>
          <li>When dropping an account, you'll be asked for the allocation percentage (0-100%)</li>
          <li>Accounts can be split across multiple categories (total must not exceed 100%)</li>
          <li>Enabled accounts appear first, followed by disabled accounts in each category</li>
          <li>Use the ✏️ button to rename a category</li>
          <li>Use the 🗑️ button to delete a category (accounts will become uncategorized)</li>
        </ul>
      </div>
    </div>
  );

  const renderListView = () => (
    <div style={{ padding: '20px' }}>
      {/* Bulk Assignment Bar */}
      {selectedAccounts.length > 0 && (
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '15px 20px',
          borderRadius: '8px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '15px',
          boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)'
        }}>
          <div style={{ flex: 1 }}>
            <strong style={{ fontSize: '15px' }}>
              {selectedAccounts.length} account(s) selected
            </strong>
          </div>
          
          <select
            value={bulkCategory}
            onChange={(e) => setBulkCategory(e.target.value)}
            style={{
              padding: '8px 12px',
              fontSize: '13px',
              border: 'none',
              borderRadius: '4px',
              minWidth: '200px',
              cursor: 'pointer'
            }}
          >
            <option value="">Select Category...</option>
            {categoryNames.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          
          <input
            type="number"
            min="0"
            max="100"
            value={bulkPortion}
            onChange={(e) => setBulkPortion(parseInt(e.target.value) || 0)}
            style={{
              width: '80px',
              padding: '8px',
              fontSize: '13px',
              border: 'none',
              borderRadius: '4px',
              textAlign: 'center'
            }}
            placeholder="Portion %"
          />
          
          <button
            onClick={handleBulkAssign}
            disabled={!bulkCategory || saving}
            style={{
              padding: '8px 20px',
              fontSize: '13px',
              fontWeight: 600,
              border: 'none',
              borderRadius: '4px',
              background: 'white',
              color: '#667eea',
              cursor: bulkCategory ? 'pointer' : 'not-allowed',
              opacity: bulkCategory ? 1 : 0.5
            }}
          >
            {saving ? 'Assigning...' : 'Assign to Category'}
          </button>
          
          <button
            onClick={() => {
              setSelectedAccounts([]);
              setBulkCategory('');
              setBulkPortion(100);
            }}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              border: '1px solid white',
              borderRadius: '4px',
              background: 'transparent',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            Clear
          </button>
        </div>
      )}
      
      <div style={{ background: 'white', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e0e0e0' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: 600, fontSize: '13px', width: '50px' }}>
                <input
                  type="checkbox"
                  checked={selectedAccounts.length === allAccountsForList.length && allAccountsForList.length > 0}
                  onChange={toggleSelectAll}
                  style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                />
              </th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '13px' }}>Status</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '13px' }}>Account Name</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '13px' }}>Account Code</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '13px', width: '250px' }}>Category</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '13px', width: '100px' }}>Portion %</th>
            </tr>
          </thead>
          <tbody>
            {allAccountsForList.map((acc, index) => (
              <tr 
                key={`${acc.account}-${acc.category}-${index}`}
                style={{ 
                  borderBottom: '1px solid #eee',
                  background: selectedAccounts.includes(acc.account) 
                    ? '#e8eaf6' 
                    : (acc.disabled ? '#fafafa' : (acc.is_partial && acc.category === 'uncategorized' ? '#fff3e0' : 'white')),
                  opacity: acc.disabled ? 0.7 : 1
                }}
              >
                <td style={{ padding: '10px', textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={selectedAccounts.includes(acc.account)}
                    onChange={() => toggleAccountSelection(acc.account)}
                    style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                  />
                </td>
                <td style={{ padding: '10px' }}>
                  {acc.disabled ? (
                    <span style={{
                      fontSize: '10px',
                      padding: '3px 8px',
                      background: '#ffcdd2',
                      color: '#c62828',
                      borderRadius: '3px',
                      fontWeight: 600,
                      display: 'inline-block'
                    }}>
                      DISABLED
                    </span>
                  ) : (
                    <span style={{
                      fontSize: '10px',
                      padding: '3px 8px',
                      background: '#c8e6c9',
                      color: '#2e7d32',
                      borderRadius: '3px',
                      fontWeight: 600,
                      display: 'inline-block'
                    }}>
                      ENABLED
                    </span>
                  )}
                </td>
                <td style={{ padding: '10px', fontSize: '13px', fontWeight: 500 }}>
                  {acc.account_name}
                  {acc.is_partial && (
                    <span style={{
                      marginLeft: '8px',
                      fontSize: '10px',
                      padding: '2px 6px',
                      background: '#fff3e0',
                      color: '#e65100',
                      borderRadius: '3px',
                      fontWeight: 600
                    }}>
                      {acc.category === 'uncategorized' ? `${acc.remaining}% Unallocated` : 'Partial'}
                    </span>
                  )}
                </td>
                <td style={{ padding: '10px', fontSize: '12px', color: '#666' }}>
                  {acc.account}
                  {acc.total_allocated > 0 && acc.total_allocated < 100 && (
                    <div style={{ fontSize: '10px', color: '#999', marginTop: '2px' }}>
                      Total allocated: {acc.total_allocated}%
                    </div>
                  )}
                </td>
                <td style={{ padding: '10px' }}>
                  <select
                    value={acc.category}
                    onChange={(e) => handleCategoryChangeInList(acc.account, acc.category, e.target.value, acc.portion)}
                    disabled={saving}
                    style={{
                      width: '100%',
                      padding: '6px 10px',
                      fontSize: '13px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      background: 'white',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="uncategorized">Uncategorized</option>
                    {categoryNames.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </td>
                <td style={{ padding: '10px' }}>
                  <input
                    type="number"
                    min="0"
                    max={acc.category === 'uncategorized' ? 100 : acc.remaining + acc.portion}
                    value={acc.portion}
                    onBlur={(e) => {
                      const newPortion = parseFloat(e.target.value);
                      const maxAllowed = acc.category === 'uncategorized' ? 100 : acc.remaining + acc.portion;
                      if (!isNaN(newPortion) && newPortion >= 0 && newPortion <= maxAllowed && acc.category !== 'uncategorized' && newPortion !== acc.portion) {
                        handlePortionChange(acc.account, acc.category, acc.portion, newPortion);
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.target.blur();
                      }
                    }}
                    disabled={acc.category === 'uncategorized'}
                    style={{
                      width: '70px',
                      padding: '6px',
                      fontSize: '13px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      textAlign: 'center'
                    }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: '30px', padding: '20px', background: '#e3f2fd', borderRadius: '8px' }}>
        <strong>💡 How to use List View:</strong>
        <ul style={{ marginTop: '10px', marginLeft: '20px' }}>
          <li><strong>Individual Assignment:</strong> Select a category from the dropdown to assign a single account</li>
          <li><strong>Bulk Assignment:</strong> Check the boxes next to multiple accounts, select a category, and click "Assign to Category"</li>
          <li><strong>Select All:</strong> Use the checkbox in the header to select/deselect all accounts at once</li>
          <li>Changes are saved automatically when you change the dropdown or use bulk assign</li>
          <li>Adjust the portion percentage (0-100%) for each account or set it for bulk assignments</li>
          <li>Enabled accounts appear at the top, disabled accounts at the bottom</li>
          <li>Selected accounts are highlighted in light purple</li>
        </ul>
      </div>
    </div>
  );

  return (
    <div className="container">
      <div className="header">
        <h1 className="header-title">⚙️ Category Management</h1>
        <p className="header-subtitle">
          Organize your financial accounts into categories for better analysis
        </p>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={onBack}>
            ← Back to Dashboard
          </button>
        </div>
      </div>

      {message && (
        <div className={message.type === 'error' ? 'error' : 'success'}>
          {message.text}
        </div>
      )}

      <div className="card">
        <div className="card-header">
          Manage Categories
          <div style={{ float: 'right', display: 'flex', gap: '10px', alignItems: 'center' }}>
            {/* View Mode Toggle */}
            <div style={{ display: 'flex', gap: '5px', marginRight: '15px' }}>
              <button
                className={`btn ${viewMode === 'drag-drop' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setViewMode('drag-drop')}
                style={{ padding: '6px 15px', fontSize: '13px' }}
              >
                🎯 Drag & Drop
              </button>
              <button
                className={`btn ${viewMode === 'list' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setViewMode('list')}
                style={{ padding: '6px 15px', fontSize: '13px' }}
              >
                📋 List View
              </button>
            </div>

            {/* Filter Toggle - Only show in List View */}
            {viewMode === 'list' && (
              <button
                className={`btn ${showOnlyUnallocated ? 'btn-warning' : 'btn-secondary'}`}
                onClick={() => setShowOnlyUnallocated(!showOnlyUnallocated)}
                style={{ 
                  padding: '6px 15px', 
                  fontSize: '13px',
                  marginRight: '15px',
                  fontWeight: showOnlyUnallocated ? 600 : 400
                }}
                title="Show only accounts with unallocated portions"
              >
                {showOnlyUnallocated ? '⚠️ Unallocated Only' : '📊 Show All'}
              </button>
            )}

            {/* Account Type Tabs */}
            <button
              className={`btn ${activeTab === 'asset' ? 'btn-success' : 'btn-secondary'}`}
              onClick={() => setActiveTab('asset')}
              style={{ padding: '6px 15px', fontSize: '13px' }}
            >
              Asset
            </button>
            <button
              className={`btn ${activeTab === 'liability' ? 'btn-warning' : 'btn-secondary'}`}
              onClick={() => setActiveTab('liability')}
              style={{ padding: '6px 15px', fontSize: '13px' }}
            >
              Liability
            </button>
            <button
              className={`btn ${activeTab === 'income' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('income')}
              style={{ padding: '6px 15px', fontSize: '13px' }}
            >
              Income
            </button>
            <button
              className={`btn ${activeTab === 'expense' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('expense')}
              style={{ padding: '6px 15px', fontSize: '13px' }}
            >
              Expense
            </button>

            {/* New Category Button */}
            <button
              className="btn btn-success"
              onClick={() => setShowNewCategoryModal(true)}
              style={{ padding: '6px 15px', fontSize: '13px' }}
            >
              + New Category
            </button>
          </div>
        </div>

        {loading ? (
          <div className="loading">
            <div className="loading-spinner"></div>
            <p>Loading categories...</p>
          </div>
        ) : (
          viewMode === 'drag-drop' ? renderDragDropView() : renderListView()
        )}
      </div>

      {/* New Category Modal */}
      {showNewCategoryModal && (
        <div className="modal-overlay" onClick={closeNewCategoryModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ minWidth: '500px' }}>
            <div className="modal-header">
              <h2 className="modal-title">Create New Category</h2>
              <span className="modal-close" onClick={closeNewCategoryModal}>&times;</span>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Category Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  placeholder="Enter category name"
                  autoFocus
                />
              </div>
              
              <div className="form-group" style={{ marginTop: '15px' }}>
                <label className="form-label">Root Type *</label>
                <select
                  className="form-input"
                  value={activeTab}
                  disabled
                  style={{ 
                    background: '#f5f5f5', 
                    cursor: 'not-allowed',
                    textTransform: 'capitalize'
                  }}
                >
                  <option value="asset">Asset</option>
                  <option value="liability">Liability</option>
                  <option value="income">Income</option>
                  <option value="expense">Expense</option>
                </select>
                <small style={{ color: '#666', fontSize: '12px', marginTop: '5px', display: 'block' }}>
                  Root type is set based on the current tab
                </small>
              </div>

              <div className="form-group" style={{ marginTop: '15px' }}>
                <label className="form-label">Description</label>
                <textarea
                  className="form-input"
                  value={newCategoryDescription}
                  onChange={(e) => setNewCategoryDescription(e.target.value)}
                  placeholder="Enter category description (optional)"
                  rows="3"
                  style={{ resize: 'vertical', fontFamily: 'inherit' }}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn btn-secondary" 
                onClick={closeNewCategoryModal}
                disabled={saving}
              >
                Cancel
              </button>
              <button 
                className="btn btn-success" 
                onClick={handleCreateCategory}
                disabled={saving || !newCategoryName.trim()}
              >
                {saving ? 'Creating...' : 'Create Category'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryManagement;
