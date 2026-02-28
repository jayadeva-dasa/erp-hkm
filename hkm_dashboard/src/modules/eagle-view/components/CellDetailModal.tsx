import React, { useState, useEffect, useMemo } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Text,
  Spinner,
  Center,
  VStack,
  HStack,
  Badge,
  Button,
  Flex,
  useColorModeValue,
  useDisclosure,
} from '@chakra-ui/react';
import { DownloadIcon } from '@chakra-ui/icons';
import { eagleViewApi } from '../api/eagleViewApi';
import type { EagleViewFilters, EagleViewRow } from '../types';
import { VoucherViewerModal } from './VoucherViewerModal';

interface CellDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  mainDimensionValue: string | null;
  secondaryDimensionValue: string | null;
  columnType: 'inc' | 'exp' | 'net' | 'both' | null;
  baseFilters: EagleViewFilters;
  mainDimensionLabel: string;
  secondaryDimensionLabel: string;
}

export const CellDetailModal: React.FC<CellDetailModalProps> = ({
  isOpen,
  onClose,
  mainDimensionValue,
  secondaryDimensionValue,
  columnType,
  baseFilters,
  mainDimensionLabel,
  secondaryDimensionLabel,
}) => {
  const [loading, setLoading] = useState(false);
  const [detailData, setDetailData] = useState<EagleViewRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // For VoucherViewerModal
  const { isOpen: isVoucherModalOpen, onOpen: onVoucherModalOpen, onClose: onVoucherModalClose } = useDisclosure();
  const [selectedVoucherIndex, setSelectedVoucherIndex] = useState(0);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const headerBg = useColorModeValue('gray.50', 'gray.700');

  // Fetch detailed data when modal opens
  useEffect(() => {
    if (isOpen && mainDimensionValue && secondaryDimensionValue) {
      fetchDetailData();
    }
  }, [isOpen, mainDimensionValue, secondaryDimensionValue, columnType]);

  const fetchDetailData = async () => {
    if (!mainDimensionValue || !secondaryDimensionValue) return;

    setLoading(true);
    setError(null);

    try {
      // Build filters for detailed view
      const detailFilters: EagleViewFilters = {
        ...baseFilters,
        report_view: 'Detailed View',
        // Add main dimension filter
        dimension: baseFilters.main_dimension || 'Cost Head',
        dimension_value: [mainDimensionValue],
        // Add secondary dimension as additional filter
        // We need to use the appropriate filter key based on secondary dimension type
      };

      // Add secondary dimension filter dynamically
      if (baseFilters.secondary_dimension) {
        // Create additional dimension filter
        if (baseFilters.secondary_dimension === 'Cost Center') {
          detailFilters.additional_dimensions = [{
            dimension: 'Cost Center',
            values: [secondaryDimensionValue]
          }];
        } else if (baseFilters.secondary_dimension === 'Project') {
          detailFilters.additional_dimensions = [{
            dimension: 'Project',
            values: [secondaryDimensionValue]
          }];
        } else {
          // For other dimensions, add as additional dimensions
          detailFilters.additional_dimensions = [{
            dimension: baseFilters.secondary_dimension,
            values: [secondaryDimensionValue]
          }];
        }
      }

      // Set report type based on column type
      if (columnType === 'inc') {
        detailFilters.report_type = 'Detailed Income';
      } else if (columnType === 'exp') {
        detailFilters.report_type = 'Detailed Expense';
      } else {
        detailFilters.report_type = 'Both Income and Expenses';
      }

      console.log('Fetching detail data with filters:', detailFilters);

      const response = await eagleViewApi.getEagleViewData(detailFilters);
      
      if (response && response.data) {
        setDetailData(Array.isArray(response.data) ? response.data : []);
      } else {
        setDetailData([]);
      }
    } catch (err: any) {
      console.error('Error fetching detail data:', err);
      setError(err.message || 'Failed to load detailed data');
      setDetailData([]);
    } finally {
      setLoading(false);
    }
  };

  // Format currency
  const formatCurrency = (value: number | undefined) => {
    if (value === undefined || value === null) return '₹ 0';
    return `₹ ${Math.round(value).toLocaleString('en-IN')}`;
  };

  // Get column type label
  const getColumnTypeLabel = () => {
    if (columnType === 'inc') return 'Income';
    if (columnType === 'exp') return 'Expense';
    if (columnType === 'net') return 'Net';
    return 'Both';
  };

  // Prepare voucher data for VoucherViewerModal
  const voucherData = useMemo(() => {
    return detailData.map(row => ({
      voucher_no: row.voucher_no,
      voucher_type: row.voucher_type,
      posting_date: row.posting_date,
      company: row.company,
      attachments: row.attachments || [],
    }));
  }, [detailData]);

  // Handle voucher click
  const handleVoucherClick = (index: number) => {
    setSelectedVoucherIndex(index);
    onVoucherModalOpen();
  };

  // Calculate totals for income and expense
  const totals = useMemo(() => {
    let totalIncome = 0;
    let totalExpense = 0;

    detailData.forEach(row => {
      const amount = (row.amount as number) || 0;
      if (row.root_type === 'Income') {
        totalIncome += amount;
      } else if (row.root_type === 'Expense') {
        totalExpense += amount;
      }
    });

    return {
      income: totalIncome,
      expense: totalExpense,
      net: totalIncome - totalExpense,
    };
  }, [detailData]);

  // Export to Excel
  const exportToExcel = () => {
    if (detailData.length === 0) return;

    const htmlContent = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta charset="utf-8">
        <style>
          table { border-collapse: collapse; width: 100%; }
          th { background-color: #4a5568; color: white; padding: 8px; text-align: left; font-weight: bold; border: 1px solid #ddd; }
          td { padding: 6px 8px; border: 1px solid #ddd; }
          .number { text-align: right; }
        </style>
      </head>
      <body>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Company</th>
              <th>Voucher Type</th>
              <th>Voucher No</th>
              <th>${mainDimensionLabel}</th>
              <th>${secondaryDimensionLabel}</th>
              <th>Account</th>
              <th>Type</th>
              <th class="number">Amount</th>
              <th>Remarks</th>
            </tr>
          </thead>
          <tbody>
            ${detailData.map(row => `
              <tr>
                <td>${row.posting_date || '-'}</td>
                <td>${row.company || '-'}</td>
                <td>${row.voucher_type || '-'}</td>
                <td>${row.voucher_no || '-'}</td>
                <td>${mainDimensionValue}</td>
                <td>${secondaryDimensionValue}</td>
                <td>${row.account_head || '-'}</td>
                <td>${row.root_type || '-'}</td>
                <td class="number">${Math.round((row.amount as number) || 0).toLocaleString('en-IN')}</td>
                <td>${row.remarks || '-'}</td>
              </tr>
            `).join('')}
            <tr style="font-weight: bold; background-color: #f7fafc; border-top: 2px solid #333;">
              <td colspan="7" style="text-align: right; padding: 12px;">TOTALS:</td>
              <td style="text-align: center;">-</td>
              <td class="number">
                ${totals.income > 0 ? `Income: ${Math.round(totals.income).toLocaleString('en-IN')}<br>` : ''}
                ${totals.expense > 0 ? `Expense: ${Math.round(totals.expense).toLocaleString('en-IN')}<br>` : ''}
                ${totals.income > 0 || totals.expense > 0 ? `<strong>Net: ${Math.round(totals.net).toLocaleString('en-IN')}</strong>` : ''}
              </td>
              <td>-</td>
            </tr>
          </tbody>
        </table>
      </body>
      </html>
    `;

    const blob = new Blob([htmlContent], { type: 'application/vnd.ms-excel' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `detail_${mainDimensionValue}_${secondaryDimensionValue}_${new Date().toISOString().split('T')[0]}.xls`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="6xl">
      <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(4px)" />
      <ModalContent maxW="95vw" maxH="90vh" m={4}>
        {/* Header */}
        <ModalHeader bg={headerBg} borderBottom="2px" borderColor={borderColor} pr={16}>
          <VStack align="start" spacing={2}>
            <Text fontSize="lg" fontWeight="bold">
              Detailed Entries
            </Text>
            <HStack spacing={3} flexWrap="wrap">
              <Badge colorScheme="purple" fontSize="sm" px={2} py={1}>
                {mainDimensionLabel}: {mainDimensionValue}
              </Badge>
              <Badge colorScheme="blue" fontSize="sm" px={2} py={1}>
                {secondaryDimensionLabel}: {secondaryDimensionValue}
              </Badge>
              {columnType && (
                <Badge 
                  colorScheme={
                    columnType === 'inc' ? 'green' : 
                    columnType === 'exp' ? 'red' : 
                    'gray'
                  } 
                  fontSize="sm" 
                  px={2} 
                  py={1}
                >
                  Type: {getColumnTypeLabel()}
                </Badge>
              )}
              {detailData.length > 0 && (
                <Badge colorScheme="teal" fontSize="sm" px={2} py={1}>
                  {detailData.length} {detailData.length === 1 ? 'Entry' : 'Entries'}
                </Badge>
              )}
            </HStack>
          </VStack>
        </ModalHeader>
        <ModalCloseButton top={4} right={4} />

        {/* Body */}
        <ModalBody p={0}>
          {loading ? (
            <Center h="400px">
              <VStack spacing={4}>
                <Spinner size="xl" color="blue.500" />
                <Text color="gray.600">Loading detailed entries...</Text>
              </VStack>
            </Center>
          ) : error ? (
            <Center h="400px">
              <VStack spacing={4}>
                <Text color="red.500" fontSize="lg" fontWeight="bold">
                  Error
                </Text>
                <Text color="gray.600">{error}</Text>
                <Button onClick={fetchDetailData} colorScheme="blue" size="sm">
                  Retry
                </Button>
              </VStack>
            </Center>
          ) : detailData.length === 0 ? (
            <Center h="400px">
              <Text color="gray.500" fontSize="lg">
                No entries found for this selection
              </Text>
            </Center>
          ) : (
            <>
              {/* Action Bar */}
              <Flex p={4} borderBottom="1px" borderColor={borderColor} justify="space-between" align="center" gap={4} flexWrap="wrap">
                <HStack spacing={4} flexWrap="wrap">
                  <Text fontSize="sm" color="gray.600">
                    Showing {detailData.length} {detailData.length === 1 ? 'entry' : 'entries'}
                  </Text>
                  
                  {totals.income > 0 && (
                    <Badge colorScheme="green" fontSize="sm" px={3} py={1}>
                      Income: ₹ {Math.round(totals.income).toLocaleString('en-IN')}
                    </Badge>
                  )}
                  
                  {totals.expense > 0 && (
                    <Badge colorScheme="red" fontSize="sm" px={3} py={1}>
                      Expense: ₹ {Math.round(totals.expense).toLocaleString('en-IN')}
                    </Badge>
                  )}
                  
                  {(totals.income > 0 || totals.expense > 0) && (
                    <Badge 
                      colorScheme={totals.net >= 0 ? 'green' : 'red'} 
                      fontSize="sm" 
                      px={3} 
                      py={1}
                      variant="solid"
                    >
                      Net: ₹ {Math.round(totals.net).toLocaleString('en-IN')}
                    </Badge>
                  )}
                </HStack>
                
                <Button
                  leftIcon={<DownloadIcon />}
                  colorScheme="green"
                  size="sm"
                  onClick={exportToExcel}
                >
                  Export to Excel
                </Button>
              </Flex>

              {/* Table */}
              <Box 
                overflowX="auto" 
                overflowY="auto"
                maxH="calc(90vh - 200px)"
              >
                <Table variant="simple" size="sm">
                  <Thead bg="gray.50" position="sticky" top={0} zIndex={10}>
                    <Tr>
                      <Th textTransform="none" fontSize="sm" fontWeight="600">Date</Th>
                      <Th textTransform="none" fontSize="sm" fontWeight="600">Company</Th>
                      <Th textTransform="none" fontSize="sm" fontWeight="600">Voucher Type</Th>
                      <Th textTransform="none" fontSize="sm" fontWeight="600">Voucher No</Th>
                      <Th textTransform="none" fontSize="sm" fontWeight="600">Account</Th>
                      <Th textTransform="none" fontSize="sm" fontWeight="600">Type</Th>
                      <Th textTransform="none" fontSize="sm" fontWeight="600" isNumeric>Amount</Th>
                      <Th textTransform="none" fontSize="sm" fontWeight="600">Remarks</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {detailData.map((row, index) => (
                      <Tr key={index} _hover={{ bg: 'gray.50' }}>
                        <Td fontSize="sm">{row.posting_date || '-'}</Td>
                        <Td fontSize="sm">{row.company || '-'}</Td>
                        <Td fontSize="sm">{row.voucher_type || '-'}</Td>
                        <Td fontSize="sm">
                          <Button
                            variant="link"
                            colorScheme="blue"
                            size="sm"
                            fontWeight="500"
                            onClick={() => handleVoucherClick(index)}
                          >
                            {row.voucher_no || '-'}
                          </Button>
                        </Td>
                        <Td fontSize="sm">{row.account_head || '-'}</Td>
                        <Td fontSize="sm">
                          <Badge
                            colorScheme={row.root_type === 'Income' ? 'green' : 'red'}
                            fontSize="xs"
                          >
                            {row.root_type || '-'}
                          </Badge>
                        </Td>
                        <Td fontSize="sm" isNumeric>
                          <Text
                            fontWeight="500"
                            color={row.root_type === 'Income' ? 'green.600' : 'red.600'}
                          >
                            {formatCurrency(row.amount as number)}
                          </Text>
                        </Td>
                        <Td fontSize="sm" maxW="200px" isTruncated title={row.remarks as string}>
                          {row.remarks || '-'}
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
            </>
          )}
        </ModalBody>
      </ModalContent>

      {/* Voucher Viewer Modal */}
      <VoucherViewerModal
        isOpen={isVoucherModalOpen}
        onClose={onVoucherModalClose}
        vouchers={voucherData}
        initialIndex={selectedVoucherIndex}
      />
    </Modal>
  );
};

