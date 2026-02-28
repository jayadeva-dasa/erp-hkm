// Asset Reco Page
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Container,
  VStack,
  Heading,
  Text,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  useToast,
  Spinner,
  HStack,
  Badge,
  Image,
  Flex,
  Icon,
  Button,
  IconButton,
  Tooltip,
  Input,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
} from '@chakra-ui/react';
import { FiRefreshCw, FiImage, FiEye, FiEdit2, FiCheckCircle, FiXCircle, FiSend, FiSave, FiFilter, FiX, FiDownload } from 'react-icons/fi';
import { assetRecoApi } from '../api/assetRecoApi';
import type { AssetRecoItem } from '../types';
import { ImageModal } from '../components/ImageModal';
import { SearchableSelect, type SelectOption } from '../components/SearchableSelect';
import { AssetRecoDetailModal } from '../components/AssetRecoDetailModal';

const AssetRecoPage: React.FC = () => {
  const [assets, setAssets] = useState<AssetRecoItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImages, setSelectedImages] = useState<string[]>([]);
  const [isImageModalOpen, setIsImageModalOpen] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [selectedAssetName, setSelectedAssetName] = useState<string>('');
  const [submitting, setSubmitting] = useState<Record<string, boolean>>({});
  const [users, setUsers] = useState<SelectOption[]>([]);
  const [loadingUsers, setLoadingUsers] = useState<boolean>(false);
  const [selectedAssetId, setSelectedAssetId] = useState<string>('');
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [companies, setCompanies] = useState<string[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [categories, setCategories] = useState<SelectOption[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [custodians, setCustodians] = useState<SelectOption[]>([]);
  const [selectedCustodian, setSelectedCustodian] = useState<string>('');
  const [selectedSecondaryCustodian, setSelectedSecondaryCustodian] = useState<string>('');
  const [purchasedDateFrom, setPurchasedDateFrom] = useState<string>('');
  const [purchasedDateTo, setPurchasedDateTo] = useState<string>('');
  const [showFilters, setShowFilters] = useState<boolean>(false);

  // Column width state with localStorage persistence (same pattern as HKMP User Entries)
  const assetRecoColumnOrder = ['id', 'assetName', 'location', 'dateAmount', 'custodian', 'remarks', 'images', 'actions', 'status'] as const;
  const defaultColumnWidths: { [key: string]: number } = {
    id: 100,
    assetName: 95,
    location: 120,
    dateAmount: 140,
    custodian: 120,
    remarks: 120,
    images: 80,
    actions: 180,
    status: 100,
  };
  const [columnWidths, setColumnWidths] = useState<{ [key: string]: number }>(() => {
    const saved = localStorage.getItem('asset_reco_column_widths');
    return saved ? JSON.parse(saved) : defaultColumnWidths;
  });
  const [resizingColumn, setResizingColumn] = useState<string | null>(null);
  const [resizeStartX, setResizeStartX] = useState(0);
  const [resizeStartWidth, setResizeStartWidth] = useState(0);

  const toast = useToast();

  const fetchAssets = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const filters: any = {};
      
      if (selectedCompany) filters.company = selectedCompany;
      if (selectedCategory) filters.asset_category = selectedCategory;
      if (purchasedDateFrom) filters.purchased_date_from = purchasedDateFrom;
      if (purchasedDateTo) filters.purchased_date_to = purchasedDateTo;
      if (selectedCustodian) filters.custodian = selectedCustodian;
      if (selectedSecondaryCustodian) filters.secondary_custodian = selectedSecondaryCustodian;
      
      const data = await assetRecoApi.getAssetReco(Object.keys(filters).length > 0 ? filters : undefined);
      setAssets(data);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch asset data';
      setError(errorMessage);
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanies = async () => {
    try {
      const data = await assetRecoApi.getCompanies();
      setCompanies(data);
      // Set first company as default
      if (data.length > 0 && !selectedCompany) {
        setSelectedCompany(data[0]);
      }
    } catch (err: any) {
      console.error('Error fetching companies:', err);
      toast({
        title: 'Error',
        description: 'Failed to fetch companies',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const fetchCustodians = async () => {
    try {
      const data = await assetRecoApi.getCustodians();
      const custodianOptions: SelectOption[] = data.map((custodian) => ({
        value: custodian,
        label: custodian,
      }));
      setCustodians(custodianOptions);
    } catch (err: any) {
      console.error('Error fetching custodians:', err);
    }
  };

  const clearAllFilters = () => {
    setSelectedCompany(companies.length > 0 ? companies[0] : '');
    setSelectedCategory('');
    setSelectedCustodian('');
    setSelectedSecondaryCustodian('');
    setPurchasedDateFrom('');
    setPurchasedDateTo('');
  };

  // Persist column widths to localStorage
  useEffect(() => {
    localStorage.setItem('asset_reco_column_widths', JSON.stringify(columnWidths));
  }, [columnWidths]);

  // Column resize handlers (same as HKMP User Entries)
  const handleResizeStart = (e: React.MouseEvent, columnKey: string) => {
    e.preventDefault();
    e.stopPropagation();
    setResizingColumn(columnKey);
    setResizeStartX(e.clientX);
    setResizeStartWidth(columnWidths[columnKey] ?? defaultColumnWidths[columnKey] ?? 120);
  };

  useEffect(() => {
    const handleResizeMove = (e: MouseEvent) => {
      if (!resizingColumn) return;
      const diff = e.clientX - resizeStartX;
      const newWidth = Math.max(50, resizeStartWidth + diff);
      setColumnWidths((prev) => ({ ...prev, [resizingColumn]: newWidth }));
    };
    const handleResizeEnd = () => setResizingColumn(null);
    if (resizingColumn) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
      return () => {
        document.removeEventListener('mousemove', handleResizeMove);
        document.removeEventListener('mouseup', handleResizeEnd);
      };
    }
  }, [resizingColumn, resizeStartX, resizeStartWidth]);

  const resetColumnWidths = () => {
    setColumnWidths(defaultColumnWidths);
    toast({
      title: 'Column widths reset',
      description: 'Column widths restored to default',
      status: 'info',
      duration: 2000,
      isClosable: true,
    });
  };

  // Fetch users for secondary custodian dropdown
  const fetchUsers = useCallback(async (searchTerm: string = '') => {
    try {
      setLoadingUsers(true);
      const data = await assetRecoApi.getUsers(searchTerm);
      const userOptions: SelectOption[] = data.map((user) => ({
        value: user.email,
        label: user.full_name || user.email,
      }));
      setUsers(userOptions);
    } catch (err: any) {
      console.error('Error fetching users:', err);
      // Don't show toast for user search errors, just log
    } finally {
      setLoadingUsers(false);
    }
  }, []);

  // Handle user search with debounce
  const userSearchTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const handleUserSearch = useCallback((searchTerm: string) => {
    if (userSearchTimeoutRef.current) {
      clearTimeout(userSearchTimeoutRef.current);
    }
    
    // If empty search, load initial users immediately
    if (!searchTerm.trim()) {
      fetchUsers('');
      return;
    }
    
    // Debounce search - wait longer for short terms
    const debounceTime = searchTerm.length <= 2 ? 500 : 300;
    
    userSearchTimeoutRef.current = setTimeout(() => {
      fetchUsers(searchTerm);
    }, debounceTime);
  }, [fetchUsers]);

  useEffect(() => {
    fetchCompanies();
    fetchUsers(); // Load initial 30 users
    fetchCustodians();
  }, []);

  useEffect(() => {
    if (selectedCompany) {
      fetchAssets();
    }
  }, [selectedCompany]);

  // Extract unique categories from assets
  useEffect(() => {
    if (assets.length > 0) {
      const uniqueCategories = Array.from(new Set(assets.map(a => a.asset_category).filter(Boolean)));
      const categoryOptions: SelectOption[] = uniqueCategories.map((category) => ({
        value: category,
        label: category,
      }));
      setCategories(categoryOptions);
    }
  }, [assets]);


  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const formatCurrency = (amount: number | null) => {
    if (amount === null || amount === undefined) return '-';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatCompanyName = (companyName: string | null) => {
    if (!companyName) return '-';
    
    // Check if it contains "Movement"
    const movementIndex = companyName.toLowerCase().indexOf('movement');
    if (movementIndex === -1) return companyName;
    
    // Get the part before "Movement"
    const beforeMovement = companyName.substring(0, movementIndex).trim();
    // Get the part after "Movement"
    const afterMovement = companyName.substring(movementIndex + 'movement'.length).trim();
    
    // Extract first letters of words before "Movement"
    const words = beforeMovement.split(/\s+/).filter(word => word.length > 0);
    const abbreviation = words.map(word => word[0].toUpperCase()).join('');
    
    // Return abbreviation + M + location
    return `${abbreviation}M ${afterMovement}`;
  };

  // Group assets by category only
  const groupAssetsByCategory = (assets: AssetRecoItem[]) => {
    const grouped: Record<string, AssetRecoItem[]> = {};
    
    assets.forEach((asset) => {
      const category = asset.asset_category || 'Uncategorized';
      
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(asset);
    });
    
    return grouped;
  };

  const getDocStatusBadge = (docstatus: number) => {
    switch (docstatus) {
      case 0:
        return { 
          label: '', 
          colorScheme: 'orange',
          icon: FiEdit2,
          bg: 'orange.50',
          color: 'orange.700',
          borderColor: 'orange.300',
          variant: 'outline' as const
        };
      case 1:
        return { 
          label: '', 
          colorScheme: 'green',
          icon: FiCheckCircle,
          bg: 'green.50',
          color: 'green.700',
          borderColor: 'green.300',
          variant: 'solid' as const
        };
      case 2:
        return { 
          label: '', 
          colorScheme: 'red',
          icon: FiXCircle,
          bg: 'red.50',
          color: 'red.700',
          borderColor: 'red.300',
          variant: 'outline' as const
        };
      default:
        return { 
          label: 'Unknown', 
          colorScheme: 'gray',
          icon: FiEdit2,
          bg: 'gray.50',
          color: 'gray.700',
          borderColor: 'gray.300',
          variant: 'subtle' as const
        };
    }
  };

  const openImageModal = (images: string[], index: number = 0, assetName: string = '') => {
    // Filter out invalid/empty image URLs
    const validImages = images.filter((img) => img && typeof img === 'string' && img.trim() !== '');
    if (validImages.length === 0) {
      toast({
        title: 'No Images',
        description: 'No valid images found for this asset.',
        status: 'info',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    setSelectedImages(validImages);
    setSelectedImageIndex(Math.min(index, validImages.length - 1));
    setSelectedAssetName(assetName);
    setIsImageModalOpen(true);
  };

  const closeImageModal = () => {
    setIsImageModalOpen(false);
    setSelectedImages([]);
    setSelectedImageIndex(0);
    setSelectedAssetName('');
  };

  const handleSubmit = async (assetName: string) => {
    if (submitting[assetName]) return;
    
    try {
      setSubmitting((prev) => ({ ...prev, [assetName]: true }));
      await assetRecoApi.submitAssetReco(assetName);
      
      toast({
        title: 'Success',
        description: `Asset ${assetName} submitted successfully.`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      // Refresh the data
      await fetchAssets();
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to submit asset';
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setSubmitting((prev) => {
        const newState = { ...prev };
        delete newState[assetName];
        return newState;
      });
    }
  };

  // Open detail modal with full specifications support
  const handleOpenDetailModal = (asset: AssetRecoItem) => {
    setSelectedAssetId(asset.name);
    setIsDetailModalOpen(true);
  };

  // Close detail modal
  const handleCloseDetailModal = () => {
    setSelectedAssetId('');
    setIsDetailModalOpen(false);
  };

  // Export current asset list to Excel (HTML table format)
  const exportToExcel = () => {
    if (assets.length === 0) {
      toast({
        title: 'No data to export',
        description: 'Load asset records and try again.',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    const statusLabel = (docstatus: number) => {
      switch (docstatus) {
        case 0: return 'Draft';
        case 1: return 'Submitted';
        case 2: return 'Cancelled';
        default: return 'Unknown';
      }
    };
    const escapeHtml = (val: string | number | null | undefined) => {
      if (val === null || val === undefined) return '-';
      const s = String(val);
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    };
    const escapeAttr = (val: string) =>
      String(val)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    const imagesCellHtml = (imageUrls: string[] | null | undefined) => {
      const valid = imageUrls && Array.isArray(imageUrls) ? imageUrls.filter((u) => u && String(u).trim()) : [];
      if (valid.length === 0) return escapeHtml('-');
      return valid
        .map((url, i) => `<a href="${escapeAttr(url)}">F${i + 1}</a>`)
        .join(' / ');
    };
    const headers = [
      'ID',
      'Asset Name',
      'Category',
      'Location',
      'Purchased Date',
      'Purchased Amount',
      'Custodian',
      'Secondary Custodian',
      'Remarks',
      'Images',
      'Status',
    ];
    let htmlContent = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta charset="utf-8">
        <!--[if gte mso 9]>
        <xml>
          <x:ExcelWorkbook>
            <x:ExcelWorksheets>
              <x:ExcelWorksheet>
                <x:Name>Asset Reco</x:Name>
                <x:WorksheetOptions>
                  <x:DisplayGridlines/>
                </x:WorksheetOptions>
              </x:ExcelWorksheet>
            </x:ExcelWorksheets>
          </x:ExcelWorkbook>
        </xml>
        <![endif]-->
        <style>
          table { border-collapse: collapse; width: 100%; }
          th { background-color: #3182ce; color: white; padding: 8px; text-align: left; font-weight: bold; border: 1px solid #ddd; }
          td { padding: 6px 8px; border: 1px solid #ddd; }
          .number { text-align: right; }
        </style>
      </head>
      <body>
        <table>
          <thead>
            <tr>
              ${headers.map((h) => `<th>${escapeHtml(h)}</th>`).join('')}
            </tr>
          </thead>
          <tbody>
    `;
    assets.forEach((asset) => {
      const cells = [
        `<td>${escapeHtml(asset.name)}</td>`,
        `<td>${escapeHtml(asset.asset_name ?? '-')}</td>`,
        `<td>${escapeHtml(asset.asset_category ?? '-')}</td>`,
        `<td>${escapeHtml(asset.location ?? '-')}</td>`,
        `<td>${escapeHtml(formatDate(asset.purchased_date))}</td>`,
        `<td>${escapeHtml(asset.purchased_amount !== null && asset.purchased_amount !== undefined ? formatCurrency(asset.purchased_amount) : '-')}</td>`,
        `<td>${escapeHtml(asset.custodian ?? '-')}</td>`,
        `<td>${escapeHtml(asset.secondary_custodian ?? '-')}</td>`,
        `<td>${escapeHtml(asset.remarks ?? '-')}</td>`,
        `<td>${imagesCellHtml(asset.image_urls)}</td>`,
        `<td>${escapeHtml(statusLabel(asset.docstatus ?? 0))}</td>`,
      ];
      htmlContent += `<tr>${cells.join('')}</tr>`;
    });
    htmlContent += `
          </tbody>
        </table>
      </body>
      </html>
    `;
    const blob = new Blob([htmlContent], { type: 'application/vnd.ms-excel' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `asset_reco_${new Date().toISOString().split('T')[0]}.xls`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast({
      title: 'Exported to Excel',
      description: `${assets.length} record(s) exported.`,
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };

  return (
    <Box minH="100vh" bg="gray.50">
      <Container maxW="container.xl" py={6}>
        <VStack spacing={4} align="stretch">
          <Flex justify="space-between" align="center">
            <Box>
              <Heading size="xl" mb={1} color="gray.700">
                Asset Reco
              </Heading>
              <Text fontSize="sm" color="gray.600">
                Asset Reconciliation - {assets.length} {assets.length === 1 ? 'record' : 'records'}
              </Text>
            </Box>
            <HStack spacing={3}>
              <Button
                leftIcon={<Icon as={FiFilter} />}
                onClick={() => setShowFilters(!showFilters)}
                colorScheme={showFilters ? "purple" : "gray"}
                variant={showFilters ? "solid" : "outline"}
                size="sm"
              >
                {showFilters ? 'Hide Filters' : 'Show Filters'}
              </Button>
              <Button
                leftIcon={<Icon as={FiDownload} />}
                onClick={exportToExcel}
                isDisabled={loading || assets.length === 0}
                colorScheme="green"
                variant="outline"
                size="sm"
              >
                Export to Excel
              </Button>
              <Tooltip label="Drag column right edge to resize">
                <Button
                  onClick={resetColumnWidths}
                  size="sm"
                  variant="outline"
                  colorScheme="gray"
                >
                  Reset Widths
                </Button>
              </Tooltip>
              <Button
                leftIcon={<Icon as={FiRefreshCw} />}
                onClick={fetchAssets}
                isLoading={loading}
                colorScheme="blue"
                variant="outline"
                size="sm"
              >
                Refresh
              </Button>
            </HStack>
          </Flex>

          {/* Filters Section */}
          {showFilters && (
            <Box bg="white" p={4} borderRadius="lg" shadow="md" borderWidth="1px" borderColor="gray.200">
              <Flex justify="space-between" align="center" mb={3}>
                <Heading size="sm" color="gray.700">
                  <Icon as={FiFilter} mr={2} />
                  Filters
                </Heading>
                <Button
                  leftIcon={<Icon as={FiX} />}
                  onClick={clearAllFilters}
                  colorScheme="red"
                  variant="ghost"
                  size="xs"
                >
                  Clear All
                </Button>
              </Flex>
              
              <VStack spacing={3} align="stretch">
                {/* Row 1: Company and Category */}
                <HStack spacing={3}>
                  <Box flex={1}>
                    <Text fontSize="xs" fontWeight="bold" mb={1} color="gray.600">
                      Company
                    </Text>
                    <Select
                      value={selectedCompany}
                      onChange={(e) => setSelectedCompany(e.target.value)}
                      size="sm"
                      bg="white"
                      borderColor="blue.300"
                      _hover={{ borderColor: 'blue.400' }}
                    >
                      {companies.map((company) => (
                        <option key={company} value={company}>
                          {company}
                        </option>
                      ))}
                    </Select>
                  </Box>
                  
                  <Box flex={1}>
                    <Text fontSize="xs" fontWeight="bold" mb={1} color="gray.600">
                      Category
                    </Text>
                    <SearchableSelect
                      options={categories}
                      value={selectedCategory}
                      onChange={(value) => setSelectedCategory(value)}
                      placeholder="All Categories"
                      isLoading={false}
                    />
                  </Box>
                  
                  <Box flex={1} />
                </HStack>

                {/* Row 2: Date Range */}
                <HStack spacing={3}>
                  <Box flex={1}>
                    <Text fontSize="xs" fontWeight="bold" mb={1} color="gray.600">
                      Purchased Date From
                    </Text>
                    <Input
                      type="date"
                      value={purchasedDateFrom}
                      onChange={(e) => setPurchasedDateFrom(e.target.value)}
                      size="sm"
                      bg="white"
                    />
                  </Box>
                  
                  <Box flex={1}>
                    <Text fontSize="xs" fontWeight="bold" mb={1} color="gray.600">
                      Purchased Date To
                    </Text>
                    <Input
                      type="date"
                      value={purchasedDateTo}
                      onChange={(e) => setPurchasedDateTo(e.target.value)}
                      size="sm"
                      bg="white"
                    />
                  </Box>
                  
                  <Box flex={1}>
                    <Text fontSize="xs" fontWeight="bold" mb={1} color="gray.600">
                      Custodian
                    </Text>
                    <SearchableSelect
                      options={custodians}
                      value={selectedCustodian}
                      onChange={(value) => setSelectedCustodian(value)}
                      placeholder="All Custodians"
                      isLoading={false}
                    />
                  </Box>
                </HStack>

                {/* Row 3: Secondary Custodian and Apply Button */}
                <HStack spacing={3}>
                  <Box flex={1}>
                    <Text fontSize="xs" fontWeight="bold" mb={1} color="gray.600">
                      Secondary Custodian
                    </Text>
                    <SearchableSelect
                      options={users}
                      value={selectedSecondaryCustodian}
                      onChange={(value) => setSelectedSecondaryCustodian(value)}
                      onSearch={handleUserSearch}
                      placeholder="Select Secondary Custodian"
                      isLoading={loadingUsers}
                    />
                  </Box>
                  
                  <Box flex={1}>
                    <Text fontSize="xs" fontWeight="bold" mb={1} color="gray.600" visibility="hidden">
                      Apply
                    </Text>
                    <Button
                      colorScheme="blue"
                      size="sm"
                      width="full"
                      onClick={fetchAssets}
                      isLoading={loading}
                    >
                      Apply Filters
                    </Button>
                  </Box>
                  
                  <Box flex={1} />
                </HStack>
              </VStack>
            </Box>
          )}

          {loading && (
            <Box p={8} bg="white" borderRadius="lg" shadow="sm" textAlign="center">
              <Spinner size="lg" color="blue.500" thickness="3px" />
              <Text mt={3} color="gray.600" fontSize="sm">
                Loading asset data...
              </Text>
            </Box>
          )}

          {error && !loading && (
            <Box p={6} bg="red.50" borderRadius="lg" shadow="sm" borderWidth="1px" borderColor="red.200">
              <Text color="red.600" fontWeight="medium" fontSize="sm">
                Error: {error}
              </Text>
              <Button mt={3} onClick={fetchAssets} colorScheme="red" size="sm">
                Try Again
              </Button>
            </Box>
          )}

          {!loading && !error && assets.length === 0 && (
            <Box p={8} bg="white" borderRadius="lg" shadow="sm" textAlign="center">
              <Text color="gray.500" fontSize="sm">No asset records found.</Text>
            </Box>
          )}

          {!loading && !error && assets.length > 0 && (() => {
            const groupedAssets = groupAssetsByCategory(assets);
            const categories = Object.keys(groupedAssets).sort();
            
            return (
              <VStack spacing={4} align="stretch">
                {categories.map((category) => {
                  const categoryAssets = groupedAssets[category];
                  return (
                    <Box key={category} bg="white" borderRadius="xl" shadow="md" p={4} borderWidth="1px" borderColor="gray.200">
                      {/* Category Header */}
                      <Box bg="purple.500" px={6} py={3} borderRadius="lg" mb={2}>
                        <HStack justify="space-between">
                          <HStack spacing={3}>
                            <Badge colorScheme="white" bg="white" color="purple.700" fontSize="md" px={4} py={2} fontWeight="bold" borderRadius="md">
                              {category}
                            </Badge>
                            <Text fontSize="sm" color="white" fontWeight="medium">
                              {categoryAssets.length} assets
                            </Text>
                          </HStack>
                        </HStack>
                      </Box>
                      
                      <TableContainer overflowX="auto" borderRadius="lg" borderWidth="1px" borderColor="gray.200">
                        <Table variant="simple" size="sm" bg="white" minW="max-content">
                          <Thead bg="blue.500">
                            <Tr>
                              {assetRecoColumnOrder.map((colKey) => {
                                const w = columnWidths[colKey] ?? defaultColumnWidths[colKey] ?? 120;
                                const labels: Record<string, string> = {
                                  id: 'ID',
                                  assetName: 'Asset Name',
                                  location: 'Location',
                                  dateAmount: 'Date / Amount',
                                  custodian: 'Custodian',
                                  remarks: 'Remarks',
                                  images: 'Images',
                                  actions: 'Actions',
                                  status: 'Status',
                                };
                                const isCenter = colKey === 'images' || colKey === 'actions';
                                return (
                                  <Th
                                    key={colKey}
                                    py={3}
                                    fontSize="xs"
                                    fontWeight="bold"
                                    textTransform="uppercase"
                                    color="white"
                                    borderColor="blue.600"
                                    width={`${w}px`}
                                    minW={`${w}px`}
                                    textAlign={isCenter ? 'center' : 'left'}
                                    position="relative"
                                  >
                                    {labels[colKey]}
                                    <Box
                                      position="absolute"
                                      right={0}
                                      top={0}
                                      bottom={0}
                                      width="6px"
                                      cursor="col-resize"
                                      bg={resizingColumn === colKey ? 'blue.300' : 'whiteAlpha.400'}
                                      opacity={resizingColumn === colKey ? 1 : 0.7}
                                      _hover={{ bg: 'blue.200', opacity: 1 }}
                                      onMouseDown={(e) => handleResizeStart(e, colKey)}
                                      zIndex={10}
                                      title="Drag to resize column"
                                      borderRight="2px solid"
                                      borderColor={resizingColumn === colKey ? 'blue.400' : 'whiteAlpha.500'}
                                    />
                                  </Th>
                                );
                              })}
                            </Tr>
                          </Thead>
                          <Tbody>
                            {categoryAssets.map((asset) => {
                              const docStatus = getDocStatusBadge(asset.docstatus ?? 0);
                              const StatusIcon = docStatus.icon;
                              return (
                                <Tr 
                                  key={asset.name} 
                                  _hover={{ bg: 'blue.50', transform: 'scale(1.001)', transition: 'all 0.2s' }}
                                  bg="white"
                                  borderBottomWidth="1px"
                                  borderColor="gray.200"
                                >
                                  <Td py={3} width={`${columnWidths.id ?? defaultColumnWidths.id}px`} minW={`${columnWidths.id ?? defaultColumnWidths.id}px`}>
                                    <Text fontWeight="bold" color="blue.700" fontSize="sm">
                                      {asset.name}
                                    </Text>
                                  </Td>
                                  <Td py={3} width={`${columnWidths.assetName ?? defaultColumnWidths.assetName}px`} minW={`${columnWidths.assetName ?? defaultColumnWidths.assetName}px`} maxW={`${columnWidths.assetName ?? defaultColumnWidths.assetName}px`}>
                                    <Text fontSize="sm" noOfLines={3} wordBreak="break-word" whiteSpace="normal">
                                      {asset.asset_name || '-'}
                                    </Text>
                                  </Td>
                                  <Td py={3} width={`${columnWidths.location ?? defaultColumnWidths.location}px`} minW={`${columnWidths.location ?? defaultColumnWidths.location}px`} maxW={`${columnWidths.location ?? defaultColumnWidths.location}px`}>
                                    <Text fontSize="sm" noOfLines={3} wordBreak="break-word" whiteSpace="normal">
                                      {asset.location || '-'}
                                    </Text>
                                  </Td>
                                  <Td py={3} width={`${columnWidths.dateAmount ?? defaultColumnWidths.dateAmount}px`} minW={`${columnWidths.dateAmount ?? defaultColumnWidths.dateAmount}px`}>
                                    <VStack align="start" spacing={0}>
                                      <Text fontSize="sm">{formatDate(asset.purchased_date)}</Text>
                                      <Text fontSize="sm" fontWeight="bold" color="green.600">
                                        {formatCurrency(asset.purchased_amount)}
                                      </Text>
                                    </VStack>
                                  </Td>
                                  <Td py={3} width={`${columnWidths.custodian ?? defaultColumnWidths.custodian}px`} minW={`${columnWidths.custodian ?? defaultColumnWidths.custodian}px`}>
                                    <Text fontSize="sm" fontWeight="medium">{asset.custodian || '-'}</Text>
                                  </Td>
                                  <Td py={3} width={`${columnWidths.remarks ?? defaultColumnWidths.remarks}px`} minW={`${columnWidths.remarks ?? defaultColumnWidths.remarks}px`} maxW={`${columnWidths.remarks ?? defaultColumnWidths.remarks}px`}>
                                    <Text fontSize="sm" noOfLines={3} wordBreak="break-word" whiteSpace="normal">
                                      {asset.remarks || '-'}
                                    </Text>
                                  </Td>
                                  <Td py={3} textAlign="center" width={`${columnWidths.images ?? defaultColumnWidths.images}px`} minW={`${columnWidths.images ?? defaultColumnWidths.images}px`}>
                                    {asset.image_urls && asset.image_urls.length > 0 ? (() => {
                                      const validImageUrls = asset.image_urls.filter((url) => url && typeof url === 'string' && url.trim() !== '');
                                      if (validImageUrls.length === 0) {
                                        return <Text color="gray.400" fontSize="xs">-</Text>;
                                      }
                                      return (
                                        <Button
                                          size="sm"
                                          variant="ghost"
                                          colorScheme="blue"
                                          leftIcon={<Icon as={FiImage} />}
                                          onClick={() => openImageModal(validImageUrls, 0, asset.name)}
                                        >
                                          {validImageUrls.length}
                                        </Button>
                                      );
                                    })() : (
                                      <Text color="gray.400" fontSize="xs">-</Text>
                                    )}
                                  </Td>
                                  <Td py={3} textAlign="center" width={`${columnWidths.actions ?? defaultColumnWidths.actions}px`} minW={`${columnWidths.actions ?? defaultColumnWidths.actions}px`}>
                                    <HStack spacing={2} justify="center">
                                      <Tooltip label={asset.docstatus === 0 ? "Edit with Specifications" : "View Details"}>
                                        <Button
                                          size="sm"
                                          colorScheme="blue"
                                          leftIcon={<Icon as={asset.docstatus === 0 ? FiEdit2 : FiEye} />}
                                          onClick={() => handleOpenDetailModal(asset)}
                                        >
                                          {asset.docstatus === 0 ? 'Edit' : 'View'}
                                        </Button>
                                      </Tooltip>
                                      {asset.docstatus === 0 && (
                                        <Button
                                          size="sm"
                                          colorScheme="green"
                                          leftIcon={<Icon as={FiSend} />}
                                          isLoading={submitting[asset.name]}
                                          onClick={() => handleSubmit(asset.name)}
                                        >
                                          Submit
                                        </Button>
                                      )}
                                    </HStack>
                                  </Td>
                                  <Td py={3} width={`${columnWidths.status ?? defaultColumnWidths.status}px`} minW={`${columnWidths.status ?? defaultColumnWidths.status}px`}>
                                    <Badge 
                                      colorScheme={docStatus.colorScheme} 
                                      variant="solid"
                                      fontSize="xs"
                                      display="flex"
                                      alignItems="center"
                                      gap={1}
                                      w="fit-content"
                                      px={3}
                                      py={1.5}
                                      fontWeight="bold"
                                      borderRadius="md"
                                    >
                                      <Icon as={StatusIcon} boxSize={3} />
                                      {docStatus.label}
                                    </Badge>
                                  </Td>
                                </Tr>
                              );
                            })}
                          </Tbody>
                        </Table>
                      </TableContainer>
                    </Box>
                  );
                })}
              </VStack>
            );
          })()}

        </VStack>
      </Container>

      {/* Image Modal */}
      <ImageModal
        isOpen={isImageModalOpen}
        onClose={closeImageModal}
        images={selectedImages}
        initialIndex={selectedImageIndex}
        assetName={selectedAssetName}
      />

      {/* Asset Detail Modal with Full Specifications Support */}
      {selectedAssetId && (
        <AssetRecoDetailModal
          isOpen={isDetailModalOpen}
          onClose={handleCloseDetailModal}
          assetId={selectedAssetId}
          onSave={fetchAssets}
          users={users}
          onUserSearch={handleUserSearch}
          loadingUsers={loadingUsers}
        />
      )}
    </Box>
  );
};

export default AssetRecoPage;
