import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { DragDropContext, Droppable } from 'react-beautiful-dnd';
import '../index.css';
import {
  Box,
  Container,
  Heading,
  HStack,
  Button,
  useToast,
  useColorModeValue,
  Text,
  Spinner,
  useDisclosure,
  Icon,
} from '@chakra-ui/react';
import { FiArrowLeft, FiAlertCircle } from 'react-icons/fi';
import ChartFilters from '../components/ChartFilters';
import AccountTreeNode from '../components/AccountTreeNode';
import AccountDetailsModal from '../components/AccountDetailsModal';
import MoveParentModal from '../components/MoveParentModal';
import {
  getCompanies,
  getChartOfAccounts,
  updateAccountParent,
  validateAccountMove,
  getAccountBalances,
} from '../api/chartOfAccountsApi';
import {
  buildAccountTree,
  findAccountInTree,
  isAncestor,
  exportToCSV,
  getDefaultAsOnDate,
  splitTreesBySection,
  getGroupAccountsByRootType,
} from '../utils/accountUtils';

const ChartOfAccountsPage = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState('Hare Krishna Movement Jaipur');
  const [accounts, setAccounts] = useState([]);
  const [accountTree, setAccountTree] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [asOnDate, setAsOnDate] = useState(getDefaultAsOnDate());
  const [maxDepth, setMaxDepth] = useState(3);
  const [showBalance, setShowBalance] = useState(true);
  const [showDisabled, setShowDisabled] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [currency, setCurrency] = useState('INR');
  const { isOpen: isMoveOpen, onOpen: onMoveOpen, onClose: onMoveClose } = useDisclosure();
  const [moveAccount, setMoveAccount] = useState(null);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const headerBg = useColorModeValue('white', 'gray.800');
  
  // Load companies on mount
  useEffect(() => {
    loadCompanies();
  }, []);
  
  // Load chart of accounts when company or filters change
  useEffect(() => {
    if (selectedCompany) {
      loadChartOfAccounts();
    }
  }, [selectedCompany]);
  
  const loadCompanies = async () => {
    try {
      const companiesList = await getCompanies();
      setCompanies(companiesList);
      
      // Set currency from first company
      if (companiesList.length > 0) {
        const company = companiesList.find(c => c.name === selectedCompany) || companiesList[0];
        setCurrency(company.default_currency || 'INR');
      }
    } catch (err) {
      console.error('Error loading companies:', err);
      toast({
        title: 'Error',
        description: 'Failed to load companies',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };
  
  const loadChartOfAccounts = async (skipBalances = false) => {
    if (!selectedCompany) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await getChartOfAccounts(selectedCompany, maxDepth);
      
      // Filter disabled accounts if not showing them
      const filteredData = showDisabled ? data : data.filter(acc => !acc.disabled);
      
      setAccounts(filteredData);
      
      // Load balances if showBalance is enabled and not skipping
      if (showBalance && !skipBalances && filteredData.length > 0) {
        const accountNames = filteredData.map(acc => acc.name);
        const balances = await getAccountBalances(accountNames, selectedCompany, asOnDate, asOnDate);
        
        // Merge balances into accounts
        const accountsWithBalances = filteredData.map(acc => ({
          ...acc,
          balance: balances[acc.name] || 0,
        }));
        
        const tree = buildAccountTree(accountsWithBalances, maxDepth);
        setAccountTree(tree);
      } else {
        const tree = buildAccountTree(filteredData, maxDepth);
        setAccountTree(tree);
      }
    } catch (err) {
      console.error('Error loading chart of accounts:', err);
      setError(err.message || 'Failed to load chart of accounts');
      toast({
        title: 'Error',
        description: err.message || 'Failed to load chart of accounts',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleDragEnd = async (result) => {
    const { source, destination, draggableId } = result;
    
    // Dropped outside the list
    if (!destination) {
      return;
    }
    
    // Dropped in the same position
    if (source.droppableId === destination.droppableId && source.index === destination.index) {
      return;
    }
    
    const accountName = draggableId;
    const newParentName = destination.droppableId;
    
    // Find accounts
    const account = findAccountInTree(accountTree, accountName);
    const newParent = findAccountInTree(accountTree, newParentName);
    
    if (!account || !newParent) {
      toast({
        title: 'Error',
        description: 'Invalid account or parent',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    // Validate: New parent must be a group account
    if (!newParent.is_group) {
      toast({
        title: 'Invalid Move',
        description: 'Can only drop accounts into group accounts',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    // Validate: Cannot move account to itself or its descendants
    if (accountName === newParentName || isAncestor(accountTree, accountName, newParentName)) {
      toast({
        title: 'Invalid Move',
        description: 'Cannot move account to itself or its descendants',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    // Validate: Account types must match
    if (account.root_type !== newParent.root_type) {
      toast({
        title: 'Invalid Move',
        description: `Cannot move ${account.root_type} account under ${newParent.root_type} account`,
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    try {
      // Validate with backend
      const validation = await validateAccountMove(accountName, newParentName);
      
      if (!validation.valid) {
        toast({
          title: 'Invalid Move',
          description: validation.message || 'This move is not allowed',
          status: 'warning',
          duration: 5000,
          isClosable: true,
        });
        return;
      }
      
      // Update parent in backend
      await updateAccountParent(accountName, newParentName, selectedCompany);
      
      // Update tree locally without reloading balances
      const updatedAccounts = accounts.map(acc => 
        acc.name === accountName 
          ? { ...acc, parent_account: newParentName }
          : acc
      );
      
      setAccounts(updatedAccounts);
      const tree = buildAccountTree(updatedAccounts, maxDepth);
      setAccountTree(tree);
      
      toast({
        title: 'Success',
        description: `Moved "${account.account_name}" under "${newParent.account_name}"`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (err) {
      console.error('Error moving account:', err);
      toast({
        title: 'Error',
        description: err.message || 'Failed to move account',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };
  
  const handleToggle = useCallback((accountName) => {
    setAccountTree(prevTree => {
      const toggleNode = (nodes) => {
        return nodes.map(node => {
          if (node.name === accountName) {
            return { ...node, expanded: !node.expanded };
          }
          if (node.children && node.children.length > 0) {
            return { ...node, children: toggleNode(node.children) };
          }
          return node;
        });
      };
      return toggleNode(prevTree);
    });
  }, []);
  
  const handleAccountClick = (account) => {
    setSelectedAccount(account);
    onOpen();
  };

  const handleMoveClick = (account) => {
    setMoveAccount(account);
    onMoveOpen();
  };

  const handleMoveSuccess = (newParentName) => {
    if (!moveAccount) return;
    const updatedAccounts = accounts.map((acc) =>
      acc.name === moveAccount.name ? { ...acc, parent_account: newParentName } : acc
    );
    setAccounts(updatedAccounts);
    setAccountTree(buildAccountTree(updatedAccounts, maxDepth));
    setMoveAccount(null);
  };
  
  const handleExpandAll = () => {
    const expandNode = (nodes) => {
      return nodes.map(node => ({
        ...node,
        expanded: true,
        children: node.children ? expandNode(node.children) : [],
      }));
    };
    setAccountTree(expandNode(accountTree));
  };
  
  const handleCollapseAll = () => {
    const collapseNode = (nodes) => {
      return nodes.map(node => ({
        ...node,
        expanded: false,
        children: node.children ? collapseNode(node.children) : [],
      }));
    };
    setAccountTree(collapseNode(accountTree));
  };
  
  const handleExport = () => {
    if (accounts.length === 0) {
      toast({
        title: 'No Data',
        description: 'No accounts to export',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    exportToCSV(accounts);
    toast({
      title: 'Success',
      description: 'Chart of accounts exported to CSV',
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };
  
  // Filter accounts based on search term
  const filteredTree = searchTerm
    ? accountTree.filter((node) => {
        const matchesSearch = (n) => {
          const matches =
            n.account_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (n.account_number && n.account_number.toLowerCase().includes(searchTerm.toLowerCase()));
          if (matches) return true;
          if (n.children && n.children.length > 0) {
            return n.children.some((child) => matchesSearch(child));
          }
          return false;
        };
        return matchesSearch(node);
      })
    : accountTree;

  const { balanceSheet, profitLoss } = splitTreesBySection(filteredTree);
  const groupAccountsForMove = moveAccount
    ? getGroupAccountsByRootType(accounts, moveAccount.root_type, moveAccount.name)
    : [];

  const renderTreeColumn = (roots, droppableId) => (
    <Droppable droppableId={droppableId} type="ACCOUNT">
      {(provided) => (
        <Box ref={provided.innerRef} {...provided.droppableProps} flex="1" minW={0}>
          {roots.map((account, index) => (
            <AccountTreeNode
              key={account.name}
              account={account}
              index={index}
              onToggle={handleToggle}
              onAccountClick={handleAccountClick}
              onMoveClick={handleMoveClick}
              showBalance={showBalance}
              currency={currency}
              searchTerm={searchTerm}
              compact
            />
          ))}
          {provided.placeholder}
        </Box>
      )}
    </Droppable>
  );

  return (
    <Box minH="100vh" bg={bgColor}>
      {/* Compact header + filters */}
      <Box bg={headerBg} borderBottomWidth="1px" borderColor="gray.200" py={2} px={4}>
        <Container maxW="container.xl">
          <HStack justify="space-between" align="center" mb={2}>
            <HStack spacing={3}>
              <Button leftIcon={<FiArrowLeft />} variant="ghost" size="sm" onClick={() => navigate('/')}>
                Back
              </Button>
              <Heading size="sm" color="gray.800">
                Chart of Accounts
              </Heading>
              <Button size="xs" variant="outline" onClick={handleExpandAll}>
                Expand
              </Button>
              <Button size="xs" variant="outline" onClick={handleCollapseAll}>
                Collapse
              </Button>
            </HStack>
          </HStack>
          <ChartFilters
            companies={companies}
            selectedCompany={selectedCompany}
            onCompanyChange={setSelectedCompany}
            asOnDate={asOnDate}
            onAsOnDateChange={setAsOnDate}
            maxDepth={maxDepth}
            onMaxDepthChange={setMaxDepth}
            showBalance={showBalance}
            onShowBalanceChange={setShowBalance}
            showDisabled={showDisabled}
            onShowDisabledChange={setShowDisabled}
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            onRefresh={loadChartOfAccounts}
            onExport={handleExport}
            loading={loading}
          />
        </Container>
      </Box>

      {/* Two-column tree */}
      <Container maxW="container.xl" py={3} pb={8}>
        {loading ? (
          <Box textAlign="center" py={8}>
            <Spinner size="lg" color="blue.500" />
            <Text mt={2} fontSize="sm" color="gray.500">Loading...</Text>
          </Box>
        ) : error ? (
          <Box textAlign="center" py={8}>
            <Icon as={FiAlertCircle} boxSize={8} color="red.500" mb={2} />
            <Text color="red.500" fontSize="sm" mb={2}>{error}</Text>
            <Button onClick={loadChartOfAccounts} colorScheme="blue" size="sm">Retry</Button>
          </Box>
        ) : filteredTree.length === 0 ? (
          <Box textAlign="center" py={8}>
            <Text color="gray.500" fontSize="sm">
              {searchTerm ? 'No accounts match search' : 'No accounts found'}
            </Text>
            {searchTerm && (
              <Button onClick={() => setSearchTerm('')} mt={2} size="sm">Clear search</Button>
            )}
          </Box>
        ) : (
          <DragDropContext onDragEnd={handleDragEnd}>
            <HStack align="stretch" spacing={4}>
              {/* Left: Balance Sheet */}
              <Box flex={1} minW={0}>
                <HStack spacing={2} mb={1} px={1}>
                  <Box w="2" h="2" borderRadius="full" bg="blue.400" />
                  <Text fontSize="xs" fontWeight="bold" color="gray.600">Balance Sheet</Text>
                </HStack>
                <Box fontSize="xs" color="gray.500" mb={0.5} px={1}>
                  <Text as="span" color="blue.500">Asset</Text>
                  <Text as="span" mx={1}>·</Text>
                  <Text as="span" color="red.500">Liability</Text>
                  <Text as="span" mx={1}>·</Text>
                  <Text as="span" color="purple.500">Equity</Text>
                </Box>
                {renderTreeColumn(balanceSheet, 'balance-sheet')}
              </Box>
              {/* Right: P&L */}
              <Box flex={1} minW={0}>
                <HStack spacing={2} mb={1} px={1}>
                  <Box w="2" h="2" borderRadius="full" bg="green.400" />
                  <Text fontSize="xs" fontWeight="bold" color="gray.600">Profit & Loss</Text>
                </HStack>
                <Box fontSize="xs" color="gray.500" mb={0.5} px={1}>
                  <Text as="span" color="green.500">Income</Text>
                  <Text as="span" mx={1}>·</Text>
                  <Text as="span" color="orange.500">Expense</Text>
                  <Text as="span" mx={1}>·</Text>
                  <Text as="span" color="pink.500">COGS</Text>
                </Box>
                {renderTreeColumn(profitLoss, 'profit-loss')}
              </Box>
            </HStack>
          </DragDropContext>
        )}
      </Container>

      <AccountDetailsModal
        isOpen={isOpen}
        onClose={onClose}
        account={selectedAccount}
        company={selectedCompany}
        asOnDate={asOnDate}
        allAccounts={accounts}
      />

      <MoveParentModal
        isOpen={isMoveOpen}
        onClose={() => { onMoveClose(); setMoveAccount(null); }}
        account={moveAccount}
        groupAccounts={groupAccountsForMove}
        company={selectedCompany}
        onSuccess={handleMoveSuccess}
      />
    </Box>
  );
};

export default ChartOfAccountsPage;
